# PreArrival — Software Requirements Spec

Team: VisionForge. Domain: Health Operations, AICON'26 Build with AI.
Demo: Sunday 11 October 2026, 12:02–12:07, SEECS Lecture Hall.
Repo: private, `ArslanSiddiqui75/prearrival`.

This file is the signed spec. If code and this file disagree, this file wins until the team edits it on purpose.

## 1. Problem

The ER learns about a patient when the stretcher arrives. Beds, blood, CT, and specialists are arranged after the clock has started.

Form-based incumbents already do prehospital notification (Pulsara, Twiage). The wedge is unstructured English speech plus a monitor photo plus an inspectable score. The model does not invent the priority.

## 2. User and surface

The user is the ER charge nurse, watching one incoming patient.

One laptop screen. The paramedic step is an input panel on that screen. A separate mobile app is out of scope.

## 3. Stage promise

A saved English voice note plus a saved monitor photo. Both are sent to the cloud live during the slot. The board shows the request timestamp so a judge can see the result was not pre-filled.

Live English into the mic is a second milestone. Start it only after the file path has succeeded twice on the presenting laptop, on the phone hotspot.

A dead network means a dead demo. That risk is accepted. Bring the hotspot and the API key. Do not commit the key.

## 4. Pipeline

1. `transcribe(audio_path)` sends the wav to cloud speech-to-text.
2. `read_monitor(image_path)` sends the photo to a cloud vision model.
3. `extract_note(text)` pulls the non-monitor fields from the transcript.
4. `score_news(fields)` computes a partial NEWS2.
5. `decide(fields, score)` applies the fixed table and returns priority plus the prepare-for list.

The model extracts fields and an evidence quote for each field. It does not assign priority and it does not write orders.

## 5. Field schema

```text
hr: int or null
sbp: int or null
dbp: int or null
spo2: int or null
rr: int or null
temp_c: float or null
consciousness: "alert" or "not_alert" or null
on_oxygen: bool or null
mechanism: "head_injury" | "chest_pain" | "limb_injury" | "shortness_of_breath" | "stroke" | "other" or null
eta_min: int or null
evidence: map of field name to a short quote from the note or "monitor photo"
```

Missing fields stay null. They are never filled with a normal value. Diastolic BP is extracted for display. It is not part of NEWS2.

## 6. Partial NEWS2

Score only parameters that were extracted. Show the missing list on the board. Do not impute 0 for a missing parameter. Show the arithmetic.

Use NEWS2 Scale 1 for SpO2. Do not implement Scale 2. Supplemental oxygen adds 2 when `on_oxygen` is true.

- Respiratory rate: ≤8 = 3, 9–11 = 1, 12–20 = 0, 21–24 = 2, ≥25 = 3.
- SpO2 Scale 1: ≤91 = 3, 92–93 = 2, 94–95 = 1, ≥96 = 0.
- Oxygen: 2 if `on_oxygen` is true, otherwise 0.
- Systolic BP: ≤90 = 3, 91–100 = 2, 101–110 = 1, 111–219 = 0, ≥220 = 3.
- Pulse (`hr`): ≤40 = 3, 41–50 = 1, 51–90 = 0, 91–110 = 1, 111–130 = 2, ≥131 = 3.
- Consciousness: alert = 0, not alert = 3.
- Temperature °C: ≤35.0 = 3, 35.1–36.0 = 1, 36.1–38.0 = 0, 38.1–39.0 = 1, ≥39.1 = 2.

`score_news` returns `{points, missing, any_red, breakdown}`. `any_red` is true when any scored parameter is 3. `breakdown` maps each scored parameter to its points.

## 7. Priority

Apply the first matching rule.

- P1 when `points >= 7`, or `any_red` is true, or mechanism is `head_injury` while consciousness is `not_alert`, or mechanism is `chest_pain` while `sbp <= 90`, or mechanism is `stroke`.
- P2 when `points` is 5 or 6 and no P1 rule fired.
- P3 otherwise.

