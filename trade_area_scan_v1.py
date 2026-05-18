import streamlit as st
import requests
import re
import math
import json
import pandas as pd

# -----------------------------------------------------------------------------
# 1. HIGH-DENSITY LIGHT MODE & HYPERLINK OVERRIDES
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
            --border-gray: #cbd5e1;
            --text-muted: #475569;
        }
        
        /* Maximize primary viewport space */
        .block-container {
            padding: 0rem !important;
        }
        
        /* Compressed Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: var(--white-clean) !important;
            color: var(--navy-brand) !important;
            border-right: 1px solid var(--border-gray) !important;
            width: 320px !important; /* Force slimmer sidebar ratio */
        }
        
        [data-testid="stSidebarUserContent"] {
            padding-top: 16px !important;
            padding-left: 12px !important;
            padding-right: 12px !important;
        }
        
        /* Centered Header Element */
        .sidebar-title {
            color: var(--navy-brand) !important;
            font-size: 24px !important;
            font-weight: 900 !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
            text-align: center !important;
            margin-bottom: 2px !important;
            font-family: 'Arial', sans-serif !important;
        }
        
        /* Hyperlink Emulation for the Clear Button */
        div.clear-link-wrapper div.stButton > button {
            background: transparent !important;
            border: none !important;
            color: var(--text-muted) !important;
            text-decoration: underline !important;
            font-weight: 700 !important;
            font-size: 10px !important;
            text-transform: uppercase !important;
            padding: 0 !important;
            width: 100% !important;
            box-shadow: none !important;
            text-align: center !important;
            margin-bottom: 15px !important;
        }
        div.clear-link-wrapper div.stButton > button:hover {
            color: var(--navy-brand) !important;
        }
        
        /* Compressed Widget Sizing */
        [data-testid="stSidebar"] label p {
            color: var(--navy-brand) !important;
            font-weight: 800 !important;
            font-size: 10px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            margin-bottom: -6px !important;
        }
        
        div[data-baseweb="input"], div[data-baseweb="select"], .stSelectbox, .stTextInput, .stNumberInput {
            border-radius: 4px !important;
            min-height: 32px !important; /* Squeeze vertical height */
        }
        
        div[data-baseweb="input"] { border: 1px solid var(--border-gray) !important; }
        div[data-baseweb="input"]:focus-within { border-color: var(--navy-brand) !important; }
        div[data-baseweb="select"] { border: 1px solid var(--border-gray) !important; }
        
        /* Primary Action Buttons */
        .action-tray div.stButton > button, div.stDownloadButton > button {
            background-color: var(--navy-brand) !important;
            color: var(--white-clean) !important;
            font-weight: 800 !important;
            font-size: 11px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            border: none !important;
            border-radius: 6px !important;
            width: 100% !important;
            padding: 6px !important;
            transition: all 0.1s ease-in-out !important;
            margin-top: 5px !important;
        }
        .action-tray div.stButton > button:hover, div.stDownloadButton > button:hover {
            background-color: var(--gold-accent) !important;
            color: var(--navy-brand) !important;
        }
        
        /* Compact Expander Panels */
        [data-testid="stSidebar"] .st-expander {
            border: 1px solid var(--border-gray) !important;
            background-color: #f8fafc !important;
            border-radius: 4px !important;
            margin-bottom: 2px !important;
        }
        [data-testid="stSidebar"] .st-expander details summary {
            padding-top: 4px !important;
            padding-bottom: 4px !important;
        }
        
        .stDeployButton, footer, #stDecoration { display:none !important; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. STATE PERSISTENCE & DATA MODELS
# -----------------------------------------------------------------------------
DEFAULT_COORDS = "14.6465, 121.0371"
DEFAULT_RADIUS = 1000

if 'geo_coords' not in st.session_state: st.session_state.geo_coords = DEFAULT_COORDS
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = DEFAULT_RADIUS
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'last_scan_lat' not in st.session_state: st.session_state.last_scan_lat = 14.6465
if 'last_scan_lon' not in st.session_state: st.session_state.last_scan_lon = 121.0371

