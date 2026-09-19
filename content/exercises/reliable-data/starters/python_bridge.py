"""Task B1: implement a different input case before reading reference.py."""
records = [{"record_id": "s1", "units": "11"}, {"record_id": "s2", "units": None},
           {"record_id": "s3", "units": "2.5"}, {"record_id": "s4", "units": "0"}]


def parse_records(rows):
    """Return accepted/rejected lists with a reason for each rejected row.

    Do not turn missing into zero. Decimal strings are malformed for this task.
    Expected accepted: s1=11, s4=0; rejected: s2 missing, s3 malformed integer.
    """
    raise NotImplementedError("Implement the task, then compare TASKS and SOLUTIONS")
