"""Lab L08 acceptance runner. Local Apache Spark 4.0.4 in local[2] mode, UI disabled, offline.

    python run_tests.py --evidence <path>

A real Structured Streaming query reads a file-source landing directory into which the
fixture files are moved one at a time. Every assertion compares what Spark reported
(progress per micro-batch, the checkpoint's offset and commit logs, the state read back
with the state data source, the rows the foreachBatch sink received) against literals in
expected/*.json that were written by hand before the final run; expected/windows.json is
also re-derived by expected/derive_expected.py, which never imports Spark. Runs are
bounded (availableNow, or processAllAvailable then stop); there is no sleep anywhere.
Any failure, error or skip makes the exit status non-zero. Nothing ran on Databricks and
no number here is a timing. Spark's temporary files, checkpoints and outputs go to a
directory the runner creates and deletes.
"""
import sys

sys.dont_write_bytecode = True  # leave no __pycache__ inside the package

import argparse  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import platform  # noqa: E402
import shutil  # noqa: E402
import tempfile  # noqa: E402
import unittest  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from hashlib import sha256  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["SPARK_LOCAL_IP"] = "127.0.0.1"

from pyspark.errors import AnalysisException, StreamingQueryException  # noqa: E402

from expected.derive_expected import derive, watermarks_after_each_arrival  # noqa: E402
from solutions import streaming_restart as lab  # noqa: E402

LAB = "lab-l08-streaming-restart"
EXECUTION_CLASS = "local-executed"
ORDER = [a["file"] for a in lab.manifest()["arrivals"]]
OUTPUTS = {}


def expected(name):
    return json.loads((ROOT / "expected" / name).read_text(encoding="utf-8"))


WINDOWS = expected("windows.json")
SEQUENTIAL = expected("sequential.json")
BACKLOG = expected("backlog.json")
TRANSFER = expected("transfer.json")
JOIN = expected("join_restart.json")
NEGATIVE = expected("negative.json")
SETTINGS = expected("restart_settings.json")


def condition(exc):
    getter = getattr(exc, "getCondition", None)
    return getter() if getter else None


class StreamingRestartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_root = Path(tempfile.mkdtemp(prefix="lab-l08-"))
        (cls.temp_root / "local").mkdir()
        cls.spark = lab.build_session("SpicyBrain lab L08 acceptance", cls.temp_root / "local",
                                      cls.temp_root / "warehouse")
        cls.spark.sparkContext.setLogLevel("ERROR")
        cls.staging = cls.temp_root / "staging"
        # Scenario S shares one landing directory, one checkpoint and one downstream stub across tests 02-05.
        cls.s_landing = cls.temp_root / "s" / "landing"
        cls.s_checkpoint = cls.temp_root / "s" / "checkpoint"
        cls.s_sink = lab.DownstreamStub()
        cls.s_runs = []
        OUTPUTS["environment"] = {
            "spark": cls.spark.version, "master": "local[2]",
            "java": cls.spark._jvm.System.getProperty("java.version"),
            "settings_read_back": {k: cls.spark.conf.get(k) for k in (
                "spark.sql.shuffle.partitions", "spark.sql.session.timeZone",
                "spark.sql.streaming.noDataMicroBatches.enabled",
                "spark.sql.streaming.stateStore.providerClass")},
        }

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
        shutil.rmtree(cls.temp_root, ignore_errors=True)
        OUTPUTS["temp_dir_removed"] = not cls.temp_root.exists()

    # ------------------------------------------------------------------ helpers
    def run_s(self, name, landed, fail_on_window=None, quiet=False):
        """One availableNow run of scenario S's query on its one checkpoint (a restart after the first)."""
        for file_name in landed:
            lab.land(file_name, self.s_landing, self.staging)
        self.s_sink.fail_on_window = fail_on_window
        record = self.run_query(lab.line_windows(lab.read_events(self.spark, self.s_landing)),
                                self.s_checkpoint, self.s_sink, quiet)
        record.update(run=name, landed=list(landed))
        self.s_runs.append(record)
        return record

    def run_query(self, frame, checkpoint, sink, quiet=False, read_state=True):
        calls_before = len(sink.calls)
        if quiet:
            self.spark.sparkContext.setLogLevel("OFF")  # the injected failure is expected; keep its trace out of the log
        try:
            executed, error, idle = lab.run_available_now(frame, checkpoint, sink)
        finally:
            self.spark.sparkContext.setLogLevel("ERROR")
        calls = sink.calls[calls_before:]
        emitted = {c["batchId"]: c["rows"] for c in calls}
        batches = [dict(b, emitted=emitted.get(b["batchId"], [])) for b in executed]
        logs = lab.checkpoint_logs(checkpoint)
        state_after = ({str(b["batchId"]): lab.state_rows(self.spark, checkpoint, b["batchId"]) for b in executed}
                       if read_state else {})
        return {"batches": batches, "stateAfter": state_after, "offsets": logs["offsets"],
                "commits": logs["commits"], "sinkCalls": calls, "error": error,
                "idleReports": [{"batchId": p["batchId"], "inputRows": p["inputRows"]} for p in idle],
                "outboxAfter": {"naive": len(sink.naive_outbox), "keyed": len(sink.keyed_outbox)},
                "logs": logs}

    def assert_run(self, got, want):
        for key in ("batches", "stateAfter", "offsets", "commits"):
            self.assertEqual(got[key], want[key], f"{want['run']}: {key}")
        if "outboxAfter" in want:
            self.assertEqual(got["outboxAfter"], want["outboxAfter"], f"{want['run']}: outbox")

    @staticmethod
    def public(record):
        """The path-free part of a run record, for the evidence file."""
        out = {k: v for k, v in record.items() if k not in ("error", "logs")}
        out["error"] = None if record.get("error") is None else {"condition": condition(record["error"])}
        return out

    # -------------------------------------------------------------------- tests
    def test_01_fixtures_and_expected_are_consistent(self):
        derived = derive()
        for key in ("totals", "eventTimeTumbling", "processingTimeTumbling", "slidingEventTime"):
            self.assertEqual(WINDOWS[key], derived[key], f"expected/windows.json {key} differs from derive_expected.py")
        self.assertEqual(ORDER, ["01.json", "02.json", "03.json", "04.json", "05.json"])
        ids = [json.loads(line)["event_id"] for name in ORDER
               for line in (ROOT / "fixtures" / "arrivals" / name).read_text(encoding="utf-8").splitlines() if line]
        self.assertEqual(len(ids), 18)
        self.assertEqual(len(set(ids)), 18)
        # The hand-written watermark of each run's no-data batch is the largest event time so far minus the delay.
        five = [r["batches"][-1]["watermark"] for r in SEQUENTIAL["runs"] if r["run"].startswith("arrival-0") and r["run"] != "arrival-04-failure"]
        five.insert(3, SEQUENTIAL["runs"][3]["plannedNotCommitted"]["batchWatermark"])
        self.assertEqual(five, watermarks_after_each_arrival(5))
        fifteen = [r["batches"][-1]["watermark"] for r in TRANSFER["runs"]]
        self.assertEqual(fifteen, watermarks_after_each_arrival(15))
        # What scenario S emits, plus the one row it drops, plus the window still open, is the event-time truth.
        emitted = SEQUENTIAL["sink"]["table"]
        dropped = SEQUENTIAL["lateEvents"]["droppedTooLate"]["units"]
        still_open = sum(r["units"] for r in SEQUENTIAL["lateEvents"]["neverEmitted"])
        self.assertEqual(sum(r["units"] for r in emitted) + dropped + still_open, WINDOWS["totals"]["units"])
        OUTPUTS["fixture_provenance"] = {"events": len(ids), "units": WINDOWS["totals"]["units"], "arrivals": ORDER,
                                         "watermarks_5min": watermarks_after_each_arrival(5),
                                         "watermarks_15min": watermarks_after_each_arrival(15)}

    def test_02_sequential_arrivals_watermark_state_and_late_rows(self):
        for want in SEQUENTIAL["runs"][:3]:
            got = self.run_s(want["run"], want["landed"])
            self.assertIsNone(got["error"])
            self.assert_run(got, want)
        # e008 (09:05:00) was read in batch 2 under the 09:07:40 watermark: older than the watermark,
        # yet counted, because its window (end 09:10) was still open.
        batch2 = self.s_runs[1]["batches"][0]
        self.assertEqual(batch2["watermark"], "2026-09-14T09:07:40Z")
        self.assertEqual(self.s_runs[1]["batches"][1]["emitted"][1], {"window_start": "2026-09-14T09:00:00Z",
                                                                      "line": "L2", "units": 23, "events": 3})
        # e011 (09:03:00) arrived after its window had been emitted and evicted: counted as dropped,
        # and the emitted 09:00 L1 total stays 27, not the event-time truth of 36.
        batch4 = self.s_runs[2]["batches"][0]
        self.assertEqual(batch4["droppedLate"], 1)
        self.assertEqual(self.s_runs[1]["batches"][1]["emitted"][0]["units"], 27)
        # Each restart read only its own new file: the file-source log assigns one file per source offset.
        self.assertEqual(self.s_runs[2]["logs"]["sourceFiles"], {"0": ["01.json"], "1": ["02.json"], "2": ["03.json"]})
        OUTPUTS["sequential_first_three_runs"] = [self.public(r) for r in self.s_runs[:3]]

    def test_03_failure_after_downstream_effects_leaves_a_planned_batch(self):
        want = SEQUENTIAL["runs"][3]
        got = self.run_s(want["run"], want["landed"], fail_on_window=want["failOnWindow"], quiet=True)
        self.assertIsInstance(got["error"], StreamingQueryException)
        self.assertEqual(condition(got["error"]), want["failure"]["condition"])
        for text in want["failure"]["messageContains"]:
            self.assertIn(text, str(got["error"]))
        self.assert_run(got, want)
        self.assertEqual(got["sinkCalls"], want["sinkCalls"])
        planned = want["plannedNotCommitted"]
        logs = got["logs"]
        self.assertIn(planned["batchId"], logs["offsets"])
        self.assertNotIn(planned["batchId"], logs["commits"])
        self.assertEqual(logs["batchWatermark"][str(planned["batchId"])], planned["batchWatermark"])
        self.assertEqual(logs["batchSourceOffset"][str(planned["batchId"])], planned["sourceOffset"])
        OUTPUTS["sequential_failure_run"] = self.public(got)
        OUTPUTS["checkpoint_after_failure"] = {"offsets": logs["offsets"], "commits": logs["commits"],
                                               "batchWatermark": logs["batchWatermark"],
                                               "batchSourceOffset": logs["batchSourceOffset"]}

    def test_04_restart_replays_only_the_uncommitted_batch(self):
        replay_want, idle_want = SEQUENTIAL["runs"][4], SEQUENTIAL["runs"][5]
        failed_call = self.s_sink.calls[-1]
        replay = self.run_s(replay_want["run"], [])
        self.assertIsNone(replay["error"])
        self.assert_run(replay, replay_want)
        # Same batch id, same rows: the offset log's plan was replayed, not re-planned.
        self.assertEqual(replay["sinkCalls"], [failed_call])
        self.assertEqual(replay["logs"]["batchSourceOffset"]["7"], 3)
        idle = self.run_s(idle_want["run"], [])
        self.assertIsNone(idle["error"])
        self.assert_run(idle, idle_want)
        self.assertEqual(idle["sinkCalls"], [])  # nothing committed was processed again
        OUTPUTS["sequential_restart_runs"] = [self.public(replay), self.public(idle)]

    def test_05_new_file_after_restart_is_the_only_input(self):
        want = SEQUENTIAL["runs"][6]
        got = self.run_s(want["run"], want["landed"])
        self.assertIsNone(got["error"])
        self.assert_run(got, want)
        logs = got["logs"]
        for key in ("sourceFiles", "batchSourceOffset", "batchWatermark", "nextBatchWatermark"):
            self.assertEqual(logs[key], SEQUENTIAL["checkpoint"][key], key)
        sink = SEQUENTIAL["sink"]
        self.assertEqual([c["batchId"] for c in self.s_sink.calls], sink["callBatchIds"])
        self.assertEqual(self.s_sink.table_rows(), sink["table"])
        self.assertEqual(len(self.s_sink.naive_outbox), sink["naiveOutbox"])
        self.assertEqual(len(self.s_sink.keyed_outbox), sink["keyedOutbox"])
        keys = [m["key"] for m in self.s_sink.naive_outbox]
        self.assertEqual(sorted({k for k in keys if keys.count(k) > 1}), sink["duplicatedKeys"])
        self.assertEqual(got["stateAfter"]["9"], SEQUENTIAL["lateEvents"]["neverEmitted"])
        OUTPUTS["sequential_last_run"] = self.public(got)
        OUTPUTS["sequential_checkpoint"] = {k: logs[k] for k in ("offsets", "commits", "sourceFiles", "batchSourceOffset",
                                                                 "batchWatermark", "nextBatchWatermark")}
        OUTPUTS["sequential_sink"] = {"callBatchIds": [c["batchId"] for c in self.s_sink.calls],
                                      "table": self.s_sink.table_rows(),
                                      "naiveOutbox": self.s_sink.naive_outbox,
                                      "keyedOutbox": self.s_sink.keyed_outbox}

    def backlog_landing(self):
        """All five files landed (in manifest order, with their landing times) before any query starts."""
        landing = self.temp_root / "b" / "landing"
        if not landing.exists():
            for file_name in ORDER:
                lab.land(file_name, landing, self.staging)
        return landing

    def backlog_run(self, name):
        sink = lab.DownstreamStub()
        frame = lab.line_windows(lab.read_events(self.spark, self.backlog_landing()))
        return self.run_query(frame, self.temp_root / "b" / name, sink, read_state=False)

    def test_06_backlog_run_counts_the_row_the_sequential_run_dropped(self):
        got = self.backlog_run("checkpoint")
        self.assertIsNone(got["error"])
        self.assertEqual(got["batches"], BACKLOG["batches"])
        self.assertEqual(got["offsets"], BACKLOG["offsets"])
        self.assertEqual(got["commits"], BACKLOG["commits"])
        compared = BACKLOG["comparedWithSequential"]
        first = got["batches"][2]["emitted"][0]
        self.assertEqual((first["window_start"], first["line"], first["units"]),
                         (compared["window_start"], compared["line"], compared["backlogUnits"]))
        self.assertEqual(compared["backlogUnits"], WINDOWS["eventTimeTumbling"][0]["units"])
        # The late row's window end lies between the previous batch's watermark and this batch's.
        logs = got["logs"]
        self.assertEqual((logs["batchWatermark"]["1"], logs["batchWatermark"]["2"]),
                         ("2026-09-14T09:07:40Z", "2026-09-14T09:13:30Z"))
        OUTPUTS["backlog_run"] = self.public(got)

    def test_07_internal_setting_attributes_the_difference(self):
        check = BACKLOG["mechanismCheck"]
        key, value = check["setting"].split("=")
        self.spark.conf.set(key, value)
        try:
            got = self.backlog_run("checkpoint-mechanism")
        finally:
            self.spark.conf.set(key, "true")
        self.assertIsNone(got["error"])
        self.assertEqual(got["batches"][2], check["changedBatch"])
        for index in check["otherBatchesUnchanged"]:
            self.assertEqual(got["batches"][index], BACKLOG["batches"][index])
        OUTPUTS["backlog_mechanism_check"] = {"setting": check["setting"], "batches": got["batches"]}

    def test_08_transfer_fifteen_minute_watermark_delay(self):
        landing, checkpoint = self.temp_root / "t" / "landing", self.temp_root / "t" / "checkpoint"
        sink, runs = lab.DownstreamStub(), []
        for file_name, want in zip(ORDER, TRANSFER["runs"]):
            lab.land(file_name, landing, self.staging)
            frame = lab.line_windows(lab.read_events(self.spark, landing), delay=TRANSFER["delay"])
            got = self.run_query(frame, checkpoint, sink, read_state=False)
            self.assertIsNone(got["error"])
            self.assertEqual(got["batches"], want["batches"], want["run"])
            runs.append({"run": want["run"], "batches": got["batches"]})
        self.assertEqual(lab.state_rows(self.spark, checkpoint, 9), TRANSFER["stillOpenAfterLastRun"])
        compared = TRANSFER["comparedWithFiveMinutes"]
        self.assertEqual(len(sink.table), compared["windowsEmitted"]["fifteenMinutes"])
        self.assertEqual(len(SEQUENTIAL["sink"]["table"]), compared["windowsEmitted"]["fiveMinutes"])
        self.assertEqual(sink.table["2026-09-14T09:00:00Z|L1"]["units"], 36)
        OUTPUTS["transfer_runs"] = runs

    def test_09_processing_time_event_time_and_sliding_windows(self):
        got = lab.batch_windows(self.spark, self.backlog_landing())
        self.assertEqual(got["eventTimeTumbling"], WINDOWS["eventTimeTumbling"])
        self.assertEqual(got["processingTimeTumbling"], WINDOWS["processingTimeTumbling"])
        self.assertEqual(got["sliding"], WINDOWS["slidingEventTime"]["rows"])
        self.assertEqual(sum(r["units"] for r in got["sliding"]), 2 * WINDOWS["totals"]["units"])
        OUTPUTS["batch_windows"] = got

    def test_10_stream_static_join_stops_and_restarts(self):
        landing = self.temp_root / "j" / "landing"
        output, checkpoint = self.temp_root / "j" / "output", self.temp_root / "j" / "checkpoint"
        lines = lab.lines_table(self.spark)
        runs = []
        for want in JOIN["runs"]:
            for file_name in want["landedBeforeStart"]:
                lab.land(file_name, landing, self.staging)
            batches, active = lab.run_until_idle_then_stop(lab.enrich(lab.read_events(self.spark, landing), lines),
                                                           output, checkpoint)
            rows = self.spark.read.parquet(str(output)).count()
            self.assertEqual(batches, want["committedBatches"], want["run"])
            self.assertEqual(active, want["activeAfterStop"])
            self.assertEqual(rows, want["outputRows"])
            runs.append({"run": want["run"], "committedBatches": batches, "activeAfterStop": active, "outputRows": rows})
        result = self.spark.read.parquet(str(output))
        ids = sorted(r["event_id"] for r in result.select("event_id").collect())
        self.assertEqual(ids, JOIN["eventIds"])
        self.assertEqual(len(set(ids)), JOIN["distinctEventIds"])
        plants = {r["plant"]: r["count"] for r in result.groupBy("plant").count().collect()}
        self.assertEqual(plants, JOIN["rowsPerPlant"])
        log = sorted(int(p.name) for p in (output / "_spark_metadata").iterdir() if p.name.isdigit())
        self.assertEqual(log, JOIN["fileSinkLogBatches"])
        OUTPUTS["stream_static_join"] = {"runs": runs, "eventIds": ids, "rowsPerPlant": plants, "fileSinkLog": log}

    def test_11_append_without_watermark_is_refused(self):
        want = NEGATIVE["appendWithoutWatermark"]
        landing, checkpoint = self.temp_root / "n1" / "landing", self.temp_root / "n1" / "checkpoint"
        lab.land("01.json", landing, self.staging)
        frame = lab.line_windows_without_watermark(lab.read_events(self.spark, landing))
        with self.assertRaises(AnalysisException) as caught:
            frame.writeStream.outputMode("append").option("checkpointLocation", str(checkpoint)) \
                .foreachBatch(lab.DownstreamStub()).trigger(availableNow=True).start()
        self.assertEqual(condition(caught.exception), want["condition"])
        self.assertIn(want["messageContains"], str(caught.exception))
        self.assertEqual(lab.checkpoint_logs(checkpoint)["offsets"], [])  # refused before any batch was planned
        OUTPUTS["negative_append_without_watermark"] = {"exception": type(caught.exception).__name__,
                                                        "condition": condition(caught.exception)}

    def test_12_changed_aggregation_cannot_reuse_state(self):
        want = NEGATIVE["changedAggregationRestart"]
        landing, checkpoint = self.temp_root / "n2" / "landing", self.temp_root / "n2" / "checkpoint"
        sink = lab.DownstreamStub()
        for file_name in want["firstRun"]["landed"]:
            lab.land(file_name, landing, self.staging)
        first = self.run_query(lab.line_windows(lab.read_events(self.spark, landing)), checkpoint, sink, read_state=False)
        self.assertIsNone(first["error"])
        self.assertEqual(first["commits"], want["firstRun"]["commits"])
        lab.land("02.json", landing, self.staging)
        changed = self.run_query(lab.line_windows_with_largest(lab.read_events(self.spark, landing)), checkpoint, sink,
                                 quiet=True, read_state=False)
        self.assertIsInstance(changed["error"], StreamingQueryException)
        self.assertIn(want["messageContains"], str(changed["error"]))
        self.assertEqual(changed["offsets"], want["offsetsAfter"])
        self.assertEqual(changed["commits"], want["commitsAfter"])
        OUTPUTS["negative_changed_aggregation"] = {"exception": type(changed["error"]).__name__,
                                                   "condition": condition(changed["error"]),
                                                   "stateSchemaError": want["messageContains"] in str(changed["error"]),
                                                   "offsets": changed["offsets"], "commits": changed["commits"]}

    def test_13_restart_keeps_the_checkpointed_shuffle_partitions(self):
        want = SETTINGS
        landing, checkpoint = self.temp_root / "n3" / "landing", self.temp_root / "n3" / "checkpoint"
        sink = lab.DownstreamStub()
        for file_name in want["firstRun"]["landed"]:
            lab.land(file_name, landing, self.staging)
        first = self.run_query(lab.line_windows(lab.read_events(self.spark, landing)), checkpoint, sink, read_state=False)
        self.assertIsNone(first["error"])
        self.assertEqual(first["commits"], want["firstRun"]["commits"])
        self.assertEqual(first["logs"]["shufflePartitions"], want["firstRun"]["shufflePartitions"])
        self.spark.conf.set("spark.sql.shuffle.partitions", want["restart"]["sessionSetting"])
        try:
            for file_name in want["restart"]["landed"]:
                lab.land(file_name, landing, self.staging)
            second = self.run_query(lab.line_windows(lab.read_events(self.spark, landing)), checkpoint, sink,
                                    read_state=False)
        finally:
            self.spark.conf.set("spark.sql.shuffle.partitions", str(lab.SHUFFLE_PARTITIONS))
        self.assertIsNone(second["error"])
        self.assertEqual(second["batches"], want["restart"]["batches"])
        self.assertEqual(second["commits"], want["restart"]["commits"])
        self.assertEqual(second["logs"]["shufflePartitions"], want["restart"]["shufflePartitions"])
        self.assertEqual(second["logs"]["statePartitions"], want["restart"]["statePartitionDirectories"])
        OUTPUTS["restart_settings"] = {"sessionSetting": want["restart"]["sessionSetting"],
                                       "shufflePartitions": second["logs"]["shufflePartitions"],
                                       "statePartitions": second["logs"]["statePartitions"],
                                       "batches": second["batches"]}