## 8. Prepare-for table

Fixed rows. The model does not write this list. Use the first matching row.

- Head injury and not alert: resus bay, CT, senior review
- Chest pain and systolic BP at or below 90: resus bay, ECG, cardiology
- Shortness of breath: resus bay, oxygen, chest x-ray
- Limb injury and the priority is not P1: cubicle, limb x-ray
- Any other P1: resus bay, senior review
- Any other P2 or P3: cubicle, repeat vitals

Stroke is a P1 trigger. Its checklist is the generic P1 row (resus bay, senior review) unless a later edit to this file adds a stroke row.

## 9. Contracts

- `transcribe(audio_path) -> {text, requested_at}`
- `read_monitor(image_path) -> {hr, sbp, dbp, spo2, evidence, requested_at}`
- `extract_note(text) -> {consciousness, mechanism, eta_min, on_oxygen, rr, temp_c, evidence}`
- `score_news(fields) -> {points, missing, any_red, breakdown}`
- `decide(fields, score) -> {priority, prepare_for, reasons}`

`decide` is a pure function of sections 7 and 8. The UI calls it. The UI does not reimplement thresholds.

`requested_at` is an ISO timestamp from the moment the cloud call is sent.

## 10. Fixtures

Both fixtures run live through the API. The note text is in `fixtures/a/note.txt` and `fixtures/b/note.txt`. The speech owner adds `audio.wav` and `monitor.jpg` and writes the numbers they can actually read into `photo.json`. Do not invent monitor numbers.

Fixture A is the stage case. Confused patient after a head strike. ETA is spoken as eight minutes. The photo must show an abnormal heart rate or systolic BP. Expect P1 and resus bay, CT, senior review.

Fixture B is the contrast case. Painful swollen ankle, patient alert. ETA is spoken as twelve minutes. The photo must show normal heart rate, systolic BP, and SpO2. Expect P3 and cubicle, limb x-ray.

The talk uses A. B is one extra click if a judge asks whether every patient becomes a resus.

## 11. Impact line

On screen, prep lead time equals the spoken ETA in minutes, because the checklist exists before arrival. Beside it, cite one published door-to-CT or door-to-needle figure and label it as published context, not as a measurement by this team.

## 12. Safety line

Say this on stage: "This prepares the room. It does not diagnose, and it does not replace the nurse's triage."

## 13. Out of scope

Urdu on stage, GPS, a multi-patient board, free-form LLM orders, a mobile app, Scale 2 NEWS2, and any claim of measured minutes saved in a real ER.

## 14. Demo constraints

Sunday 11 October 2026, 12:02–12:07, SEECS Lecture Hall. Presenting laptop on the phone hotspot. One speaker. File path first. Wi-Fi in the hall is not the plan.

## 15. Work split

| Owner | Files | Done when |
|---|---|---|
| Speech and vision | `src/transcribe.py`, `src/vision.py`, `src/extract_note.py`, `fixtures/*/audio.wav`, `fixtures/*/monitor.jpg`, `fixtures/*/photo.json` | Both fixtures return live JSON with evidence quotes and timestamps |
| Score and table | `src/news.py`, `src/decide.py`, `tests/test_news.py`, `tests/test_decide.py` | `pytest` is green |
| Board | `app.py` | Input panel, NEWS2 arithmetic, checklist, prep lead time, readable from the back of the hall. Imports `decide`. Does not reimplement thresholds |
| Talk | `talk/SCRIPT.md` | Six slides, two timed runs on the hotspot, Fixture A then optional B |

## 16. Clock

Saturday 13:00 — board renders with fake fields. Saturday 18:00 — both fixtures return live JSON. Saturday 21:00 — feature freeze. Saturday 23:00 — submission pack. Sunday 10:30 — two rehearsals on the presenting laptop. Be at SEECS if the submission link is handed out on site.
