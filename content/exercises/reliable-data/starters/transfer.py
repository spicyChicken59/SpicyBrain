"""New domain; first write your grain, ordering and deletion policy in prose."""


def order_totals(events):
    """Input: fixtures/orders.json. An order can contain multiple lines and line
    IDs repeat across orders. Cancellations are explicit retained tombstones.
    Return totals in integer cents; absent lines are not cancellation requests.
    Raise an error for conflicting current payloads. Verify replay and late data.
    """
    raise NotImplementedError("Design the composite key and cancellation handling")
