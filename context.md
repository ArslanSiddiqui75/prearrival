# Session context — read this first

Snapshot for anyone (human or AI session) picking up the work cold. Keep it current: update **Status** and **Session log** before ending a session.

Source of truth order: [docs/SRS.md](docs/SRS.md) (signed spec) > [docs/PROJECT.md](docs/PROJECT.md) (why, settled decisions) > [docs/AICON.md](docs/AICON.md) (event rules) > this file. This file summarizes; it never overrides the spec.

## One-paragraph summary

PreArrival is an ambulance-to-ER handoff board for team VisionForge, AICON'26 Build with AI, Health Operations. A saved English voice note (wav) and a monitor photo (jpg) are sent live to a cloud model (OpenAI). The model extracts fields plus evidence quotes only. A rules layer computes a partial NEWS2 (Scale 1, missing params stay missing) and a fixed table sets priority (P1/P2/P3) and a prepare-for list. One Streamlit screen for the ER charge nurse. Demo: Sunday 11 Oct 2026, 12:02–12:07, SEECS Lecture Hall, laptop on phone hotspot.

## Hard rules (don't reopen)

- Model extracts fields + evidence. It never assigns priority or writes orders/checklists.
- Missing fields stay `null`. Never impute a normal value or 0.
- NEWS2 Scale 1 only. `on_oxygen` true adds 2. Show the arithmetic and the missing list.
- Priority + prepare-for come only from `src/decide.py` (SRS §7, §8). UI never reimplements thresholds.
- Every cloud call returns `requested_at` (ISO timestamp at send time). No silent fixture fallback that fakes a live call.
- Do not invent monitor numbers. `photo.json` holds only what is actually readable on `monitor.jpg`.
- Live mic is optional, only after the file path works twice on the presenting laptop + hotspot.
- API key only in `.env` (gitignored). Never commit it.
- Out of scope: Urdu on stage, mobile app, multi-patient, Scale 2, free-form LLM orders, GPS, claims of measured minutes saved.
- CodeBlue (ICU alarm idea) is dropped. Don't rebuild it.
- Respect file ownership (README owners table). Don't edit another track's files during freeze.

## Layout

| Path | What | Owner track |
|---|---|---|
| `src/transcribe.py` | `transcribe(audio_path) -> {text, requested_at}` | Speech/vision |
| `src/vision.py` | `read_monitor(image_path) -> {hr, sbp, dbp, spo2, evidence, requested_at}` | Speech/vision |
| `src/extract_note.py` | `extract_note(text) -> {consciousness, mechanism, eta_min, on_oxygen, rr, temp_c, evidence}` | Speech/vision |
| `src/news.py` | `score_news(fields) -> {points, missing, any_red, breakdown}` | Score/table |
| `src/decide.py` | `decide(fields, score) -> {priority, prepare_for, reasons}` (pure) | Score/table |
| `app.py` | Streamlit board | Board |
| `tests/` | `test_news.py`, `test_decide.py` | Score/table |
| `fixtures/a`, `fixtures/b` | `note.txt`, `expected.json`; to add: `audio.wav`, `monitor.jpg`, `photo.json` | Speech/vision |
| `talk/SCRIPT.md` | 5-minute script | Talk |

Fixture A: head injury, confused, ETA 8 → P1, resus bay / CT / senior review. Fixture B: alert ankle, ETA 12 → P3, cubicle / limb x-ray.

## Run

```bash
python3 -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                              # then set OPENAI_API_KEY
pytest
streamlit run app.py
```

## Status

See [progress.md](progress.md) for the task checklist. Headline as of the last update:

- Repo is at the initial stubs. All `src/` functions raise `NotImplementedError`. `pytest` red.
- This machine (`adan`, GitHub KodeeBz) works on branch `machine/adan` and may edit all tracks.

## Team decisions (not yet in docs/PROJECT.md)

- 2026-10-10: This machine may edit every track (user's call), not just one owner's paths.
- 2026-10-10: The cloud provider is **Groq**, not OpenAI. The key goes in `.env` as `GROQ_API_KEY`. README and `.env.example` still say OpenAI and need updating.
- 2026-10-10: Prefer sourced sample media over recording our own. Monitor photos come from openly licensed sources (license noted next to the file). `photo.json` still holds only the numbers actually readable in the photo.

## Fixture media

- A `monitor.jpg`: Tempus Pro ambulance monitor (Wikimedia, SEM, CC BY-SA). HR 105, NIBP 120/80, SpO2 96. Spanish labels.
- B `monitor.jpg`: Philips IntelliVue MP70 (Flickr, Quinn Dombrowski, CC BY-SA 2.0). HR 73, NBP 129/57, SpO2 100. Also shows ABP 100/59, which must not be read as the systolic.
- Both are stand-in monitors, not the patients in the notes. The board caption says so and credits the source. Sources and readings are in each `photo.json`.
- Other candidates (none fit as well) were downloaded to a scratch dir and are not in the repo.

## Open questions

- Which Groq models to use for speech-to-text, vision and extraction? Check what Groq currently offers.
- Audio: is a TTS-generated `audio.wav` from `note.txt` acceptable for the stage case? A real paramedic recording that matches our scripts won't exist online.
- Context files are pushed on `machine/adan`. Should they be merged to `main`?

## Session log

Newest first. One or two lines per session: what changed, what's next.

- 2026-10-10 11:40 PKT — Six-slide deck published as a claude.ai Slides artifact (https://claude.ai/artifact/X3xYC58YmNxFv9gk1rRRY1). talk/SCRIPT.md rewritten to match. Literature figure corrected to the 2018 AHA/ASA guideline (the 2019 update dropped the 20-minute number). Remaining: hotspot test, rehearsals, merge to main.
- 2026-10-10 11:20 PKT — Generated audio.wav for A and B with Groq Orpheus TTS. Full live pipeline passes for both fixtures (18:00 milestone done). Models: whisper-large-v3-turbo, qwen/qwen3.8-27b, openai/gpt-oss-120b. Watch the free-tier vision rate limit (see progress.md). Next: talk slides, literature figure, hotspot test.
- 2026-10-10 11:05 PKT — Accepted the repo invite as KodeeBz and pushed `machine/adan`. Push from this machine with `flatpak-spawn --host git push`, because VS Code runs in a Flatpak sandbox and gh only exists on the host.
- 2026-10-10 10:55 PKT — Implemented news/decide (12 tests pass), Groq calls (untested live, no key yet), board, and switched to Groq. Added fixture photos and photo.json. pip is slow on this network.
- 2026-10-10 10:35 PKT — Created branch `machine/adan` and pushed the context files. User chose Groq and sourced sample media. Searching for monitor photos next.
- 2026-10-10 10:20 PKT — Cloned repo (user GitHub: KodeeBz). Read all docs + stubs. Created `context.md`, `progress.md`, `CLAUDE.md`. No code changes yet.
