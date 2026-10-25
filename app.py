"""Multimodal Construction Intelligence Platform (Skill Wallet Capstone 1).

Streamlit entry point. Four modules:
  Tab 1 — Site Safety & PPE Audit (multimodal, any provider)
  Tab 2 — Crack Diagnostics & Structural Integrity (multimodal, any provider)
  Tab 3 — Planning & Real Estate Valuation (deterministic calculator)
  Tab 4 — Daily Site Assistant & Weather-Aware Advisory (chat + alerts)

Zero external database dependencies — all state lives in Streamlit session state.
"""

from __future__ import annotations

import json
import urllib.parse

import streamlit as st

from src import config as C
from src.gemini_client import demo_crack_result, demo_ppe_result
from src.providers import (
    PROVIDERS,
    fetch_models,
    run_chat,
    run_image_analysis,
)
from src.prompts import CRACK_DIAGNOSTICS_PROMPT, PPE_AUDIT_PROMPT
from src.ui import demo_banner, inject_css, pill, severity_pill, status_pill
from src.valuation import calculate_project, format_inr, indian_format

st.set_page_config(
    page_title=C.APP_TITLE,
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()


# ---------------------------------------------------------------------------
# Sidebar — provider, API key, model, architecture overview
# ---------------------------------------------------------------------------
def _secret_value(name: str) -> str:
    """A saved secret (Cloud secrets or .streamlit/secrets.toml)."""
    try:
        return (st.secrets.get(name, "") or "").strip()
    except Exception:
        return ""


def _key_input(provider: str, secret_name: str, session_key: str,
                optional: bool = False) -> str:
    """Key field for one provider. A saved secret hides the input entirely."""
    if _secret_value(secret_name):
        st.success(f"🔒 {provider} key saved securely (Streamlit secrets).")
        return _secret_value(secret_name)
    typed = st.text_input(
        f"{provider} API key",
        type="password",
        key=session_key,
        help="Only for this session. Save it in Streamlit secrets to stop being asked."
        + (" Leave empty for local servers without auth." if optional else ""),
    )
    return (typed or "").strip()


def _model_picker(provider: str, models: dict, key_prefix: str) -> str:
    """Model dropdown + editable model-ID field. Returns the effective ID."""
    label = st.selectbox("Model", list(models), key=f"model_{key_prefix}")
    info = models[label]
    model_id = st.text_input(
        "Model ID (editable)",
        value=info["model_id"],
        key=f"mid_{key_prefix}_{label}",
        help="Exact ID sent to the API. Edit it if your account uses a different ID.",
    )
    return (model_id or "").strip() or info["model_id"]


with st.sidebar:
    st.title("🏗️ Construction Intelligence")
    st.caption(C.APP_SUBTITLE)

    # --- Mode switch: Demonstration vs Use API key ---
    any_secret = any(
        _secret_value(name)
        for name in (
            "GEMINI_API_KEY",
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "CUSTOM_API_KEY",
        )
    )
    app_mode = st.radio(
        "Mode",
        ["🎭 Demonstration", "🔑 Use API key"],
        index=1 if any_secret else 0,
        key="app_mode",
        help="Demonstration shows sample results and never calls a provider, so no "
        "quota is used. Use API key sends your photos and questions to the "
        "selected provider. Provider, key and model controls appear only in "
        "Use API key mode.",
    )
    force_demo = app_mode.startswith("🎭")

    # Provider, key and model controls exist only in Use API key mode.
    # In Demonstration mode the sidebar stays clean; the defaults below
    # keep the tab code working (calls are forced to demo anyway).
    provider, api_key, model_id, base_url = "Google Gemini", "", "", ""
    context_tokens = None
    if not force_demo:
        provider = st.selectbox(
            "AI provider",
            PROVIDERS,
            help="Each provider uses its own endpoint and key. Custom endpoint speaks "
            "OpenAI-compatible chat completions, Hermes-style.",
        )
        base_url = ""
        context_tokens = None

        if provider == "Google Gemini":
            api_key = _key_input("Google Gemini", "GEMINI_API_KEY", "gemini_api_key")
            model_id = _model_picker(provider, C.MODELS, "gemini")
            info = C.MODELS[st.session_state["model_gemini"]]
            st.caption(
                f"Free tier: **{info['rpm']} req/min · {info['rpd']} req/day · "
                f"{info['tpm']} tokens/min** — {info['note']}"
            )
            with st.expander("All Gemini models' free-tier limits"):
                for label, item in C.MODELS.items():
                    st.write(
                        f"**{label}** (`{item['model_id']}`): {item['rpm']} req/min, "
                        f"{item['rpd']} req/day, {item['tpm']} tokens/min"
                    )
                st.caption(
                    "Approximate free-tier figures — Google no longer publishes a "
                    "free-tier table, so your exact quota is shown in Google AI Studio. "
                    "Paid tiers raise these limits substantially."
                )
        elif provider == "Anthropic":
            api_key = _key_input("Anthropic", "ANTHROPIC_API_KEY", "anthropic_api_key")
            model_id = _model_picker(provider, C.ANTHROPIC_MODELS, "anthropic")
            info = C.ANTHROPIC_MODELS[st.session_state["model_anthropic"]]
            st.caption(f"{info['note']} Rate limits depend on your plan — see the Anthropic console.")
        elif provider == "OpenAI":
            api_key = _key_input("OpenAI", "OPENAI_API_KEY", "openai_api_key")
            model_id = _model_picker(provider, C.OPENAI_MODELS, "openai")
            info = C.OPENAI_MODELS[st.session_state["model_openai"]]
            st.caption(f"{info['note']} Rate limits depend on your plan — see the OpenAI console.")
        else:  # Custom endpoint (Hermes-style)
            base_url = st.text_input(
                "Base URL",
                value=_secret_value("CUSTOM_BASE_URL") or "http://localhost:11434/v1",
                help="OpenAI-compatible endpoint. /v1 is added automatically if missing.",
            )
            api_key = _key_input(
                "Custom endpoint", "CUSTOM_API_KEY", "custom_api_key", optional=True
            )
            if st.button("Fetch models"):
                ids, err = fetch_models(base_url, api_key)
                if err:
                    st.error(err)
                else:
                    st.session_state["custom_models"] = ids
                    st.session_state["custom_model_input"] = ids[0]
            model_id = st.text_input(
                "Model name",
                value=_secret_value("CUSTOM_MODEL") or "",
                key="custom_model_input",
                help="Any model your endpoint serves, e.g. qwen3.5:27b. Use Fetch models "
                "above to list what the server offers.",
            )
            if st.session_state.get("custom_models"):
                st.caption("Server models: " + ", ".join(st.session_state["custom_models"]))
            with st.expander("Advanced"):
                context_tokens = st.number_input(
                    "Context length (chat history budget, tokens)",
                    min_value=0,
                    value=64000,
                    step=1000,
                    help="Older chat turns are trimmed to fit this budget. Image analysis "
                    "is single-turn and unaffected. (Hermes-style field; unlike Hermes, "
                    "this app sends short requests, so no 64K minimum is enforced.)",
                )

    # --- Mode indicator ---
    if force_demo:
        st.markdown("**Mode:** 🎭 Demonstration mode")
        st.caption("Sample results only — no provider is called and no quota is used.")
    else:
        live = bool(api_key) if provider != "Custom endpoint" else bool(base_url.strip())
        mode = f"🟢 Live {provider}" if live else "🎭 Demonstration mode"
        st.markdown(f"**Mode:** {mode}")
        if not live:
            st.caption(
                "No key found for this provider — demonstration results are shown. "
                "Add the key in Streamlit secrets or in the field above, or switch "
                "to Demonstration mode."
            )

    st.divider()
    st.subheader("Architecture overview")
    st.markdown(
        """
        ```
        Streamlit UI (4 tabs)
              │
        ┌─────┴──────┐
        │ LLM provider│ (multimodal + chat)
        │ Gemini /    │
        │ Anthropic / │
        │ OpenAI /    │
        │ Custom      │
        └─────┬──────┘
              │
        Demo fallback engine
        (seeded, no key needed)
        ```
        - **No database** — state lives in session only.
        - **No stored keys** — the key is never written to disk.
        - **Deploy:** Streamlit Community Cloud, 1-click from GitHub.
        """
    )
    st.divider()
    st.subheader("Modules")
    st.markdown(
        "1. 🦺 Site Safety & PPE Audit\n"
        "2. 🧱 Crack Diagnostics\n"
        "3. 🏠 Planning & Valuation\n"
        "4. 🌦️ Daily Site Assistant"
    )

st.title(f"🏗️ {C.APP_TITLE}")
st.caption(
    "AI-assisted site safety, structural diagnostics, project valuation and "
    "weather-aware daily guidance — with a demonstration mode that works "
    "without any API key."
)

tabs = st.tabs(
    [
        "🦺 Site Safety & PPE Audit",
        "🧱 Crack Diagnostics",
        "🏠 Planning & Valuation",
        "🌦️ Daily Site Assistant",
    ]
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def _uploaded_image(uploaded_file):
    """Return (bytes, mime) for an uploaded image, or (None, None)."""
    if uploaded_file is None:
        return None, None
    return uploaded_file.getvalue(), uploaded_file.type or "image/jpeg"


def _download_json_button(label: str, data: dict, filename: str) -> None:
    st.download_button(
        label,
        data=json.dumps(data, indent=2),
        file_name=filename,
        mime="application/json",
    )


# ---------------------------------------------------------------------------
# Tab 1 — Site Safety & PPE Audit
# ---------------------------------------------------------------------------
with tabs[0]:
    st.header("🦺 Site Safety & PPE Audit")
    st.write(
        "Upload a construction site photo. The audit checks helmet, high-vis "
        "vest, steel-toe boot and harness compliance under OSHA 29 CFR 1926 "
        "and IS 456, and lists hazards with severity and remedies."
    )
    uploaded = st.file_uploader(
        "Construction site photo", type=["jpg", "jpeg", "png"], key="ppe_upload"
    )
    image_bytes, mime = _uploaded_image(uploaded)

    if image_bytes:
        st.image(image_bytes, caption="Uploaded site photo", width=480)
        if st.button("Run PPE Audit", key="ppe_run"):
            with st.spinner("Analysing PPE compliance…"):
                result, note = run_image_analysis(
                    provider, api_key, model_id, base_url,
                    image_bytes, mime, PPE_AUDIT_PROMPT, demo_ppe_result,
                    force_demo=force_demo,
                )
            if note:
                demo_banner(note)
            try:
                score = int(result.get("safety_score", 0))
                status = result.get("overall_status", "Needs Attention")
                col1, col2 = st.columns(2)
                col1.metric("Safety score", f"{score}/100")
                with col2:
                    st.markdown(f"**Overall status**<br>{status_pill(status)}",
                                unsafe_allow_html=True)
                st.subheader("PPE compliance checklist")
                for row in result.get("ppe_detection", []):
                    tick = "✅" if row.get("detected") else "❌"
                    st.write(
                        f"{tick} **{row.get('item')}** — "
                        f"{row.get('compliance_rate', 0)}% compliant · "
                        f"{row.get('notes', '')}"
                    )
                st.subheader("Identified hazards")
                for hz in result.get("hazards", []):
                    st.markdown(
                        f"{severity_pill(hz.get('severity', 'Low'))} "
                        f"**{hz.get('hazard')}** — {hz.get('remedy', '')}",
                        unsafe_allow_html=True,
                    )
                st.write(result.get("summary", ""))
                _download_json_button(
                    "⬇️ Download JSON report", result, "ppe_audit_report.json"
                )
            except Exception as exc:
                st.error(f"Could not render the audit result ({exc}).")
    else:
        st.info("Upload a JPG or PNG site photo to begin the audit.")


# ---------------------------------------------------------------------------
# Tab 2 — Crack Diagnostics & Structural Integrity
# ---------------------------------------------------------------------------
with tabs[1]:
    st.header("🧱 Crack Diagnostics & Structural Integrity")
    st.write(
        "Upload a photo of a concrete or masonry surface. The analysis "
        "classifies the defect, estimates crack width, and recommends "
        "engineering repairs."
    )
    uploaded = st.file_uploader(
        "Concrete / wall surface photo", type=["jpg", "jpeg", "png"], key="crack_upload"
    )
    image_bytes, mime = _uploaded_image(uploaded)

    if image_bytes:
        st.image(image_bytes, caption="Uploaded surface photo", width=480)
        if st.button("Diagnose Crack", key="crack_run"):
            with st.spinner("Diagnosing structural defect…"):
                result, note = run_image_analysis(
                    provider, api_key, model_id, base_url,
                    image_bytes, mime, CRACK_DIAGNOSTICS_PROMPT, demo_crack_result,
                    force_demo=force_demo,
                )
            if note:
                demo_banner(note)
            try:
                col1, col2, col3 = st.columns(3)
                col1.metric("Defect type", result.get("defect_type", "—"))
                col2.metric("Crack width", f"{result.get('crack_width_mm', 0)} mm")
                with col3:
                    st.markdown(
                        f"**Severity**<br>{severity_pill(result.get('severity', 'Low'))}",
                        unsafe_allow_html=True,
                    )
                st.markdown(f"**Urgency:** {result.get('urgency', '—')}")
                st.subheader("Likely root causes")
                for cause in result.get("root_causes", []):
                    st.write(f"• {cause}")
                st.subheader("Recommended engineering repairs")
                for repair in result.get("recommended_repairs", []):
                    st.write(f"• {repair}")
                st.write(result.get("summary", ""))
                _download_json_button(
                    "⬇️ Download JSON report", result, "crack_diagnostics_report.json"
                )
            except Exception as exc:
                st.error(f"Could not render the diagnostics result ({exc}).")
    else:
        st.info("Upload a JPG or PNG photo of the surface to begin.")


# ---------------------------------------------------------------------------
# Tab 3 — Planning & Real Estate Valuation
# ---------------------------------------------------------------------------
with tabs[2]:
    st.header("🏠 Planning & Real Estate Valuation")
    st.write(
        "Planning-grade estimates based on transparent per-sq-ft rates, a "
        "location-tier multiplier and a market premium. Treat figures as "
        "budget guidance, not a quotation."
    )
    col_a, col_b = st.columns(2)
    with col_a:
        structure = st.selectbox("Structure type", list(C.STRUCTURE_TYPES))
        sqft = st.number_input(
            "Built-up area (sq ft)", min_value=100, max_value=1_000_000,
            value=1500, step=50,
        )
    with col_b:
        tier = st.selectbox("Location tier", list(C.LOCATION_TIERS))
        completion = st.slider("Completion (%)", 0, 100, 40)

    try:
        calc = calculate_project(structure, float(sqft), tier, float(completion))
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total project budget", format_inr(calc["total_budget"]))
        m2.metric("Capex incurred", format_inr(calc["capex_incurred"]))
        m3.metric("Current market valuation", format_inr(calc["current_market_value"]))
        m4.metric("Value at completion", format_inr(calc["market_value_completed"]))
        m5, m6, m7 = st.columns(3)
        m5.metric("Steel required", f"{calc['steel_tonnes']:.1f} tonnes ({indian_format(calc['steel_kg'])} kg)")
        m6.metric("Cement required", f"{indian_format(calc['cement_bags'])} bags ({calc['cement_tonnes']:.1f} tonnes)")
        m7.metric("Remaining budget", format_inr(calc["remaining_budget"]))

        st.subheader("Milestone progress")
        st.progress(completion / 100.0)
        st.write(f"**Current phase:** {calc['phase']} ({completion}% complete)")
        st.caption(
            f"Rate applied: ₹{indian_format(calc['rate_per_sqft'])} per sq ft "
            f"(base × tier multiplier {calc['tier_multiplier']}). "
            f"Market value assumes a {int((C.MARKET_PREMIUM - 1) * 100)}% premium "
            f"over budget and a {int(C.LAND_SHARE * 100)}% land share at 0% completion."
        )
    except ValueError as exc:
        st.error(str(exc))

    st.divider()
    st.subheader("🏛️ Conceptual 3D architectural rendering (Pollinations AI)")
    render_desc = st.text_input(
        "Describe the building",
        value=f"Modern {structure.lower()} building, Indian city, contemporary architecture, "
              "glass balconies, evening light, photorealistic 3D architectural rendering",
    )
    if st.button("Generate 3D Rendering"):
        prompt = urllib.parse.quote(render_desc)
        image_url = (
            f"https://image.pollinations.ai/prompt/{prompt}"
            "?width=1024&height=768&model=flux&nologo=true"
        )
        with st.spinner("Rendering via Pollinations AI…"):
            try:
                st.image(image_url, caption="AI-generated conceptual rendering (Pollinations)")
                st.caption("Generated live from Pollinations AI — no API key required.")
            except Exception as exc:
                st.error(f"Rendering failed ({exc}). Check your connection and retry.")


# ---------------------------------------------------------------------------
# Tab 4 — Daily Site Assistant & Weather-Aware Advisory
# ---------------------------------------------------------------------------
with tabs[3]:
    st.header("🌦️ Daily Site Assistant & Weather-Aware Advisory")
    weather = st.selectbox(
        "Today's weather condition",
        list(C.WEATHER_ADVISORIES),
        help="Advisories update instantly for the selected condition.",
    )
    adv = C.WEATHER_ADVISORIES[weather]
    st.markdown(
        f"{pill(adv['level'], adv['level_color'])}",
        unsafe_allow_html=True,
    )
    st.subheader("⚠️ Safety alerts")
    for alert in adv["alerts"]:
        st.warning(alert)
    col_do, col_dont = st.columns(2)
    with col_do:
        st.subheader("✅ Do")
        for item in adv["do"]:
            st.write(f"• {item}")
    with col_dont:
        st.subheader("🚫 Don't")
        for item in adv["dont"]:
            st.write(f"• {item}")

    st.divider()
    st.subheader("💬 Construction engineering assistant")
    st.caption(
        "Ask about safety, concrete, curing, scaffolding, cranes or IS codes. "
        "Live answers from the selected provider when a key is set; otherwise a built-in "
        "rule-based assistant replies."
    )
    st.session_state.setdefault("chat_history", [])
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    user_msg = st.chat_input("Ask a site engineering question…")
    if user_msg:
        st.session_state["chat_history"].append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.write(user_msg)
        with st.spinner("Thinking…"):
            reply, note = run_chat(
                provider, api_key, model_id, base_url,
                st.session_state["chat_history"], context_tokens=context_tokens,
                force_demo=force_demo,
            )
        st.session_state["chat_history"].append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.write(reply)
        if note:
            st.caption(note)
