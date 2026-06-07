import os
import sys

# Ensures sibling modules are importable on Streamlit Cloud
_dir = os.path.dirname(os.path.abspath(__file__))
if _dir not in sys.path:
    sys.path.insert(0, _dir)

import streamlit as st
from config import initialize_session_states
from sidebar import render_unified_dashboard_sidebar
from map_view import render_leaflet_component_iframe

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Open Node",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS  –  Google My Maps clone aesthetic
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

/* ── Force full-viewport, no scroll ───────────────────────────────────────── */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main, .block-container {
    background-color: #e8eaed !important;
    color: #202124 !important;
    font-family: 'Roboto', Arial, sans-serif !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}

[data-testid="stMain"] {
    position: absolute !important;
    inset: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 1 !important;
}

.block-container,
[data-testid="stAppViewBlockContainer"],
[data-testid="stVerticalBlock"],
.stElementContainer {
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100vw !important;
    height: 100vh !important;
    gap: 0 !important;
}

/* iframe fills viewport */
iframe {
    height: 100vh !important;
    width: 100vw !important;
    border: none !important;
    display: block !important;
}

/* ── Sidebar: Google My Maps floating card ─────────────────────────────────── */
[data-testid="stSidebar"] {
    position: fixed !important;
    top: 16px !important;
    left: 16px !important;
    height: auto !important;
    max-height: calc(100vh - 32px) !important;
    /* ── SIDEBAR WIDTH: adjust the three values below to change width ── */
    width: 300px !important;
    min-width: 300px !important;
    max-width: 300px !important;
    background-color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3), 0 4px 12px rgba(0,0,0,0.15) !important;
    z-index: 999999 !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
}

[data-testid="stSidebarUserContent"] {
    padding: 0 !important;
    height: auto !important;
    overflow-y: auto !important;
    scrollbar-width: thin !important;
    scrollbar-color: rgba(0,0,0,0.2) transparent !important;
    max-height: calc(100vh - 80px) !important;
}
[data-testid="stSidebarUserContent"]::-webkit-scrollbar { width: 4px; }
[data-testid="stSidebarUserContent"]::-webkit-scrollbar-thumb {
    background: rgba(0,0,0,0.2);
    border-radius: 2px;
}

/* Hide Streamlit chrome */
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
[data-testid="stHeader"],
header, #stDecoration { display: none !important; }

/* ── Brand header ─────────────────────────────────────────────────────────── */
.brand-title {
    font-family: 'Roboto', Arial, sans-serif !important;
    font-weight: 500 !important;
    font-style: normal !important;
    color: #ffffff !important;
    background-color: #1a73e8 !important;
    font-size: 15px !important;
    text-align: left !important;
    padding: 14px 16px !important;
    margin: 0 !important;
    border-bottom: none !important;
    letter-spacing: 0.2px !important;
}

/* ── Sidebar inner component spacing ─────────────────────────────────────── */
div.stNumberInput,
div.stTextInput,
div.stCheckbox,
div.stButton,
[data-testid="stExpander"],
div.stPopover,
div.stDownloadButton {
    padding-left: 14px !important;
    padding-right: 14px !important;
}

div.stButton,
div.stDownloadButton { margin-top: 4px !important; margin-bottom: 2px !important; }

/* ── Expanders: flat list sections ────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: none !important;
    background-color: transparent !important;
    box-shadow: none !important;
    margin-bottom: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    border-bottom: 1px solid #e8eaed !important;
    border-radius: 0 !important;
}
[data-testid="stExpander"] summary {
    padding: 9px 16px !important;
    background-color: #f8f9fa !important;
}
[data-testid="stExpander"] summary:hover { background-color: #f1f3f4 !important; }
[data-testid="stExpander"] summary p {
    font-size: 11px !important;
    font-weight: 500 !important;
    color: #202124 !important;
}
div[data-testid="stExpander"] fieldset {
    padding: 4px 16px !important;
    border: none !important;
}

/* ── Checkbox labels ──────────────────────────────────────────────────────── */
.stCheckbox label p {
    font-size: 11px !important;
    font-weight: 400 !important;
    color: #3c4043 !important;
    font-family: 'Roboto', Arial, sans-serif !important;
}
div[data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"] {
    background-color: #1a73e8 !important;
    border-color: #1a73e8 !important;
}

/* ── Text / number inputs ─────────────────────────────────────────────────── */
div[data-baseweb="input"] {
    background-color: transparent !important;
    border: none !important;
    border-bottom: 1px solid #dadce0 !important;
    border-radius: 0 !important;
}
div[data-baseweb="input"]:focus-within {
    border-bottom: 2px solid #1a73e8 !important;
}
.stTextInput label p,
.stNumberInput label p {
    font-size: 10px !important;
    font-weight: 500 !important;
    color: #5f6368 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.4px !important;
}

/* ── Primary action buttons (SCAN, CLEAR) ─────────────────────────────────── */
div.stButton > button[kind="secondary"] {
    background-color: #1a73e8 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 4px !important;
    padding: 8px 16px !important;
    box-shadow: none !important;
    width: 100% !important;
}
div.stButton > button[kind="secondary"]:hover { background-color: #1557b0 !important; }
div.stButton > button[kind="secondary"] p {
    color: #ffffff !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
}

/* Ghost button (CLEAR ALL) */
div.stButton > button[kind="primary"] {
    background: transparent !important;
    border: 1px solid #dadce0 !important;
    border-radius: 4px !important;
    width: 100% !important;
    padding: 6px 12px !important;
}
div.stButton > button[kind="primary"] p {
    color: #5f6368 !important;
    font-size: 10px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.4px !important;
}
div.stButton > button[kind="primary"]:hover { background: #f1f3f4 !important; }

/* Download buttons */
div.stDownloadButton > button {
    background-color: #ffffff !important;
    border: 1px solid #dadce0 !important;
    border-radius: 4px !important;
    width: 100% !important;
    padding: 6px 8px !important;
}
div.stDownloadButton > button:hover { background-color: #f8f9fa !important; }
div.stDownloadButton > button p {
    color: #1a73e8 !important;
    font-size: 10px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
}

/* Popover */
[data-testid="stPopover"] > button {
    background-color: #ffffff !important;
    border: 1px solid #dadce0 !important;
    border-radius: 4px !important;
    width: 100% !important;
    padding: 6px 12px !important;
}
[data-testid="stPopover"] > button p {
    color: #3c4043 !important;
    font-size: 10px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
}
[data-testid="stPopover"] > button:hover { background-color: #f8f9fa !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# BOOT
# ─────────────────────────────────────────────────────────────────────────────
initialize_session_states()

lat, lon, radius = render_unified_dashboard_sidebar()

render_leaflet_component_iframe(
    lat=lat,
    lon=lon,
    radius=radius,
    pts_active=st.session_state.scanned_records,
)
