import os
import sys

# Core Environment Enforcer Block: Overcomes Streamlit Cloud folder mounting quirks
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import streamlit as st
from config import initialize_session_states
from sidebar import render_unified_dashboard_sidebar
from map_view import render_leaflet_component_iframe

# Initialize session parameters and default settings
initialize_session_states()

# --- PROGRAMMATIC LIGHT MODE LOCK (Must execute before st.set_page_config) ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\n")

# -----------------------------------------------------------------------------
# 1. HARD LIGHT-MODE ENFORCEMENT & HIGH-COMPACT FLOATING SIDEBAR ENGINE
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');

        /* Strict Light Theme Variable Injections: Overrides native dark styling rules completely */
        :root, [data-theme="light"], [data-theme="dark"] {
            --brand-midnight: #003366 !important;
            --brand-gold: #C9AB4C !important;
            --white-clean: #ffffff !important;
            --bg-offwhite: #f8fafc !important;
            --text-muted: #64748b !important;
            --soft-shadow: 0 4px 20px rgba(0, 51, 102, 0.12) !important;
            
            /* Streamlit specific base variables override block */
            --background-color: #ffffff !important;
            --secondary-background-color: #f8fafc !important;
            --text-color: #003366 !important;
            --primary-color: #003366 !important;
        }

        /* Enforce absolute full-screen canvas baseline layouts */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: #ffffff !important;
            color: #003366 !important;
            margin: 0px !important;
            padding: 0px !important;
            width: 100vw !important;
            height: 100vh !important;
            overflow: hidden !important;
        }

        [data-testid="stMain"] {
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            z-index: 1 !important;
        }

        .block-container, [data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"], .stElementContainer {
            padding: 0px !important;
            margin: 0px !important;
            max-width: 100vw !important;
            max-height: 100vh !important;
            height: 100vh !important;
        }

        # =====================================================================
        # PRODUCTION DIRECTIVE: SIDEBAR SIZE CONFIGURATION CONTROLLER
        # =====================================================================
        # ADJUST SIDEBAR WIDTH HERE: Palitan ang 240px sa ibaba upang baguhin 
        # ang kabuuang lapad ng floating panel (e.g., 220px para sa mas compact, 
        # o 280px para sa mas malawak na layout). Siguraduhing pareho ang tatlong 
        # value (width, min-width, max-width) upang maiwasan ang flex layout distortion.
        # ---------------------------------------------------------------------
        [data-testid="stSidebar"] {
            position: fixed !important;
            top: 10px !important;
            left: 10px !important;
            height: calc(100vh - 20px) !important;
            width: 240px !important;      /* <--- BAGUHIN ITO PARA SA LAPAD */
            min-width: 240px !important;  /* <--- IPANTAY DITO */
            max-width: 240px !important;  /* <--- IPANTAY DITO */
            background-color: rgba(255, 255, 255, 0.94) !important;
            backdrop-filter: blur(16px) !important;
            -webkit-backdrop-filter: blur(16px) !important;
            border: 1px solid rgba(0, 51, 102, 0.12) !important;
            border-radius: 6px !important;
            box-shadow: var(--soft-shadow) !important;
            z-index: 999999 !important;
            transition: all 0.2s ease-in-out !important;
            overflow: hidden !important;
        }

        /* Strict padding compaction layer for input fields and expanders mapping tools */
        [data-testid="stSidebarUserContent"] {
            padding: 10px !important;
            height: 100% !important;
            overflow-y: auto !important;
            scrollbar-width: none !important;
        }
        [data-testid="stSidebarUserContent"]::-webkit-scrollbar {
            display: none !important;
        }

        /* Structural font density scaling blocks */
        .brand-title { 
            font-family: 'Montserrat', sans-serif !important; 
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
            font-style: normal !important; 
            color: var(--brand-midnight); 
            font-size: 16px !important; 
            text-align: center; 
            border-bottom: 2px solid var(--brand-gold); 
            padding-bottom: 4px !important; 
            margin-bottom: 10px !important; 
        }

        /* Compact spacing limits for text variables inputs and numeric spinners */
        div.stNumberInput, div.stTextInput, div.stCheckbox {
            margin-bottom: 4px !important;
        }
        
        .stTextInput cubic-bezier, .stNumberInput cubic-bezier {
            padding-top: 2px !important;
            padding-bottom: 2px !important;
        }

        [data-testid="stSidebar"] .st-expander { 
            border: 1px solid rgba(0, 51, 102, 0.08) !important; 
            background-color: #ffffff !important; 
            border-radius: 4px !important; 
            margin-bottom: 3px !important; 
        }

        div[data-testid="stExpander"] fieldset {
            padding: 4px 6px !important;
        }

        /* Native layout footprint scrubbing rules */
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] { display: none !important; }
        [data-testid="stHeader"], header, #stDecoration { display: none !important; }
        iframe { height: 100vh !important; width: 100vw !important; border: none !important; display: block !important; }

        /* Input field visualization parameter adjustments */
        div[data-baseweb="input"], div[data-baseweb="select"] { background-color: transparent !important; border: none !important; border-bottom: 1px solid rgba(201, 171, 76, 0.5) !important; border-radius: 0px !important; box-shadow: none !important; }
        div.stButton > button[kind="secondary"], [data-testid="stPopover"] > button { background-color: var(--brand-midnight) !important; border: 1px solid var(--brand-midnight) !important; border-radius: 3px !important; width: 100% !important; padding: 4px !important; box-shadow: 0 2px 6px rgba(0, 51, 102, 0.08) !important; }
        div.stButton > button[kind="secondary"]:hover, [data-testid="stPopover"] > button:hover { background-color: var(--brand-gold) !important; border-color: var(--brand-gold) !important; }
        div.stButton > button[kind="secondary"] p, [data-testid="stPopover"] > button p, [data-testid="stPopover"] > button div, div.stDownloadButton > button p { color: var(--white-clean) !important; font-weight: 700 !important; font-size: 9px !important; text-transform: uppercase !important; letter-spacing: 0.5px; }
        div.stDownloadButton > button { background-color: var(--brand-midnight) !important; border: none !important; border-radius: 3px !important; width: 100% !important; padding: 4px !important; }
        div.stDownloadButton > button:hover { background-color: var(--brand-gold) !important; }
        div.stButton > button[kind="primary"] { background: transparent !important; border: none !important; color: var(--text-muted) !important; padding: 0 !important; margin-top: 1px; }
        div.stButton > button[kind="primary"] p { color: var(--text-muted) !important; font-size: 8.5px !important; font-weight: 600; text-transform: uppercase; }
        
        /* Font scaling overrides for checkbox metrics text elements */
        .stCheckbox label p { font-size: 9px !important; font-weight: 600 !important; color: var(--brand-midnight) !important; }
    </style>
""", unsafe_allow_html=True)

def main():
    # 1. Mount sidebar parameter arrays directly inside compacted card dashboard panel wrapper
    lat, lon, radius = render_unified_dashboard_sidebar()

    # 2. Render absolute full screen leaflet map view matrix frame
    render_leaflet_component_iframe(
        lat=lat, 
        lon=lon, 
        radius=radius, 
        pts_active=st.session_state.scanned_records
    )

if __name__ == "__main__":
    main()