def execute_global_purge():
    st.session_state.geo_coords = DEFAULT_COORDS
    st.session_state.geo_radius = DEFAULT_RADIUS
    st.session_state.scanned_records = []
    st.session_state.last_scan_lat = 14.6465
    st.session_state.last_scan_lon = 121.0371
    for key in list(st.session_state.keys()):
        if key.startswith("chk_"): st.session_state[key] = False

POI_CONFIG = {
    "COMMERCIAL": [['Corporate Office', '"building"~"office|commercial",i'], ['Business Center', '"building"="commercial"'], ['Hospital', '"amenity"~"hospital|clinic",i'], ['Hotel', '"tourism"="hotel"']],
    "RETAIL": [['Mall', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"supermarket|grocery",i'], ['Convenience', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"']],
    "FOOD & BEVERAGE": [['Restaurant', '"amenity"="restaurant"'], ['Cafe', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"']],
    "LOGISTICS": [['Exits', '"highway"~"motorway_junction|toll_gantry",i'], ['Ports', '"industrial"="port"'], ['Manufacturing', '"industrial"~"factory|processing",i'], ['Warehouses', '"building"~"warehouse|depot",i']]
}

# -----------------------------------------------------------------------------
# 3. KML COMPILATION ENGINES
# -----------------------------------------------------------------------------
def compile_radius_kml(lat, lon, r_meters):
    kml = f'<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scan Radius</name><Placemark><name>Buffer Zone</name><Style><LineStyle><color>ff3d1a00</color><width>3</width></LineStyle><PolyStyle><fill>0</fill></PolyStyle></Style><Polygon><outerBoundaryIs><LinearRing><coordinates>'
    for i in range(37):
        angle = (i * 10) * math.pi / 180
        d_lat = (r_meters / 6371000) * math.cos(angle)
        d_lon = (r_meters / (6371000 * math.cos(lat * math.pi / 180))) * math.sin(angle)
        kml += f"{lon + (d_lon * 180 / math.pi)},{lat + (d_lat * 180 / math.pi)},0 "
    return kml + '</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></Document></kml>'

def compile_features_kml(features):
    kml = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scanned POIs</name>'
    for f in features:
        name = f.get('name', 'Asset').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        class_type = f.get('type', 'Node').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        kml += f"<Placemark><name>{name}</name><description>{class_type}</description><Point><coordinates>{f['lon']},{f['lat']},0</coordinates></Point></Placemark>"
    return kml + '</Document></kml>'

# -----------------------------------------------------------------------------
# 4. SIDEBAR WORKSPACE COMPRESSION
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">TRADE AREA SCAN</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="clear-link-wrapper">', unsafe_allow_html=True)
    if st.button("Clear All Parameters", key="master_purge_btn"):
        execute_global_purge()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    coords_val = st.text_input("Target Coordinates", key="geo_coords")
    radius_val = st.number_input("Radius (Meters)", min_value=100, max_value=50000, key="geo_radius", step=100)

    coord_match = re.match(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", coords_val)
    lat_coord, lon_coord = (float(coord_match.group(1)), float(coord_match.group(2))) if coord_match else (14.6465, 121.0371)

    search_query = st.text_input("Filter Catalog", placeholder="Search tags...").lower()
    
    selected_tags = []
    for cat_name, node_items in POI_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for label, tag in matched:
                    if st.checkbox(label, key=f"chk_{cat_name}_{label}"): selected_tags.append(tag)

    st.markdown("<hr style='margin: 10px 0; border-color: #cbd5e1;'>", unsafe_allow_html=True)
    
    st.markdown('<div class="action-tray">', unsafe_allow_html=True)
    if st.button("🚀 SCAN AREA PROFILE", use_container_width=True):
        if not selected_tags:
            st.error("Select ≥ 1 layer.")
        else:
            url = "https://overpass-api.de/api/interpreter"
            statements = "\n".join([f"  nwr[{tag}](around:{radius_val},{lat_coord},{lon_coord});" for tag in selected_tags])
            ql = f"[out:json][timeout:90];(\n{statements}\n);\nout center;"
            
            with st.spinner("Extracting nodes..."):
                try:
                    res = requests.post(url, data={"data": ql}, headers={"User-Agent": "TradeAreaScan/3.0"}, timeout=100)
                    if res.status_code == 200:
                        records = []
                        for el in res.json().get('elements', []):
                            e_lat = el.get('lat') or el.get('center', {}).get('lat')
                            e_lon = el.get('lon') or el.get('center', {}).get('lon')
                            if e_lat and e_lon:
                                tags = el.get('tags', {})
                                records.append({"lat": e_lat, "lon": e_lon, "name": tags.get('name', 'Unknown'), "type": tags.get('amenity') or tags.get('shop') or tags.get('building') or 'Node'})
                        st.session_state.scanned_records = records
                        st.session_state.last_scan_lat = lat_coord
                        st.session_state.last_scan_lon = lon_coord
                        st.rerun()
                    else: st.sidebar.error(f"Error {res.status_code}")
                except Exception as e: st.sidebar.error("Timeout")
    st.markdown('</div>', unsafe_allow_html=True)

    # Export Handlers
    st.markdown("<p style='color:#001a3d; font-size:10px; font-weight:800; margin-top:15px; margin-bottom:0;'>DATA EXPORTS</p>", unsafe_allow_html=True)
    exp_fmt = st.selectbox("Format", ["Select...", "Radius (KML)", "Scanned POIs (KML)", "Scanned POIs (CSV)"], label_visibility="collapsed")
    
    if exp_fmt == "Radius (KML)":
        st.download_button("Download", compile_radius_kml(lat_coord, lon_coord, radius_val), f"Radius_{radius_val}m.kml", "application/vnd.google-earth.kml+xml")
    elif exp_fmt == "Scanned POIs (KML)":
        st.download_button("Download", compile_features_kml(st.session_state.scanned_records), "POIs.kml", "application/vnd.google-earth.kml+xml", disabled=not st.session_state.scanned_records)
    elif exp_fmt == "Scanned POIs (CSV)":
        csv_data = pd.DataFrame(st.session_state.scanned_records).to_csv(index=False).encode('utf-8') if st.session_state.scanned_records else b""
        st.download_button("Download", csv_data, "POIs.csv", "text/csv", disabled=not st.session_state.scanned_records)

# -----------------------------------------------------------------------------
# 5. ZERO-LATENCY SPATIAL CANVAS (LEAFLET NATIVE)
# -----------------------------------------------------------------------------
# We utilize standard map tiles natively to strip the editor panel entirely.
geojson_str = json.dumps(st.session_state.scanned_records)
render_lat = st.session_state.last_scan_lat
render_lon = st.session_state.last_scan_lon

leaflet_html = f"""
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>body, html, #map {{ margin: 0; padding: 0; height: 100vh; width: 100vw; background: #f8fafc; }}</style>
</head>
<body>
    <div id="map"></div>
    <script>
        const map = L.map('map', {{ zoomControl: true, attributionControl: false }}).setView([{render_lat}, {render_lon}], 14);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ maxZoom: 19 }}).addTo(map);
        
        // Pinned Red Target Coordinate Marker
        L.circleMarker([{render_lat}, {render_lon}], {{
            radius: 7, fillColor: "#e11d48", color: "#ffffff", weight: 2, opacity: 1, fillOpacity: 1
        }}).addTo(map).bindPopup("<b>TARGET COORDINATES</b>");
        
        // Meter-Accurate Radius Ring Geofence
        L.circle([{render_lat}, {render_lon}], {{
            radius: {radius_val}, color: "#001a3d", weight: 2, fillColor: "#001a3d", fillOpacity: 0.1
        }}).addTo(map);
        
        const pts = {geojson_str};
        pts.forEach(p => {{
            L.circleMarker([p.lat, p.lon], {{
                radius: 5, fillColor: "#d4af37", color: "#001a3d", weight: 1, opacity: 1, fillOpacity: 0.9
            }}).addTo(map).bindPopup("<b>" + p.name + "</b><br>" + p.type);
        }});
        
        if(pts.length > 0) {{
            const bounds = L.featureGroup([L.marker([{render_lat}, {render_lon}]), ...pts.map(p => L.marker([p.lat, p.lon]))]).getBounds();
            map.fitBounds(bounds.pad(0.1));
        }}
        
        setTimeout(() => map.invalidateSize(), 200);
    </script>
</body>
</html>
"""

st.components.v1.html(leaflet_html, height=900, scrolling=False)
