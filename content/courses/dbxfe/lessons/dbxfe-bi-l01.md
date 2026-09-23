<!-- section:dbxfe-bi-l01-outcome -->

After this lesson you can plan a dashboard that Cinderline's North plant morning quality meeting acts on, and prove it shows the right numbers: a decision chain, defensible labels bound to the `unit_defect_rate` contract, filters and parameters, an access matrix with two doors, freshness in words, a metric view, the business-user surface, external BI tools, a storyboard and an acceptance script. Nothing here needs a workspace; the dashboard drawn is a labelled schematic, not product UI.

<!-- section:dbxfe-bi-l01-start -->

Bring SQL aggregation and a metric contract. [Build a metric people can trust](#/lesson/dbxfe-m05-l01) shows why two reports disagree, and [data modeling and metric contracts](#/module/dbxfe-modeling) writes the contract consumed here: `unit_defect_rate` v1, defective over inspected units of accepted inspections, per line per business day, one decimal, empty lines in words, restated days marked. [Design least-privilege access](#/lesson/dbxfe-m06-l02) supplies the grant vocabulary; Databricks SQL runs the queries on SQL warehouses.

<!-- section:dbxfe-bi-l01-decision -->

Start from the meeting. Supervisors meet at 8 a.m. and choose which line to investigate first: that is the **audience**, the **decision** and the **action**, and yesterday's `unit_defect_rate` per line is the **metric** that changes it. A tile on no link of that chain, such as a sensor average with no contract behind it, is removed before it is drawn.

A number is then defensible only with its label. The misleading draft reads "Defects 4.8" over an axis from 4.0 to 5.0, with no date. The defensible version carries five parts:

| Part | Misleading | Defensible |
|---|---|---|
| Axis | 4.0 to 5.0 | from 0, or truncation stated |
| Units | "Defects 4.8" | per cent of inspected units |
| Period | none | previous business day |
| Denominator | hidden | 12 of 250; 1 excluded |
| Freshness | none | covers Tuesday, published 06:32 |

Read the label aloud; if the sentence cannot be spoken, a part is missing.

<!-- section:dbxfe-bi-l01-binding -->

A tile inherits its contract. On day 4 the four lines inspected 300, 250, 250 and 240 units with 10, 15, 12 and 10 defective. The plant figure is 47 over 1,040, which is 4.5%; the mean of the four line rates is 4.6%, a number no contract defines. The per-line dataset starts from the line list and divides with `try_divide`, so an empty line returns NULL and the tile prints "no inspections" (or "no inspected units" when accepted inspections total zero units), never 0.0%.

Two controls change what a tile shows. A **field filter** narrows rows a dataset already returned: setting line to 3 hides the other lines and leaves the plant dataset, which has no line field, untouched. A **parameter** such as `:business_day` is substituted into the SQL before aggregation, so every dataset using it recomputes. Choose each deliberately and give none of them the job of a permission.

<!-- section:dbxfe-bi-l01-access -->

An AI/BI dashboard has its own permission levels, Can View, Can Run, Can Edit and Can Manage. The tables behind it carry Unity Catalog privileges. Neither grants the other.

At publish time the publisher chooses whose data permissions run the queries. With **shared data permissions**, the default, every viewer's query runs with the publisher's grants and viewers share one cache, so a filter is not a wall. With **individual data permissions**, each viewer's own grants decide and a viewer without SELECT sees no data. Cinderline publishes the morning page with individual permissions, so the matrix's grants protect the rows; a shared publisher would have to be a service principal granted only the accepted table, never a personal login.

| Principal | Page | Underlying data | Must not |
|---|---|---|---|
| north-reporting-analysts | Can View | SELECT accepted.daily_line_rate | Reach raw or quarantine rows |
| quality-stewards | Can View, quarantine link | SELECT accepted and quarantine | Edit the page |
| data team | Can Edit | its own grants | Publish a tile with no contract |
| sp-north-nightly | none | writes the accepted tables | Author or publish the page |
| everyone else | none | none | Open the page |

<!-- section:dbxfe-bi-l01-freshness -->

Freshness has two clocks: the period the numbers cover and the moment they were published. Say both at the top of the page: "Covers Tuesday. Published 06:32. Restated days are marked." When the nightly run has not published by 7:30, the same place reads "Not updated: showing Monday. See the operator note."; a report held for a conflict reads "Held: conflict under adjudication". That line is a tile reading the latest successful row of a publish-run table.

A dashboard schedule runs every dataset's SQL on a cadence, refreshes the shared cache for a page with shared data permissions, and can send snapshots to email, Slack or Microsoft Teams subscribers. It cannot produce rows the job has not published: if the job finishes at 08:20, a 06:30 snapshot posts Monday with no warning. Put the refresh after the job, for example as a dashboard task that follows the publishing task, and let the freshness line say when it did not.

<!-- section:dbxfe-bi-l01-semantic -->

A **metric view** is a Unity Catalog object, written in YAML, holding measures apart from dimensions. `unit_defect_rate` is defined once as the ratio of sums; a query asks `MEASURE(unit_defect_rate)` grouped by `line_id` and gets 4.8% for line 3, or with no grouping gets 4.5% for the plant, because the engine recomputes the ratio for each grouping. The contract then lives in the catalog, and every client reading the view computes it the same way; the page still renders the empty case and the restatement mark.

**AI/BI** names Databricks' dashboards together with Genie Agents and **Genie One**, previously Databricks One, the simplified interface where business users view dashboards, ask questions in natural language and use apps. A supervisor needs the consumer access entitlement, Can View and, because the page runs each viewer's grants, SELECT through their group; the page and its freshness line are the same object on every surface. Natural-language questions belong to the Genie module.

<!-- section:dbxfe-bi-l01-external -->

External tools read the warehouse, not the page. Each connects under its own identity, so Unity Catalog grants apply to that identity and nothing of the AI/BI page travels.

| Integration | Connects by | Runs as | Refresh |
|---|---|---|---|
| AI/BI page | datasets | viewer or publisher | schedule or task |
| Power BI | Partner Connect, hostname and HTTP path, Delta Sharing | its connection | DirectQuery live, or Import copy |
| Tableau | Partner Connect, manual, Tableau Cloud data sources | its data source | live, or extract |
| ODBC or JDBC client | the driver | its connection string | the client's own |

Power BI's Databricks connector supports DirectQuery, where each visual sends SQL and SQL warehouses are recommended, and Import, where the rows are copied and Power BI's own sharing decides who reads them. A metric view can be queried by SQL from any of them; a tool's own semantic model re-expresses the measure and needs its own acceptance row.

<!-- section:dbxfe-bi-l01-example -->

Each storyboard frame becomes an acceptance row.

| Frame | Time | Actor | Reads | Decides |
|---|---|---|---|---|
| 1 | 07:30 | Plant analyst | freshness line, tiles against the sheet | confirms, notes exclusions |
| 2 | 07:45 | Supervisors, phone | freshness line | trusts Tuesday or reads the note |
| 3 | 07:47 | Supervisors | four line tiles | line 2 first, 6.0% |
| 4 | 07:50 | Supervisors | line 2's day-2 mark | accepts 5.1%, previous 5.3% |
| 5 | 08:05 | Quality lead | excluded count, quarantine link | opens the inspection |

The acceptance script takes expected values from the five-day reconciliation sheet, never from the page: line 3, day 4 is 4.8%; line 2, day 2 counts 20 accepted, 1 excluded, 1 quarantined; line 2's day-2 mark shows previous 5.3% after the day-4 correction; line 4, day 5 reads "no inspections"; filtering to line 3 leaves the plant at 4.5%; a test analyst is refused the quarantine link; an outsider cannot load the page. The plant analyst, quality lead and security lead sign their rows. The first run failed one row, 0.0% for line 4, day 5; the fix went into the dataset.

<!-- section:dbxfe-bi-l01-exercise -->

The supplier's quality contact wants line 2's daily rate in the supplier's Tableau, and the operations director wants a snapshot of the page in the supervisors' Microsoft Teams channel at 07:40. Write the identity and grants each delivery needs, what each keeps or loses of the page, its freshness wording, and three acceptance rows with sources and signers.

<!-- section:dbxfe-bi-l01-solution -->

**Tableau.** The supplier's data source connects under its own identity, so it gets SELECT on a view returning only line 2, never the table. The page's permissions, filters and freshness line do not travel, so the Tableau view carries its own caption naming the business day and extract time, and extracts run after the nightly job.

**Teams snapshot.** A subscription sends a picture taken at send time, so it goes only after the job has published, with the freshness line inside the snapshot so a late morning says "Not updated" in the channel.

**Acceptance rows.** Line 2, day 4 in the supplier's view equals 6.0% from the reconciliation sheet (plant analyst). The supplier identity querying line 3 returns no rows (security lead). On the simulated late morning the 07:40 snapshot shows "Not updated: showing Monday" (quality lead).

<!-- section:dbxfe-bi-l01-mistakes -->

- Twenty tiles designed from the tables, and no decision.
- A plant tile averaging line rates, or a rolling average labelled daily.
- 0.0% for a line that did not run.
- A filter treated as security under shared data permissions.
- Publishing from a personal login with broad grants.
- A clock refresh before the job, stamped fresh over old rows.
- A Power BI or Tableau report assumed to inherit the page's permissions.
- Expected values copied from the page.

<!-- section:dbxfe-bi-l01-sources -->

Twenty Databricks documentation pages, from AI/BI, dashboards, sharing, filters, parameters, schedules, caching and the dashboard API to metric views, Genie One, Power BI, Tableau and the drivers, were confirmed by search-result title and snippet on 23 September 2026; their bodies were not fetched because the sandbox blocks the documentation host. Documented behaviour, original guidance and fictional Cinderline records are labelled separately; nothing was created or run.

<!-- section:dbxfe-bi-l01-related -->

[Data modeling and metric contracts](#/module/dbxfe-modeling) writes the contract and the metric view definition this lesson reads. [SQL analytics and performance diagnosis](#/module/dbxfe-m05) owns a slow page at the moment it is needed. [Unity Catalog and governance](#/module/dbxfe-m06) owns the privileges behind the access matrix. The Genie module takes the business user's natural-language questions over the same governed data.

<!-- section:dbxfe-bi-l01-revisit -->

Say without notes why the plant figure is 4.5%, not 4.6%; whose grants a viewer uses under each publishing choice; and what the page says when the job is late. Revisit any section you needed.
