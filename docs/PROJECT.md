# Project requirements and decision record

Signed product behavior is [SRS.md](SRS.md). Event constraints are [AICON.md](AICON.md). This file is why the spec looks like that, so a new session does not reopen settled questions.

## Product

PreArrival is an ambulance-to-ER handoff board. A paramedic voice note and a photo of the vitals monitor become structured fields. A partial NEWS2 and a fixed table produce a triage priority and a prepare-for checklist on one ER screen.

Original pitch, before the drill narrowed it:

- Input: a paramedic voice note, messy, in any language mix, plus a photo of the vitals monitor.
- AI: speech-to-text, then a multimodal model reads the photo (HR, BP, SpO2, GCS, suspected condition). A rule layer computes NEWS2. A model then writes triage priority and a prepare-for checklist (resus bay, CT, blood cross-match, cardiology).
- Solution: a paramedic mobile app and a live ER dashboard with ETA, priority, and resources.
- Impact: minutes saved from door to treatment.
- Wow: speak a chaotic note on stage and the projected dashboard fills in within seconds.

## Requirements drill

Asked on Saturday 10 October 2026. Answers are binding.

**What is the stage input?**

A saved English voice note plus a saved monitor photo is the promise. Live English into the mic is the expansion, and only after the file path has succeeded twice on the presenting laptop. A live Urdu-English mix is out. "Any language" is not a promise. Whisper-class models are reliable on rehearsed English. Code-switching is not a five-minute bet.

**Where do the models run?**

Cloud calls are allowed. The team brings a phone hotspot and an API key and accepts that a dead network kills the demo. The board shows the request timestamp so the result is visibly live, not a JSON file baked into the UI.

The hybrid option (checked-in photo result if the network drops, offline speech) was not chosen. Do not add a silent fixture fallback that pretends the call succeeded.

## What the drill locked after those answers

- User: the ER charge nurse, one incoming patient.
- Surface: one laptop screen. The paramedic step is the input panel. No mobile app.
- The model extracts fields and evidence quotes. It does not assign priority and it does not write orders.
- Score: partial NEWS2 on extracted parameters only. Missing inputs stay missing. Never impute 0. Scale 1 only. Oxygen adds 2. Show the arithmetic.
- Priority and the prepare-for list come from the table in the SRS. Free-form checklist text from the model is a clinical hallucination risk (invented CT, invented cross-match).
- Two fixtures, both sent live: A is head injury, confused, abnormal photo, P1, resus and CT. B is an alert ankle, normal photo, P3, cubicle and x-ray. The talk runs A. B answers the "every patient is a resus" question.
- Impact number on screen: prep lead time equals the spoken ETA, because the checklist exists before arrival. A published door-to-CT or door-to-needle figure may sit beside it, labeled as literature, not as this team's measurement.
- Safety line: "This prepares the room. It does not diagnose, and it does not replace the nurse's triage."

## Rejected alternative

CodeBlue Acoustic, an ICU alarm-fatigue console, was the previous candidate and is dropped. Do not rebuild it in this repo.

Why it lost: Health Operations examples in the allocation email are triage and hospital resource management, which PreArrival is. Alarm suppression also walks into a medical-device claim. The Joint Commission and the FDA have already tied silenced alarms to deaths. A live lecture-hall microphone plus a from-scratch spectrogram model was not going to be reliable by Sunday noon.

Useful residue, already applied here: the bedside-alarm idea taught the safety boundary (the system prepares, it does not act on the patient), the impact line has to be a number with a stated limit, and the demo path has to be a checked-in file before anyone trusts a live mic.

## Acceptance

The MVP is done at Sunday 11:30 only if all of these are true on the presenting laptop, on the phone hotspot:

- Fixture A plays from disk, the cloud call is live, and the board shows a request timestamp, evidence quotes, partial NEWS2 arithmetic, P1, and resus bay, CT, senior review.
- Prep lead time shows 8 minutes for Fixture A.
- Fixture B is one click away and shows P3, cubicle, limb x-ray.
- `pytest` is green for `tests/test_news.py` and `tests/test_decide.py`.
- The safety line is in the talk.
- Wi-Fi can be off if the hotspot is up. The hall network is not required.
- The API key is only in `.env`.

Live mic is not part of acceptance.

## Non-functional

- The board is readable from the back of SEECS Lecture Hall. Large priority, large checklist.
- One speaker, five minutes, script in [../talk/SCRIPT.md](../talk/SCRIPT.md).
- Feature freeze Saturday 21:00. Submission pack Saturday 23:00. Two rehearsals Sunday 10:30.
- Owners and paths are in the README. Do not edit another owner's files to "help" during the freeze.

## Prior art to be able to say out loud

Pulsara and Twiage already notify an ER from a form. PreArrival's wedge is unstructured speech, a monitor photo, and a score the judge can recompute. NEWS2 is the Royal College of Physicians early-warning score. This build uses Scale 1 and leaves missing parameters blank.
