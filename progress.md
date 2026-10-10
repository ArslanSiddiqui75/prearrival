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

- [x] `score_news` per SRS §6 (partial, Scale 1, oxygen +2, breakdown, missing, any_red)
- [x] `decide` per SRS §7–8 (first-match priority, first-match prepare-for row, reasons)
- [x] `pytest` green (12 tests; verified by calling the test functions directly, real pytest run pending)

## Speech and vision (`src/transcribe.py`, `src/vision.py`, `src/extract_note.py`, `fixtures/`)

- [x] `transcribe` → cloud STT, returns text + requested_at
- [x] `read_monitor` → cloud vision, nulls for unreadable values, evidence, requested_at
- [x] `extract_note` → cloud model, schema fields + evidence quotes, nulls when absent
- [ ] Fixture A: `audio.wav` (todo, TTS) · [x] `monitor.jpg` Tempus Pro, HR 105 · [x] `photo.json`
- [ ] Fixture B: `audio.wav` (todo, TTS) · [x] `monitor.jpg` IntelliVue, NBP 129/57 · [x] `photo.json`
- [ ] Both fixtures return live JSON matching `expected.json`

## Board (`app.py`)

- [x] Input panel: fixture A / B picker, run button
- [x] Shows request timestamps, extracted fields with evidence quotes
- [x] NEWS2 arithmetic + missing list
- [x] Large priority + large checklist (readable from back of hall)
- [x] Prep lead time = spoken ETA; one published door-to-CT/needle figure labeled as literature
- [x] Imports `decide`; no thresholds in UI
- [x] Clear error on network failure (no fake fallback)

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

## Notes

- Speech, vision and extraction code is written against Groq but **not yet run live**. It needs `GROQ_API_KEY`.
- The literature figure in `app.py` (`LITERATURE`) needs checking by the talk owner before the demo.
- `audio.wav` plan: generate it from `note.txt` with TTS (Groq Orpheus or an offline engine). No public dataset has our scripts.
- With the human-read photo numbers, the rules give A = P1 (resus bay, CT, senior review) and B = P3 (cubicle, limb x-ray), matching `expected.json`.
- Fixture B risk: the photo also shows an arterial line at 100/59. The vision prompt says to prefer the cuff NBP. Watch this on the first live run.
