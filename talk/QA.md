# Judge Q&A

Short answers first. Each one is true for what we built; don't stretch them.

**Why not let the AI choose the priority?**
Free-form clinical orders are a hallucination risk: a model can invent a CT or a cross-match. Our model only reads the note and the photo and quotes its source. A fixed, published-style table makes the decision, and anyone can check it by hand.

**How do you know the extraction is right?**
Every value shows its evidence: a quote from the transcript or "monitor photo". On our two fixtures the photo read matched a human read 6 out of 6 times, and the note fields matched every time. When there's a checkable reason for doubt (unclear speech, a quote not in the transcript, an implausible vital, digits cut off in the photo), the value is flagged and listed under "confirm with crew". It is still scored, never silently changed.

**What if a vital is missing?**
It stays missing. The score shows it as "not scored, not assumed normal" and asks the ER to confirm it with the crew. That's why we call it a partial NEWS2.

**Why NEWS2?**
It's the Royal College of Physicians early-warning score, widely used for deteriorating adults, and its thresholds are public. We use Scale 1 only.

**Does every patient become a resus?**
No. Fixture B, an alert ankle injury, comes out P3: cubicle and limb x-ray. (Show it.)

**Is the ambulance tracking real?**
No, and the board says so on screen: simulated position, simulated roadblock, on an illustrative road graph. It shows the workflow: the crew decides the route, the board updates the ETA, and the triage never changes. Real GPS and live traffic are the next integration, not something we're claiming today.

**Who would use this, and who would buy it?**
The ER charge nurse uses the board; the paramedic just talks. The buyer is the hospital or the emergency service. The natural pilot is Rescue 1122 handoffs into a tertiary ER like PIMS, which receives over 8,000 patients a day.

**How much time does it actually save?**
We claim lead time, not a measured saving: the checklist exists for the whole drive, 8 minutes in our case. Measuring real minutes saved needs a pilot comparing door-to-CT with and without it. We say that limit out loud on purpose.

**What about patient data and privacy?**
The demo uses no real patient data: synthetic voice notes and openly licensed stand-in monitor photos. A real deployment would need consent, an agreement with the cloud provider or on-premise models, and no storage of audio beyond the handoff.

**What happens without the network?**
The cloud calls fail visibly on the board. We never fake a result. The map still draws without tiles. For production you'd run speech and extraction models on-premise or at the edge.

**Urdu or mixed speech?**
Not today. Whisper is reliable on English; mixed Urdu-English is a real need and our next language step, but we didn't want to promise it on stage.

**How is this different from Pulsara or Twiage?**
They notify the ER from a form typed in the ambulance. PreArrival takes unstructured speech and a monitor photo, and the score is something a judge can recompute.

**Which models?**
On Groq: Whisper large-v3 turbo for speech, Qwen 3.8 27B vision for the photo, GPT-OSS 120B for the note fields. About 4 seconds end to end.

**Is this a medical device?**
It prepares the room. It does not diagnose and does not replace the nurse's triage. Keeping that boundary is a design decision, not an afterthought.
