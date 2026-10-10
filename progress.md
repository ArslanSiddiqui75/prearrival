# Progress

Task checklist against the clock in [docs/SRS.md](docs/SRS.md) §16. Tick items as they land; add the commit hash where useful.

## Clock (Saturday 10 → Sunday 11 Oct 2026, PKT)

- [ ] Sat 13:00 — board renders with fake fields
- [ ] Sat 18:00 — both fixtures return live JSON
- [ ] Sat 21:00 — feature freeze
- [ ] Sat 23:00 — submission pack
- [ ] Sun 10:30 — two rehearsals on presenting laptop + hotspot
- [ ] Sun 12:02 — demo

## Score and table (`src/news.py`, `src/decide.py`, `tests/`)

- [ ] `score_news` per SRS §6 (partial, Scale 1, oxygen +2, breakdown, missing, any_red)
- [ ] `decide` per SRS §7–8 (first-match priority, first-match prepare-for row, reasons)
- [ ] `pytest` green

## Speech and vision (`src/transcribe.py`, `src/vision.py`, `src/extract_note.py`, `fixtures/`)

- [ ] `transcribe` → cloud STT, returns text + requested_at
- [ ] `read_monitor` → cloud vision, nulls for unreadable values, evidence, requested_at
- [ ] `extract_note` → cloud model, schema fields + evidence quotes, nulls when absent
- [ ] Fixture A: `audio.wav`, `monitor.jpg` (abnormal HR or SBP), `photo.json`
- [ ] Fixture B: `audio.wav`, `monitor.jpg` (normal HR, SBP, SpO2), `photo.json`
- [ ] Both fixtures return live JSON matching `expected.json`

## Board (`app.py`)

- [ ] Input panel: fixture A / B picker, run button
- [ ] Shows request timestamps, extracted fields with evidence quotes
- [ ] NEWS2 arithmetic + missing list
- [ ] Large priority + large checklist (readable from back of hall)
- [ ] Prep lead time = spoken ETA; one published door-to-CT/needle figure labeled as literature
- [ ] Imports `decide`; no thresholds in UI
- [ ] Clear error on network failure (no fake fallback)

## Talk (`talk/`)

- [ ] Six slides
- [ ] Safety line included
- [ ] Published literature figure chosen and cited
- [ ] Two timed runs on hotspot

## Acceptance (PROJECT.md) — all must be true Sun 11:30

- [ ] Fixture A from disk, live call, timestamp, evidence, NEWS2 arithmetic, P1, resus bay / CT / senior review
- [ ] Prep lead time shows 8 min for A
- [ ] Fixture B one click away: P3, cubicle, limb x-ray
- [ ] `pytest` green
- [ ] Safety line in talk
- [ ] Works on hotspot with hall Wi-Fi off
- [ ] API key only in `.env`
