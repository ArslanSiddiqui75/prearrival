"""Priority rules from docs/SRS.md sections 7 and 8. These fail until decide is implemented."""

from src.decide import decide


def _score(points, any_red=False):
    return {"points": points, "missing": [], "any_red": any_red, "breakdown": {}}


def test_head_injury_not_alert_is_p1_with_ct():
    fields = {"mechanism": "head_injury", "consciousness": "not_alert", "sbp": 130, "eta_min": 8}
    result = decide(fields, _score(0))
    assert result["priority"] == "P1"
    assert result["prepare_for"] == ["resus bay", "CT", "senior review"]


def test_chest_pain_low_sbp_is_p1():
    fields = {"mechanism": "chest_pain", "consciousness": "alert", "sbp": 88}
    result = decide(fields, _score(0))
    assert result["priority"] == "P1"
    assert result["prepare_for"] == ["resus bay", "ECG", "cardiology"]


def test_stroke_is_p1_generic_row():
    fields = {"mechanism": "stroke", "consciousness": "not_alert", "sbp": 140}
    result = decide(fields, _score(1))
    assert result["priority"] == "P1"
    assert result["prepare_for"] == ["resus bay", "senior review"]


def test_score_7_is_p1_even_without_a_named_mechanism():
    fields = {"mechanism": "other", "consciousness": "alert", "sbp": 130}
    result = decide(fields, _score(7, any_red=True))
    assert result["priority"] == "P1"
    assert result["prepare_for"] == ["resus bay", "senior review"]


def test_single_red_parameter_is_p1():
    fields = {"mechanism": "other", "consciousness": "alert", "sbp": 130}
    result = decide(fields, _score(3, any_red=True))
    assert result["priority"] == "P1"


def test_score_5_is_p2():
    fields = {"mechanism": "other", "consciousness": "alert", "sbp": 130}
    result = decide(fields, _score(5, any_red=False))
    assert result["priority"] == "P2"
    assert result["prepare_for"] == ["cubicle", "repeat vitals"]


def test_limb_injury_stable_is_p3():
    fields = {"mechanism": "limb_injury", "consciousness": "alert", "sbp": 120}
    result = decide(fields, _score(0))
    assert result["priority"] == "P3"
    assert result["prepare_for"] == ["cubicle", "limb x-ray"]


def test_limb_injury_that_is_p1_uses_the_generic_p1_row():
    fields = {"mechanism": "limb_injury", "consciousness": "alert", "sbp": 80}
    result = decide(fields, _score(8, any_red=True))
    assert result["priority"] == "P1"
    assert result["prepare_for"] == ["resus bay", "senior review"]


def test_shortness_of_breath_row():
    fields = {"mechanism": "shortness_of_breath", "consciousness": "alert", "sbp": 120}
    result = decide(fields, _score(1))
    assert result["prepare_for"] == ["resus bay", "oxygen", "chest x-ray"]
