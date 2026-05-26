import streamlit as st
import requests
import re
import json
import os
import osmnx as ox
import pandas as pd
from shapely.geometry import Point, Polygon, LineString

# =============================================================================
# [ CONFIGURATION BLOCK: STREAMLIT THEME & SETUP ]
# =============================================================================
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\n")

st.set_page_config(page_title="Trade Area Scan Playground", layout="wide", initial_sidebar_state="expanded")

# Configure OSMnx local caching to accelerate repetitive spatial queries
ox.config(use_cache=True, log_console=False)

# =============================================================================
# [ CONFIGURATION BLOCK: GLOBAL CSS STYLES ]
# =============================================================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Montserrat:wght@400;500;600;700;800&display=swap');
        
        :root {
            --brand-midnight: #003366 !important;
            --brand-gold: #C9AB4C !important;     
            --brand-dark: #001F3F !important;     
            --white-clean: #ffffff !important;
            --bg-offwhite: #f8fafc !important;    
            --text-muted: #888780 !important;
            --soft-shadow: 0 4px 12px rgba(0, 51, 102, 0.08) !important;
        }
        
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: var(--white-clean) !important; color: var(--brand-midnight) !important; font-family: 'Montserrat', sans-serif !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: var(--bg-offwhite) !important; color: var(--brand-midnight) !important;
            border-right: 1px solid rgba(0, 51, 102, 0.08) !important; width: 280px !important; min-width: 280px !important; max-width: 280px !important;
            box-shadow: 2px 0 15px rgba(0,0,0,0.03) !important;
        }
        
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"], [data-testid="stHeader"], header, #stDecoration, .stDeployButton, footer { display: none !important; }
        ::-webkit-scrollbar { width: 0px !important; background: transparent !important; }
        * { scrollbar-width: none !important; -ms-overflow-style: none !important; }
        
        p, label, h1, h2, h3, h4, h5, h6, .stMarkdown, [data-testid="stExpander"] summary p { color: var(--brand-midnight) !important; font-family: 'Montserrat', sans-serif !important; }
        
        [data-testid="stAppViewContainer"] { display: flex !important; flex-direction: row !important; width: 100vw !important; height: 100vh !important; overflow: hidden !important; }
        [data-testid="stMain"] { flex-grow: 1 !important; width: calc(100vw - 280px) !important; height: 100vh !important; overflow: hidden !important; margin: 0px !important; padding: 0px !important; }
        .block-container, [data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"], .stElementContainer { padding: 0px !important; margin: 0px !important; max-width: 100% !important; gap: 0rem !important; }
        iframe { height: 100vh !important; width: 100% !important; border: none !important; display: block !important; }
        
        [data-testid="stSidebarUserContent"] { padding-top: 12px !important; padding-left: 12px !important; padding-right: 12px !important; height: 100vh !important; overflow-y: auto !important; overflow-x: hidden !important; }
        
        div[data-baseweb="input"], div[data-baseweb="select"] { background-color: transparent !important; border: none !important; border-bottom: 1px solid rgba(201, 171, 76, 0.5) !important; border-radius: 0px !important; box-shadow: none !important; }
        div[data-baseweb="input"]:focus-within { border-bottom: 2px solid var(--brand-gold) !important; }
        
        div.stButton > button[kind="secondary"], div.stDownloadButton > button { background-color: var(--brand-midnight) !important; border: 1px solid var(--brand-midnight) !important; border-radius: 2px !important; width: 100% !important; padding: 6px !important; box-shadow: var(--soft-shadow) !important; transition: all 0.3s ease !important; }
        div.stButton > button[kind="secondary"]:hover, div.stDownloadButton > button:hover { background-color: var(--brand-gold) !important; border-color: var(--brand-gold) !important; }
        div.stButton > button[kind="secondary"] p, div.stDownloadButton > button p { color: var(--white-clean) !important; font-weight: 700 !important; font-size: 9px !important; text-transform: uppercase !important; letter-spacing: 1px; }
        
        div.stButton > button[kind="primary"] { background: transparent !important; border: none !important; color: var(--text-muted) !important; box-shadow: none !important; padding: 0 !important; margin-top: 2px; display: inline-flex; }
        div.stButton > button[kind="primary"] p { color: var(--text-muted) !important; font-size: 9px !important; font-weight: 600 !important; text-decoration: none !important; text-transform: uppercase; }
        div.stButton > button[kind="primary"]:hover p { color: #AA2E20 !important; }
        
        [data-testid="stSidebar"] .st-expander { border: 1px solid rgba(0, 51, 102, 0.05) !important; background-color: var(--white-clean) !important; border-radius: 2px !important; margin-bottom: 2px !important; overflow: hidden !important; }
        [data-testid="stSidebar"] .st-expander summary p { font-size: 10px !important; font-weight: 500 !important; }
        .stCheckbox label p { font-size: 10px !important; font-weight: 500 !important; }
        div[data-baseweb="checkbox"] input:checked + div, div[data-baseweb="checkbox"] div[aria-checked="true"] { background-color: var(--brand-midnight) !important; border-color: var(--brand-midnight) !important; }
        
        .brand-title { font-family: 'Cormorant Garamond', serif !important; font-style: italic; color: var(--brand-midnight); font-size: 30px; text-align: center; border-bottom: 1px solid var(--brand-gold); padding-bottom: 6px; margin-bottom: 15px; }
        .stTextInput label p, .stNumberInput label p { font-size: 9px !important; font-weight: 500 !important; letter-spacing: 0.5px; color: var(--text-muted) !important; }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# [ CONFIGURATION BLOCK: SESSION STATE INITIALIZATION ]
# =============================================================================
DEFAULT_COORDS = "14.5995, 120.9842"
DEFAULT_RADIUS = 1000

if 'geo_coords' not in st.session_state: st.session_state.geo_coords = DEFAULT_COORDS
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = DEFAULT_RADIUS
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'last_scan_lat' not in st.session_state: st.session_state.last_scan_lat = 14.5995
if 'last_scan_lon' not in st.session_state: st.session_state.last_scan_lon = 120.9842

# Structured tags mappings for clean OSMnx lookup logic execution
POI_CONFIG = {
    "COMMERCIAL": [['Corporate Office', 'office', 'commercial'], ['IT/Tech Center', 'office', 'it'], ['Business Center', 'building', 'commercial'], ['Hospital', 'amenity', 'hospital'], ['Hotel', 'tourism', 'hotel'], ['Motel', 'tourism', 'motel']],
    "RESIDENTIAL": [['Apartments', 'building', 'apartments'], ['House', 'building', 'house'], ['Residential Area', 'landuse', 'residential'], ['Condominium', 'building', 'residential']],
    "RETAIL": [['Mall/Department Store', 'shop', 'mall'], ['Supermarket', 'shop', 'supermarket'], ['Convenience Store', 'shop', 'convenience'], ['Pharmacy', 'amenity', 'pharmacy']],
    "FOOD AND BEVERAGES": [['Restaurant', 'amenity', 'restaurant'], ['Cafe/Coffee Shop', 'amenity', 'cafe'], ['Fast Food', 'amenity', 'fast_food'], ['Bar/Pub/Nightclub', 'amenity', 'bar']]
}

# =============================================================================
# [ PIPELINE EXECUTION ENGINE: OSMNX + OVERPASS FAILOVER ]
# =============================================================================
def run_spatial_scan(lat, lon, radius, selected_filters):
    """
    Primary orchestration engine: Queries via OSMnx geometries module first.
    Switches gracefully to programmatic Overpass requests if remote bounds resolve blank.
    """
    records = []
    center_point = (lat, lon)
    
    # Restructure selected UI items into precise OSM querying dictionaries
    tags_dict = {}
    for item in selected_filters:
        key, val = item[0], item[1]
        if key not in tags_dict:
            tags_dict[key] = []
        if isinstance(tags_dict[key], list):
            tags_dict[key].append(val)

    st.log(f"Executing Engine Phase 1: OSMnx resolution over spatial bounds radius {radius}m.")
    try:
        gdf = ox.geometries_from_point(center_point, tags=tags_dict, dist=radius)
        if not gdf.empty:
            for idx, row in gdf.iterrows():
                geom = row.geometry
                # Normalizing varying shapes (Polygons/Lines) safely to center coordinates
                if isinstance(geom, Point):
                    plat, plon = geom.y, geom.x
                else:
                    plat, plon = geom.centroid.y, geom.centroid.x
                
                # Resolving type mapping based on key collision lookups
                resolved_type = "Asset"
                for k in tags_dict.keys():
                    if k in row and pd.notna(row[k]):
                        resolved_type = row[k]
                        break

                records.append({
                    "lat": float(plat),
                    "lon": float(plon),
                    "name": str(row.get('name') if pd.notna(row.get('name')) else 'Unknown'),
                    "type": str(resolved_type),
                    "geomType": "Point"
                })
            return records
    except Exception as osmnx_err:
        # Graceful logging fall-through
        pass

    # Phase 2 Interceptor: Overpass Failover Protocol Execution
    OVERPASS_ENDPOINTS = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.private.coffee/api/interpreter"
    ]
    
    statements = []
    for item in selected_filters:
        statements.append(f'nwr["{item[0]}"="{item[1]}"](around:{radius},{lat},{lon});')
    ql = f"[out:json][timeout:60];(\n" + "\n".join(statements) + "\n);out center;"
    
    for url in OVERPASS_ENDPOINTS:
        try:
            res = requests.post(url, data={"data": ql}, headers={"User-Agent": "TradeAreaScan/6.0"}, timeout=30)
            if res.status_code == 200:
                for el in res.json().get('elements', []):
                    plat = el.get('lat') or el.get('center', {}).get('lat')
                    plon = el.get('lon') or el.get('center', {}).get('lon')
                    if plat and plon:
                        tags = el.get('tags', {})
                        records.append({
                            "lat": float(plat),
                            "lon": float(plon),
                            "name": tags.get('name', 'Unknown'),
                            "type": tags.get('amenity') or tags.get('shop') or tags.get('building') or 'Node',
                            "geomType": "Point"
                        })
                return records
        except Exception:
            continue
            
    return records

# =============================================================================
# [ CONFIGURATION BLOCK: SIDEBAR UI & LOGIC ]
# =============================================================================
with st.sidebar:
    st.markdown('<div class="brand-title">Trade Area Scan</div>', unsafe_allow_html=True)
    
    # DYNAMIC EXPORT FIX: Read directly from a text-input containing live, synced Leaflet state elements
    captured_client_state = st.text_input("STATE_SYNC_BRIDGE", value="", label_visibility="collapsed")
    
    export_payload = json.dumps(st.session_state.scanned_records, indent=2)
    if captured_client_state:
        try:
            # Parse real-time state from map engine adjustments if populated
            clean_payload = json.loads(captured_client_state)
            if clean_payload:
                export_payload = json.dumps(clean_payload, indent=2)
        except:
            pass

    st.download_button(
        label="EXPORT ALL POIs", 
        data=export_payload, 
        file_name="TradeArea_Data.json", 
        mime="application/json",
        use_container_width=True
    )
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    location_input = st.text_input("LOCATION SEARCH OR COORDINATES", value=st.session_state.geo_coords, key="geo_coords_input")
    radius_val = st.number_input("RADIUS (METERS)", min_value=100, max_value=50000, value=st.session_state.geo_radius, key="geo_radius_input", step=100)
    st.session_state.geo_radius = radius_val

    coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", location_input)
    if coord_match:
        lat_coord, lon_coord = float(coord_match.group(1)), float(coord_match.group(2))
        st.session_state.geo_coords = location_input
    else:
        if location_input and location_input != st.session_state.get('last_geocoded_query', ''):
            with st.spinner("Locating via Nominatim..."):
                try:
                    headers = {'User-Agent': 'TradeAreaScan/6.0'}
                    osm_url = f"https://nominatim.openstreetmap.org/search?q={location_input}&format=json&limit=1"
                    resp = requests.get(osm_url, headers=headers, timeout=10).json()
                    if resp:
                        new_lat, new_lon = float(resp[0]['lat']), float(resp[0]['lon'])
                        st.session_state.geo_coords = f"{new_lat:.5f}, {new_lon:.5f}"
                        st.session_state.last_geocoded_query = location_input
                        st.rerun()
                    else:
                        st.error("Location not found.")
                        lat_coord, lon_coord = 14.5995, 120.9842 
                except Exception:
                    st.error("API Error: Nominatim Timeout")
                    lat_coord, lon_coord = 14.5995, 120.9842
        else:
            fallback_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", st.session_state.geo_coords)
            lat_coord, lon_coord = (float(fallback_match.group(1)), float(fallback_match.group(2))) if fallback_match else (14.5995, 120.9842)

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    search_query = st.text_input("SEARCH TAGS", placeholder="Search parameters...").lower()
    
    selected_filters = []
    for cat_name, node_items in POI_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for label, tag_key, tag_val in matched:
                    if st.checkbox(label, key=f"chk_{cat_name}_{label}"): 
                        selected_filters.append((tag_key, tag_val))

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("SCAN AREA", type="secondary", use_container_width=True, key="scan_btn"):
        if not selected_filters:
            st.error("Select ≥ 1 POI filter configuration matrix context.")
        else:
            with st.spinner("Querying Hybrid Network Engine Architecture..."):
                results = run_spatial_scan(lat_coord, lon_coord, radius_val, selected_filters)
                if results:
                    st.session_state.scanned_records = results
                    st.session_state.last_scan_lat, st.session_state.last_scan_lon = lat_coord, lon_coord
                    st.success(f"Parsed {len(results)} spatial points successfully.")
                    st.rerun()
                else:
                    st.error("No vectors matching parameters returned from structural engines.")

    if st.button("CLEAR ALL", type="primary", key="clear_btn"):
        st.session_state.scanned_records = []
        for key in list(st.session_state.keys()):
            if key.startswith("chk_"):
                st.session_state[key] = False
        st.rerun()

# =============================================================================
# [ CONFIGURATION BLOCK: LEAFLET SPATIAL ENGINE BINDINGS ]
# =============================================================================
geojson_str = json.dumps(st.session_state.scanned_records)
is_stale = "true" if (lat_coord != st.session_state.last_scan_lat or lon_coord != st.session_state.last_scan_lon) else "false"

leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="https://unpkg.com/@geoman-io/leaflet-geoman-free@2.14.2/dist/leaflet-geoman.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/@geoman-io/leaflet-geoman-free@2.14.2/dist/leaflet-geoman.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #ffffff; overflow: hidden; font-family: 'Montserrat', sans-serif; }
        #map { height: 100vh; width: 100%; }
        .routing-active-indicator { display: none; position: absolute; top: 20px; left: 50%; transform: translateX(-50%); background: #AA2E20; color: #fff; font-weight: 800; padding: 8px 20px; border-radius: 4px; z-index: 2000; font-size: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); text-transform: uppercase; cursor: pointer;}
        body.routing-mode .routing-active-indicator { display: block; }
        body.routing-mode #map { cursor: crosshair !important; }
        #search-container { position: absolute; top: 15px; left: 60px; z-index: 1000; width: 300px; }
        #map-search { width: 100%; padding: 8px 12px; border: 1px solid rgba(0, 51, 102, 0.1); border-radius: 4px; font-size: 11px; font-weight: 600; color: #003366; outline: none; box-sizing: border-box; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); }
        #search-results { position: absolute; top: 38px; left: 0; width: 100%; background: #ffffff; border-radius: 2px; display: none; max-height: 250px; overflow-y: auto; border: 1px solid rgba(0, 51, 102, 0.1); z-index: 1001; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); }
        .search-item { padding: 8px 12px; font-size: 10px; font-weight: 600; cursor: pointer; border-bottom: 1px solid #f8fafc; color: #003366; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .search-item:hover { background: #f8fafc; color: #C9AB4C; }
        #minimal-basemap-panel { position: absolute; top: 110px; left: 60px; z-index: 1000; background: #ffffff; border-radius: 4px; border: 1px solid rgba(0, 51, 102, 0.1); display: none; flex-direction: column; padding: 4px; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); width: 160px; }
        #minimal-basemap-panel select { border: none; border-bottom: 1px solid #f0f0f0; padding: 6px; font-size: 10px; font-weight: 700; color: #003366; background: transparent; outline: none; cursor: pointer; width: 100%; text-transform: uppercase; font-family: inherit;}
        .minimal-label { font-size: 9px; font-weight: 700; padding: 6px; display: flex; align-items: center; gap: 4px; cursor: pointer; color: #888780; margin: 0; text-transform: uppercase; border-top: 1px solid #f8fafc;}
        #scan-results-panel { position: absolute; top: 10px; right: 10px; z-index: 1000; background: #ffffff; width: 280px; max-height: calc(100vh - 20px); border-radius: 2px; border: 1px solid rgba(0, 51, 102, 0.1); display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); }
        .results-header { background: #003366; color: #ffffff; padding: 10px 12px; font-size: 10px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; border-bottom: 2px solid #C9AB4C; }
        .manage-layers-btn { background: #f8fafc; color: #003366; padding: 6px; text-align: center; font-size: 9px; font-weight: 800; border-bottom: 1px solid #e0e0e0; cursor: pointer; text-transform: uppercase; }
        .results-list { overflow-y: auto; flex-grow: 1; padding-bottom: 8px; }
        .layer-category-block { border-bottom: 1px solid #f0f0f0; background: #fff;}
        .layer-category-header { background: #ffffff; padding: 8px 12px; display: flex; align-items: center; justify-content: space-between; user-select: none; border-left: 3px solid transparent;}
        .layer-category-header:hover { background: #f8fafc; border-left: 3px solid #C9AB4C;}
        .layer-header-left { display: flex; align-items: center; gap: 6px; font-size: 9px; font-weight: 700; color: #003366; text-transform: uppercase;}
        .layer-category-items { padding: 0; background: #f8fafc; min-height: 10px;}
        .layer-category-items.collapsed { display: none !important; }
        .results-item { padding: 6px 12px 6px 28px; font-size: 9px; font-weight: 600; color: #888780; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f0f0f0; background: #fff;}
        .manage-tools { display: none; }
        .manage-mode-active .manage-tools { display: flex; }
        .manage-mode-active .layer-category-header, .manage-mode-active .results-item { cursor: move; }
        .icon-btn { cursor: pointer; padding: 2px; margin-left:4px; fill: #888780; }
        .icon-btn.del:hover { fill: #AA2E20; }
        .add-layer-btn { display: block; width: 100%; text-align: center; padding: 8px; background: #f8fafc; color: #003366; font-size: 9px; font-weight: 800; cursor: pointer; border-top: 1px solid #e0e0e0; text-transform: uppercase;}
        .poi-text-label { background: #fff; border: 1px solid #003366; padding: 2px 4px; border-radius: 2px; font-size: 9px; font-weight: 700; }
        .hide-labels .poi-text-label { display: none !important; }
        .color-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; border: 1px solid rgba(0,0,0,0.2); }
        .edit-form-container { display: flex; flex-direction: column; gap: 6px; min-width: 180px;}
        .edit-form-container label { font-size: 8px; font-weight: 700; color: #888780; text-transform: uppercase; margin-bottom: -4px;}
        .edit-form-container input[type="text"], .edit-form-container input[type="color"] { width: 100%; border: none; border-bottom: 1px solid #C9AB4C; padding: 4px 0; font-size: 11px; font-weight: 600; color: #003366; outline: none; background: transparent;}
        .edit-form-container button { background: #003366; color: white; border: none; padding: 6px; border-radius: 2px; cursor: pointer; font-size: 9px; font-weight: 700; text-transform: uppercase;}
        .leaflet-control-custom-stack { background: #fff; border: 2px solid rgba(0,0,0,0.2); border-radius: 4px; display: flex; flex-direction: column; }
        .leaflet-control-custom-stack a { display: flex !important; align-items: center; justify-content: center; width: 34px; height: 34px; border-bottom: 1px solid #ccc; cursor: pointer;}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="routing-active-indicator" onclick="cancelRouting()">CANCEL ROUTING</div>
    <div id="search-container">
        <input type="text" id="map-search" placeholder="Nominatim Search..." onkeyup="handleSearch(event)">
        <div id="search-results"></div>
    </div>
    <div id="minimal-basemap-panel">
        <select id="basemap-select" onchange="switchActiveBasemap(this.value)">
            <option value="osm">OpenStreetMap</option>
            <option value="satellite">Google Satellite</option>
            <option value="carto">Carto Light</option>
        </select>
        <label class="minimal-label"><input type="checkbox" id="label-toggle-chk" checked onchange="toggleLabelsMatrix(this.checked)"> Show POI Labels</label>
    </div>
    <div id="scan-results-panel">
        <div class="results-header"><span>LAYERS</span><span id="results-count" style="color:#C9AB4C;">0</span></div>
        <div class="manage-layers-btn" onclick="toggleManageLayers()">⚙️ Manage Layers</div>
        <div class="results-list" id="results-list-box"></div>
        <div class="add-layer-btn" onclick="createNewLayer()">+ Add Custom Layer</div>
    </div>

    <script>
        const map = L.map('map', { zoomControl: false, attributionControl: false }).setView([__LAT__, __LON__], 14);
        L.control.zoom({ position: 'bottomright' }).addTo(map);

        const basemaps = {
            osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }),
            satellite: L.tileLayer('http://www.google.cn/maps/vt?lyrs=s@189&gl=cn&x={x}&y={y}&z={z}', { maxZoom: 20 }),
            carto: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 })
        };
        basemaps['osm'].addTo(map);

        function switchActiveBasemap(k) { Object.keys(basemaps).forEach(x => map.removeLayer(basemaps[x])); basemaps[k].addTo(map); }
        function toggleLabelsMatrix(b) { if(b) document.getElementById('map').classList.remove('hide-labels'); else document.getElementById('map').classList.add('hide-labels'); }

        map.pm.addControls({ position: 'topleft', drawMarker: true, drawPolyline: true, drawRectangle: true, drawPolygon: true, drawCircle: true, editMode: true, dragMode: true, removalMode: true });

        let pts = __GEOJSON__;
        let globalIdCounter = 1000;
        pts.forEach(p => { if(!p._uid) p._uid = globalIdCounter++; });

        let layerGroupsRef = {};
        const catPalette = ["#003366", "#C9AB4C", "#1A5A8A", "#A8862E"];
        let categoryColors = {};
        let colorIndex = 0;

        // CRITICAL FUNCTION: Transmits raw synced client configuration arrays right into Streamlit parent DOM node
        function syncStateToParent() {
            const stripped = pts.map(p => ({
                lat: p.lat, lon: p.lon, name: p.name, type: p.type, geomType: p.geomType
            }));
            const parentDoc = window.parent.document;
            const inputElements = parentDoc.querySelectorAll('input');
            // Locate specific custom state placeholder string bridge object
            for (let el of inputElements) {
                if (el.getAttribute('aria-label') === "STATE_SYNC_BRIDGE" || el.placeholder === "") {
                    if(el.value !== JSON.stringify(stripped)){
                        el.value = JSON.stringify(stripped);
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                    break;
                }
            }
        }

        const createPinIcon = (c) => L.divIcon({ html: `<svg viewBox="0 0 24 24" width="24" height="24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" fill="${c}" stroke="#fff" stroke-width="1.5"/></svg>`, className: '', iconSize: [24,24], iconAnchor: [12,24] });

        function renderSidebar() {
            const listBox = document.getElementById('results-list-box');
            document.getElementById('results-count').innerText = pts.length;
            
            Object.values(layerGroupsRef).forEach(g => map.removeLayer(g));
            layerGroupsRef = {};

            const categoryMap = {};
            pts.forEach(p => {
                if(!categoryMap[p.type]) {
                    categoryMap[p.type] = [];
                    if(!categoryColors[p.type]) categoryColors[p.type] = catPalette[colorIndex++ % catPalette.length];
                }
                categoryMap[p.type].push(p);
            });

            let html = '';
            Object.keys(categoryMap).forEach(cat => {
                layerGroupsRef[cat] = L.layerGroup().addTo(map);
                const c = categoryColors[cat];
                
                html += `<div class="layer-category-block" data-id="${cat}">
                    <div class="layer-category-header">
                        <div class="layer-header-left">
                            <span class="color-dot" style="background:${c}"></span>
                            <span>${cat} (${categoryMap[cat].length})</span>
                        </div>
                    </div>
                    <div class="layer-category-items" id="items-${cat.replace(/\s/g, '')}">`;
                
                categoryMap[cat].forEach(p => {
                    if(!p._layer) {
                        p._layer = L.marker([p.lat, p.lon], { icon: createPinIcon(p.color || c) });
                        if(p.name !== 'Unknown') p._layer.bindTooltip(p.name, { permanent: true, className: 'poi-text-label' });
                    }
                    p._layer.addTo(layerGroupsRef[cat]);

                    html += `<div class="results-item" data-uid="${p._uid}">
                        <div style="flex-grow:1; overflow:hidden; text-overflow:ellipsis;">${p.name}</div>
                        <div class="manage-tools">
                            <span onclick="removePoiInstance(${p._uid})" style="color:#AA2E20; cursor:pointer;">✕</span>
                        </div>
                    </div>`;
                });
                html += `</div></div>`;
            });
            listBox.innerHTML = html;
            syncStateToParent();
        }

        window.toggleManageLayers = function() { document.getElementById('scan-results-panel').classList.toggle('manage-mode-active'); }
        window.removePoiInstance = function(uid) {
            const idx = pts.findIndex(x => x._uid === uid);
            if(idx > -1) { if(pts[idx]._layer) map.removeLayer(pts[idx]._layer); pts.splice(idx, 1); renderSidebar(); }
        }

        L.circle([__LAT__, __LON__], { radius: __RADIUS__, color: "#003366", weight: 1.5, fillColor: "#003366", fillOpacity: 0.08 }).addTo(map);
        renderSidebar();
    </script>
</body>
</html>
"""

leaflet_html = (leaflet_template
                .replace("__LAT__", str(lat_coord))
                .replace("__LON__", str(lon_coord))
                .replace("__RADIUS__", str(radius_val))
                .replace("__GEOJSON__", geojson_str))

st.components.v1.html(leaflet_html, height=850, scrolling=False)
