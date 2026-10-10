"""Pull non-monitor fields from the transcript. Speech owner implements this."""

MECHANISMS = {"head_injury", "chest_pain", "limb_injury", "shortness_of_breath", "stroke", "other"}

PROMPT = """You extract structured fields from a paramedic's radio handoff note for an ER.
Extract only what the note states. If the note does not state a field, use null. Never assume a normal value.

Fields:
- consciousness: "alert" if the patient is described as alert / talking normally / oriented; "not_alert" if confused, disoriented, drowsy, responds only to voice or pain, or unresponsive; else null.
- mechanism: one of "head_injury", "chest_pain", "limb_injury", "shortness_of_breath", "stroke", "other"; null if no complaint is given.
- eta_min: arrival time in minutes as an integer (words like "eight" -> 8); else null.
- on_oxygen: true if on supplemental oxygen, false if the note says not on oxygen; null if not mentioned.
- rr: respiratory rate in breaths/min if stated; else null.
- temp_c: temperature in Celsius if stated; else null.

For each non-null field, add an evidence quote: a short phrase copied word for word from the note.

Return only a JSON object:
{"consciousness": ..., "mechanism": ..., "eta_min": ..., "on_oxygen": ..., "rr": ..., "temp_c": ...,
 "evidence": {"<field>": "<exact quote>"}}"""

# Appended to an evidence quote that is not found word for word in the note. src/confidence.py reads it.
NOT_FOUND_MARK = " [not found verbatim in note]"

FIELDS = ("consciousness", "mechanism", "eta_min", "on_oxygen", "rr", "temp_c")


def extract_note(text: str) -> dict:
    """Read consciousness, mechanism, eta_min, on_oxygen, rr, temp_c.

    mechanism is one of head_injury, chest_pain, limb_injury,
    shortness_of_breath, stroke, other.
    consciousness is "alert" or "not_alert".
    Each present field has a short evidence quote taken from text.
    Missing fields stay null.
    """
    from src.groq_client import TEXT_MODEL, as_float, as_int, client, parse_json
    from src.transcribe import now_iso

    requested_at = now_iso()
    reply = client().chat.completions.create(
        model=TEXT_MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": text},
        ],
    )
    raw = parse_json(reply.choices[0].message.content)

    out = {
        "consciousness": raw.get("consciousness") if raw.get("consciousness") in ("alert", "not_alert") else None,
        "mechanism": raw.get("mechanism") if raw.get("mechanism") in MECHANISMS else None,
        "eta_min": as_int(raw.get("eta_min")),
        "on_oxygen": raw.get("on_oxygen") if isinstance(raw.get("on_oxygen"), bool) else None,
        "rr": as_int(raw.get("rr")),
        "temp_c": as_float(raw.get("temp_c")),
    }

    # Keep the model's quote, but flag it when it is not actually in the note.
    model_evidence = raw.get("evidence") or {}
    evidence = {}
    for field in FIELDS:
        if out[field] is None:
            continue
        quote = str(model_evidence.get(field) or "").strip()
        if quote and quote.lower().strip(" .\"'") in text.lower():
            evidence[field] = quote
        else:
            evidence[field] = f"{quote or '(no quote)'}{NOT_FOUND_MARK}"
    out["evidence"] = evidence
    out["requested_at"] = requested_at
    return out
