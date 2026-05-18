import streamlit as st
import urllib.parse
import re
import math

# -----------------------------------------------------------------------------
# 1. PREMIUM LIGHT MODE & GEOMETRIC PILL OVERRIDES
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TRADE AREA SCAN",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        :root {
            --navy-brand: #001a3d;
            --white-clean: #ffffff;
            --gold-accent: #d4af37;
            --border-gray: #e0e4ec;
        }
        
        /* Maximize primary viewport space */
        .block-container {
            padding: 0rem !important;
        }
        
        /* Clean Light Mode Sidebar Re-skinning */
        [data-testid="stSidebar"] {
            background-color: var(--white-clean) !important;
            color: var(--navy-brand) !important;
            border-right: 1px solid var(--border-gray) !important;
        }
        
        [data-testid="stSidebarUserContent"] {
            padding-top: 24px !important;
            padding-left: 16px !important;
            padding-right: 16px !important;
        }
        
        /* Upscaled & Centered Header Element */
        .sidebar-title {
            color: var(--navy-brand) !important;
            font-size: 26px !important;
            font-weight: 900 !important;
            letter-spacing: 1.5px !important;
            text-transform: uppercase !important;
            text-align: center !important;
            margin-top: 10px !important;
            margin-bottom: 5px !important;
            font-family: 'Arial', sans-serif !important;
        }
        
        [data-testid="stSidebar"] label p {
            color: var(--navy-brand) !important;
            font-weight: 700 !important;
            font-size: 11px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }
        
        /* Input Field Geometry Rounding */
        div[data-baseweb="input"], div[data-baseweb="select"], .stSelectbox, .stTextInput, .stNumberInput {
            border-radius: 8px !important;
        }
        
        div[data-baseweb="input"] {
            border: 1px solid var(--border-gray) !important;
        }
        
        div[data-baseweb="input"]:focus-within {
            border-color: var(--navy-brand) !important;
        }
        
        div[data-baseweb="select"] {
            border: 1px solid var(--border-gray) !important;
        }
        
        /* Pill Button Specifications */
        div.stButton > button, div.stDownloadButton > button {
            background-color: var(--navy-brand) !important;
            color: var(--white-clean) !important;
            font-weight: 700 !important;
            font-size: 11px !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
            border: 1px solid var(--navy-brand) !important;
            border-radius: 24px !important;
            width: 100% !important;
            padding: 8px 16px !important;
            transition: all 0.15s ease-in-out !important;
        }
        
        div.stButton > button:hover, div.stDownloadButton > button:hover {
            background-color: var(--gold-accent) !important;
            color: var(--navy-brand) !important;
            border-color: var(--gold-accent) !important;
        }
        
        /* Custom Clear All Hyperlink Button Styling Wrapper */
        .clear-all-container div.stButton > button {
            background: none !important;
            border: none !important;
            color: var(--navy-brand) !important;
            text-decoration: underline !important;
            font-weight: 700 !important;
            font-size: 11px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            padding: 0 !important;
            width: auto !important;
            box-shadow: none !important;
            border-radius: 0 !important;
            float: right !important;
        }
        
        .clear-all-container div.stButton > button:hover {
            color: var(--gold-accent) !important;
            background: none !important;
        }
        
        /* Clean Expander Tree Styling */
        [data-testid="stSidebar"] .st-expander {
            border: 1px solid var(--border-gray) !important;
            background-color: #f8fafc !important;
            border-radius: 8px !important;
            margin-bottom: 6px;
        }
        
        /* Zero-Edge Iframe Full Workspace Scaling */
        iframe {
            border: none !important;
            width: 100% !important;
            height: calc(100vh - 5px) !important;
        }
        
        .stDeployButton, footer, #stDecoration { display:none !important; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. STATE PERSISTENCE CORE
# -----------------------------------------------------------------------------
DEFAULT_COORDS = "14.6465, 121.0371"
DEFAULT_RADIUS = 1000
DEFAULT_SEARCH = ""
# Default to a centered viewing grid baseline matching your target coordinates location
INITIAL_URL = "https://overpass-turbo.eu/?C=14.6465;121.0371;14"

if 'geo_coords' not in st.session_state:
    st.session_state.geo_coords = DEFAULT_COORDS
if 'geo_radius' not in st.session_state:
    st.session_state.geo_radius = DEFAULT_RADIUS
if 'search_filter' not in st.session_state:
    st.session_state.search_filter = DEFAULT_SEARCH
if 'target_url' not in st.session_state:
    st.session_state.target_url = INITIAL_URL

def execute_global_purge():
    st.session_state.geo_coords = DEFAULT_COORDS
    st.session_state.geo_radius = DEFAULT_RADIUS
    st.session_state.search_filter = DEFAULT_SEARCH
    st.session_state.target_url = INITIAL_URL
    for key in list(st.session_state.keys()):
        if key.startswith("chk_") or key.startswith("input_chk_"):
            st.session_state[key] = False

