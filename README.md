# Multimodal Construction Intelligence Platform

> **Category:** Generative AI | Real Estate Decision Support | **Platform ID:** `6ac4c98d1dcde6d7857c1642`

**Skill Wallet Capstone Project 1** — a Streamlit app that brings multimodal
AI to construction sites: PPE safety audits from site photos, crack
diagnostics from concrete photos, planning-grade project valuation, and a
weather-aware daily site assistant. No database is required — all state
lives in the session.

**Live demo:** https://multimodal-construction-intelligence-platform-l9hjzurajnd6mt7q.streamlit.app/

---

## Table of contents

- [Features](#features)
- [Quick start](#quick-start)
- [Mode switch](#mode-switch)
- [AI providers](#ai-providers)
- [Choosing a model](#choosing-a-model)
- [Saving your API key](#saving-your-api-key)
- [Deploy on Streamlit Community Cloud](#deploy-on-streamlit-community-cloud)
- [Project structure](#project-structure)
- [How it works](#how-it-works)
- [Valuation: assumptions and example](#valuation-assumptions-and-example)
- [Security and privacy](#security-and-privacy)
- [Limitations](#limitations)

---

## Features

| Tab | What it does |
| --- | --- |
| 🦺 Site Safety & PPE Audit | Upload a site photo → structured audit: safety score (0–100), overall status, PPE checklist (helmet, high-vis vest, steel-toe boots, harness, gloves, eye protection) against OSHA 29 CFR 1926 with IS 456 site context, hazards with severity + remedies, downloadable JSON report. |
| 🧱 Crack Diagnostics | Upload a concrete/wall photo → defect classification (Hairline, Settlement, Structural Shear, Thermal Expansion, Spalling), estimated crack width (mm), root causes, engineering repairs, urgency. |
| 🏠 Planning & Valuation | Structure type, built-up area, location tier (Tier 1/2/3 Indian cities) and completion % → total budget, capex incurred, current market valuation in ₹ Lakhs/Crores, steel and cement requirements, milestone progress, plus a Pollinations AI conceptual 3D rendering. |
| 🌦️ Daily Site Assistant | Weather selector (Normal, High Wind, Heavy Rain, Extreme Heat) with dynamic safety alerts, plus a multi-turn construction engineering chatbot. |

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

No API key is required to explore: without a key the app runs in
**demonstration mode** with realistic, image-seeded sample results. For
live multimodal analysis and chat, switch to **Use API key** mode in the
sidebar and add a provider key.

## Mode switch

The sidebar has a **Mode** switch with two options:

- **🎭 Demonstration** — sample results only. The provider is never called,
  even if a key is saved, so no quota is used. Useful for demos and
  testing.
- **🔑 Use API key** — live calls to the selected provider. If no key is
  found for that provider, demonstration results are shown with a note
  explaining why.

The switch defaults to **Use API key** when any provider key is saved in
secrets, and to **Demonstration** otherwise. Provider, key and model
controls only appear in **Use API key** mode — in **Demonstration** mode
the sidebar shows just the switch and the mode indicator, since there is
nothing to configure.

## AI providers

Each provider uses its own endpoint and key. Model IDs are editable in the
sidebar, because exact IDs can differ by account.

| Provider | Endpoint | Models (defaults) |
| --- | --- | --- |
| Google Gemini | google-genai SDK | Gemini 3.6 Flash, Gemini 3.8 Flash, Gemini 3.5 Flash-Lite |
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
This works with Ollama, vLLM, llama.cpp server, SGLang, LocalAI and
OpenAI-compatible gateways. Any provider failure falls back to
demonstration results with a note.

## Choosing a model

All listed models accept image + text, so every tab works with any choice.
Approximate Gemini free-tier limits:

| Model | ID | Req/min | Req/day | Tokens/min |
| --- | --- | --- | --- | --- |
| Gemini 3.6 Flash | `gemini-3.6-flash` | 5 | 20 | 250K |
| Gemini 3.8 Flash | `gemini-3.8-flash` | 5 | 20 | 250K |
| Gemini 3.5 Flash-Lite | `gemini-3.5-flash-lite` | 10 | 500 | 250K |

Google no longer publishes a free-tier table — your exact quota is shown in
Google AI Studio, and paid tiers raise these limits substantially.
Anthropic and OpenAI limits depend on your plan; see the respective
provider console.

## Saving your API key

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
`.streamlit/secrets.toml` and put your key there. That file is
git-ignored, so it is never pushed to GitHub.

**Why this stays safe:**

- Secrets are stored encrypted by Streamlit, never written into code,
  never committed to GitHub, and never shown to app visitors — the sidebar
  input disappears entirely once a secret is set.
- A key typed into the sidebar instead lives only in session memory and is
  never written to disk.
- One honest caveat: anyone who can open a *public* app can still trigger
  model calls on your key's quota (the key itself stays hidden, but usage
  is billed to you). For a personal project, keep the deployed app private
  or treat the free-tier limits as your budget.

## Deploy on Streamlit Community Cloud

1. Push this folder to a public GitHub repo.
2. At [share.streamlit.io](https://share.streamlit.io), create an app
   pointing at `app.py`.
3. (Optional) In **Settings → Secrets**, add the keys listed above.
4. Deploy. No database or other service is required.

## Project structure

```
app.py                          # Streamlit entry point (sidebar + 4 tabs)
requirements.txt                # streamlit, google-genai, Pillow, requests
README.md
.gitignore                      # ignores .streamlit/secrets.toml, caches, venvs
.streamlit/
  secrets.toml.example          # placeholder-only template (no real keys)
src/
  __init__.py
  config.py                     # rates, tiers, advisories, model tables
  valuation.py                  # pure, testable valuation math
  prompts.py                    # multimodal + chat prompts
  gemini_client.py              # Gemini wrapper + demonstration data
  providers.py                  # Gemini / Anthropic / OpenAI / Custom dispatch
  ui.py                         # CSS, status pills, banners
```

## How it works

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

- **Tabs 1, 2 and the chatbot** send the photo (or conversation) to the
  selected provider and parse the structured JSON/text reply. Any
  failure — missing key, bad key, unreachable server, invalid response —
  falls back to the demonstration result with an explanatory note, so the
  UI never crashes.
- **Tab 3 (valuation)** never calls an AI provider: it is deterministic
  math in `src/valuation.py`, so its figures are reproducible. Only the
  conceptual 3D rendering comes from Pollinations (keyless, needs
  internet).
- **Tab 4 advisories** are built-in weather rules, independent of any
  provider.

## Valuation: assumptions and example

- Base construction rates per sq ft and tier multipliers live in
  `src/config.py` and are planning-grade estimates, not quotations.
- Completed market value assumes a 30% premium over construction budget;
  current market value assumes a 25% land share at 0% completion.
- Steel/cement factors are standard Indian RCC rules of thumb
  (≈4 kg steel and ≈0.4 bags cement per sq ft for standard residential).

Verified example — Standard Residential, 1500 sq ft, Tier 1, 40% complete:

| Figure | Value |
| --- | --- |
| Total budget | ₹36.45 L |
| Capex incurred | ₹14.58 L |
| Current market valuation | ₹26.06 L |
| Completed value | ₹47.39 L |
| Steel required | 6.0 tonnes |
| Cement required | 600 bags |
| Current phase | Structural frame (RCC) |

## Security and privacy

- API keys are held only in session memory (typed) or Streamlit secrets
  (saved), never in code and never committed.
- Uploaded photos are sent only to the provider you selected, and only
  when you press a Run button. In Demonstration mode nothing leaves the
  app except the Pollinations rendering request in Tab 3.
- Demonstration mode is clearly labelled wherever it appears.

## Limitations

- Demonstration PPE/crack reports are realistic samples seeded from the
  uploaded image — they do not actually inspect the photo. Real analysis
  needs a provider key or a local model via the custom endpoint.
- Valuation figures are planning-grade estimates, not engineering
  quotations or certified valuations.
- IS 456 is referenced in the audit prompt for structural/concrete site
  context; OSHA 29 CFR 1926 governs the PPE requirements.
