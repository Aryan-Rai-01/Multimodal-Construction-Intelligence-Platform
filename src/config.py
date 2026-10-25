"""Static configuration for the Multimodal Construction Intelligence Platform.

All rates, multipliers and advisory text live here so the app logic stays
clean and the assumptions are easy to audit or update.
"""

from __future__ import annotations

APP_TITLE = "Multimodal Construction Intelligence Platform"
APP_SUBTITLE = "Skill Wallet Capstone Project 1 · Gemini-powered site intelligence"

# ---------------------------------------------------------------------------
# Planning & valuation model (Tab 3)
# ---------------------------------------------------------------------------
# Base construction cost per sq ft (INR). These are planning-grade estimates,
# not quotations — the UI states this assumption clearly.
STRUCTURE_TYPES = {
    "Standard Residential": {
        "rate_per_sqft": 1800,
        "steel_kg_per_sqft": 4.0,
        "cement_bags_per_sqft": 0.40,
    },
    "Premium Residential": {
        "rate_per_sqft": 2500,
        "steel_kg_per_sqft": 4.5,
        "cement_bags_per_sqft": 0.45,
    },
    "Luxury Villa": {
        "rate_per_sqft": 3500,
        "steel_kg_per_sqft": 5.0,
        "cement_bags_per_sqft": 0.50,
    },
    "Commercial": {
        "rate_per_sqft": 2200,
        "steel_kg_per_sqft": 4.5,
        "cement_bags_per_sqft": 0.45,
    },
    "Industrial": {
        "rate_per_sqft": 1500,
        "steel_kg_per_sqft": 3.5,
        "cement_bags_per_sqft": 0.35,
    },
}

LOCATION_TIERS = {
    "Tier 1 (Mumbai, Delhi, Bengaluru, Hyderabad…)": 1.35,
    "Tier 2 (Pune, Jaipur, Lucknow, Indore…)": 1.15,
    "Tier 3 (Smaller cities & towns)": 1.00,
}

# Assumed market premium of a completed asset over its construction budget.
MARKET_PREMIUM = 1.30
# Assumed land share of the completed value (value present even at 0% work).
LAND_SHARE = 0.25

# Milestone bands used for the progress readout (completion % -> phase).
MILESTONES = [
    (0, "Site preparation & foundation"),
    (15, "Structural frame (RCC)"),
    (55, "Masonry, plaster & waterproofing"),
    (75, "Finishing, fixtures & MEP"),
    (95, "Handover & snagging"),
]

# ---------------------------------------------------------------------------
# Safety audit (Tab 1)
# ---------------------------------------------------------------------------
PPE_ITEMS = [
    "Safety Helmet",
    "High-Vis Vest",
    "Steel-Toe Boots",
    "Safety Harness",
    "Safety Gloves",
    "Eye Protection",
]

SEVERITY_COLORS = {
    "Low": "#2e7d32",
    "Medium": "#f9a825",
    "High": "#ef6c00",
    "Critical": "#c62828",
}

STATUS_COLORS = {
    "Safe": "#2e7d32",
    "Needs Attention": "#f9a825",
    "Unsafe": "#ef6c00",
    "Critical": "#c62828",
}

# ---------------------------------------------------------------------------
# Crack diagnostics (Tab 2)
# ---------------------------------------------------------------------------
DEFECT_TYPES = [
    "Hairline",
    "Settlement",
    "Structural Shear",
    "Thermal Expansion",
    "Spalling",
]

