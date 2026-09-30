import streamlit as st
import requests
import re
import json
import os

# --- PROGRAMMATIC LIGHT MODE LOCK (Must execute before st.set_page_config) ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
os.makedirs(_config_dir, exist_ok=True)
_theme_block = """[theme]
base="light"
primaryColor="#003366"
backgroundColor="#ffffff"
secondaryBackgroundColor="#f8fafc"
textColor="#003366"
font="sans serif"
"""
if not os.path.exists(_config_file):
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write(_theme_block)
else:
    with open(_config_file, "r", encoding="utf-8") as f:
        _cfg = f.read()
    if "[theme]" not in _cfg:
        with open(_config_file, "a", encoding="utf-8") as f:
            f.write("\n" + _theme_block)

# -----------------------------------------------------------------------------
# 1. BRANDED THEME & STRUCTURAL FULL OVERRIDES
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Open Node",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300;1,400&family=Montserrat:wght@400;500;600;700;800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

        /* Protect Material Symbols font on all icon elements so ligatures render correctly */
        .material-symbols-rounded,
        [data-testid="stIconMaterial"],
        [data-testid="stExpanderToggleIcon"],
        [data-testid="stExpanderToggleIcon"] *,
        [data-testid="stSidebarCollapseButton"] *,
        [data-testid="collapsedControl"] * {
            font-family: 'Material Symbols Rounded' !important;
            font-weight: normal !important;
            font-style: normal !important;
            line-height: 1 !important;
            text-transform: none !important;
            letter-spacing: normal !important;
            word-wrap: normal !important;
            white-space: nowrap !important;
            direction: ltr !important;
            -webkit-font-smoothing: antialiased !important;
        }

        /* ================================================================
           PRIME PHILIPPINES -- PALETTE OF SOVEREIGN INTELLIGENCE
           Backgrounds: #003366 (PRIME Blue) or #FFFCFB (Warm White) ONLY
           Accent:      #C9AB4C (PRIME Gold) -- never a background fill
           Text:        #003366 (Blue) or #181D1E (Gray) -- never #000000
           Radius:      0 everywhere -- Edges Stay Sharp
        ================================================================ */

        :root, [data-theme="dark"], [data-theme="light"], .stApp {
            color-scheme: light !important;
            --prime-blue:       #003366;
            --prime-warm-white: #FFFCFB;
            --prime-gold:       #C9AB4C;
            --prime-gray:       #181D1E;
            --prime-muted:      rgba(0, 51, 102, 0.45);
            --prime-divider:    rgba(0, 51, 102, 0.10);
            --prime-shadow:     0 4px 16px rgba(0, 51, 102, 0.10);
            --prime-radius:     0;
            --brand-midnight:   #003366;
            --brand-gold:       #C9AB4C;
            --white-clean:      #FFFCFB;
            --bg-offwhite:      #FFFCFB;
            --text-muted:       rgba(0, 51, 102, 0.45);
            --soft-shadow:      0 4px 16px rgba(0, 51, 102, 0.10);
        }

        html, body,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        .main, .block-container {
            background-color: var(--prime-warm-white) !important;
            color: var(--prime-blue) !important;
            font-family: 'Montserrat', Arial, Helvetica, sans-serif !important;
            color-scheme: light !important;
        }

        /* ----------------------------------------------------------------
           STREAMLIT HEADER -- transparent shell
        ---------------------------------------------------------------- */
        [data-testid="stHeader"], header {
            background: transparent !important;
            border-bottom: none !important;
            box-shadow: none !important;
            height: 0px !important;
            overflow: visible !important;
            pointer-events: none !important;
        }

        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapseButton"] {
            pointer-events: all !important;
        }

        [data-testid="stToolbar"], #stDecoration,
        [data-testid="stMainMenu"], [data-testid="stStatusWidget"] {
            display: none !important;
        }

        /* ----------------------------------------------------------------
           SIDEBAR -- STATIC & NON-COLLAPSIBLE (Modern Web Guidance)
        ---------------------------------------------------------------- */
        [data-testid="stSidebar"] {
            width: 310px !important;
            min-width: 310px !important;
            max-width: 310px !important;
            flex: 0 0 310px !important;
            transform: none !important;
            margin-left: 0 !important;
            transition: none !important;
            background-color: var(--prime-warm-white) !important;
            border-right: 2px solid var(--prime-gold) !important;
            box-shadow: 2px 0 20px rgba(0, 51, 102, 0.08) !important;
            z-index: 100 !important;
            position: relative !important;
        }

        /* Permanently suppress any native collapse / expand controls & empty header */
        [data-testid="stSidebarHeader"],
        [data-testid="stSidebarHeader"] *,
        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"],
        button[data-testid="stSidebarCollapseButton"],
        button[data-testid="stSidebarCollapsedControl"],
        [data-testid="stHeader"] [data-testid="collapsedControl"] {
            display: none !important;
            visibility: hidden !important;
            pointer-events: none !important;
            width: 0 !important;
            height: 0 !important;
            min-height: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
            opacity: 0 !important;
        }

        /* Sidebar scroll container with modern scrollbar and overscroll containment */
        [data-testid="stSidebarContent"] {
            background-color: var(--prime-warm-white) !important;
            color: var(--prime-blue) !important;
            padding: 0 14px 3rem 14px !important;
            height: 100dvh !important;
            max-height: 100dvh !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            overscroll-behavior: contain !important;
            scrollbar-width: thin !important;
            scrollbar-color: rgba(0, 51, 102, 0.2) transparent !important;
        }

        /* Modern subtle scrollbar with no ugly native arrow buttons */
        [data-testid="stSidebarContent"]::-webkit-scrollbar {
            width: 5px !important;
        }
        [data-testid="stSidebarContent"]::-webkit-scrollbar-track {
            background: transparent !important;
        }
        [data-testid="stSidebarContent"]::-webkit-scrollbar-thumb {
            background-color: rgba(0, 51, 102, 0.18) !important;
            border-radius: 0 !important;
        }
        [data-testid="stSidebarContent"]::-webkit-scrollbar-thumb:hover {
            background-color: var(--prime-gold) !important;
        }
        [data-testid="stSidebarContent"]::-webkit-scrollbar-button {
            display: none !important;
            width: 0 !important;
            height: 0 !important;
        }

        /* ----------------------------------------------------------------
           LAYOUT -- continuous flex viewport (100% width to avoid scrollbar jump)
        ---------------------------------------------------------------- */
        [data-testid="stAppViewContainer"] {
            display: flex !important;
            flex-direction: row !important;
            width: 100% !important;
            height: 100dvh !important;
            overflow: hidden !important;
        }

        [data-testid="stMain"] {
            flex: 1 1 0% !important;
            width: 100% !important;
            min-width: 0 !important;
            height: 100dvh !important;
            overflow: hidden !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        .block-container,
        [data-testid="stAppViewBlockContainer"],
        [data-testid="stVerticalBlock"],
        .stElementContainer {
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
            height: 100% !important;
            gap: 0 !important;
        }

        iframe {
            height: 100dvh !important;
            width: 100% !important;
            border: none !important;
            display: block !important;
        }

        /* ----------------------------------------------------------------
           TYPOGRAPHY -- Montserrat UI (no span override to protect icons)
        ---------------------------------------------------------------- */
        p, label, h1, h2, h3, h4, h5, h6, .stMarkdown {
            color: var(--prime-blue) !important;
            font-family: 'Montserrat', Arial, Helvetica, sans-serif !important;
        }

        /* ----------------------------------------------------------------
           FORM CONTROLS -- PRIME Warm White surfaces, sharp edges
        ---------------------------------------------------------------- */
        [data-testid="stTextInput"] div[data-baseweb="base-input"],
        [data-testid="stTextInput"] div[data-baseweb="input"],
        [data-testid="stNumberInput"] div[data-baseweb="base-input"],
        [data-testid="stNumberInput"] div[data-baseweb="input"],
        [data-testid="stNumberInputContainer"],
        div[data-baseweb="base-input"],
        div[data-baseweb="input"],
        div[data-testid="stTextInputRootElement"] {
            background-color: var(--prime-warm-white) !important;
            border: 1px solid rgba(0, 51, 102, 0.28) !important;
            border-radius: 0 !important;
            box-shadow: none !important;
        }

        [data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
        [data-testid="stTextInput"] div[data-baseweb="base-input"]:focus-within,
        [data-testid="stNumberInputContainer"]:focus-within,
        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="base-input"]:focus-within {
            border-color: var(--prime-gold) !important;
            box-shadow: 0 0 0 1px var(--prime-gold) !important;
        }

        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        div[data-baseweb="base-input"] input,
        div[data-baseweb="input"] input,
        div[data-testid="stNumberInputContainer"] input,
        input {
            background-color: var(--prime-warm-white) !important;
            color: var(--prime-blue) !important;
            -webkit-text-fill-color: var(--prime-blue) !important;
            font-family: 'Montserrat', sans-serif !important;
            font-size: 11px !important;
            font-weight: 600 !important;
            border-radius: 0 !important;
        }

        input::placeholder {
            color: var(--prime-muted) !important;
            -webkit-text-fill-color: var(--prime-muted) !important;
            font-weight: 400 !important;
            font-size: 10px !important;
            opacity: 1 !important;
        }

        .stTextInput label p,
        .stNumberInput label p,
        [data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] label {
            font-size: 9px !important;
            font-weight: 700 !important;
            color: var(--prime-muted) !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
            margin-bottom: 3px !important;
            font-family: 'Montserrat', sans-serif !important;
        }

        /* Number Input +/- Buttons */
        div[data-testid="stNumberInputContainer"] button,
        button[data-testid="stNumberInputStepDown"],
        button[data-testid="stNumberInputStepUp"] {
            background-color: var(--prime-warm-white) !important;
            color: var(--prime-blue) !important;
            border: none !important;
            border-left: 1px solid rgba(0, 51, 102, 0.18) !important;
            border-radius: 0 !important;
            min-width: 26px !important;
        }

        div[data-testid="stNumberInputContainer"] button:hover,
        button[data-testid="stNumberInputStepDown"]:hover,
        button[data-testid="stNumberInputStepUp"]:hover {
            background-color: rgba(201, 171, 76, 0.15) !important;
        }

        div[data-testid="stNumberInputContainer"] button svg,
        button[data-testid="stNumberInputStepDown"] svg,
        button[data-testid="stNumberInputStepUp"] svg {
            fill: var(--prime-blue) !important;
            stroke: var(--prime-blue) !important;
        }

        /* ----------------------------------------------------------------
           BUTTONS -- PRIME Blue on Warm White, Gold accent, sharp corners
        ---------------------------------------------------------------- */
        div.stButton > button[kind="secondary"],
        [data-testid="stPopover"] > button {
            background-color: var(--prime-blue) !important;
            border: 1.5px solid var(--prime-gold) !important;
            border-radius: 0 !important;
            width: 100% !important;
            padding: 10px 8px !important;
            box-shadow: 0 3px 10px rgba(0, 51, 102, 0.18) !important;
            letter-spacing: 1.5px !important;
            transition: all 0.15s ease !important;
            margin-bottom: 4px !important;
        }

        div.stButton > button[kind="secondary"]:hover,
        [data-testid="stPopover"] > button:hover {
            background-color: var(--prime-gold) !important;
            border-color: var(--prime-gold) !important;
            box-shadow: 0 4px 14px rgba(201, 171, 76, 0.3) !important;
        }

        div.stButton > button[kind="secondary"] p,
        [data-testid="stPopover"] > button p,
        [data-testid="stPopover"] > button div,
        div.stDownloadButton > button p {
            color: var(--prime-warm-white) !important;
            font-weight: 800 !important;
            font-size: 9px !important;
            text-transform: uppercase !important;
            letter-spacing: 1.5px !important;
        }

        div.stButton > button[kind="secondary"]:hover p,
        [data-testid="stPopover"] > button:hover p {
            color: var(--prime-blue) !important;
        }

        div.stDownloadButton > button {
            background-color: var(--prime-blue) !important;
            border: 1px solid var(--prime-blue) !important;
            border-radius: 0 !important;
            width: 100% !important;
            padding: 8px 6px !important;
            transition: all 0.15s ease !important;
        }

        div.stDownloadButton > button:hover {
            background-color: var(--prime-gold) !important;
            border-color: var(--prime-gold) !important;
        }

        div.stDownloadButton > button:hover p {
            color: var(--prime-blue) !important;
        }

        div.stButton > button[kind="primary"] {
            background: transparent !important;
            border: 1px solid rgba(0, 51, 102, 0.22) !important;
            border-radius: 0 !important;
            color: var(--prime-muted) !important;
            padding: 6px 8px !important;
            margin-top: 6px !important;
            margin-bottom: 12px !important;
            width: 100% !important;
            transition: all 0.15s ease !important;
        }

        div.stButton > button[kind="primary"]:hover {
            background: rgba(170, 46, 32, 0.08) !important;
            border-color: #AA2E20 !important;
        }

        div.stButton > button[kind="primary"] p {
            color: var(--prime-muted) !important;
            font-size: 9px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 1.5px !important;
            margin: 0 !important;
        }

        div.stButton > button[kind="primary"]:hover p {
            color: #AA2E20 !important;
        }

        /* ----------------------------------------------------------------
           EXPANDERS (POI categories) -- sharp, Warm White
        ---------------------------------------------------------------- */
        [data-testid="stSidebar"] [data-testid="stExpander"],
        [data-testid="stSidebar"] details,
        div[data-testid="stExpander"],
        details[data-testid="stExpander"] {
            background-color: var(--prime-warm-white) !important;
            border: 1px solid var(--prime-divider) !important;
            border-radius: 0 !important;
            margin-bottom: 2px !important;
            overflow: hidden !important;
        }

        [data-testid="stSidebar"] [data-testid="stExpander"] summary,
        [data-testid="stSidebar"] details > summary,
        div[data-testid="stExpander"] summary {
            background-color: var(--prime-warm-white) !important;
            color: var(--prime-blue) !important;
            padding: 7px 10px !important;
            border-radius: 0 !important;
        }

        [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover,
        div[data-testid="stExpander"] summary:hover {
            background-color: rgba(0, 51, 102, 0.04) !important;
        }

        [data-testid="stSidebar"] [data-testid="stExpander"] summary p,
        div[data-testid="stExpander"] summary p {
            color: var(--prime-blue) !important;
            font-size: 9px !important;
            font-weight: 700 !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
        }

        [data-testid="stExpanderToggleIcon"] {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-width: 18px !important;
            color: var(--prime-blue) !important;
        }

        [data-testid="stExpanderToggleIcon"] *,
        [data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stExpanderToggleIcon"] svg,
        div[data-testid="stExpanderToggleIcon"] svg,
        div[data-testid="stExpander"] summary svg {
            fill: var(--prime-blue) !important;
            color: var(--prime-blue) !important;
            font-size: 16px !important;
        }

        [data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stExpanderDetails"],
        div[data-testid="stExpanderDetails"] {
            background-color: var(--prime-warm-white) !important;
            border-top: 1px solid var(--prime-divider) !important;
            padding: 6px 8px !important;
        }

        /* ----------------------------------------------------------------
           CHECKBOXES -- sharp, Warm White unchecked, Blue checked
        ---------------------------------------------------------------- */
        .stCheckbox {
            display: flex !important;
            align-items: center !important;
            margin-bottom: 2px !important;
        }

        .stCheckbox label {
            display: inline-flex !important;
            align-items: center !important;
            gap: 6px !important;
            margin: 0 !important;
            padding: 0 !important;
            cursor: pointer !important;
        }

        .stCheckbox label p {
            font-size: 10px !important;
            font-weight: 500 !important;
            color: var(--prime-blue) !important;
            display: inline-block !important;
            margin: 0 !important;
            line-height: 1.3 !important;
        }

        div[data-baseweb="checkbox"] { align-self: center !important; }

        div[data-testid="stCheckbox"] div[role="checkbox"],
        div[data-baseweb="checkbox"] > div:first-child,
        div[data-testid="stCheckbox"] [role="checkbox"][aria-checked="false"] {
            background-color: var(--prime-warm-white) !important;
            border: 1.5px solid rgba(0, 51, 102, 0.40) !important;
            border-radius: 0 !important;
        }

        div[data-testid="stCheckbox"]:hover div[role="checkbox"],
        div[data-baseweb="checkbox"]:hover > div:first-child {
            border-color: var(--prime-blue) !important;
        }

        div[data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"],
        div[data-baseweb="checkbox"] input:checked + div,
        div[data-baseweb="checkbox"] div[aria-checked="true"],
        div[data-baseweb="checkbox"] [role="checkbox"][aria-checked="true"] > div,
        div[data-baseweb="checkbox"] [role="checkbox"][aria-checked="true"] {
            background-color: var(--prime-blue) !important;
            border-color: var(--prime-blue) !important;
            border-radius: 0 !important;
        }

        div[data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"] svg,
        div[data-baseweb="checkbox"] input:checked + div svg,
        div[data-baseweb="checkbox"] [aria-checked="true"] svg {
            fill: var(--prime-warm-white) !important;
            stroke: var(--prime-warm-white) !important;
        }

        /* ----------------------------------------------------------------
           POPOVERS & FILE UPLOADER
        ---------------------------------------------------------------- */
        div[data-testid="stPopoverBody"] {
            background-color: var(--prime-warm-white) !important;
            border: 1px solid var(--prime-divider) !important;
            box-shadow: var(--prime-shadow) !important;
            border-radius: 0 !important;
            color: var(--prime-blue) !important;
        }

        section[data-testid="stFileUploaderDropzone"] {
            background-color: var(--prime-warm-white) !important;
            border: 1.5px dashed rgba(0, 51, 102, 0.25) !important;
            border-radius: 0 !important;
        }

        section[data-testid="stFileUploaderDropzone"]:hover {
            border-color: var(--prime-gold) !important;
        }

        section[data-testid="stFileUploaderDropzone"] div,
        section[data-testid="stFileUploaderDropzone"] span,
        section[data-testid="stFileUploaderDropzone"] small,
        section[data-testid="stFileUploaderDropzone"] p {
            color: var(--prime-blue) !important;
        }

        section[data-testid="stFileUploaderDropzone"] button {
            background-color: var(--prime-blue) !important;
            color: var(--prime-warm-white) !important;
            border: none !important;
            border-radius: 0 !important;
            font-weight: 700 !important;
            font-size: 9px !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
        }

        section[data-testid="stFileUploaderDropzone"] button:hover {
            background-color: var(--prime-gold) !important;
        }

        /* ----------------------------------------------------------------
           SELECT / DROPDOWN
        ---------------------------------------------------------------- */
        div[data-baseweb="select"] {
            background-color: var(--prime-warm-white) !important;
            border: 1px solid rgba(0, 51, 102, 0.22) !important;
            border-radius: 0 !important;
            color: var(--prime-blue) !important;
        }

        div[data-baseweb="select"] * {
            color: var(--prime-blue) !important;
            background-color: transparent !important;
        }

        div[data-baseweb="popover"], ul[data-baseweb="menu"] {
            background-color: var(--prime-warm-white) !important;
            border: 1px solid var(--prime-divider) !important;
            box-shadow: var(--prime-shadow) !important;
            border-radius: 0 !important;
        }

        li[data-baseweb="menu-item"] {
            color: var(--prime-blue) !important;
            background-color: var(--prime-warm-white) !important;
        }

        li[data-baseweb="menu-item"]:hover {
            background-color: rgba(0, 51, 102, 0.06) !important;
        }

        /* ----------------------------------------------------------------
           BRAND TITLE -- Cormorant Garamond Italic (sidebar header)
        ---------------------------------------------------------------- */
        .brand-title {
            font-family: 'Cormorant Garamond', Georgia, serif !important;
            font-style: italic !important;
            font-weight: 400 !important;
            color: var(--prime-warm-white) !important;
            font-size: 26px !important;
            text-align: center !important;
            background-color: var(--prime-blue) !important;
            border-bottom: 2px solid var(--prime-gold) !important;
            padding: 16px 14px 14px 14px !important;
            margin: 0 -14px 16px -14px !important;
            letter-spacing: -0.01em !important;
            user-select: none !important;
            box-shadow: 0 4px 12px rgba(0, 51, 102, 0.12) !important;
        }

        /* ----------------------------------------------------------------
           HR DIVIDERS
        ---------------------------------------------------------------- */
        hr {
            border: none !important;
            border-top: 1px solid var(--prime-divider) !important;
            margin: 10px 0 !important;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. STATE PERSISTENCE & DATA CONFIGURATIONS
# -----------------------------------------------------------------------------
DEFAULT_COORDS = "14.5995, 120.9842"
DEFAULT_RADIUS = 1000

if 'geo_coords' not in st.session_state: st.session_state.geo_coords = DEFAULT_COORDS
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = DEFAULT_RADIUS
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'last_scan_lat' not in st.session_state: st.session_state.last_scan_lat = 14.5995
if 'last_scan_lon' not in st.session_state: st.session_state.last_scan_lon = 120.9842
if 'layer_meta' not in st.session_state: st.session_state.layer_meta = {}
if 'layer_groups' not in st.session_state: st.session_state.layer_groups = {}
if 'scan_active_loading' not in st.session_state: st.session_state.scan_active_loading = False

if 'target_config' not in st.session_state:
    st.session_state.target_config = {"size": 24, "color": "#003366", "style": "star"}

if 'radius_config' not in st.session_state:
    st.session_state.radius_config = {"color": "#003366", "fill_opacity": 0.08, "weight": 1.5}

if 'global_marker_style' not in st.session_state: st.session_state.global_marker_style = "dots"
if 'global_marker_size' not in st.session_state: st.session_state.global_marker_size = 12
if 'global_marker_color' not in st.session_state: st.session_state.global_marker_color = "#003366"

POI_CONFIG = {
    "COMMERCIAL & OFFICES": [['Corporate Office', '"building"~"office|commercial",i'], ['IT/Tech Center', '"office"~"it|telecommunication",i'], ['Business Center', '"building"="commercial"'], ['Bank', '"amenity"="bank"'], ['ATM', '"amenity"="atm"'], ['Office', '"office"="yes"']],
    "RETAIL": [['Mall/Department Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"market|grocery",i'], ['Convenience Store', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Hardware', '"shop"~"hardware|doityourself",i'], ['General Shops', '"shop"~"boutique|clothes|shoes",i'], ['Beauty', '"shop"="beauty"'], ['Bicycle', '"shop"="bicycle"'], ['Books/Stationary', '"shop"~"books|stationary",i'], ['Car', '"shop"="car"'], ['Chemist', '"shop"="chemist"'], ['Clothes', '"shop"="clothes"'], ['Copyshop', '"shop"="copyshop"'], ['Cosmetics', '"shop"="cosmetics"'], ['Department store', '"shop"="department_store"'], ['DIY/hardware', '"shop"~"hardware|doityourself",i'], ['Garden centre', '"shop"="garden_centre"'], ['General', '"shop"="general"'], ['Gift', '"shop"="gift"'], ['Hairdresser', '"shop"="hairdresser"'], ['Jewelry', '"shop"="jewelry"'], ['Kiosk', '"shop"="kiosk"'], ['Leather', '"shop"="leather"'], ['Marketplace', '"amenity"="marketplace"'], ['Musical instrument', '"shop"="musical_instrument"'], ['Optician', '"shop"="optician"'], ['Pets', '"shop"="pets"'], ['Phone', '"shop"="mobile_phone"'], ['Photo', '"shop"="photo"'], ['Shoes', '"shop"="shoes"'], ['Shopping centre', '"shop"="mall"'], ['Textiles', '"shop"="textiles"'], ['Toys', '"shop"="toys"'], ['Travel agency', '"shop"="travel_agency"']],
    "FOOD, BEVERAGE & HOSPITALITY": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee Shop', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"'], ['Bar/Pub/Nightclub', '"amenity"~"bar|pub|nightclub",i'], ['Bakery/Pastry', '"shop"="bakery"'], ['BBQ', '"amenity"="bbq"'], ['Biergarten', '"amenity"="biergarten"'], ['Food court', '"amenity"="food_court"'], ['Ice cream', '"amenity"="ice_cream"'], ['Pub', '"amenity"="pub"'], ['Hotel', '"tourism"="hotel"'], ['Motel', '"tourism"="motel"'], ['Alpine Hut', '"tourism"="alpine_hut"'], ['Apartment', '"tourism"="apartment"'], ['Camp Site', '"tourism"="camp_site"'], ['Chalet', '"tourism"="chalet"'], ['Guest House', '"tourism"="guest_house"'], ['Hostel', '"tourism"="hostel"'], ['Casino', '"amenity"="casino"']],
    "RESIDENTIAL": [['Apartments', '"building"="apartments"'], ['House', '"building"="house"'], ['Residential Area', '"landuse"="residential"'], ['Condominium', '"building"="residential"'], ['City', '"place"="city"'], ['Town', '"place"="town"'], ['Village', '"place"="village"'], ['Hamlet', '"place"="hamlet"'], ['Suburb', '"place"="suburb"'], ['Construction', '"landuse"="construction"']],
    "INDUSTRIAL & LOGISTICS": [['Expressway Exits', '"highway"~"motorway_junction|toll_gantry",i'], ['Ports & Terminals', '"industrial"="port"'], ['Manufacturing Plants', '"industrial"~"factory|manufacturing|processing",i'], ['Cold Storage Facilities', '"warehouse"~"cold_store|cold_storage",i'], ['Industrial Parks/Estates', '"landuse"~"industrial|industrial_estate",i'], ['Warehouses & Depots', '"building"~"warehouse|depot",i'], ['Storage Facilities', '"building"="storage"'], ['Truck Access Routes (HGV)', '"hgv"~"designated|yes",i']],
    "HEALTH & EMERGENCY SERVICES": [['Hospital', '"amenity"~"hospital|clinic",i'], ['Clinic', '"amenity"="clinic"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Police Station', '"amenity"="police"'], ['Fire Station', '"amenity"="fire_station"'], ['Firestation', '"amenity"="fire_station"'], ['Police', '"amenity"="police"'], ['Hospital Adv', '"amenity"="hospital"'], ['Defibrillator - AED', '"emergency"="defibrillator"'], ['Fire hose/extinguisher', '"emergency"~"fire_hose|fire_extinguisher",i']],
    "GOVERNMENT, EDUCATION & INFRASTRUCTURE": [['City Hall', '"amenity"="townhall"'], ['Airport Terminal', '"aeroway"~"terminal|aerodrome",i'], ['University/College', '"amenity"~"university|college",i'], ['K-12 School', '"amenity"="school"'], ['Vocational/Other', '"amenity"="learning_centre"'], ['Embassy', '"amenity"="embassy"'], ['Library', '"amenity"="library"'], ['Music School', '"amenity"="music_school"'], ['Letter Box', '"amenity"="letter_box"'], ['Post Office', '"amenity"="post_office"'], ['School/College', '"amenity"~"school|college",i'], ['University', '"amenity"="university"'], ['Kindergarten', '"amenity"="kindergarten"'], ['Public camera', '"man_made"="surveillance"']],
    "LEISURE, SPORTS & PUBLIC SPACES": [['Church', '"religion"="christian"'], ['Mosque', '"religion"="muslim"'], ['Buddhist Temple', '"religion"="buddhist"'], ['Hindu Temple', '"religion"="hindu"'], ['Synagogue', '"religion"="jewish"'], ['Cemetery', '"landuse"="cemetery"'], ['Spa', '"leisure"="spa"'], ['Sauna', '"leisure"="sauna"'], ['Bench', '"amenity"="bench"'], ['Bicycle Parking', '"amenity"="bicycle_parking"'], ['Bicycle Rental', '"amenity"="bicycle_rental"'], ['Cinema', '"amenity"="cinema"'], ['Fuel', '"amenity"="fuel"'], ['Parking', '"amenity"="parking"'], ['Taxi', '"amenity"="taxi"'], ['Theatre', '"amenity"="theatre"'], ['Toilets', '"amenity"="toilets"'], ['American football', '"sport"="american_football"'], ['Baseball', '"sport"="baseball"'], ['Basketball', '"sport"="basketball"'], ['Cycling', '"sport"="cycling"'], ['Gymnastics', '"sport"="gymnastics"'], ['Golf', '"sport"="golf"'], ['Hockey', '"sport"="hockey"'], ['Horse racing', '"sport"="horse_racing"'], ['Ice hockey', '"sport"="ice_hockey"'], ['Soccer', '"sport"="soccer"'], ['Sports centre', '"leisure"="sports_centre"'], ['Surfing', '"sport"="surfing"'], ['Swimming', '"sport"="swimming"'], ['Tennis', '"sport"="tennis"'], ['Volleyball', '"sport"="volleyball"'], ['Busstop', '"highway"="bus_stop"'], ['E-bike charging', '"amenity"="charging_station"'], ['Recycling', '"amenity"="recycling"'], ['Fixme', '"fixme"~".",i'], ['Note-Node', '"type"="node"'], ['Note-Way', '"type"="way"'], ['Image', '"image"~".",i']]
}

ADVANCED_CONFIG = {}

def compile_features_kml(features):
    kml = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scanned POIs</name>'
    for f in features:
        if not f.get('visible', True): continue
        name = f.get('name', 'Asset').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        class_type = f.get('type', 'Node').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        kml += f"<Placemark><name>{name}</name><description>{class_type}</description><Point><coordinates>{f['lon']},{f['lat']},0</coordinates></Point></Placemark>"
    return kml + '</Document></kml>'

# -----------------------------------------------------------------------------
# 3. SIDEBAR CONTROLS & GEOPROCESSING
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="brand-title">Open Node</div>', unsafe_allow_html=True)
    
    selected_tags = []
    scan_triggered = st.button("SCAN AREA", type="secondary", use_container_width=True, key="scan_btn")
    
    location_input = st.text_input("COORDINATES", value=st.session_state.geo_coords, key="geo_coords_input")
    radius_val = st.number_input("RADIUS (METERS)", min_value=100, max_value=50000, value=st.session_state.geo_radius, key="geo_radius_input", step=100)
    st.session_state.geo_radius = radius_val

    coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", location_input)
    if coord_match:
        lat_coord, lon_coord = float(coord_match.group(1)), float(coord_match.group(2))
        st.session_state.geo_coords = location_input
    else:
        fallback_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", st.session_state.geo_coords)
        lat_coord, lon_coord = (float(fallback_match.group(1)), float(fallback_match.group(2))) if fallback_match else (14.5995, 120.9842)

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    search_query = st.text_input("SEARCH TAGS", placeholder="Search parameters...").lower()
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    
    for cat_name, node_items in POI_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for label, tag in matched:
                    if st.checkbox(label, key=f"chk_{cat_name}_{label}"): selected_tags.append(tag)

    st.markdown("<div style='font-weight: 700; font-size: 11px; margin-top: 15px; margin-bottom: 8px; color: #003366; letter-spacing: 1px;'>ADVANCED POIs</div>", unsafe_allow_html=True)
    with st.container():
        for cat_name, node_items in ADVANCED_CONFIG.items():
            matched = [item for item in node_items if search_query in item[0].lower()]
            if matched:
                with st.expander(cat_name, expanded=(len(search_query) > 0)):
                    for label, tag in matched:
                        if st.checkbox(label, key=f"chk_adv_{cat_name}_{label}"): selected_tags.append(tag)

    if scan_triggered:
        if not selected_tags:
            st.error("Select >= 1 layer.")
        else:
            st.session_state.scan_active_loading = True
            records = []
            success = False
            
            try:
                import osmnx as ox
                tags_dict = {}
                for tag in selected_tags:
                    clean = tag.replace('"', '')
                    if '=' in clean:
                        k, v = clean.split('=', 1)
                        if '|' in v: v = [x.strip() for x in v.split('|')]
                        tags_dict[k] = v
                    else:
                        tags_dict[clean] = True
                        
                gdf = ox.geometries_from_point((lat_coord, lon_coord), tags_dict, dist=radius_val)
                if not gdf.empty:
                    for idx, row in gdf.iterrows():
                        if hasattr(row.geometry, 'centroid'):
                            c_lat, c_lon = row.geometry.centroid.y, row.geometry.centroid.x
                        else: continue
                        name = row.get('name', 'Unknown')
                        if isinstance(name, float): name = 'Unknown'
                        
                        matched_type = 'Node'
                        for k in tags_dict.keys():
                            if k in row and row[k]:
                                matched_type = str(row[k])
                                break
                        records.append({
                            "lat": c_lat, "lon": c_lon, "name": str(name), 
                            "type": matched_type, "visible": True, "uid": len(records)
                        })
                    st.session_state.scanned_records = records
                    st.session_state.last_scan_lat = lat_coord
                    st.session_state.last_scan_lon = lon_coord
                    success = True
            except Exception: pass

            if not success:
                url = "https://overpass-api.de/api/interpreter"
                statements = "\n".join([f"  nwr[{tag}](around:{radius_val},{lat_coord},{lon_coord});" for tag in selected_tags])
                ql = f"[out:json][timeout:90];(\n{statements}\n);\nout center;"
                try:
                    res = requests.post(url, data={"data": ql}, headers={"User-Agent": "OpenNode/3.1"}, timeout=90)
                    if res.status_code == 200:
                        for el in res.json().get('elements', []):
                            e_lat = el.get('lat') or el.get('center', {}).get('lat')
                            e_lon = el.get('lon') or el.get('center', {}).get('lon')
                            if e_lat and e_lon:
                                tags = el.get('tags', {})
                                records.append({
                                    "lat": e_lat, "lon": e_lon, "name": tags.get('name', 'Unknown'), 
                                    "type": tags.get('amenity') or tags.get('shop') or tags.get('building') or 'Node',
                                    "visible": True, "uid": len(records)
                                })
                        st.session_state.scanned_records = records
                        st.session_state.last_scan_lat = lat_coord
                        st.session_state.last_scan_lon = lon_coord
                        success = True
                except Exception: pass
            
            st.session_state.scan_active_loading = False
            if success: st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("CLEAR ALL", type="primary", key="clear_btn"):
        st.session_state.scanned_records = []
        st.session_state.layer_meta = {}
        st.session_state.layer_groups = {}
        st.session_state.scan_active_loading = False
        for key in list(st.session_state.keys()):
            if key.startswith("chk_"): st.session_state[key] = False
        st.rerun()

    st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    # Filter only fully visible pins for strict map-sync exports
    visible_only_records = [p for p in st.session_state.scanned_records if p.get('visible', True)]
    
    with col1: st.download_button("RADIUS", json.dumps(visible_only_records), "scan.json", "application/json", use_container_width=True)
    with col2: st.download_button("MARKERS", compile_features_kml(st.session_state.scanned_records), "POIs.kml", "application/vnd.google-earth.kml+xml", use_container_width=True)

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

    with st.popover("IMPORT FILE", use_container_width=True):
        imported_file = st.file_uploader("Select JSON", type=["json"], label_visibility="collapsed")
        if imported_file is not None:
            if st.button("LOAD", type="secondary", use_container_width=True):
                try:
                    data = json.load(imported_file)
                    st.session_state.scanned_records = data.get("scanned_records", data)
                    st.session_state.geo_coords = data.get("coords", st.session_state.geo_coords)
                    st.session_state.geo_radius = data.get("radius", st.session_state.geo_radius)
                    st.rerun()
                except Exception: st.error("Invalid File")

# -----------------------------------------------------------------------------
# 4. MAP FRAME RENDERING ENGINE & INTERACTION ARCHITECTURE
# -----------------------------------------------------------------------------
pts_active = st.session_state.scanned_records
unique_layers = list(set([p.get('type', 'Unclassified') for p in pts_active]))
cat_palette = ["#003366", "#C9AB4C", "#1A5A8A", "#A8862E", "#3D7DA8", "#7A5C10", "#6A94B0", "#D4B85A", "#001F3F", "#E8D494"]

for idx, layer in enumerate(unique_layers):
    if layer not in st.session_state.layer_meta:
        st.session_state.layer_meta[layer] = {
            "color": cat_palette[idx % len(cat_palette)],
            "style": st.session_state.global_marker_style,
            "size": st.session_state.global_marker_size
        }

layer_meta_json = json.dumps(st.session_state.layer_meta)
target_config_json = json.dumps(st.session_state.target_config)
radius_config_json = json.dumps(st.session_state.radius_config)
geojson_str = json.dumps(pts_active)

render_lat = lat_coord
render_lon = lon_coord
is_stale = "true" if (lat_coord != st.session_state.last_scan_lat or lon_coord != st.session_state.last_scan_lon) else "false"
show_loading = "true" if st.session_state.scan_active_loading else "false"

leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #FFFCFB; overflow: hidden; font-family: 'Montserrat', sans-serif; }
        #map-container { position: relative; width: 100%; height: 100vh; }
        #map { height: 100vh; width: 100%; z-index: 1; }

        /* Centered Loading Splash Overlay UI */
        #map-loading-overlay {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
            background: rgba(255, 252, 251, 0.82); z-index: 9999; 
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            transition: opacity 0.3s ease; pointer-events: all;
        }
        .loading-spinner {
            width: 40px; height: 40px; border: 4px solid rgba(0, 51, 102, 0.12);
            border-left-color: #003366; border-radius: 50%; animation: spin 1s linear infinite;
            margin-bottom: 12px;
        }
        .loading-text { font-size: 11px; font-weight: 700; color: #003366; text-transform: uppercase; letter-spacing: 1.5px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        #scan-results-panel { 
            position: absolute; top: 10px; right: 10px; z-index: 1000; background: #FFFCFB; width: 310px; 
            max-height: calc(100vh - 20px); border-radius: 0; border: 1px solid rgba(0, 51, 102, 0.18); 
            border-top: 2px solid #C9AB4C;
            background-clip: padding-box; display: flex; flex-direction: column; overflow: hidden; 
            box-shadow: 0 4px 20px rgba(0, 51, 102, 0.12); 
            transition: max-height 0.25s cubic-bezier(0.4, 0, 0.2, 1), width 0.2s ease, box-shadow 0.2s ease;
        }

        #scan-results-panel.collapsed {
            max-height: 38px !important;
            width: auto !important;
            min-width: 170px !important;
            box-shadow: 0 2px 10px rgba(0, 51, 102, 0.18) !important;
        }

        #scan-results-panel.collapsed #workspace-content-body {
            display: none !important;
        }

        #scan-results-panel.collapsed #workspace-toggle-arrow {
            transform: rotate(-90deg);
        }

        #scan-results-panel.collapsed #group-layers-trigger-btn {
            display: none !important;
        }

        .results-header { background: #003366; color: #FFFCFB; padding: 9px 12px; font-size: 10px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; border-bottom: 2px solid #C9AB4C; letter-spacing: 1.5px; user-select: none; }
        .results-list { overflow-y: auto; flex-grow: 1; padding-bottom: 0px; max-height: 250px; }
        .layer-category-block { border-bottom: 1px solid rgba(0,51,102,0.08); }
        .layer-category-header { background: #FFFCFB; padding: 6px 10px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; user-select: none; }
        .layer-header-left { display: flex; align-items: center; gap: 6px; font-size: 9px; font-weight: 700; color: #003366; text-transform: uppercase; flex-grow: 1; overflow: hidden;}
        .layer-category-items { padding: 0; background: rgba(0,51,102,0.03); }
        .layer-category-items.collapsed { display: none !important; }
        
        .results-item { padding: 4px 8px 4px 16px; font-size: 9px; font-weight: 600; color: rgba(0,51,102,0.55); display: flex; justify-content: space-between; align-items: center; cursor: pointer; border-bottom: 1px solid rgba(0,51,102,0.06); }
        .results-item:hover { background: #FFFCFB; color: #003366; }
        
        .action-icon-trigger { cursor: pointer; padding: 2px; display: inline-flex; align-items: center; justify-content: center; width: 18px; height: 18px; border-radius: 0; transition: all 0.15s; }
        .action-icon-trigger:hover { background: rgba(0, 51, 102, 0.06); }
        .action-icon-trigger svg { fill: rgba(0,51,102,0.45); width: 12px; height: 12px; }
        .action-icon-trigger:hover svg { fill: #003366; }
        .action-icon-trigger.delete-btn:hover svg { fill: #AA2E20; }

        .poi-text-label { background: #FFFCFB; border: 1px solid #003366; padding: 2px 4px; border-radius: 0; font-size: 9px; font-family: 'Montserrat', sans-serif; font-weight: 700; white-space: nowrap; box-shadow: 0 2px 4px rgba(0,51,102,0.1); }
        .hide-labels .poi-text-label { display: none !important; }
        .color-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; border: 1px solid rgba(0,0,0,0.1); }
        
        .config-block-wrapper { padding: 6px 12px; background: #FFFCFB; border-bottom: 1px solid rgba(0, 51, 102, 0.08); display: flex; flex-direction: column; gap: 4px; }
        .config-headline { 
            font-size: 8px; font-weight: 800; color: #003366; text-transform: uppercase; letter-spacing: 1px; 
            margin-bottom: 2px; cursor: pointer; display: flex; align-items: center; justify-content: space-between;
            user-select: none;
        }
        .config-headline:hover { color: #C9AB4C; }
        .sec-toggle { font-size: 8px; color: rgba(0,51,102,0.45); transition: transform 0.2s ease; }
        .config-block-wrapper.section-collapsed .config-flex-row { display: none !important; }
        .config-block-wrapper.section-collapsed .sec-toggle { transform: rotate(-90deg); }

        .config-flex-row { display: flex; align-items: center; justify-content: space-between; font-size: 9px; font-weight: 600; color: #003366; gap: 6px; }
        .config-flex-row select, .config-flex-row input { font-size: 9px; font-family: 'Montserrat', sans-serif; color: #003366; background: #FFFCFB; border: 1px solid rgba(0, 51, 102, 0.18); border-radius: 0; padding: 2px 4px; outline: none; }
        .slider-control-element { flex-grow: 1; margin: 0; -webkit-appearance: none; height: 4px; background: rgba(0,51,102,0.12); border-radius: 0; outline: none; }
        .slider-control-element::-webkit-slider-thumb { -webkit-appearance: none; width: 10px; height: 10px; border-radius: 50%; background: #003366; cursor: pointer; }

        .group-cluster-block { background: rgba(0,51,102,0.04); border-left: 3px solid #C9AB4C; margin-bottom: 4px; border-bottom: 1px solid rgba(0,51,102,0.08); }
        .group-cluster-header { background: rgba(0,51,102,0.07); padding: 6px 10px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; }
        .group-cluster-title { font-size: 9px; font-weight: 800; color: #003366; text-transform: uppercase; display: flex; align-items: center; gap: 6px; }
        .cluster-popover-modal { display: none; position: absolute; top: 40px; left: 10px; right: 10px; background: #FFFCFB; border: 1px solid #003366; border-top: 2px solid #C9AB4C; z-index: 2000; border-radius: 0; box-shadow: 0 4px 20px rgba(0,51,102,0.18); padding: 10px; }
        .cluster-popover-modal.active { display: block; }
        .cluster-selection-row { display: flex; align-items: center; gap: 8px; font-size: 9px; padding: 4px 0; color: #003366; font-weight: 600; }
    </style>
</head>
<body>
    <div id="map-container">
        <div id="map-loading-overlay" style="display: none;">
            <div class="loading-spinner"></div>
            <div class="loading-text">Scanning Area...</div>
        </div>
        
        <div id="map"></div>

        <div id="scan-results-panel">
            <div class="results-header" onclick="toggleWorkspacePanel(event)" style="cursor: pointer; user-select: none;">
                <div style="display: flex; align-items: center; gap: 6px;">
                    <span id="workspace-toggle-arrow" style="font-size: 9px; transition: transform 0.2s ease; display: inline-block;">&#9660;</span>
                    <span>WORKSPACE</span>
                    <span id="results-count" style="color:#C9AB4C; font-weight: 800; font-size: 10px; margin-left: 2px;">0</span>
                </div>
                <div style="display: flex; align-items: center; gap: 6px;" onclick="event.stopPropagation();">
                    <span id="group-layers-trigger-btn" onclick="openClusterModalWindow()" style="color: #ffffff; font-size: 8px; font-weight: 700; border: 1px solid #C9AB4C; padding: 2px 5px; border-radius: 2px; cursor: pointer;">GROUP LAYERS</span>
                    <button id="workspace-toggle-btn" onclick="toggleWorkspacePanel(event)" style="background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.35); color: #ffffff; border-radius: 3px; font-size: 12px; font-weight: bold; width: 20px; height: 20px; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; padding: 0; line-height: 1;" title="Collapse/Expand Workspace">&minus;</button>
                </div>
            </div>

            <div id="workspace-content-body" style="overflow-y: auto; flex-grow: 1; display: flex; flex-direction: column;">
                <div id="cluster-modal-overlay" class="cluster-popover-modal">
                    <div style="font-size: 9px; font-weight: 800; color: #003366; border-bottom: 1px solid #C9AB4C; padding-bottom: 4px; margin-bottom: 8px;">CREATE LAYER CLUSTER GROUP</div>
                    <div style="margin-bottom: 8px;">
                        <input type="text" id="new-cluster-name-input" placeholder="Enter cluster namespace..." style="width: calc(100% - 10px); font-family: Montserrat; font-size: 9px; padding: 4px; border: 1px solid rgba(0,51,102,0.2);">
                    </div>
                    <div id="cluster-checkbox-target-mount" style="max-height: 140px; overflow-y: auto; margin-bottom: 8px;"></div>
                    <div style="display: flex; gap: 4px;">
                        <button onclick="commitStructuralLayerCluster()" style="flex:1; background: #003366; color:#fff; border:none; padding: 4px; font-size:9px; font-weight:700; cursor:pointer;">BUILD</button>
                        <button onclick="closeClusterModalWindow()" style="flex:1; background: #888780; color:#fff; border:none; padding: 4px; font-size:9px; font-weight:700; cursor:pointer;">CANCEL</button>
                    </div>
                </div>
                
                <div class="config-block-wrapper" style="border-bottom: 2px solid var(--brand-gold);">
                    <div class="config-headline" onclick="toggleConfigSection(this)"><span>Basemap Controller</span><span class="sec-toggle">&#9660;</span></div>
                    <div class="config-flex-row">
                        <span>Tile Style:</span>
                        <select id="basemap-select" onchange="switchActiveBasemap(this.value)">
                            <option value="osm">OpenStreetMap</option>
                            <option value="satellite">Satellite View</option>
                            <option value="carto">Carto Light</option>
                        </select>
                        <label style="font-size:9px; font-weight:700; color:#003366; display:flex; align-items:center; gap:3px; cursor:pointer;">
                            <input type="checkbox" id="label-toggle-chk" onchange="toggleLabelsMatrix(this.checked)" style="accent-color: #003366;"> Labels
                        </label>
                    </div>
                </div>
                
                <div class="config-block-wrapper">
                    <div class="config-headline" onclick="toggleConfigSection(this)"><span>Global Markers</span><span class="sec-toggle">&#9660;</span></div>
                    <div class="config-flex-row">
                        <span>Style:</span>
                        <select id="gl-marker-style" onchange="patchGlobalMarkerStyle(this.value)">
                            <option value="dots">Dots</option>
                            <option value="pin">Pin Location</option>
                            <option value="modern-pin">Modern Drop-Pin</option>
                        </select>
                        <span>Size:</span>
                        <input type="range" min="10" max="40" value="__GLOBAL_MARKER_SIZE__" class="slider-control-element" id="gl-marker-size" oninput="patchGlobalMarkerSize(this.value)">
                    </div>
                    <div class="config-flex-row">
                        <span>Color:</span>
                        <input type="color" id="gl-marker-color" value="__GLOBAL_MARKER_COLOR__" onchange="patchGlobalMarkerColor(this.value)">
                        <select onchange="document.getElementById('gl-marker-color').value=this.value; patchGlobalMarkerColor(this.value);" style="width:70px;">
                            <option value="">Preset</option>
                            <option value="#003366">Midnight</option>
                            <option value="#C9AB4C">Gold</option>
                            <option value="#AA2E20">Crimson</option>
                        </select>
                    </div>
                </div>

                <div class="config-block-wrapper">
                    <div class="config-headline" onclick="toggleConfigSection(this)"><span>Target Coordinates & Radius Layer</span><span class="sec-toggle">&#9660;</span></div>
                    <div class="config-flex-row">
                        <span>Target:</span>
                        <select onchange="patchTargetCenterConfig('style', this.value)">
                            <option value="star">Star</option>
                            <option value="circle">Dot</option>
                        </select>
                        <input type="color" value="#003366" onchange="patchTargetCenterConfig('color', this.value)">
                        <input type="range" min="10" max="60" value="24" class="slider-control-element" oninput="patchTargetCenterConfig('size', this.value)">
                    </div>
                    <div class="config-flex-row">
                        <span>Radius Fill:</span>
                        <input type="color" value="#003366" onchange="patchRadiusLayerConfig('color', this.value)">
                        <span>Opacity:</span>
                        <input type="range" min="0" max="1" step="0.01" value="0.08" class="slider-control-element" oninput="patchRadiusLayerConfig('fill_opacity', this.value)">
                    </div>
                    <div class="config-flex-row">
                        <span>Thickness:</span>
                        <input type="range" min="0.5" max="8" step="0.5" value="1.5" class="slider-control-element" oninput="patchRadiusLayerConfig('weight', this.value)">
                    </div>
                </div>
                
                <div class="results-list" id="results-list-box"></div>
            </div>
        </div>
    </div>

    <script>
        const map = L.map('map', { 
            zoomControl: false, 
            attributionControl: false, 
            preferCanvas: true 
        }).setView([__LAT__, __LON__], 14);

        window.addEventListener('resize', function() {
            if (map) map.invalidateSize();
        });
        if (window.ResizeObserver) {
            new ResizeObserver(function() {
                if (map) map.invalidateSize();
            }).observe(document.getElementById('map-container'));
        }

        window.toggleWorkspacePanel = function(event) {
            if (event) event.stopPropagation();
            const panel = document.getElementById('scan-results-panel');
            const toggleBtn = document.getElementById('workspace-toggle-btn');
            const isCollapsed = panel.classList.toggle('collapsed');
            localStorage.setItem('workspace_collapsed', isCollapsed ? 'true' : 'false');
            if (toggleBtn) {
                toggleBtn.innerHTML = isCollapsed ? '+' : '&minus;';
                toggleBtn.title = isCollapsed ? 'Expand Workspace' : 'Collapse Workspace';
            }
            setTimeout(function() { if (map) map.invalidateSize(); }, 300);
        };

        window.toggleConfigSection = function(headlineEl) {
            const parent = headlineEl.closest('.config-block-wrapper');
            if (parent) {
                parent.classList.toggle('section-collapsed');
            }
        };

        const savedWsState = localStorage.getItem('workspace_collapsed');
        if (savedWsState === 'true') {
            const panel = document.getElementById('scan-results-panel');
            if (panel) {
                panel.classList.add('collapsed');
                const toggleBtn = document.getElementById('workspace-toggle-btn');
                if (toggleBtn) {
                    toggleBtn.innerText = '+';
                    toggleBtn.title = 'Expand Workspace';
                }
            }
        }

        let layerMeta = __LAYER_META_JSON__;
        let targetConfig = __TARGET_CONFIG_JSON__;
        let radiusConfig = __RADIUS_CONFIG_JSON__;
        let pts = __GEOJSON__;
        let clusters = {}; 

        // Explicit loading engine toggle mapping
        if (__SHOW_LOADING__) {
            document.getElementById('map-loading-overlay').style.display = 'flex';
        }

        const basemaps = {
            osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { 
                maxZoom: 19,
                attribution: '&copy; OpenStreetMap contributors' 
            }),
            satellite: L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', { 
                maxZoom: 20,
                attribution: '&copy; Google' 
            }),
            carto: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', { 
                maxZoom: 16,
                attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ' 
            })
        };

        basemaps[(localStorage.getItem('ts_persistent_basemap') || 'osm')].addTo(map);
        
        function switchActiveBasemap(targetKey) {
            Object.keys(basemaps).forEach(k => { if(map.hasLayer(basemaps[k])) map.removeLayer(basemaps[k]); });
            basemaps[targetKey].addTo(map); localStorage.setItem('ts_persistent_basemap', targetKey);
        }

        let labelsActive = localStorage.getItem('ts_persistent_labels') !== 'false';
        document.getElementById('label-toggle-chk').checked = labelsActive;
        if (!labelsActive) document.getElementById('map').classList.add('hide-labels');
        
        function toggleLabelsMatrix(isShown) {
            if (isShown) document.getElementById('map').classList.remove('hide-labels');
            else document.getElementById('map').classList.add('hide-labels');
            localStorage.setItem('ts_persistent_labels', isShown);
        }

        let radiusCircle = null;
        function renderRadiusCircleBounds() {
            if (radiusCircle) map.removeLayer(radiusCircle);
            radiusCircle = L.circle([__LAT__, __LON__], {
                radius: __RADIUS__, color: radiusConfig.color, weight: parseFloat(radiusConfig.weight),
                fillColor: radiusConfig.color, fillOpacity: parseFloat(radiusConfig.fill_opacity)
            }).addTo(map);
        }

        let centerMarker = null;
        function renderTargetCenterIcon() {
            if (centerMarker) map.removeLayer(centerMarker);
            const d = targetConfig.size; const c = targetConfig.color;
            const htmlElement = targetConfig.style === "star" 
                ? `<div style="background-color: ${c}; color: #ffffff; width: ${d}px; height: ${d}px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: ${d*0.5}px; border: 2px solid #ffffff; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">&#9733;</div>`
                : `<div style="background-color: ${c}; width: ${d}px; height: ${d}px; border-radius: 50%; border: 3px solid #ffffff; box-shadow: 0 2px 6px rgba(0,0,0,0.4);"></div>`;
            
            centerMarker = L.marker([__LAT__, __LON__], { 
                icon: L.divIcon({ className: 'custom-center-icon', html: htmlElement, iconSize: [d, d], iconAnchor: [d/2, d/2] }), zIndexOffset: 999999 
            }).addTo(map);
        }

        const generateMarkerElement = (color, styleMode, sizeDimension) => {
            const d = parseInt(sizeDimension);
            if (styleMode === "pin") {
                return L.divIcon({ 
                    html: `<div class="custom-pin-container"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${d*1.3}" height="${d*1.3}"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="${color}" stroke="#ffffff" stroke-width="1.5"/></svg></div>`, 
                    className: '', iconSize: [d*1.3, d*1.3], iconAnchor: [d*0.65, d*1.3] 
                });
            } else if (styleMode === "modern-pin") {
                const w = d * 1.5;
                const h = d * 2.2;
                // Core Update: Removed white inner dot matrix core, added flat black pin stalk with custom drop-shadow filter styling
                const customSvg = `
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 60" width="${w}" height="${h}">
                    <defs>
                        <filter id="shadowFilter" x="-40%" y="-40%" width="180%" height="180%">
                            <feDropShadow dx="0" dy="5" stdDeviation="3.5" flood-color="#000000" flood-opacity="0.4"/>
                        </filter>
                    </defs>
                    <g filter="url(#shadowFilter)">
                        <path d="M20 20 L20 54" stroke="#000000" stroke-width="3.5" stroke-linecap="round"/>
                        <circle cx="20" cy="20" r="14" fill="${color}" stroke="#000000" stroke-width="1.5" />
                    </g>
                </svg>`;
                return L.divIcon({
                    html: `<div style="transform: translate(-50%, -88%); width: ${w}px; height: ${h}px;">${customSvg}</div>`,
                    className: '', iconSize: [w, h], iconAnchor: [0, 0]
                });
            }
            return L.divIcon({ 
                html: `<div style="background-color: ${color}; width: ${d}px; height: ${d}px; border-radius: 50%; border: 1.5px solid #ffffff; box-shadow: 0 1px 4px rgba(0,0,0,0.2);"></div>`, 
                className: '', iconSize: [d, d], iconAnchor: [d/2, d/2] 
            });
        };

        const layerGroupsRef = {}; const categoryMap = {};

        function compileLayersAndRenderPoints() {
            Object.keys(layerGroupsRef).forEach(k => { map.removeLayer(layerGroupsRef[k]); delete layerGroupsRef[k]; });
            Object.keys(categoryMap).forEach(k => delete categoryMap[k]);
            
            pts.forEach(p => {
                const layerKey = p.type || 'Unclassified';
                if (!categoryMap[layerKey]) categoryMap[layerKey] = []; categoryMap[layerKey].push(p);
            });

            Object.keys(categoryMap).forEach(key => {
                layerGroupsRef[key] = L.layerGroup().addTo(map);
                const meta = layerMeta[key] || { color: "#003366", style: "dots", size: 12 };
                
                categoryMap[key].forEach(p => {
                    if (p.visible === false) return;
                    const marker = L.marker([p.lat, p.lon], { icon: generateMarkerElement(meta.color, meta.style, meta.size) })
                                    .bindPopup(`<b>${p.name}</b><br><span style="color:#888780;font-size:9px;">${p.type}</span>`);
                    if (p.name && p.name !== 'Unknown') {
                        marker.bindTooltip(p.name, { permanent: true, direction: 'top', offset: [0, -10], className: 'poi-text-label' });
                    }
                    marker.addTo(layerGroupsRef[key]);
                });
            });
        }

        window.openClusterModalWindow = function() {
            const container = document.getElementById('cluster-checkbox-target-mount');
            container.innerHTML = '';
            const layers = Object.keys(categoryMap);
            
            if(layers.length === 0) {
                container.innerHTML = '<div style="font-size:9px; padding:4px; color:#888780;">No active layers to compile.</div>';
            } else {
                layers.forEach(lyr => {
                    container.innerHTML += `
                        <div class="cluster-selection-row">
                            <input type="checkbox" class="cluster-matrix-select-target" value="${lyr}" style="accent-color:#003366;">
                            <span>${lyr} (${categoryMap[lyr].length})</span>
                        </div>
                    `;
                });
            }
            document.getElementById('cluster-modal-overlay').classList.add('active');
        };

        window.closeClusterModalWindow = function() {
            document.getElementById('cluster-modal-overlay').classList.remove('active');
            document.getElementById('new-cluster-name-input').value = '';
        };

        window.commitStructuralLayerCluster = function() {
            const titleInput = document.getElementById('new-cluster-name-input').value.trim();
            if (!titleInput) { alert('Cluster designation namespace required.'); return; }
            
            const selectedCheckboxes = document.querySelectorAll('.cluster-matrix-select-target:checked');
            const layerKeys = Array.from(selectedCheckboxes).map(cb => cb.value);
            
            if (layerKeys.length === 0) { alert('Select at least 1 layer entry.'); return; }
            
            clusters[titleInput] = layerKeys;
            closeClusterModalWindow();
            rebuildSidebarControlLayout();
        };

        window.destroyClusterGroupReference = function(clusterId) {
            delete clusters[clusterId];
            rebuildSidebarControlLayout();
        };

        window.toggleClusterGroupVisibility = function(clusterId, currentlyVisible) {
            const targetedLayers = clusters[clusterId] || [];
            pts.forEach(p => {
                if (targetedLayers.includes(p.type)) p.visible = !currentlyVisible;
            });
            compileLayersAndRenderPoints();
            rebuildSidebarControlLayout();
        };

        // Core Feature Update: Intercept and distribute property matrices across cluster layers dynamically
        window.batchStyleGroupCluster = function(clusterId, property, value) {
            const targetedLayers = clusters[clusterId] || [];
            targetedLayers.forEach(layerKey => {
                if (!layerMeta[layerKey]) layerMeta[layerKey] = {};
                layerMeta[layerKey][property] = property === 'size' ? parseInt(value) : value;
            });
            compileLayersAndRenderPoints();
            rebuildSidebarControlLayout();
        };

        window.patchGlobalMarkerStyle = function(v) { Object.keys(layerMeta).forEach(k => layerMeta[k].style = v); compileLayersAndRenderPoints(); };
        window.patchGlobalMarkerSize = function(v) { Object.keys(layerMeta).forEach(k => layerMeta[k].size = parseInt(v)); compileLayersAndRenderPoints(); };
        window.patchGlobalMarkerColor = function(v) { Object.keys(layerMeta).forEach(k => layerMeta[k].color = v); compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); };
        window.patchTargetCenterConfig = function(key, val) { targetConfig[key] = val; renderTargetCenterIcon(); };
        window.patchRadiusLayerConfig = function(key, val) { radiusConfig[key] = val; renderRadiusCircleBounds(); };
        window.triggerLayerUpdate = function(layerKey, property, value) { if (!layerMeta[layerKey]) layerMeta[layerKey] = {}; layerMeta[layerKey][property] = property === 'size' ? parseInt(value) : value; compileLayersAndRenderPoints(); };

        function rebuildSidebarControlLayout() {
            const listBox = document.getElementById('results-list-box');
            document.getElementById('results-count').innerText = pts.length;
            if (pts.length === 0) { listBox.innerHTML = "<div style='font-size:9px; padding:12px; color:#888780;'>No items mapped.</div>"; return; }

            let htmlPayload = '';
            const trashSvg = `<svg viewBox="0 0 24 24"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>`;
            const eyeSvg = `<svg viewBox="0 0 24 24"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>`;
            const editSvg = `<svg viewBox="0 0 24 24"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a.996.996 0 0 0 0-1.41l-2.34-2.34a.996.996 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>`;

            // Render Operational Groups with Dynamic Batch Layout Styling Controls Panel Modals
            Object.keys(clusters).forEach(clusterName => {
                const assignedLayers = clusters[clusterName] || [];
                let aggregatedCount = 0;
                let groupIsVisible = false;

                assignedLayers.forEach(lKey => {
                    if (categoryMap[lKey]) {
                        aggregatedCount += categoryMap[lKey].length;
                        if (categoryMap[lKey].some(p => p.visible !== false)) groupIsVisible = true;
                    }
                });

                htmlPayload += `
                    <div class="group-cluster-block" id="cluster-block-${clusterName}">
                        <div class="group-cluster-header">
                            <div class="group-cluster-title" onclick="toggleAccordionCollapse('cluster-items-${clusterName}')">
                                <span style="color:#C9AB4C;">&#9889;</span>
                                <span>${clusterName} <span style="font-weight:500; font-size:8px; opacity:0.75;">(${aggregatedCount} PINS)</span></span>
                            </div>
                            <div style="display:flex; align-items:center; gap:2px;">
                                <a class="action-icon-trigger" title="Hide/Show Group" onclick="toggleClusterGroupVisibility('${clusterName}', ${groupIsVisible})">${eyeSvg}</a>
                                <a class="action-icon-trigger delete-btn" title="Dissolve Group" onclick="destroyClusterGroupReference('${clusterName}')">${trashSvg}</a>
                                <span id="chevron-cluster-items-${clusterName}" onclick="toggleAccordionCollapse('cluster-items-${clusterName}')" style="font-size: 8px; color:#003366; margin-left:4px; cursor:pointer;">&#9660;</span>
                            </div>
                        </div>
                        
                        <div class="config-block-wrapper" style="background: #e2e8f0; border-bottom: 1px solid rgba(0,51,102,0.15);">
                            <div class="config-headline" style="font-size:7.5px; opacity:0.8;">Batch Group Style Controller</div>
                            <div class="config-flex-row">
                                <select onchange="batchStyleGroupCluster('${clusterName}', 'style', this.value)">
                                    <option value="dots">Dots</option>
                                    <option value="pin">Pin</option>
                                    <option value="modern-pin">Modern Pin</option>
                                </select>
                                <input type="range" min="10" max="40" value="12" class="slider-control-element" oninput="batchStyleGroupCluster('${clusterName}', 'size', this.value)">
                                <input type="color" value="#003366" onchange="batchStyleGroupCluster('${clusterName}', 'color', this.value)">
                            </div>
                        </div>

                        <div class="layer-category-items collapsed" id="items-cluster-items-${clusterName}" style="padding-left: 8px; background: rgba(0,0,0,0.02);">
                `;

                assignedLayers.forEach(catName => {
                    if(!categoryMap[catName]) return;
                    const meta = layerMeta[catName] || { color: "#003366", style: "dots", size: 12 };
                    const layerPts = categoryMap[catName] || [];
                    const isLayerVisible = layerPts.some(p => p.visible !== false);

                    htmlPayload += injectLayerItemDOMElements(catName, meta, layerPts, isLayerVisible, editSvg, eyeSvg, trashSvg);
                });

                htmlPayload += '</div></div>';
            });

            // Cleanly loop trace remaining loose data sets outside explicit configurations
            Object.keys(categoryMap).forEach(catName => {
                let insideClusterGroup = false;
                Object.values(clusters).forEach(layerArr => { if(layerArr.includes(catName)) insideClusterGroup = true; });
                if (insideClusterGroup) return;

                const meta = layerMeta[catName] || { color: "#003366", style: "dots", size: 12 };
                const layerPts = categoryMap[catName] || [];
                const isLayerVisible = layerPts.some(p => p.visible !== false);

                htmlPayload += `
                    <div class="layer-category-block" id="cat-block-${catName}">
                `;
                htmlPayload += injectLayerItemDOMElements(catName, meta, layerPts, isLayerVisible, editSvg, eyeSvg, trashSvg);
                htmlPayload += '</div>';
            });

            listBox.innerHTML = htmlPayload;
        }

        function injectLayerItemDOMElements(catName, meta, layerPts, isLayerVisible, editSvg, eyeSvg, trashSvg) {
            let chunk = `
                <div class="layer-category-header">
                    <div class="layer-header-left" onclick="toggleAccordionCollapse('${catName}')">
                        <span class="color-dot" style="background-color: ${meta.color};"></span>
                        <span style="font-weight:700;">${catName} <span style="color:#C9AB4C; font-size:8px;">(${layerPts.length})</span></span>
                    </div>
                    <div style="display:flex; align-items:center; gap:1px;">
                        <a class="action-icon-trigger" title="Rename" onclick="promptRenameLayer('${catName}')">${editSvg}</a>
                        <a class="action-icon-trigger" title="Hide/Show" onclick="toggleLayerWorkspaceVisibility('${catName}', ${isLayerVisible})">${eyeSvg}</a>
                        <a class="action-icon-trigger delete-btn" title="Delete" onclick="triggerLayerDeletion('${catName}')">${trashSvg}</a>
                        <span id="chevron-${catName}" onclick="toggleAccordionCollapse('${catName}')" style="font-size: 8px; color:#C9AB4C; margin-left:4px; cursor:pointer;">&#9660;</span>
                    </div>
                </div>
                <div class="config-block-wrapper" style="background:#ffffff; border-bottom:1px dashed rgba(0,51,102,0.05);">
                    <div class="config-flex-row">
                        <select onchange="triggerLayerUpdate('${catName}', 'style', this.value)">
                            <option value="dots" ${meta.style==='dots'?'selected':''}>Dots</option>
                            <option value="pin" ${meta.style==='pin'?'selected':''}>Pin</option>
                            <option value="modern-pin" ${meta.style==='modern-pin'?'selected':''}>Modern Drop-Pin</option>
                        </select>
                        <input type="range" min="10" max="40" value="${meta.size}" class="slider-control-element" oninput="triggerLayerUpdate('${catName}', 'size', this.value)">
                        <input type="color" value="${meta.color}" onchange="triggerLayerUpdate('${catName}', 'color', this.value); rebuildSidebarControlLayout();">
                    </div>
                </div>
                <div class="layer-category-items collapsed" id="items-${catName}">
            `;
            layerPts.forEach(p => {
                const itemVisible = p.visible !== false;
                chunk += `
                <div class="results-item" id="res-item-${p.uid}" style="${itemVisible ? '' : 'opacity:0.4;'}">
                    <div style="flex-grow:1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${p.name || 'Unknown'}" onclick="map.flyTo([${p.lat}, ${p.lon}], 17);">
                        ${p.name || 'Unknown'}
                    </div>
                    <div style="display:flex; align-items:center; gap:1px;">
                        <a class="action-icon-trigger" onclick="promptRenamePoi(${p.uid}, '${p.name}')">${editSvg}</a>
                        <a class="action-icon-trigger" onclick="togglePoiVisibility(${p.uid})">${eyeSvg}</a>
                        <a class="action-icon-trigger delete-btn" onclick="removePoiInstance(${p.uid}, '${catName}')">${trashSvg}</a>
                    </div>
                </div>`;
            });
            chunk += '</div>';
            return chunk;
        }

        window.toggleAccordionCollapse = function(catKey) {
            const panel = document.getElementById('items-' + catKey); const chev = document.getElementById('chevron-' + catKey);
            if(panel) { panel.classList.toggle('collapsed'); chev.innerHTML = panel.classList.contains('collapsed') ? '&#9660;' : '&#9650;'; }
        };

        window.togglePoiVisibility = function(uid) { const p = pts.find(item => item.uid === uid); if (p) { p.visible = (p.visible === false); compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); } };
        window.promptRenamePoi = function(uid, oldName) { const newName = prompt("Rename asset description Name:", oldName); if (newName && newName.trim() !== "") { const p = pts.find(item => item.uid === uid); if (p) { p.name = newName; compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); } } };
        window.removePoiInstance = function(uid, catKey) { pts = pts.filter(item => item.uid !== uid); compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); };
        window.toggleLayerWorkspaceVisibility = function(catKey, currentlyVisible) { pts.forEach(p => { if (p.type === catKey) p.visible = !currentlyVisible; }); compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); };

        window.promptRenameLayer = function(oldKey) {
            const newKey = prompt("Rename layer designation path description:", oldKey);
            if (newKey && newKey.trim() !== "" && newKey !== oldKey) {
                pts.forEach(p => { if (p.type === oldKey) p.type = newKey; });
                if (layerMeta[oldKey]) { layerMeta[newKey] = layerMeta[oldKey]; delete layerMeta[oldKey]; }
                
                Object.keys(clusters).forEach(cName => {
                    clusters[cName] = clusters[cName].map(item => item === oldKey ? newKey : item);
                });
                compileLayersAndRenderPoints(); rebuildSidebarControlLayout();
            }
        };

        window.triggerLayerDeletion = function(catKey) {
            if (confirm(`Remove entire layer cluster: "${catKey}"?`)) { 
                pts = pts.filter(p => p.type !== catKey); 
                delete layerMeta[catKey]; 
                Object.keys(clusters).forEach(cName => { clusters[cName] = clusters[cName].filter(item => item !== catKey); });
                compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); 
            }
        };

        map.on('contextmenu', function(e) {
            const lat = e.latlng.lat; const lng = e.latlng.lng;
            const menuHtml = `
                <div style="font-family: Montserrat, sans-serif; font-size: 10px; color: #003366; min-width: 140px; background:#fff; padding:4px;">
                    <div style="font-weight: 800; border-bottom: 1px solid #C9AB4C; padding-bottom: 4px; margin-bottom: 6px; letter-spacing: 0.5px;">MAP OPTIONS</div>
                    <div style="padding: 5px 2px; cursor: pointer; font-weight: 700;" onclick="navigator.clipboard.writeText('${lat.toFixed(5)}, ${lng.toFixed(5)}'); map.closePopup();">Copy Coordinates</div>
                    <div style="padding: 5px 2px; cursor: pointer; font-weight: 700;" onclick="window.open('https://www.google.com/maps/search/?api=1&query=${lat},${lng}', '_blank'); map.closePopup();">Open in Google Maps</div>
                    <div style="padding: 5px 2px; cursor: pointer; font-weight: 700;" onclick="window.open('https://www.google.com/maps?layer=c&cbll=${lat},${lng}', '_blank'); map.closePopup();">Open in Streetview</div>
                </div>
            `;
            L.popup().setLatLng(e.latlng).setContent(menuHtml).openOn(map);
        });

        renderTargetCenterIcon(); renderRadiusCircleBounds(); compileLayersAndRenderPoints(); rebuildSidebarControlLayout();

        if (pts.length > 0 && !__IS_STALE__) {
            const validPts = pts.filter(p => p.visible !== false);
            if (validPts.length > 0) { map.fitBounds(L.featureGroup([L.marker([__LAT__, __LON__]), ...validPts.map(p => L.marker([p.lat, p.lon]))]).getBounds().pad(0.05)); }
        }
    </script>
</body>
</html>
"""

leaflet_html = (leaflet_template
                .replace("__LAT__", str(render_lat))
                .replace("__LON__", str(render_lon))
                .replace("__RADIUS__", str(radius_val))
                .replace("__IS_STALE__", is_stale)
                .replace("__SHOW_LOADING__", show_loading)
                .replace("__GLOBAL_MARKER_SIZE__", str(st.session_state.global_marker_size))
                .replace("__GLOBAL_MARKER_COLOR__", str(st.session_state.global_marker_color))
                .replace("__TARGET_CONFIG_JSON__", target_config_json)
                .replace("__RADIUS_CONFIG_JSON__", radius_config_json)
                .replace("__LAYER_META_JSON__", layer_meta_json)
                .replace("__GEOJSON__", geojson_str))

st.components.v1.html(leaflet_html, height=850, scrolling=False)
