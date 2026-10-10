# Timeline

All times are Pakistan time, Saturday 10 October and Sunday 11 October 2026. The demo is Sunday 12:02–12:07 in the SEECS Lecture Hall. This file is the working clock. The milestone names match [SRS.md](SRS.md) section 16. Acceptance is defined in [PROJECT.md](PROJECT.md).

Four tracks run in parallel: speech, score, board, talk. One person can hold two tracks. The presenting laptop is chosen before Saturday 18:00 and is the only machine that matters after that.

## Saturday 10 October

### 10:30–11:00 — Claim and boot

Everyone clones `ArslanSiddiqui75/prearrival`, creates a venv, and copies `.env.example` to `.env`.

- Speech puts `OPENAI_API_KEY` in `.env` and confirms one cloud call returns text.
- Score reads SRS sections 6–8 and runs `pytest` once, expecting red.
- Board runs `streamlit run app.py` and sees the shell.
- Talk reads `talk/SCRIPT.md` and `docs/AICON.md`.
- One person messages the organizers if the submission link is still unknown. If the link is only handed out at SEECS, that person goes to campus. The other three keep building.

### 11:00–13:00 — Gate: board with fake fields

- Score implements `score_news` and `decide` until `pytest` is green. Push as soon as it is.
- Board renders Fixture A from a hardcoded field dict: big P1, checklist, NEWS2 arithmetic, prep lead time of 8 minutes. No cloud call in this gate.
- Speech records both notes (`fixtures/a/note.txt`, `fixtures/b/note.txt`) as `audio.wav`, photographs or mocks two monitor images, and writes the numbers actually visible into `photo.json`.
- Talk drafts six slides from the script. No new claims.

**13:00 stop.** If pytest is still red, the score owner stops new cases and fixes the failing test. If the board cannot show fake fields, the talk owner sits with the board owner. Speech does not block this gate.

### 13:00–15:30 — Live extraction, still separate

- Speech implements `transcribe`, `read_monitor`, and `extract_note`. Each function prints `requested_at`. Fixture A returns evidence quotes. Then Fixture B.
- Board keeps using fake fields until speech pushes a working call. Do not invent thresholds in `app.py`.
- Talk picks the one literature number (door-to-CT or door-to-needle) and writes the citation on the slide as published context.

### 15:30–18:00 — Gate: both fixtures live

Wire the board to `transcribe`, `read_monitor`, `extract_note`, `score_news`, and `decide`. Run Fixture A, then Fixture B, on the phone hotspot, on the presenting laptop.

**18:00 done means:**

- Fixture A shows a timestamp, quotes, partial NEWS2, P1, resus bay, CT, senior review, prep lead time 8.
- Fixture B shows P3, cubicle, limb x-ray.
- `pytest` is green.
- The presenting laptop did both runs with hall Wi-Fi unused.

If 18:00 slips, cut in this order: live mic stays unbuilt, Fixture B can wait until after A is stable, no new mechanisms, no slide polish.

### 18:00–21:00 — Demo path only

Fix whatever broke on the presenting laptop. Re-run A twice. If both succeed, speech may try live English into the mic once. If that attempt is shaky, delete it from the talk. The stage promise stays the saved files.

**21:00 feature freeze.** No new screens, no new mechanisms, no dependency bumps. After this, only bugs that stop Fixture A.

### 21:00–23:00 — Submission pack

- Pull `main` on the presenting laptop and run Fixture A one last time.
- Record that successful run. The recording is the submission backup. The stage demo is still the live call.
- Submit whatever the organizers asked for (repo link, zip, form). The public schedule says Saturday midnight with no extensions. If the link is on site, the person at SEECS submits before leaving.
- Charger, mouse, hotspot phone, and the laptop that just succeeded go in one bag.

## Sunday 11 October

Finals run 9:00–14:00 in the Lecture Hall. Lunch on the public schedule is 13:00, after your slot.

| Time | Where | What |
|---|---|---|
| 9:30 | SEECS | Whole team on campus. Presenting laptop and hotspot in the bag. |
| 10:00 | Outside the Lecture Hall | Confirm the room. Join the hotspot. Run Fixture A once. If it fails, use the remaining hour on that bug only. |
| 10:30 | Same | Rehearsal 1, phone timer, full five minutes, out loud. |
| 11:15 | Same | Rehearsal 2. The second run is the one you keep. |
| 11:30 | Same | Acceptance check from PROJECT.md. If A works, you are done. |
| 11:50 | Inside the hall | Seated, laptop open, demo loaded, hotspot connected. They wait 2 minutes past 12:02, then the slot moves to the end. |
| 12:02–12:07 | Stage | Fixture A. Safety line. Literature number labeled as literature. Fixture B only if a judge asks whether every patient is a resus. |

After the slot, stop changing the repo until submissions are closed.

## If the clock slips

Keep Fixture A, the timestamp, the partial NEWS2 arithmetic, the fixed checklist, and the safety line. Drop live mic, Urdu, a second app, and any sentence that says the team measured minutes in a real ER.
