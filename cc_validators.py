# cc_validators.py
# (Optional extra validation hooks – currently kept minimal)
# You can expand these if you want stricter checks.

def sanity_check(record: dict) -> dict:
    """
    Adjust confidences based on simple constraints.
    """
    conf = record.setdefault("confidence", {})
    ta = record.get("total_amount_due")
    mn = record.get("minimum_amount_due")

    if ta is not None and mn is not None and mn <= ta:
        conf["total_amount_due"] = max(conf.get("total_amount_due", 0.7), 0.85)
        conf["minimum_amount_due"] = max(conf.get("minimum_amount_due", 0.7), 0.85)
    return record
