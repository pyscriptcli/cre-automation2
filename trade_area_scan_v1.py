import streamlit as st
import requests
import re
import math
import json

# -----------------------------------------------------------------------------
# 1. BICHROMATIC (NAVY/WHITE) FORCED MODE & TRUE FULL SCREEN OVERRIDES
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TRADE AREA SCAN",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        /* FORCE STRICT BICHROMATIC THEME (NAVY & WHITE ONLY) OVERRIDING ALL SYSTEM SETTINGS */
        :root {
            --navy-brand: #001a3d !important;
            --white-clean: #ffffff !important;
        }
        
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: var(--white-clean) !important;
            color: var(--navy-brand) !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: var(--white-clean) !important;
            color: var(--navy-brand) !important;
            border-right: 2px solid var(--navy-brand) !important;
            width: 320px !important;
            min-width: 320px !important;
            max-width: 320px !important;
            transform: none !important;
            visibility: visible !important;
            overflow: hidden !important;
        }
        
        /* ELIMINATE SIDEBAR COLLAPSE CHEVRON AND SCROLLBARS */
        [data-testid="collapsedControl"] { display: none !important; }
        ::-webkit-scrollbar { width: 0px !important; background: transparent !important; }
        * { scrollbar-width: none !important; -ms-overflow-style: none !important; }
        
        p, span, label, h1, h2, h3, h4, h5, h6, .stMarkdown, [data-testid="stExpander"] summary p {
            color: var(--navy-brand) !important;
        }
        
        /* ELIMINATE STREAMLIT HEADER ZONE */
        [data-testid="stHeader"], header, #stDecoration { display: none !important; }
        
        /* FORCE ROOT FLEX MATRIX */
        [data-testid="stAppViewContainer"] {
            display: flex !important; flex-direction: row !important;
            width: 100vw !important; height: 100vh !important; overflow: hidden !important;
        }
        
        /* LOCK MAIN AREA TO FILL THE EXACT REMAINING SPACE CLEANLY */
        [data-testid="stMain"] {
            flex-grow: 1 !important; width: calc(100vw - 320px) !important;
            height: 100vh !important; overflow: hidden !important; margin: 0px !important; padding: 0px !important;
        }
        
        .block-container, [data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"], .stElementContainer {
            padding: 0px !important; margin: 0px !important; max-width: 100% !important; gap: 0rem !important;
        }
        
        iframe { height: 100vh !important; width: 100% !important; border: none !important; display: block !important; }
        
        [data-testid="stSidebarUserContent"] {
            padding-top: 24px !important; padding-left: 12px !important; padding-right: 12px !important;
            height: 100vh !important; overflow-y: auto !important; overflow-x: hidden !important;
        }
        
        /* BICHROMATIC INPUT RE-STYLING */
        div[data-baseweb="input"], div[data-baseweb="select"], input, select, .stSelectbox, .stTextInput, .stNumberInput {
            background-color: var(--white-clean) !important; color: var(--navy-brand) !important;
            border-radius: 0px !important; border: 1px solid var(--navy-brand) !important; min-height: 32px !important;
        }
        div[data-baseweb="input"]:focus-within { border: 2px solid var(--navy-brand) !important; }
        
        .action-tray div.stButton > button[kind="secondary"], div.stDownloadButton > button {
            background-color: var(--navy-brand) !important; color: var(--white-clean) !important;
            font-weight: 800 !important; font-size: 11px !important; text-transform: uppercase !important;
            border: none !important; border-radius: 0px !important; width: 100% !important; padding: 6px !important;
        }
        .action-tray div.stButton > button[kind="secondary"]:hover, div.stDownloadButton > button:hover {
            background-color: var(--white-clean) !important; color: var(--navy-brand) !important;
            border: 2px solid var(--navy-brand) !important;
        }
        
        [data-testid="stSidebar"] .st-expander {
            border: 1px solid var(--navy-brand) !important; background-color: var(--white-clean) !important;
            border-radius: 0px !important; margin-bottom: 2px !important;
        }
        .stDeployButton, footer { display:none !important; }
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
if 'map_styles' not in st.session_state:
    st.session_state.map_styles = {
        "pin_color": "#001a3d",
        "radius_color": "#001a3d",
        "radius_opacity": 0.1,
        "poi_color": "#001a3d",
        "poi_opacity": 0.9
    }

