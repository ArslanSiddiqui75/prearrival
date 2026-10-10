"""One-command check for the presenting laptop: key, models, and one live Fixture A run.

    python scripts/preflight.py          # Fixture A only (3 cloud calls)
    python scripts/preflight.py a b      # both fixtures
    python scripts/preflight.py --offline a b   # tracking check only, no network

Uses the same functions as the board. Prints PASS or FAIL per check and exits non-zero on any failure.
"""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.confidence import compute_flags, confirm_with_crew  # noqa: E402
from src.decide import decide  # noqa: E402
from src.groq_client import STT_MODEL, TEXT_MODEL, VISION_MODEL, client  # noqa: E402
from src.news import score_news  # noqa: E402

NOTE_KEYS = ("consciousness", "mechanism", "eta_min", "on_oxygen", "rr", "temp_c")
failed = False


def check(name, ok, detail=""):
    global failed
    failed |= not ok
    print(f"{'PASS' if ok else 'FAIL'}  {name}{'  — ' + detail if detail else ''}")


def run_fixture(fx):
    from src.extract_note import extract_note
    from src.transcribe import transcribe
    from src.vision import read_monitor

    folder = ROOT / "fixtures" / fx
    expected = json.loads((folder / "expected.json").read_text())
    photo_truth = json.loads((folder / "photo.json").read_text())

    t = time.time()
    heard = transcribe(str(folder / "audio.wav"))
    photo = read_monitor(str(folder / "monitor.jpg"))
    note = extract_note(heard["text"])
    secs = time.time() - t

    fields = {k: note[k] for k in NOTE_KEYS} | {k: photo[k] for k in ("hr", "sbp", "dbp", "spo2")}
    score = score_news(fields)
    plan = decide(fields, score)
    flags = compute_flags(note, photo, heard["segments"])
    # Flags must never change the score or the plan.
    fields["flags"] = flags
    check(f"fixture {fx}: flags leave score and plan unchanged", score_news(fields) == score and decide(fields, score_news(fields)) == plan)
    print(f"      flags: {flags or 'none'} · confirm with crew: {', '.join(confirm_with_crew(flags, score['missing'])) or 'nothing'}")

    note_diff = {k: (note[k], v) for k, v in expected["from_note"].items() if note[k] != v}
    photo_diff = {k: (photo[k], photo_truth[k]) for k in ("hr", "sbp", "dbp", "spo2") if photo[k] != photo_truth[k]}
    check(f"fixture {fx}: note fields", not note_diff, f"got vs expected {note_diff}" if note_diff else "")
    check(f"fixture {fx}: photo read", not photo_diff, f"got vs human read {photo_diff}" if photo_diff else "")
    check(
        f"fixture {fx}: {plan['priority']} {', '.join(plan['prepare_for'])}",
        plan["priority"] == expected["expect_priority"] and plan["prepare_for"] == expected["expect_prepare_for"],
        f"NEWS2 {score['points']} {score['breakdown']} · {secs:.1f}s",
    )


def tracking_check(fixtures):
    """Offline: simulated route ETA vs spoken ETA, and what a roadblock at the start would offer."""
    from src.route import load_graph
    from src.tracking import new_sim, sim_answer, sim_inject, total_min

    graph = load_graph()
    for fx in fixtures:
        spoken = json.loads((ROOT / "fixtures" / fx / "expected.json").read_text())["from_note"]["eta_min"]
        sim = new_sim(graph, fx, "preflight", now=0.0)
        route_eta = total_min(sim["route"])
        check(f"tracking {fx}: route ETA {route_eta:g} min vs spoken {spoken} min", abs(route_eta - spoken) <= 1,
              " -> ".join(sim["route"]["route"]))
        for kind in ("closed", "slow"):
            hit = sim_inject(sim, graph, kind, now=0.0)
            line = hit.get("alert") or hit["status"]
            if hit["pending"]:
                line += " | Accept: " + sim_answer(hit, graph, True, now=0.0)["status"]
            print(f"      {kind} at start: {line}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    fixtures = args or ["a"]
    tracking_check(fixtures)
    if "--offline" in sys.argv:
        print("\nREADY (offline tracking check)" if not failed else "\nNOT READY — fix the FAIL lines above")
        sys.exit(1 if failed else 0)

    try:
        available = {m.id for m in client().models.list().data}
        check("GROQ_API_KEY works", True)
    except Exception as e:
        check("GROQ_API_KEY works", False, f"{type(e).__name__}: {e}")
        sys.exit(1)
    for model in (STT_MODEL, VISION_MODEL, TEXT_MODEL):
        check(f"model available: {model}", model in available)

    for fx in fixtures:
        try:
            run_fixture(fx)
        except Exception as e:
            check(f"fixture {fx}: live run", False, f"{type(e).__name__}: {e}")

    print("\nREADY" if not failed else "\nNOT READY — fix the FAIL lines above")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