# -----------------------------------------------------------------------------
# 3. TAG COMPILER DATA STRUCTURES
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
    "ADV - AMENITIES": [['ATM', '"amenity"="atm"'], ['Bank', '"amenity"="bank"']],
    "ADV - RETAIL_ADV": [['Beauty', '"shop"="beauty"'], ['Car', '"shop"="car"'], ['DIY/hardware', '"shop"~"hardware|doityourself",i']]
}

# -----------------------------------------------------------------------------
# 4. MATH MODULES (RADIUS BUFFER GENERATOR)
# -----------------------------------------------------------------------------
def compile_radius_kml(lat, lon, r_meters):
    kml = f'<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scan Radius Geofence</name><Placemark><name>Buffer Zone</name><Style><LineStyle><color>ff3d1a00</color><width>3</width></LineStyle><PolyStyle><fill>0</fill></PolyStyle></Style><Polygon><outerBoundaryIs><LinearRing><coordinates>'
    for i in range(37):
        angle = (i * 10) * math.pi / 180
        d_lat = (r_meters / 6371000) * math.cos(angle)
        d_lon = (r_meters / (6371000 * math.cos(lat * math.pi / 180))) * math.sin(angle)
        p_lat = lat + (d_lat * 180 / math.pi)
        p_lon = lon + (d_lon * 180 / math.pi)
        kml += f"{p_lon},{p_lat},0 "
    kml += '</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></Document></kml>'
    return kml

# -----------------------------------------------------------------------------
# 5. SIDEBAR QUERY PANEL WORKSPACE
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">TRADE AREA SCAN</div>', unsafe_allow_html=True)
    
    # Render clear button as a hyperlink element
    st.markdown('<div class="clear-all-container">', unsafe_allow_html=True)
    col_v, col_purge = st.columns([1.6, 1])
    with col_purge:
        if st.button("CLEAR ALL", key="master_purge_btn"):
            execute_global_purge()
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Core parameters mapping (No card containers)
    coords_val = st.text_input("Coordinates Target", key="geo_coords")
    radius_val = st.number_input("Scan Radius (Meters)", min_value=100, max_value=50000, key="geo_radius", step=100)

    coord_match = re.match(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", coords_val)
    lat_coord, lon_coord = (float(coord_match.group(1)), float(coord_match.group(2))) if coord_match else (14.6465, 121.0371)

    search_query = st.text_input("Filter Options", key="search_filter", placeholder="Search categories...").lower()
    
    selected_osm_tags = []
    for cat_name, node_items in POI_CONFIG.items():
        matched_rows = [item for item in node_items if search_query in item[0].lower()]
        if matched_rows:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for presentation_label, osm_tag in matched_rows:
                    if st.checkbox(presentation_label, key=f"input_chk_core_{cat_name}_{presentation_label}"):
                        selected_osm_tags.append(osm_tag)

    for cat_name, node_items in ADVANCED_CONFIG.items():
        matched_rows = [item for item in node_items if search_query in item[0].lower()]
        if matched_rows:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for presentation_label, osm_tag in matched_rows:
                    if st.checkbox(presentation_label, key=f"input_chk_adv_{cat_name}_{presentation_label}"):
                        selected_osm_tags.append(osm_tag)

    # Dropdown handles localized file outputs vs remote app instructions info
    export_format = st.selectbox("Export Options Data Dropdown", ["Select Export Format...", "Radius (KML)", "POIs & CSV Tables (Use Map Export Panel)"], index=0)
    
    if export_format == "Radius (KML)":
        radius_kml_payload = compile_radius_kml(lat_coord, lon_coord, radius_val)
        st.download_button(
            label="Download Radius KML",
            data=radius_kml_payload,
            file_name=f"Radius_Ring_{radius_val}m.kml",
            mime="application/vnd.google-earth.kml+xml"
        )
    elif export_format == "POIs & CSV Tables (Use Map Export Panel)":
        st.info("💡 To export compiled map vectors or tables, use the native 'Export' action button located inside the top menu bar of the Overpass Turbo canvas workspace.")

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🚀 SCAN AREA PROFILE", type="primary", use_container_width=True):
        if not selected_osm_tags:
            st.error("Select at least 1 feature layer to compile data.")
        else:
            # Complete QL code construction logic script strings
            statements = "\n".join([f"  nwr[{tag}](around:{radius_val},{lat_coord},{lon_coord});" for tag in selected_osm_tags])
            compiled_ql = f"[out:json][timeout:120];\n(\n{statements}\n);\nout center;\n>;\nout skel qt;"
            encoded_ql = urllib.parse.quote(compiled_ql)
            
            # Pass encoded script along with the execution trigger flag 'R'
            st.session_state.target_url = f"https://overpass-turbo.eu/?Q={encoded_ql}&R"
            st.rerun()

# -----------------------------------------------------------------------------
# 6. WORKSPACE VIEWPORT ENGINE (EDGE-TO-EDGE OVERPASS IFRAME LAYOUT)
# -----------------------------------------------------------------------------
st.components.v1.iframe(st.session_state.target_url)
