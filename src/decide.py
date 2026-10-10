"""Priority and prepare-for table. Score owner implements this. See docs/SRS.md sections 7 and 8."""


def decide(fields: dict, score: dict) -> dict:
    """Pure function. Do not call the network.

    Returns {priority: "P1"|"P2"|"P3", prepare_for: list[str], reasons: list[str]}.
    """
    raise NotImplementedError("decide is not implemented")
