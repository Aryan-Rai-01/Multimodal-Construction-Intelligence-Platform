"""Multi-provider LLM access for the Construction Intelligence Platform.

Providers
---------
- Google Gemini — via the google-genai SDK (existing behaviour).
- Anthropic — via the Messages API (https://api.anthropic.com/v1/messages).
- OpenAI — via Chat Completions (https://api.openai.com/v1/chat/completions).
- Custom endpoint — Hermes-style: any OpenAI-compatible server reached at
  ``{base_url}/chat/completions`` (Ollama, vLLM, llama.cpp, LocalAI,
  OpenRouter-style gateways, ...).

Design rules (mirroring the Hermes custom-endpoint research):
- Base URLs are normalised: a trailing slash is stripped and ``/v1`` is
  appended when the URL contains no ``/v1`` segment at all.
- API keys are optional for custom endpoints (local servers often need none).
- Custom endpoints get a long timeout (300 s) because local models are slow.
- Every failure — missing key, bad key, unreachable server, bad response —
  falls back to the demonstration result with an explanatory note, so the
  UI never crashes.

All provider calls share one contract:
- ``run_image_analysis(...)`` -> (result dict, note str)
- ``run_chat(...)`` -> (reply str, note str)
``history`` is a list of ``{"role": "user"|"assistant", "content": str}``
already including the latest user message.
"""

from __future__ import annotations

import base64
import json
import re
from typing import Callable, Optional, Tuple

import requests

from src import config as C
from src.gemini_client import build_client as build_gemini_client
from src.prompts import CHAT_SYSTEM_PROMPT

PROVIDERS = ["Google Gemini", "Anthropic", "OpenAI", "Custom endpoint"]

SECRET_KEYS = {
    "Google Gemini": "GEMINI_API_KEY",
    "Anthropic": "ANTHROPIC_API_KEY",
    "OpenAI": "OPENAI_API_KEY",
    "Custom endpoint": "CUSTOM_API_KEY",
}

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

CLOUD_TIMEOUT = 120
CUSTOM_TIMEOUT = 300


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def normalize_base_url(url: str) -> str:
    """Normalise a custom base URL (Hermes rule: it must reach ``/v1``).

    Strips a trailing slash and appends ``/v1`` only when the URL contains
    no ``/v1`` segment — so ``https://api.deepinfra.com/v1/openai`` is left
    untouched, while ``http://localhost:11434`` becomes
    ``http://localhost:11434/v1``.
    """
    url = (url or "").strip().rstrip("/")
    if not url:
        return ""
    if "/v1" not in url:
        url += "/v1"
    return url


def _extract_json(text: str) -> dict:
    """Extract the first JSON object from model text and parse it."""
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("Model did not return JSON.")
    return json.loads(match.group(0))


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def build_openai_messages(
    prompt: str,
    history: Optional[list] = None,
    image_bytes: Optional[bytes] = None,
    mime_type: str = "image/jpeg",
) -> list:
    """OpenAI-style messages. Image (if any) rides as an image_url part."""
    if history:
        messages = [
            {"role": m["role"], "content": m["content"]} for m in history
        ]
        return messages
    content: list = [{"type": "text", "text": prompt}]
    if image_bytes:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{_b64(image_bytes)}"
                },
            }
        )
    return [{"role": "user", "content": content}]


def build_anthropic_messages(
    prompt: str,
    history: Optional[list] = None,
    image_bytes: Optional[bytes] = None,
    mime_type: str = "image/jpeg",
) -> list:
    """Anthropic-style messages. Image (if any) rides as a base64 block."""
    if history:
        return [
            {"role": m["role"], "content": m["content"]} for m in history
        ]
    content: list = []
    if image_bytes:
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": _b64(image_bytes),
                },
            }
        )
    content.append({"type": "text", "text": prompt})
    return [{"role": "user", "content": content}]


def _anthropic_text(data: dict) -> str:
    parts = [
        block.get("text", "")
        for block in data.get("content", [])
        if block.get("type") == "text"
    ]
    text = "".join(parts).strip()
    if not text:
        raise ValueError("Anthropic returned no text.")
    return text


def trim_history(history: list, max_tokens: Optional[int]) -> list:
    """Keep the most recent turns that fit an approximate token budget.

    Token estimate: ~4 characters per token. The latest user message is
    always kept. A non-positive budget disables trimming.
    """
    if not max_tokens or max_tokens <= 0 or not history:
        return history
    budget_chars = max_tokens * 4
    kept: list = []
    total = 0
    for msg in reversed(history):
        size = len(msg.get("content", ""))
        if kept and total + size > budget_chars:
            break
        kept.append(msg)
        total += size
    kept = list(reversed(kept))
    # Anthropic requires the conversation to start with a user turn.
    if kept and kept[0].get("role") != "user":
        kept = kept[1:]
    return kept


# ---------------------------------------------------------------------------
# Per-provider raw calls (raise on failure; callers convert to demo fallback)
# ---------------------------------------------------------------------------
def _call_anthropic(
    api_key: str,
    model: str,
    messages: list,
    system: Optional[str] = None,
) -> str:
    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }
    payload: dict = {"model": model, "max_tokens": 4096, "messages": messages}
    if system:
        payload["system"] = system
    resp = requests.post(
        ANTHROPIC_URL, headers=headers, json=payload, timeout=CLOUD_TIMEOUT
    )
    resp.raise_for_status()
    return _anthropic_text(resp.json())


