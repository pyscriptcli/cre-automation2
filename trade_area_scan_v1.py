import streamlit as st
import requests
import re
import math
import json

# -----------------------------------------------------------------------------
# 1. SOFT BICHROMATIC THEME & TRUE FULL SCREEN OVERRIDES
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TRADE AREA SCAN",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        /* FORCE STRICT BICHROMATIC THEME WITH MODERN TACTILE GEOMETRY */
        :root {
            --navy-brand: #001a3d !important;
            --white-clean: #ffffff !important;
            --soft-shadow: 0 4px 16px rgba(0, 26, 61, 0.12) !important;
        }
        
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: var(--white-clean) !important;
            color: var(--navy-brand) !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: var(--white-clean) !important;
            color: var(--navy-brand) !important;
            border-right: 1px solid rgba(0, 26, 61, 0.1) !important;
            width: 320px !important;
            min-width: 320px !important;
            max-width: 320px !important;
            transform: none !important;
            visibility: visible !important;
            overflow: hidden !important;
            box-shadow: 2px 0 10px rgba(0, 26, 61, 0.05) !important;
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
            padding-top: 24px !important; padding-left: 16px !important; padding-right: 16px !important;
            height: 100vh !important; overflow-y: auto !important; overflow-x: hidden !important;
        }
        
        /* ROUNDED BICHROMATIC INPUT RE-STYLING */
        div[data-baseweb="input"], div[data-baseweb="select"], input, select, .stSelectbox, .stTextInput, .stNumberInput {
            background-color: var(--white-clean) !important; color: var(--navy-brand) !important;
            border-radius: 8px !important; border: 1px solid rgba(0, 26, 61, 0.3) !important; min-height: 36px !important;
            box-shadow: inset 0 1px 3px rgba(0, 26, 61, 0.05) !important;
        }
        div[data-baseweb="input"]:focus-within { border: 2px solid var(--navy-brand) !important; box-shadow: var(--soft-shadow) !important; }
        
        /* ROUNDED BUTTONS */
        .action-tray div.stButton > button[kind="secondary"], div.stDownloadButton > button {
            background-color: var(--navy-brand) !important; color: var(--white-clean) !important;
            font-weight: 800 !important; font-size: 11px !important; text-transform: uppercase !important;
            border: none !important; border-radius: 8px !important; width: 100% !important; padding: 10px !important;
            box-shadow: var(--soft-shadow) !important; transition: all 0.2s ease !important;
        }
        .action-tray div.stButton > button[kind="secondary"]:hover, div.stDownloadButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(0, 26, 61, 0.2) !important;
        }
        
        /* ROUNDED EXPANDERS */
        [data-testid="stSidebar"] .st-expander {
            border: 1px solid rgba(0, 26, 61, 0.15) !important; background-color: var(--white-clean) !important;
            border-radius: 8px !important; margin-bottom: 6px !important; overflow: hidden !important;
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
    st.markdown('<div style="color: #001a3d; font-size: 22px; font-weight: 900; letter-spacing: 1px; margin-bottom: 24px; text-align: center;">TRADE AREA SCAN</div>', unsafe_allow_html=True)
    
    coords_val = st.text_input("TARGET COORDINATES", key="geo_coords")
    radius_val = st.number_input("RADIUS (METERS)", min_value=100, max_value=50000, key="geo_radius", step=100)

    coord_match = re.match(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", coords_val)
    lat_coord, lon_coord = (float(coord_match.group(1)), float(coord_match.group(2))) if coord_match else (14.6465, 121.0371)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
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

    st.markdown("<hr style='margin: 16px 0; border: 0; border-top: 1px solid rgba(0, 26, 61, 0.1);'>", unsafe_allow_html=True)
    
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

    st.markdown("<p style='color:#001a3d; font-size:10px; font-weight:900; margin-top:24px; margin-bottom:8px; text-transform: uppercase;'>System Config</p>", unsafe_allow_html=True)
    
    project_bundle = {
        "geo_coords": coords_val,
        "geo_radius": radius_val,
        "scanned_records": st.session_state.scanned_records,
        "last_scan_lat": st.session_state.last_scan_lat,
        "last_scan_lon": st.session_state.last_scan_lon,
        "map_styles": st.session_state.map_styles
    }
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("EXPORT PROJECT", json.dumps(project_bundle, indent=2), "trade_area_scan.json", "application/json", use_container_width=True)
    with col2:
        st.download_button("EXPORT KML", compile_features_kml(st.session_state.scanned_records), "POIs.kml", "application/vnd.google-earth.kml+xml", use_container_width=True)
    
    imported_project = st.file_uploader("IMPORT PROJECT [JSON]", type=["json"], label_visibility="collapsed")
    if imported_project is not None:
        try:
            config_payload = json.load(imported_project)
            st.session_state.geo_coords = config_payload.get("geo_coords", DEFAULT_COORDS)
            st.session_state.geo_radius = config_payload.get("geo_radius", DEFAULT_RADIUS)
            st.session_state.scanned_records = config_payload.get("scanned_records", [])
            st.session_state.last_scan_lat = config_payload.get("last_scan_lat", 14.6465)
            st.session_state.last_scan_lon = config_payload.get("last_scan_lon", 121.0371)
            st.rerun()
        except: pass

# -----------------------------------------------------------------------------
# 4. ZERO-LATENCY SPATIAL CANVAS (FULL-BLEED SPLIT VIEW)
# -----------------------------------------------------------------------------
geojson_str = json.dumps(st.session_state.scanned_records)
render_lat = lat_coord
render_lon = lon_coord
is_stale = "true" if (lat_coord != st.session_state.last_scan_lat or lon_coord != st.session_state.last_scan_lon) else "false"

leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #ffffff; overflow: hidden; font-family: 'Arial', sans-serif; }
        #map { height: 100vh; width: 100%; }
        
        /* ROUNDED GOOGLE MAPS STYLE SEARCH BAR OVERLAY */
        #search-container {
            position: absolute; top: 16px; left: 60px; z-index: 1000; width: 340px;
        }
        #map-search {
            width: 100%; padding: 12px 16px; border: 1px solid rgba(0, 26, 61, 0.2); border-radius: 8px;
            font-size: 13px; font-weight: bold; color: #001a3d; background: #ffffff; outline: none;
            box-shadow: 0 4px 12px rgba(0, 26, 61, 0.1); box-sizing: border-box; transition: all 0.2s ease;
        }
        #map-search:focus { border: 2px solid #001a3d; box-shadow: 0 6px 16px rgba(0, 26, 61, 0.15); }
        #map-search::placeholder { color: rgba(0,26,61,0.4); font-weight: normal; }
        
        #search-results {
            position: absolute; top: 50px; left: 0; width: 100%; background: #ffffff;
            border-radius: 8px; display: none; max-height: 250px; overflow-y: auto; 
            box-shadow: 0 6px 20px rgba(0, 26, 61, 0.15); border: 1px solid rgba(0, 26, 61, 0.1); margin-top: 8px;
            box-sizing: border-box;
        }
        .search-item {
            padding: 12px 16px; font-size: 12px; font-weight: 600; color: #001a3d;
            cursor: pointer; border-bottom: 1px solid rgba(0,26,61,0.05); transition: background 0.1s;
        }
        .search-item:last-child { border-bottom: none; }
        .search-item:hover { background: #001a3d; color: #ffffff; }

        /* ROUNDED FLAT TOOLBAR OVERLAY */
        #map-action-toolbar {
            position: absolute; top: 80px; left: 16px; z-index: 1000;
            display: flex; flex-direction: column; gap: 8px;
        }
        .toolbar-trigger-btn {
            background: #ffffff; width: 34px; height: 34px; border-radius: 8px; border: 1px solid rgba(0, 26, 61, 0.2);
            display: flex; align-items: center; justify-content: center; cursor: pointer;
            font-size: 16px; color: #001a3d; font-weight: bold; user-select: none; box-shadow: 0 4px 12px rgba(0, 26, 61, 0.1);
            transition: all 0.2s;
        }
        .toolbar-trigger-btn:hover { background: #001a3d; color: #ffffff; transform: scale(1.05); }
        
        /* ROUNDED FLOATING MENU BLOCKS */
        .toolbar-floating-menu {
            position: absolute; left: 46px; background: #ffffff; border-radius: 8px; border: 1px solid rgba(0, 26, 61, 0.1);
            padding: 16px; color: #001a3d; width: 200px; display: none; box-shadow: 0 8px 24px rgba(0, 26, 61, 0.12);
        }
        #basemap-menu-container { top: 0px; }
        
        .panel-row { margin-bottom: 12px; }
        .panel-row:last-child { margin-bottom: 0; }
        .panel-row label { display: block; font-size: 10px; font-weight: 900; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px;}
        .panel-row select {
            width: 100%; font-size: 11px; padding: 6px; border-radius: 6px; border: 1px solid rgba(0, 26, 61, 0.3); color: #001a3d; background: #ffffff; font-weight: bold; cursor: pointer; outline: none;
        }
        .panel-row select:focus { border-color: #001a3d; }

        /* ROUNDED BICHROMATIC SCAN RESULTS PANEL */
        #scan-results-panel {
            position: absolute; top: 16px; right: 16px; z-index: 1000; background: #ffffff;
            width: 280px; max-height: calc(100vh - 40px); border-radius: 12px; border: 1px solid rgba(0, 26, 61, 0.1);
            display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 8px 30px rgba(0, 26, 61, 0.15);
        }
        .results-header {
            background: #001a3d; color: #ffffff; padding: 14px 16px; font-size: 11px; font-weight: 900;
            display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; letter-spacing: 1px;
        }
        .results-list { overflow-y: auto; flex-grow: 1; padding-bottom: 8px; }
        .layer-category-block { border-bottom: 1px solid rgba(0, 26, 61, 0.05); }
        .layer-category-block:last-child { border-bottom: none; }
        .layer-category-header {
            background: #ffffff; padding: 10px 16px; display: flex; align-items: center; justify-content: space-between;
            cursor: pointer; user-select: none; transition: background 0.2s;
        }
        .layer-category-header:hover { background: rgba(0,26,61,0.03); }
        .layer-header-left { display: flex; align-items: center; gap: 10px; font-size: 11px; font-weight: 800; color: #001a3d; }
        .layer-header-left input[type="checkbox"] { margin: 0; cursor: pointer; transform: scale(1.1); }
        
        .layer-category-items { padding: 0; background: rgba(0, 26, 61, 0.02); }
        .layer-category-items.collapsed { display: none !important; }
        
        .results-item {
            padding: 8px 16px 8px 38px; font-size: 11px; font-weight: 600; color: #001a3d;
            cursor: pointer; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; transition: all 0.1s;
        }
        .results-item:hover { background: #001a3d; color: #ffffff; padding-left: 42px; }

        /* RIGHT CLICK CONTEXT PANEL VIEWER */
        #right-viewer-panel {
            position: absolute; top: 16px; right: 312px; z-index: 1001; background: #ffffff; border-radius: 12px;
            width: 450px; height: calc(100vh - 32px); border: 1px solid rgba(0, 26, 61, 0.1);
            display: none; flex-direction: column; box-shadow: -4px 0 20px rgba(0, 26, 61, 0.15); overflow: hidden;
        }
        .viewer-header {
            background: #001a3d; color: #ffffff; padding: 14px 16px; font-weight: 900; font-size: 11px;
            display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; letter-spacing: 1px;
        }
        .viewer-header a { color: #ffffff !important; text-decoration: none; font-weight: bold; margin-right: 15px; border: 1px solid rgba(255,255,255,0.4); padding: 4px 8px; border-radius: 4px; transition: all 0.2s;}
        .viewer-header a:hover { background: #ffffff; color: #001a3d !important; }
        .viewer-header span.close-btn { cursor: pointer; font-size: 16px; line-height: 1; }
        #viewer-iframe { flex-grow: 1; border: none; width: 100%; background: #f8fafc; }

        .poi-text-label {
            background: #ffffff; border: 1px solid #001a3d; padding: 3px 6px; border-radius: 4px; font-size: 10px; font-weight: 900; color: #001a3d; white-space: nowrap; box-shadow: 0 2px 6px rgba(0,0,0,0.1);
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
        <div class="toolbar-trigger-btn" title="Basemap Settings" onclick="toggleMenuPanel(event, 'basemap-menu-container')">▤</div>
    </div>
    
    <div id="basemap-menu-container" class="toolbar-floating-menu" onclick="event.stopPropagation();">
        <div class="panel-row">
            <label>Map Raster View</label>
            <select id="basemap-select" onchange="switchActiveBasemap(this.value)">
                <option value="osm">OSM Standard</option>
                <option value="satellite">Google Satellite</option>
                <option value="carto">Carto Light</option>
            </select>
        </div>
        <div class="panel-row" style="display:flex; align-items:center; gap:8px; margin-top:12px; margin-bottom: 4px;">
            <input type="checkbox" id="label-toggle-chk" style="margin:0; transform: scale(1.1); cursor: pointer;" onchange="toggleLabelsMatrix(this.checked)">
            <label style="margin:0; cursor:pointer; text-transform: none; font-weight: 800; font-size: 11px;" for="label-toggle-chk">Show Text Labels</label>
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
            <div style="display: flex; align-items: center;">
                <a id="viewer-ext-link" href="#" target="_blank">⤢ NEW TAB</a>
                <span class="close-btn" onclick="closeViewer()">✖</span>
            </div>
        </div>
        <iframe id="viewer-iframe" src=""></iframe>
    </div>

    <script>
        const map = L.map('map', { zoomControl: true, attributionControl: false }).setView([__LAT__, __LON__], 14);
        
        // Relocate zoom control below custom tools
        map.zoomControl.setPosition('topleft');
        
        const basemaps = {
            osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }),
            satellite: L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', { maxZoom: 20 }),
            carto: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 })
        };
        
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
        
        // Improved toggle with global click listener to close menu
        function toggleMenuPanel(event, panelId) {
            event.stopPropagation();
            const el = document.getElementById(panelId);
            const activeNow = el.style.display === 'block';
            document.querySelectorAll('.toolbar-floating-menu').forEach(p => p.style.display = 'none');
            if (!activeNow) el.style.display = 'block';
        }
        
        document.addEventListener('click', function(event) {
            document.querySelectorAll('.toolbar-floating-menu').forEach(p => p.style.display = 'none');
            document.getElementById('search-results').style.display = 'none';
        });
        
        document.getElementById('search-container').addEventListener('click', function(e) {
            e.stopPropagation();
        });

        let searchTimeout;
        function handleSearch(e) {
            clearTimeout(searchTimeout);
            const q = e.target.value;
            const resDiv = document.getElementById('search-results');
            if (q.length < 3) { resDiv.style.display = 'none'; return; }
            searchTimeout = setTimeout(() => {
                fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}`)
                .then(res => res.json())
                .then(data => {
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
        }).addTo(map).bindPopup("<b style='font-family: Arial;'>TARGET COORDINATES</b>");
        
        const radiusCircle = L.circle([__LAT__, __LON__], {
            radius: __RADIUS__, color: "#001a3d", weight: 2, fillColor: "#001a3d", fillOpacity: 0.1
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
                    radius: 5, fillColor: "#001a3d", color: "#ffffff", weight: 1.5, opacity: 1, fillOpacity: 0.9
                }).bindPopup("<b style='color:#001a3d; font-family: Arial;'>" + p.name + "</b><br><span style='font-family: Arial; font-size: 10px;'>" + p.type + "</span>");
                
                if (p.name && p.name !== 'Unknown') {
                    marker.bindTooltip(p.name, {
                        permanent: true, direction: 'top', offset: [0, -6], className: 'poi-text-label'
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
                                <span>${catName} <span style="color: #64748b; font-size: 10px;">(${categoryMap[catName].length})</span></span>
                            </div>
                            <span id="chevron-${catName}" style="font-size: 10px;">▼</span>
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
                        setTimeout(() => layer.openPopup(), 350);
                    }
                }
            });
        }
        
        map.on('contextmenu', function(e) {
            const lat = e.latlng.lat; const lng = e.latlng.lng;
            const coordStr = lat.toFixed(5) + ", " + lng.toFixed(5);
            
            const menuHtml = `
                <div style="font-family: Arial; font-size: 11px; color: #001a3d; min-width: 140px;">
                    <div style="font-weight: 900; border-bottom: 1px solid rgba(0,26,61,0.1); padding-bottom: 6px; margin-bottom: 6px; letter-spacing: 0.5px;">MAP ACTIONS</div>
                    <div style="padding: 6px 0; cursor: pointer; font-weight: bold; transition: color 0.1s;" onmouseover="this.style.color='#64748b'" onmouseout="this.style.color='#001a3d'" onclick="navigator.clipboard.writeText('${coordStr}'); alert('Copied: ${coordStr}'); map.closePopup();">◧ COPY COORDINATES</div>
                    <div style="padding: 6px 0; cursor: pointer; font-weight: bold; transition: color 0.1s;" onmouseover="this.style.color='#64748b'" onmouseout="this.style.color='#001a3d'" onclick="openRightPanel('routes', ${lat}, ${lng}); map.closePopup();">↱ OPEN ROUTES</div>
                    <div style="padding: 6px 0; cursor: pointer; font-weight: bold; transition: color 0.1s;" onmouseover="this.style.color='#64748b'" onmouseout="this.style.color='#001a3d'" onclick="openRightPanel('streetview', ${lat}, ${lng}); map.closePopup();">👁 OPEN STREETVIEW</div>
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
