<!-- section:dbxfe-ai-assist-l01-outcome -->

After this lesson you can ask the workspace coding assistant to explain, draft, diagnose and test, then check each answer against something it did not produce. You can name the context it sends and what bounds it, keep confidential material out, write a checkable request, compute expected rows by hand, catch a many-to-many join that multiplies money, correct it from a documented source, and keep a record a reviewer can read. No workspace or AI tool is needed; every suggestion shown is authored and labelled, never captured product output.

<!-- section:dbxfe-ai-assist-l01-start -->

Bring SQL joins at the level of [Grain, joins, and execution behavior](#/lesson/dbxfe-grain-joins), the idea from [Unity Catalog names and basic access](#/lesson/dbxfe-m06-l01) that a principal sees only what it was granted, and a pencil: the fixture is five Cinderline order lines and six shipments, small enough to work on paper.

<!-- section:dbxfe-ai-assist-l01-names -->

Current Databricks pages title the workspace coding and data assistant **Genie Code**: it generates and runs code, builds pipelines and AI/BI dashboards, debugs errors and works with Unity Catalog data, in notebooks, the SQL editor, jobs, AI/BI dashboards and the file editor. The former name, **Databricks Assistant**, survives on *What is Databricks Assistant?* and *Use Databricks Assistant* for Google Cloud and on the AWS page *Tips to improve Databricks Assistant responses*; the former AWS FAQ and usage addresses are indexed as *Genie Code* and *Use Genie Code*. One product, two names; the Genie Code pages are newer where they differ. **Genie Agents**, formerly Genie spaces, are a different feature for business users' plain-English questions.

Every documented feature proposes; none decides: **Chat** answers with citations; **inline suggestions** complete code; **Quick Fix** proposes a correction for a basic error that you can accept and run; **Diagnose Error** analyses harder failures, including environment errors; **slash commands** wrap common prompts.

<!-- section:dbxfe-ai-assist-l01-context -->

To complete a task the assistant sends your prompt and relevant context to the model: table and column names, descriptions, the code you are working with, data samples from tables and cell outputs. You add context with **Add context** or `@resource_name`, and instruction files such as AGENTS.md above the open notebook are read too. The boundary is your own **Unity Catalog permissions**: the assistant can access only what you can, so a table you cannot SELECT contributes nothing and a draft over it is written blind.

The trust page covers the model side: partners retain nothing submitted, even for abuse monitoring, and submissions are not used to train generative foundation models Databricks offers to third parties. That is not permission to paste: a credential in a prompt sits in a transcript, and personal data and bulk records stay out unless a policy allows them. Attach a labelled sample, use placeholders for secrets, and record what was withheld.

<!-- section:dbxfe-ai-assist-l01-requests -->

A **bounded request** names the tables, the grain, the columns, the counting rules a draft could misread, and the expected row count on a fixture. The tips page asks for specific prompts, a stated structure and attached context; grain and count make the answer checkable. An authored pair:

| Request | What the model has to guess |
|---|---|
| "Write revenue by customer." | Which tables, how several lines and shipments per order are counted, what happens to unshipped orders, how many rows are right |
| "One row per customer from @sales.order_lines and @logistics.shipments: revenue = SUM(amount) counted once per line; shipped_qty counted once per shipment; an order may have several lines and zero or many shipments; keep unshipped orders; two rows expected on the attached fixture." | Almost nothing; a wrong answer is visibly wrong |

Other uses follow suit. **Explain**: ask about one cell, then trace one record. **Diagnose**: send the redacted error; ask for the cause first. **Test**: take the scaffolding, write the expected values yourself.

<!-- section:dbxfe-ai-assist-l01-verify -->

The fixture, `sales.order_lines` then `logistics.shipments` (synthetic and fictional):

| order_id | customer | amount |
|---|---|---|
| 1001 | Amberline Motors | 250 |
| 1001 | Amberline Motors | 150 |
| 1002 | Amberline Motors | 250 |
| 1003 | Brightwater Pumps | 900 |
| 1004 | Brightwater Pumps | 120 |

| shipment_id | order_id | shipped_qty | shipped_at |
|---|---|---|---|
| S1 | 1001 | 10 | 2026-09-01 |
| S2 | 1001 | 5 | 2026-09-03 |
| S3 | 1002 | 8 | 2026-09-02 |
| S4 | 1003 | 20 | 2026-09-04 |
| S5 | 1003 | 20 | 2026/09/05 |
| S6 | 1003 | 10 | 2026-09-06 |

**Expected, by hand, before any query runs.** Revenue belongs to order lines: Amberline 250 + 150 + 250 = 650, Brightwater 900 + 120 = 1020, total 1670. Quantity belongs to shipments: Amberline 10 + 5 + 8 = 23, Brightwater 20 + 20 + 10 = 50, total 73. Two rows; four orders reach the final grouping.

**AUTHORED wrong suggestion** (written for this lesson, not captured assistant output):

```sql
SELECT l.customer, SUM(l.amount) AS revenue, SUM(s.shipped_qty) AS shipped_qty
FROM sales.order_lines l
JOIN logistics.shipments s ON l.order_id = s.order_id
GROUP BY l.customer;
```

**AUTHORED misleading explanation**: "This joins each order line to its shipment and adds up the line amounts and shipped quantities per customer, giving total revenue and shipped quantity per customer." Trace order 1001: two lines meet two shipments, four rows. Trace 1004: no shipment, no row. The sentence hides both.

**Observed on the fixture**: Amberline 1050 / 38, Brightwater 2700 / 50; 8 joined rows against 4 orders. An inner join returns every matching pair, so a measure repeats once per match on the other side. Order 1001 is **many-to-many** (two lines × two shipments), so its amounts and quantities both double; 1003 is one-to-many, so 900 triples while its quantities stay right; 1004 disappears.

**Source-supported correction.** The JOIN reference: an inner join returns rows with matching values in both references; a left join returns all left rows, with NULL where there is no match. So reduce both tables to order grain, then left join:

```sql
WITH order_totals AS (
  SELECT order_id, customer, SUM(amount) AS amount
  FROM sales.order_lines GROUP BY order_id, customer
),
shipped AS (
  SELECT order_id, SUM(shipped_qty) AS shipped_qty
  FROM logistics.shipments GROUP BY order_id
)
SELECT o.customer, SUM(o.amount) AS revenue,
       SUM(COALESCE(s.shipped_qty, 0)) AS shipped_qty
FROM order_totals o
LEFT JOIN shipped s ON o.order_id = s.order_id
GROUP BY o.customer;
```

Observed: 650 / 23 and 1020 / 50, two rows, totals 1670 and 73. The check that catches the draft: `GROUP BY order_id HAVING COUNT(*) > 1` on each table returns 1001 for order lines and 1001, 1003 for shipments.

<!-- section:dbxfe-ai-assist-l01-review -->

The **review gate** is the same for a draft, a fix and a test: read the diff, run on the fixture, compare with the expected result, record, then accept or reject. The quarter cell filters with `CAST(shipped_at AS DATE)`, which raises CAST_INVALID_INPUT on S5's `2026/09/05` under ANSI mode, the documented default for accounts created on or after 19 October 2022. A suggested quick fix swaps in `try_cast`; the error disappears because `try_cast` returns NULL, so S5 fails the filter and Brightwater loses 20 units. The real fix parses each format explicitly and adds a no-NULL check. A generated test that asserts the draft's output is likewise a snapshot of the wrong answer.

The **assistance record** keeps the bounded request, context attached and withheld, a suggestion summary, expected and observed results, the verdict and the cited correction beside the code.

<!-- section:dbxfe-ai-assist-l01-example -->

The record, condensed. *Request* and *context*: the bounded request above, two tables attached, finance workbook, contact columns and token withheld. *Expected*: 650 / 23 and 1020 / 50, four rows after the join, totals 1670 and 73, with sources. *Observed*: 1050 / 38 and 2700 / 50, 1004 absent. *Verdict*: rejected; 1001 is two lines × two shipments. *Correction*: both sides to order grain, LEFT JOIN; JOIN reference cited; observed equals expected. *Error fix*: try_cast rejected, explicit parse accepted. *Unverified*: duplicates the fixture lacks.

<!-- section:dbxfe-ai-assist-l01-task -->

Cinderline adds `logistics.returns`, one row per returned batch (return_id, order_id, returned_qty): R1 for order 1001 (2 units), R2 and R3 for order 1003 (5 units each). A colleague asks the assistant for "net shipped quantity per order" and receives an authored draft that inner-joins shipments to returns on order_id and sums `shipped_qty - returned_qty` per order. Write the bounded request you would have sent, compute the expected net quantity for all four orders by hand, predict what the draft returns for orders 1001 and 1003 and which orders it omits, and give the corrected SQL with a test plan.

<!-- section:dbxfe-ai-assist-l01-solution -->

Request: "One row per order for every order_id in @sales.order_lines, over @logistics.shipments and @logistics.returns: net_qty = SUM(shipped_qty) − SUM(returned_qty), each summed to order grain first; zero or many of either per order; orders with none show 0; four rows expected."

Expected by hand: 1001 = 15 − 2 = 13; 1002 = 8; 1003 = 50 − 10 = 40; 1004 = 0; total 61.

The draft is many-to-many on 1003: 3 shipments × 2 returns = 6 rows, so 2 × 50 − 3 × 10 = 70. On 1001, 2 × 1 rows: 15 − 2 × 2 = 11. Orders 1002 and 1004 have no return, so the inner join omits them.

Corrected: take the order list from order lines, aggregate shipments and returns to order grain in two CTEs, LEFT JOIN both, and compute `COALESCE(shipped, 0) - COALESCE(returned, 0)`. Test plan: rows 4; 13, 8, 40, 0; total 61; each order_id once; per-key counts on both detail tables.

<!-- section:dbxfe-ai-assist-l01-limits -->

Common mistakes: treating a clean run as a test; saving the draft's first output as the expected result; accepting a fix because the error went away; pre-aggregating only one side of a many-to-many join, which leaves the other side's measure doubled for order 1001; reaching for DISTINCT, which collapses equal values rather than repeated pairs; pasting a whole notebook, secrets included.

Limits: only page titles and snippets were confirmed; every suggestion shown is authored; names, preview features and billing change; a passing fixture proves the query on the fixture only.

<!-- section:dbxfe-ai-assist-l01-sources -->

The pages Genie Code, Use Genie Code, Genie Code features and capabilities, Tips to improve Genie Code responses, What is Databricks Assistant?, Tips to improve Databricks Assistant responses, Databricks AI assistive features trust and safety, JOIN and try_cast function were confirmed by search title and snippet on 23 September 2026; bodies were not fetched because the sandbox blocks the host.

<!-- section:dbxfe-ai-assist-l01-links -->

[Grain, joins, and execution behavior](#/lesson/dbxfe-grain-joins) owns the join mechanics applied here. [Unity Catalog names and basic access](#/lesson/dbxfe-m06-l01) explains the privileges that bound the assistant's context. The analytical SQL module teaches window patterns a correction may use; the GenAI evaluation module judges model output against an oracle in general.

<!-- section:dbxfe-ai-assist-l01-revisit -->

Work the returns exercise on paper, then review the cards. Opening a section or revealing the solution records no completion; mark completion only when you choose.
