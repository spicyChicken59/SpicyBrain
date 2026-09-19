import json
from solutions.reference import LocalPipeline

with open("fixtures/baseline.json", encoding="utf-8") as handle:
    baseline = json.load(handle)
with open("fixtures/batches.json", encoding="utf-8") as handle:
    correction = json.load(handle)["correction"]
pipeline = LocalPipeline()
pipeline.ingest(baseline)
old_id = pipeline.published["snapshot_id"]
try:
    pipeline.ingest(correction, fail_after="retained_raw")
except RuntimeError:
    pass  # Expected injected failure only, not a general error suppression policy.
assert pipeline.status == "stale_previous"
assert pipeline.published["totals"]["inspected_units"] == 20
pipeline.recover()
assert pipeline.published["totals"]["inspected_units"] == 22
assert pipeline.published["totals"]["defective_units"] == 1
assert pipeline.published["snapshot_id"] != old_id
pipeline.recover()
assert len(pipeline.outbox) == 2  # One local effect per distinct published snapshot.
