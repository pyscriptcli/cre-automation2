import streamlit as st
import requests
import re
import math
import json

# -----------------------------------------------------------------------------
# 1. CORE INTERFACE SETUP & ADVANCED CARD STYLING MAPS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TRADE AREA SCAN",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Implementation of customized CSS rules for light-themed embossed structures
st.markdown("""
    <style>
        /* Base Theme Set Variables */
        :root {
            --navy: #001a3d;
            --white: #ffffff;
            --gold: #d4af37;
            --slate-bg: #f8fafc;
        }
        
        /* Remove framework margins to allow map layout maximization */
        .block-container {
            padding: 0rem !important;
        }
        
        /* Sidebar layout background adjustments */
        [data-testid="stSidebar"] {
            background-color: var(--slate-bg) !important;
            color: var(--navy) !important;
            border-right: 3px solid var(--navy) !important;
        }
        
        /* Ensure sidebar content has breathing room above fixed footer */
        [data-testid="stSidebarUserContent"] {
            padding-bottom: 220px !important;
        }
        
        /* Embossed Custom Container Architecture Layouts */
        .ui-container-block {
            background-color: var(--white);
            border: 2px solid var(--navy);
            border-radius: 8px;
            padding: 14px;
            margin-bottom: 12px;
            box-shadow: 3px 3px 0px var(--navy);
        }
        
        /* Custom Labels & Typography overrides */
        [data-testid="stSidebar"] label {
            color: var(--navy) !important;
            font-weight: 800 !important;
            font-family: 'Arial', sans-serif !important;
            text-transform: uppercase;
            font-size: 10px !important;
            letter-spacing: 0.5px;
        }
        
        /* Sticky Actions Footer Tray Pinned securely to Bottom of Sidebar */
        div.sticky-footer-tray {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 336px; /* Matches standard Streamlit sidebar viewport width */
            background-color: var(--slate-bg);
            border-top: 3px solid var(--navy);
            padding: 16px;
            z-index: 999999;
        }
        
        /* Form Action Elements Styling Strategy (White BG, Bold Navy Text) */
        div.stButton > button, div.stDownloadButton > button {
            background-color: var(--white) !important;
            color: var(--navy) !important;
            font-weight: 900 !important;
            text-transform: uppercase !important;
            border: 2px solid var(--navy) !important;
            border-radius: 4px !important;
            width: 100% !important;
            box-shadow: 2px 2px 0px var(--navy) !important;
            font-size: 11px !important;
            transition: all 0.1s ease-in-out !important;
        }
        
        div.stButton > button:hover, div.stDownloadButton > button:hover {
            background-color: var(--navy) !important;
            color: var(--white) !important;
            box-shadow: 2px 2px 0px var(--gold) !important;
        }
        
        .stDeployButton, footer, #stDecoration { display:none !important; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. STATE STORAGE ASSIGNMENT MAPPINGS & INITIALIZATION
# -----------------------------------------------------------------------------
# Baseline constants defaults
DEFAULT_COORDS = "14.6465, 121.0371"
DEFAULT_RADIUS = 1000
DEFAULT_SEARCH = ""

if 'geo_coords' not in st.session_state:
    st.session_state.geo_coords = DEFAULT_COORDS
if 'geo_radius' not in st.session_state:
    st.session_state.geo_radius = DEFAULT_RADIUS
if 'search_filter' not in st.session_state:
    st.session_state.search_filter = DEFAULT_SEARCH
if 'scanned_records' not in st.session_state:
    st.session_state.scanned_records = []

# Unified Deep Clear Engine
def clear_all_parameters():
    st.session_state.geo_coords = DEFAULT_COORDS
    st.session_state.geo_radius = DEFAULT_RADIUS
    st.session_state.search_filter = DEFAULT_SEARCH
    st.session_state.scanned_records = []
    for key in list(st.session_state.keys()):
        if key.startswith("chk_"):
            st.session_state[key] = False

# -----------------------------------------------------------------------------
# 3. STATIC DATA DICTIONARY CONFIGURATIONS
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

# -----------------------------------------------------------------------------
# 4. KML COMPILER ENGINE MODULES
# -----------------------------------------------------------------------------
def compile_radius_kml(lat, lon, r_meters):
    kml = f'<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scan Radius Geofence</name><Placemark><name>Buffer Zone</name><Style><LineStyle><color>ff0000ff</color><width>3</width></LineStyle><PolyStyle><fill>0</fill></PolyStyle></Style><Polygon><outerBoundaryIs><LinearRing><coordinates>'
    for i in range(37):
        angle = (i * 10) * math.pi / 180
        d_lat = (r_meters / 6371000) * math.cos(angle)
        d_lon = (r_meters / (6371000 * math.cos(lat * math.pi / 180))) * math.sin(angle)
        p_lat = lat + (d_lat * 180 / math.pi)
        p_lon = lon + (d_lon * 180 / math.pi)
        kml += f"{p_lon},{p_lat},0 "
    kml += '</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></Document></kml>'
    return kml

def compile_features_kml(features):
    kml = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scanned POI Asset Layers</name>'
    for f in features:
        name = html_escape(f.get('name', 'Unnamed Asset'))
        class_type = html_escape(f.get('type', 'POI Node'))
        kml += f"<Placemark><name>{name}</name><description>Classification: {class_type}</description><Point><coordinates>{f['lon']},{f['lat']},0</coordinates></Point></Placemark>"
    kml += '</Document></kml>'
    return kml

def html_escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# -----------------------------------------------------------------------------
# 5. CONTROL INTERFACE DISPLAY MECHANICS (SIDEBAR WORKSPACE)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 style='color:var(--navy); text-align:center; font-family:Arial; font-weight:900; margin-top:10px; margin-bottom:5px; letter-spacing:1px;'>TRADE AREA SCAN</h2>", unsafe_allow_html=True)
    
    # GLOBAL RESET HANDLER LINK TRIGGER
    col_void, col_clear_trigger = st.columns([2, 1])
    with col_clear_trigger:
        if st.button("❌ CLEAR ALL", key="master_purge_btn", help="Completely reset geographic properties and clean selections"):
            clear_all_parameters()
            st.rerun()

    # CONTAINER 1: GEOGRAPHIC INPUT SEPARATE CARD UI
    st.markdown('<div class="ui-container-block">', unsafe_allow_html=True)
    st.markdown("<div style='color:var(--navy); font-weight:900; font-size:11px; margin-bottom:8px;'>GEOGRAPHIC PROFILE</div>", unsafe_allow_html=True)
    coords_val = st.text_input("Target Center Coordinates", key="geo_coords")
    radius_val = st.number_input("Scan Radius Boundary (M)", min_value=100, max_value=50000, key="geo_radius", step=100)
    st.markdown('</div>', unsafe_allow_html=True)

    # Coords parsing validation match
    coord_match = re.match(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", coords_val)
    lat_coord, lon_coord = (float(coord_match.group(1)), float(coord_match.group(2))) if coord_match else (14.6465, 121.0371)

    # CONTAINER 2: BASEMAP OPTIONS CARD UI
    st.markdown('<div class="ui-container-block">', unsafe_allow_html=True)
    st.markdown("<div style='color:var(--navy); font-weight:900; font-size:11px; margin-bottom:8px;'>BASEMAP VIEW SELECTION</div>", unsafe_allow_html=True)
    basemap_choice = st.selectbox("Layer Engine Type", ["OpenStreetMap", "Carto Light", "Satellite Real World"], index=0, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    # CONTAINER 3: SELECTION SEARCH & POIS ACCORDION TREE CARD UI
    st.markdown('<div class="ui-container-block">', unsafe_allow_html=True)
    st.markdown("<div style='color:var(--navy); font-weight:900; font-size:11px; margin-bottom:8px;'>TARGET LAYER QUERY LIBRARY</div>", unsafe_allow_html=True)
    search_query = st.text_input("Search POI Categories", key="search_filter").lower()
    
    selected_osm_tags = []
    for cat_name, node_items in POI_CONFIG.items():
        matched_rows = [item for item in node_items if search_query in item[0].lower()]
        if matched_rows:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for presentation_label, osm_tag in matched_rows:
                    if st.checkbox(presentation_label, key=f"chk_core_{cat_name}_{presentation_label}"):
                        selected_osm_tags.append(osm_tag)
    st.markdown('</div>', unsafe_allow_html=True)

    # PERSISTENT CONTROL BAR TRAY DESIGN OVERLAY AT BOTTOM
    st.markdown('<div class="sticky-footer-tray">', unsafe_allow_html=True)
    
    # Process Execution Action
    if st.button("🛰️ SCAN AREA PROFILE", type="primary", use_container_width=True):
        if not selected_osm_tags:
            st.error("Select minimal 1 item to profile.")
        else:
            # Native Backend Thread Execution targeting standard interpreter endpoints
            overpass_url = "https://overpass-api.de/api/interpreter"
            statements = "\n".join([f"  nwr[{tag}](around:{radius_val},{lat_coord},{lon_coord});" for tag in selected_osm_tags])
            compiled_ql = f"[out:json][timeout:90];(\n{statements}\n);\nout center;"
            
            try:
                api_response = requests.post(overpass_url, data={"data": compiled_ql}, timeout=100)
                if api_response.status_code == 200:
                    raw_elements = api_response.json().get('elements', [])
                    parsed_records = []
                    for el in raw_elements:
                        e_lat = el.get('lat') or el.get('center', {}).get('lat')
                        e_lon = el.get('lon') or el.get('center', {}).get('lon')
                        if e_lat and e_lon:
                            tags = el.get('tags', {})
                            parsed_records.append({
                                "lat": e_lat, "lon": e_lon,
                                "name": tags.get('name', 'Unnamed Node'),
                                "type": tags.get('amenity') or tags.get('shop') or tags.get('building') or 'Asset Point'
                            })
                    st.session_state.scanned_records = parsed_records
                    if not parsed_records:
                        st.sidebar.warning("No nodes found.")
                else:
                    st.sidebar.error(f"Server Error Status: {api_response.status_code}")
            except Exception as e:
                st.sidebar.error(f"Network Timeout: {str(e)}")

    # Double Down Column Export System Frame Layout
    col_exp_scan, col_exp_rad = st.columns(2)
    with col_exp_scan:
        scanned_kml_payload = compile_features_kml(st.session_state.scanned_records)
        st.download_button(
            label="KML Scanned Area",
            data=scanned_kml_payload,
            file_name=f"Scanned_Area_{radius_val}m.kml",
            mime="application/vnd.google-earth.kml+xml",
            disabled=(len(st.session_state.scanned_records) == 0)
        )
    with col_exp_rad:
        radius_kml_payload = compile_radius_kml(lat_coord, lon_coord, radius_val)
        st.download_button(
            label="KML Radius Ring",
            data=radius_kml_payload,
            file_name=f"Radius_Ring_{radius_val}m.kml",
            mime="application/vnd.google-earth.kml+xml"
        )
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. PRIMARY VIEWPORT DISPLAY MAIN AREA (ZERO-LATENCY LEAFLET VIEWPORT)
# -----------------------------------------------------------------------------
# Basemap URL Registry Dict
TILE_DICTIONARY = {
    "OpenStreetMap": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    "Carto Light": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    "Satellite Real World": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
}
selected_tile_template = TILE_DICTIONARY[basemap_choice]

# Convert python collection objects to raw JSON strings safely injected to layout frames
geojson_features_string = json.dumps(st.session_state.scanned_records)

leaflet_injection_html = f"""
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body, html, #map-canvas-container {{
            margin: 0; padding: 0; height: 100vh; width: 100vw; overflow: hidden;
        }}
    </style>
