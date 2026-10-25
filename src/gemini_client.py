"""Gemini client wrapper with a graceful demonstration-mode fallback.

Design rule: the app must work with zero configuration. If no API key is
supplied, the SDK is missing, or a call fails, the module returns realistic
demonstration data and a human-readable note instead of crashing.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from typing import Callable, Tuple

from src.config import DEFECT_TYPES, PPE_ITEMS

MODEL_NAME = "gemini-2.5-flash"


# ---------------------------------------------------------------------------
# Client construction
# ---------------------------------------------------------------------------
def build_client(api_key: str):
    """Return (client, note). client is None in demonstration mode."""
    if not api_key:
        return None, "No API key supplied — running in demonstration mode."
    try:
        from google import genai
    except Exception:
        return None, "google-genai SDK is not installed — demonstration mode."
    try:
        return genai.Client(api_key=api_key), ""
    except Exception as exc:  # invalid key, network, etc.
        return None, f"Could not initialise Gemini ({exc}) — demonstration mode."


# ---------------------------------------------------------------------------
# JSON extraction / validation
# ---------------------------------------------------------------------------
def _extract_json(text: str) -> dict:
    """Extract the first JSON object from model text and parse it."""
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("Model did not return JSON.")
    return json.loads(match.group(0))


def _seed_from_bytes(data: bytes) -> int:
    return int(hashlib.md5(data).hexdigest()[:8], 16)


# ---------------------------------------------------------------------------
# Demonstration data (seeded by image content, so results are stable)
# ---------------------------------------------------------------------------
def demo_ppe_result(image_bytes: bytes) -> dict:
    rng = random.Random(_seed_from_bytes(image_bytes))
    score = rng.randint(58, 92)
    status = (
        "Safe" if score >= 85 else "Needs Attention" if score >= 70 else "Unsafe"
    )
    ppe = []
    for item in PPE_ITEMS:
        detected = rng.random() > 0.25
        ppe.append(
            {
                "item": item,
                "detected": detected,
                "compliance_rate": rng.randint(85, 100) if detected else rng.randint(20, 55),
                "notes": "Observed on most workers."
                if detected
                else "Not observed on some workers — remind crew.",
            }
        )
    hazard_pool = [
        ("Unprotected edge on upper floor", "High", "Install guardrails and toe boards before next shift."),
        ("Loose debris near walkway", "Medium", "Clear the walkway and enforce daily housekeeping."),
        ("Worker without harness at height", "Critical", "Stop work at height until harnesses and anchor points are provided."),
        ("Material stacked near excavation edge", "Medium", "Move stockpiles at least 1 m back from the edge."),
        ("Dust without respiratory protection", "Low", "Provide dust masks and wet-cut where possible."),
    ]
    hazards = [
        {"hazard": h, "severity": s, "remedy": r}
        for h, s, r in rng.sample(hazard_pool, k=rng.randint(1, 3))
    ]
    return {
        "safety_score": score,
        "overall_status": status,
        "ppe_detection": ppe,
        "hazards": hazards,
        "summary": (
            "Demonstration result: most PPE is in use, but gaps remain around "
            "height work and housekeeping. Address the listed hazards before "
            "the next shift."
        ),
    }


def demo_crack_result(image_bytes: bytes) -> dict:
    rng = random.Random(_seed_from_bytes(image_bytes))
    defect = rng.choice(DEFECT_TYPES)
    width = round(rng.uniform(0.2, 4.5), 1)
    severity = "Low" if width < 1 else "Medium" if width < 2.5 else "High"
    repairs = {
        "Hairline": ["Monitor width monthly", "Seal with polymer-modified filler if it grows"],
        "Settlement": ["Check foundation drainage", "Underpinning assessment by a structural engineer"],
        "Structural Shear": ["Urgent structural engineer inspection", "Epoxy injection and crack stitching"],
        "Thermal Expansion": ["Provide/maintain expansion joints", "Seal with flexible sealant"],
        "Spalling": ["Remove loose concrete", "Structural re-grouting and protective coating"],
    }
    causes = {
        "Hairline": ["Plastic shrinkage during curing", "Minor thermal movement"],
        "Settlement": ["Differential foundation settlement", "Poor soil compaction"],
        "Structural Shear": ["Overloading", "Inadequate shear reinforcement"],
        "Thermal Expansion": ["Temperature variation without joints", "Restrained movement"],
        "Spalling": ["Reinforcement corrosion", "Water ingress and freeze–thaw"],
    }
    return {
        "defect_type": defect,
        "crack_width_mm": width,
        "severity": severity,
        "urgency": (
            "Monitor"
            if severity == "Low"
            else "Repair soon"
            if severity == "Medium"
            else "Urgent — engineer inspection required"
        ),
        "root_causes": causes[defect],
        "recommended_repairs": repairs[defect],
        "summary": (
            f"Demonstration result: a {defect.lower()} defect of about "
            f"{width} mm was identified. Treat this as a planning estimate — "
            "confirm on site before any repair."
        ),
    }


# ---------------------------------------------------------------------------
# Public API used by the app
# ---------------------------------------------------------------------------
def analyze_image(
    client,
    image_bytes: bytes,
    mime_type: str,
    prompt: str,
    demo_fn: Callable[[bytes], dict],
) -> Tuple[dict, str]:
    """Run a multimodal analysis. Returns (result, note).

    On any failure the demonstration result is returned with an explanatory
    note, so the UI never breaks.
    """
    if client is None:
        return demo_fn(image_bytes), "Demonstration mode — add a Gemini API key for live analysis."
    try:
        from google.genai import types

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                prompt,
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            ],
        )
        result = _extract_json(response.text or "")
        if not isinstance(result, dict) or not result:
            raise ValueError("Empty or invalid model response.")
        return result, ""
    except Exception as exc:
        return demo_fn(image_bytes), (
            f"Live analysis failed ({exc}). Showing a demonstration result instead."
        )


_DEMO_CHAT_RULES = [
    ("curing", "Keep fresh concrete moist for at least 7 days — wet hessian, ponding, or a curing compound. In hot weather, start curing as soon as the surface can take water without damage."),
    ("crane", "Never operate a crane above the manufacturer's wind limit (typically ~40 km/h gusts). Barricade the swing radius and use a banksman for every blind lift."),
    ("helmet", "IS 2925 helmets are mandatory on site. Replace a helmet after any impact, and check the shell and harness before each shift."),
    ("rain", "In heavy rain: isolate electrical boards, stop trenching, protect fresh concrete from washout, and never work near overhead lines during lightning."),
    ("heat", "Extreme heat protocol: shaded rest, water + ORS stations, work–rest cycles, and watch for heatstroke symptoms (confusion, hot dry skin) — move the worker to shade and call for help."),
    ("crack", "Hairline cracks (<1 mm) are usually shrinkage and just need monitoring. Diagonal cracks near supports, or anything above ~2 mm and growing, need a structural engineer before repair."),
]


def chat_reply(client, history: list, user_message: str) -> Tuple[str, str]:
    """Return (reply, note). history is a list of {'role','content'} dicts."""
    if client is None:
        lowered = user_message.lower()
        for keyword, answer in _DEMO_CHAT_RULES:
            if keyword in lowered:
                return answer, "Demonstration mode — add a Gemini API key for live answers."
        return (
            "Demonstration answer: for site questions, start with the safety "
            "check — PPE, fall protection, electrical isolation, and weather "
            "conditions — then confirm the detail against IS 456 / IS 1893. "
            "Add a Gemini API key in the sidebar for full AI answers.",
            "Demonstration mode — add a Gemini API key for live answers.",
        )
    try:
        transcript = "\n".join(
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in history[-10:]
        )
        from src.prompts import CHAT_SYSTEM_PROMPT

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=f"{CHAT_SYSTEM_PROMPT}\n\nConversation so far:\n{transcript}\n\nUser: {user_message}\nAssistant:",
        )
        return (response.text or "").strip(), ""
    except Exception as exc:
        return (
            "I could not reach the assistant service right now. Please retry, "
            "or check your API key in the sidebar.",
            f"Live chat failed ({exc}).",
        )
