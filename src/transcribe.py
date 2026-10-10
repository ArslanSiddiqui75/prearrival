"""Cloud speech-to-text. Speech owner implements this. Score and board owners do not edit it."""

from datetime import datetime


def transcribe(audio_path: str) -> dict:
    """Send the wav to the cloud and return the transcript.

    Returns {"text": str, "requested_at": ISO-8601 str}.
    requested_at is the moment the request is sent, not when the file was saved.
    """
    raise NotImplementedError(f"transcribe is not implemented for {audio_path}")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")
