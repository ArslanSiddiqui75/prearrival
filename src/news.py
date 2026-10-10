"""Partial NEWS2. Score owner implements this. See docs/SRS.md section 6."""


def score_news(fields: dict) -> dict:
    """Score only extracted parameters. Do not impute 0 for a missing one.

    Returns {points: int, missing: list[str], any_red: bool, breakdown: dict}.
    any_red is true when any scored parameter is 3.
    """
    raise NotImplementedError("score_news is not implemented")
