"""React board API: fixture list, fake board, live path with the cloud faked, 502 on failure, simulated tracking."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import api
from src.tracking import new_sim

ROOT = Path(__file__).resolve().parent.parent
NOTE_A = (ROOT / "fixtures/a/note.txt").read_text().strip()
STAMPS = {
    "speech-to-text": "2026-10-10T20:00:00+05:00",
    "monitor photo": "2026-10-10T20:00:01+05:00",
    "note extraction": "2026-10-10T20:00:02+05:00",
}
CLOUD = ("src.transcribe.transcribe", "src.vision.read_monitor", "src.extract_note.extract_note")
SIM_LABEL = "SIMULATED POSITION · SIMULATED ROADBLOCK"

client = TestClient(api.app)


def _form(**fields):
    """Text-only multipart fields, the way the browser's FormData sends them."""
    return {k: (None, v) for k, v in fields.items()}


def _post(path, **body):
    r = client.post(path, json=body)
    assert r.status_code == 200, r.text
    return r.json()


SEGMENTS = [
    {"text": "A man fell off a bike and hit his head.", "start": 0.0, "end": 3.2, "avg_logprob": -0.1},
    {"text": "He is confused, not answering properly.", "start": 3.2, "end": 6.0, "avg_logprob": -0.1},
    {"text": "He is not on oxygen. ETA eight minutes.", "start": 6.0, "end": 9.5, "avg_logprob": -0.1},
]


def _heard():
    return {"text": NOTE_A, "requested_at": STAMPS["speech-to-text"], "segments": SEGMENTS}


def _photo(legibility=None):
    return {
        "hr": 105, "sbp": 120, "dbp": 80, "spo2": 96,
        "evidence": {"hr": "monitor photo: 105", "sbp": "monitor photo: 120", "dbp": "monitor photo: 80",
                     "spo2": "monitor photo: 96"},
        "legibility": legibility or {},
        "requested_at": STAMPS["monitor photo"],
    }


def _note():
    return {
        "consciousness": "not_alert", "mechanism": "head_injury", "eta_min": 8, "on_oxygen": False, "rr": None,
        "temp_c": None,
        "evidence": {
            "consciousness": "He is confused, not answering properly",
            "mechanism": "fell off a bike and hit his head",
            "eta_min": "ETA eight minutes",
            "on_oxygen": "He is not on oxygen",
        },
        "requested_at": STAMPS["note extraction"],
    }


@pytest.fixture(autouse=True)
def _isolated(monkeypatch):
    """No test reaches the real cloud, and no simulation leaks from one test into the next."""

    def blocked(*args, **kwargs):
        raise AssertionError("this test did not fake the cloud")

    for target in CLOUD:
        monkeypatch.setattr(target, blocked)
    api._SIM.update(sim=None, fixture=None)
    yield
    api._SIM.update(sim=None, fixture=None)


@pytest.fixture
def cloud(monkeypatch):
    """Canned cloud replies for Fixture A. The returned dict records what each stage was called with."""
    seen = {}

    def transcribe(path):
        seen["audio"] = path
        return _heard()

    def read_monitor(path):
        seen["photo"] = path
        return _photo()

    def extract_note(text):
        seen["text"] = text
        return _note()

    monkeypatch.setattr("src.transcribe.transcribe", transcribe)
    monkeypatch.setattr("src.vision.read_monitor", read_monitor)
    monkeypatch.setattr("src.extract_note.extract_note", extract_note)
    return seen


# ---------- fixtures and fake board ----------


def test_fixtures_lists_a_and_b_with_media_that_is_served():
    items = client.get("/api/fixtures").json()
    assert [i["id"] for i in items] == ["a", "b"]
    assert [i["label"] for i in items] == ["A · Head injury", "B · Ankle"]
    for item in items:
        assert item["audio"] == f"/fixtures/{item['id']}/audio.wav"
        assert item["photo"] == f"/fixtures/{item['id']}/monitor.jpg"
        assert "sample device" in item["photo_caption"]
        assert client.get(item["audio"]).status_code == 200
        assert client.get(item["photo"]).status_code == 200
    assert items[0]["photo_caption"].endswith(
        "· Sistema d'Emergències Mèdiques (SEM), CC BY-SA (confirm version on the file page)"
    )
    assert "Quinn Dombrowski" in items[1]["photo_caption"]


