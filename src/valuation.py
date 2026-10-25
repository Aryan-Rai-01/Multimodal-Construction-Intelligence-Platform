"""Pure calculation helpers for Tab 3 (Planning & Real Estate Valuation).

These functions have no Streamlit dependency, so they are unit-testable.
All monetary values are in INR.
"""

from __future__ import annotations

from src.config import (
    LAND_SHARE,
    LOCATION_TIERS,
    MARKET_PREMIUM,
    MILESTONES,
    STRUCTURE_TYPES,
)


def indian_format(amount: float) -> str:
    """Format a number with Indian digit grouping, e.g. 12345678 -> 1,23,45,678."""
    whole = str(int(round(amount)))
    if len(whole) <= 3:
        return whole
    last_three = whole[-3:]
    rest = whole[:-3]
    parts = []
    while len(rest) > 2:
        parts.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        parts.insert(0, rest)
    return ",".join(parts + [last_three])


def format_inr(amount: float) -> str:
    """Human-friendly INR amount: Lakhs below 1 Crore, Crores above it."""
    if amount >= 1e7:
        return f"₹{amount / 1e7:.2f} Cr"
    if amount >= 1e5:
        return f"₹{amount / 1e5:.2f} L"
    return f"₹{indian_format(amount)}"


def milestone_phase(completion_pct: float) -> str:
    """Return the construction phase name for a completion percentage."""
    phase = MILESTONES[0][1]
    for threshold, name in MILESTONES:
        if completion_pct >= threshold:
            phase = name
    return phase


def calculate_project(
    structure_type: str,
    built_up_sqft: float,
    tier_label: str,
    completion_pct: float,
) -> dict:
    """Calculate budget, spend, valuation and material requirements.

    Model (assumptions are surfaced in the UI):
      total budget        = sqft × base rate × tier multiplier
      capex incurred      = total budget × completion %
      completed value     = total budget × MARKET_PREMIUM
      current market value = completed value × (LAND_SHARE + (1 - LAND_SHARE) × completion %)
      steel / cement      = sqft × per-sqft factors for the structure type
    """
    if built_up_sqft <= 0:
        raise ValueError("Built-up area must be greater than zero.")
    if not 0 <= completion_pct <= 100:
        raise ValueError("Completion percentage must be between 0 and 100.")
    if structure_type not in STRUCTURE_TYPES:
        raise ValueError(f"Unknown structure type: {structure_type}")
    if tier_label not in LOCATION_TIERS:
        raise ValueError(f"Unknown location tier: {tier_label}")

    spec = STRUCTURE_TYPES[structure_type]
    tier_multiplier = LOCATION_TIERS[tier_label]
    completion = completion_pct / 100.0

    total_budget = built_up_sqft * spec["rate_per_sqft"] * tier_multiplier
    capex_incurred = total_budget * completion
    market_value_completed = total_budget * MARKET_PREMIUM
    current_market_value = market_value_completed * (
        LAND_SHARE + (1 - LAND_SHARE) * completion
    )

    steel_kg = built_up_sqft * spec["steel_kg_per_sqft"]
    cement_bags = built_up_sqft * spec["cement_bags_per_sqft"]

    return {
        "structure_type": structure_type,
        "tier_label": tier_label,
        "tier_multiplier": tier_multiplier,
        "rate_per_sqft": spec["rate_per_sqft"] * tier_multiplier,
        "total_budget": total_budget,
        "capex_incurred": capex_incurred,
        "remaining_budget": total_budget - capex_incurred,
        "market_value_completed": market_value_completed,
        "current_market_value": current_market_value,
        "steel_kg": steel_kg,
        "steel_tonnes": steel_kg / 1000.0,
        "cement_bags": cement_bags,
        "cement_tonnes": cement_bags * 50 / 1000.0,  # 1 bag = 50 kg
        "phase": milestone_phase(completion_pct),
    }
