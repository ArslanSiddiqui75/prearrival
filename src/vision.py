"""Cloud monitor-photo read. Speech owner implements this."""

import base64
import mimetypes

PROMPT = """You are reading a photo of a patient vital-signs monitor.
Report only numbers that are clearly visible on the screen. If a value is not shown or not legible, use null. Never guess a normal value.

Return only a JSON object with exactly these keys:
{"hr": int|null, "sbp": int|null, "dbp": int|null, "spo2": int|null,
 "evidence": {"<field>": "<where on screen and what you read, e.g. 'green HR box: 132'>"}}

hr = heart rate / pulse (bpm). sbp/dbp = non-invasive blood pressure systolic/diastolic (mmHg, usually shown as 120/80). spo2 = oxygen saturation (%).
Labels may be abbreviated or in another language (e.g. FC = heart rate, PSNI = non-invasive BP, S/D = systolic/diastolic). The number in parentheses next to a BP is the mean; do not use it as sbp or dbp.
SpO2 is often a large blue or cyan number next to the pleth waveform, labeled SpO2 or Pleth; a value of 100 is valid.
If both a non-invasive cuff pressure (NBP, NIBP, PSNI) and an invasive arterial pressure (ABP, ART, IBP) are shown, use the non-invasive cuff pressure for sbp and dbp.
Include an evidence entry only for fields that are not null."""


def read_monitor(image_path: str) -> dict:
    """Send the monitor photo to a vision model.

    Returns hr, sbp, dbp, spo2, evidence, requested_at.
    Use null for a number the photo does not show. Never fill a normal default.
    evidence maps each present field to "monitor photo" plus what was read.
    """
    from src.groq_client import VISION_MODEL, as_int, client, parse_json
    from src.transcribe import now_iso

    mime = mimetypes.guess_type(image_path)[0] or "image/jpeg"
    with open(image_path, "rb") as f:
        data_url = f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"

    requested_at = now_iso()
    reply = client().chat.completions.create(
        model=VISION_MODEL,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
    )
    raw = parse_json(reply.choices[0].message.content)

    out = {k: as_int(raw.get(k)) for k in ("hr", "sbp", "dbp", "spo2")}
    model_evidence = raw.get("evidence") or {}
    out["evidence"] = {
        k: f"monitor photo: {model_evidence.get(k) or out[k]}" for k in ("hr", "sbp", "dbp", "spo2") if out[k] is not None
    }
    out["requested_at"] = requested_at
    return out
