"""Repair this intentionally flawed resolver; do not use it as a solution."""


def flawed_current(rows):
    current = {}
    for row in rows:
        if row.get("inspected_units") is not None and row["inspected_units"] >= 0:
            # BUGS: last arrival wins, invalid latest disappears, conflict ignored.
            current[row["inspection_id"]] = row
    return list(current.values())


def resolve(rows):
    """Implement retained evidence, explicit quarantine, identity conflict checks,
    latest revision (including invalid evidence), and blocked publication.
    Use fixtures and independently authored expected/business.json as your oracle.
    """
    raise NotImplementedError("Replace arrival-order logic with a stated source contract")
