import streamlit as st
import urllib.parse
import re
import math

# -----------------------------------------------------------------------------
# 1. GRAPHICAL SYSTEM & EMBOSS THEME INJECTION (LIGHT MODE BASELINE)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TRADE AREA SCAN",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Implementation of specialized CSS to wrap widgets into high-contrast panels
st.markdown("""
    <style>
        /* Base Color System Configuration */
        :root {
            --navy: #001a3d;
            --white: #ffffff;
            --gold: #d4af37;
            --slate-light: #f4f6f9;
        }
        
        /* Main Workspace Area Adjustments */
        .block-container {
            padding: 0rem !important;
        }
        
        /* Sidebar System Architecture */
        [data-testid="stSidebar"] {
            background-color: var(--slate-light) !important;
            color: var(--navy) !important;
            border-right: 3px solid var(--navy) !important;
        }
        
        /* Container Card Layer Blocks */
        .custom-card {
            background-color: var(--white);
            border: 2px solid var(--navy);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 2px 2px 0px var(--navy);
        }
        
        /* Typography Rules */
        [data-testid="stSidebar"] label {
            color: var(--navy) !important;
            font-weight: bold !important;
            font-family: 'Arial', sans-serif !important;
            text-transform: uppercase;
            font-size: 11px !important;
            letter-spacing: 0.5px;
        }
        
        /* Hyperlink Clear Action Styling */
        .clear-link-btn {
            color: var(--navy) !important;
            text-decoration: underline !important;
            font-weight: bold !important;
            font-size: 11px !important;
            background: none !important;
            border: none !important;
            padding: 0 !important;
            cursor: pointer;
            float: right;
        }
        
        /* Unified Button Layout Specifications (White BG, Bold Navy Text) */
        div.stButton > button, div.stDownloadButton > button {
            background-color: var(--white) !important;
            color: var(--navy) !important;
            font-weight: 900 !important;
            text-transform: uppercase !important;
            border: 2px solid var(--navy) !important;
            border-radius: 4px !important;
            width: 100% !important;
            box-shadow: 2px 2px 0px var(--navy) !important;
            transition: all 0.15s ease-in-out !important;
        }
        
        div.stButton > button:hover, div.stDownloadButton > button:hover {
            background-color: var(--navy) !important;
            color: var(--white) !important;
            box-shadow: 2px 2px 0px var(--gold) !important;
            border-color: var(--navy) !important;
        }
        
        /* Expander Frame Enhancements */
        [data-testid="stSidebar"] .st-expander {
            border: 1px solid rgba(0, 26, 61, 0.2) !important;
            background-color: var(--white) !important;
            margin-bottom: 6px;
        }

        /* Edge-to-Edge Frame Control Layout */
        iframe {
            border: none !important;
            width: 100% !important;
            height: calc(100vh - 4px) !important;
        }
        
        .stDeployButton, footer, #stDecoration { display:none !important; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. DICTIONARY DEFINITIONS (OSM STRUCTURAL STRINGS)
# -----------------------------------------------------------------------------
POI_CONFIG = {
    "COMMERCIAL": [['Corporate Office', '"building"~"office|commercial",i'], ['IT/Tech Center', '"office"~"it|telecommunication",i'], ['Business Center', '"building"="commercial"'], ['Hospital', '"amenity"~"hospital|clinic",i'], ['Hotel', '"tourism"="hotel"']],
    "RETAIL": [['Mall/Department Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"supermarket|grocery",i'], ['Convenience Store', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"']],
    "FOOD AND BEVERAGES": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee Shop', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"']],
    "INDUSTRIAL & LOGISTICS": [
        ['Expressway Exits', '"highway"~"motorway_junction|toll_gantry",i'], 
        ['Ports & Terminals', '"industrial"="port"'], 
        ['Manufacturing Plants', '"industrial"~"factory|manufacturing|processing",i'],
        ['Cold Storage Facilities', '"warehouse"~"cold_store|cold_storage",i'],
        ['Industrial Parks/Estates', '"landuse"~"industrial|industrial_estate",i'],
        ['Warehouses & Depots', '"building"~"warehouse|depot",i']
    ]
}

ADVANCED_CONFIG = {
    "AMENITIES": [['ATM', '"amenity"="atm"'], ['Bank', '"amenity"="bank"']],
    "RETAIL_ADV": [['Beauty', '"shop"="beauty"'], ['Car', '"shop"="car"'], ['DIY/hardware', '"shop"~"hardware|doityourself",i']]
}

# Geofence Circle Boundary Calculation Math Module
def generate_kml_radius(lat, lon, radius_meters):
    kml_header = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Radius Scan</name><Placemark><Polygon><outerBoundaryIs><LinearRing><coordinates>'
    kml_footer = '</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></Document></kml>'
    points = []
    for i in range(37):
        angle = (i * 10) * math.pi / 180
        delta_lat = (radius_meters / 6371000) * math.cos(angle)
        delta_lon = (radius_meters / (6371000 * math.cos(lat * math.pi / 180))) * math.sin(angle)
        pt_lat = lat + (delta_lat * 180 / math.pi)
        pt_lon = lon + (delta_lon * 180 / math.pi)
        points.append(f"{pt_lon},{pt_lat},0")
    return kml_header + " ".join(points) + kml_footer

# Base Target Configuration Assignment
if 'target_url' not in st.session_state:
    st.session_state.target_url = "https://overpass-turbo.eu/?C=14.6465;121.0371;14"

# -----------------------------------------------------------------------------
# 3. CONTROL PANEL GRAPHICS (SIDEBAR COMPONENT ENGINE)
# -----------------------------------------------------------------------------
with st.sidebar:
    # Centered Header Panel Alignment
    st.markdown("<h2 style='color:var(--navy); text-align:center; font-family:Arial; font-weight:900; margin-top:10px; margin-bottom:20px; letter-spacing:1px;'>TRADE AREA SCAN</h2>", unsafe_allow_html=True)
    
    # CONTAINER 1: GEOGRAPHIC CONTROL PANEL CARD
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    
    # Title & Hyperlink layout execution
    col_lbl, col_lnk = st.columns([2, 1])
    with col_lbl:
        st.markdown("<span style='color:var(--navy); font-weight:900; font-size:12px;'>GEOGRAPHY</span>", unsafe_allow_html=True)
    with col_lnk:
        # Clear All Action execution handling via state verification loop reset
        if st.button("CLEAR ALL", key="action_clear_state", help="Uncheck all active selection parameters"):
            for session_key in list(st.session_state.keys()):
                if session_key.startswith("chk_"):
                    st.session_state[session_key] = False
            st.rerun()
            
    coords_input = st.text_input("Coordinates Target", value="14.6465, 121.0371", key="geo_coords_coord")
    radius_input = st.number_input("Scan Radius (Meters)", min_value=100, max_value=100000, value=1000, step=100, key="geo_radius_val")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Coordinate validation processing
    coord_match = re.match(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", coords_input)
    lat, lon = (coord_match.group(1), coord_match.group(2)) if coord_match else ("14.6465", "121.0371")

    # CONTAINER 2: SELECTION & POI TREE CARD
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.markdown("<div style='color:var(--navy); font-weight:900; font-size:12px; margin-bottom:10px;'>POI SELECTION LIBRARY</div>", unsafe_allow_html=True)
    
    search_term = st.text_input("Filter Options", "", key="search_query_filter").lower()
    
    chosen_tags = []

    # UI Core Loop Compilation
    for category, structural_items in POI_CONFIG.items():
        matched_items = [item for item in structural_items if search_term in item[0].lower()]
        if matched_items:
            with st.expander(category, expanded=(len(search_term) > 0)):
                for labels, tag_string in matched_items:
                    if st.checkbox(labels, key=f"chk_core_{category}_{labels}"):
                        chosen_tags.append(tag_string)

    # UI Advanced Loop Compilation
    for category, structural_items in ADVANCED_CONFIG.items():
        matched_items = [item for item in structural_items if search_term in item[0].lower()]
        if matched_items:
            with st.expander(f"ADV - {category}", expanded=(len(search_term) > 0)):
                for labels, tag_string in matched_items:
                    if st.checkbox(labels, key=f"chk_adv_{category}_{labels}"):
                        chosen_tags.append(tag_string)
    st.markdown('</div>', unsafe_allow_html=True)

    # ACTION FOOTER FRAME (DUAL COLUMN ACTION WORKSPACE)
    st.markdown("<br>", unsafe_allow_html=True)
    col_action_left, col_action_right = st.columns(2)
    
    with col_action_left:
        # Pre-calculate active KML text string streams to support instant download handshakes
        try:
            kml_payload = generate_kml_radius(float(lat), float(lon), radius_input)
        except ValueError:
            kml_payload = ""
            
        st.download_button(
            label="Export Radius",
            data=kml_payload,
            file_name=f"Radius_{lat}_{lon}_{radius_input}m.kml",
            mime="application/vnd.google-earth.kml+xml",
            use_container_width=True,
            key="btn_trigger_kml"
        )
        
    with col_action_right:
        if st.button("Scan Area", type="primary", use_container_width=True, key="btn_trigger_overpass"):
            if not chosen_tags:
                st.error("Select at least 1 filter layer.")
            else:
                # Direct generation of standard Overpass QL structural code scripts
                statement_blocks = "\n".join([f"  nwr[{tag}](around:{radius_input},{lat},{lon});" for tag in chosen_tags])
                compiled_overpass_ql = f"[out:json][timeout:120];\n(\n{statement_blocks}\n);\nout center;\n>;\nout skel qt;"
                encoded_ql = urllib.parse.quote(compiled_overpass_ql)
                
                # Append &R execution code string flag to drop code views automatically and maximize map estate
                st.session_state.target_url = f"https://overpass-turbo.eu/?Q={encoded_ql}&R"

# -----------------------------------------------------------------------------
# 4. VIEWPORT CANVAS RENDERING FRAME
# -----------------------------------------------------------------------------
st.components.v1.iframe(st.session_state.target_url)
