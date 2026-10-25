"""Small UI helpers: global CSS, status pills and metric cards."""

from __future__ import annotations

import streamlit as st

from src.config import SEVERITY_COLORS, STATUS_COLORS

CSS = """
<style>
  .block-container { padding-top: 1.2rem; }
  .pill {
    display: inline-block; padding: 4px 14px; border-radius: 999px;
    color: #fff; font-weight: 600; font-size: 0.85rem; margin: 2px 0;
  }
  .card {
    border: 1px solid #e0e0e0; border-radius: 14px; padding: 14px 18px;
    background: #ffffff; margin-bottom: 10px;
  }
  .card h4 { margin: 0 0 4px 0; }
  .muted { color: #666; font-size: 0.9rem; }
  .demo-banner {
    border-left: 4px solid #f9a825; background: #fff8e1;
    padding: 10px 14px; border-radius: 8px; margin: 8px 0;
  }
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def pill(text: str, color: str) -> str:
    """HTML for a coloured status pill (render with st.markdown, unsafe HTML)."""
    return f'<span class="pill" style="background:{color}">{text}</span>'


def severity_pill(severity: str) -> str:
    return pill(severity, SEVERITY_COLORS.get(severity, "#666"))


def status_pill(status: str) -> str:
    return pill(status, STATUS_COLORS.get(status, "#666"))


def demo_banner(note: str) -> None:
    st.markdown(f'<div class="demo-banner">🎭 {note}</div>', unsafe_allow_html=True)
