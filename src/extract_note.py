"""Pull non-monitor fields from the transcript. Speech owner implements this."""


def extract_note(text: str) -> dict:
    """Read consciousness, mechanism, eta_min, on_oxygen, rr, temp_c.

    mechanism is one of head_injury, chest_pain, limb_injury,
    shortness_of_breath, stroke, other.
    consciousness is "alert" or "not_alert".
    Each present field has a short evidence quote taken from text.
    Missing fields stay null.
    """
    raise NotImplementedError(f"extract_note is not implemented ({len(text)} chars)")
