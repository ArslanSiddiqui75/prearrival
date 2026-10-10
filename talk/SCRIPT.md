# Five-minute talk

One speaker. Phone timer. Presenting laptop on the phone hotspot.

Slides (six): https://claude.ai/artifact/X3xYC58YmNxFv9gk1rRRY1 (private until shared from its Share menu). Each slide has speaker notes. Download it as PDF before Sunday. Slide sources are in `talk/deck/`.

Safety line, word for word: "This prepares the room. It does not diagnose, and it does not replace the nurse's triage."

## Setup before you start talking

- Board open at http://localhost:8501 in its own browser window. Fixture **A** selected, Voice note **Saved file**, **Ambulance tracking (simulated) ON**.
- No result on screen yet. If one is there from rehearsal, reload the page (F5) and turn tracking back on.
- Slides in a second window. Alt+Tab between them.

## The run

| Time | Screen | Say and do |
|---|---|---|
| 0:00–0:15 | 1 Cover | "We're VisionForge. PreArrival gets the ER ready before the ambulance arrives." |
| 0:15–0:40 | 2 Problem | PIMS gets 8,000+ patients a day, three times its capacity. Rescue 1122 answered 2.5 million emergencies in Punjab last year; road crashes were the top cause. The ER still learns about the patient at the door. |
| 0:40–1:05 | 3 Pipeline | "AI reads, rules decide." Voice and photo go to the cloud in parallel; plain code scores and picks the checklist. |
| 1:05–1:15 | 4 Demo | "Bike crash, head strike, confused, eight minutes out." Alt+Tab to the board. |
| 1:15–1:25 | Board | Press **Send live**. While it runs (about 4 s): "That's the real voice note and monitor photo going to the cloud right now." |
| 1:25–1:40 | Board | "P1. Resus bay, CT, senior review. Eight minutes before he arrives." |
| 1:40–2:10 | Board | **Within 15 s of the result, click Inject roadblock (closed).** "Kashmir Highway just closed. The crew gets an alternate." Click **Accept**. "ETA eight to eleven; prep lead time updates. And still P1, same checklist. The route changed, the triage didn't." |
| 2:10–3:20 | Board (scroll down) | Evidence: the quote "He is confused, not answering properly". Arithmetic: heart rate 105 → 1, confused → 3, total 4. Resp rate and temperature listed as missing, not assumed normal, and the line "Confirm with crew". Point at the request timestamps: live. |
| 3:20–4:05 | 5 Impact | 8 minutes of lead time; 2018 AHA/ASA imaging target of 20 minutes, labelled literature. Say the limit: lead time, not a measured saving. Next step: test on recorded Rescue 1122 handoffs against nurse triage. |
| 4:05–4:45 | 6 Safety | Safety line, word for word. "Not every case is resus; it says what it doesn't know; no AI orders." |
| 4:45–5:00 | 6 Safety | "PreArrival: the ER is ready before the ambulance arrives. Thank you." |

If a judge asks whether every patient becomes a resus: board, Fixture **B**, Send live. Ankle, alert, P3, cubicle, limb x-ray.

## If something goes wrong

- **Send live spins past 15 s:** free-tier rate limit retrying. Keep talking; it finishes on its own.
- **"Live call failed" on screen:** say "the network dropped, here is the recorded run," and play the backup video. Never press Fake fields on stage.
- **Missed the 15 s roadblock window:** skip it and say "the crew can reroute around closures; the triage never changes". Don't click late: after 36 s there is no road left to block.
- **Map tiles don't load:** the route and labels still draw. Carry on.

## Live mic (optional, only if both rehearsals worked)

Switch Voice note to **Live mic**, record, stop, Send live. The monitor photo still comes from the selected fixture. English only. Allow mic permission during setup, not on stage. Works only from `http://localhost`.

Example: "Crew two, about ten out. Sixty-year-old woman, crushing chest pain, alert, resp rate twenty-four, on four litres of oxygen."

## Before the slot

- Groq free tier: about 3 Send-live clicks per minute. No clicks in the 2 minutes before 12:02.
- Hotspot on, hall Wi-Fi off. At 10:00 run `python scripts/preflight.py a b` and expect READY.
- Browser zoom so P1 is readable from the back (Ctrl +). At 1366×768 the crew alert and Accept stay on screen at 100%.

Q&A answers: [QA.md](QA.md).
