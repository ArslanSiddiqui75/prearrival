"""Partial NEWS2 from docs/SRS.md section 6. These fail until score_news is implemented."""

from src.news import score_news


def test_missing_parameters_are_not_scored_as_zero():
    result = score_news({"hr": 80, "sbp": 120, "spo2": 98, "consciousness": "alert"})
    assert result["points"] == 0
    assert result["any_red"] is False
    assert "rr" in result["missing"]
    assert "temp_c" in result["missing"]
    assert "rr" not in result["breakdown"]


def test_red_systolic_and_not_alert_add_up():
    result = score_news(
        {
            "hr": 130,
            "sbp": 85,
            "spo2": 96,
            "consciousness": "not_alert",
            "on_oxygen": False,
        }
    )
    # pulse 111-130 is 2, sbp <= 90 is 3, spo2 >= 96 is 0, not alert is 3
    assert result["breakdown"]["hr"] == 2
    assert result["breakdown"]["sbp"] == 3
    assert result["breakdown"]["spo2"] == 0
    assert result["breakdown"]["consciousness"] == 3
    assert result["points"] == 8
    assert result["any_red"] is True


def test_oxygen_adds_two_and_does_not_invent_a_respiratory_rate():
    result = score_news({"spo2": 94, "on_oxygen": True, "consciousness": "alert"})
    assert result["breakdown"]["spo2"] == 1
    assert result["breakdown"]["on_oxygen"] == 2
    assert result["breakdown"]["consciousness"] == 0
    assert result["points"] == 3
    assert "rr" in result["missing"]