# ---------------------------------------------------------------------------
# Weather-aware advisory (Tab 4)
# ---------------------------------------------------------------------------
WEATHER_ADVISORIES = {
    "Normal": {
        "level": "Normal operations",
        "level_color": "#2e7d32",
        "alerts": ["No weather-driven restrictions. Standard safety protocols apply."],
        "do": [
            "Run the standard morning toolbox talk and PPE check.",
            "Log daily progress photos and material deliveries.",
        ],
        "dont": ["Skip the end-of-day housekeeping walk."],
    },
    "High Wind": {
        "level": "High-risk — restrict height & lifting work",
        "level_color": "#c62828",
        "alerts": [
            "Suspend crane operations when gusts exceed ~40 km/h (manufacturer limit governs).",
            "Secure scaffolding, loose sheets, and stacked material against wind uplift.",
            "Stop all work at height on exposed edges and roofs.",
        ],
        "do": [
            "Tie down or lower tower-crane loads; park the crane in weathervane mode if specified.",
            "Inspect scaffolding ties and edge protection before resuming work.",
            "Brief workers on falling-object risk and enforce hard-hat zones.",
        ],
        "dont": [
            "Do not lift sheet material, formwork panels, or long members in gusts.",
            "Do not use personnel hoists or open-edge platforms until wind drops.",
        ],
    },
    "Heavy Rain": {
        "level": "High-risk — electrical & excavation hazards",
        "level_color": "#c62828",
        "alerts": [
            "Electrical hazard: isolate and cover distribution boards; use RCCB/ELCB protection.",
            "Stop excavation and trenching work — risk of collapse and waterlogging.",
            "Protect fresh concrete from washout; do not pour during active rain.",
        ],
        "do": [
            "Run dewatering pumps and keep trenches barricaded and inspected.",
            "Provide covered walkways and anti-slip mats on access routes.",
            "Check for water ingress in basements and electrical rooms.",
        ],
        "dont": [
            "Do not operate tower cranes or work near overhead lines in lightning.",
            "Do not pour concrete, plaster, or paint on wet substrates.",
        ],
    },
    "Extreme Heat": {
        "level": "Warning — heat stress & curing risk",
        "level_color": "#ef6c00",
        "alerts": [
            "Heat-stress protocol: shaded rest, hydration stations, and work–rest cycles.",
            "Concrete curing protocol: keep fresh concrete moist (wet curing / curing compound).",
            "Avoid midday concrete pours; schedule heavy work for early morning/evening.",
        ],
        "do": [
            "Provide cool drinking water and ORS; watch for heatstroke symptoms.",
            "Cure slabs with wet hessian or ponding for the first 7 days.",
            "Rotate crews and reduce PPE-heavy tasks during peak heat.",
        ],
        "dont": [
            "Do not let concrete dry out in the first 24 hours — plastic shrinkage cracks follow.",
            "Do not ignore dizziness, nausea, or confusion — move the worker to shade immediately.",
        ],
    },
}

# ---------------------------------------------------------------------------
# Gemini models selectable in the sidebar (Tab: model picker)
# ---------------------------------------------------------------------------
# Free-tier limits below are approximate (requests/min, requests/day,
# input tokens/min). Google no longer publishes a free-tier table, and
# third-party measurements disagree slightly (e.g. 10 vs 15 RPM for
# Flash-Lite). The authoritative quota for a project is shown in
# Google AI Studio. Paid tiers raise these limits substantially.
MODELS = {
    "Gemini 3.6 Flash": {
        "model_id": "gemini-3.6-flash",
        "rpm": 5,
        "rpd": 20,
        "tpm": "250K",
        "note": "Balanced workhorse — coding, multimodal, agentic tasks.",
    },
    "Gemini 3.8 Flash": {
        "model_id": "gemini-3.8-flash",
        "rpm": 5,
        "rpd": 20,
        "tpm": "250K",
        "note": "Strongest reasoning/coding of the three — long-horizon work.",
    },
    "Gemini 3.5 Flash-Lite": {
        "model_id": "gemini-3.5-flash-lite",
        "rpm": 10,
        "rpd": 500,
        "tpm": "250K",
        "note": "Fastest and cheapest — highest daily allowance.",
    },
}

DEFAULT_MODEL_LABEL = "Gemini 3.6 Flash"
