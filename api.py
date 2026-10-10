"""PreArrival API for the optional React board. Reuses app.py logic; no thresholds here."""

import asyncio
import json
import math
import re
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.confidence import _segment_for, compute_flags, confirm_with_crew
from src.decide import decide
from src.news import PARAMS, score_news
from src.route import load_graph, segment
from src.tracking import new_sim, sim_answer, sim_inject, sim_position, total_min

ROOT = Path(__file__).resolve().parent
FIXTURES = {"a": ROOT / "fixtures/a", "b": ROOT / "fixtures/b"}
FIXTURE_LABELS = {"a": "A · Head injury", "b": "B · Ankle"}
SAFETY = "This prepares the room. It does not diagnose, and it does not replace the nurse's triage."
# Verified 2026-10-10: 2018 AHA/ASA early stroke guideline (the 2019 update dropped the fixed number).
LITERATURE = (
    "Published context, not our measurement: the 2018 AHA/ASA stroke guideline set a target of brain imaging "
    "within 20 minutes of ER arrival for more than half of treatment candidates "
    "(Powers et al., Stroke 2018, doi:10.1161/STR.0000000000000158)."
)
LABELS = {
    "rr": "Resp rate",
    "spo2": "SpO2",
    "on_oxygen": "On oxygen",
    "sbp": "Systolic BP",
    "hr": "Heart rate",
    "consciousness": "Consciousness",
    "temp_c": "Temp °C",
    "dbp": "Diastolic BP",
    "mechanism": "Mechanism",
    "eta_min": "ETA (min)",
}
NOTE_KEYS = ("consciousness", "mechanism", "eta_min", "on_oxygen", "rr", "temp_c")
MONITOR_KEYS = ("hr", "sbp", "dbp", "spo2")
SIM_LABEL = "SIMULATED POSITION · SIMULATED ROADBLOCK"
ETA_GAP_MIN = 3  # show route and spoken ETA side by side when they differ by more than this
ROW_KEYS = ["mechanism", "consciousness", "eta_min", "hr", "sbp", "dbp", "spo2", "rr", "temp_c", "on_oxygen"]

# Layout check only. The board labels this as not live.
FAKE = {
    "fields": {
        "hr": 132, "sbp": 96, "dbp": 60, "spo2": 95, "rr": None, "temp_c": None,
        "consciousness": "not_alert", "on_oxygen": False, "mechanism": "head_injury", "eta_min": 8,
        "evidence": {"hr": "FAKE", "sbp": "FAKE", "consciousness": "FAKE", "mechanism": "FAKE", "eta_min": "FAKE"},
    },
    "transcript": "FAKE FIELDS — layout check, no cloud call.",
    "stamps": {},
}

GRAPH = load_graph()
# One simulation at a time, shared by every browser tab. Endpoints run in worker threads, so a lock guards it.
_SIM = {"sim": None, "fixture": None}
_LOCK = threading.Lock()


def run_live(folder: Path, audio_path: Path) -> dict:
    from src.extract_note import extract_note
    from src.transcribe import transcribe
    from src.vision import read_monitor

    # Speech and photo are independent; send both at once to cut stage wait.
    with ThreadPoolExecutor(max_workers=2) as pool:
        heard_job = pool.submit(transcribe, str(audio_path))
        photo_job = pool.submit(read_monitor, str(next(folder.glob("monitor.*"))))
        heard, photo = heard_job.result(), photo_job.result()
    note = extract_note(heard["text"])
    fields = {k: note[k] for k in NOTE_KEYS} | {k: photo[k] for k in MONITOR_KEYS}
    fields["evidence"] = {**note["evidence"], **photo["evidence"]}
    # Flags only mark values to confirm with the crew; score_news and decide never read them.
    fields["flags"] = compute_flags(note, photo, heard["segments"])
    stamps = {
        "speech-to-text": heard["requested_at"],
        "monitor photo": photo["requested_at"],
        "note extraction": note["requested_at"],
    }
    return {"fields": fields, "transcript": heard["text"], "stamps": stamps, "segments": heard["segments"]}


