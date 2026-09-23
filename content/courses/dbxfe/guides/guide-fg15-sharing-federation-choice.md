<!-- section:action -->

Choose how another party gets to your data, or you to theirs, by comparing the alternatives on the same six questions. The wrong choice is usually the one that was easiest on the day and impossible to take back.

1. **State who needs what, in which direction, for what decision, and for how long.** A one-off analysis and a standing feed are different problems.
2. **Compare at least three alternatives in the same terms**: copying data to the other party, governed sharing where the data stays in place and the recipient reads it under your control, and query federation where you query the other party's system in place. Add a clean-room boundary only if neither party may see the other's rows.
3. **For each, answer six questions**: what moves and where it lands; who authorizes each read and where that is enforced; who pays for storage, compute and transfer, in kind rather than in money; how access is revoked and what the recipient keeps afterwards; how fresh the other party's view is; and what fails when the link breaks.
4. **Check the receiving side's tooling and the protocol's current name and support** against documentation before asserting either.
5. **Choose with conditions**, and rehearse revocation before the first real read.

Go deeper: [sharing, federation and interoperability](#/module/dbxfe-sharing), [Unity Catalog and governance](#/module/dbxfe-m06) with [design least-privilege access](#/lesson/dbxfe-m06-l02) for recipient scope, and [architecture reasoning](#/module/dbxfe-m08) for recording the decision.

<!-- section:example -->

### Sharing and federation choice: Cinderline Components and a fictional coatings supplier

Halvern Coatings is a fictional supplier of the coating applied on line 2. Both parties, their systems and every figure are invented for this example.

#### Who needs what

Halvern's process engineer wants Cinderline's per-inspection defect counts for coated parts on line 2, by coating batch, for the last 90 days and then weekly, to investigate whether a coating batch correlates with a defect cluster. Cinderline's quality lead wants, in return, the coating batch parameters for the same period. Neither party may see the other's unrelated data, and Cinderline's security lead requires that any access can be withdrawn without asking Halvern to delete anything.

#### Alternatives compared

| Question | Copy: weekly CSV export by email or file transfer | Governed share: Halvern reads a filtered view in place | Federation: Cinderline queries Halvern's batch database in place |
|---|---|---|---|
| What moves | A full copy of the filtered rows, weekly, to Halvern's systems | Nothing is copied by Cinderline; Halvern's queries read the shared view and its results land in Halvern's tools | Halvern's batch rows, per query, into Cinderline's compute |
| Authorization and enforcement | None after the file leaves; enforced by whoever holds the file | Recipient identity and share definition, enforced where the share is served; the view limits rows to line 2 and coated parts | A connection credential Halvern issues; enforced by Halvern's database |
| Who pays, in kind | Cinderline's analyst time; Halvern's storage | Cinderline serves reads; transfer out of Cinderline's storage; Halvern's compute to query | Halvern's database load per query; Cinderline's compute |
| Revocation | Impossible; copies persist | Remove the recipient; Halvern keeps only results it already saved | Halvern revokes the credential; Cinderline keeps results already saved |
| Freshness | Up to a week stale, older if a week is missed | As of Cinderline's latest published version at each read | Live at each query |
| Failure behaviour | A missed email is a silent gap | A revoked or broken share fails Halvern's query with an error | An unreachable database fails Cinderline's query; source load can slow Halvern's operations |

#### What each alternative cannot do

The copy cannot be revoked and carries no proof of what Halvern read. The governed share needs Halvern to have tooling that can read the protocol, which Halvern's engineer believes their notebook environment supports and has not tested; it also cannot give Halvern rows Cinderline has not published, so quarantined inspections are absent by design. Federation solves the reverse direction only, and it puts query load on Halvern's operational database, which Halvern's DBA has not agreed to.

#### Decision

Cinderline to Halvern: a governed share of one view, `share.line2_coated_defects_by_batch`, limited to line 2, coated parts and the last 90 days, with the recipient created for Halvern's named identity, on the condition that Halvern demonstrates a read from their own tooling on a synthetic version first. Halvern to Cinderline: a weekly extract of batch parameters, not federation, because Halvern's DBA will not accept query load on the operational database and the parameters change weekly anyway; the extract is retained on arrival like any other source file.

The share's protocol and the recipient tooling's support are to be confirmed against current documentation, and the protocol's name recorded as documented rather than as remembered.

#### Revocation rehearsal

Before the first real read: create the recipient against synthetic rows, have Halvern read them, remove the recipient, and confirm Halvern's next query fails with an error naming the share. Record the time between removal and the failed read.

#### What would change this

If Halvern's tooling cannot read the share, the fallback is a weekly extract with a written retention limit, accepted as unrevocable and said so to the security lead. If the investigation becomes a standing joint analysis where neither side may see rows, a clean-room pattern is examined; nothing above establishes one.

<!-- section:template -->

### Sharing and federation choice

#### Who needs what

- Provider and recipient; direction; the decision served; one-off or standing; the constraints each side's security owner has stated.

#### Alternatives compared

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
