"""Confidence flags from checkable signals. Pure functions, no network.

A flag means "confirm this with the crew". A flagged value is still scored: flags never
change a field, the NEWS2 score, the priority or the prepare-for list.
No model is asked to rate its own confidence. The signals are:
- Whisper's own avg_logprob for the segment holding a note field's quote
- an evidence quote that is not in the transcript word for word
- monitor values outside a physically plausible range
- how the digits look in the photo (vision legibility: clear / partial / unclear)
"""

from src.extract_note import NOT_FOUND_MARK

# Whisper segment average log-probability below this counts as unclear speech.
LOW_LOGPROB = -0.5

# Plausible monitor ranges (inclusive). Outside these, the read is probably wrong.
PLAUSIBLE = {"hr": (20, 250), "sbp": (50, 260), "dbp": (20, 160), "spo2": (50, 100)}

NOTE_FIELDS = ("consciousness", "mechanism", "eta_min", "on_oxygen", "rr", "temp_c")
MONITOR_FIELDS = ("hr", "sbp", "dbp", "spo2")

UNCLEAR_SPEECH = "unclear speech"
QUOTE_NOT_FOUND = "quote not found"
IMPLAUSIBLE = "implausible"
PARTLY_VISIBLE = "partly visible"
UNCLEAR_ON_PHOTO = "unclear on photo"
LEGIBILITY_FLAGS = {"partial": PARTLY_VISIBLE, "unclear": UNCLEAR_ON_PHOTO}

LABELS = {
    "hr": "heart rate",
    "sbp": "systolic BP",
    "dbp": "diastolic BP",
    "spo2": "SpO2",
    "rr": "resp rate",
    "temp_c": "temperature",
    "consciousness": "consciousness",
    "on_oxygen": "oxygen",
    "mechanism": "mechanism",
    "eta_min": "ETA",
}


def _norm(text: str) -> str:
    return " ".join(str(text).lower().split()).strip(" .,;:\"'")


def _segment_for(quote: str, segments: list) -> dict | None:
    """The Whisper segment that holds the quote (case-insensitive substring either way)."""
    q = _norm(quote)
    if not q:
        return None
    for seg in segments:
        s = _norm(seg.get("text", ""))
        if s and (q in s or s in q):
            return seg
    return None


def _add(flags: dict, field: str, reason: str) -> None:
    if reason not in flags.setdefault(field, []):
        flags[field].append(reason)


def note_flags(note: dict, segments: list) -> dict:
    """Flags for fields taken from the voice note."""
    flags = {}
    for field in NOTE_FIELDS:
        if note.get(field) is None:
            continue
        quote = note.get("evidence", {}).get(field, "")
        if quote.endswith(NOT_FOUND_MARK):
            _add(flags, field, QUOTE_NOT_FOUND)
            continue
        seg = _segment_for(quote, segments)
        if seg is not None and seg.get("avg_logprob") is not None and seg["avg_logprob"] < LOW_LOGPROB:
            _add(flags, field, UNCLEAR_SPEECH)
    return flags


def monitor_flags(photo: dict) -> dict:
    """Flags for values read off the monitor photo."""
    flags = {}
    for field in MONITOR_FIELDS:
        value = photo.get(field)
        if value is None:
            continue
        low, high = PLAUSIBLE[field]
        if not low <= value <= high:
            _add(flags, field, IMPLAUSIBLE)
        reason = LEGIBILITY_FLAGS.get(photo.get("legibility", {}).get(field))
        if reason:
            _add(flags, field, reason)
    sbp, dbp = photo.get("sbp"), photo.get("dbp")
    if sbp is not None and dbp is not None and sbp <= dbp:
        _add(flags, "sbp", IMPLAUSIBLE)
        _add(flags, "dbp", IMPLAUSIBLE)
    return flags


def compute_flags(note: dict, photo: dict, segments: list) -> dict:
    """All flags as {field: [reason, ...]}. Empty dict when nothing is in doubt."""
    flags = note_flags(note, segments)
    for field, reasons in monitor_flags(photo).items():
        for reason in reasons:
            _add(flags, field, reason)
    return flags


def confirm_with_crew(flags: dict, missing: list) -> list[str]:
    """Flagged fields first, then missing NEWS2 parameters, as short phrases."""
    items = [f"{LABELS.get(f, f)} ({', '.join(reasons)})" for f, reasons in flags.items()]
    items += [f"{LABELS.get(f, f)} (missing)" for f in missing if f not in flags]
    return items
