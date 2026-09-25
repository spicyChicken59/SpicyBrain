<!-- section:action -->

Diagnose from evidence you collected, in an order that keeps observation, guess and test apart. "It is slow" is a complaint; "queueing is 30 of 45 seconds at 8 a.m. and 0 at noon" is an observation you can act on.

1. **Record what was observed**: who experienced what, when, and the decomposed timeline (queueing, startup, execution, result transfer, rendering). Capture the query or job text, the input snapshot, the compute configuration, and whether results were cached.
2. **Collect the execution evidence**: the plan and profile or the stage and task view, with rows in and out per operator, bytes scanned, shuffle size, spill, and the slowest task against the median. Note what you could not see and why.
3. **Write one hypothesis** that the evidence points to, in a form a single observation could refute.
4. **Design one experiment** that changes one variable, holds the input and compute fixed, repeats the measurement at least three times, and includes a correctness check so a faster wrong answer is caught.
5. **Run it and record every observation**, including the ones that did not fit.
6. **Conclude with what is supported, what remains unproven, and what a production run would still have to show.**

Go deeper: [distributed execution and Spark evidence](#/module/dbxfe-spark-execution) for reading stages, shuffles, skew and spills, [SQL analytics and performance diagnosis](#/module/dbxfe-m05), [diagnose a slow query](#/lesson/dbxfe-m05-l02), [balance concurrency, latency and cost](#/lesson/dbxfe-m05-l03), and [compute choices and FinOps](#/module/dbxfe-finops) before proposing more capacity.

<!-- section:example -->

### Slow-workload diagnosis: Cinderline Components (fictional), nightly resolution job

All timings are fictional observations from a test environment on synthetic records; nothing here is a platform benchmark.

#### Observations

The nightly job that resolves inspections and corrections ran in about 6 minutes for the North plant alone. The night after the East plant's export was added, it ran 41 minutes, then 39 and 44 on the following two nights. The 7:30 a.m. report was late twice. Input grew from roughly 40,000 to 95,000 inspection rows per night and from 300 to 700 correction rows; the correction file format did not change. Compute was unchanged: job compute, four workers. No results are cached in this path.

Stage view for the 44-minute run: three stages; the second, the full outer join of inspections to corrections on `inspection_id`, took 38 minutes. Its plan showed a sort-merge join, adaptive execution on and no skew split. Within it, 199 of 200 tasks read about 320 rows each and finished in under 30 seconds; one task read 31,618 rows (4 MB, far below the 256 MB default at which adaptive execution splits a skewed partition), wrote 6.66 million, ran 37 minutes and spilled 2.1 GB. The first and third stages were unchanged from the fast nights.

What could not be seen: the East export's row-level content on the first slow night, because raw retention started the following night.

#### Hypothesis

One join key value carries a large share of the rows on both sides, so one partition does almost all the work and multiplies it: skew on `inspection_id`. The East export is suspected of filling `inspection_id` with a placeholder for rows not yet assigned, because the DBA mentioned that East assigns identifiers in a nightly batch; East's corrections may copy it. Tens of thousands of rows on one side and hundreds on the other under one key would produce exactly one slow, spilling task writing millions of rows.

#### Experiment

Variable changed: rows with the placeholder key are routed to quarantine before the join, as the change-data contract already requires for missing identity, instead of after it. Held fixed: the same retained input snapshot from the 44-minute night, the same job compute, the same code otherwise. Repeated three times. Correctness check: accepted per-line totals must equal the unmodified run's, and the quarantined records must be exactly the placeholder-key rows.

Before running, the retained East files were checked: 31,406 of 55,000 export rows and 212 of 400 correction rows carried `inspection_id` = `0`, and 31,406 × 212 is the slow task's 6.66 million. The hypothesis was now supported by input evidence, not only by the task shape.

#### Results

| Run | Total | Join stage | Slowest task | Spill | Correctness |
|---|---|---|---|---|---|
| Unmodified, retained input | 43 min | 38 min | 37 min | Yes | Reference |
| Modified, run 1 | 7 min | 2 min | 40 s | No | Totals equal; 31,618 quarantined |
| Modified, run 2 | 7 min | 2 min | 38 s | No | Equal |
| Modified, run 3 | 8 min | 2 min | 41 s | No | Equal |

#### Conclusion

Supported: the slowdown was skew from a placeholder join key in the East files, and routing missing-identity rows to quarantine before the join removes it on this input, with identical accepted totals. Not the cause: input volume as such, compute size, or the North plant's rows. Unproven: whether East's placeholder rows receive real identifiers later and should be re-admitted, which is a source-contract question for the DBA and the quality lead; whether production nights with three plants show other skewed keys; and whether the 7-minute figure holds on real volume, which only a measured production run can show. Not recommended: more workers, which would have shortened nothing for one task.

The 31,618 quarantined records are themselves a finding for the ingestion decision: more than half of East's export and of its corrections have no identity yet, and the report's exclusion count will say so until the source is fixed.

<!-- section:template -->

### Slow-workload diagnosis

#### Observations

- Who experienced what, when; the decomposed timeline (queue, startup, execution, transfer, render) with figures; query or job text; input snapshot; compute configuration; cache state.

#### Execution evidence

- Plan or stage view: operators, rows in and out, bytes scanned, shuffle size, spill, slowest task against the median; what could not be seen and why.

#### Hypothesis

- One sentence the evidence points to, phrased so a single observation could refute it; the input check that would support it before any experiment.

#### Experiment

- Variable changed; everything held fixed; number of repetitions; correctness check that a faster wrong answer would fail.

#### Results

| Run | Total | Dominant stage or phase | Slowest task or component | Spill or queue | Correctness |
|---|---|---|---|---|---|

#### Conclusion

- Supported; ruled out; unproven; what a production run would still have to show; what is not recommended and why.

<!-- section:limits -->

This diagnosis establishes a cause on the input and compute you tested, under the conditions you recorded; it cannot establish production behaviour, which differs in volume, concurrency, cache state and hardware, and it is not a benchmark of any platform. A single decomposed timeline is one observation, so a diagnosis without repetition is a hypothesis. The method finds the dominant delay, not every delay; a second bottleneck often appears once the first is removed. Execution evidence needs the permissions to view it, and a cached result may have no profile. Escalate when the evidence cannot be collected as the intended identity, when the correctness check fails after a change, or when the only proposed remedy is capacity nobody has shown to be the constraint.
