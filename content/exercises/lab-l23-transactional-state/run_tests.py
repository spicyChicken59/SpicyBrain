"""lab-l23-transactional-state test runner (platform-guide class; local PostgreSQL 16 only).

    python3.12 run_tests.py --evidence <path>      # judge solutions/*.sql, write evidence JSON
    python3.12 run_tests.py --starter              # judge your starters/*.sql by the same literals
    python3.12 run_tests.py --pg-bin <dir>         # where postgres, initdb, pg_ctl and psql live

Starts a throwaway PostgreSQL 16 server on 127.0.0.1 for the length of the run, executes
the SQL through psql (two psql processes are two real sessions), then stops the server and
deletes its directory. Standard library only. Every expected value is a hand-authored
literal in expected/*.json (derivations in DATA.md); no test compares the SQL with a value
the SQL itself produced. Managed Lakebase is NOT executed: see ADAPTATION.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True  # keep the package free of __pycache__
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from pglocal import LabError, LocalPostgres, Session, find_bin_dir  # noqa: E402

LAB = "lab-l23-transactional-state"
EXECUTION_CLASS = "platform-guide"
FIX = ROOT / "fixtures"
EXP = ROOT / "expected"
APP_ROLE = "qr_app"
TEMPLATE = "qr_template"
OPTIONS = {"sql_dir": ROOT / "solutions", "pg_bin": None}
STATE: dict[str, object] = {}
OUTPUTS: dict[str, object] = {}
MESSAGE_KEYS = ("message_id", "item_id", "source_seq", "plant_id", "part_serial",
                "defect_code", "severity", "flagged_at")

# ---- the wrong approaches the tests prove wrong (also shown in SOLUTIONS.md) -------------
NAIVE_INTAKE = """
INSERT INTO qr.review_item AS r
       (item_id, plant_id, part_serial, defect_code, severity, flagged_at, source_seq)
VALUES (:'item_id', :'plant_id', :'part_serial', :'defect_code',
        CAST(:severity AS smallint), CAST(:'flagged_at' AS timestamptz), :source_seq)
ON CONFLICT (item_id) DO UPDATE
   SET defect_code = EXCLUDED.defect_code, severity = EXCLUDED.severity,
       source_seq = EXCLUDED.source_seq, version = r.version + 1