def audio_span(key: str, evidence: str, segments: list) -> dict | None:
    """{start, end} of the Whisper segment holding a voice-note row's quote; None for monitor rows or no match."""
    if key not in NOTE_KEYS or not evidence:
        return None
    seg = _segment_for(evidence, segments)
    if seg is None or seg.get("start") is None or seg.get("end") is None:
        return None
    return {"start": seg["start"], "end": seg["end"]}


def json_safe(x):
    """Reduce to plain dict/list/str/int/float/bool/None. A non-finite float becomes None: JSON has no NaN."""
    if isinstance(x, dict):
        return {str(k): json_safe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set, frozenset)):
        return [json_safe(v) for v in x]
    if x is None or isinstance(x, (bool, str)):
        return x
    if isinstance(x, int):
        return int(x)
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    return str(x)


def build_board(result: dict, fixture: str, source: str, live: bool) -> dict:
    """Everything the React board shows. Score and plan come only from score_news and decide."""
    fields = {**result["fields"]}
    fields.setdefault("evidence", {})
    fields.setdefault("flags", {})
    score = score_news(fields)
    plan = decide(fields, score)
    segments = result.get("segments") or []
    board = {
        "run_id": time.time(),
        "live": live,
        "fixture": fixture,
        "source": source,
        "fields": fields,
        "transcript": result["transcript"],
        "transcript_segments": [{"text": s.get("text", ""), "start": s.get("start"), "end": s.get("end")} for s in segments],
        "stamps": result["stamps"],
        "score": score,
        "plan": plan,
        "news_terms": [
            {"key": k, "label": LABELS[k], "value": fields[k], "points": score["breakdown"][k]}
            for k in PARAMS
            if k in score["breakdown"]
        ],
        "missing": [{"key": k, "label": LABELS[k]} for k in score["missing"]],
        "confirm": confirm_with_crew(fields["flags"], score["missing"]),
        "rows": [
            {
                "key": k,
                "label": LABELS[k],
                "value": fields.get(k),
                "evidence": fields["evidence"].get(k, ""),
                "flags": fields["flags"].get(k, []),
                "audio_span": audio_span(k, fields["evidence"].get(k, ""), segments),
            }
            for k in ROW_KEYS
        ],
        "safety": SAFETY,
        "literature": LITERATURE,
        "eta_gap_min": ETA_GAP_MIN,
    }
    return json_safe(board)


def fixture_info(fixture: str) -> dict:
    folder = FIXTURES[fixture]
    photo = next(iter(sorted(folder.glob("monitor.*"))), folder / "monitor.jpg")
    caption = "Monitor photo (sample device, read live by the vision model)"
    meta = folder / "photo.json"
    if meta.exists():
        src = json.loads(meta.read_text()).get("source", {})
        credit = ", ".join(x for x in (src.get("author"), src.get("license")) if x)
        if credit:
            caption += f" · {credit}"
    return {
        "id": fixture,
        "label": FIXTURE_LABELS[fixture],
        "audio": f"/fixtures/{fixture}/audio.wav",
        "photo": f"/fixtures/{fixture}/{photo.name}",
        "photo_caption": caption,
    }


def sim_view(sim: dict | None, now: float | None = None) -> dict:
    """The simulated trip as the React board draws it. Timing and rerouting stay in src/tracking."""
    if sim is None:
        return {
            "active": False, "label": SIM_LABEL, "graph": None, "pickup": None, "route": [], "alternate": None,
            "incidents": [], "position": None, "route_eta_min": None, "remaining_min": None, "first_eta_min": None,
            "halted": False, "pending": False, "alert": "", "status": "", "busy": False,
        }
    now = time.time() if now is None else now
    pos = sim_position(sim, GRAPH, now)
    route = sim["route"]["route"]
    pending = sim["pending"]
    incidents = [{"segment": x, "name": segment(GRAPH, x)["name"], "kind": "closed"} for x in sim["closed"]] + [
        {"segment": x, "name": segment(GRAPH, x)["name"], "kind": "slow"} for x in sim["slow"]
    ]
    return json_safe({
        "active": True,
        "label": SIM_LABEL,
        "graph": {"nodes": GRAPH["nodes"], "segments": GRAPH["segments"], "destination": GRAPH["destination"]},
        "pickup": route[0],
        "route": route,
        "alternate": pending["offer"]["alternate"]["route"] if pending else None,
        "incidents": incidents,
        "position": {"lat": pos["lat"], "lon": pos["lon"], "arrived": pos["arrived"]},
        "route_eta_min": None if sim["halted"] else total_min(sim["route"]),
        "remaining_min": pos["eta_route_min"],
        "first_eta_min": sim["first_eta"],
        "halted": sim["halted"],
        "pending": bool(pending),
        "alert": sim.get("alert", ""),
        "status": sim["status"],
        "busy": bool(pending) or sim["halted"] or pos["arrived"],
    })


