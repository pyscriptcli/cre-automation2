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

# Initialize parameters
initialize_session_states()

# -----------------------------------------------------------------------------
# GOOGLE MY MAPS ARCHITECTURAL VISUAL CLONE CLUSTER OVERRIDES
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

        /* Hard Light-Theme Configuration Profiles */
        :root, [data-theme="light"], [data-theme="dark"] {
            --brand-gmaps-blue: #1a73e8 !important;
            --brand-text-dark: #202124 !important;
            --brand-border-gray: #dadce0 !important;
            --brand-text-muted: #5f6368 !important;
            --white-solid: #ffffff !important;
            --soft-gmaps-shadow: 0 1px 4px rgba(0, 0, 0, 0.3) !important;
            
            --background-color: #ffffff !important;
            --secondary-background-color: #ffffff !important;
            --text-color: #202124 !important;
            --primary-color: #1a73e8 !important;
        }

        /* Enforce absolute fluid full-viewport matrix boundaries */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: #ffffff !important;
            color: var(--brand-text-dark) !important;
            font-family: 'Roboto', Arial, sans-serif !important;
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
        # ADJUST SIDEBAR WIDTH HERE: Palitan ang 300px sa ibaba upang baguhin 
        # ang kabuuang lapad ng floating panel (e.g., 280px para sa mas compact, 
        # o 320px para sa mas malawak na layout). Siguraduhing pareho ang tatlong 
        # value (width, min-width, max-width) upang maiwasan ang flex layout distortion.
        # ---------------------------------------------------------------------
        [data-testid="stSidebar"] {
            position: fixed !important;
            top: 20px !important;
            left: 20px !important;
            height: auto !important;
            max-height: calc(100vh - 40px) !important;
            width: 300px !important;      /* <--- BAGUHIN ITO PARA SA LAPAD */
            min-width: 300px !important;  /* <--- IPANTAY DITO */
            max-width: 300px !important;  /* <--- IPANTAY DITO */
            background-color: var(--white-solid) !important;
            border: none !important;
            border-radius: 8px !important;
            box-shadow: var(--soft-gmaps-shadow) !important;
            z-index: 999999 !important;
            overflow: hidden !important;
            display: flex !important;
            flex-direction: column !important;
        }

        /* Scrape-out native wrapper spaces completely */
        [data-testid="stSidebarUserContent"] {
            padding: 0px !important;
            height: auto !important;
            overflow-y: auto !important;
            scrollbar-width: none !important;
        }
        [data-testid="stSidebarUserContent"]::-webkit-scrollbar { display: none !important; }

        /* Google My Maps Header Panel Block Structure */
        .brand-title { 
            font-family: 'Roboto', Arial, sans-serif !important;
            font-weight: 500 !important;
            font-style: normal !important;
            color: var(--white-solid) !important;
            background-color: var(--brand-gmaps-blue) !important;
            font-size: 16px !important;
            text-align: left !important;
            padding: 14px 16px !important;
            margin: 0px !important;
            border-bottom: none !important;
            letter-spacing: 0.2px !important;
        }

        /* Padding structure logic inject layer for entry form variables control components */
        div.stNumberInput, div.stTextInput, div.stCheckbox, div.stButton, [data-testid="stExpander"], div.stPopover {
            padding-left: 14px !important;
            padding-right: 14px !important;
        }

        div.stButton {
            margin-top: 10px !important;
            margin-bottom: 4px !important;
        }

        /* Re-engineering Expander layout architecture into minimal flat list structures */
        [data-testid="stExpander"] {
            border: none !important;
            background-color: transparent !important;
            box-shadow: none !important;
            margin-bottom: 0px !important;
            padding-left: 0px !important;
            padding-right: 0px !important;
            border-bottom: 1px solid var(--brand-border-gray) !important;
            border-radius: 0px !important;
        }
        
        [data-testid="stExpander"] summary {
            padding: 10px 16px !important;
            background-color: #f8fafc !important;
        }
        
        [data-testid="stExpander"] summary:hover {
            background-color: #f1f3f4 !important;
        }

        [data-testid="stExpander"] summary p {
            font-size: 12px !important;
            font-weight: 500 !important;
            color: var(--brand-text-dark) !important;
        }

        div[data-testid="stExpander"] fieldset {
            padding: 6px 16px !important;
            border: none !important;
        }

        /* Compaction layer inside layer items selection boxes */
        .stCheckbox label p {
            font-size: 11px !important;
            font-weight: 400 !important;
            color: #3c4043 !important;
            font-family: 'Roboto', Arial, sans-serif !important;
        }

        /* Material Input Border Styling Overrides */
        div[data-baseweb="input"] {
            background-color: transparent !important;
            border: none !important;
            border-bottom: 1px solid #ch748b !important;
            border-radius: 0px !important;
        }
        div[data-baseweb="input"]:focus-within {
            border-bottom: 2px solid var(--brand-gmaps-blue) !important;
        }

        /* Action triggers mapping control parameters adjustments */
        div.stButton > button[kind="secondary"], [data-testid="stPopover"] > button {
            background-color: var(--brand-gmaps-blue) !important;
            border: none !important;
            border-radius: 4px !important;
            padding: 8px 16px !important;
            box-shadow: none !important;
        }
        div.stButton > button[kind="secondary"]:hover, [data-testid="stPopover"] > button:hover {
            background-color: #1557b0 !important;
        }
        div.stButton > button[kind="secondary"] p, [data-testid="stPopover"] > button p {
            font-size: 11px !important;
            font-weight: 700 !important;
            letter-spacing: 0.3px !important;
        }

        /* Native element footprint scrubs */
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] { display: none !important; }
        [data-testid="stHeader"], header, #stDecoration { display: none !important; }
        iframe { height: 100vh !important; width: 100vw !important; border: none !important; display: block !important; }
    </style>
""", unsafe_allow_html=True)

def main():
    # 1. Pull parameter controls array out of the modified Google My Maps floating container
    lat, lon, radius = render_unified_dashboard_sidebar()

    # 2. Compile full viewport leaflet canvas frame
    render_leaflet_component_iframe(
        lat=lat, 
        lon=lon, 
        radius=radius, 
        pts_active=st.session_state.scanned_records
    )

if __name__ == "__main__":
    main()
