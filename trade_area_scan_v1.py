import streamlit as st
import requests
import re
import math
import json

# -----------------------------------------------------------------------------
# 1. LUXURY CORPORATE NAVY & GOLD DOM STYLING ENGINE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TRADE AREA SCAN",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Deep inject custom style metrics to completely rebuild Streamlit's base shell
st.markdown("""
    <style>
        /* Base Variables Definitions */
        :root {
            --navy-main: #001a3d;
            --navy-dark: #001126;
            --gold-accent: #d4af37;
            --white-clean: #ffffff;
            --glass-bg: rgba(255, 255, 255, 0.05);
            --glass-border: rgba(212, 175, 55, 0.2);
        }
        
        /* Maximize primary workspace surface footprint */
        .block-container {
            padding: 0rem !important;
        }
        
        /* Complete Sidebar Re-skinning */
        [data-testid="stSidebar"] {
            background-color: var(--navy-main) !important;
            color: var(--white-clean) !important;
            border-right: 2px solid var(--gold-accent) !important;
        }
        
        /* Enforce layout padding clear space above the action panel */
        [data-testid="stSidebarUserContent"] {
            padding-bottom: 220px !important;
            padding-left: 12px !important;
            padding-right: 12px !important;
        }
        
        /* Luxury Micro-Card Container Structuring */
        .ui-container-block {
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 14px;
            transition: border-color 0.2s ease;
        }
        .ui-container-block:hover {
            border-color: var(--gold-accent);
        }
        
        /* Executive Level Typography Rules */
        [data-testid="stSidebar"] h2 {
            font-size: 20px !important;
            letter-spacing: 2px !important;
            text-transform: uppercase !important;
            text-shadow: 0px 2px 4px rgba(0,0,0,0.3);
        }
        
        [data-testid="stSidebar"] label p {
            color: var(--white-clean) !important;
            font-weight: 700 !important;
            font-size: 10px !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
            opacity: 0.85;
        }
        
        /* Overriding Native Streamlit Input Widgets for Brand Alignment */
        div[data-baseweb="input"], div[data-baseweb="select"] {
            background-color: rgba(0, 17, 38, 0.6) !important;
            border: 1px solid var(--glass-border) !important;
            border-radius: 4px !important;
            color: var(--white-clean) !important;
        }
        div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {
            border-color: var(--gold-accent) !important;
        }
        input {
            color: var(--white-clean) !important;
            font-family: 'Arial', sans-serif !important;
        }
        
        /* Fixed Sticky Action Control Bar at Sidebar Root base */
        div.sticky-footer-tray {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 336px;
            background-color: var(--navy-dark);
            border-top: 2px solid var(--gold-accent);
            padding: 16px;
            z-index: 999999;
            box-shadow: 0px -5px 15px rgba(0,0,0,0.5);
        }
        
        /* Styled Clean Action Inputs (White/Gold Transitions) */
        div.stButton > button, div.stDownloadButton > button {
            background-color: var(--white-clean) !important;
            color: var(--navy-main) !important;
            font-weight: 800 !important;
            font-size: 11px !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
            border: 1px solid var(--white-clean) !important;
            border-radius: 4px !important;
            width: 100% !important;
            padding: 8px 0px !important;
            transition: all 0.2s ease-in-out !important;
            box-shadow: none !important;
        }
        
        div.stButton > button:hover, div.stDownloadButton > button:hover {
            background-color: var(--gold-accent) !important;
            color: var(--navy-dark) !important;
            border-color: var(--gold-accent) !important;
        }
        
        /* Custom Streamlit Accordion Polish */
        [data-testid="stSidebar"] .st-expander {
            border: 1px solid rgba(255,255,255,0.1) !important;
            background-color: rgba(0,0,0,0.2) !important;
            margin-bottom: 4px;
        }
        
        /* Hide native framework branding artifacts */
        .stDeployButton, footer, #stDecoration { display:none !important; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. STATE CAPTURE ENGINE INITIALIZATION
# -----------------------------------------------------------------------------
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

def trigger_master_purge():
    st.session_state.geo_coords = DEFAULT_COORDS
    st.session_state.geo_radius = DEFAULT_RADIUS
    st.session_state.search_filter = DEFAULT_SEARCH
    st.session_state.scanned_records = []
    for key in list(st.session_state.keys()):
        if key.startswith("chk_"):
            st.session_state[key] = False

# -----------------------------------------------------------------------------
# 3. GEOSPATIAL REGISTRY STRUCTURES
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
# 4. DATA EXPORT STORAGE WRITERS
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
        name = f.get('name', 'Unnamed Asset').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        class_type = f.get('type', 'POI Node').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        kml += f"<Placemark><name>{name}</name><description>Classification: {class_type}</description><Point><coordinates>{f['lon']},{f['lat']},0</coordinates></Point></Placemark>"
    kml += '</Document></kml>'
    return kml

# -----------------------------------------------------------------------------
# 5. CONTROL INTERFACE GRAPHICS (SIDEBAR WORKSPACE)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 style='color:var(--gold-accent); text-align:center; font-family:Arial; font-weight:900; margin-top:15px; margin-bottom:5px;'>TRADE AREA SCAN</h2>", unsafe_allow_html=True)
    
    col_void, col_clear_trigger = st.columns([1.5, 1])
    with col_clear_trigger:
        if st.button("✨ CLEAR ALL", key="master_purge_btn", help="Flush all geo configurations and selected vectors"):
            trigger_master_purge()
            st.rerun()

    # PANEL CARD 1: GEOGRAPHIC CRITERIA
    st.markdown('<div class="ui-container-block">', unsafe_allow_html=True)
    st.markdown("<div style='color:var(--gold-accent); font-weight:800; font-size:11px; margin-bottom:10px; letter-spacing:0.5px;'>GEOGRAPHIC PARAMETERS</div>", unsafe_allow_html=True)
    coords_val = st.text_input("Center Coordinates", key="geo_coords")
    radius_val = st.number_input("Buffer Radius (M)", min_value=100, max_value=50000, key="geo_radius", step=100)
    st.markdown('</div>', unsafe_allow_html=True)

    coord_match = re.match(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", coords_val)
    lat_coord, lon_coord = (float(coord_match.group(1)), float(coord_match.group(2))) if coord_match else (14.6465, 121.0371)

    # PANEL CARD 2: RENDER BASES
    st.markdown('<div class="ui-container-block">', unsafe_allow_html=True)
    st.markdown("<div style='color:var(--gold-accent); font-weight:800; font-size:11px; margin-bottom:10px; letter-spacing:0.5px;'>BASEMAP SELECTION</div>", unsafe_allow_html=True)
    basemap_choice = st.selectbox("Layer Engine Type", ["OpenStreetMap", "Carto Light", "Satellite Real World"], index=0, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    # PANEL CARD 3: QUERY MATRIX FILTER
    st.markdown('<div class="ui-container-block">', unsafe_allow_html=True)
    st.markdown("<div style='color:var(--gold-accent); font-weight:800; font-size:11px; margin-bottom:10px; letter-spacing:0.5px;'>POI LAYER REGISTRY</div>", unsafe_allow_html=True)
    search_query = st.text_input("Filter Categories", key="search_filter", placeholder="Type to filter...").lower()
    
    selected_osm_tags = []
    for cat_name, node_items in POI_CONFIG.items():
        matched_rows = [item for item in node_items if search_query in item[0].lower()]
        if matched_rows:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for presentation_label, osm_tag in matched_rows:
                    if st.checkbox(presentation_label, key=f"chk_core_{cat_name}_{presentation_label}"):
                        selected_osm_tags.append(osm_tag)
    st.markdown('</div>', unsafe_allow_html=True)

    # FIXED PERSISTENT TRAY FOOTER OVERLAY AT SIDEBAR BASE
    st.markdown('<div class="sticky-footer-tray">', unsafe_allow_html=True)
    if st.button("🛰️ EXECUTE SURVEY SCAN", type="primary", use_container_width=True):
        if not selected_osm_tags:
            st.error("Select at least 1 layer vector.")
        else:
            overpass_url = "https://overpass-api.de/api/interpreter"
            statements = "\n".join([f"  nwr[{tag}](around:{radius_val},{lat_coord},{lon_coord});" for tag in selected_osm_tags])
            compiled_ql = f"[out:json][timeout:90];(\n{statements}\n);\nout center;"
            
            with st.spinner("Querying Overpass Nodes..."):
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
                    else:
                        st.sidebar.error(f"API Interface Error: {api_response.status_code}")
                except Exception as e:
                    st.sidebar.error(f"Network Timeout: {str(e)}")

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
# 6. WORKSPACE VIEWPORT LAYER (FULL RE-CALCULATION BLOCKS)
# -----------------------------------------------------------------------------
TILE_DICTIONARY = {
    "OpenStreetMap": "https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",
    "Carto Light": "https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png",
    "Satellite Real World": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}"
}
selected_tile_template = TILE_DICTIONARY[basemap_choice]
geojson_features_string = json.dumps(st.session_state.scanned_records)

leaflet_injection_html = f"""
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body, html, #map-canvas-container {{
            margin: 0; padding: 0; height: 100vh; width: 100vw; overflow: hidden; background: #001126;
        }}
    </style>
