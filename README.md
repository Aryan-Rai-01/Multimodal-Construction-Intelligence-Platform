# Multimodal Construction Intelligence Platform

**Skill Wallet Capstone Project 1** — a Streamlit app that brings Gemini
multimodal AI to construction sites: PPE safety audits, crack diagnostics,
project valuation, and a weather-aware daily site assistant.

## Features

| Tab | What it does |
| --- | --- |
| 🦺 Site Safety & PPE Audit | Upload a site photo → structured JSON audit: safety score (0–100), overall status, PPE checklist (helmet, high-vis vest, steel-toe boots, harness, gloves, eye protection) under OSHA 29 CFR 1926 and IS 456, hazards with severity + remedies, downloadable JSON report. |
| 🧱 Crack Diagnostics | Upload a concrete/wall photo → defect classification (Hairline, Settlement, Structural Shear, Thermal Expansion, Spalling), estimated crack width (mm), root causes, engineering repairs, urgency. |
| 🏠 Planning & Valuation | Structure type, built-up sq ft, location tier (Tier 1/2/3 Indian cities) and completion slider → total budget, capex incurred, current market valuation in ₹ Lakhs/Crores, steel/cement requirements, milestone progress, plus a Pollinations AI conceptual 3D rendering. |
| 🌦️ Daily Site Assistant | Weather selector (High Wind, Heavy Rain, Extreme Heat, Normal) with dynamic safety alerts, plus a multi-turn construction engineering chatbot. |

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

No API key is required to explore: without a key the app runs in
**demonstration mode** with realistic, image-seeded sample results. For live
multimodal analysis and chat, pick a provider in the sidebar and add its key.

## Mode switch

The sidebar has a **Mode** switch with two options:

- **🎭 Demonstration** — sample results only. The provider is never called,
  even if a key is saved, so no quota is used. Useful for demos and testing.
- **🔑 Use API key** — live calls to the selected provider. If no key is
  found for that provider, demonstration results are shown with a note
  explaining why.

The switch defaults to **Use API key** when any provider key is saved in
secrets, and to **Demonstration** otherwise. Provider, key and model
controls only appear in **Use API key** mode — in **Demonstration** mode
the sidebar shows just the switch and the mode indicator, since there is
nothing to configure.

## Providers

| Provider | Endpoint | Models (defaults, IDs editable in the sidebar) |
| --- | --- | --- |
| Google Gemini | google-genai SDK | Gemini 3.6 Flash, 3.8 Flash, 3.5 Flash-Lite |
| Anthropic | `https://api.anthropic.com/v1/messages` | Opus 5.5, Sonnet 5.5, Haiku 5.5 |
| OpenAI | `https://api.openai.com/v1/chat/completions` | GPT 6 Astra, GPT 6.1 Sol, GPT 6 Luna |
| Custom endpoint | Your URL (Hermes-style) | Any model your server offers |

**Custom endpoint (Hermes-style):** enter a base URL, an optional API key
(leave empty for local servers without auth), and a model name — or hit
**Fetch models** to list what the server offers via `GET {base}/models`.
Base URLs are normalised automatically: a trailing slash is stripped and
`/v1` is appended when the URL contains no `/v1` segment. Requests use
OpenAI-compatible chat completions with a long (300 s) timeout for slow
local models. The optional context-length field trims older chat turns to
fit the server's context; image analysis is single-turn and unaffected.
Any provider failure falls back to demonstration results with a note.

## Saving your API key (so the app never asks for it)

**On Streamlit Community Cloud (recommended):** open your app → **Settings →
Secrets** and add whichever keys you use:

```toml
GEMINI_API_KEY = "your-key-here"
ANTHROPIC_API_KEY = "your-key-here"
OPENAI_API_KEY = "your-key-here"
CUSTOM_API_KEY = "your-key-here"
CUSTOM_BASE_URL = "https://your-endpoint.example/v1"
CUSTOM_MODEL = "your-model-name"
```

Then reboot the app once. The sidebar will show "API key saved securely"
and stop asking for a key.

**Locally:** copy `.streamlit/secrets.toml.example` to
`.streamlit/secrets.toml` and put your key there.

**Why this stays safe:**
- Secrets are stored encrypted by Streamlit and are never written into code,
  never committed to GitHub (`.streamlit/secrets.toml` is git-ignored), and
  never shown to app visitors — the sidebar input disappears entirely once a
  secret is set.
- One honest caveat: anyone who can open a *public* app can still trigger
  model calls on your key's quota (the key itself stays hidden, but usage is
  billed to you). For a personal project, keep the deployed app private or
  treat the free-tier limits as your budget.

## Choosing a model

Pick from the sidebar — all three accept image + text, so every tab works
with any choice. Approximate free-tier limits:

| Model | ID | Req/min | Req/day | Tokens/min |
| --- | --- | --- | --- | --- |
| Gemini 3.6 Flash | `gemini-3.6-flash` | 5 | 20 | 250K |
| Gemini 3.8 Flash | `gemini-3.8-flash` | 5 | 20 | 250K |
| Gemini 3.5 Flash-Lite | `gemini-3.5-flash-lite` | 10 | 500 | 250K |

Google no longer publishes a free-tier table — your exact quota is shown in
Google AI Studio, and paid tiers raise these limits substantially.

## Deploy on Streamlit Community Cloud (1-click)

1. Push this folder to a public GitHub repo.
2. At [share.streamlit.io](https://share.streamlit.io), create an app
   pointing at `app.py`.
3. (Optional) In **Advanced settings → Secrets**, add:
   `GEMINI_API_KEY = "your-key-here"`.
4. Deploy. No database or other service is required.

## Project layout

```
app.py                  # Streamlit entry point (sidebar + 4 tabs)
src/
  config.py             # Rates, tiers, advisories, model tables
  valuation.py          # Pure, testable valuation math
  prompts.py            # Multimodal + chat prompts
  gemini_client.py      # Gemini wrapper + demonstration data
  providers.py          # Gemini / Anthropic / OpenAI / Custom dispatch
  ui.py                 # CSS, status pills, banners
requirements.txt
README.md
```

## Assumptions (valuation tab)

- Base construction rates per sq ft and tier multipliers live in
  `src/config.py` and are planning-grade estimates, not quotations.
- Completed market value assumes a 30% premium over construction budget;
  current market value assumes a 25% land share at 0% completion.
- Steel/cement factors are standard Indian RCC rules of thumb
  (≈4 kg steel and ≈0.4 bags cement per sq ft for standard residential).

## Notes

- The API key is held only in session memory and never written to disk.
- Demonstration mode is clearly labelled wherever it appears.
- IS 456 is referenced in the audit prompt for structural/concrete site
  context; OSHA 29 CFR 1926 governs the PPE requirements.