def test_fake_board_is_not_live_and_leaves_FAKE_alone():
    board = client.post("/api/fake", json={"fixture": "a"}).json()
    assert board["live"] is False and board["source"] == "file" and board["fixture"] == "a"
    assert board["plan"]["priority"] == "P1"
    assert board["transcript"].startswith("FAKE")
    assert board["transcript_segments"] == [] and all(row["audio_span"] is None for row in board["rows"])
    assert board["stamps"] == {}
    assert board["fields"]["flags"] == {}
    assert "flags" not in api.FAKE["fields"]


def test_unknown_fixture_is_rejected():
    assert client.post("/api/run", files=_form(fixture="z", source="file")).status_code == 422
    assert client.post("/api/fake", json={"fixture": "z"}).status_code == 422


# ---------- live path ----------


def test_run_file_builds_the_board_from_score_news_and_decide(cloud):
    r = client.post("/api/run", files=_form(fixture="a", source="file"))
    assert r.status_code == 200
    board = r.json()

    assert set(board) == {"run_id", "live", "fixture", "source", "fields", "transcript", "transcript_segments", "stamps",
                          "score", "plan", "news_terms", "missing", "confirm", "rows", "safety", "literature",
                          "eta_gap_min"}
    assert board["live"] is True and board["fixture"] == "a" and board["source"] == "file"
    assert isinstance(board["run_id"], float)

    # The saved fixture files are what the cloud stages receive.
    assert cloud["audio"].endswith("fixtures/a/audio.wav") and cloud["photo"].endswith("fixtures/a/monitor.jpg")
    assert cloud["text"] == NOTE_A and board["transcript"] == NOTE_A
    assert board["stamps"] == STAMPS

    assert board["plan"]["priority"] == "P1"
    assert board["plan"]["prepare_for"] == ["resus bay", "CT", "senior review"]
    assert board["score"]["points"] == 4 and board["score"]["any_red"] is True
    assert board["score"]["missing"] == ["rr", "temp_c"]

    # PARAMS order, scored parameters only.
    assert [t["key"] for t in board["news_terms"]] == ["spo2", "on_oxygen", "sbp", "hr", "consciousness"]
    terms = {t["key"]: t for t in board["news_terms"]}
    assert terms["hr"] == {"key": "hr", "label": "Heart rate", "value": 105, "points": 1}
    assert terms["consciousness"]["points"] == 3 and terms["consciousness"]["value"] == "not_alert"
    assert terms["on_oxygen"]["value"] is False
    assert board["missing"] == [{"key": "rr", "label": "Resp rate"}, {"key": "temp_c", "label": "Temp °C"}]
    assert board["confirm"] == ["resp rate (missing)", "temperature (missing)"]

    assert set(board["fields"]) == {"hr", "sbp", "dbp", "spo2", "rr", "temp_c", "consciousness", "on_oxygen",
                                    "mechanism", "eta_min", "evidence", "flags"}
    assert board["fields"]["evidence"]["hr"] == "monitor photo: 105"
    assert board["fields"]["evidence"]["consciousness"] == "He is confused, not answering properly"

    assert [row["key"] for row in board["rows"]] == ["mechanism", "consciousness", "eta_min", "hr", "sbp", "dbp",
                                                     "spo2", "rr", "temp_c", "on_oxygen"]
    rows = {row["key"]: row for row in board["rows"]}
    assert rows["mechanism"] == {"key": "mechanism", "label": "Mechanism", "value": "head_injury",
                                 "evidence": "fell off a bike and hit his head", "flags": [],
                                 "audio_span": {"start": 0.0, "end": 3.2}}
    assert rows["rr"] == {"key": "rr", "label": "Resp rate", "value": None, "evidence": "", "flags": [],
                          "audio_span": None}

    # Hear the evidence: Whisper segments travel with the board; voice-note rows point at their segment,
    # monitor-photo rows have no span.
    assert board["transcript_segments"] == [{"text": s["text"], "start": s["start"], "end": s["end"]} for s in SEGMENTS]
    assert rows["consciousness"]["audio_span"] == {"start": 3.2, "end": 6.0}
    assert rows["eta_min"]["audio_span"] == {"start": 6.0, "end": 9.5}
    assert rows["hr"]["audio_span"] is None and rows["spo2"]["audio_span"] is None
    assert rows["on_oxygen"]["value"] is False and rows["eta_min"]["value"] == 8

    assert board["safety"] == "This prepares the room. It does not diagnose, and it does not replace the nurse's triage."
    assert board["literature"].startswith("Published context, not our measurement:")
    assert board["eta_gap_min"] == 3


