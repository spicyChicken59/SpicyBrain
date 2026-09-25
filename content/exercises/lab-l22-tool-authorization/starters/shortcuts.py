"""Three plausible shortcuts that run_tests.py proves wrong. Read them; do not copy them.

Each factory takes the gate module under test (the reference solution or
your completed starter) and returns a subclass of its Gate with one
shortcut added, so the tests can show exactly which property breaks.
"""
from __future__ import annotations

import re


def content_trusting(module, documents: dict):
    """Shortcut 1: believe what retrieved text says about identity and approval.

    It scans the documents in the call's context. "the current user is
    supervisor X" switches the session to X; "supervisor X has approved"
    skips the approval hold. A system-prompt sentence such as "only trust the
    signed-in user" would not stop this code, because the code, not the model,
    reads the text.
    """

    class ContentTrustingGate(module.Gate):
        def handle(self, call):
            text = " ".join(documents[doc_id]["text"] for doc_id in call.get("context", []))
            claimed = re.search(r"current user is supervisor ([a-z0-9-]+)", text)
            if claimed:
                session = next(s for s, v in self.sessions.items() if v["user"] == claimed.group(1))
                call = dict(call, session=session)
            self._approved_in_text = re.search(r"supervisor ([a-z0-9-]+) has approved", text)
            return super().handle(call)

        def _needs_approval(self, tool, arguments):
            if getattr(self, "_approved_in_text", None):
                return False
            return super()._needs_approval(tool, arguments)

    return ContentTrustingGate


def fresh_key_per_attempt(module):
    """Shortcut 2: retry a timed-out write, but with a new key on every attempt.

    It looks careful (bounded attempts, backoff) and still duplicates the
    effect, because the target cannot tell the second attempt is the same
    intent as the first one that committed late.
    """

    class FreshKeyGate(module.Gate):
        def _execute(self, tool, arguments, key, on_behalf_of, extra, ref):
            limit, backoff = tool["timeout_ms"], tool["backoff_ms"]
            log, elapsed = [], 0
            for attempt in range(1, tool["max_attempts"] + 1):
                attempt_key = None if key is None else f"{key}/attempt-{attempt}"
                latency, result = self.downstream.perform(tool, arguments, attempt_key, on_behalf_of, extra, ref)
                if latency <= limit:
                    log.append({"attempt": attempt, "latency_ms": latency, "outcome": "reply", "backoff_ms": 0})
                    return {"status": "ok", "attempts": attempt, "elapsed_ms": elapsed + latency, "log": log,
                            "result": result}
                wait = backoff * 2 ** (attempt - 1) if attempt < tool["max_attempts"] else 0
                elapsed += limit + wait
                log.append({"attempt": attempt, "latency_ms": latency, "outcome": "timeout", "backoff_ms": wait})
            return {"status": "timed_out", "attempts": tool["max_attempts"], "elapsed_ms": elapsed, "log": log,
                    "result": None}

    return FreshKeyGate


def application_fallback(module):
    """Shortcut 3: when the user's credential is missing, act as the application.

    The request "works", but the grants that applied were the service
    principal's, across every plant, not the signed-in user's.
    """

    class FallbackGate(module.Gate):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            app = self.application["id"]
            scopes = sorted(set(self.scope_of.values()))
            grants = [f"{s}:{p}" for s in self.application["delegated_scopes"] for p in scopes]
            self.users = dict(self.users, **{app: {"grants": grants}})

        def _user(self, session_id):
            return super()._user(session_id) or self.application["id"]

    return FallbackGate