def _call_openai_compatible(
    base_url: str,
    api_key: str,
    model: str,
    messages: list,
    timeout: int = CLOUD_TIMEOUT,
) -> str:
    headers = {"content-type": "application/json"}
    if api_key:
        headers["authorization"] = f"Bearer {api_key}"
    resp = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json={"model": model, "messages": messages},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"Unexpected chat-completions response: {exc}")
    if not text:
        raise ValueError("Provider returned empty content.")
    return text.strip()


def fetch_models(base_url: str, api_key: str = "") -> Tuple[list, Optional[str]]:
    """GET {base}/models (Hermes-style auto-detection). Returns (ids, error)."""
    base = normalize_base_url(base_url)
    if not base:
        return [], "Enter a base URL first."
    headers = {}
    if api_key:
        headers["authorization"] = f"Bearer {api_key}"
    try:
        resp = requests.get(f"{base}/models", headers=headers, timeout=15)
        resp.raise_for_status()
        ids = [
            item.get("id")
            for item in resp.json().get("data", [])
            if item.get("id")
        ]
        if not ids:
            return [], "The server returned no models."
        return sorted(ids), None
    except Exception as exc:
        return [], f"Could not list models ({exc})."


# ---------------------------------------------------------------------------
# Unified public API used by the app
# ---------------------------------------------------------------------------
def provider_models(provider: str) -> dict:
    """Model table for a provider (label -> info). Empty for Custom."""
    if provider == "Google Gemini":
        return C.MODELS
    if provider == "Anthropic":
        return C.ANTHROPIC_MODELS
    if provider == "OpenAI":
        return C.OPENAI_MODELS
    return {}


def run_image_analysis(
    provider: str,
    api_key: str,
    model: str,
    base_url: str,
    image_bytes: bytes,
    mime_type: str,
    prompt: str,
    demo_fn: Callable[[bytes], dict],
) -> Tuple[dict, str]:
    """Run a multimodal analysis through the selected provider."""
    try:
        if provider == "Google Gemini":
            client, note = build_gemini_client(api_key)
            if client is None:
                return demo_fn(image_bytes), note or "Demonstration mode."
            from google.genai import types

            response = client.models.generate_content(
                model=model,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                ],
            )
            result = _extract_json(response.text or "")
            if not isinstance(result, dict) or not result:
                raise ValueError("Empty or invalid model response.")
            return result, ""

        if provider == "Anthropic":
            if not api_key:
                raise ValueError("No Anthropic API key supplied.")
            text = _call_anthropic(
                api_key,
                model,
                build_anthropic_messages(prompt, image_bytes=image_bytes, mime_type=mime_type),
            )
            return _extract_json(text), ""

        if provider == "OpenAI":
            if not api_key:
                raise ValueError("No OpenAI API key supplied.")
            text = _call_openai_compatible(
                "https://api.openai.com/v1",
                api_key,
                model,
                build_openai_messages(prompt, image_bytes=image_bytes, mime_type=mime_type),
            )
            return _extract_json(text), ""

        if provider == "Custom endpoint":
            base = normalize_base_url(base_url)
            if not base:
                raise ValueError("No custom base URL supplied.")
            text = _call_openai_compatible(
                base,
                api_key,
                model,
                build_openai_messages(prompt, image_bytes=image_bytes, mime_type=mime_type),
                timeout=CUSTOM_TIMEOUT,
            )
            return _extract_json(text), ""

        raise ValueError(f"Unknown provider: {provider}")
    except Exception as exc:
        return demo_fn(image_bytes), (
            f"{provider} analysis failed ({exc}). Showing a demonstration result instead."
        )


def run_chat(
    provider: str,
    api_key: str,
    model: str,
    base_url: str,
    history: list,
    context_tokens: Optional[int] = None,
) -> Tuple[str, str]:
    """Run one chat turn through the selected provider."""
    try:
        history = trim_history(history, context_tokens)
        if provider == "Google Gemini":
            client, note = build_gemini_client(api_key)
            if client is None:
                return (
                    "Demonstration answer: for site questions, start with the safety "
                    "check — PPE, fall protection, electrical isolation, and weather "
                    "conditions — then confirm the detail against IS 456 / IS 1893. "
                    "Add an API key in the sidebar for full AI answers.",
                    note or "Demonstration mode.",
                )
            transcript = "\n".join(
                f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
                for m in history[-10:]
            )
            response = client.models.generate_content(
                model=model,
                contents=f"{CHAT_SYSTEM_PROMPT}\n\nConversation so far:\n{transcript}\n\nAssistant:",
            )
            return (response.text or "").strip(), ""

        if provider == "Anthropic":
            if not api_key:
                raise ValueError("No Anthropic API key supplied.")
            return (
                _call_anthropic(
                    api_key,
                    model,
                    build_anthropic_messages("", history=history),
                    system=CHAT_SYSTEM_PROMPT,
                ),
                "",
            )

        if provider == "OpenAI":
            if not api_key:
                raise ValueError("No OpenAI API key supplied.")
            messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
            messages += build_openai_messages("", history=history)
            return (
                _call_openai_compatible(
                    "https://api.openai.com/v1", api_key, model, messages
                ),
                "",
            )

        if provider == "Custom endpoint":
            base = normalize_base_url(base_url)
            if not base:
                raise ValueError("No custom base URL supplied.")
            messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
            messages += build_openai_messages("", history=history)
            return (
                _call_openai_compatible(
                    base, api_key, model, messages, timeout=CUSTOM_TIMEOUT
                ),
                "",
            )

        raise ValueError(f"Unknown provider: {provider}")
    except Exception as exc:
        return (
            "I could not reach the assistant service right now. Please check the "
            "provider, model and key in the sidebar, then retry.",
            f"{provider} chat failed ({exc}).",
        )