def execute_global_purge():
    st.session_state.geo_coords = DEFAULT_COORDS
    st.session_state.geo_radius = DEFAULT_RADIUS
    st.session_state.scanned_records = []
    st.session_state.last_scan_lat = 14.6465
    st.session_state.last_scan_lon = 121.0371
    for key in list(st.session_state.keys()):
        if key.startswith("chk_"): st.session_state[key] = False

POI_CONFIG = {
    "COMMERCIAL": [['Corporate Office', '"building"~"office|commercial",i'], ['IT/Tech Center', '"office"~"it|telecommunication",i'], ['Business Center', '"building"="commercial"'], ['Hospital', '"amenity"~"hospital|clinic",i'], ['Hotel', '"tourism"="hotel"'], ['Motel', '"tourism"="motel"']],
    "RETAIL": [['Mall/Dept Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"supermarket|grocery",i'], ['Convenience', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Hardware', '"shop"~"hardware|doityourself",i'], ['General Shops', '"shop"~"boutique|clothes|shoes",i']],
    "FOOD & BEVERAGES": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"'], ['Bar/Pub/Club', '"amenity"~"bar|pub|nightclub",i'], ['Bakery', '"shop"="bakery"']],
    "INDUSTRIAL & LOGISTICS": [
        ['Expressway Exits', '"highway"~"motorway_junction|toll_gantry",i'], 
        ['Ports & Terms', '"industrial"="port"'], 
        ['Mfg Plants', '"industrial"~"factory|manufacturing|processing",i'],
        ['Cold Storage', '"warehouse"~"cold_store|cold_storage",i'],
        ['Ind. Parks', '"landuse"~"industrial|industrial_estate",i'],
        ['Warehouses', '"building"~"warehouse|depot",i'],
        ['Storage Facs', '"building"="storage"'],
        ['Truck Routes', '"hgv"~"designated|yes",i']
    ],
    "GOV & INFRASTRUCTURE": [['City Hall', '"amenity"="townhall"'], ['Police Station', '"amenity"="police"'], ['Fire Station', '"amenity"="fire_station"'], ['Airport', '"aeroway"~"terminal|aerodrome",i']],
    "SCHOOLS": [['University', '"amenity"~"university|college",i'], ['K-12 School', '"amenity"="school"'], ['Vocational', '"amenity"="learning_centre"']]
}

ADVANCED_CONFIG = {
    "AMENITIES": [['ATM', '"amenity"="atm"'], ['Bank', '"amenity"="bank"'], ['Bench', '"amenity"="bench"'], ['Bicycle Parking', '"amenity"="bicycle_parking"'], ['Bicycle Rental', '"amenity"="bicycle_rental"'], ['Cinema', '"amenity"="cinema"'], ['Clinic', '"amenity"="clinic"'], ['Embassy', '"amenity"="embassy"'], ['Firestation', '"amenity"="fire_station"'], ['Fuel', '"amenity"="fuel"'], ['Hospital', '"amenity"="hospital"'], ['Library', '"amenity"="library"'], ['Parking', '"amenity"="parking"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Police', '"amenity"="police"'], ['Post Office', '"amenity"="post_office"'], ['School/College', '"amenity"~"school|college",i'], ['Taxi', '"amenity"="taxi"']],
    "PLACE OF WORSHIP": [['Church', '"religion"="christian"'], ['Mosque', '"religion"="muslim"'], ['Buddhist Temple', '"religion"="buddhist"'], ['Cemetery', '"landuse"="cemetery"']],
    "FOOD & BEVERAGE": [['Bar', '"amenity"="bar"'], ['Cafe', '"amenity"="cafe"'], ['Fast food', '"amenity"="fast_food"'], ['Restaurant', '"amenity"="restaurant"']],
    "MISCELLANEOUS": [['Busstop', '"highway"="bus_stop"'], ['Construction', '"landuse"="construction"'], ['Public camera', '"man_made"="surveillance"']]
}

def compile_features_kml(features):
    kml = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scanned POIs</name>'
    for f in features:
        name = f.get('name', 'Asset').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        class_type = f.get('type', 'Node').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        kml += f"<Placemark><name>{name}</name><description>{class_type}</description><Point><coordinates>{f['lon']},{f['lat']},0</coordinates></Point></Placemark>"
    return kml + '</Document></kml>'

# -----------------------------------------------------------------------------
# 3. SIDEBAR WORKSPACE
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div style="text-align:center; margin-bottom:12px;">', unsafe_allow_html=True)
    if st.button("CLEAR ALL WORKSPACE DATA", use_container_width=True):
        execute_global_purge()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    coords_val = st.text_input("TARGET COORDINATES", key="geo_coords")
    radius_val = st.number_input("RADIUS (METERS)", min_value=100, max_value=50000, key="geo_radius", step=100)

    coord_match = re.match(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", coords_val)
    lat_coord, lon_coord = (float(coord_match.group(1)), float(coord_match.group(2))) if coord_match else (14.6465, 121.0371)

    search_query = st.text_input("FILTER CATALOG", placeholder="Search tags...").lower()
    
    selected_tags = []
    
    for cat_name, node_items in POI_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                cols = st.columns(2)
                for i, (label, tag) in enumerate(matched):
                    with cols[i % 2]:
                        if st.checkbox(label, key=f"chk_{cat_name}_{label}"): 
                            selected_tags.append(tag)

    for cat_name, node_items in ADVANCED_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(f"ADV - {cat_name}", expanded=(len(search_query) > 0)):
                cols = st.columns(2)
                for i, (label, tag) in enumerate(matched):
                    with cols[i % 2]:
                        if st.checkbox(label, key=f"chk_adv_{cat_name}_{label}"): 
                            selected_tags.append(tag)

    st.markdown("<hr style='margin: 10px 0; border: 1px solid #001a3d;'>", unsafe_allow_html=True)
    
    st.markdown('<div class="action-tray">', unsafe_allow_html=True)
    if st.button("RUN SPATIAL SCAN", use_container_width=True):
        if not selected_tags:
            st.error("Select ≥ 1 layer.")
        else:
            url = "https://overpass-api.de/api/interpreter"
            statements = "\n".join([f"  nwr[{tag}](around:{radius_val},{lat_coord},{lon_coord});" for tag in selected_tags])
            ql = f"[out:json][timeout:90];(\n{statements}\n);\nout center;"
            
            with st.spinner("Extracting nodes..."):
                try:
                    res = requests.post(url, data={"data": ql}, headers={"User-Agent": "TradeAreaScan/3.1"}, timeout=100)
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
                except Exception as e: st.sidebar.error("Timeout")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<p style='color:#001a3d; font-size:10px; font-weight:900; margin-top:20px; margin-bottom:4px;'>SYSTEM CONFIGURATION</p>", unsafe_allow_html=True)
    
    # SIDE-BY-SIDE IMPORT & EXPORT MATRIX AT THE BOTTOM
    project_bundle = {
        "geo_coords": coords_val,
        "geo_radius": radius_val,
        "scanned_records": st.session_state.scanned_records,
        "last_scan_lat": st.session_state.last_scan_lat,
        "last_scan_lon": st.session_state.last_scan_lon,
        "map_styles": st.session_state.map_styles
    }
    
    st.download_button("EXPORT PROJECT [JSON]", json.dumps(project_bundle, indent=2), "trade_area_scan.json", "application/json", use_container_width=True)
    st.download_button("EXPORT DATA [KML]", compile_features_kml(st.session_state.scanned_records), "POIs.kml", "application/vnd.google-earth.kml+xml", use_container_width=True)
    
    imported_project = st.file_uploader("IMPORT PROJECT [JSON]", type=["json"], label_visibility="collapsed")
    if imported_project is not None:
        try:
            config_payload = json.load(imported_project)
            st.session_state.geo_coords = config_payload.get("geo_coords", DEFAULT_COORDS)
            st.session_state.geo_radius = config_payload.get("geo_radius", DEFAULT_RADIUS)
            st.session_state.scanned_records = config_payload.get("scanned_records", [])
            st.session_state.last_scan_lat = config_payload.get("last_scan_lat", 14.6465)
            st.session_state.last_scan_lon = config_payload.get("last_scan_lon", 121.0371)
            if "map_styles" in config_payload: st.session_state.map_styles = config_payload["map_styles"]
            st.rerun()
        except: pass

# -----------------------------------------------------------------------------
# 4. ZERO-LATENCY SPATIAL CANVAS (FULL-BLEED SPLIT VIEW)
# -----------------------------------------------------------------------------
geojson_str = json.dumps(st.session_state.scanned_records)
render_lat = lat_coord
render_lon = lon_coord

is_stale = "true" if (lat_coord != st.session_state.last_scan_lat or lon_coord != st.session_state.last_scan_lon) else "false"
style_bundle_str = json.dumps(st.session_state.map_styles)

leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #ffffff; overflow: hidden; font-family: 'Arial', sans-serif; }
        #map { height: 100vh; width: 100%; }
        
        /* GOOGLE MAPS STYLE SEARCH BAR OVERLAY */
        #search-container {
            position: absolute; top: 12px; left: 50px; z-index: 1000; width: 320px;
        }
        #map-search {
            width: 100%; padding: 10px 14px; border: 2px solid #001a3d; border-radius: 0px;
            font-size: 12px; font-weight: bold; color: #001a3d; background: #ffffff; outline: none;
            box-shadow: 0 2px 6px rgba(0,26,61,0.2); box-sizing: border-box;
        }
        #map-search::placeholder { color: rgba(0,26,61,0.5); }
        #search-results {
            position: absolute; top: 38px; left: 0; width: 100%; background: #ffffff;
            border: 2px solid #001a3d; border-top: none; display: none; max-height: 250px;
            overflow-y: auto; box-shadow: 0 4px 8px rgba(0,26,61,0.2); box-sizing: border-box;
        }
        .search-item {
            padding: 10px; font-size: 11px; font-weight: 600; color: #001a3d;
            cursor: pointer; border-bottom: 1px solid rgba(0,26,61,0.1);
        }
        .search-item:hover { background: #001a3d; color: #ffffff; }

        /* FLAT TOOLBAR OVERLAY */
        #map-action-toolbar {
            position: absolute; top: 80px; left: 12px; z-index: 1000;
            display: flex; flex-direction: column; gap: 4px;
        }
        .toolbar-trigger-btn {
            background: #ffffff; width: 32px; height: 32px; border: 2px solid #001a3d;
            display: flex; align-items: center; justify-content: center; cursor: pointer;
            font-size: 16px; color: #001a3d; font-weight: bold; user-select: none;
        }
        .toolbar-trigger-btn:hover { background: #001a3d; color: #ffffff; }
        
        /* FLOATING MENU BLOCKS */
        .toolbar-floating-menu {
            position: absolute; left: 42px; background: #ffffff; border: 2px solid #001a3d;
            padding: 12px; color: #001a3d; width: 180px; display: none; box-shadow: 0 4px 10px rgba(0,26,61,0.15);
        }
        #basemap-menu-container { top: 0px; }
        #style-menu-container { top: 35px; }
        
        .panel-row { margin-bottom: 8px; }
        .panel-row label { display: block; font-size: 9px; font-weight: 900; margin-bottom: 4px; text-transform: uppercase; }
        .panel-row select, .panel-row input[type="text"] {
            width: 100%; font-size: 10px; padding: 4px; border: 1px solid #001a3d; color: #001a3d; background: #ffffff; font-weight: bold;
        }
        .style-slider-input { width: 100%; margin: 4px 0 0 0; cursor: pointer; }

        /* BICHROMATIC SCAN RESULTS PANEL */
        #scan-results-panel {
            position: absolute; top: 12px; right: 12px; z-index: 1000; background: #ffffff;
            width: 280px; max-height: calc(100vh - 40px); border: 2px solid #001a3d;
            display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 15px rgba(0,26,61,0.2);
        }
        .results-header {
            background: #001a3d; color: #ffffff; padding: 10px 12px; font-size: 10px; font-weight: 900;
            display: flex; justify-content: space-between; align-items: center; text-transform: uppercase;
        }
        .results-list { overflow-y: auto; flex-grow: 1; }
        .layer-category-block { border-bottom: 1px solid #001a3d; }
        .layer-category-header {
            background: #ffffff; padding: 8px 10px; display: flex; align-items: center; justify-content: space-between;
            cursor: pointer; user-select: none; border-bottom: 1px solid rgba(0,26,61,0.2);
        }
        .layer-category-header:hover { background: rgba(0,26,61,0.05); }
        .layer-header-left { display: flex; align-items: center; gap: 8px; font-size: 11px; font-weight: 900; color: #001a3d; }
        .layer-header-left input[type="checkbox"] { margin: 0; cursor: pointer; }
        
        .layer-category-items { padding: 0; }
        .layer-category-items.collapsed { display: none !important; }
        
        .results-item {
            padding: 6px 12px 6px 30px; font-size: 10px; font-weight: bold; color: #001a3d;
            cursor: pointer; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .results-item:hover { background: #001a3d; color: #ffffff; }

        /* RIGHT CLICK CONTEXT PANEL VIEWER */
        #right-viewer-panel {
            position: absolute; top: 12px; right: 302px; z-index: 1001; background: #ffffff;
            width: 450px; height: calc(100vh - 24px); border: 2px solid #001a3d;
            display: none; flex-direction: column; box-shadow: -4px 0 15px rgba(0,26,61,0.2);
        }
        .viewer-header {
            background: #001a3d; color: #ffffff; padding: 10px 12px; font-weight: 900; font-size: 11px;
            display: flex; justify-content: space-between; text-transform: uppercase;
        }
        .viewer-header a { color: #ffffff !important; text-decoration: none; font-weight: 900; margin-right: 15px; border: 1px solid #ffffff; padding: 2px 6px; }
        .viewer-header span.close-btn { cursor: pointer; font-size: 14px; }
        #viewer-iframe { flex-grow: 1; border: none; width: 100%; }

        .poi-text-label {
            background: #ffffff; border: 1px solid #001a3d; padding: 2px 4px; font-size: 9px; font-weight: 900; color: #001a3d; white-space: nowrap;
        }
        .hide-labels .poi-text-label { display: none !important; }
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div id="search-container">
        <input type="text" id="map-search" placeholder="Search location globally..." onkeyup="handleSearch(event)">
        <div id="search-results"></div>
    </div>

    <div id="map-action-toolbar">
        <div class="toolbar-trigger-btn" title="Basemap Settings" onclick="toggleMenuPanel('basemap-menu-container')">▤</div>
        <div class="toolbar-trigger-btn" title="Style Controls" onclick="toggleMenuPanel('style-menu-container')">✎</div>
    </div>
    
    <div id="basemap-menu-container" class="toolbar-floating-menu">
        <div class="panel-row">
            <label>Map Raster View</label>
            <select id="basemap-select" onchange="switchActiveBasemap(this.value)">
                <option value="osm">OSM Standard</option>
                <option value="satellite">Google Satellite</option>
                <option value="carto">Carto Light</option>
            </select>
        </div>
        <div class="panel-row" style="display:flex; align-items:center; gap:6px; margin-top:8px;">
            <input type="checkbox" id="label-toggle-chk" style="margin:0;" onchange="toggleLabelsMatrix(this.checked)">
            <label style="margin:0; cursor:pointer;" for="label-toggle-chk">Show Text Labels</label>
        </div>
    </div>
    
    <div id="style-menu-container" class="toolbar-floating-menu">
        <div class="panel-row">
            <label>Radius Visual Opacity</label>
            <input type="range" id="opac-radius-slider" class="style-slider-input" min="0" max="1" step="0.05" oninput="setCustomElementOpacity('radius', this.value)">
        </div>
        <div class="panel-row">
            <label>POI Visual Opacity</label>
            <input type="range" id="opac-poi-slider" class="style-slider-input" min="0" max="1" step="0.05" oninput="setCustomElementOpacity('poi', this.value)">
        </div>
        <div class="panel-row" style="margin-top:10px; font-size:8px; font-weight:bold;">
            * BICHROMATIC LOCK ACTIVE: All elements restricted to pure Navy & White.
        </div>
    </div>

    <div id="scan-results-panel">
        <div class="results-header">
            <span>Scan Index</span>
            <span id="results-count">0</span>
        </div>
        <div class="results-list" id="results-list-box"></div>
    </div>

    <div id="right-viewer-panel">
        <div class="viewer-header">
            <span id="viewer-title">VIEWER</span>
            <div>
                <a id="viewer-ext-link" href="#" target="_blank">⤢ OPEN NEW TAB</a>
                <span class="close-btn" onclick="closeViewer()">✖</span>
            </div>
        </div>
        <iframe id="viewer-iframe" src=""></iframe>
    </div>

    <script>
        const map = L.map('map', { zoomControl: true, attributionControl: false }).setView([__LAT__, __LON__], 14);
        
        const basemaps = {
            osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }),
            satellite: L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', { maxZoom: 20 }),
            carto: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 })
        };
        
        let p_radiusOpac = 0.1;
        let p_poiOpac = 0.9;
        document.getElementById('opac-radius-slider').value = p_radiusOpac;
        document.getElementById('opac-poi-slider').value = p_poiOpac;

        let activeBasemapKey = localStorage.getItem('ts_persistent_basemap') || 'osm';
        if (!basemaps[activeBasemapKey]) activeBasemapKey = 'osm';
        document.getElementById('basemap-select').value = activeBasemapKey;
        basemaps[activeBasemapKey].addTo(map);
        
        function switchActiveBasemap(targetKey) {
            map.removeLayer(basemaps[activeBasemapKey]);
            basemaps[targetKey].addTo(map);
            activeBasemapKey = targetKey;
            localStorage.setItem('ts_persistent_basemap', targetKey);
        }
        
        let labelsActive = localStorage.getItem('ts_persistent_labels') !== 'false';
        document.getElementById('label-toggle-chk').checked = labelsActive;
        if (!labelsActive) document.getElementById('map').classList.add('hide-labels');
        
        function toggleLabelsMatrix(isShown) {
            if (isShown) document.getElementById('map').classList.remove('hide-labels');
            else document.getElementById('map').classList.add('hide-labels');
            localStorage.setItem('ts_persistent_labels', isShown);
        }
        
        function toggleMenuPanel(panelId) {
            const el = document.getElementById(panelId);
            const activeNow = el.style.display === 'block';
            document.querySelectorAll('.toolbar-floating-menu').forEach(p => p.style.display = 'none');
            if (!activeNow) el.style.display = 'block';
        }
        
        let searchTimeout;
        function handleSearch(e) {
            clearTimeout(searchTimeout);
            const q = e.target.value;
            if (q.length < 3) { document.getElementById('search-results').style.display = 'none'; return; }
            searchTimeout = setTimeout(() => {
                fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}`)
                .then(res => res.json())
                .then(data => {
                    const resDiv = document.getElementById('search-results');
                    resDiv.innerHTML = '';
                    if(data.length > 0) {
                        data.forEach(item => {
                            const div = document.createElement('div');
                            div.className = 'search-item'; div.innerText = item.display_name;
                            div.onclick = () => {
                                const newLat = parseFloat(item.lat); const newLon = parseFloat(item.lon);
                                map.flyTo([newLat, newLon], 15);
                                centerMarker.setLatLng([newLat, newLon]);
                                radiusCircle.setLatLng([newLat, newLon]);
                                resDiv.style.display = 'none';
                                document.getElementById('map-search').value = item.display_name;
                            };
                            resDiv.appendChild(div);
                        });
                        resDiv.style.display = 'block';
                    } else { resDiv.style.display = 'none'; }
                });
            }, 400);
        }
        
        const centerMarker = L.circleMarker([__LAT__, __LON__], {
            radius: 8, fillColor: "#ffffff", color: "#001a3d", weight: 3, opacity: 1, fillOpacity: 1
        }).addTo(map).bindPopup("<b>TARGET COORDINATES</b>");
        
        const radiusCircle = L.circle([__LAT__, __LON__], {
            radius: __RADIUS__, color: "#001a3d", weight: 2, fillColor: "#001a3d", fillOpacity: p_radiusOpac
        }).addTo(map);
        
        const pts = __GEOJSON__;
        const categoryMap = {};
        const layerGroupsRef = {};
        
        pts.forEach(p => {
            const layerKey = p.type || 'Unclassified';
            if (!categoryMap[layerKey]) categoryMap[layerKey] = [];
            categoryMap[layerKey].push(p);
        });
        
        Object.keys(categoryMap).forEach(key => {
            layerGroupsRef[key] = L.layerGroup().addTo(map);
            categoryMap[key].forEach(p => {
                const marker = L.circleMarker([p.lat, p.lon], {
                    radius: 5, fillColor: "#001a3d", color: "#ffffff", weight: 1, opacity: 1, fillOpacity: p_poiOpac
                }).bindPopup("<b style='color:#001a3d;'>" + p.name + "</b><br>" + p.type);
                
                if (p.name && p.name !== 'Unknown') {
                    marker.bindTooltip(p.name, {
                        permanent: true, direction: 'top', offset: [0, -4], className: 'poi-text-label'
                    });
                }
                marker.addTo(layerGroupsRef[key]);
            });
        });

        const listBox = document.getElementById('results-list-box');
        document.getElementById('results-count').innerText = pts.length;
        
        if (pts.length > 0) {
            let htmlPayload = '';
            Object.keys(categoryMap).forEach(catName => {
                htmlPayload += `
                    <div class="layer-category-block">
                        <div class="layer-category-header" onclick="toggleAccordionCollapse('${catName}')">
                            <div class="layer-header-left">
                                <input type="checkbox" checked onclick="event.stopPropagation(); toggleCategoryVisibility('${catName}', this.checked)">
                                <span>${catName} (${categoryMap[catName].length})</span>
                            </div>
                            <span id="chevron-${catName}">▼</span>
                        </div>
                        <div class="layer-category-items" id="items-${catName}">
                `;
                categoryMap[catName].forEach(p => {
                    htmlPayload += `<div class="results-item" onclick="flyToAndHighlightPoint(${p.lat}, ${p.lon})">${p.name || 'Unknown'}</div>`;
                });
                htmlPayload += '</div></div>';
            });
            listBox.innerHTML = htmlPayload;
        }

        function toggleCategoryVisibility(catKey, isVisible) {
            if (isVisible) map.addLayer(layerGroupsRef[catKey]);
            else map.removeLayer(layerGroupsRef[catKey]);
        }

        function toggleAccordionCollapse(catKey) {
            const panel = document.getElementById('items-' + catKey);
            const chev = document.getElementById('chevron-' + catKey);
            if (panel.classList.contains('collapsed')) {
                panel.classList.remove('collapsed'); chev.innerText = '▼';
            } else {
                panel.classList.add('collapsed'); chev.innerText = '▲';
            }
        }

        function flyToAndHighlightPoint(lat, lon) {
            map.flyTo([lat, lon], 17);
            map.eachLayer(layer => {
                if (layer instanceof L.CircleMarker && layer.getLatLng) {
                    const loc = layer.getLatLng();
                    if (Math.abs(loc.lat - lat) < 0.00001 && Math.abs(loc.lng - lon) < 0.00001) {
                        setTimeout(() => layer.openPopup(), 300);
                    }
                }
            });
        }

        function setCustomElementOpacity(layerType, val) {
            const opac = parseFloat(val);
            if (layerType === 'radius') {
                radiusCircle.setStyle({ fillOpacity: opac });
            } else if (layerType === 'poi') {
                Object.keys(layerGroupsRef).forEach(k => {
                    layerGroupsRef[k].eachLayer(m => m.setStyle({ fillOpacity: opac }));
                });
            }
        }
        
        // CONTEXT MENU (RIGHT CLICK)
        map.on('contextmenu', function(e) {
            const lat = e.latlng.lat; const lng = e.latlng.lng;
            const coordStr = lat.toFixed(5) + ", " + lng.toFixed(5);
            
            const menuHtml = `
                <div style="font-family: Arial; font-size: 11px; color: #001a3d; min-width: 130px;">
                    <div style="font-weight: 900; border-bottom: 2px solid #001a3d; padding-bottom: 5px; margin-bottom: 5px;">MAP ACTIONS</div>
                    <div style="padding: 5px 0; cursor: pointer; font-weight: bold;" onclick="navigator.clipboard.writeText('${coordStr}'); alert('Copied: ${coordStr}'); map.closePopup();">◧ COPY COORDINATES</div>
                    <div style="padding: 5px 0; cursor: pointer; font-weight: bold;" onclick="openRightPanel('routes', ${lat}, ${lng}); map.closePopup();">↱ OPEN ROUTES</div>
                    <div style="padding: 5px 0; cursor: pointer; font-weight: bold;" onclick="openRightPanel('streetview', ${lat}, ${lng}); map.closePopup();">👁 OPEN STREETVIEW</div>
                </div>
            `;
            L.popup().setLatLng(e.latlng).setContent(menuHtml).openOn(map);
        });

        function openRightPanel(type, lat, lng) {
            const panel = document.getElementById('right-viewer-panel');
            const iframe = document.getElementById('viewer-iframe');
            const extLink = document.getElementById('viewer-ext-link');
            document.getElementById('viewer-title').innerText = type.toUpperCase();
            
            if(type === 'routes') {
                iframe.src = `https://maps.google.com/maps?q=${lat},${lng}&output=embed`;
                extLink.href = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
            } else {
                iframe.src = `https://maps.google.com/maps?q=${lat},${lng}&layer=c&cbll=${lat},${lng}&output=svembed`;
                extLink.href = `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${lat},${lng}`;
            }
            panel.style.display = 'flex';
        }
        function closeViewer() {
            document.getElementById('right-viewer-panel').style.display = 'none';
            document.getElementById('viewer-iframe').src = "";
        }
        
        if (pts.length > 0 && !__IS_STALE__) {
            const bounds = L.featureGroup([L.marker([__LAT__, __LON__]), ...pts.map(p => L.marker([p.lat, p.lon]))]).getBounds();
            map.fitBounds(bounds.pad(0.1));
        } else { map.setView([__LAT__, __LON__], 15); }
        setTimeout(() => map.invalidateSize(), 200);
    </script>
</body>
</html>
"""

leaflet_html = (leaflet_template
                .replace("__LAT__", str(render_lat))
                .replace("__LON__", str(render_lon))
                .replace("__RADIUS__", str(radius_val))
                .replace("__IS_STALE__", is_stale)
                .replace("__GEOJSON__", geojson_str))

st.components.v1.html(leaflet_html, scrolling=False)
