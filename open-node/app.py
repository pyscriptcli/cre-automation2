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

# -----------------------------------------------------------------------------
# HIGH-LEVEL FLOATING OVERLAY & FULL-SCREEN VIEWPORT INTERCEPT SYSTEM
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');

        :root {
            --brand-midnight: #003366 !important;
            --brand-gold: #C9AB4C !important;
            --white-clean: #ffffff !important;
            --bg-offwhite: #f8fafc !important;
            --soft-shadow: 0 8px 32px rgba(0, 51, 102, 0.15) !important;
        }

        /* Enforce absolute full-screen canvas mapping architecture */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: #ffffff !important;
            margin: 0px !important;
            padding: 0px !important;
            width: 100vw !important;
            height: 100vh !important;
            overflow: hidden !important;
        }

        /* Main view container configuration pass */
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

        /* Transform the default sidebar layout into a floating executive control panel */
        [data-testid="stSidebar"] {
            position: fixed !important;
            top: 15px !important;
            left: 15px !important;
            height: calc(100vh - 30px) !important;
            width: 290px !important;
            min-width: 290px !important;
            max-width: 290px !important;
            background-color: rgba(248, 250, 252, 0.92) !important; /* Elegant frost transparency */
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(0, 51, 102, 0.1) !important;
            border-radius: 8px !important;
            box-shadow: var(--soft-shadow) !important;
            z-index: 999999 !important; /* Enforce stacking index visibility over leaflet layers */
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            overflow: hidden !important;
        }

        /* Smooth scroll management wrapper for sidebar content matrices */
        [data-testid="stSidebarUserContent"] {
            padding: 18px !important;
            height: 100% !important;
            overflow-y: auto !important;
            scrollbar-width: none !important;
        }
        [data-testid="stSidebarUserContent"]::-webkit-scrollbar {
            display: none !important;
        }

        /* Clean framework footprint overrides */
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] { display: none !important; }
        [data-testid="stHeader"], header, #stDecoration { display: none !important; }
        iframe { height: 100vh !important; width: 100vw !important; border: none !important; display: block !important; }

        /* Branded custom sub-elements adjustments */
        div[data-baseweb="input"], div[data-baseweb="select"] { background-color: transparent !important; border: none !important; border-bottom: 1px solid rgba(201, 171, 76, 0.5) !important; border-radius: 0px !important; box-shadow: none !important; }
        div.stButton > button[kind="secondary"], [data-testid="stPopover"] > button { background-color: var(--brand-midnight) !important; border: 1px solid var(--brand-midnight) !important; border-radius: 4px !important; width: 100% !important; padding: 6px !important; box-shadow: 0 2px 8px rgba(0, 51, 102, 0.1) !important; }
        div.stButton > button[kind="secondary"]:hover, [data-testid="stPopover"] > button:hover { background-color: var(--brand-gold) !important; border-color: var(--brand-gold) !important; }
        div.stButton > button[kind="secondary"] p, [data-testid="stPopover"] > button p, [data-testid="stPopover"] > button div, div.stDownloadButton > button p { color: var(--white-clean) !important; font-weight: 700 !important; font-size: 9.5px !important; text-transform: uppercase !important; letter-spacing: 1px; }
        div.stDownloadButton > button { background-color: var(--brand-midnight) !important; border: none !important; border-radius: 4px !important; width: 100% !important; padding: 6px !important; }
        div.stDownloadButton > button:hover { background-color: var(--brand-gold) !important; }
        div.stButton > button[kind="primary"] { background: transparent !important; border: none !important; color: var(--text-muted) !important; padding: 0 !important; margin-top: 2px; }
        div.stButton > button[kind="primary"] p { color: var(--text-muted) !important; font-size: 9px !important; font-weight: 600; text-transform: uppercase; }
        [data-testid="stSidebar"] .st-expander { border: 1px solid rgba(0, 51, 102, 0.05) !important; background-color: #ffffff !important; border-radius: 4px !important; margin-bottom: 4px !important; }
        .stCheckbox { display: flex !important; align-items: center !important; margin-bottom: 2px !important; }
        .stCheckbox label { display: inline-flex !important; align-items: center !important; gap: 6px !important; }
        .stCheckbox label p { font-size: 10px !important; font-weight: 500; color: var(--brand-midnight) !important; }
        .brand-title { font-family: 'Cormorant Garamond', serif !important; font-style: italic; color: var(--brand-midnight); font-size: 28px; text-align: center; border-bottom: 1px solid var(--brand-gold); padding-bottom: 6px; margin-bottom: 14px; }
    </style>
""", unsafe_allow_html=True)

def main():
    # 1. Mount sidebar asset controllers and geoprocessing tasks directly inside floating element
    lat, lon, radius = render_unified_dashboard_sidebar()

    # 2. Compile and stretch map viewport components across the complete screen matrix
    render_leaflet_component_iframe(
        lat=lat, 
        lon=lon, 
        radius=radius, 
        pts_active=st.session_state.scanned_records
    )

if __name__ == "__main__":
    main()
