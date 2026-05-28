import streamlit as st
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium

# =============================================================================
# [ PAGE CONFIGURATION & PRIME THEME INJECTION ]
# =============================================================================
st.set_page_config(page_title="PRIME Trade Area Scan", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        /* CORE BACKGROUND: Pure White */
        .stApp, .block-container {
            background-color: #FFFFFF !important;
        }
        
        /* RULE 1 FIX: TYPOGRAPHY EXCLUSION */
        h1, h2, h3, h4, h5, h6, p, label, span:not(.material-icons):not(.material-symbols-rounded) {
            color: #003366 !important;
            font-family: 'Inter', sans-serif !important;
        }
        
        /* Explicitly force Material Icons to keep their native font */
        .material-symbols-rounded, .material-icons, span.material-icons {
            font-family: 'Material Symbols Rounded', 'Material Icons' !important;
        }

        /* BUTTONS & POPOVERS: Midnight Blue -> Gold Hover */
        div.stButton > button, div[data-testid="stPopover"] > button {
            background-color: #003366 !important;
            color: #FFFFFF !important;
            border: 2px solid #003366 !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease-in-out;
            width: 100%;
        }
        div.stButton > button:hover, div[data-testid="stPopover"] > button:hover {
            background-color: #C9AB4C !important;
            color: #003366 !important;
            border-color: #C9AB4C !important;
        }

        /* RADIO BUTTONS (Workspace Switcher) */
        div[role="radiogroup"] > label {
            background-color: #F0F4F8 !important;
            padding: 10px 20px !important;
            border-radius: 8px !important;
        }
        div[role="radiogroup"] div[data-testid="stMarkdownContainer"] p {
            font-weight: bold !important;
        }

        /* ANNIHILATE SIDEBAR */
        [data-testid="stSidebar"], [data-testid="collapsedControl"] { 
            display: none !important; 
        }
        
        /* RULE 2 FIX: EDGE-TO-EDGE CANVAS WITH TOP CLEARANCE */
        .block-container {
            padding-top: 3rem !important;
            padding-bottom: 0rem !important;
            padding-left: 0rem !important;
            padding-right: 0rem !important;
            margin: 0px !important;
            max-width: 100% !important;
        }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# [ STATE INITIALIZATION ]
# =============================================================================
if "map_drawings" not in st.session_state:
    st.session_state.map_drawings = None

# =============================================================================
# [ TOP NAVIGATION MATRIX ]
# =============================================================================
# 1. Workspace Mode Switcher
st.radio(
    "Active Environment",
    options=["Map Workspace Mode", "Market Analytics Mode"],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# 2. Tools & Settings Popovers
col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 4])

with col1:
    with st.popover("⚙️ Map Edit"):
        st.write("Map styling and base layer toggles go here.")
with col2:
    with st.popover("🎯 Trade Area Scan"):
        st.write("POI extraction tags and radius sliders go here.")
with col3:
    with st.popover("👥 Demographics"):
        st.write("Population and density metrics go here.")
with col4:
    with st.popover("📊 Insights"):
        st.write("Generative AI market summaries go here.")

# =============================================================================
# [ SPATIAL ENGINE: FOLIUM + DRAW ]
# =============================================================================
# Initialize base map
m = folium.Map(location=[14.5995, 120.9842], zoom_start=14, tiles="CartoDB positron")

# Inject drawing tools
draw_options = Draw(
    export=False,
    position="topleft",
    draw_options={
        "polyline": True,
        "polygon": True,
        "rectangle": True,
        "circle": False, 
        "marker": True,
        "circlemarker": False
    },
    edit_options={"edit": True, "remove": True}
)
draw_options.add_to(m)

# Render giant map and bind to State
map_output = st_folium(
    m, 
    height=750, 
    use_container_width=True, 
    returned_objects=["all_drawings"]
)

# Persist drawings into backend memory
if map_output and "all_drawings" in map_output:
    st.session_state.map_drawings = map_output["all_drawings"]
