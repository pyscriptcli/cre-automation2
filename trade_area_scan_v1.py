import streamlit as st
import requests
import re
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
        
        [data-testid="collapsedControl"] { display: none !important; }
        ::-webkit-scrollbar { width: 0px !important; background: transparent !important; }
        * { scrollbar-width: none !important; -ms-overflow-style: none !important; }
        
        p, span, label, h1, h2, h3, h4, h5, h6, .stMarkdown, [data-testid="stExpander"] summary p {
            color: var(--navy-brand) !important;
        }
        
        [data-testid="stHeader"], header, #stDecoration { display: none !important; }
        
        [data-testid="stAppViewContainer"] {
            display: flex !important; flex-direction: row !important;
            width: 100vw !important; height: 100vh !important; overflow: hidden !important;
        }
        
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
        
        div[data-baseweb="input"], div[data-baseweb="select"] {
            background-color: transparent !important;
            border: none !important; border-bottom: 2px solid rgba(0, 26, 61, 0.2) !important;
            border-radius: 0px !important; box-shadow: none !important;
        }
        div[data-baseweb="input"]:focus-within { border-bottom: 2px solid var(--navy-brand) !important; }
        
        /* PRIMARY & POPOVER BUTTONS */
        div.stButton > button[kind="secondary"], [data-testid="stPopover"] > button {
            background-color: var(--navy-brand) !important; 
            border: none !important; border-radius: 4px !important; width: 100% !important; padding: 8px !important;
            box-shadow: var(--soft-shadow) !important; transition: all 0.2s ease !important;
        }
        div.stButton > button[kind="secondary"] p, [data-testid="stPopover"] > button p, [data-testid="stPopover"] > button div, div.stDownloadButton > button p {
            color: var(--white-clean) !important; font-weight: 800 !important; font-size: 11px !important; text-transform: uppercase !important;
        }
        
        div.stDownloadButton > button {
            background-color: var(--navy-brand) !important; 
            border: none !important; border-radius: 4px !important; width: 100% !important; padding: 4px !important;
            box-shadow: var(--soft-shadow) !important;
        }
        
        /* HYPERLINK STYLE FOR CLEAR BUTTON */
        div.stButton > button[kind="primary"] {
            background: transparent !important; border: none !important; color: var(--navy-brand) !important;
            box-shadow: none !important; padding: 0 !important; margin-top: 4px; display: inline-flex;
        }
        div.stButton > button[kind="primary"] p {
            color: var(--navy-brand) !important; font-size: 11px !important; font-weight: 800 !important; text-decoration: underline !important; text-transform: uppercase;
        }
        div.stButton > button[kind="primary"]:hover p { color: #ff3366 !important; }
        
        [data-testid="stSidebar"] .st-expander {
            border: 1px solid rgba(0, 26, 61, 0.1) !important; background-color: var(--white-clean) !important;
            border-radius: 4px !important; margin-bottom: 4px !important; overflow: hidden !important;
        }
        .stDeployButton, footer { display:none !important; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. STATE PERSISTENCE & DATA MODELS
# -----------------------------------------------------------------------------
DEFAULT_COORDS = "14.5995, 120.9842"
DEFAULT_RADIUS = 1000

if 'geo_coords' not in st.session_state: st.session_state.geo_coords = DEFAULT_COORDS
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = DEFAULT_RADIUS
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'last_scan_lat' not in st.session_state: st.session_state.last_scan_lat = 14.5995
if 'last_scan_lon' not in st.session_state: st.session_state.last_scan_lon = 120.9842

POI_CONFIG = {
    "COMMERCIAL": [['Corporate Office', '"building"~"office|commercial",i'], ['IT/Tech Center', '"office"~"it|telecommunication",i'], ['Business Center', '"building"="commercial"'], ['Hospital', '"amenity"~"hospital|clinic",i'], ['Hotel', '"tourism"="hotel"'], ['Motel', '"tourism"="motel"']],
    "RETAIL": [['Mall/Department Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"supermarket|grocery",i'], ['Convenience Store', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Hardware', '"shop"~"hardware|doityourself",i'], ['General Shops', '"shop"~"boutique|clothes|shoes",i']],
    "FOOD AND BEVERAGES": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee Shop', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"'], ['Bar/Pub/Nightclub', '"amenity"~"bar|pub|nightclub",i'], ['Bakery/Pastry', '"shop"="bakery"']],
    "INDUSTRIAL & LOGISTICS": [['Expressway Exits', '"highway"~"motorway_junction|toll_gantry",i'], ['Ports & Terminals', '"industrial"="port"'], ['Manufacturing Plants', '"industrial"~"factory|manufacturing|processing",i'], ['Cold Storage Facilities', '"warehouse"~"cold_store|cold_storage",i'], ['Industrial Parks/Estates', '"landuse"~"industrial|industrial_estate",i'], ['Warehouses & Depots', '"building"~"warehouse|depot",i'], ['Storage Facilities', '"building"="storage"'], ['Truck Access Routes (HGV)', '"hgv"~"designated|yes",i']],
    "GOVERNMENT & INFRASTRUCTURE": [['City Hall', '"amenity"="townhall"'], ['Police Station', '"amenity"="police"'], ['Fire Station', '"amenity"="fire_station"'], ['Airport Terminal', '"aeroway"~"terminal|aerodrome",i']],
    "SCHOOLS": [['University/College', '"amenity"~"university|college",i'], ['K-12 School', '"amenity"="school"'], ['Vocational/Other', '"amenity"="learning_centre"']]
}

ADVANCED_CONFIG = {
    "AMENITIES": [['ATM', '"amenity"="atm"'], ['Bank', '"amenity"="bank"'], ['Bench', '"amenity"="bench"'], ['Bicycle Parking', '"amenity"="bicycle_parking"'], ['Bicycle Rental', '"amenity"="bicycle_rental"'], ['Cinema', '"amenity"="cinema"'], ['Clinic', '"amenity"="clinic"'], ['Embassy', '"amenity"="embassy"'], ['Firestation', '"amenity"="fire_station"'], ['Fuel', '"amenity"="fuel"'], ['Hospital', '"amenity"="hospital"'], ['Library', '"amenity"="library"'], ['Music School', '"amenity"="music_school"'], ['Parking', '"amenity"="parking"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Police', '"amenity"="police"'], ['Letter Box', '"amenity"="letter_box"'], ['Post Office', '"amenity"="post_office"'], ['School/College', '"amenity"~"school|college",i'], ['Taxi', '"amenity"="taxi"'], ['Theatre', '"amenity"="theatre"'], ['Toilets', '"amenity"="toilets"'], ['University', '"amenity"="university"']],
    "PLACE OF WORSHIP": [['Church', '"religion"="christian"'], ['Mosque', '"religion"="muslim"'], ['Buddhist Temple', '"religion"="buddhist"'], ['Hindu Temple', '"religion"="hindu"'], ['Synagogue', '"religion"="jewish"'], ['Cemetery', '"landuse"="cemetery"'], ['Alpine Hut', '"tourism"="alpine_hut"'], ['Apartment', '"tourism"="apartment"'], ['Camp Site', '"tourism"="camp_site"'], ['Chalet', '"tourism"="chalet"'], ['Guest House', '"tourism"="guest_house"'], ['Hostel', '"tourism"="hostel"'], ['Hotel', '"tourism"="hotel"'], ['Motel', '"tourism"="motel"'], ['Casino', '"amenity"="casino"'], ['Spa', '"leisure"="spa"'], ['Sauna', '"leisure"="sauna"']],
    "FOOD & BEVERAGE": [['Bar', '"amenity"="bar"'], ['BBQ', '"amenity"="bbq"'], ['Biergarten', '"amenity"="biergarten"'], ['Cafe', '"amenity"="cafe"'], ['Fast food', '"amenity"="fast_food"'], ['Food court', '"amenity"="food_court"'], ['Ice cream', '"amenity"="ice_cream"'], ['Pub', '"amenity"="pub"'], ['Restaurant', '"amenity"="restaurant"']],
    "RETAIL_ADV": [['Beauty', '"shop"="beauty"'], ['Bicycle', '"shop"="bicycle"'], ['Books/Stationary', '"shop"~"books|stationary",i'], ['Car', '"shop"="car"'], ['Chemist', '"shop"="chemist"'], ['Clothes', '"shop"="clothes"'], ['Copyshop', '"shop"="copyshop"'], ['Cosmetics', '"shop"="cosmetics"'], ['Department store', '"shop"="department_store"'], ['DIY/hardware', '"shop"~"hardware|doityourself",i'], ['Garden centre', '"shop"="garden_centre"'], ['General', '"shop"="general"'], ['Gift', '"shop"="gift"'], ['Hairdresser', '"shop"="hairdresser"'], ['Jewelry', '"shop"="jewelry"'], ['Kiosk', '"shop"="kiosk"'], ['Leather', '"shop"="leather"'], ['Marketplace', '"amenity"="marketplace"'], ['Musical instrument', '"shop"="musical_instrument"'], ['Optician', '"shop"="optician"'], ['Pets', '"shop"="pets"'], ['Phone', '"shop"="mobile_phone"'], ['Photo', '"shop"="photo"'], ['Shoes', '"shop"="shoes"'], ['Shopping centre', '"shop"="mall"'], ['Textiles', '"shop"="textiles"'], ['Toys', '"shop"="toys"']],
    "SPORTS": [['American football', '"sport"="american_football"'], ['Baseball', '"sport"="baseball"'], ['Basketball', '"sport"="basketball"'], ['Cycling', '"sport"="cycling"'], ['Gymnastics', '"sport"="gymnastics"'], ['Golf', '"sport"="golf"'], ['Hockey', '"sport"="hockey"'], ['Horse racing', '"sport"="horse_racing"'], ['Ice hockey', '"sport"="ice_hockey"'], ['Soccer', '"sport"="soccer"'], ['Sports centre', '"leisure"="sports_centre"'], ['Surfing', '"sport"="surfing"'], ['Swimming', '"sport"="swimming"'], ['Tennis', '"sport"="tennis"'], ['Volleyball', '"sport"="volleyball"']],
    "MISCELLANEOUS": [['Busstop', '"highway"="bus_stop"'], ['E-bike charging', '"amenity"="charging_station"'], ['Kindergarten', '"amenity"="kindergarten"'], ['Marketplace', '"amenity"="marketplace"'], ['Office', '"office"="yes"'], ['Recycling', '"amenity"="recycling"'], ['Travel agency', '"shop"="travel_agency"'], ['Defibrillator - AED', '"emergency"="defibrillator"'], ['Fire hose/extinguisher', '"emergency"~"fire_hose|fire_extinguisher",i'], ['Fixme', '"fixme"~".",i'], ['Note-Node', '"type"="node"'], ['Note-Way', '"type"="way"'], ['Construction', '"landuse"="construction"'], ['Image', '"image"~".",i'], ['Public camera', '"man_made"="surveillance"'], ['City', '"place"="city"'], ['Town', '"place"="town"'], ['Village', '"place"="village"'], ['Hamlet', '"place"="hamlet"'], ['Suburb', '"place"="suburb"']]
}

def compile_features_kml(features):
    kml = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scanned POIs</name>'
    for f in features:
        name = f.get('name', 'Asset').replace("&", "&").replace("<", "<").replace(">", ">")
        class_type = f.get('type', 'Node').replace("&", "&").replace("<", "<").replace(">", ">")
        kml += f"<Placemark><name>{name}</name><description>{class_type}</description><Point><coordinates>{f['lon']},{f['lat']},0</coordinates></Point></Placemark>"
    return kml + '</Document></kml>'

# -----------------------------------------------------------------------------
# 3. SIDEBAR WORKSPACE
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div style="color: #001a3d; font-size: 20px; font-weight: 900; letter-spacing: 1px; margin-bottom: 24px; text-align: center;">TRADE AREA SCAN</div>', unsafe_allow_html=True)
    
    coords_val = st.text_input("COORDINATES", key="geo_coords")
    radius_val = st.number_input("RADIUS (METERS)", min_value=100, max_value=50000, key="geo_radius", step=100)

    coord_match = re.match(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", coords_val)
    lat_coord, lon_coord = (float(coord_match.group(1)), float(coord_match.group(2))) if coord_match else (14.5995, 120.9842)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    search_query = st.text_input("SEARCH TAGS", placeholder="Search...").lower()
    
    selected_tags = []
    for cat_name, node_items in POI_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for label, tag in matched:
                    if st.checkbox(label, key=f"chk_{cat_name}_{label}"): selected_tags.append(tag)

    for cat_name, node_items in ADVANCED_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(f"ADV - {cat_name}", expanded=(len(search_query) > 0)):
                for label, tag in matched:
                    if st.checkbox(label, key=f"chk_adv_{cat_name}_{label}"): selected_tags.append(tag)

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("RUN SPATIAL SCAN", type="secondary", use_container_width=True):
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
                except Exception as e: st.error("Timeout")

    if st.button("Clear All POIs", type="primary"):
        st.session_state.scanned_records = []
        st.rerun()

    st.markdown("<hr style='margin: 16px 0; border: 0; border-top: 1px solid rgba(0, 26, 61, 0.1);'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("EXPORT PROJ", json.dumps(st.session_state.scanned_records), "scan.json", "application/json", use_container_width=True)
    with col2:
        st.download_button("EXPORT KML", compile_features_kml(st.session_state.scanned_records), "POIs.kml", "application/vnd.google-earth.kml+xml", use_container_width=True)

    with st.popover("IMPORT PROJECT", use_container_width=True):
        st.markdown("<div style='font-size:11px; font-weight:800; color:#001a3d; margin-bottom: 8px;'>UPLOAD SAVED PROJECT FILE</div>", unsafe_allow_html=True)
        imported_file = st.file_uploader("Select JSON file", type=["json"], label_visibility="collapsed")
        if imported_file is not None:
            if st.button("EXECUTE IMPORT", type="secondary", use_container_width=True):
                try:
                    data = json.load(imported_file)
                    st.session_state.scanned_records = data.get("scanned_records", data)
                    st.rerun()
                except Exception:
                    st.error("Invalid File")

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
        
        #minimal-basemap-panel {
            position: absolute; bottom: 20px; left: 10px; z-index: 1000;
            background: #ffffff; border-radius: 4px; border: 2px solid rgba(0,0,0,0.2); background-clip: padding-box;
            display: flex; flex-direction: column; padding: 2px;
        }
        #minimal-basemap-panel select {
            border: none; border-bottom: 1px solid #eee; padding: 4px; font-size: 11px; font-weight: bold;
            color: #333; background: transparent; outline: none; cursor: pointer; width: 100%;
        }
        .minimal-label {
            font-size: 10px; font-weight: bold; padding: 4px; display: flex; align-items: center; gap: 4px; cursor: pointer; color: #333; margin: 0;
        }

        #search-container { position: absolute; top: 10px; left: 54px; z-index: 1000; width: 340px; }
        #map-search {
            width: 100%; padding: 10px 14px; border: 2px solid rgba(0,0,0,0.2); border-radius: 4px; background-clip: padding-box;
            font-size: 13px; font-weight: bold; color: #333; background: #ffffff; outline: none; box-sizing: border-box;
        }
        #search-results {
            position: absolute; top: 45px; left: 0; width: 100%; background: #ffffff;
            border-radius: 4px; display: none; max-height: 250px; overflow-y: auto; 
            border: 2px solid rgba(0,0,0,0.2); box-sizing: border-box; z-index: 1001;
        }
        .search-item { padding: 10px 14px; font-size: 12px; cursor: pointer; border-bottom: 1px solid #eee; }
        .search-item:hover { background: #f4f4f4; }

        #scan-results-panel {
            position: absolute; top: 10px; right: 10px; z-index: 1000; background: #ffffff;
            width: 280px; max-height: calc(100vh - 20px); border-radius: 4px; border: 2px solid rgba(0,0,0,0.2); background-clip: padding-box;
            display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .results-header {
            background: #001a3d; color: #ffffff; padding: 12px 14px; font-size: 11px; font-weight: 900;
            display: flex; justify-content: space-between; align-items: center; text-transform: uppercase;
        }
        .results-list { overflow-y: auto; flex-grow: 1; padding-bottom: 8px; }
        .layer-category-block { border-bottom: 1px solid #eee; }
        .layer-category-header {
            background: #ffffff; padding: 10px 14px; display: flex; align-items: center; justify-content: space-between;
            cursor: pointer; user-select: none;
        }
        .layer-category-header:hover { background: #fafafa; }
        .layer-header-left { display: flex; align-items: center; gap: 8px; font-size: 11px; font-weight: 800; color: #001a3d; }
        
        .layer-category-items { padding: 0; background: #fafafa; }
        .layer-category-items.collapsed { display: none !important; }
        
        .results-item {
            padding: 8px 14px 8px 34px; font-size: 11px; font-weight: 600; color: #333;
            cursor: pointer; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .results-item:hover { background: #eaeaea; }

        .poi-text-label { background: #fff; border: 1px solid #000; padding: 2px 4px; border-radius: 2px; font-size: 9px; font-weight: bold; white-space: nowrap; }
        .hide-labels .poi-text-label { display: none !important; }
        .color-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; border: 1px solid rgba(0,0,0,0.2); }

        #right-viewer-panel {
            position: absolute; top: 10px; right: 300px; z-index: 1001; background: #ffffff; border-radius: 4px;
            width: 450px; height: calc(100vh - 20px); border: 2px solid rgba(0,0,0,0.2); background-clip: padding-box;
            display: none; flex-direction: column; box-shadow: -4px 0 20px rgba(0,0,0,0.15); overflow: hidden;
        }
        .viewer-header {
            background: #001a3d; color: #ffffff; padding: 12px 14px; font-weight: 900; font-size: 11px;
            display: flex; justify-content: space-between; align-items: center; text-transform: uppercase;
        }
        .viewer-header span.close-btn { cursor: pointer; font-size: 16px; line-height: 1; }
        #viewer-iframe { flex-grow: 1; border: none; width: 100%; background: #f8fafc; }
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div id="search-container">
        <input type="text" id="map-search" placeholder="Search location globally..." onkeyup="handleSearch(event)">
        <div id="search-results"></div>
    </div>

    <div id="minimal-basemap-panel">
        <select id="basemap-select" onchange="switchActiveBasemap(this.value)">
            <option value="osm">OpenStreetMap</option>
            <option value="satellite">Google Satellite</option>
            <option value="carto">Carto Light</option>
        </select>
        <label class="minimal-label" for="label-toggle-chk">
            <input type="checkbox" id="label-toggle-chk" style="margin:0; cursor: pointer;" onchange="toggleLabelsMatrix(this.checked)"> Show Labels
        </label>
    </div>

    <div id="scan-results-panel">
        <div class="results-header">
            <span>SCAN INDEX</span>
            <span id="results-count">0</span>
        </div>
        <div class="results-list" id="results-list-box"></div>
    </div>

    <div id="right-viewer-panel">
        <div class="viewer-header">
            <span id="viewer-title">VIEWER</span>
            <span class="close-btn" onclick="closeViewer()">✖</span>
        </div>
        <iframe id="viewer-iframe" src=""></iframe>
    </div>

    <script>
        const map = L.map('map', { zoomControl: true, attributionControl: false }).setView([__LAT__, __LON__], 14);
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
        
        const starIcon = L.divIcon({
            className: 'custom-center-icon',
            html: '<div style="background-color: #001a3d; color: #ffffff; width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; border: 2px solid #ffffff; box-shadow: 0 2px 6px rgba(0,0,0,0.5);">★</div>',
            iconSize: [26, 26], iconAnchor: [13, 13]
        });
        const centerMarker = L.marker([__LAT__, __LON__], { icon: starIcon, zIndexOffset: 10000 }).addTo(map);
        
        const radiusCircle = L.circle([__LAT__, __LON__], {
            radius: __RADIUS__, color: "#001a3d", weight: 2, fillColor: "#001a3d", fillOpacity: 0.1
        }).addTo(map);
        
        const pts = __GEOJSON__;
        const categoryMap = {};
        const layerGroupsRef = {};
        
        const catPalette = ["#6b8ca6", "#bfa482", "#8da186", "#b095a8", "#dca77d", "#92a6af", "#d4b8b2", "#a69aa4", "#859ea8", "#adae95", "#bf929a", "#7e9c91"];
        const categoryColors = {}; let colorIndex = 0;
        
        pts.forEach(p => {
            const layerKey = p.type || 'Unclassified';
            if (!categoryMap[layerKey]) {
                categoryMap[layerKey] = []; categoryColors[layerKey] = catPalette[colorIndex % catPalette.length]; colorIndex++;
            }
            categoryMap[layerKey].push(p);
        });
        
        Object.keys(categoryMap).forEach(key => {
            layerGroupsRef[key] = L.layerGroup().addTo(map);
            const pColor = categoryColors[key];
            categoryMap[key].forEach(p => {
                const marker = L.circleMarker([p.lat, p.lon], {
                    radius: 5, fillColor: pColor, color: "#ffffff", weight: 1.5, opacity: 1, fillOpacity: 0.9
                }).bindPopup("<b>" + p.name + "</b><br>" + p.type);
                if (p.name && p.name !== 'Unknown') {
                    marker.bindTooltip(p.name, { permanent: true, direction: 'top', offset: [0, -6], className: 'poi-text-label' });
                }
                marker.addTo(layerGroupsRef[key]);
            });
        });

        const listBox = document.getElementById('results-list-box');
        document.getElementById('results-count').innerText = pts.length;
        
        if (pts.length > 0) {
            let htmlPayload = '';
            Object.keys(categoryMap).forEach(catName => {
                const dotColor = categoryColors[catName];
                htmlPayload += `
                    <div class="layer-category-block">
                        <div class="layer-category-header" onclick="toggleAccordionCollapse('${catName}')">
                            <div class="layer-header-left">
                                <input type="checkbox" checked onclick="event.stopPropagation(); toggleCategoryVisibility('${catName}', this.checked)">
                                <span class="color-dot" style="background-color: ${dotColor};"></span>
                                <span>${catName} <span style="color: #888; font-size: 10px;">(${categoryMap[catName].length})</span></span>
                            </div>
                            <span id="chevron-${catName}" style="font-size: 10px;">▼</span>
                        </div>
                        <div class="layer-category-items" id="items-${catName}">
                `;
                categoryMap[catName].forEach(p => {
                    htmlPayload += `<div class="results-item" onclick="map.flyTo([${p.lat}, ${p.lon}], 17);">${p.name || 'Unknown'}</div>`;
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
            panel.classList.toggle('collapsed');
            chev.innerText = panel.classList.contains('collapsed') ? '▲' : '▼';
        }

        map.on('contextmenu', function(e) {
            const lat = e.latlng.lat; const lng = e.latlng.lng;
            const coordStr = lat.toFixed(5) + ", " + lng.toFixed(5);
            const menuHtml = `
                <div style="font-family: Arial; font-size: 11px; color: #333; min-width: 140px;">
                    <div style="font-weight: 900; border-bottom: 1px solid rgba(0,0,0,0.1); padding-bottom: 6px; margin-bottom: 6px; letter-spacing: 0.5px;">MAP ACTIONS</div>
                    <div style="padding: 6px 0; cursor: pointer; font-weight: bold; transition: color 0.1s;" onmouseover="this.style.color='#001a3d'" onmouseout="this.style.color='#333'" onclick="navigator.clipboard.writeText('${coordStr}'); map.closePopup();">📋 COPY COORDINATES</div>
                    <div style="padding: 6px 0; cursor: pointer; font-weight: bold; transition: color 0.1s;" onmouseover="this.style.color='#001a3d'" onmouseout="this.style.color='#333'" onclick="openRightPanel('routes', ${lat}, ${lng}); map.closePopup();">🗺️ GOOGLE MAPS</div>
                    <div style="padding: 6px 0; cursor: pointer; font-weight: bold; transition: color 0.1s;" onmouseover="this.style.color='#001a3d'" onmouseout="this.style.color='#333'" onclick="openRightPanel('streetview', ${lat}, ${lng}); map.closePopup();">🛣️ STREETVIEW</div>
                </div>
            `;
            L.popup().setLatLng(e.latlng).setContent(menuHtml).openOn(map);
        });

        function openRightPanel(type, lat, lng) {
            const panel = document.getElementById('right-viewer-panel');
            const iframe = document.getElementById('viewer-iframe');
            document.getElementById('viewer-title').innerText = type === 'routes' ? 'GOOGLE MAPS' : 'STREETVIEW';
            
            if(type === 'routes') {
                iframe.src = `https://maps.google.com/maps?q=${lat},${lng}&output=embed`;
            } else {
                iframe.src = `https://maps.google.com/maps?q=${lat},${lng}&layer=c&cbll=${lat},${lng}&output=svembed`;
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
        }
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

st.components.v1.html(leaflet_html, height=850, scrolling=False)
