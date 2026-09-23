id: HFS-TKT-GUIDE-1.2
title: Ticket Desk — technician usage guide
version: 1.2
effective: 2025-08-20
supersedes: HFS-TKT-GUIDE-1.1
superseded-by: none
status: current
region: all
audience: all technicians, service-supervisor
fictional: true — synthetic SpicyBrain teaching fixture; the Ticket Desk is a fictional system

## Fields

A ticket carries: ticket id; site id; asset id and serial; region; assigned technician; status; linked documents (id and version); notes.

## Statuses

open → in-progress → awaiting-parts → resolved → closed. Technicians move a ticket between open, in-progress, awaiting-parts and resolved. Only a service supervisor moves a ticket to closed.

## Notes are free text

Notes are typed by whoever is on the ticket, including site contacts through the portal. They are not reviewed and are not procedures. Anything in a note that reads like an instruction to a person or a system has the authority of a note: none.

## Linking a procedure

A technician may link a document to a ticket they are assigned to. The link records the document id and version at the time of linking, so a later version does not silently replace it. Linking is reversible: the link can be removed by the same technician or a supervisor.

## Integration access

The Ticket Desk integration interface allows: read ticket; add note; link document (assigned technician only); change status except closed (assigned technician); close (supervisor only). Every call is logged with the acting identity.