</head>
<body>
    <div id="map-canvas-container"></div>
    <script>
        // Init viewport coordinates mapping
        const map = L.map('map-canvas-container', {{ zoomControl: true, attributionControl: false }}).setView([{lat_coord}, {lon_coord}], 14);
        
        // Dynamic basemap tile provider loading sequence execution
        L.tileLayer('{selected_tile_template}', {{ maxZoom: 19 }}).addTo(map);
        
        // Affix focal center target point vector overlay asset
        L.circleMarker([{lat_coord}, {lon_coord}], {{
            radius: 8, fillColor: "#ff3333", color: "#ffffff", weight: 3, opacity: 1, fillOpacity: 1
        }}).addTo(map).bindPopup("<b>PRIME LOGISTICS TARGET CENTER</b>");
        
        // Draw physical scanning perimeter buffer line geofence ring
        L.circle([{lat_coord}, {lon_coord}], {{
            radius: {radius_val}, color: "#001a3d", weight: 2, fillColor: "#d4af37", fillOpacity: 0.08
        }}).addTo(map);
        
        // Parse raw payload elements
        const featurePoints = {geojson_features_string};
        
        // Intercept loops to mount parsed markers on canvas interface layouts
        featurePoints.forEach(pt => {{
            L.circleMarker([pt.lat, pt.lon], {{
                radius: 6, fillColor: "#d4af37", color: "#001a3d", weight: 1.5, opacity: 1, fillOpacity: 0.9
            }}).addTo(map).bindPopup("<b>" + pt.name + "</b><br>Class: " + pt.type);
        }});
        
        // Automatic boundary scale adjustment
        if(featurePoints.length > 0) {{
            const group = new L.featureGroup([
                L.marker([{lat_coord}, {lon_coord}]),
                ...featurePoints.map(p => L.marker([p.lat, p.lon]))
            ]);
            map.fitBounds(group.getBounds().pad(0.1));
        }}
    </script>
</body>
</html>
"""

# Render map layout execution seamlessly inside remaining horizontal and vertical screen space
st.components.v1.html(leaflet_injection_html, height=None, scrolling=False)