def test_run_flags_reach_confirm_and_the_row_but_not_the_score(cloud, monkeypatch):
    monkeypatch.setattr("src.vision.read_monitor", lambda path: _photo({"hr": "unclear"}))
    board = client.post("/api/run", files=_form(fixture="a", source="file")).json()
    assert board["fields"]["flags"] == {"hr": ["unclear on photo"]}
    assert board["confirm"] == ["heart rate (unclear on photo)", "resp rate (missing)", "temperature (missing)"]
    assert next(row for row in board["rows"] if row["key"] == "hr")["flags"] == ["unclear on photo"]
    assert board["score"]["points"] == 4 and board["plan"]["priority"] == "P1"


@pytest.mark.parametrize("target", CLOUD)
def test_live_failure_is_502_and_never_a_fixture(cloud, monkeypatch, target):
    def boom(arg):
        raise RuntimeError("boom")

    monkeypatch.setattr(target, boom)
    r = client.post("/api/run", files=_form(fixture="a", source="file"))
    assert r.status_code == 502
    assert r.json() == {"detail": "Live call failed: RuntimeError: boom"}


def test_mic_without_a_recording_is_400():
    r = client.post("/api/run", files=_form(fixture="a", source="mic"))
    assert r.status_code == 400 and "recording" in r.json()["detail"]
    empty = client.post("/api/run", files={**_form(fixture="a", source="mic"), "audio": ("rec.webm", b"", "audio/webm")})
    assert empty.status_code == 400


@pytest.mark.parametrize("filename, suffix", [("recording.webm", ".webm"), ("take.OGG", ".ogg"), ("blob", ".webm")])
def test_mic_recording_is_saved_with_its_own_extension_then_removed(cloud, monkeypatch, filename, suffix):
    got = {}

    def transcribe(path):
        got.update(path=path, suffix=Path(path).suffix, data=Path(path).read_bytes())
        return _heard()

    monkeypatch.setattr("src.transcribe.transcribe", transcribe)
    files = {**_form(fixture="a", source="mic"), "audio": (filename, b"fake-audio", "audio/webm")}
    r = client.post("/api/run", files=files)
    assert r.status_code == 200
    assert r.json()["source"] == "mic" and r.json()["live"] is True
    assert got["suffix"] == suffix and got["data"] == b"fake-audio"
    assert not Path(got["path"]).exists()
    assert cloud["photo"].endswith("fixtures/a/monitor.jpg")


# ---------- simulated tracking ----------


def test_sim_is_inactive_until_started_and_stray_calls_do_nothing():
    off = client.get("/api/sim").json()
    assert off["active"] is False and off["label"] == SIM_LABEL
    assert off["graph"] is None and off["position"] is None and off["alternate"] is None
    assert off["route"] == [] and off["incidents"] == [] and off["alert"] == "" and off["status"] == ""
    assert off["route_eta_min"] is None and off["remaining_min"] is None and off["first_eta_min"] is None
    assert off["busy"] is False
    assert _post("/api/sim/inject", kind="closed") == off
    assert _post("/api/sim/answer", accept=True) == off
    # One shape whether or not a trip is running.
    assert set(_post("/api/sim/start", run_id=1, fixture="a")) == set(off)


