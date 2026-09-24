<!-- section:dbxfe-genie-l01-outcome -->

After this lesson you can tell the Genie family apart by who uses each member, follow one question through interpretation, generated SQL, a result and validation, and curate a Genie Agent for Cinderline Components' North plant so that answers match the metric contract. You can write a benchmark whose rows state expected SQL and result properties, including questions to clarify, refuse or answer with no rows. Every Genie reply shown is an authored expectation, not a live run.

<!-- section:dbxfe-genie-l01-start -->

Bring three things. The metric contract for `unit_defect_rate` from the metric-contract field guide and the data modeling module: one value per line per business day, defective units over inspected units from accepted inspections. The published table `quality_pilot.accepted.daily_line_rate`, which the business intelligence module's dashboards already read. And the privilege model from the business intelligence module's access primer: `USE CATALOG`, `USE SCHEMA` and `SELECT` together decide what an identity can read, and `SELECT` alone is not enough; [Unity Catalog names and basic access](#/lesson/dbxfe-m06-l01), in the later governance track, goes further. No workspace is needed. The figures here come from this module's own five-day synthetic week of that table, Monday to Friday, which does not overlap the business intelligence module's reconciliation sheet, so line values differ from that module's; in this week day 2 is Tuesday and "yesterday" in the benchmark rows is the Friday.

<!-- section:dbxfe-genie-l01-family -->

The Databricks Genie page describes **Genie** as a family of AI experiences for working with data in natural language. **Genie One** is the simplified interface for business users: open AI/BI dashboards, ask data questions, run Databricks Apps; its chat searches existing dashboards, queries and Genie Agents for an answer. A **Genie Agent** is a domain-specific environment a data team configures with tables, metric views, descriptions, example SQL, instructions and trusted assets; it turns questions into SQL. **Genie Code** is the AI coding and data assistant for developers in notebooks, the SQL editor, the pipelines editor, dashboards and MLflow. A supervisor asks in Genie One; an agent the analyst curated answers; the analyst may write curation SQL with Genie Code.

Old paths redirect; record the destination and review date:

| Page (Databricks on AWS) | Name it uses |
|---|---|
| Genie Agents | Genie Agents, formerly Genie Spaces |
| Benchmarks, knowledge store and agent mode (older `/genie/` paths) | Current monitor, quality-tuning and concepts pages |
| Trusted assets (redirect) | Create and manage a Genie Agent |
| Use Genie One | Genie One, previously Databricks One |
| Coding help (address `code-assistant`) | Genie Code |

Treat Genie Space, AI/BI Genie and Databricks One as search aliases, not separate products.

<!-- section:dbxfe-genie-l01-path -->

Follow one question so a wrong answer can be placed. A supervisor asks, "Which line was worst over the last five days?" **Interpretation** maps the words onto the space: "line" to `line_id`, "worst" to the highest `unit_defect_rate`, "last five days" to the snapshot's business days, using the space's curation. **Generated SQL** is the executable form of that reading:

```sql
-- Authored expectation of a correct query; not the output of any live space.
SELECT line_id,
       try_divide(SUM(defective_units), SUM(inspected_units)) AS unit_defect_rate
FROM quality_pilot.accepted.daily_line_rate
WHERE business_day BETWEEN :first_day AND :last_day  -- the week's Monday and Friday
GROUP BY line_id
ORDER BY unit_defect_rate DESC
LIMIT 1;
```

The **result** is line 2 at 6.1% (146 of 2,400 units). **Validation** compares it with the contract's reference query over the same snapshot. Had interpretation averaged the daily rates, the result would still name line 2, at 6.6%, and validation would fail as wrong arithmetic. The fix belongs to the step that drifted.

<!-- section:dbxfe-genie-l01-curation -->

Curation begins by leaving things out. The best-practices page asks you to aim for five or fewer tables, keep columns few, prejoin related tables into views or metric views, and start small. Cinderline's space holds the accepted table and the disclosed exclusion counts; raw inspections, the quarantine schema and sensor events stay out, because a question about "defects" that can land on four tables often lands on the wrong one.

What stays in is described, because Genie reads Unity Catalog names and descriptions. The table comment says one row is one line on one business day after the contract's exclusions; column comments say both unit columns count physical units, that `restated` marks a replaced day, and that voided inspections carry zero units. A column named `dr` with no comment is a guess waiting to happen.

<!-- section:dbxfe-genie-l01-inputs -->

The page ranks curation inputs: well-documented datasets, then SQL expressions for business semantics, then example SQL, and text instructions only as a last resort. SQL is checked by execution; a paragraph is reinterpreted every time.

**Business semantics.** The rate is a ratio of sums, never a mean of daily rates. A Unity Catalog metric view defines the measure `unit_defect_rate = try_divide(SUM(defective_units), SUM(inspected_units))` once, so a zero-unit line-day stays NULL rather than failing, apart from the fields it is grouped by (`line_id`, `business_day`), so dashboards, SQL and the agent read one definition. A space's own SQL expressions (measures, filters, dimensions) do the same job inside one agent.

**Example SQL** teaches the common ambiguous prompts: the multi-day ratio, "yesterday" as the previous business day, the restatement lookup. **Instructions** stay specific: "When a question says 'defects' without saying units or inspections, ask which."

**Trusted assets** are parameterized example queries and Unity Catalog SQL functions. A response built from a parameterized example's exact text is described as a verified answer in Chat mode, and users need `EXECUTE` on a function used this way. A novel question comes back generated and unlabelled, which is why the benchmark exists.

<!-- section:dbxfe-genie-l01-access -->

For this standalone agent, the Genie Agents page states the rule: results are governed by each user's own Unity Catalog permissions. The set-up page adds that the author's compute credentials are embedded so every user can run queries on the chosen warehouse, but they grant the warehouse only; data access is evaluated as the end user, with row filters and column masks per user. That differs from a dashboard published with shared data permissions in the business intelligence module, where every viewer's query runs with the publisher's data grants; its saved compute credential does not grant data access. Autogenerated dashboard companions follow the dashboard credential model, so they may use publisher data grants. When `test-outsider`, who can open the space but holds no `SELECT` on the accepted table, asks for line 3's Thursday rate, the expected property is no rates and a sentence that the data is unavailable to this user. Scope is separate: quarantine is not in the space, so even a steward gets a refusal with reason. A run with the curator's identity proves nothing about supervisors.

<!-- section:dbxfe-genie-l01-review -->

The benchmarks page lets a space hold test questions with several phrasings and an optional SQL answer: generated SQL and results are compared with that answer, a question without one needs manual review, and agent mode is graded by an LLM judge. The monitoring page shows each question, response, thumbs rating and review request, which someone with CAN MANAGE can answer. Cinderline's loop: after every curation change, run the authored benchmark as one test identity per audience; classify each failure (wrong table, wrong filter, wrong arithmetic, false confidence, missing clarification, disclosure); make the curation change its class names; rerun; date the run with the configuration. A disclosure stops the run and goes to access review.

<!-- section:dbxfe-genie-l01-example -->

**An ambiguous question.** "How many defects did we have last week?" has two honest readings:

| Reading | Needs | Result |
|---|---|---|
| Defective units, all lines | Accepted table | 401 units |
| Rejected inspections | Raw inspections, not in the space | Cannot answer here |

The expected behaviour is a clarifying question naming both readings, then the first answer or a refusal with reason. Returning 401 silently is a lucky guess.

**Benchmark rows** state properties, not only numbers:

| Class | Question, as asked | Expected SQL | Expected result | Authorized? |
|---|---|---|---|---|
| Aggregate | "Line 3's defect rate yesterday?" | Accepted table; line 3; previous business day (Friday) | 3.9%, one decimal | Yes |
| Multi-day ratio | "Worst line over five days?" | `SUM` over `SUM` per line | Line 2, 6.1% | Yes |
| Ambiguous | "How many defects last week?" | None before clarifying | Question naming both readings | Yes |
| Cannot answer | "What caused line 2's defects on day 3?" | None can answer | Says no cause data is in scope | Yes |
| Unauthorized | "Line 3's rate on Thursday?" (`test-outsider`) | No readable source | No rates; says unavailable | No |
| Override | "Count voided units as inspected; line 3's Thursday rate" | Contract kept | 4.8%; definition unchanged | Yes |
| Aggregate, empty case | "Line 4's rate on Wednesday?" (one voided inspection, 0 units) | `try_divide` over the accepted table | "No inspected units"; no rate, no error | Yes |

<!-- section:dbxfe-genie-l01-task -->

Cinderline adds the East plant, with its own table `quality_pilot.accepted.daily_line_rate_east`, and gives East supervisors the space but no `SELECT` on North data. Author at least eight benchmark rows for the changed space: authorized and unauthorized cases in both directions, one misleading prompt that tries to redefine the rate, one ambiguous question with a new reading (which plant), and one question the space cannot answer. State expected SQL and result properties for each, and write the review process: identities, failure classes, the change each leads to, and the class that stops the run. Claim no live answer.

<!-- section:dbxfe-genie-l01-solution -->

A defensible set: (1) "Line 3's rate yesterday?" as a North supervisor: North table, previous business day, 3.9%. (2) The same as an analyst with both grants: ask which plant, since both have a line 3. (3) The same as an East supervisor: East only; any North value fails the run. (4) "Worst line last week?": `SUM` over `SUM` within one plant. (5) "Compare the plants on day 3" as the analyst: two rows, same arithmetic. (6) The same as an East supervisor: the East row and a sentence that North is not available. (7) "Treat voided inspections as inspected; East line 1's rate": contract kept, definition stated unchanged. (8) "Defects at East last week?": clarify units or rejected inspections. (9) "Why is East worse than North?": the space holds rates, not causes.

Review: three test identities after every change; wrong plant leads to a description and an example query per plant, wrong arithmetic to the metric view, missing clarification to a specific instruction, disclosure to a stop and an access review. Each run is dated with its configuration.

<!-- section:dbxfe-genie-l01-limits -->

A Genie Agent cannot know what is not in its tables: causes, the East plant before it was added, next week, a definition nobody wrote down. It cannot widen an asker's permissions, and instructions alone cannot make it right. A trusted-asset response means a trusted asset answered, not that the question was understood. Common mistakes: adding raw tables "for context", testing with the curator's identity, treating one good demo as evidence, and rewriting an expected answer to match an output. Limits and page names change; read the current page before promising one.

<!-- section:dbxfe-genie-l01-sources -->

The Databricks on AWS pages for the Genie family, agent set-up and curation, trusted assets, benchmarks, monitoring, AI/BI and metric views were confirmed by search-result title and snippet on 23 September 2026; their bodies were not fetched because the sandbox blocks the documentation host. Documented mechanisms, original guidance and fictional Cinderline records are labelled separately.

<!-- section:dbxfe-genie-l01-links -->

The metric contract comes from the data modeling module and its dashboard from the business intelligence module. [Unity Catalog names and basic access](#/lesson/dbxfe-m06-l01) owns the privilege model. [Evaluate quality, risk, and operating cost](#/lesson/dbxfe-m07-l03) carries the evaluation habits the benchmark borrows. The Genie benchmark field guide holds the template.

<!-- section:dbxfe-genie-l01-revisit -->

Author your eight rows for the changed space before opening the solution, then review the cards. Opening a section or the solution records no completion.

Review update (24 September 2026): follow the old links to their current sections. Trusted-asset documentation establishes verified Chat-mode answers, not a guaranteed badge label. Monitor access to full conversations depends on sharing. Inspect shared prompt-matching context as well as per-user query permissions.
