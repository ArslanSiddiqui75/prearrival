"""Confidence flags from checkable signals. Flags never change a value, the score or the priority."""

from src.confidence import (
    IMPLAUSIBLE,
    LOW_LOGPROB,
    PARTLY_VISIBLE,
    QUOTE_NOT_FOUND,
    UNCLEAR_ON_PHOTO,
    UNCLEAR_SPEECH,
    compute_flags,
    confirm_with_crew,
)
from src.decide import decide
from src.extract_note import NOT_FOUND_MARK
from src.news import score_news

CLEAR_SEGMENTS = [{"text": " Ambulance four. ETA eight minutes. He is confused.", "start": 0, "end": 5, "avg_logprob": -0.1, "no_speech_prob": 0}]


def _note(**kw):
    note = {"consciousness": "not_alert", "mechanism": "head_injury", "eta_min": 8, "on_oxygen": None, "rr": None, "temp_c": None}
    note.update(kw)
    note.setdefault("evidence", {"consciousness": "He is confused", "mechanism": "He is confused", "eta_min": "ETA eight minutes"})
    return note


def _photo(**kw):
    photo = {"hr": 105, "sbp": 120, "dbp": 80, "spo2": 96, "legibility": {"hr": "clear", "sbp": "clear", "dbp": "clear", "spo2": "clear"}}
    photo.update(kw)
    return photo


def test_no_flags_on_a_clean_read():
    assert compute_flags(_note(), _photo(), CLEAR_SEGMENTS) == {}


def test_unclear_speech_uses_the_segment_holding_the_quote():
    segments = [
        {"text": " Ambulance four. ETA eight minutes.", "avg_logprob": -0.1},
        {"text": " He is confused.", "avg_logprob": LOW_LOGPROB - 0.2},
    ]
    flags = compute_flags(_note(), _photo(), segments)
    assert flags["consciousness"] == [UNCLEAR_SPEECH]
    assert "eta_min" not in flags


def test_logprob_at_the_threshold_is_not_flagged():
    segments = [{"text": "ETA eight minutes. He is confused.", "avg_logprob": LOW_LOGPROB}]
    assert compute_flags(_note(), _photo(), segments) == {}


def test_quote_not_found_flag():
    note = _note(evidence={"consciousness": "patient drowsy" + NOT_FOUND_MARK, "eta_min": "ETA eight minutes"})
    flags = compute_flags(note, _photo(), CLEAR_SEGMENTS)
    assert flags == {"consciousness": [QUOTE_NOT_FOUND]}


def test_implausible_monitor_value():
    flags = compute_flags(_note(), _photo(hr=300, spo2=45), CLEAR_SEGMENTS)
    assert flags == {"hr": [IMPLAUSIBLE], "spo2": [IMPLAUSIBLE]}


def test_systolic_not_above_diastolic_flags_both():
    flags = compute_flags(_note(), _photo(sbp=80, dbp=80), CLEAR_SEGMENTS)
    assert flags == {"sbp": [IMPLAUSIBLE], "dbp": [IMPLAUSIBLE]}


def test_legibility_flags():
    photo = _photo(legibility={"hr": "partial", "sbp": "unclear", "dbp": "clear", "spo2": "clear"})
    flags = compute_flags(_note(), photo, CLEAR_SEGMENTS)
    assert flags == {"hr": [PARTLY_VISIBLE], "sbp": [UNCLEAR_ON_PHOTO]}


def test_null_values_are_never_flagged():
    photo = _photo(hr=None, legibility={"hr": "unclear"})
    assert "hr" not in compute_flags(_note(), photo, CLEAR_SEGMENTS)


def test_flagged_value_is_still_scored_and_priority_unchanged():
    photo = _photo(sbp=85, dbp=90, legibility={"sbp": "partial"})
    note = _note()
    fields = {k: v for k, v in {**note, **photo}.items() if k not in ("evidence", "legibility")}
    before_score, before_plan = score_news(fields), decide(fields, score_news(fields))

    flags = compute_flags(note, photo, CLEAR_SEGMENTS)
    assert IMPLAUSIBLE in flags["sbp"] and PARTLY_VISIBLE in flags["sbp"]
    fields["flags"] = flags

    assert fields["sbp"] == 85
    assert score_news(fields) == before_score
    assert score_news(fields)["breakdown"]["sbp"] == 3
    assert decide(fields, score_news(fields)) == before_plan


def test_confirm_list_puts_flags_before_missing():
    items = confirm_with_crew({"hr": [PARTLY_VISIBLE]}, ["rr", "temp_c"])
    assert items == ["heart rate (partly visible)", "resp rate (missing)", "temperature (missing)"]


def test_confirm_list_empty_when_nothing_to_confirm():
    assert confirm_with_crew({}, []) == []
