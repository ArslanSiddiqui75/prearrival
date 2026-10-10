"""Shared Groq client and JSON parsing for the cloud calls."""

import json
import os
import re
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

STT_MODEL = os.getenv("PREARRIVAL_STT_MODEL", "whisper-large-v3")
VISION_MODEL = os.getenv("PREARRIVAL_VISION_MODEL", "qwen/qwen3.8-27b")
TEXT_MODEL = os.getenv("PREARRIVAL_TEXT_MODEL", "openai/gpt-oss-120b")


@lru_cache(maxsize=1)
def client():
    from groq import Groq

    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set. Put it in .env.")
    return Groq(api_key=key, timeout=30)


def parse_json(text: str) -> dict:
    """Pull the first JSON object out of a model reply (drops <think> blocks and code fences)."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"model reply has no JSON object: {text[:200]!r}")
    return json.loads(text[start : end + 1])


def as_int(v):
    if v is None or isinstance(v, bool):
        return None
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return None


def as_float(v):
    if v is None or isinstance(v, bool):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
