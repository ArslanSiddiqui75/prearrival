"""Cloud speech-to-text. Speech owner implements this. Score and board owners do not edit it."""

from datetime import datetime


def transcribe(audio_path: str) -> dict:
    """Send the wav to the cloud and return the transcript.

    Returns {"text": str, "requested_at": ISO-8601 str}.
    requested_at is the moment the request is sent, not when the file was saved.
    """
    from src.groq_client import STT_MODEL, client

    with open(audio_path, "rb") as f:
        audio = f.read()
    requested_at = now_iso()
    result = client().audio.transcriptions.create(
        file=(audio_path.rsplit("/", 1)[-1], audio),
        model=STT_MODEL,
        language="en",
        temperature=0,
    )
    return {"text": result.text.strip(), "requested_at": requested_at}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")