RETURNING r.item_id, r.version;
"""
UNLOCKED_PICK = ("SELECT item_id FROM qr.review_item WHERE status = 'ready' "
                 "ORDER BY severity DESC, flagged_at, item_id LIMIT 1;")
UNLOCKED_TAKE = ("UPDATE qr.review_item SET status = 'claimed', claimed_by = :'reviewer_id', "
                 "claimed_at = now(), version = version + 1 WHERE item_id = :'item_id' RETURNING item_id;")
SNAPSHOT = """
SELECT item_id, plant_id, part_serial, defect_code, severity,
       to_char(flagged_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
       source_seq, status, coalesce(claimed_by, ''), coalesce(decision, ''), version
  FROM qr.review_item ORDER BY item_id;
"""
SNAPSHOT_FIELDS = ("plant_id", "part_serial", "defect_code", "severity", "flagged_at", "source_seq",
                   "status", "claimed_by", "decision", "version")
INTEGER_FIELDS = {"severity", "source_seq", "version"}


def load(folder: Path, name: str):
    return json.loads((folder / name).read_text(encoding="utf-8"))


def statement(name: str) -> str:
    return (OPTIONS["sql_dir"] / name).read_text(encoding="utf-8")


def server() -> LocalPostgres:
    return STATE["server"]  # type: ignore[return-value]


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def record(name: str, value):
    OUTPUTS[name] = value
    return value


def constraint_name(error: str) -> str:
    found = re.search(r'constraint "([^"]+)"', error) or re.search(r'column "([^"]+)"', error)
    return found.group(1) if found else ""


# ---- module fixture: one throwaway server for the whole run -------------------------------
def setUpModule():  # noqa: N802 (unittest hook name)
    bin_dir, version = find_bin_dir(OPTIONS["pg_bin"])
    pg = LocalPostgres(bin_dir)
    STATE["server"] = pg
    unittest.addModuleCleanup(stop_server)  # runs even when this setup fails part-way
    STATE["server_version_line"] = version
    STATE["psql_version"] = subprocess.run([str(bin_dir / "psql"), "--version"],
                                           capture_output=True, text=True).stdout.strip()
    pg.start()
    STATE["cluster_owner"] = pg.os_user or "current user"
    STATE["app_password"] = f"app-{time.time_ns()}"  # generated per run, never stored in the package
    steps = [pg.run(f"CREATE DATABASE {TEMPLATE};"),
             pg.run_file(OPTIONS["sql_dir"] / "schema.sql", db=TEMPLATE),
             pg.run(f"CREATE ROLE {APP_ROLE} LOGIN PASSWORD '{STATE['app_password']}';"),
             pg.run_file(OPTIONS["sql_dir"] / "grants.sql", db=TEMPLATE)]
    reference = load(FIX, "reference.json")
    seed = ["INSERT INTO qr.plant (plant_id, plant_name) VALUES "
            + ", ".join(f"('{p['plant_id']}', '{p['plant_name']}')" for p in reference["plants"]) + ";",
            "INSERT INTO qr.reviewer (reviewer_id, display_name, plant_id, active) VALUES "
            + ", ".join(f"('{r['reviewer_id']}', '{r['display_name']}', '{r['plant_id']}', {str(r['active']).lower()})"
                        for r in reference["reviewers"]) + ";"]
    steps.append(pg.run("\n".join(seed), db=TEMPLATE))
    for done in steps:
        if done.returncode != 0:
            raise LabError(f"template setup failed: {done.stderr.strip()}")


def stop_server():
    pg = STATE.get("server")
    if pg is not None:
        STATE["cleanup_ok"] = pg.stop()  # type: ignore[union-attr]


class LabCase(unittest.TestCase):
    """Each test gets its own database cloned from the prepared template."""

    def setUp(self):
        self.db = "t_" + self._testMethodName.lower()
        self.sessions: list[Session] = []
        pg = server()
        pg.run(f"DROP DATABASE IF EXISTS {self.db} WITH (FORCE);")
        created = pg.run(f"CREATE DATABASE {self.db} TEMPLATE {TEMPLATE};")
        self.assertEqual(created.returncode, 0, created.stderr)

    def tearDown(self):
        for session in self.sessions:
            session.close()
        server().run(f"DROP DATABASE IF EXISTS {self.db} WITH (FORCE);")

    # -- helpers ------------------------------------------------------------------------
    def app(self, name: str) -> Session:
        session = server().session(db=self.db, user=APP_ROLE, password=STATE["app_password"], app=name)
        self.sessions.append(session)
        return session

    def apply(self, session: Session, deliveries, sql: str) -> list[str]:
        outcomes = []
        for message in deliveries:
            result = session.run(sql, {k: message[k] for k in MESSAGE_KEYS})
            self.assertEqual(result.sqlstate, "00000", result.lines)
            outcomes.append("applied" if result.rows else "skipped")
        return outcomes

    def primary(self) -> list[str]:
        return self.apply(self.app("lab-intake"), load(FIX, "intake_stream.json")["deliveries"],
                          statement("intake.sql"))

    def snapshot(self) -> dict:
        out = server().scalar(SNAPSHOT, db=self.db)
        items = {}
        for line in out.splitlines():
            cells = line.split("|")
            row = dict(zip(SNAPSHOT_FIELDS, cells[1:]))
            items[cells[0]] = {k: int(v) if k in INTEGER_FIELDS else v for k, v in row.items()}
        return items

    def count(self, table: str) -> int:
        return int(server().scalar(f"SELECT count(*) FROM qr.{table};", db=self.db))

    def claim(self, session: Session, reviewer: str, sql: str | None = None):
        return session.run(sql or statement("claim.sql"), {"reviewer_id": reviewer})

    # -- 0. the engine really is local PostgreSQL 16 ----------------------------------------
    def test_00_server_is_local_postgresql_16(self):
        expected = load(EXP, "server.json")
        pg = server()
        actual = {
            "major_version": pg.scalar("SHOW server_version;", db=self.db).split(".")[0],
            "default_isolation": pg.scalar("SHOW transaction_isolation;", db=self.db),
            "listen_addresses": pg.scalar("SHOW listen_addresses;", db=self.db),
            "password_encryption": pg.scalar("SHOW password_encryption;", db=self.db)}
        STATE["server_version"] = pg.scalar("SHOW server_version;", db=self.db)
        self.assertEqual(record("server", actual), expected)

    # -- 1. constraints reject impossible rows, and a failed statement changes nothing ------------
    def test_01_constraints_reject_bad_rows(self):
        expected = load(EXP, "constraints.json")
        self.primary()
        worker = self.app("lab-worker-a")
        self.assertEqual(self.claim(worker, "R-101").column(), ["QR-0001"])
        actual = []
        for case in load(FIX, "constraint_cases.json")["cases"]:
            result = worker.run(case["sql"])
            actual.append({"case": case["case"], "sqlstate": result.sqlstate,
                           "name": constraint_name(" ".join(result.errors))})
        record("constraints", actual)
        self.assertEqual(actual, expected["cases"])
        self.assertEqual(self.count("review_item"), expected["rows_after_cases"])

    def test_02_multirow_insert_is_atomic(self):
        expected = load(EXP, "constraints.json")["atomic_batch"]
        self.primary()
        before = self.count("review_item")
        result = self.app("lab-worker-a").run(load(FIX, "constraint_cases.json")["atomic_batch"])
        visible = int(server().scalar("SELECT count(*) FROM qr.review_item WHERE item_id IN ('QR-0911', 'QR-0912');",
                                      db=self.db))
        actual = {"sqlstate": result.sqlstate, "name": constraint_name(" ".join(result.errors)),
                  "rows_before": before, "rows_after": self.count("review_item"), "valid_rows_visible": visible}
        self.assertEqual(record("atomic_batch", actual), expected)

    # -- 2. idempotent intake --------------------------------------------------------------------
    def test_03_intake_stream_final_state(self):
        expected = load(EXP, "intake.json")
        outcomes = self.primary()
        actual = {"outcomes": outcomes, "message_count": self.count("intake_message"), "items": self.snapshot()}
        record("intake", actual)
        self.assertEqual(actual["outcomes"], expected["outcomes"])
        self.assertEqual(actual["message_count"], expected["message_count"])
        self.assertEqual(actual["items"], expected["items"])

    def test_04_redelivery_is_a_no_op(self):
        expected = load(EXP, "intake.json")
        session = self.app("lab-intake")
        deliveries = load(FIX, "intake_stream.json")["deliveries"]
        self.apply(session, deliveries, statement("intake.sql"))
        first = self.snapshot()
        replay = self.apply(session, deliveries, statement("intake.sql"))
        actual = {"replay_outcomes": replay, "replay_message_count": self.count("intake_message"),
                  "unchanged": self.snapshot() == first}
        record("replay", actual)
        self.assertEqual(actual["replay_outcomes"], expected["replay_outcomes"])
        self.assertEqual(actual["replay_message_count"], expected["replay_message_count"])
        self.assertTrue(actual["unchanged"], "a redelivered stream changed the state")

    def test_05_naive_upsert_regresses(self):
        """Wrong approach: last write wins. Late and repeated messages overwrite newer state."""
        expected = load(EXP, "naive.json")["items"]
        self.apply(self.app("lab-naive"), load(FIX, "intake_stream.json")["deliveries"], NAIVE_INTAKE)
        items = self.snapshot()
        actual = {k: {f: items[k][f] for f in ("defect_code", "severity", "source_seq", "version")} for k in expected}
        self.assertEqual(record("naive_upsert", actual), expected)
        guarded = load(EXP, "intake.json")["items"]
        self.assertNotEqual(actual["QR-0001"]["source_seq"], guarded["QR-0001"]["source_seq"])

    # -- 3. the work queue -------------------------------------------------------------------
    def test_06_claim_order_and_empty_queue(self):
        expected = load(EXP, "queue.json")
        self.primary()
        reviewer = self.app("lab-worker-a")
        order, claimed, decided = [], {}, {}
        for _ in range(len(expected["order"])):
            got = self.claim(reviewer, "R-101")
            self.assertEqual(got.sqlstate, "00000", got.lines)
            item_id, _, version = got.rows[0]
            order.append(item_id)
            claimed[item_id] = int(version)
            done = reviewer.run(statement("decide.sql"), {"item_id": item_id, "reviewer_id": "R-101",
                                                          "decision": "accept", "expected_version": version})
            self.assertEqual(done.sqlstate, "00000", done.lines)
            decided[item_id] = int(done.rows[0][3])
        empty = self.claim(reviewer, "R-101")
        actual = {"order": order, "claimed_versions": claimed, "decided_versions": decided,
                  "claim_when_empty": empty.rows}
        self.assertEqual(record("queue", actual), expected)

    def test_07_skip_locked_two_sessions(self):
        expected = load(EXP, "concurrency.json")["skip_locked"]
        self.primary()
        a, b = self.app("lab-worker-a"), self.app("lab-worker-b")
        got_a = a.run("BEGIN;\n" + statement("claim.sql"), {"reviewer_id": "R-101"})
        got_b = self.claim(b, "R-102")  # A's transaction is still open and holds QR-0001
        state_a = server().scalar("SELECT state FROM pg_stat_activity WHERE application_name = 'lab-worker-a';",
                                  db=self.db)
        self.assertEqual(a.run("COMMIT;").sqlstate, "00000")
        ready = int(server().scalar("SELECT count(*) FROM qr.review_item WHERE status = 'ready';", db=self.db))
        actual = {"a": got_a.rows[0] if got_a.rows else [], "b": got_b.rows[0] if got_b.rows else [],
                  "a_state_while_b_claimed": state_a, "ready_after": ready}
        self.assertEqual(record("skip_locked", actual), expected)

    def test_08_nowait_reports_the_lock_and_rollback_restores(self):
        expected = load(EXP, "concurrency.json")["nowait"]
        self.primary()
        a, b = self.app("lab-worker-a"), self.app("lab-worker-b")
        self.assertEqual(a.run("BEGIN;\n" + statement("claim.sql"), {"reviewer_id": "R-101"}).column(), ["QR-0001"])
        probe = b.run("SELECT item_id FROM qr.review_item WHERE item_id = 'QR-0001' FOR UPDATE NOWAIT;")
        self.assertEqual(a.run("ROLLBACK;").sqlstate, "00000")
        row = self.snapshot()["QR-0001"]
        actual = {"sqlstate": probe.sqlstate, "error": probe.errors[0] if probe.errors else "",
                  "after_rollback": {k: row[k] for k in ("status", "claimed_by", "version")}}
        self.assertEqual(record("nowait", actual), expected)

    def test_09_plain_for_update_waits_then_takes_next(self):
        """Without SKIP LOCKED the second worker queues behind the first; correct, but serialized."""
        expected = load(EXP, "concurrency.json")["blocking"]
        self.primary()
        blocking_claim = statement("claim.sql").replace("FOR UPDATE SKIP LOCKED", "FOR UPDATE")
        if blocking_claim == statement("claim.sql"):
            self.fail("claim.sql must lock the chosen row with FOR UPDATE SKIP LOCKED")
        a, b = self.app("lab-worker-a"), self.app("lab-worker-b")
        self.assertEqual(a.run("BEGIN;\n" + statement("claim.sql"), {"reviewer_id": "R-101"}).column(), ["QR-0001"])
        token = b.send(blocking_claim, {"reviewer_id": "R-102"})
        waited = server().wait_for_activity(db=self.db, app="lab-worker-b", column="wait_event_type", value="Lock")
        self.assertEqual(a.run("COMMIT;").sqlstate, "00000")
        got_b = b.collect(token)
        actual = {"b_wait_event_type": waited, "b_after_a_commit": got_b.rows[0] if got_b.rows else []}
        self.assertEqual(record("blocking", actual), expected)

    def test_10_unlocked_read_then_update_double_claims(self):
        """Wrong approach: read, then update, with no lock and no status check."""
        expected = load(EXP, "concurrency.json")["unlocked"]
        self.primary()
        a, b = self.app("lab-worker-a"), self.app("lab-worker-b")
        saw_a = a.run("BEGIN;\n" + UNLOCKED_PICK).column()
        saw_b = b.run("BEGIN;\n" + UNLOCKED_PICK).column()
        took_a = a.run(UNLOCKED_TAKE, {"reviewer_id": "R-101", "item_id": saw_a[0]})
        self.assertEqual(a.run("COMMIT;").sqlstate, "00000")
        took_b = b.run(UNLOCKED_TAKE, {"reviewer_id": "R-102", "item_id": saw_b[0]})
        self.assertEqual(b.run("COMMIT;").sqlstate, "00000")
        row = self.snapshot()[saw_a[0]]
        actual = {"a_saw": saw_a[0], "b_saw": saw_b[0], "a_rows": len(took_a.rows), "b_rows": len(took_b.rows),
                  "final_claimed_by": row["claimed_by"], "final_version": row["version"]}
        self.assertEqual(record("unlocked_double_claim", actual), expected)

    # -- 4. optimistic concurrency ----------------------------------------------------------------
    def test_11_optimistic_version_conflict(self):
        expected = load(EXP, "optimistic.json")
        self.primary()
        reviewer, supervisor = self.app("lab-reviewer"), self.app("lab-supervisor")
        claimed = self.claim(reviewer, "R-101").rows[0]
        form_version = claimed[2]  # what the reviewer's open form holds
        moved = supervisor.run("UPDATE qr.review_item SET claimed_by = 'R-103', claimed_at = now(), "
                               "version = version + 1 WHERE item_id = 'QR-0001' AND version = 3 RETURNING version;")
        decide = statement("decide.sql")
        stale = reviewer.run(decide, {"item_id": "QR-0001", "reviewer_id": "R-101", "decision": "accept",
                                      "expected_version": form_version})
        row = self.snapshot()["QR-0001"]
        wrong = reviewer.run(decide, {"item_id": "QR-0001", "reviewer_id": "R-101", "decision": "accept",
                                      "expected_version": row["version"]})
        final = supervisor.run(decide, {"item_id": "QR-0001", "reviewer_id": "R-103", "decision": "rework",
                                        "expected_version": row["version"]})
        actual = {"claimed": claimed, "reassigned_version": moved.column()[0] if moved.rows else "",
                  "stale_submit_rows": len(stale.rows), "wrong_reviewer_rows": len(wrong.rows),
                  "after_conflict": {k: row[k] for k in ("status", "claimed_by", "decision", "version")},
                  "final": final.rows[0] if final.rows else []}
        record("optimistic", actual)
        for key in actual:
            self.assertEqual(actual[key], expected[key], key)

    def test_12_last_write_wins_without_a_version(self):
        expected = load(EXP, "optimistic.json")
        self.primary()
        a, b = self.app("lab-supervisor-a"), self.app("lab-supervisor-b")
        naive_a = a.run("UPDATE qr.review_item SET severity = 3 WHERE item_id = 'QR-0003' RETURNING severity;")
        naive_b = b.run("UPDATE qr.review_item SET severity = 1 WHERE item_id = 'QR-0003' RETURNING severity;")
        after_naive = self.snapshot()["QR-0003"]
        guard_a = a.run("UPDATE qr.review_item SET severity = 3, version = version + 1 "
                        "WHERE item_id = 'QR-0004' AND version = 1 RETURNING version;")
        guard_b = b.run("UPDATE qr.review_item SET severity = 2, version = version + 1 "
                        "WHERE item_id = 'QR-0004' AND version = 1 RETURNING version;")
        after_guard = self.snapshot()["QR-0004"]
        actual = {
            "last_write_wins": {"a_rows": len(naive_a.rows), "b_rows": len(naive_b.rows),
                                "final_severity": after_naive["severity"], "final_version": after_naive["version"]},
            "guarded": {"a_rows": len(guard_a.rows), "b_rows": len(guard_b.rows),
                        "final_severity": after_guard["severity"], "final_version": after_guard["version"]}}
        record("last_write_wins", actual)
        self.assertEqual(actual["last_write_wins"], expected["last_write_wins"])
        self.assertEqual(actual["guarded"], expected["guarded"])

    # -- 5. isolation, as a two-session timeline -----------------------------------------------------
    def test_13_isolation_timeline(self):
        expected = load(EXP, "isolation.json")
        self.primary()
        a, b = self.app("lab-worker-a"), self.app("lab-worker-b")
        ready = "SELECT count(*) FROM qr.review_item WHERE status = 'ready';"
        rc_first = a.run("BEGIN;\n" + ready).column()[0]
        rc_claim = self.claim(b, "R-102").column()[0]
        rc_second = a.run(ready).column()[0]
        a.run("COMMIT;")
        rr_first = a.run("BEGIN ISOLATION LEVEL REPEATABLE READ;\n" + ready).column()[0]
        rr_claim = self.claim(b, "R-103").column()[0]
        rr_second = a.run(ready).column()[0]
        rr_update = a.run(f"UPDATE qr.review_item SET severity = 3 WHERE item_id = '{rr_claim}';")
        a.run("ROLLBACK;")
        rcu_first = a.run("BEGIN;\nSELECT severity FROM qr.review_item WHERE item_id = 'QR-0005';").column()[0]
        rcu_claim = self.claim(b, "R-104").column()[0]
        rcu_update = a.run("UPDATE qr.review_item SET severity = 3 WHERE item_id = 'QR-0005';")
        a.run("COMMIT;")
        row = self.snapshot()["QR-0005"]
        actual = {
            "read_committed": {"first_read": int(rc_first), "b_claimed": rc_claim, "second_read": int(rc_second)},
            "repeatable_read": {"first_read": int(rr_first), "b_claimed": rr_claim, "second_read": int(rr_second),
                                "update_sqlstate": rr_update.sqlstate,
                                "update_error": rr_update.errors[0] if rr_update.errors else ""},
            "read_committed_update": {"first_read_severity": int(rcu_first), "b_claimed": rcu_claim,
                                      "update_sqlstate": rcu_update.sqlstate, "final_status": row["status"],
                                      "final_claimed_by": row["claimed_by"], "final_severity": row["severity"],
                                      "final_version": row["version"]}}
        record("isolation", actual)
        for key in expected:
            self.assertEqual(actual[key], expected[key], key)

    # -- 6. authentication and least privilege on the local server ---------------------------------
    def test_14_wrong_password_is_rejected(self):
        expected = load(EXP, "security.json")
        pg = server()
        wrong = pg.run("SELECT current_user;", db=self.db, user=APP_ROLE, password="not-the-password",
                       app="lab-auth")
        right = pg.run("SELECT current_user;", db=self.db, user=APP_ROLE, password=STATE["app_password"],
                       app="lab-auth")
        stderr = re.sub(r"port \d+", "port <port>", wrong.stderr.strip())  # the port is random per run
        actual = {"wrong_password_exit": wrong.returncode, "wrong_password_stderr": stderr,
                  "right_password_user": right.stdout.strip()}
        record("authentication", actual)
        self.assertEqual(actual["wrong_password_exit"], expected["wrong_password_exit"])
        self.assertIn(expected["wrong_password_message"], actual["wrong_password_stderr"])
        self.assertEqual(actual["right_password_user"], expected["right_password_user"])

    def test_15_app_role_has_least_privilege(self):
        expected = load(EXP, "security.json")
        self.primary()
        app = self.app("lab-worker-a")
        attempts = [("delete review item", "DELETE FROM qr.review_item WHERE item_id = 'QR-0004';"),
                    ("update intake log", "UPDATE qr.intake_message SET source_seq = 9;"),
                    ("truncate intake log", "TRUNCATE qr.intake_message;"),
                    ("drop intake log", "DROP TABLE qr.intake_message;")]
        denied = []
        for label, sql in attempts:
            result = app.run(sql)
            denied.append({"statement": label, "sqlstate": result.sqlstate,
                           "error": result.errors[0] if result.errors else ""})
        actual = {"denied": denied, "rows_after": {"review_item": self.count("review_item"),
                                                   "intake_message": self.count("intake_message")}}
        record("least_privilege", actual)
        self.assertEqual(actual["denied"], expected["denied"])
        self.assertEqual(actual["rows_after"], expected["rows_after"])

    # -- 7. session state belongs to one connection ---------------------------------------------------
    def test_16_session_state_is_per_connection(self):
        """What a transaction-mode pooler or a closed idle connection takes away (PgBouncer itself is not run)."""
        expected = load(EXP, "session.json")
        self.primary()
        a, b = self.app("lab-worker-a"), self.app("lab-worker-b")
        a.run("CREATE TEMP TABLE draft_note (item_id text, note text);\n"
              "INSERT INTO draft_note VALUES ('QR-0001', 'check porosity map');\n"
              "SET search_path = qr, public;")
        a_draft = a.run("SELECT count(*) FROM draft_note;").column()[0]
        a_unqualified = a.run("SELECT count(*) FROM review_item;").column()[0]
        b_draft = b.run("SELECT count(*) FROM draft_note;")
        b_unqualified = b.run("SELECT count(*) FROM review_item;")
        a_lock = a.run("SELECT pg_try_advisory_lock(2301);").column()[0]
        b_lock_1 = b.run("SELECT pg_try_advisory_lock(2301);").column()[0]
        a.close()
        self.assertTrue(server().wait_until_gone(db=self.db, app="lab-worker-a"), "session A never ended")
        b_lock_2 = b.run("SELECT pg_try_advisory_lock(2301);").column()[0]
        actual = {"a_draft_rows": int(a_draft), "a_unqualified_rows": int(a_unqualified),
                  "b_draft_sqlstate": b_draft.sqlstate, "b_unqualified_sqlstate": b_unqualified.sqlstate,
                  "a_lock": a_lock, "b_lock_while_a_connected": b_lock_1, "b_lock_after_a_closed": b_lock_2}
        self.assertEqual(record("session_state", actual), expected)

    # -- 8. transfer: a different stream with a claim in the middle -----------------------------------------
    def test_17_transfer_stream(self):
        expected = load(EXP, "transfer.json")
        transfer = load(FIX, "transfer_stream.json")
        intake, worker = self.app("lab-intake"), self.app("lab-worker-a")
        outcomes = []
        for step in transfer["steps"]:
            if step["kind"] == "claim":
                outcomes.append("claimed:" + self.claim(worker, step["reviewer_id"]).column()[0])
            else:
                outcomes += self.apply(intake, [step], statement("intake.sql"))
        items = self.snapshot()
        count = self.count("intake_message")
        order = []
        for reviewer in transfer["follow_up_claims"]:
            got = self.claim(self.app(f"lab-follow-{reviewer.lower()}"), reviewer)
            order.append(got.column()[0] if got.rows else "")
        actual = {"outcomes": outcomes, "message_count": count, "items": items, "follow_up_order": order}
        self.assertEqual(record("transfer", actual), expected)


# ---- evidence ---------------------------------------------------------------------------------------
NOT_EXECUTED = [
    "Create a Lakebase project, its production branch and a compute (managed Lakebase was not used)",
    "Connect with an OAuth token for a Databricks identity; tokens expire after one hour and are checked at login",
    "Connect through Lakebase's managed PgBouncer pooler in transaction mode",
    "Apply schema.sql on a Lakebase child branch and compare it with the parent branch",
    "Point-in-time restore, or a branch created from a past point inside the project's restore window",
    "Create a synced table from a Unity Catalog table in snapshot, triggered or continuous mode",
    "Stream review_item changes to Unity Catalog with Lakehouse Sync (documented as Public Preview)",
    "Add Lakebase as a resource of a Databricks App and connect as the app's service principal role",
    "High-availability failover or reads from readable secondaries",
    "PgBouncer itself: session-state loss is shown with two direct local connections instead",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(paths) -> dict[str, str]:
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--evidence", help="write the evidence JSON to this path")
    parser.add_argument("--starter", action="store_true", help="judge starters/*.sql instead of solutions/*.sql")
    parser.add_argument("--pg-bin", help="directory holding postgres, initdb, pg_ctl and psql (PostgreSQL 16)")
    args = parser.parse_args()
    OPTIONS["sql_dir"] = ROOT / ("starters" if args.starter else "solutions")
    OPTIONS["pg_bin"] = args.pg_bin
    started = datetime.now(timezone.utc)
    clock = time.monotonic()
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)
    finished = datetime.now(timezone.utc)
    ok = result.wasSuccessful() and not result.skipped
    exit_code = 0 if ok else 1
    if args.evidence:
        sql_dir = OPTIONS["sql_dir"]
        evidence = {
            "lab": LAB,
            "executionClass": EXECUTION_CLASS,
            "executed": "local PostgreSQL 16 on one machine: a throwaway server on 127.0.0.1 driven through psql; "
                        "managed Lakebase NOT executed",
            "target": sql_dir.name,
            "python": platform.python_version(),
            "interpreter": sys.executable,
            "packages": {},
            "postgresql": {"serverBinary": STATE.get("server_version_line", ""),
                           "serverVersion": STATE.get("server_version", ""),
                           "psql": STATE.get("psql_version", ""),
                           "clusterOwner": STATE.get("cluster_owner", ""),
                           "authentication": "scram-sha-256 over 127.0.0.1; no Unix socket"},
            "platform": f"{platform.system()} {platform.release()}",
            "startedAt": started.isoformat(),
            "finishedAt": finished.isoformat(),
            "durationSeconds": round(time.monotonic() - clock, 3),
            "tests": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "exit": exit_code,
            "fixtureHashes": hashes(FIX.glob("*.json")),
            "expectedHashes": hashes(EXP.glob("*.json")),
            "solutionHashes": hashes([*sql_dir.glob("*.sql"), ROOT / "run_tests.py", ROOT / "pglocal.py"]),
            "outputHashes": {k: hashlib.sha256(canonical(v).encode()).hexdigest() for k, v in sorted(OUTPUTS.items())},
            "cleanup": {"serverStoppedAndDirectoryRemoved": bool(STATE.get("cleanup_ok", False))},
            "commands": [" ".join([sys.executable, *sys.argv])],
            "notExecuted": NOT_EXECUTED,
            "notes": ("Class P (platform-guide). Every SQL statement ran on a local PostgreSQL 16 server started for "
                      "this run with initdb and pg_ctl in a temporary directory, listening on 127.0.0.1 only with "
                      "SCRAM password authentication, and deleted afterwards. Two psql processes are two real "
                      "sessions. Expected literals were derived by hand (DATA.md) before the SQL ran. Nothing ran "
                      "on Databricks or Lakebase, and SQLite was not used."),
        }
        Path(args.evidence).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LabError as problem:
        print(f"lab setup failed: {problem}", file=sys.stderr)
        sys.exit(1)
