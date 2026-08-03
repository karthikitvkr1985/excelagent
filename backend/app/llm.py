"""Google Gemini wrapper with graceful fallback when no API key is set.

All calls return None (or raise AppCommsError with a friendly message) when
the key is missing, so the rest of the app degrades gracefully instead of
crashing on upload.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from .config import settings

_client = None


def _get_client():
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            return None
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        _client = genai
    return _client


def llm_available() -> bool:
    return bool(settings.gemini_api_key)


def llm_text(prompt: str, system: Optional[str] = None) -> str:
    client = _get_client()
    if client is None:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    model = client.GenerativeModel(settings.gemini_model, system_instruction=system)
    resp = model.generate_content(prompt)
    return resp.text or ""


def llm_json(prompt: str, system: Optional[str] = None) -> Optional[dict]:
    """Ask the LLM for strict JSON, returning a dict or None."""
    client = _get_client()
    if client is None:
        return None
    try:
        model = client.GenerativeModel(
            settings.gemini_model,
            system_instruction=system,
            generation_config={"response_mime_type": "application/json"},
        )
        resp = model.generate_content(prompt)
        text = (resp.text or "").strip()
        return json.loads(text)
    except Exception:
        return None


def json_mode() -> bool:
    return llm_available()


def decode_json_field(raw: Any) -> Optional[dict]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return None
    return None