# Promotion checklist: scrap summary, test → prod

A promotion moves one reviewed commit from `test` to `prod`. It is not a copy
of files and not a re-run of notebooks. Every row needs its own evidence; a
green row earlier in the list is never evidence for a later one.

Status legend for this lab: **EXECUTED** (this package ran it locally),
**NOT RUN** (needs a workspace, a pipeline or a reviewer; not attempted),
**N/A HERE** (needs a Git hosting service).

| # | Gate | Evidence required | This lab |
|---|---|---|---|
| 1 | The change was made on a branch and merged to `main` through a pull request | the pull request, its diff and an approving review from someone other than the author | N/A HERE |
| 2 | Unit tests pass on the merge commit | CI log with the commit SHA and test counts | EXECUTED locally: 14 of 14 on the reviewed tree |
| 3 | Configuration parses and passes the local structure rules | checker output with zero findings | EXECUTED locally: 0 findings; 21 mutations each caught |
| 4 | Every target resolves to the intended parameters | resolved table; only catalog and schema differ between test and prod | EXECUTED locally |
| 5 | Dependencies and tools are pinned | `==` pins; CLI version printed in the pipeline log | pins checked locally; CLI version NOT RUN |
| 6 | `databricks bundle validate --strict --target test` passes as the test service principal | validate output naming the principal and the target | NOT RUN |
| 7 | `databricks bundle plan --target test` shows no unexpected delete or recreate | the saved plan, reviewed | NOT RUN |
| 8 | `databricks bundle deploy --target test` from the merge commit | deploy log with the commit SHA | NOT RUN |
| 9 | `databricks bundle run scrap_summary --target test` succeeds | run ID and result state | NOT RUN |
| 10 | Integration check of the test output | `scrap_summary.json` in the test volume compared with an expected summary | NOT RUN |
| 11 | Prod target reviewed: fixed root path, `run_as` service principal, `git.branch: main`, permissions | structure rules D4, H2, H3, H4 with zero findings, and a reviewer's sign-off | rules EXECUTED locally; sign-off NOT RUN |
| 12 | `validate` and `plan` for prod reviewed by a second person | plan output and approval record | NOT RUN |
| 13 | Deploy prod from the same commit SHA as test | deploy log; SHA equal to row 8's | NOT RUN |
| 14 | First prod run observed; rollback path known | run ID; the previous release's commit to redeploy if needed | NOT RUN |

What this lab can honestly claim: rows 2, 3 and 4 and the pin check in row 5
ran on one machine against synthetic data. Nothing was validated, deployed or
run on Databricks, so rows 6 to 14 remain open, whatever rows 2 to 4 say.