def hashes(patterns):
    out = {}
    for pattern in patterns:
        for path in sorted(ROOT.glob(pattern)):
            if path.is_file():
                out[path.relative_to(ROOT).as_posix()] = sha256(path.read_bytes()).hexdigest()
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", help="write JSON evidence to this path")
    args = parser.parse_args()
    started = datetime.now(timezone.utc).isoformat()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(StreamingRestartTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finished = datetime.now(timezone.utc).isoformat()
    exit_status = 0 if result.wasSuccessful() and not result.skipped else 1
    if args.evidence:
        import py4j
        import pyspark
        environment = OUTPUTS.get("environment", {})
        evidence = {
            "lab": LAB,
            "executionClass": EXECUTION_CLASS,
            "runtime": "spark",
            "interpreter": sys.executable,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "java": environment.get("java", "unavailable"),
            "spark": environment.get("spark", pyspark.__version__),
            "master": "local[2]",
            "packages": {"pyspark": pyspark.__version__, "py4j": py4j.__version__},
            "sparkConfig": {"spark.ui.enabled": "false", "spark.ui.showConsoleProgress": "false",
                            "spark.driver.bindAddress": "127.0.0.1",
                            "spark.sql.shuffle.partitions": str(lab.SHUFFLE_PARTITIONS),
                            "spark.sql.session.timeZone": "UTC",
                            "spark.sql.streaming.statefulOperator.allowMultiple": "default (true); false in test 07 only",
                            "spark.sql.shuffle.partitions in test 13": "set to 3 in the session before a restart; the checkpoint's 2 was used",
                            "spark.local.dir": "a runner-created temporary directory, deleted after the run"},
            "startedAt": started,
            "finishedAt": finished,
            "tests": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "exit": exit_status,
            "fixtureHashes": hashes(["fixtures/*", "fixtures/arrivals/*", "expected/*"]),
            "solutionHashes": hashes(["solutions/*.py", "starters/*.py", "run_tests.py"]),
            "outputHashes": {key: sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()
                             for key, value in sorted(OUTPUTS.items())},
            "commands": ["python run_tests.py --evidence evidence.json", " ".join([sys.executable] + sys.argv)],
            "notes": ("Local Apache Spark 4.0.4 on one machine in local[2] mode with the web UI disabled, "
                      "spark.sql.shuffle.partitions=2 and the UTC session time zone. Real Structured Streaming "
                      "queries read a file-source landing directory into which the five fixture files were moved "
                      "one at a time; runs were bounded by trigger(availableNow=True), or by processAllAvailable() "
                      "then stop() for the stream-static join. Watermarks, state-row counts and late-row drops are "
                      "Spark's own progress reports; offsets and commits are read from the checkpoint; state rows "
                      "are read with the experimental state data source; downstream effects are local stubs. "
                      "Observed: a row older than the watermark was counted while its window was open; a row whose "
                      "window had been finalized was dropped in the one-file-at-a-time run but counted when the "
                      "same files were processed as a backlog, because late rows are filtered against the previous "
                      "micro-batch's watermark (confirmed in test 07 with an internal setting, never a "
                      "recommendation). Not executed: a stream-stream join, Kafka or other replayable message "
                      "sources, Delta Lake sinks, the RocksDB state store, continuous processing, clusters, and "
                      "anything on Databricks. No number here is a timing."),
            "observations": OUTPUTS,
        }
        Path(args.evidence).write_text(json.dumps(evidence, indent=1, default=str) + "\n", encoding="utf-8")
        print(f"evidence written to {args.evidence}")
    print(f"{result.testsRun} tests, {len(result.failures)} failures, {len(result.errors)} errors, "
          f"{len(result.skipped)} skipped; exit {exit_status}")
    sys.exit(exit_status)


if __name__ == "__main__":
    main()
