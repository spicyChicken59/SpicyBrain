<!-- section:dbxfe-features-l01-outcome -->

After this lesson you can take any feature value and say what it describes, when it became usable and which prediction may use it. You can build a point-in-time training set with an as-of join on availability time, handle missing values by cause with one policy for training and serving, refuse duplicate keys and drifted transformations with tests, and choose batch or online delivery from the decision it serves. Then you can map each mechanism onto Databricks Feature Store capabilities, with their preview and entitlement caveats, without letting platform names replace the reasoning.
<!-- section:dbxfe-features-l01-start -->

Bring the vocabulary of [Machine learning fundamentals](#/module/dbxfe-m07): a prediction time, a label horizon and leakage from fields written after the fact. [The prediction-time lesson](#/lesson/dbxfe-m07-l01) showed one reading that describes one moment and arrives later. This lesson does not repeat that; it follows readings as a scheduled job turns them into features, joins them to many labelled moments, serves them online and corrects them with late data. You need SQL joins and `GROUP BY`; the pandas code is explained where it appears. Machines, times and numbers are fictional and match Lab L18, which executes every example locally with pandas.
<!-- section:dbxfe-features-l01-feature -->

A feature is a value a transformation computes for one entity over one period. Cinderline's job turns each press's sensor readings into two-hour window rows. PR-02's readings at 08:30, 09:10 and 10:00 become one row: `machine_id` PR-02, `feature_time` 10:00 (the end of the window (08:00, 10:00]), `temp_mean_2h` 70.0, `vib_max_2h` 1.9, `reading_count_2h` 3 and `vib_count_2h` 2, because the 09:10 reading carried no vibration value. The entity key and the window end identify the row. Windows closed on the right keep the 10:00:00 reading in the window it closes; whichever convention you choose, training and serving must share it.
<!-- section:dbxfe-features-l01-times -->

The window end says what a row describes. It does not say when the row existed. The job publishes each window at the next run, 30 minutes after it closes, so the row for (08:00, 10:00] becomes readable at 10:30. Store that as `available_at` beside `feature_time`.

| time | event |
|---|---|
| 10:00 | window (08:00, 10:00] closes |
| 10:15 | PR-02 prediction |
| 10:30 | the 10:00 window is published |
| 14:15 | the 10:15 prediction's outcome is known |

Labels have their own times as well: a prediction time, and a later time when the outcome is known. PR-01 fails at 14:10, so its 11:00 prediction is a positive known at 14:10; a negative is known only when its four-hour horizon ends. A training set built at 17:00 excludes rows whose outcome is not yet known.
<!-- section:dbxfe-features-l01-join -->

A point-in-time join gives each labelled row the newest feature row of the same entity published at or before its prediction time:

```python
train = pd.merge_asof(labels.sort_values("prediction_time"),
                      features.sort_values("available_at"),
                      left_on="prediction_time", right_on="available_at",
                      by="machine_id", direction="backward")
```

PR-02 at 10:15 receives the 08:00 window (65.5, 135 minutes old); PR-03 at 10:20 receives nothing, because nothing of PR-03's had been published. Joining on `feature_time` instead hands both predictions the 10:00 windows, which did not exist until 10:30. A latest-value lookup, each machine's newest row as the table stands today, is right when serving and wrong for history: in the lab it was wrong for seven of eleven training rows. One caution: `merge_asof` on `available_at` alone returns the most recently published row; after an older window is republished it picks that older row, so the lab uses the explicit rule, newest window first and newest version second.
<!-- section:dbxfe-features-l01-missing -->

Decide by cause, and apply the same rule in both paths:

| cause | training | serving |
|---|---|---|
| no row yet | exclude, `none_available` | no score; fallback |
| older than the consumer's limit | exclude, `stale` | same limit |
| empty column in a present row | keep null | keep null, never 0.0 |
| fewer readings than expected | keep, flag `low_coverage` | same flag |
| unknown entity key | refuse | refuse |

Under a 180-minute limit, PR-03 at 13:00 is exactly 180 minutes old and usable; at 13:30 it is 210 and stale. The limit belongs to the consumer: a handover model that predicts at 10:00 and 12:00 with a 90-minute limit finds every row 120 minutes old, a cadence mismatch to fix in the schedule, not in the join.
<!-- section:dbxfe-features-l01-contract -->

A feature contract states keys, time meanings, units, null meaning, bounds and cadence, and code checks it. Duplicate entity-time rows are refused, because a join would otherwise pick by storage order: two rows for PR-01's 10:00 window give 77.0 or 99.0. On Databricks, primary keys are informational and not enforced, so the pipeline must check them. Late readings append versions instead of rewriting rows: PR-01's 09:50 reading lands at 11:05 and the 11:30 run publishes 78.0 beside the original 77.0. Only predictions after 11:30 see it. A lineage column, the latest ingestion time of a row's inputs, lets the contract refuse a backfill that stamps 10:30 on a row using an 11:05 reading.
<!-- section:dbxfe-features-l01-serving -->

Training/serving skew appears when serving computes a feature differently. Import one transformation in both paths; if a port is unavoidable, compare it with the training code on inputs containing every edge case. In the lab a port that buckets by window start and fills missing vibration with 0.0 agrees at 08:30 and differs at 10:30 on two windows. Delivery follows the decision: a 06:00 maintenance list is batch scoring over the offline table; a press-side alert needs an online lookup, and inputs known only in the request are computed on demand by one function shared with training. Each path has a silent failure to monitor: a skipped run, or a stalled sync.
<!-- section:dbxfe-features-l01-platform -->

Databricks Feature Store registers features in Unity Catalog; any Delta table there with a primary key can be a feature table, and a `TIMESERIES` key makes a time series feature table. `FeatureLookup(timestamp_lookup_key=...)` with `create_training_set` returns the latest value prior to each row's timestamp, and `lookback_window` excludes older values during training and batch inference. The glossary describes the timestamp key as the event time of the value, so store publication time there when values arrive late. Online Feature Stores sync feature tables for low-latency lookup, and Model Serving can look features up automatically; online inference uses the latest value regardless of the lookback window, so enforce age in the caller. Feature Views, declarative features that Databricks computes, are in Public Preview. Verify runtime, region and entitlement for every capability before designing on it.
<!-- section:dbxfe-features-l01-example -->

Take PR-02 at 10:15 and three ways to fill its features:

| join | row used | published | temp_mean_2h | verdict |
|---|---|---|---|---|
| on window end | 10:00 window | 10:30 | 70.0 | leak |
| latest row today | 10:00 window | 10:30 | 70.0 | leak |
| point-in-time | 08:00 window | 08:30 | 65.5 | correct, 135 min old |

The two leaky joins agree with each other here and still differ from what a live model saw. Only the availability comparison separates them.
<!-- section:dbxfe-features-l01-exercise -->

Using the lab's timeline, predict the result for PR-03 at 10:20, PR-03 at 13:30 and PR-01 at 11:45 after PR-01's late 09:50 reading arrives at 11:05 and version 2 of its 10:00 window is published at 11:30. For each, give the window used, its publication time, its age in minutes and its status under a 180-minute limit.
<!-- section:dbxfe-features-l01-solution -->

PR-03 at 10:20: no row, `none_available`, because PR-03's only window was published at 10:30. PR-03 at 13:30: the 10:00 window published at 10:30, 210 minutes old, `stale`, excluded from training and given the fallback in serving. PR-01 at 11:45: the 10:00 window's version 2, published at 11:30, 105 minutes old, `ok`, with 78.0 instead of 77.0; the 11:00 prediction keeps version 1, because at 11:00 the late reading had not arrived.
<!-- section:dbxfe-features-l01-mistakes -->

- Joining on the window end or on a 'current' view to build history.
- Filling blanks with 0.0, which is a measurement nobody made.
- Re-implementing the transformation for serving and testing it only on inputs without edge cases.
- Overwriting rows when late data arrives, which erases what was known and hides the leak.
- Trusting a declared primary key that the platform does not enforce.
- Treating a label as known before its horizon has passed.
- Assuming the lookback window also applies online.
<!-- section:dbxfe-features-l01-sources -->

Platform behaviour comes from Databricks' Feature Store, point-in-time feature join, Online Feature Store and constraint pages, confirmed by search on 2026-09-23 without fetching page bodies; availability varies by region, runtime and entitlement. Join semantics come from the pandas `merge_asof` reference, preprocessing discipline from scikit-learn's common pitfalls, and training-serving skew from Google's Rules of Machine Learning. Every Cinderline value is synthetic and was executed only in a local pandas lab; nothing ran in a Databricks workspace.
<!-- section:dbxfe-features-l01-related -->

[Machine learning fundamentals](#/module/dbxfe-m07) defines targets, splits and leakage; this lesson supplies the joins those splits depend on. The ingestion module's [record resolution lesson](#/lesson/dbxfe-record-resolution) handles duplicate and late deliveries before features are computed. The experiment-tracking and serving modules build on the training set and the online path described here; Lab L18 executes every example.
<!-- section:dbxfe-features-l01-revisit -->

In a week, redraw the timeline for one machine from memory: readings, window ends, publications, one late reading, two predictions and their label times. Then say which row each prediction uses and why the answer changes for only one of them after the late reading.