</head>
<body>
    <div id="map-canvas-container"></div>
    <script>
        const map = L.map('map-canvas-container', {{ zoomControl: true, attributionControl: false }}).setView([{lat_coord}, {lon_coord}], 14);
        L.tileLayer('{selected_tile_template}', {{ maxZoom: 19 }}).addTo(map);
        
        L.circleMarker([{lat_coord}, {lon_coord}], {{
            radius: 9, fillColor: "#ff3333", color: "#ffffff", weight: 3, opacity: 1, fillOpacity: 1
        }}).addTo(map).bindPopup("<b>TARGET CENTER POINT</b>");
        
        L.circle([{lat_coord}, {lon_coord}], {{
            radius: {radius_val}, color: "#d4af37", weight: 2, fillColor: "#d4af37", fillOpacity: 0.05
        }}).addTo(map);
        
        const featurePoints = {geojson_features_string};
        featurePoints.forEach(pt => {{
            L.circleMarker([pt.lat, pt.lon], {{
                radius: 6, fillColor: "#d4af37", color: "#001a3d", weight: 1.5, opacity: 1, fillOpacity: 0.9
            }}).addTo(map).bindPopup("<b>" + pt.name + "</b><br>Type: " + pt.type);
        }});
        
        if(featurePoints.length > 0) {{
            const group = new L.featureGroup([
                L.marker([{lat_coord}, {lon_coord}]),
                ...featurePoints.map(p => L.marker([p.lat, p.lon]))
            ]);
            map.fitBounds(group.getBounds().pad(0.1));
        }}
        
        setTimeout(function() {{ map.invalidateSize(); }}, 200);
    </script>
</body>
</html>
"""

st.components.v1.html(leaflet_injection_html, height=920, scrolling=False)
