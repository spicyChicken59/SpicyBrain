<!-- section:action -->

Choose how another party gets to your data, or you to theirs, by comparing the alternatives on the same six questions. The wrong choice is usually the one that was easiest on the day and impossible to take back.

1. **State who needs what, in which direction, for what decision, and for how long.** A one-off analysis and a standing feed are different problems.
2. **For each direction, compare at least three alternatives in the same terms**: copying data to the reader, governed sharing where the data stays in place and the reader reads it under its owner's control, and query federation where the reader queries the owner's system in place. Two directions need two comparisons. Add a clean-room boundary only if neither party may see the other's rows.
3. **For each, answer six questions**: what moves and where it lands; who authorizes each read and where that is enforced; who pays for storage, compute and transfer, in kind rather than in money; how access is revoked and what the recipient keeps afterwards; how fresh the other party's view is; and what fails when the link breaks.
4. **Check the receiving side's tooling and the protocol's current name and support** against documentation before asserting either.
5. **Choose with conditions**, and rehearse revocation before the first real read.

Go deeper: [sharing, federation and interoperability](#/module/dbxfe-sharing), [Unity Catalog and governance](#/module/dbxfe-m06) with [design least-privilege access](#/lesson/dbxfe-m06-l02) for recipient scope, and [architecture reasoning](#/module/dbxfe-m08) for recording the decision.

<!-- section:example -->

### Sharing and federation choice: Cinderline Components and a fictional coatings supplier

Halvern Coatings, a fictional supplier, coats the parts on line 2; both parties, their systems and every figure are invented.

#### Who needs what

Halvern's process engineer wants Cinderline's per-inspection defect counts for line 2's coated parts, by coating batch, for 90 days and then weekly, to test whether a batch correlates with a defect cluster. Cinderline's quality lead wants the batch parameters for the same period. Neither party may see the other's unrelated data, and Cinderline's security lead requires that access can be withdrawn without asking Halvern to delete anything.

#### Alternatives compared, Cinderline to Halvern

| Question | Copy: weekly CSV transfer | Governed share of a filtered view | Federation: Halvern queries a Cinderline endpoint |
|---|---|---|---|
| What moves | A full filtered copy into Halvern's systems | Only query results, into Halvern's tools | Query results, per query, into Halvern's tools |
| Authorization | None after the file leaves | Recipient identity and share definition, enforced where served | An identity Cinderline issues, enforced by Cinderline's grants |
| Who pays, in kind | Cinderline's analyst time; Halvern's storage | Cinderline serves reads and transfer; Halvern's compute | Cinderline's compute per query |
| Revocation | Impossible; copies persist | Remove the recipient; saved results stay | Disable the identity; saved results stay |
| Freshness | Up to a week stale | Latest published version at each read | Live at each query |
| Failure behaviour | A missed transfer is a silent gap | Halvern's query fails with an error | Halvern's query fails |

#### Alternatives compared, Halvern to Cinderline

| Question | Extract: weekly file from Halvern | Share provided by Halvern | Federation: Cinderline queries Halvern's batch database |
|---|---|---|---|
| What moves | A weekly file into Cinderline's raw storage | Nothing copied; reads land in Cinderline's compute | Batch rows, per query, into Cinderline's compute |
| Authorization | Halvern's, before sending | Halvern's share definition | A credential Halvern issues, enforced by its database |
| Who pays, in kind | Halvern's export time; Cinderline's storage | Halvern serves reads | Load on Halvern's operational database |
| Revocation | Halvern stops sending; files stay | Halvern removes the recipient | Halvern revokes the credential |
| Freshness | Weekly, as often as parameters change | Halvern's latest version | Live at each query |
| Failure behaviour | A missed file shows in the arrival check | A broken share fails Cinderline's read | The query fails; load can slow Halvern's operations |

#### What each alternative cannot do

The copy cannot be revoked and records nothing of what Halvern read. The endpoint needs an external identity and inbound path Cinderline has never operated. The share needs tooling Halvern's engineer believes their notebooks support but has not tested, and cannot carry unpublished rows, so quarantined inspections are absent by design. Halvern has not confirmed tooling to publish a share, and its DBA declined federation's query load in writing on 18 March.

#### Decision

Cinderline to Halvern: a governed share of one view, `share.line2_coated_defects_by_batch`, limited to line 2, coated parts and 90 days, for Halvern's named identity, provided Halvern first reads a synthetic version from their own tooling. Halvern to Cinderline: a weekly extract of batch parameters, retained on arrival like any other source; parameters change weekly and neither alternative is available today. Protocol support and the recipient's tooling are confirmed against current documentation, and the protocol's name recorded as documented, not as remembered.

#### Revocation rehearsal

Before the first real read: create the recipient against synthetic rows, have Halvern read them, remove the recipient, and confirm Halvern's next query fails with an error naming the share. Record the time between removal and the failed read.

#### What would change this

If Halvern's tooling cannot read the share, the fallback is a weekly extract with a written retention limit, accepted as unrevocable and said so to the security lead. If the investigation becomes a standing joint analysis where neither side may see rows, a clean-room pattern is examined; nothing above establishes one.

<!-- section:template -->

### Sharing and federation choice

#### Who needs what

- Provider and recipient; direction; the decision served; one-off or standing; the constraints each side's security owner has stated.

#### Alternatives compared, one table per direction

| Question | Copy | Governed share (data stays in place) | Federation (query the other system in place) | Clean room, if applicable |
|---|---|---|---|---|
| What moves and where it lands | | | | |
| Who authorizes each read and where it is enforced | | | | |
| Who pays, in kind (storage, compute, transfer, people) | | | | |
| Revocation, and what the recipient keeps afterwards | | | | |
| Freshness of the recipient's view | | | | |
| Failure behaviour when the link breaks | | | | |

#### What each alternative cannot do

- The limits that rule an alternative out for this need, including tooling support not yet tested.

#### Decision

- The alternative per direction, the conditions attached, and the protocol and tooling facts still to be confirmed against documentation.

#### Revocation rehearsal

- The steps, the expected failure on the recipient's side, and the time measured.

#### What would change this

- Observations that switch the choice and the fallback each leads to.

<!-- section:limits -->

This choice compares alternatives on movement, authorization, cost in kind, revocation, freshness and failure; it cannot establish what a protocol or product supports today, which needs current documentation and a test with the recipient's own tooling, nor any monetary cost, which needs a worksheet with sources. It does not create the legal or contractual basis for sharing, does not classify the data, and does not make a recipient's environment trustworthy. Revocation is proven by rehearsal, not by design. A clean room is named as a boundary, not described. Escalate when a recipient cannot read a synthetic share from their own tooling, when the security owner has not classified the rows in the view, or when the only workable alternative is an unrevocable copy.
