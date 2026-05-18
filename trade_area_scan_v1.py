import streamlit as st
import requests
import re
import math
import json
import pandas as pd

# -----------------------------------------------------------------------------
# 1. LIGHT MODE SYSTEM DESIGN & CORPORATE TYPOGRAPHY CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TRADE AREA SCAN",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS injection to center headers, style hyperlinks, and round elements
st.markdown("""
    <style>
        :root {
            --navy-brand: #001a3d;
            --white-clean: #ffffff;
            --gold-accent: #d4af37;
            --border-gray: #e0e4ec;
        }
        
        /* Maximize workspace dimensions */
        .block-container {
            padding: 0rem !important;
        }
        
        /* Clean Light Mode Sidebar Specification */
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
        
        /* Upscaled & Centered App Title Header */
        .sidebar-title {
            color: var(--navy-brand) !important;
            font-size: 28px !important;
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
        
        /* Precise Geometric Rounding Rules for Input Fields */
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
        
        /* Standard Pill Buttons (Scan and Download Utilities) */
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
        
        /* Isolated Hyperlink Emulation Class for CLEAR ALL Triggers */
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
        
        /* Seamless Expansion Accordion Rounding */
        [data-testid="stSidebar"] .st-expander {
            border: 1px solid var(--border-gray) !important;
            background-color: #f8fafc !important;
            border-radius: 8px !important;
            margin-bottom: 6px;
        }
        
        .stDeployButton, footer, #stDecoration { display:none !important; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. APPLICATION LIFECYCLE MANAGEMENT ENGINE
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

def execute_global_purge():
    st.session_state.geo_coords = DEFAULT_COORDS
    st.session_state.geo_radius = DEFAULT_RADIUS
    st.session_state.search_filter = DEFAULT_SEARCH
    st.session_state.scanned_records = []
    for key in list(st.session_state.keys()):
        if key.startswith("chk_") or key.startswith("input_chk_"):
            st.session_state[key] = False

# -----------------------------------------------------------------------------
# 3. SPATIAL PARAMETER TAG DICTIONARIES
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
# 4. DATA PACKAGING ENGINE (KML AND CSV WRITERS)
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

def compile_features_kml(features):
    kml = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scanned POI Asset Layers</name>'
    for f in features:
        name = f.get('name', 'Unnamed Asset').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        class_type = f.get('type', 'POI Node').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        kml += f"<Placemark><name>{name}</name><description>Classification: {class_type}</description><Point><coordinates>{f['lon']},{f['lat']},0</coordinates></Point></Placemark>"
    kml += '</Document></kml>'
    return kml

# -----------------------------------------------------------------------------
# 5. CONTROL PANEL GRAPHICS (SIDEBAR COMPONENT ENGINE)
# -----------------------------------------------------------------------------
with st.sidebar:
    # Centered Title Injector
    st.markdown('<div class="sidebar-title">TRADE AREA SCAN</div>', unsafe_allow_html=True)
    
    # Styled Clear All Hyperlink Button Anchor Block
    st.markdown('<div class="clear-all-container">', unsafe_allow_html=True)
    col_v, col_purge = st.columns([1.6, 1])
    with col_purge:
        if st.button("CLEAR ALL", key="master_purge_btn", help="Flush coordinate configurations, filters, and plotted layers"):
            execute_global_purge()
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Geographic Core Properties (Container card layers completely expunged)
    coords_val = st.text_input("Coordinates Target", key="geo_coords")
    radius_val = st.number_input("Scan Radius (Meters)", min_value=100, max_value=50000, key="geo_radius", step=100)

    coord_match = re.match(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", coords_val)
    lat_coord, lon_coord = (float(coord_match.group(1)), float(coord_match.group(2))) if coord_match else (14.6465, 121.0371)

    # Active Filter Interface
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

    # Structural Dropdown for Multi-Format Exports
    export_format = st.selectbox("Export Options Data Dropdown", ["Select Export Format...", "Radius (KML)", "POIs (KML)", "Attributes (CSV)"], index=0)
    
    if export_format == "Radius (KML)":
        radius_kml_payload = compile_radius_kml(lat_coord, lon_coord, radius_val)
        st.download_button(
            label="Download Radius KML",
            data=radius_kml_payload,
            file_name=f"Radius_Ring_{radius_val}m.kml",
            mime="application/vnd.google-earth.kml+xml"
        )
    elif export_format == "POIs (KML)":
        scanned_kml_payload = compile_features_kml(st.session_state.scanned_records)
        st.download_button(
            label="Download POI KML",
            data=scanned_kml_payload,
            file_name=f"Scanned_Area_{radius_val}m.kml",
            mime="application/vnd.google-earth.kml+xml",
            disabled=(len(st.session_state.scanned_records) == 0)
        )
    elif export_format == "Attributes (CSV)":
        if st.session_state.scanned_records:
            csv_dataframe = pd.DataFrame(st.session_state.scanned_records)
            csv_payload = csv_dataframe.to_csv(index=False).encode('utf-8')
        else:
            csv_payload = b""
        st.download_button(
            label="Download Attributes CSV",
            data=csv_payload,
            file_name=f"Trade_Area_Nodes_{radius_val}m.csv",
            mime="text/csv",
            disabled=(len(st.session_state.scanned_records) == 0)
        )

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🚀 SCAN AREA PROFILE", type="primary", use_container_width=True):
        if not selected_osm_tags:
            st.error("Select at least 1 feature layer to compile data.")
        else:
            overpass_url = "https://overpass-api.de/api/interpreter"
            statements = "\n".join([f"  nwr[{tag}](around:{radius_val},{lat_coord},{lon_coord});" for tag in selected_osm_tags])
            compiled_ql = f"[out:json][timeout:90];(\n{statements}\n);\nout center;"
            
            with st.spinner("Executing spatial compile over backend API..."):
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
                        st.rerun()
                    else:
                        st.sidebar.error(f"Interpreter Exception: {api_response.status_code}")
                except Exception as e:
                    st.sidebar.error(f"Network Connection Timeout: {str(e)}")

# -----------------------------------------------------------------------------
# 6. FIXED CANVAS SPATIAL VIEWPORT (NATIVE HIGH-PERFORMANCE LEAFLET)
# -----------------------------------------------------------------------------
geojson_features_string = json.dumps(st.session_state.scanned_records)

# Hardcoded standard light mode OpenStreetMap layer configuration strings
light_mode_basemap_url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"

leaflet_injection_html = f"""
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body, html {{
            margin: 0; padding: 0; overflow: hidden; background: #ffffff;
        }}
        #map-canvas-container {{
            width: 100%;
            height: 900px;
        }}
    </style>
</head>
<body>
    <div id="map-canvas-container"></div>
    <script>
        const map = L.map('map-canvas-container', {{ zoomControl: true, attributionControl: false }}).setView([{lat_coord}, {lon_coord}], 14);
        L.tileLayer('{light_mode_basemap_url}', {{ maxZoom: 19, noWrap: false }}).addTo(map);
        
        // Solid Red Pinned Target Circle Dot Marker Asset Configuration
        L.circleMarker([{lat_coord}, {lon_coord}], {{
            radius: 7, fillColor: "#ff0000", color: "#ffffff", weight: 2, opacity: 1, fillOpacity: 1
        }}).addTo(map).bindPopup("<b>PINNED GEOGRAPHIC TARGET</b>");
        
        // Boundary Scan Perimeter Buffer Ring - Corporate Navy Blue with Light 12% Translucent Inner Fill Opacity
        L.circle([{lat_coord}, {lon_coord}], {{
            radius: {radius_val}, color: "#001a3d", weight: 2.5, fillColor: "#001a3d", fillOpacity: 0.12
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

st.components.v1.html(leaflet_injection_html, height=900, scrolling=False)
