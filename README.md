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
**demonstration mode** with realistic, image-seeded sample results. Add a
Google Gemini API key in the sidebar (or as a Streamlit secret named
`GEMINI_API_KEY`) for live multimodal analysis and chat.

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
  config.py             # Rates, tiers, advisories, constants
  valuation.py          # Pure, testable valuation math
  prompts.py            # Gemini multimodal + chat prompts
  gemini_client.py      # Gemini wrapper + demonstration fallback
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
