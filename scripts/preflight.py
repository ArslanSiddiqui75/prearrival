"""One-command check for the presenting laptop: key, models, and one live Fixture A run.

    python scripts/preflight.py          # Fixture A only (3 cloud calls)
    python scripts/preflight.py a b      # both fixtures

Uses the same functions as the board. Prints PASS or FAIL per check and exits non-zero on any failure.
"""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.decide import decide  # noqa: E402
from src.groq_client import STT_MODEL, TEXT_MODEL, VISION_MODEL, client  # noqa: E402
from src.news import score_news  # noqa: E402

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

    fields = {k: v for k, v in {**note, **photo}.items() if k not in ("evidence", "requested_at")}
    plan = decide(fields, score_news(fields))

    note_diff = {k: (note[k], v) for k, v in expected["from_note"].items() if note[k] != v}
    photo_diff = {k: (photo[k], photo_truth[k]) for k in ("hr", "sbp", "dbp", "spo2") if photo[k] != photo_truth[k]}
    check(f"fixture {fx}: note fields", not note_diff, f"got vs expected {note_diff}" if note_diff else "")
    check(f"fixture {fx}: photo read", not photo_diff, f"got vs human read {photo_diff}" if photo_diff else "")
    check(
        f"fixture {fx}: {plan['priority']} {', '.join(plan['prepare_for'])}",
        plan["priority"] == expected["expect_priority"] and plan["prepare_for"] == expected["expect_prepare_for"],
        f"{secs:.1f}s",
    )


def main():
    try:
        available = {m.id for m in client().models.list().data}
        check("GROQ_API_KEY works", True)
    except Exception as e:
        check("GROQ_API_KEY works", False, f"{type(e).__name__}: {e}")
        sys.exit(1)
    for model in (STT_MODEL, VISION_MODEL, TEXT_MODEL):
        check(f"model available: {model}", model in available)

    for fx in sys.argv[1:] or ["a"]:
        try:
            run_fixture(fx)
        except Exception as e:
            check(f"fixture {fx}: live run", False, f"{type(e).__name__}: {e}")

    print("\nREADY" if not failed else "\nNOT READY — fix the FAIL lines above")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
