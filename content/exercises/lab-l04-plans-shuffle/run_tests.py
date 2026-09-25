"""Lab L04 acceptance runner. Local Apache Spark 4.0.4 in local[2] mode, UI disabled, offline.

    python run_tests.py --evidence <path>

Every test compares Spark's own output (plans, partition membership, executed
stages and tasks, shuffle records, rows) against literals authored independently
of the solution: expected/totals.json comes from plain-Python arithmetic over the
fixtures and expected/plans.json from written-down predictions. Any failure,
error or skip makes the exit status non-zero. Nothing here is a benchmark; wall
time is not an assertion anywhere. Spark's temporary files go to a directory the
runner creates and deletes.
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
from collections import Counter  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from hashlib import sha256  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["SPARK_LOCAL_IP"] = "127.0.0.1"

from pyspark.sql import functions as F  # noqa: E402

from expected.derive_expected import derive  # noqa: E402
from fixtures.generate_inspections import balanced_rows, plant_rows, skewed_rows  # noqa: E402
from solutions import execution_evidence as ev  # noqa: E402

LAB = "lab-l04-plans-shuffle"
EXECUTION_CLASS = "local-executed"
EXPECTED = json.loads((ROOT / "expected/totals.json").read_text(encoding="utf-8"))
PLANS = json.loads((ROOT / "expected/plans.json").read_text(encoding="utf-8"))
SKEWED = EXPECTED["skewed"]
HOT = SKEWED["hot_plant_rows"]
OUTPUTS = {}
READ_BACK = ("spark.sql.shuffle.partitions", "spark.sql.adaptive.enabled", "spark.sql.autoBroadcastJoinThreshold",
             "spark.sql.adaptive.coalescePartitions.enabled", "spark.sql.adaptive.coalescePartitions.minPartitionSize",
             "spark.sql.adaptive.advisoryPartitionSizeInBytes", "spark.sql.adaptive.skewJoin.enabled",
             "spark.sql.adaptive.skewJoin.skewedPartitionFactor",
             "spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes")


def writers(metrics):
    """Executed stages that only wrote shuffle output (map stages reading the input)."""
    return [s for s in metrics if s["shuffle_read_records"] == 0]


def readers(metrics):
    return [s for s in metrics if s["shuffle_read_records"] > 0]


class PlanAndShuffleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_root = Path(tempfile.mkdtemp(prefix="lab-l04-"))
        (cls.temp_root / "local").mkdir()
        cls.spark = ev.build_session("SpicyBrain lab L04 acceptance", local_dir=cls.temp_root / "local",
                                     warehouse_dir=cls.temp_root / "warehouse")
        cls.spark.sparkContext.setLogLevel("ERROR")
        cls.skewed = ev.load_inspections(cls.spark)
        cls.balanced = ev.load_inspections(cls.spark, "inspections_balanced.json")
        cls.plants = ev.load_plants(cls.spark)
        OUTPUTS["environment"] = {
            "spark": cls.spark.version, "master": "local[2]",
            "java": cls.spark._jvm.System.getProperty("java.version"),
            "defaultParallelism": cls.spark.sparkContext.defaultParallelism,
            "input_partitions": cls.skewed.rdd.getNumPartitions(),
            "settings_read_back": {key: cls.spark.conf.get(key) for key in READ_BACK},
        }

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
        shutil.rmtree(cls.temp_root, ignore_errors=True)
        OUTPUTS["temp_dir_removed"] = not cls.temp_root.exists()

    def setUp(self):
        # Every test starts from the same three settings; the adaptive tests change them deliberately.
        self.spark.conf.set("spark.sql.adaptive.enabled", "false")
        self.spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")
        self.spark.conf.set("spark.sql.shuffle.partitions", str(ev.SHUFFLE_PARTITIONS))

    def test_01_fixtures_and_expected_are_reproducible_and_independent(self):
        for name, regenerate in (("inspections.json", skewed_rows), ("inspections_balanced.json", balanced_rows),
                                 ("plants.json", plant_rows)):
            committed = json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))
            self.assertEqual(committed, regenerate(), f"{name} differs from its seeded generator")
        self.assertEqual(EXPECTED, derive(), "expected/totals.json differs from the plain-Python derivation")
        self.assertEqual(HOT, 180)  # the design constant every skew assertion below relies on
        self.assertEqual(SKEWED["row_count"], 240)
        OUTPUTS["fixture_provenance"] = {"skewed_rows": SKEWED["row_count"], "hot_plant": SKEWED["hot_plant"],
                                         "hot_plant_rows": HOT, "hot_share": SKEWED["hot_share"],
                                         "balanced_hot_share": EXPECTED["balanced"]["hot_share"]}

    def test_02_narrow_chain_has_no_exchange_and_one_stage(self):
        # The derivation's premise first: parallelize() cut the list into four contiguous slices.
        mix = ev.partition_key_rows(self.skewed, "plant")
        self.assertEqual({p: dict(sorted(m.items())) for p, m in mix.items()},
                         {s["partition"]: s["plants"] for s in SKEWED["input_slices"]})
        narrow = ev.narrow_chain(self.skewed)
        text = ev.plan_text(narrow)
        self.assertEqual(ev.outline_nodes(text), ["Project", "Filter", "Scan"])
        self.assertEqual(ev.count_nodes(text, "Exchange"), PLANS["narrow_chain"]["exchange_nodes"])
        self.assertEqual(narrow.rdd.getNumPartitions(), PLANS["narrow_chain"]["output_partitions"])
        rows, measured = ev.measure(self.spark, "narrow-collect", lambda: len(narrow.collect()))
        self.assertEqual(rows, SKEWED["defective_rows"])
        self.assertEqual(measured["jobs"], 1)
        self.assertEqual(measured["executed_stage_tasks"], PLANS["narrow_chain"]["executed_stage_tasks"])
        # Rows kept per partition equal the defective rows of each input slice: nothing moved.
        kept = ev.partition_rows(narrow)
        self.assertEqual(kept, {s["partition"]: s["defective_rows"] for s in SKEWED["input_slices"]})
        # Even count() is an aggregation: it ends with its own one-partition exchange.
        count_plan = ev.plan_text(narrow.groupBy().count(), "simple")
        self.assertIn("Exchange SinglePartition", count_plan)
        OUTPUTS["input_plant_mix"] = {str(p): mix[p] for p in sorted(mix)}
        OUTPUTS["narrow_plan"] = text
        OUTPUTS["narrow_measured"] = measured
        OUTPUTS["narrow_partition_rows"] = {str(p): n for p, n in sorted(kept.items())}
        OUTPUTS["count_plan"] = count_plan

    def test_03_grouped_totals_need_one_exchange_and_two_stages(self):
        totals = ev.plant_totals(self.skewed)
        jobs = ev.jobs_started_by(self.spark, "explain-only", lambda: ev.plan_text(totals))
        self.assertEqual(jobs, PLANS["grouped_totals"]["jobs_started_by_explain"])  # planning runs nothing
        text = ev.plan_text(totals)
        self.assertEqual(ev.count_nodes(text, "Exchange"), PLANS["grouped_totals"]["exchange_nodes"])
        self.assertIn(PLANS["grouped_totals"]["exchange_partitioning"], text)
        rows, measured = ev.measure(self.spark, "grouped-collect", lambda: ev.rows_dicts(totals, ["plant"]))
        self.assertEqual(rows, SKEWED["plant_totals"])
        self.assertEqual(measured["jobs"], 1)
        self.assertEqual(measured["executed_stage_tasks"], PLANS["grouped_totals"]["executed_stage_tasks"])
        self.assertEqual(measured["executed_stage_tasks"][-1], int(self.spark.conf.get("spark.sql.shuffle.partitions")))
        metrics = ev.stage_metrics(self.spark, measured)
        (map_stage,), (reduce_stage,) = writers(metrics), readers(metrics)
        # One partial row per plant per input partition crossed the Exchange, not 240 raw rows.
        self.assertEqual(map_stage["task_write_records"], [len(s["plants"]) for s in SKEWED["input_slices"]])
        self.assertEqual(reduce_stage["shuffle_read_records"], SKEWED["grouped_partial_rows"])
        self.assertLessEqual(sum(1 for n in reduce_stage["task_read_records"] if n), len(SKEWED["plant_totals"]))
        OUTPUTS["explain_only_jobs"] = jobs
        OUTPUTS["grouped_plan"] = text
        OUTPUTS["grouped_measured"] = measured
        OUTPUTS["grouped_stage_metrics"] = metrics
        OUTPUTS["grouped_rows"] = rows

    def test_04_sort_merge_join_needs_three_exchanges_and_four_stages(self):
        joined = ev.region_totals(self.skewed, self.plants)
        text = ev.plan_text(joined)
        nodes = ev.outline_nodes(text)
        self.assertIn(PLANS["sort_merge_join"]["join_operator"], nodes)
        self.assertNotIn("BroadcastHashJoin", nodes)
        self.assertEqual(ev.count_nodes(text, "Exchange"), PLANS["sort_merge_join"]["exchange_nodes"])
        rows, measured = ev.measure(self.spark, "sort-merge-collect", lambda: ev.rows_dicts(joined, ["region"]))
        self.assertEqual(rows, SKEWED["region_totals"])
        self.assertEqual(measured["jobs"], PLANS["sort_merge_join"]["jobs"])
        self.assertEqual(sorted(measured["executed_stage_tasks"]), PLANS["sort_merge_join"]["executed_stage_tasks_sorted"])
        metrics = ev.stage_metrics(self.spark, measured)
        # Both inputs cross the network in full: 240 fact rows and 3 dimension rows.
        self.assertEqual(sorted(s["shuffle_write_records"] for s in writers(metrics)),
                         sorted([SKEWED["dimension_rows"], SKEWED["row_count"]]))
        join = ev.busiest_reader(metrics)
        self.assertEqual(join["shuffle_read_records"], SKEWED["join_shuffle_read_rows"])
        self.assertGreaterEqual(max(join["task_read_records"]), HOT + 1)  # North's facts and its one dimension row
        OUTPUTS["sort_merge_plan"] = text
        OUTPUTS["sort_merge_measured"] = measured
        OUTPUTS["sort_merge_stage_metrics"] = metrics
        OUTPUTS["region_rows"] = rows

    def test_05_broadcast_join_removes_the_fact_side_shuffle(self):
        joined = ev.region_totals(self.skewed, self.plants, broadcast=True)
        text = ev.plan_text(joined)
        nodes = ev.outline_nodes(text)
        self.assertIn(PLANS["broadcast_join"]["join_operator"], nodes)
        self.assertNotIn("SortMergeJoin", nodes)
        self.assertEqual(ev.count_nodes(text, "Exchange"), PLANS["broadcast_join"]["exchange_nodes"])
        self.assertEqual(ev.count_nodes(text, "BroadcastExchange"), PLANS["broadcast_join"]["broadcast_exchange_nodes"])
        rows, measured = ev.measure(self.spark, "broadcast-collect", lambda: ev.rows_dicts(joined, ["region"]))
        self.assertEqual(rows, SKEWED["region_totals"])
        self.assertEqual(measured["jobs"], PLANS["broadcast_join"]["jobs"])  # one job builds the broadcast
        main = max(measured["detail"], key=lambda job: len(job["stages"]))
        self.assertEqual([s["tasks"] for s in main["stages"] if s["completed"] > 0],
                         PLANS["broadcast_join"]["main_job_executed_stage_tasks"])
        self.assertEqual(len(measured["executed_stage_tasks"]), len(OUTPUTS["sort_merge_measured"]["executed_stage_tasks"]) - 1)
        metrics = ev.stage_metrics(self.spark, measured)
        # Only the regional partial sums crossed a shuffle; no fact row did.
        self.assertEqual(sum(s["shuffle_write_records"] for s in metrics), SKEWED["regional_partial_rows"])
        self.assertEqual(sum(s["shuffle_read_records"] for s in metrics), SKEWED["regional_partial_rows"])
        OUTPUTS["broadcast_plan"] = text
        OUTPUTS["broadcast_measured"] = measured
        OUTPUTS["broadcast_stage_metrics"] = metrics

    def test_06_hot_key_never_splits_however_many_partitions(self):
        distributions = {}
        for partitions in (4, 8, 16):
            landed = ev.keyed_partition_rows(self.skewed, partitions, "plant")
            distributions[partitions] = landed
            self.assertEqual(sum(landed.values()), SKEWED["row_count"])
            self.assertLessEqual(len(landed), len(SKEWED["plant_totals"]))  # one key never occupies two partitions
            self.assertGreaterEqual(max(landed.values()), HOT)             # the hot key is a floor, not a target
            self.assertGreaterEqual(ev.skew_share(landed), SKEWED["hot_share"])
        self.assertEqual(min(max(d.values()) for d in distributions.values()), HOT)
        OUTPUTS["keyed_partition_rows"] = {str(k): {str(p): n for p, n in sorted(v.items())} for k, v in distributions.items()}
        OUTPUTS["keyed_partition_share"] = {str(k): ev.skew_share(v) for k, v in distributions.items()}

    def test_07_window_task_carries_the_hot_key_and_round_robin_does_not_fix_it(self):
        ranked = ev.rank_within_plant(self.skewed)
        text = ev.plan_text(ranked)
        self.assertIn("Window", ev.outline_nodes(text))
        self.assertEqual(ev.count_nodes(text, "Exchange"), PLANS["window"]["exchange_nodes"])
        landed = ev.partition_rows(ranked, keep=("rank_in_plant",))
        self.assertGreaterEqual(max(landed.values()), HOT)
        top = {r["plant"]: r["top"] for r in ranked.groupBy("plant").agg(F.max("rank_in_plant").alias("top")).collect()}
        self.assertEqual(top, {t["plant"]: t["rows"] for t in SKEWED["plant_totals"]})
        _, measured = ev.measure(self.spark, "window-collect", lambda: len(ranked.collect()))
        metrics = ev.stage_metrics(self.spark, measured)
        (window_stage,) = readers(metrics)
        self.assertEqual(window_stage["shuffle_read_records"], SKEWED["row_count"])  # every row moved, not partials
        self.assertEqual(max(window_stage["task_read_records"]), max(landed.values()))  # two measurements agree
        # The wrong approach: spread the input evenly first. The window's own exchange re-collects the key.
        spread = ev.rank_within_plant(self.skewed.repartition(16))
        text_spread = ev.plan_text(spread)
        self.assertIn("RoundRobinPartitioning(16)", text_spread)
        self.assertEqual(ev.count_nodes(text_spread, "Exchange"),
                         PLANS["window"]["exchange_nodes"] + PLANS["window"]["round_robin_adds_exchange_nodes"])
        landed_spread = ev.partition_rows(spread, keep=("rank_in_plant",))
        self.assertEqual(max(landed_spread.values()), max(landed.values()))
        self.assertGreaterEqual(max(landed_spread.values()), HOT)
        _, measured_spread = ev.measure(self.spark, "window-after-round-robin-collect", lambda: len(spread.collect()))
        metrics_spread = ev.stage_metrics(self.spark, measured_spread)
        # The extra shuffle moved all 240 rows once more, and the window task still read the hot key.
        self.assertEqual(sum(s["shuffle_write_records"] for s in metrics_spread), 2 * SKEWED["row_count"])
        (round_robin_stage,) = [s for s in readers(metrics_spread) if s["shuffle_write_records"] > 0]
        (window_after_stage,) = [s for s in readers(metrics_spread) if s["shuffle_write_records"] == 0]
        self.assertEqual(round_robin_stage["tasks"], 16)
        self.assertLess(max(round_robin_stage["task_read_records"]), HOT)  # evenly spread for one stage only
        self.assertEqual(max(window_after_stage["task_read_records"]), max(window_stage["task_read_records"]))
        OUTPUTS["window_plan"] = text
        OUTPUTS["window_partition_rows"] = {str(p): n for p, n in sorted(landed.items())}
        OUTPUTS["window_stage_metrics"] = metrics
        OUTPUTS["window_after_round_robin_plan"] = text_spread
        OUTPUTS["window_after_round_robin_partition_rows"] = {str(p): n for p, n in sorted(landed_spread.items())}
        OUTPUTS["window_after_round_robin_stage_metrics"] = metrics_spread

    def test_08_salting_spreads_the_hot_key_and_keeps_totals(self):
        salted = ev.salted_join(self.skewed, self.plants)
        text = ev.plan_text(salted)
        self.assertIn(PLANS["salted_join"]["join_operator"], ev.outline_nodes(text))
        self.assertEqual(ev.count_nodes(text, "Exchange"), PLANS["salted_join"]["exchange_nodes"])
        self.assertIn("salt", text)
        landed = ev.partition_rows(salted, keep=("region",))
        self.assertEqual(sum(landed.values()), SKEWED["row_count"])   # replication of the dimension added no fact rows
        self.assertLess(max(landed.values()), HOT)                      # the hot key is finally split
        self.assertGreaterEqual(max(landed.values()), SKEWED["max_salted_group_rows"])
        groups = sorted(({"plant": r["plant"], "salt": r["salt"], "rows": r["rows"]}
                         for r in salted.groupBy("plant", "salt").agg(F.count("*").alias("rows")).collect()),
                        key=lambda g: (g["plant"], g["salt"]))
        self.assertEqual(groups, SKEWED["salted_groups"])
        regions = ev.rows_dicts(salted.groupBy("region").agg(F.count("*").alias("rows"),
                                                              F.sum("inspected_units").alias("inspected")), ["region"])
        self.assertEqual(regions, SKEWED["region_totals"])
        # Once the key is split, more shuffle partitions can spread the twelve groups further.
        self.spark.conf.set("spark.sql.shuffle.partitions", "8")
        landed_8 = ev.partition_rows(ev.salted_join(self.skewed, self.plants), keep=("region",))
        self.assertEqual(sum(landed_8.values()), SKEWED["row_count"])
        self.assertLess(max(landed_8.values()), HOT)
        self.assertGreaterEqual(max(landed_8.values()), SKEWED["max_salted_group_rows"])
        OUTPUTS["salted_plan"] = text
        OUTPUTS["salted_partition_rows"] = {str(p): n for p, n in sorted(landed.items())}
        OUTPUTS["salted_share"] = ev.skew_share(landed)
        OUTPUTS["salted_partition_rows_at_8"] = {str(p): n for p, n in sorted(landed_8.items())}

    def test_09_adaptive_execution_coalesces_planned_partitions_at_runtime(self):
        self.spark.conf.set("spark.sql.adaptive.enabled", "true")
        totals = ev.plant_totals(self.skewed)
        before = ev.plan_text(totals, "simple")
        self.assertIn(PLANS["adaptive_grouped"]["before_action"], before)
        self.assertNotIn("AQEShuffleRead", before)
        self.assertIn("hashpartitioning(plant#", before)
        self.assertIn(f", {PLANS['adaptive_grouped']['planned_shuffle_partitions']})", before)
        rows, measured = ev.measure(self.spark, "adaptive-grouped-collect", lambda: ev.rows_dicts(totals, ["plant"]))
        self.assertEqual(rows, SKEWED["plant_totals"])
        after = ev.plan_text(totals, "simple")
        self.assertIn(PLANS["adaptive_grouped"]["after_action"], after)
        self.assertIn(PLANS["adaptive_grouped"]["runtime_node"], ev.final_plan(after))
        self.assertEqual(totals.rdd.getNumPartitions(), PLANS["adaptive_grouped"]["final_output_partitions"])
        self.assertEqual(measured["executed_stage_tasks"][-1], PLANS["adaptive_grouped"]["final_stage_tasks"])
        self.assertEqual(measured["executed_stage_tasks"][0], OUTPUTS["grouped_measured"]["executed_stage_tasks"][0])
        # The setting itself did not change; the runtime read the planned shuffle differently.
        self.assertEqual(self.spark.conf.get("spark.sql.shuffle.partitions"), str(ev.SHUFFLE_PARTITIONS))
        metrics = ev.stage_metrics(self.spark, measured)
        self.assertEqual(sum(s["shuffle_write_records"] for s in writers(metrics)), SKEWED["grouped_partial_rows"])
        (final_stage,) = readers(metrics)
        self.assertEqual(final_stage["task_read_records"], [SKEWED["grouped_partial_rows"]])
        OUTPUTS["adaptive_grouped_plan_before"] = before
        OUTPUTS["adaptive_grouped_plan_after"] = after
        OUTPUTS["adaptive_grouped_measured"] = measured
        OUTPUTS["adaptive_grouped_stage_metrics"] = metrics

    def test_10_adaptive_execution_switches_join_strategy_at_runtime(self):
        self.spark.conf.set("spark.sql.adaptive.enabled", "true")
        self.spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "10485760")  # Spark's documented default, 10 MB
        joined = ev.region_totals(self.skewed, self.plants)
        before = ev.plan_text(joined, "simple")
        self.assertIn("isFinalPlan=false", before)
        self.assertIn(PLANS["adaptive_join"]["initial_join_operator"], before)   # sizes unknown at planning
        rows, measured = ev.measure(self.spark, "adaptive-join-collect", lambda: ev.rows_dicts(joined, ["region"]))
        self.assertEqual(rows, SKEWED["region_totals"])
        after = ev.plan_text(joined, "simple")
        self.assertIn(PLANS["adaptive_join"]["final_join_operator"], ev.final_plan(after))
        self.assertIn(PLANS["adaptive_join"]["initial_join_operator"], ev.initial_plan(after))
        # Repeat the identical query on fresh DataFrames and record which side each run built.
        sides = [ev.build_side(ev.final_plan(after))]
        for _ in range(PLANS["adaptive_join"]["repeats"] - 1):
            fresh = ev.region_totals(self.skewed, self.plants)
            self.assertEqual(ev.rows_dicts(fresh, ["region"]), SKEWED["region_totals"])
            final = ev.final_plan(ev.plan_text(fresh, "simple"))
            self.assertIn(PLANS["adaptive_join"]["final_join_operator"], final)
            sides.append(ev.build_side(final))
        for side in sides:
            self.assertIn(side, PLANS["adaptive_join"]["possible_build_sides"])
        OUTPUTS["adaptive_join_plan_before"] = before
        OUTPUTS["adaptive_join_plan_after"] = after
        OUTPUTS["adaptive_join_measured"] = measured
        OUTPUTS["adaptive_join_build_side"] = sides[0]       # a runtime choice on toy sizes; not a scale claim
        OUTPUTS["adaptive_join_build_sides_repeated"] = sides
        OUTPUTS["adaptive_join_build_side_counts"] = dict(sorted(Counter(sides).items()))

    def test_11_cache_changes_the_plan_not_the_answer(self):
        north = self.skewed.filter(F.col("plant") == SKEWED["hot_plant"])
        before = ev.plan_text(north.groupBy("line").count())
        self.assertNotIn(PLANS["cache"]["cached_node"], before)
        north.cache()
        self.assertEqual(north.count(), HOT)
        cached = ev.plan_text(north.groupBy("line").count())
        self.assertIn(PLANS["cache"]["cached_node"], cached)
        self.assertIn(PLANS["cache"]["storage_level_fragment"], cached)
        self.assertEqual(ev.count_nodes(cached, "Exchange"), ev.count_nodes(before, "Exchange"))
        lines = ev.rows_dicts(north.groupBy("line").count(), ["line"])
        self.assertEqual(lines, SKEWED["hot_plant_line_counts"])
        north.unpersist()
        after = ev.plan_text(north.groupBy("line").count())
        self.assertNotIn(PLANS["cache"]["cached_node"], after)
        OUTPUTS["cache_plan_before"] = before
        OUTPUTS["cache_plan_cached"] = cached
        OUTPUTS["cache_plan_after_unpersist"] = after
        OUTPUTS["cache_lines"] = lines

    def test_12_bounded_collect_refuses_the_raw_frame(self):
        with self.assertRaisesRegex(ValueError, "collection bound exceeded"):
            ev.bounded_collect(self.skewed, 50)
        totals = ev.bounded_collect(ev.plant_totals(self.skewed), 50)
        self.assertEqual(sorted(totals, key=lambda r: r["plant"]), SKEWED["plant_totals"])
        self.assertEqual(self.skewed.count(), SKEWED["row_count"])  # the count never moved the rows
        OUTPUTS["bounded_collect"] = {"raw_frame_refused_at": 50, "aggregate_rows_collected": len(totals)}

    def test_13_balanced_transfer_same_operators_different_distribution(self):
        skewed_nodes = ev.outline_nodes(ev.plan_text(ev.plant_totals(self.skewed)))
        totals = ev.plant_totals(self.balanced)
        self.assertEqual(ev.outline_nodes(ev.plan_text(totals)), skewed_nodes)  # the plan cannot see skew
        self.assertEqual(ev.rows_dicts(totals, ["plant"]), EXPECTED["balanced"]["plant_totals"])
        landed = ev.keyed_partition_rows(self.balanced, 8, "plant")
        self.assertEqual(sum(landed.values()), EXPECTED["balanced"]["row_count"])
        self.assertGreaterEqual(max(landed.values()), EXPECTED["balanced"]["hot_plant_rows"])
        self.assertLess(ev.skew_share(landed), SKEWED["hot_share"])
        regions = ev.rows_dicts(ev.region_totals(self.balanced, self.plants, broadcast=True), ["region"])
        self.assertEqual(regions, EXPECTED["balanced"]["region_totals"])
        OUTPUTS["balanced_partition_rows"] = {str(p): n for p, n in sorted(landed.items())}
        OUTPUTS["balanced_share"] = ev.skew_share(landed)

    def test_14_adaptive_skew_join_splits_the_hot_partition_at_toy_thresholds(self):
        self.spark.conf.set("spark.sql.adaptive.enabled", "true")
        # At the default thresholds (256 MB, factor 5) nothing here is large enough to split.
        at_defaults = ev.region_totals(self.skewed, self.plants)
        default_rows, default_measured = ev.measure(self.spark, "adaptive-default-join-collect",
                                                    lambda: ev.rows_dicts(at_defaults, ["region"]))
        self.assertEqual(default_rows, SKEWED["region_totals"])
        default_after = ev.plan_text(at_defaults, "simple")
        self.assertIn(PLANS["adaptive_skew_join"]["initial_join_operator"], ev.final_plan(default_after))
        self.assertNotIn(PLANS["adaptive_skew_join"]["final_join_operator"], default_after)
        default_metrics = ev.stage_metrics(self.spark, default_measured)
        OUTPUTS["adaptive_default_join_plan_after"] = default_after
        OUTPUTS["adaptive_default_join_stage_metrics"] = default_metrics
        # One intervention: scale the two size thresholds down to toy size, then run the same query.
        for key, value in ev.TOY_SKEW_SETTINGS.items():
            self.spark.conf.set(key, value)
        try:
            joined = ev.region_totals(self.skewed, self.plants)
            before = ev.plan_text(joined, "simple")
            self.assertIn("isFinalPlan=false", before)
            self.assertIn(PLANS["adaptive_skew_join"]["initial_join_operator"], before)
            self.assertNotIn(PLANS["adaptive_skew_join"]["final_join_operator"], before)
            rows, measured = ev.measure(self.spark, "adaptive-skew-join-collect", lambda: ev.rows_dicts(joined, ["region"]))
            self.assertEqual(rows, SKEWED["region_totals"])
            after = ev.plan_text(joined, "simple")
            final = ev.final_plan(after)
            self.assertIn(PLANS["adaptive_skew_join"]["final_join_operator"], final)
            self.assertTrue(any("AQEShuffleRead" in line and PLANS["adaptive_skew_join"]["shuffle_read_marker"] in line
                                for line in final.splitlines()))
            metrics = ev.stage_metrics(self.spark, measured)
            join = ev.busiest_reader(metrics)
            planned = ev.busiest_reader(OUTPUTS["sort_merge_stage_metrics"])
            # The hot partition was read by more than one task, so the largest task read less.
            self.assertLess(max(join["task_read_records"]), max(planned["task_read_records"]))
            # Each piece of a split partition re-reads the matching dimension rows, so the total can only grow.
            self.assertGreaterEqual(join["shuffle_read_records"], SKEWED["join_shuffle_read_rows"])
        finally:
            for key in ev.TOY_SKEW_SETTINGS:
                self.spark.conf.unset(key)
        OUTPUTS["adaptive_skew_settings"] = dict(ev.TOY_SKEW_SETTINGS)
        OUTPUTS["adaptive_skew_plan_before"] = before
        OUTPUTS["adaptive_skew_plan_after"] = after
        OUTPUTS["adaptive_skew_measured"] = measured
        OUTPUTS["adaptive_skew_stage_metrics"] = metrics


def file_hash(path):
    return sha256(path.read_bytes()).hexdigest()


def hashes(patterns):
    files = sorted({p for pattern in patterns for p in ROOT.glob(pattern)
                    if p.is_file() and "__pycache__" not in p.parts})
    return {str(p.relative_to(ROOT)): file_hash(p) for p in files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", help="write JSON evidence to this path")
    args = parser.parse_args()
    started = datetime.now(timezone.utc).isoformat()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PlanAndShuffleTests)
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
                            "spark.sql.shuffle.partitions": str(ev.SHUFFLE_PARTITIONS),
                            "spark.sql.adaptive.enabled": "false (true in tests 09, 10 and 14 only)",
                            "spark.sql.autoBroadcastJoinThreshold": "-1 (10485760 in test 10 only)",
                            "spark.local.dir": "a runner-created temporary directory, deleted after the run"},
            "startedAt": started,
            "finishedAt": finished,
            "tests": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "exit": exit_status,
            "fixtureHashes": hashes(["fixtures/*", "expected/*"]),
            "solutionHashes": hashes(["solutions/*.py", "starters/*.py", "run_tests.py"]),
            "outputHashes": {key: sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()
                             for key, value in sorted(OUTPUTS.items())},
            "commands": ["python run_tests.py --evidence evidence.json", " ".join([sys.executable] + sys.argv)],
            "notes": ("Local Apache Spark 4.0.4 on one machine in local[2] mode with the web UI disabled and "
                      "spark.sql.shuffle.partitions=4. Adaptive execution, the broadcast threshold and, in test 14, "
                      "two adaptive size thresholds scaled to toy size are the only settings changed, one test at a "
                      "time. Plans, partition membership, stage/task counts and shuffle records (read from Spark's "
                      "status store, the store the web UI renders) are Spark's own output; no wall-clock time is "
                      "asserted or reported as a benchmark. Nothing ran on Databricks."),
            "observations": OUTPUTS,
        }
        Path(args.evidence).write_text(json.dumps(evidence, indent=1, default=str) + "\n", encoding="utf-8")
        print(f"evidence written to {args.evidence}")
    print(f"{result.testsRun} tests, {len(result.failures)} failures, {len(result.errors)} errors, "
          f"{len(result.skipped)} skipped; exit {exit_status}")
    sys.exit(exit_status)


if __name__ == "__main__":
    main()
