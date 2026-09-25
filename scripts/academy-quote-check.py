#!/usr/bin/env python3
"""Re-check the verbatim evidence quotes in the claim decisions against their sources.

Usage: python scripts/academy-quote-check.py [--claim ID ...] [--cache DIR] [--out report.json]

Reads docs/academy/CLAIM-REVIEWS.json. Every evidence entry with a fetchUrl and
a quote is checked: the fetchUrl is downloaded (cached in --cache, default a
temporary directory; a wheel's named `member` is extracted, or every text member is searched when none is named), HTML is reduced
to text, whitespace is collapsed, simple Markdown and docstring line joins are
undone, and each quote fragment (split on '...') must appear in order. It
needs network access to the pinned sources (raw.githubusercontent.com, PyPI,
Google API discovery documents) and is not part of `npm run check`. Decision
texts that name "verify_quotes.py" refer to the build-session copy of this
checker, which applied the same matching. A pinned commit or package version
keeps the bytes stable; a failure means the quote, not the source, changed.
Exit 1 when any quote is not found or cannot be fetched.
"""
import argparse
import hashlib
import html
import io
import json
import re
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fetch(url, cache):
    path = cache / hashlib.sha256(url.encode()).hexdigest()
    if path.exists():
        return path.read_bytes()
    result = subprocess.run(["curl", "-sSL", "--max-time", "90", "-f", url], capture_output=True)
    if result.returncode != 0:
        return None
    path.write_bytes(result.stdout)
    return result.stdout


def norm(text):
    text = unicodedata.normalize("NFKC", text)
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'),
                 ("–", "-"), ("—", "-"), (" ", " ")):
        text = text.replace(a, b)
    return re.sub(r"\s+", " ", text).strip().lower()


def variants(raw):
    text = raw.decode("utf-8", "replace")
    out = [text]
    if "<html" in text[:2000].lower() or "<!doctype html" in text[:200].lower():
        stripped = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", text)
        out.append(html.unescape(re.sub(r"(?s)<[^>]+>", " ", stripped)))
    markdown = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    out.append(re.sub(r"[*_`]{1,3}", "", markdown))
    out.append(re.sub(r'"""|\n\s*', " ", text))
    return [norm(v) for v in out]


def found(quote, texts):
    fragments = [norm(f) for f in re.split(r"\.\.\.|…", quote) if norm(f)]
    if not fragments:
        return False
    for text in texts:
        pos = 0
        for fragment in fragments:
            i = text.find(fragment, pos)
            if i < 0:
                break
            pos = i + len(fragment)
        else:
            return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--claim", nargs="*")
    parser.add_argument("--cache")
    parser.add_argument("--out")
    args = parser.parse_args()
    cache = Path(args.cache) if args.cache else Path(tempfile.mkdtemp(prefix="quote-check-"))
    cache.mkdir(parents=True, exist_ok=True)
    decisions = json.loads((ROOT / "docs/academy/CLAIM-REVIEWS.json").read_text())["claims"]
    report, failures = [], 0
    for decision in decisions:
        if args.claim and decision["id"] not in args.claim:
            continue
        for i, entry in enumerate(decision.get("evidence") or []):
            url, quote = entry.get("fetchUrl"), entry.get("quote")
            if not (url and quote):
                continue
            raw = fetch(url, cache)
            if raw is None:
                status = "fetch-failed"
            else:
                texts = None
                if url.endswith(".whl"):
                    try:
                        wheel = zipfile.ZipFile(io.BytesIO(raw))
                        members = [entry["member"]] if entry.get("member") else [
                            n for n in wheel.namelist() if n.endswith((".py", ".md", ".txt", ".json", "METADATA"))]
                        texts = [t for n in members for t in variants(wheel.read(n))]
                    except (KeyError, zipfile.BadZipFile):
                        texts = []
                status = "ok" if found(quote, texts if texts is not None else variants(raw)) else "quote-not-found"
            report.append({"claim": decision["id"], "evidence": i, "fetchUrl": url, "status": status})
            if status != "ok":
                failures += 1
                print(f"FAIL {decision['id']} #{i} {status} {url}")
    print(f"{len(report) - failures}/{len(report)} quotes verified")
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=1) + "\n")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
