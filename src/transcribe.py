"""Cloud speech-to-text. Speech owner implements this. Score and board owners do not edit it."""

from datetime import datetime

# Vocabulary hint only (spelling of handoff terms), not content. Helps live mic speech.
VOCAB = "Paramedic handoff. ETA, resp rate, respiratory rate, SpO2, sats, BP, systolic, GCS, oxygen, litres, alert, confused."


def transcribe(audio_path: str) -> dict:
    """Send the wav to the cloud and return the transcript.

    Returns {"text": str, "requested_at": ISO-8601 str, "segments": list}.
    requested_at is the moment the request is sent, not when the file was saved.
    segments are Whisper's own {text, start, end, avg_logprob, no_speech_prob}, used for confidence flags.
    """
    from src.groq_client import STT_MODEL, client

    with open(audio_path, "rb") as f:
        audio = f.read()
    requested_at = now_iso()
    result = client().audio.transcriptions.create(
        file=(audio_path.rsplit("/", 1)[-1], audio),
        model=STT_MODEL,
        language="en",
        prompt=VOCAB,
        temperature=0,
        response_format="verbose_json",
    )
    segments = []
    for seg in getattr(result, "segments", None) or []:
        seg = seg if isinstance(seg, dict) else seg.model_dump()
        segments.append({k: seg.get(k) for k in ("text", "start", "end", "avg_logprob", "no_speech_prob")})
    return {"text": result.text.strip(), "requested_at": requested_at, "segments": segments}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")
