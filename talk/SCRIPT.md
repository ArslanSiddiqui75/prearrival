# Five-minute talk

One speaker. Phone timer. Presenting laptop on the phone hotspot.

Slides (six): https://claude.ai/artifact/X3xYC58YmNxFv9gk1rRRY1 (private until shared from its Share menu). Each slide has speaker notes. Download it as PDF or PPTX before Sunday so the deck works offline.

Safety line, say it out loud: "This prepares the room. It does not diagnose, and it does not replace the nurse's triage."

| Time | Slide | What you do |
|---|---|---|
| 0:00–0:20 | 1 Cover | Name, team, one line on what PreArrival does. |
| 0:20–0:40 | 2 Problem | The ER learns about the patient when the stretcher arrives. Pulsara and Twiage already take forms. This takes a messy voice note and a monitor photo. |
| 0:40–1:20 | 3 Pipeline | Cloud transcript and cloud photo read run in parallel. A model pulls the fields with quotes. Rules compute partial NEWS2 and look up a fixed table. Point at the request timestamp. |
| 1:20–4:00 | 4 Demo, then the board | Fixture A, Send live (about 9 s). Pause on the timestamps, the evidence quotes, the arithmetic (HR 105 → 1, not alert → 3, total 4; RR and temp missing), P1, resus bay, CT, senior review. Prep lead time 8 min. |
| 4:00–4:20 | 5 Impact | 8 min lead time. Published context: 2018 AHA/ASA guideline targets imaging within 20 min of arrival. Say the limit: not a measured saving. |
| 4:20–4:40 | 6 Safety | Safety line, word for word. |
| 4:40–5:00 | Board | If a judge asks whether every case is a resus: Fixture B, Send live. Ankle, alert, P3, cubicle, limb x-ray. |

Live mic only if the file path has already succeeded twice on this laptop.

## Live mic (optional)

On the board, switch "Voice note" to **Live mic**, press the record button, speak, stop, then Send live. The monitor photo still comes from the selected fixture. The board labels the run "voice: live mic".

- Say it like a radio handoff: ETA, what happened, alert or confused, on oxygen or not. Example: "Crew two, about ten out. Sixty-year-old woman, crushing chest pain, alert, resp rate twenty-four, on four litres of oxygen."
- The browser asks for mic permission the first time. Allow it during setup, not on stage.
- Works only from `http://localhost` on the presenting laptop. Browsers block the mic on a plain-http network address.
- English only. If one attempt in rehearsal is shaky, drop it from the talk.

## Before the slot

- Free-tier Groq limit: the vision model allows about 3 Send-live clicks per minute. Don't click repeatedly in the 2 minutes before the slot.
- Board open at `http://localhost:8501` (`streamlit run app.py`), Fixture A selected, browser zoomed so P1 is readable from the back.
- Hotspot on, hall Wi-Fi off. At 10:00 run `python scripts/preflight.py a b` and expect READY. Last test click at least 2 minutes before 12:02.
- If Send live spins longer than about 15 s, it is the free-tier rate limit retrying. Keep talking through the pipeline slide; it finishes on its own.

## Likely questions

- Why not let the model choose the priority? Free-form clinical orders are a hallucination risk. The table is fixed and anyone can read it.
- What if the photo is unreadable? That vital shows as missing and is not scored. It is never assumed normal.
- Is the monitor photo the real patient? No. It is a stand-in openly licensed photo, credited on the board, read live by the vision model.
- Is the voice real? It is a synthetic voice reading the paramedic note. It still goes through live speech-to-text.