def test_roadblock_then_accept_reroutes_and_stop_clears():
    on = _post("/api/sim/start", run_id=1, fixture="a")
    assert on["active"] is True and on["label"] == SIM_LABEL
    assert on["route"] == ["i8", "zp", "g8", "pims"] and on["pickup"] == "i8"
    assert on["first_eta_min"] == 8 and on["route_eta_min"] == 8 and 0 < on["remaining_min"] <= 8
    assert on["position"]["arrived"] is False
    assert on["pending"] is False and on["alternate"] is None and on["busy"] is False and on["alert"] == ""
    assert on["graph"]["destination"] == "pims"
    assert set(on["route"]) <= {n["id"] for n in on["graph"]["nodes"]}
    assert {"id", "from", "to", "name", "minutes"} <= set(on["graph"]["segments"][0])

    offered = _post("/api/sim/inject", kind="closed")
    assert offered["pending"] is True and offered["busy"] is True
    assert isinstance(offered["alternate"], list)
    assert offered["alternate"][0] == offered["route"][1] and offered["alternate"][-1] == "pims"
    assert "Road closed" in offered["alert"] and "adds 3 min" in offered["alert"]
    assert offered["status"] == "Alternate offered, waiting for crew"
    assert offered["incidents"] == [{"segment": "s11", "name": "Kashmir Highway (G-8 stretch)", "kind": "closed"}]
    assert offered["route"] == on["route"] and offered["route_eta_min"] == 8  # the route changes only on Accept

    # Another inject while the offer waits changes nothing.
    again = _post("/api/sim/inject", kind="slow")
    assert again["incidents"] == offered["incidents"] and again["alert"] == offered["alert"]

    accepted = _post("/api/sim/answer", accept=True)
    assert accepted["status"] == "ETA 8 -> 11 min (rerouted)"
    assert accepted["pending"] is False and accepted["alternate"] is None and accepted["alert"] == ""
    assert accepted["route"] == ["i8", "zp", "pims"] and accepted["route_eta_min"] == 11
    assert accepted["first_eta_min"] == 8 and accepted["busy"] is False
    assert accepted["incidents"] == offered["incidents"]

    assert _post("/api/sim/stop")["active"] is False
    assert client.get("/api/sim").json()["active"] is False


def test_keep_route_leaves_the_route_and_still_lists_the_incident():
    _post("/api/sim/start", run_id=2, fixture="a")
    offered = _post("/api/sim/inject", kind="closed")
    kept = _post("/api/sim/answer", accept=False)
    assert kept["pending"] is False and kept["alternate"] is None and kept["alert"] == ""
    assert kept["route"] == offered["route"] and kept["route_eta_min"] == 8
    assert kept["status"].startswith("Crew kept route despite reported closure")
    assert kept["incidents"] == offered["incidents"]


def test_heavy_traffic_is_listed_as_a_slow_incident():
    _post("/api/sim/start", run_id=3, fixture="a")
    offered = _post("/api/sim/inject", kind="slow")
    assert offered["pending"] is True and offered["alert"].startswith("Heavy traffic ahead")
    assert [(i["segment"], i["kind"]) for i in offered["incidents"]] == [("s11", "slow")]


def test_new_sim_follows_the_fixture_and_replaces_the_running_one():
    _post("/api/sim/start", run_id=4, fixture="a")
    _post("/api/sim/inject", kind="closed")
    b = _post("/api/sim/start", run_id=5, fixture="b")
    assert b["pickup"] == "g11" and b["first_eta_min"] == 12
    assert b["pending"] is False and b["incidents"] == []


def test_sim_view_halted_has_no_route_eta_and_is_busy():
    sim = {**new_sim(api.GRAPH, "a", 1, 0.0), "halted": True}
    view = api.sim_view(sim, now=0.0)
    assert view["halted"] is True and view["route_eta_min"] is None and view["busy"] is True


def test_sim_view_arrived_is_busy_with_nothing_remaining():
    view = api.sim_view(new_sim(api.GRAPH, "a", 1, 0.0), now=100.0)  # 100 s at 10x is 16 sim minutes; the trip is 8
    assert view["position"]["arrived"] is True and view["remaining_min"] == 0 and view["busy"] is True
    assert view["route_eta_min"] == 8


# ---------- plumbing ----------


def test_json_safe_keeps_json_types_and_scrubs_the_rest():
    class Odd:
        def __str__(self):
            return "odd"

    out = api.json_safe({1: (1, 2.5, True, None), "nan": float("nan"), "inf": float("inf"), "odd": Odd(), "set": {3}})
    assert out == {"1": [1, 2.5, True, None], "nan": None, "inf": None, "odd": "odd", "set": [3]}
    json.dumps(out, allow_nan=False)


def test_cors_allows_the_vite_dev_origin_only():
    ask = {"Access-Control-Request-Method": "POST"}
    ok = client.options("/api/run", headers={"Origin": "http://localhost:5173", **ask})
    assert ok.headers["access-control-allow-origin"] == "http://localhost:5173"
    other = client.options("/api/run", headers={"Origin": "http://example.com", **ask})
    assert "access-control-allow-origin" not in other.headers
