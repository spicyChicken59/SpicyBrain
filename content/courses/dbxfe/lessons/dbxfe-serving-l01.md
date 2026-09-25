<!-- section:dbxfe-serving-l01-outcome -->

After this lesson you can serve one registered version as a scored table and as an endpoint with a latency budget, trace a request across its identities, predict what the parser and the signature do to a body, size provisioned concurrency, release and roll back by traffic, read inference tables and a monitor as evidence, and keep drift a hypothesis until delayed labels test it. Nothing here runs against a workspace; every managed-serving example is labelled unexecuted.

<!-- section:dbxfe-serving-l01-start -->

Bring a version in Unity Catalog with a signature and an alias from [MLflow, experiments and reproducibility](#/module/dbxfe-mlflow), and point-in-time features from [Features, point-in-time correctness and data contracts](#/module/dbxfe-features): serving must use the training feature definitions. The example is fictional Cinderline Components' coating defect-risk model `cinderline.ml.defect_risk`: version 7 serves as `champion`, version 8 is a candidate. The plant makes about 3,000 parts a day over two shifts; a part scoring 0.35 or more is diverted to inspection.

<!-- section:dbxfe-serving-l01-paths -->

The nightly planner scores today's parts for tomorrow's inspection queue: nobody waits and the result is a Delta table. The end-of-line station needs one part's score within 200 ms while the part is on the belt: a caller waits and the result is JSON. **Batch inference** resolves the alias to a version number, scores the day's parts, and writes `defect_risk` beside `model_version`, `scored_at` and the run id, so a rerun can be told from the original. Version 7 was logged with the feature engineering client, so the job uses `score_batch`, which joins point-in-time features from the offline store to rows that carry only keys. `ai_query` can score from SQL, but its rows travel through the online endpoint. **Online serving** is a managed endpoint, `/serving-endpoints/defect-risk/invocations`, with one or more served entities behind it.

```python
# Batch scoring sketch; NOT executed in this build
fe = FeatureEngineeringClient()
scored = fe.score_batch(model_uri=f"models:/cinderline.ml.defect_risk/{version}", df=parts_with_keys)
# then add model_version, scored_at and run_id before writing
```

<!-- section:dbxfe-serving-l01-request -->

The station's request carries a service principal's token. The workspace checks it, the router picks a served entity by the traffic split, the body is parsed and the signature enforced, two features are looked up by `line_id` and `lot_id`, the model predicts, and `{"predictions": [0.42]}` returns. Synthetic timing: 4 ms authorization, 1 ms routing, 1 ms schema check, 12 ms lookup, 18 ms model, 5 ms network: 41 ms.

The **request contract** is the signature made external, enforced in two layers. The body is a JSON-serialized pandas DataFrame under `dataframe_split` or `dataframe_records` (tensors use `instances` or `inputs`). Open-source MLflow's server first parses it with the signature's types, so `61` or `"61"` becomes 61.0 and `"61%"` is refused as a bad request. Enforcement then matches names, refuses a missing required column, ignores an undeclared one and allows only lossless conversions. A renamed `coat_thickness_um` therefore fails every request before lookup or prediction. A null in a present column passes both layers and reaches the model.

<!-- section:dbxfe-serving-l01-capacity -->

**Provisioned concurrency** counts requests in flight; the documentation estimates the need as queries per second times model execution time. The station's 0.05 requests per second at 41 ms need 0.002 units of a Small endpoint's 4 (as read at search time). The planner's 3,000 parts at 60 per second and 80 ms would offer 4.8 units to 4: capacity is 50 per second, so a backlog of about 500 builds over the 50-second burst and station requests wait seconds. Scale to zero drops the floor to zero after 30 minutes idle; the next request waits for a cold start, usually ten to twenty seconds, sometimes minutes, with no SLA, so this endpoint stays provisioned. **Automatic feature lookup** fetches `line_defect_rate_8h` and `supplier_lot_reject_rate_30d` from an online store by key. A key the store lacks returns a null the model imputes, and the endpoint answers 200: a silent skew. Imputing zero there breaks the features module's missingness policy; an explicit no-score that the station handles by a written rule is the safer contract.

<!-- section:dbxfe-serving-l01-release -->

An endpoint can have at most ten served entities; its **traffic split** gives each a share. Version 8 joins version 7 at 10%; the inference table records which entity answered, so both are compared over the same windows. Promotion is 50% then 100%; version 7 stays deployed at 0% for seven days. Rollback is one configuration update, version 7 back to 100%, version 8 kept at 0% for diagnosis, done when the endpoint reports the configuration live. Deleting the old entity turns it into a redeploy.

<!-- section:dbxfe-serving-l01-evidence -->

An **inference table** logs each request as a row: time, status code, the request and response bodies, the served entity and execution time. Rows can take up to an hour to appear, so it explains incidents; the endpoint's exported metrics raise them. Unpacked, every prediction sits beside its inputs; joined to inspection results by `part_id`, some rows gain labels days later. The AI Gateway-enabled and legacy variants have different columns, so read the applicable page. A data profiling monitor (formerly Lakehouse Monitoring) with the inference profile writes a profile metrics table per window (counts, null rates, flagged rate) and a drift metrics table against a baseline such as the training table. Performance metrics such as precision appear only for windows whose label column is filled.

<!-- section:dbxfe-serving-l01-drift -->

**Drift** is a measured change in inputs or predictions. On day 1 of the humid season the monitor flags `humidity_pct`; on day 2 the flagged rate rises from 9% to 16%. Both are known; "the model is worse" is a hypothesis. **Delayed labels** from day 4 show precision on diverted parts 0.41 against 0.40 and audit recall unchanged: refuted, defects really rose. On day 20 a supplier's new lot coding made the lookup return nulls for 38% of parts and the flagged rate fell to 3%. After the pipeline fix and a batch rescore, 29 of 214 affected parts were recalled; labels on day 23 showed 12 defective parts had passed. Verified loss, caused by the pipeline, not a reason to retrain. Only diverted parts and a 5% audit sample get labels, about nine defective audit parts a day, so recall is estimated weekly and reported with its count.

<!-- section:dbxfe-serving-l01-incident -->

Classify an **incident** by the layer that produced its evidence: endpoint health (5xx, timeouts, latency with no request change), contract (a 4xx spike after a caller change), data and features (nulls, freshness, drift), or verified quality loss (labelled windows worse than baseline). Rollback by traffic answers the first class and, when a release preceded the loss, the last. The **operational scorecard** gives each measurement a source, owner, target and status: known, hypothesized, or unmeasurable until labels arrive. Cost follows provisioned hours whether or not requests arrive, batch job minutes, retained inference rows and the monitor's serverless compute; rates stay unknown until current pricing is checked.

<!-- section:dbxfe-serving-l01-example -->

The contract test is local and **NOT executed in this build**; it calls no endpoint and needs no workspace credentials once the version's model directory has been downloaded. It wraps the version's signature around a constant stand-in and sends JSON through open-source MLflow's request handler, testing the contract, not the model.

```python
# contract_test.py -- local, NOT executed here
import json, os, tempfile
import mlflow
from mlflow.exceptions import MlflowException
from mlflow.pyfunc import scoring_server

# A local copy of version 8's model directory, downloaded once by someone with workspace
# access: mlflow.artifacts.download_artifacts("models:/cinderline.ml.defect_risk/8",
# dst_path="defect_risk_v8") after mlflow.set_registry_uri("databricks-uc").
MODEL_DIR = "defect_risk_v8"
SIGNATURE = mlflow.models.get_model_info(MODEL_DIR).signature  # reads the MLmodel file only

class Twin(mlflow.pyfunc.PythonModel):
    def predict(self, context, model_input, params=None):
        return [0.5] * len(model_input)  # the contract, not the model

path = os.path.join(tempfile.mkdtemp(), "twin")
mlflow.pyfunc.save_model(path, python_model=Twin(), signature=SIGNATURE)
TWIN = mlflow.pyfunc.load_model(path)
SCHEMA = TWIN.metadata.get_input_schema()
COLS = [c.name for c in SCHEMA.inputs]
GOOD = ["P-4471", "L3", "K-22", 212.5, 3.2, 61.0, 48.7]

def post(cols, rows):
    body = json.dumps({"dataframe_split": {"columns": cols, "data": rows}})
    try:
        return scoring_server.invocations(body, "application/json", TWIN, SCHEMA).status
    except MlflowException as error:
        return error.get_http_status_code()

def test_signature_names_every_station_column():
    assert COLS == ["part_id", "line_id", "lot_id", "oven_temp_c",
                    "belt_speed_mpm", "humidity_pct", "coat_thickness_um"]

def test_valid_body_is_accepted():
    assert post(COLS, [GOOD]) == 200

def test_missing_column_is_refused():
    assert post(COLS[:-1], [GOOD[:-1]]) == 400

def test_renamed_column_is_refused():
    assert post(COLS[:-1] + ["thickness_um"], [GOOD]) == 400

def test_unit_suffix_is_refused():
    row = GOOD.copy()
    row[COLS.index("humidity_pct")] = "61%"
    assert post(COLS, [row]) == 400
```

Scorecard (synthetic values, during the humid season's day 2):

| Measure | Source | Owner | Target | Today | Status |
|---|---|---|---|---|---|
| P99 latency | endpoint metrics | platform | ≤120 ms | 52 ms | known |
| 4xx rate | endpoint metrics | station app | <0.1% | 0.02% | known |
| Flagged rate | monitor | model owner | 6–12% | 16% | known, out of band |
| Precision, diverted | labels (lag 1–3 d) | model owner | ≥0.35 | not yet | hypothesis |
| Recall, audit sample | labels (7 days) | quality | ≥0.60 | 0.63, 61 defects | known, small |
| Daily cost | billing | platform | budget | unknown | check pricing |

Runbook: contract test and batch replay; 10% gated on errors, P99 and flagged rate per entity; 50% once labels give precision; 100% with version 7 retained; rollback sets version 7 to 100%.

<!-- section:dbxfe-serving-l01-exercise -->

A firmware update sends `humidity_pct` as `"61%"` and adds a `shift` column, while the feature pipeline runs 90 minutes late. Predict the responses, the scorecard rows that move, each change's incident class and your first action; say what stays unknown until labels arrive, and what `"61"` would have changed.

<!-- section:dbxfe-serving-l01-solution -->

`"61%"` cannot be cast to a double at parsing, so every request returns 400 before prediction; `shift` alone would be ignored. The 4xx rate jumps, P99 may fall, diversions stop: a contract incident owned by the station app. First: revert the firmware or strip the unit on the caller's side; never widen the signature. The late pipeline serves a stale `line_defect_rate_8h` with 200s; freshness breaches its target, and any flagged-rate change is a data incident with a hypothesis attached. Whether it cost precision is unknowable until those windows' labels arrive. `"61"` would be cast and accepted by open-source MLflow's parser; the managed endpoint's behaviour is checked, not assumed.

<!-- section:dbxfe-serving-l01-mistakes -->

Routing batch traffic through the station's endpoint. Scale to zero under a latency budget. Testing the contract with a hand-built pandas frame instead of JSON. Widening the signature mid-incident. Deleting the old served entity on promotion. Reading drift as a quality verdict. Reporting precision as if every part had a label. Quoting cost without a dated pricing source.

<!-- section:dbxfe-serving-l01-sources -->

Databricks documentation on Model Serving, custom model endpoints and queries, serving multiple models, batch inference, inference tables, data profiling (formerly Lakehouse Monitoring), automatic feature lookup, training with feature tables, and endpoint health; MLflow's Model Signatures and Input Examples. Titles and URLs were confirmed by web search on 2026-09-23; page bodies were not fetched in this build. On 2026-09-25 two source files were read in their source repositories: the query call in the Databricks SDK for Python's API reference at its v0.141.0 tag, for the four input fields, the invocations path and the `predictions` response field; and open-source MLflow's scoring server at its v3.16.1 tag, for the input fields it accepts and how it parses them.

<!-- section:dbxfe-serving-l01-related -->

Before this: [MLflow, experiments and reproducibility](#/module/dbxfe-mlflow); [Features, point-in-time correctness and data contracts](#/module/dbxfe-features); [Start ML with a baseline and a valid target](#/lesson/dbxfe-m07-l01) for the action a score triggers. Alongside: the forecasting module for thresholds and inspection load, and the FinOps module for reading a bill.

<!-- section:dbxfe-serving-l01-revisit -->

Return when a payload changes, a release needs a gate, a monitor alerts, or someone asks whether the model got worse. Ask: which layer produced this evidence, what is known, what is hypothesized, and which labels would settle it.

