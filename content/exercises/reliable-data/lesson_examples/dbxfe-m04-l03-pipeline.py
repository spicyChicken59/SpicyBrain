class LocalPipeline:
    """In-memory dependency/failure simulation, not durable orchestration.

    Boundaries: retained_raw -> resolved_state -> published_snapshot -> local_effect.
    A production design needs actual durable transactions/outbox storage and a
    recipient's idempotency agreement. A Python dictionary is not that guarantee.
    """
    def __init__(self):
        self.raw = []
        self.resolved = None
        self.published = None
        self.status = "not_published"
        self.outbox = {}

    def ingest(self, batch, fail_after=None):
        self.raw.extend(deepcopy(batch))
        self.status = "stale_previous" if self.published else "not_published"
        if fail_after == "retained_raw":
            raise RuntimeError("Injected failure after retained_raw")
        return self.recover(fail_after)

    def recover(self, fail_after=None):
        self.resolved = resolve(self.raw)
        if fail_after == "resolved_state":
            raise RuntimeError("Injected failure after resolved_state")
        if not self.resolved["publication_allowed"]:
            self.status = "stale_previous" if self.published else "blocked_no_snapshot"
            return self.resolved
        snapshot = {field: deepcopy(self.resolved[field]) for field in
                    ("accepted", "totals", "excluded_keys", "coverage")}
        snapshot_id = sha256(canonical(snapshot).encode()).hexdigest()
        self.published = {"snapshot_id": snapshot_id, **snapshot}
        self.status = "current_with_exclusions" if snapshot["excluded_keys"] else "current"
        if fail_after == "published_snapshot":
            raise RuntimeError("Injected failure after published_snapshot")
        # setdefault models a receiver keyed by snapshot ID; it sends nothing.
        self.outbox.setdefault(snapshot_id, {"kind": "local_notification", "snapshot_id": snapshot_id})
        return self.resolved
