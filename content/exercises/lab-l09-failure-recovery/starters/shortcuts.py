"""Four tempting shortcuts. Each one is wrong, and run_tests.py proves how.

Plug them into a Pipeline to watch them fail:

    Pipeline(contract, tasks={"notify": notify_without_key})
    Pipeline(contract, tasks={"ingest_raw": ingest_without_freshness})
    Pipeline(contract, key_fn=fresh_key_per_try)
    Pipeline(contract, key_fn=coarse_key)

They work with the reference solution and with your completed starter, because
they reach the module's own helpers through `pipe.impl`.
"""


def notify_without_key(pipe, ctx):
    """Send to every recipient with no outbox and no idempotency key.

    Wrong because a retry after the effect cannot tell what was already sent,
    so it sends again: the first recipient receives the same report twice.
    """
    report = pipe.store.reports[ctx["business_date"]]
    ctx["faults"].hit("before_effect")
    for recipient in pipe.contract["recipients"]:
        pipe.channel.send(recipient, report)
        ctx["faults"].hit("after_effect")
    return {"sent": len(pipe.contract["recipients"])}


def ingest_without_freshness(pipe, ctx):
    """Retain whatever sits in the landing slot, without checking which day it describes.

    Wrong because a re-delivered extract from yesterday makes every task green
    while the published report repeats yesterday's numbers under today's date.
    """
    landing = pipe.impl.read_landing(ctx["landing"])
    return pipe.impl.retain_landing(pipe, ctx, landing)


def fresh_key_per_try(report, recipient, ctx):
    """A new key for every attempt and try, as if a random id were generated on each call.

    Wrong because the retry's key matches nothing the receiver has seen, so the
    receiver cannot recognize the repeat, and the first try's intents stay
    pending forever.
    """
    return f"notify:{report['report_id']}:{recipient}:{ctx['run_id']}:{ctx['attempt']}:{ctx['try']}"


def coarse_key(report, recipient, ctx):
    """One key per business date and recipient, ignoring the report's content.

    Wrong because a corrected report for the same date reuses the old key: the
    outbox says 'already sent' and nobody is told the numbers changed.
    """
    return f"notify:{report['content']['report_date']}:{recipient}"
