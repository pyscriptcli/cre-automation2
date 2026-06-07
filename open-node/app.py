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
# GOOGLE MY MAPS SPECIFICATION SIDEBAR DESIGN OVERRIDE PIPELINE
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Montserrat:wght@700;800&display=swap');

        /* Hard Light Theme Enforcements matching Google My Maps baselines */
        :root, [data-theme="light"], [data-theme="dark"] {
            --brand-midnight: #202124 !important; /* Google Dark Charcoal text color */
            --brand-blue: #1a73e8 !important;     /* Google Maps Primary Accent Blue */
            --white-clean: #ffffff !important;
            --bg-offwhite: #ffffff !important;
            --text-muted: #5f6368 !important;
            --soft-shadow: 0 1px 3px 0 rgba(60,64,67,0.3), 0 4px 8px 3px rgba(60,64,67,0.15) !important;
            
            --background-color: #ffffff !important;
            --secondary-background-color: #ffffff !important;
            --text-color: #202124 !important;
            --primary-color: #1a73e8 !important;
        }

        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: #ffffff !important;
            color: #202124 !important;
            font-family: 'Roboto', sans-serif !important;
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
        # PRODUCTION DIRECTIVE: GOOGLE MY MAPS SPEC SIDEBAR WIDTH CONTROLLER
        # =====================================================================
        # Baguhin ang 280px (width, min-width, max-width) sa ibaba kung nais
        # na ayusin ang eksaktong laki ng panel batay sa iyong viewport metrics.
        # ---------------------------------------------------------------------
        [data-testid="stSidebar"] {
            position: fixed !important;
            top: 0px !important;
            left: 0px !important;
            height: 100vh !important;
            width: 280px !important;
            min-width: 280px !important;
            max-width: 280px !important;
            background-color: #ffffff !important;
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
            border: none !important;
            border-right: 1px solid #e0e0e0 !important;
            border-radius: 0px !important; /* Sharp corners exactly like Google My Maps */
            box-shadow: var(--soft-shadow) !important;
            z-index: 999999 !important;
            overflow: hidden !important;
        }

        [data-testid="stSidebarUserContent"] {
            padding: 0px !important; /* Remove internal default spacing boundaries */
            height: 100% !important;
            overflow-y: auto !important;
            scrollbar-width: none !important;
        }
        [data-testid="stSidebarUserContent"]::-webkit-scrollbar { display: none !important; }

        /* Google My Maps Headings Style Override Block */
        .brand-title { 
            font-family: 'Roboto', sans-serif !important; 
            font-weight: 400 !important;
            color: #202124 !important; 
            font-size: 18px !important; 
            text-align: left !important;
            padding: 16px 20px 8px 20px !important;
            margin-bottom: 0px !important;
            border-bottom: none !important;
        }

        /* Flatten and strip the default accordion frames entirely to reveal flat maps trees */
        [data-testid="stSidebar"] .st-expander { 
            border: none !important; 
            background-color: transparent !important; 
            box-shadow: none !important;
            margin-bottom: 0px !important; 
            border-radius: 0px !important;
        }
        
        [data-testid="stSidebar"] .st-expander summary {
            padding: 6px 20px !important;
            background-color: transparent !important;
            color: #1a73e8 !important; /* Blue clickable category headers */
            font-size: 11px !important;
            font-weight: 500 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }
        [data-testid="stSidebar"] .st-expander summary:hover {
            background-color: #f1f3f4 !important;
        }

        div[data-testid="stExpander"] fieldset {
            padding: 2px 24px !important; /* Google sub-layer nested listing look indentation */
        }

        /* Indented Checkbox Row Component Adjustments */
        div.stCheckbox {
            margin-bottom: 2px !important;
            padding: 3px 0 !important;
        }
        
        .stCheckbox label p { 
            font-size: 12px !important; 
            font-family: 'Roboto', sans-serif !important;
            font-weight: 400 !important; 
            color: #5f6368 !important; /* Flat charcoal tracking font rules */
        }

        /* Checkbox Box Sizing & Style Alignment rules matching Google vector fields */
        div[data-testid="stCheckbox"] div[role="checkbox"] {
            border-radius: 2px !important;
            border-color: #757575 !important;
            width: 14px !important;
            height: 14px !important;
        }
        div[data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"] {
            background-color: #1a73e8 !important;
            border-color: #1a73e8 !important;
        }

        /* Action triggers interface buttons styling passes */
        div.stButton > button[kind="secondary"] { 
            background-color: #1a73e8 !important; 
            border: none !important; 
            border-radius: 4px !important; 
            width: calc(100% - 40px) !important; 
            margin: 12px 20px !important;
            padding: 8px !important; 
            box-shadow: none !important;
            font-family: 'Roboto', sans-serif !important;
        }
        div.stButton > button[kind="secondary"]:hover { background-color: #1557b0 !important; }
        div.stButton > button[kind="secondary"] p { font-size: 12px !important; font-weight: 500 !important; text-transform: none !important; letter-spacing: 0px !important; }

        /* Coordinate system text fields structure modifications */
        div.stTextInput {
            padding: 0 20px !important;
            margin-bottom: 8px !important;
        }
        div.stNumberInput {
            padding: 0 20px !important;
            margin-bottom: 12px !important;
        }

        /* Native framework design element purging */
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] { display: none !important; }
        [data-testid="stHeader"], header, #stDecoration { display: none !important; }
        iframe { height: 100vh !important; width: 100vw !important; border: none !important; display: block !important; }
        div[data-baseweb="input"] { background-color: #f1f3f4 !important; border: none !important; border-radius: 4px !important; padding: 4px 8px !important; }

        /* Action link button row styling adjustments at the footer block */
        div.stButton > button[kind="primary"] { background: transparent !important; border: none !important; padding: 4px 20px !important; text-align: left !important; width: 100% !important; }
        div.stButton > button[kind="primary"]:hover { background-color: #f1f3f4 !important; }
        div.stButton > button[kind="primary"] p { color: #d93025 !important; font-size: 11px !important; font-weight: 500; }
    </style>
""", unsafe_allow_html=True)

def main():
    # 1. Execute Sidebar Controller code arrays cleanly within Google spec layout
    lat, lon, radius = render_unified_dashboard_sidebar()

    # 2. Render flat aspect map layers across the entire frame canvas matrix
    render_leaflet_component_iframe(
        lat=lat, 
        lon=lon, 
        radius=radius, 
        pts_active=st.session_state.scanned_records
    )

if __name__ == "__main__":
    main()
