# Cost-sensitivity worksheet (hypothetical)

**Every number in this worksheet is invented for learning.** Nothing here is a
price, a quote, a discount, a benchmark or a savings claim. Real figures
require current pricing for the actual cloud, region, edition and commercial
terms, with a date. Where you need a real number, write "check current
pricing" and name the source you would use.

- **Currency:** USD (hypothetical; treat as planning units).
- **Period:** fiscal Q3, 1 October to 31 December (one quarter). All lines are
  quarter totals unless marked one-time.
- **Units:** platform usage in USD per quarter; storage in USD per quarter for
  the stated TB; movement in USD per quarter; labour in partner-days × day rate;
  dual running as the quarter's share of an annual support contract.
- **Planning ceiling (from the CFO disclosure, exercise only):** 450,000 USD
  for the quarter, covering platform usage, data movement, partner labour and
  dual running. It is not authorization to spend.

## Inputs

| Line | Unit | Low | Base | High | Note |
|---|---|---:|---:|---:|---|
| P — platform usage (compute and platform units) for the new Northbrook workspace | USD / quarter | 60,000 | 95,000 | 150,000 | Depends on wave-1 scope, warehouse size, hours; no real rate used |
| S — object storage for migrated data | USD / quarter, ~4 TB | 1,500 | 3,000 | 6,000 | Includes retained raw copies during the parallel run |
| M — data movement (one-time bulk copy plus cross-cloud sharing egress) | USD / quarter | 2,000 | 6,000 | 15,000 | Egress rates are cloud- and region-specific; verify |
| D — dual running: Granite support, quarter's share | USD / quarter | 120,000 | 120,000 | 120,000 | Fixed in every case; the notice date makes it unavoidable this quarter |
| L — partner migration labour | partner-days × 1,400 USD/day | 60 days = 84,000 | 90 days = 126,000 | 130 days = 182,000 | Day rate hypothetical; internal salaries excluded |
| O — operations and training | USD / quarter | 15,000 | 25,000 | 40,000 | Runbooks, on-call setup, BI team enablement |

Formula: **Total = P + S + M + D + L + O**.

## Scenario 1 — Path B wave 1 plus governed coexistence (the model's provisional recommendation)

| | Low | Base | High |
|---|---:|---:|---:|
| Total | 282,500 | 375,000 | 513,000 |
| Against the 450,000 ceiling | 167,500 under | 75,000 under | 63,000 over |

Check the base case: 95,000 + 3,000 + 6,000 + 120,000 + 126,000 + 25,000 = 375,000.

The input that moves the high case past the ceiling is **L** (partner days).
The control is therefore the scope of wave 1, not the platform.

## Scenario 2 — "Everything on one platform in Q3" (the memo's assumption, base only)

| Line | Base | Note |
|---|---:|---|
| P | 300,000 | All Northbrook and Vale workloads plus dual environments |
| S | 12,000 | ~30 TB during transition |
| M | 46,000 | Bulk moves in both directions |
| D | 120,000 | Unchanged |
| L | 380 days = 532,000 | Not schedulable through the 8 December – 2 January blackout in any case |
| O | 110,000 | |
| **Total** | **1,120,000** | A number for a plan the calendar does not allow; shown so the comparison is explicit |

## Scenario 3 — "Do not migrate this workload yet" (Line Pulse, finance workloads, Tessaly)

| Item | Q3 incremental cost | Note |
|---|---:|---|
| Keeping Line Pulse and the finance workloads on Granite through Q3 | 0 | Line D is already paid for the quarter under every scenario |
| Keeping Tessaly's restricted data in the hall | 0 | The regulator process is outside this worksheet (excluded) |
| Real cost of "not yet" | the renewal term chosen on 31 December | Give notice (hard 31 March exit) or renew; term options unknown — ask procurement |

## Exclusions (stated, not estimated)

BI service licence renewal (30 June); contingency; internal salaries and
backfill; network circuits and private-connectivity charges; tax; the Tessaly
regulator process; any effect on Vale's committed-use agreement (amounts not
disclosed); decommissioning after the recovery window; any benefit or savings
figure, because no realized benefit has been measured.

## How to use it

Change one input at a time and recompute the total by the formula. Record
which input you changed, why, and what evidence would replace the guess.
Present the result as a range against the ceiling, never as a point estimate,
and never as a savings claim.
