"""Cloud monitor-photo read. Speech owner implements this."""


def read_monitor(image_path: str) -> dict:
    """Send the monitor photo to a vision model.

    Returns hr, sbp, dbp, spo2, evidence, requested_at.
    Use null for a number the photo does not show. Never fill a normal default.
    evidence maps each present field to "monitor photo" plus what was read.
    """
    raise NotImplementedError(f"read_monitor is not implemented for {image_path}")
