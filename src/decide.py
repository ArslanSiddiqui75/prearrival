"""Priority and prepare-for table. Score owner implements this. See docs/SRS.md sections 7 and 8."""


def _priority(fields: dict, score: dict) -> tuple[str, list[str]]:
    mechanism = fields.get("mechanism")
    consciousness = fields.get("consciousness")
    sbp = fields.get("sbp")

    reasons = []
    if score["points"] >= 7:
        reasons.append(f"NEWS2 {score['points']} is 7 or more")
    if score["any_red"]:
        red = [k for k, v in score["breakdown"].items() if v == 3]
        reasons.append(f"red parameter: {', '.join(red)}")
    if mechanism == "head_injury" and consciousness == "not_alert":
        reasons.append("head injury and not alert")
    if mechanism == "chest_pain" and sbp is not None and sbp <= 90:
        reasons.append(f"chest pain with systolic {sbp}")
    if mechanism == "stroke":
        reasons.append("suspected stroke")
    if reasons:
        return "P1", reasons
    if score["points"] in (5, 6):
        return "P2", [f"NEWS2 {score['points']}"]
    return "P3", [f"NEWS2 {score['points']}, no P1 trigger"]


def _prepare_for(fields: dict, priority: str) -> list[str]:
    mechanism = fields.get("mechanism")
    sbp = fields.get("sbp")

    if mechanism == "head_injury" and fields.get("consciousness") == "not_alert":
        return ["resus bay", "CT", "senior review"]
    if mechanism == "chest_pain" and sbp is not None and sbp <= 90:
        return ["resus bay", "ECG", "cardiology"]
    if mechanism == "shortness_of_breath":
        return ["resus bay", "oxygen", "chest x-ray"]
    if mechanism == "limb_injury" and priority != "P1":
        return ["cubicle", "limb x-ray"]
    if priority == "P1":
        return ["resus bay", "senior review"]
    return ["cubicle", "repeat vitals"]


def decide(fields: dict, score: dict) -> dict:
    """Pure function. Do not call the network.

    Returns {priority: "P1"|"P2"|"P3", prepare_for: list[str], reasons: list[str]}.
    """
    priority, reasons = _priority(fields, score)
    return {"priority": priority, "prepare_for": _prepare_for(fields, priority), "reasons": reasons}
