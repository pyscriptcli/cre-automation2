import streamlit as st
import urllib.parse
import re
import math

# -----------------------------------------------------------------------------
# 1. COMPACT LIGHT MODE & COMPONENT SCALING OVERRIDES
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TRADE AREA SCAN",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Deep injection of optimized CSS rules to compress element footprints
st.markdown("""
    <style>
        :root {
            --navy-brand: #001a3d;
            --white-clean: #ffffff;
            --gold-accent: #d4af37;
            --border-gray: #e2e8f0;
        }
        
        /* Maximize primary viewport landscape real estate */
        .block-container {
            padding: 0rem !important;
        }
        
        /* High-Density Light Mode Sidebar Layout */
        [data-testid="stSidebar"] {
            background-color: var(--white-clean) !important;
            color: var(--navy-brand) !important;
            border-right: 1px solid var(--border-gray) !important;
        }
        
        [data-testid="stSidebarUserContent"] {
            padding-top: 14px !important;
            padding-left: 12px !important;
            padding-right: 12px !important;
        }
        
        /* Compact Brand Header Typography */
        .sidebar-title {
            color: var(--navy-brand) !important;
            font-size: 20px !important;
            font-weight: 900 !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
            text-align: center !important;
            margin-top: 5px !important;
            margin-bottom: 2px !important;
            font-family: 'Arial', sans-serif !important;
        }
        
        /* Tightened Widget Input Labels */
        [data-testid="stSidebar"] label p {
            color: var(--navy-brand) !important;
            font-weight: 700 !important;
            font-size: 10px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            margin-bottom: -4px !important;
        }
        
        /* Compact Form Element Heights and Paddings */
        div[data-baseweb="input"], div[data-baseweb="select"], .stSelectbox, .stTextInput, .stNumberInput {
            border-radius: 6px !important;
        }
        
        div[data-baseweb="input"] {
            border: 1px solid var(--border-gray) !important;
            padding: 2px 4px !important;
        }
        
        /* Custom Plain-Text Hyperlink Emulation for Clear Actions */
        div.clear-link-container {
            text-align: right;
            margin-top: -10px;
            margin-bottom: 5px;
        }
        div.clear-link-container button {
            background: none !important;
            border: none !important;
            padding: 0 !important;
            color: var(--navy-brand) !important;
            text-decoration: underline !important;
            font-weight: 700 !important;
            font-size: 11px !important;
            text-transform: uppercase !important;
            cursor: pointer !important;
        }
        div.clear-link-container button:hover {
            color: var(--gold-accent) !important;
        }
        
        /* Rounded Pill Design Pattern for Primary Execution Button */
        div.stButton > button, div.stDownloadButton > button {
            background-color: var(--navy-brand) !important;
            color: var(--white-clean) !important;
            font-weight: 700 !important;
            font-size: 11px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            border: 1px solid var(--navy-brand) !important;
            border-radius: 20px !important;
            width: 100% !important;
            padding: 6px 12px !important;
            transition: all 0.1s ease-in-out !important;
        }
        
        div.stButton > button:hover, div.stDownloadButton > button:hover {
            background-color: var(--gold-accent) !important;
            color: var(--navy-brand) !important;
            border-color: var(--gold-accent) !important;
        }
        
        /* Compact Expander Component Spacing */
        [data-testid="stSidebar"] .st-expander {
            border: 1px solid var(--border-gray) !important;
            background-color: #f8fafc !important;
            border-radius: 6px !important;
            margin-bottom: 4px;
        }
        
        /* Edge-to-Edge Full Screen Iframe Canvas Viewport */
        iframe {
            border: none !important;
            width: 100% !important;
            height: calc(100vh - 4px) !important;
        }
        
        .stDeployButton, footer, #stDecoration { display:none !important; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. STATE LOGIC LIFECYCLE
# -----------------------------------------------------------------------------
DEFAULT_COORDS = "14.6465, 121.0371"
DEFAULT_RADIUS = 1000
DEFAULT_SEARCH = ""
# Collapse the left sidebar panel natively by declaring sidebar=no in the startup template URL
INITIAL_URL = "https://overpass-turbo.eu/?C=14.6465;121.0371;14&sidebar=no"

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
# 3. OSM FEATURE TREE DICTIONARIES
# -----------------------------------------------------------------------------
POI_CONFIG = {
    "COMMERCIAL": [['Corporate Office', '"building"~"office|commercial",i'], ['IT/Tech Center', '"office"~"it|telecommunication",i'], ['Business Center', '"building"="commercial"'], ['Hospital', '"amenity"~"hospital|clinic",i'], ['Hotel', '"tourism"="hotel"']],
    "RETAIL": [['Mall/Department Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"supermarket|grocery",i'], ['Convenience Store', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"']],
    "FOOD AND BEVERAGES": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee Shop', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"']],
    "INDUSTRIAL & LOGISTICS": [
        ['Expressway Exits', '"highway"~"motorway_junction|toll_gantry",i'], 
        ['Ports & Terminals', '"industrial"="port"'], 
        ['Manufacturing Plants', '"industrial"~"factory|manufacturing|processing",i'],
        ['Cold Storage Facilities', '"warehouse"~"cold_store|cold_storage",i']
    ]
}

ADVANCED_CONFIG = {
    "ADV - AMENITIES": [['ATM', '"amenity"="atm"'], ['Bank', '"amenity"="bank"']],
    "ADV - RETAIL_ADV": [['Beauty', '"shop"="beauty"'], ['Car', '"shop"="car"']]
}

# -----------------------------------------------------------------------------
# 4. MATH MODULES (RADIUS GEOMETRY STRING COMPILER)
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
# 5. CONTROL SWITCHBOARD DECK (SIDEBAR WORKSPACE)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">TRADE AREA SCAN</div>', unsafe_allow_html=True)
    
    # Render pure link text element container
    st.markdown('<div class="clear-link-container">', unsafe_allow_html=True)
    if st.button("CLEAR ALL", key="master_purge_btn"):
        execute_global_purge()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Scoped parameters mapping
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

    # Data distribution options selectbox dropdown
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
        st.info("💡 Click 'Export' at the top of the map workspace to download data attributes.")

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🚀 SCAN AREA PROFILE", type="primary", use_container_width=True):
        if not selected_osm_tags:
            st.error("Select at least 1 feature layer to compile data.")
        else:
            # Overpass QL dynamic string generation loop
            statements = "\n".join([f"  nwr[{tag}](around:{radius_val},{lat_coord},{lon_coord});" for tag in selected_osm_tags])
            
            # MapCSS block injection: forces a bold red marker dot over derived pin node targets
            mapcss_style = """
            {{style:
              node[marker_type="center_pin"] { color: #ff0000; fill-color: #ff0000; radius: 8; opacity: 1; fill-opacity: 1; }
            }}
            """
            
            compiled_ql = f"[out:json][timeout:120];\n(\n{statements}\n  make node ::lat={lat_coord}, ::lon={lon_coord}, name='TARGET CENTER PIN', marker_type='center_pin';\n);\nout center;\n>;\nout skel qt;\n{mapcss_style}"
            encoded_ql = urllib.parse.quote(compiled_ql)
            
            # Formulate the target frame URL parameter layout with editor panels collapsed (sidebar=no)
            st.session_state.target_url = f"https://overpass-turbo.eu/?Q={encoded_ql}&R&sidebar=no"
            st.rerun()

# -----------------------------------------------------------------------------
# 6. EDGE-TO-EDGE WORKSPACE IFRAME CANVAS
# -----------------------------------------------------------------------------
st.components.v1.iframe(st.session_state.target_url)
