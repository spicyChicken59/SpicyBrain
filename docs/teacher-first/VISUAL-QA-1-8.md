# Visual QA: teaching modules 1–8

Reviewed 2026-09-20 in Chrome 153.0.8010.50 on Windows against the existing local static preview. All **67 diagrams and 128 authored states** were rendered at **1440 × 1000 in light mode** and **390 × 844 in dark mode**: 256 state/viewport cases. Each diagram was visually inspected through native-pixel contact sheets. Source hashes and per-state measurements are in the [full capture manifest](../evidence/teacher-first/visuals-1-8/capture-manifest.json); the [QA summary](VISUAL-QA-1-8.json) records scope and results.

The final automated sweep found **zero page horizontal overflow, clipped non-table labels, missing authored strings, JavaScript errors or external requests**. Essential diagram text remained at least 15 px; node labels were 20 px, values 22 px and table cells 16 px. CSS zoom and viewport scale stayed at 1. Mobile nodes reflowed vertically. Wide tables scrolled within a bounded, focusable region, with 79 additional scroll-position captures preserving the right columns. Small status labels and captions are separate from the essential-text minimum.

The review found and corrected two engine defects: screen-reader helper wording appeared beside arrows, and overflowing phone tables lacked a visible scrolling cue. The refreshed full sweep verifies the hidden helper and the overflow-only hint. The last content pass corrected missing spaces in SQL latency, Unity Catalog transfer and ML target/fit/lifecycle labels, with matching text equivalents; five visuals / 18 state/viewport cases were recaptured. Their nine phone states were inspected again. No IDs, questions, code, source claims or publication rules changed.

All 70 native contact sheets were reviewed across the initial and corrected sweeps. Final sheets were regenerated after the fixes; unchanged diagrams were not subjected to another full manual review. The [inspection record](../evidence/teacher-first/visuals-1-8/inspection-record.json) distinguishes visual review, automated checks and limitations. Full native evidence—335 PNGs, 70 native contact sheets and hashes—is retained locally outside the checkout at `../teacher-first-research/curriculum-1-8/visual-qa-native/`. The repository contains eight clearly labeled **reduced overviews**, four native examples and JSON evidence, totaling approximately 6.5 MiB.

| Module | Diagrams | States | Reduced overview |
|---|---:|---:|---|
| Platform | 8 | 12 | [Overview](../evidence/teacher-first/visuals-1-8/overview__dbxfe-m03.jpg) |
| Delta | 9 | 17 | [Overview](../evidence/teacher-first/visuals-1-8/overview__dbxfe-delta.jpg) |
| Transformations | 8 | 17 | [Overview](../evidence/teacher-first/visuals-1-8/overview__dbxfe-transformations.jpg) |
| Ingestion | 8 | 14 | [Overview](../evidence/teacher-first/visuals-1-8/overview__dbxfe-m04.jpg) |
| Orchestration | 8 | 16 | [Overview](../evidence/teacher-first/visuals-1-8/overview__dbxfe-orchestration.jpg) |
| SQL analytics | 8 | 17 | [Overview](../evidence/teacher-first/visuals-1-8/overview__dbxfe-m05.jpg) |
| Unity Catalog / security | 8 | 15 | [Overview](../evidence/teacher-first/visuals-1-8/overview__dbxfe-m06.jpg) |
| ML foundations | 10 | 20 | [Overview](../evidence/teacher-first/visuals-1-8/overview__dbxfe-m07.jpg) |

Native examples show the [Delta commit](../evidence/teacher-first/visuals-1-8/desktop-light__dbxfe-delta-commit-visual__after.png), [phone platform diagram](../evidence/teacher-first/visuals-1-8/phone-dark__dbxfe-m03-responsibilities-visual__request.png), [corrected consumer test](../evidence/teacher-first/visuals-1-8/phone-dark__dbxfe-m06-transfer-visual__accept.png) and [phone table scrolled to its result columns](../evidence/teacher-first/visuals-1-8/phone-dark__dbxfe-transformations-weighted-visual__aggregate__table-0-scroll-135.png).

Limits: this is one browser with two paired viewport/theme configurations, not a device matrix or every theme at each width. Element screenshots can exceed viewport height; normal vertical scrolling is expected. All desktop table content and representative phone scroll positions were visually reviewed; every authored cell string and scroll geometry was checked automatically. This pass does not establish enlarged-dialog keyboard behavior, screen-reader output, video playback, study-state persistence or real Databricks execution. Those app interactions have separate root-owned evidence. The screenshots contain only authored synthetic examples and an isolated browser state.