def _live(fixture: str, recording: bytes | None, suffix: str) -> dict:
    """Blocking cloud run: the saved fixture audio, or the browser recording written to a temp file."""
    folder = FIXTURES[fixture]
    if recording is None:
        return run_live(folder, folder / "audio.wav")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"mic{suffix}"
        path.write_bytes(recording)
        return run_live(folder, path)


def _audio_suffix(upload: UploadFile) -> str:
    """The upload's own extension (browsers send .webm); the speech service reads the format from it."""
    suffix = Path(upload.filename or "").suffix.lower()
    return suffix if re.fullmatch(r"\.[a-z0-9]{1,8}", suffix) else ".webm"


class FixtureBody(BaseModel):
    fixture: Literal["a", "b"]


class SimStart(FixtureBody):
    run_id: float


class SimInject(BaseModel):
    kind: Literal["closed", "slow"]


class SimAnswer(BaseModel):
    accept: bool


app = FastAPI(title="PreArrival API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/fixtures")
def list_fixtures():
    return [fixture_info(f) for f in FIXTURES]


@app.post("/api/run")
async def run(
    fixture: Annotated[Literal["a", "b"], Form()],
    source: Annotated[Literal["file", "mic"], Form()],
    audio: Annotated[UploadFile | None, File()] = None,
):
    recording, suffix = None, ""
    if source == "mic":
        recording = await audio.read() if audio is not None else b""
        if not recording:
            raise HTTPException(400, "Live mic needs a recording in the 'audio' field.")
        suffix = _audio_suffix(audio)
    try:
        # In a thread, so the server keeps answering GET /api/sim while the cloud calls run.
        result = await asyncio.to_thread(_live, fixture, recording, suffix)
        return build_board(result, fixture, source, live=True)
    except Exception as e:  # show the failure; never fall back to a fixture
        raise HTTPException(502, f"Live call failed: {type(e).__name__}: {e}") from e


@app.post("/api/fake")
def fake_board(body: FixtureBody):
    return build_board(FAKE, body.fixture, "file", live=False)


@app.get("/api/sim")
def get_sim():
    with _LOCK:
        return sim_view(_SIM["sim"])


@app.post("/api/sim/start")
def start_sim(body: SimStart):
    with _LOCK:
        _SIM["sim"] = new_sim(GRAPH, body.fixture, body.run_id, time.time())
        _SIM["fixture"] = body.fixture
        return sim_view(_SIM["sim"])


@app.post("/api/sim/inject")
def inject_sim(body: SimInject):
    with _LOCK:
        if _SIM["sim"] is not None:
            _SIM["sim"] = sim_inject(_SIM["sim"], GRAPH, body.kind, time.time())
        return sim_view(_SIM["sim"])


@app.post("/api/sim/answer")
def answer_sim(body: SimAnswer):
    with _LOCK:
        if _SIM["sim"] is not None:
            _SIM["sim"] = sim_answer(_SIM["sim"], GRAPH, body.accept, time.time())
        return sim_view(_SIM["sim"])


@app.post("/api/sim/stop")
def stop_sim():
    with _LOCK:
        _SIM["sim"] = None
        _SIM["fixture"] = None
        return sim_view(None)


app.mount("/fixtures", StaticFiles(directory=ROOT / "fixtures"), name="fixtures")
# Last, so it never shadows an API route. Skipped until the web/ app has been built.
if (ROOT / "web/dist").is_dir():
    app.mount("/", StaticFiles(directory=ROOT / "web/dist", html=True), name="web")
