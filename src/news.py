"""Partial NEWS2. Score owner implements this. See docs/SRS.md section 6."""

# Parameters in the order the board shows them.
PARAMS = ["rr", "spo2", "on_oxygen", "sbp", "hr", "consciousness", "temp_c"]


def _rr(v):
    if v <= 8:
        return 3
    if v <= 11:
        return 1
    if v <= 20:
        return 0
    if v <= 24:
        return 2
    return 3


def _spo2(v):
    if v <= 91:
        return 3
    if v <= 93:
        return 2
    if v <= 95:
        return 1
    return 0


def _sbp(v):
    if v <= 90:
        return 3
    if v <= 100:
        return 2
    if v <= 110:
        return 1
    if v <= 219:
        return 0
    return 3


def _hr(v):
    if v <= 40:
        return 3
    if v <= 50:
        return 1
    if v <= 90:
        return 0
    if v <= 110:
        return 1
    if v <= 130:
        return 2
    return 3


def _temp(v):
    if v <= 35.0:
        return 3
    if v <= 36.0:
        return 1
    if v <= 38.0:
        return 0
    if v <= 39.0:
        return 1
    return 2


_RULES = {
    "rr": _rr,
    "spo2": _spo2,
    "on_oxygen": lambda v: 2 if v else 0,
    "sbp": _sbp,
    "hr": _hr,
    "consciousness": lambda v: 0 if v == "alert" else 3,
    "temp_c": _temp,
}


def score_news(fields: dict) -> dict:
    """Score only extracted parameters. Do not impute 0 for a missing one.

    Returns {points: int, missing: list[str], any_red: bool, breakdown: dict}.
    any_red is true when any scored parameter is 3.
    """
    breakdown = {}
    missing = []
    for name in PARAMS:
        value = fields.get(name)
        if value is None:
            missing.append(name)
        else:
            breakdown[name] = _RULES[name](value)
    return {
        "points": sum(breakdown.values()),
        "missing": missing,
        "any_red": any(p == 3 for p in breakdown.values()),
        "breakdown": breakdown,
    }
