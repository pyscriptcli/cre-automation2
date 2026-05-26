import streamlit as st
import requests
import re
import json
import os
import math
import osmnx as ox
import pandas as pd

# =============================================================================
# [ CONFIGURATION BLOCK: STREAMLIT THEME & SETUP ]
# Ensures the app always loads in Light Mode to match the custom CSS variables.
# =============================================================================
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\n")

st.set_page_config(page_title="Trade Area Scan | Felt Clone", layout="wide", initial_sidebar_state="expanded")

# =============================================================================
# [ CONFIGURATION BLOCK: GLOBAL CSS STYLES (FELT.COM 1:1 OVERHAUL) ]
# =============================================================================
st.markdown("""
    <style>
        /* Import Inter font to match Felt.com typography */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        :root {
            --felt-bg: #F9F9F9 !important;
            --felt-border: #E5E5E5 !important;
            --felt-text: #333333 !important;
            --felt-text-muted: #888888 !important;
            --felt-pink: #FF3366 !important;
            --felt-pink-hover: #E62E5C !important;
            --felt-hover-bg: #F0F0F0 !important;
            --white-clean: #ffffff !important;
        }
        
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: var(--white-clean) !important; 
            color: var(--felt-text) !important; 
            font-family: 'Inter', sans-serif !important;
        }
        
        /* Sidebar styled as Felt Data/Layers Panel */
        [data-testid="stSidebar"] {
            background-color: var(--white-clean) !important; 
            color: var(--felt-text) !important;
            border-right: 1px solid var(--felt-border) !important; 
            width: 320px !important; min-width: 320px !important; max-width: 320px !important;
            box-shadow: 2px 0 10px rgba(0,0,0,0.02) !important;
        }
        
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"], [data-testid="stHeader"], header, #stDecoration, .stDeployButton, footer { display: none !important; }
        ::-webkit-scrollbar { width: 4px !important; background: transparent !important; }
        ::-webkit-scrollbar-thumb { background: #E5E5E5 !important; border-radius: 4px; }
        
        p, label, h1, h2, h3, h4, h5, h6, .stMarkdown, [data-testid="stExpander"] summary p { 
            color: var(--felt-text) !important; 
            font-family: 'Inter', sans-serif !important; 
        }
        
        [data-testid="stAppViewContainer"] { display: flex !important; flex-direction: row !important; width: 100vw !important; height: 100vh !important; overflow: hidden !important; }
        [data-testid="stMain"] { flex-grow: 1 !important; width: calc(100vw - 320px) !important; height: 100vh !important; overflow: hidden !important; margin: 0px !important; padding: 0px !important; }
        .block-container, [data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"], .stElementContainer { padding: 0px !important; margin: 0px !important; max-width: 100% !important; gap: 0rem !important; }
        iframe { height: 100vh !important; width: 100% !important; border: none !important; display: block !important; }
        
        [data-testid="stSidebarUserContent"] { padding-top: 24px !important; padding-left: 20px !important; padding-right: 20px !important; height: 100vh !important; overflow-y: auto !important; overflow-x: hidden !important; }
        
        /* Felt-style Inputs */
        div[data-baseweb="input"], div[data-baseweb="select"] { 
            background-color: var(--felt-bg) !important; 
            border: 1px solid var(--felt-border) !important; 
            border-radius: 8px !important; 
            box-shadow: none !important; 
            padding: 4px !important;
        }
        div[data-baseweb="input"]:focus-within { border: 1px solid var(--felt-text) !important; }
        
        /* Felt-style Pink Action Buttons */
        div.stButton > button[kind="secondary"], div.stDownloadButton > button { 
            background-color: var(--felt-pink) !important; 
            border: none !important; 
            border-radius: 8px !important; 
            width: 100% !important; 
            padding: 10px !important; 
            box-shadow: none !important; 
            transition: all 0.2s ease !important; 
        }
        div.stButton > button[kind="secondary"]:hover, div.stDownloadButton > button:hover { 
            background-color: var(--felt-pink-hover) !important; 
        }
        div.stButton > button[kind="secondary"] p, div.stDownloadButton > button p { 
            color: var(--white-clean) !important; 
            font-weight: 600 !important; 
            font-size: 13px !important; 
        }
        
        /* Ghost Buttons */
        div.stButton > button[kind="primary"] { 
            background: transparent !important; 
            border: 1px solid var(--felt-border) !important; 
            color: var(--felt-text) !important; 
            border-radius: 8px !important;
            padding: 8px !important; 
            width: 100% !important;
            margin-top: 8px; 
        }
        div.stButton > button[kind="primary"] p { 
            color: var(--felt-text) !important; 
            font-size: 12px !important; 
            font-weight: 500 !important; 
        }
        div.stButton > button[kind="primary"]:hover { background: var(--felt-bg) !important; }
        
        /* Expanders */
        [data-testid="stSidebar"] .st-expander { 
            border: none !important; 
            border-bottom: 1px solid var(--felt-border) !important; 
            background-color: var(--white-clean) !important; 
            border-radius: 0px !important; 
            margin-bottom: 0px !important; 
        }
        [data-testid="stSidebar"] .st-expander summary { padding-left: 0 !important; padding-right: 0 !important;}
        [data-testid="stSidebar"] .st-expander summary p { font-size: 13px !important; font-weight: 600 !important; }
        .stCheckbox label p { font-size: 13px !important; font-weight: 400 !important; color: #555 !important;}
        div[data-baseweb="checkbox"] input:checked + div, div[data-baseweb="checkbox"] div[aria-checked="true"] { 
            background-color: var(--felt-text) !important; 
            border-color: var(--felt-text) !important; 
        }
        
        .brand-title { 
            font-family: 'Inter', sans-serif !important; 
            font-weight: 700; 
            color: var(--felt-text); 
            font-size: 20px; 
            margin-bottom: 24px; 
        }
        .stTextInput label p, .stNumberInput label p { 
            font-size: 12px !important; 
            font-weight: 600 !important; 
            color: var(--felt-text) !important; 
        }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# [ CORE LOGIC: HAVERSINE DISTANCE FILTER ]
# =============================================================================
def calculate_haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Radius of Earth in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

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

# =============================================================================
# [ CONFIGURATION BLOCK: POI DICTIONARY ]
# =============================================================================
POI_CONFIG = {
    "COMMERCIAL": [['Corporate Office', '"building"~"office|commercial",i'], ['IT/Tech Center', '"office"~"it|telecommunication",i'], ['Business Center', '"building"="commercial"'], ['Hospital', '"amenity"~"hospital|clinic",i'], ['Hotel', '"tourism"="hotel"'], ['Motel', '"tourism"="motel"']],
    "RESIDENTIAL": [['Apartments', '"building"="apartments"'], ['House', '"building"="house"'], ['Residential Area', '"landuse"="residential"'], ['Condominium', '"building"="residential"']],
    "RETAIL": [['Mall/Department Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"supermarket|grocery",i'], ['Convenience Store', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Hardware', '"shop"~"hardware|doityourself",i'], ['General Shops', '"shop"~"boutique|clothes|shoes",i'], ['Beauty', '"shop"="beauty"']],
    "FOOD AND BEVERAGES": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee Shop', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"'], ['Bar/Pub/Nightclub', '"amenity"~"bar|pub|nightclub",i'], ['Bakery/Pastry', '"shop"="bakery"']],
    "INDUSTRIAL": [['Expressway Exits', '"highway"~"motorway_junction|toll_gantry",i'], ['Ports & Terminals', '"industrial"="port"'], ['Manufacturing Plants', '"industrial"~"factory|manufacturing|processing",i'], ['Warehouses & Depots', '"building"~"warehouse|depot",i']],
    "GOVERNMENT": [['City Hall', '"amenity"="townhall"'], ['Police Station', '"amenity"="police"'], ['Fire Station', '"amenity"="fire_station"'], ['Airport Terminal', '"aeroway"~"terminal|aerodrome",i']],
    "SCHOOLS": [['University/College', '"amenity"~"university|college",i'], ['K-12 School', '"amenity"="school"']]
}

ADVANCED_CONFIG = {
    "AMENITIES": [['ATM', '"amenity"="atm"'], ['Bank', '"amenity"="bank"'], ['Bench', '"amenity"="bench"'], ['Parking', '"amenity"="parking"']],
    "SPORTS": [['Basketball', '"sport"="basketball"'], ['Soccer', '"sport"="soccer"'], ['Sports centre', '"leisure"="sports_centre"']],
    "MISCELLANEOUS": [['Busstop', '"highway"="bus_stop"'], ['Construction', '"landuse"="construction"']]
}

# =============================================================================
# [ CONFIGURATION BLOCK: SIDEBAR UI & LOGIC ]
# =============================================================================
with st.sidebar:
    st.markdown('<div class="brand-title">Data Layers</div>', unsafe_allow_html=True)
    
    # DYNAMIC EXPORT BUTTON
    if st.session_state.scanned_records:
        st.download_button(
            label=f"Download GeoJSON ({len(st.session_state.scanned_records)})", 
            data=json.dumps(st.session_state.scanned_records, indent=4), 
            file_name="Felt_Export.json", 
            mime="application/json",
            use_container_width=True,
            type="secondary"
        )
    else:
        st.download_button(
            label="Download GeoJSON (Empty)", 
            data=json.dumps([]), 
            file_name="Felt_Export.json", 
            mime="application/json",
            use_container_width=True,
            disabled=True
        )
    
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    location_input = st.text_input("Location Center", value=st.session_state.geo_coords, key="geo_coords_input")
    radius_val = st.number_input("Radius Constraint (m)", min_value=100, max_value=50000, value=st.session_state.geo_radius, key="geo_radius_input", step=100)
    st.session_state.geo_radius = radius_val

    coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", location_input)
    
    if coord_match:
        lat_coord, lon_coord = float(coord_match.group(1)), float(coord_match.group(2))
        st.session_state.geo_coords = location_input
    else:
        if location_input and location_input != st.session_state.get('last_geocoded_query', ''):
            with st.spinner("Geocoding via Nominatim..."):
                try:
                    headers = {'User-Agent': 'TradeAreaScan/4.0'}
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
            if fallback_match:
                lat_coord, lon_coord = float(fallback_match.group(1)), float(fallback_match.group(2))
            else:
                lat_coord, lon_coord = 14.5995, 120.9842

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    search_query = st.text_input("Filter Tags", placeholder="e.g. cafe, office...").lower()
    
    selected_tags = []
    for cat_name, node_items in POI_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for label, tag in matched:
                    if st.checkbox(label, key=f"chk_{cat_name}_{label}"): selected_tags.append(tag)

    st.markdown("<div style='font-weight: 600; font-size: 13px; margin-top: 24px; margin-bottom: 8px; color: #888;'>Advanced Features</div>", unsafe_allow_html=True)
    with st.container():
        for cat_name, node_items in ADVANCED_CONFIG.items():
            matched = [item for item in node_items if search_query in item[0].lower()]
            if matched:
                with st.expander(cat_name, expanded=(len(search_query) > 0)):
                    for label, tag in matched:
                        if st.checkbox(label, key=f"chk_adv_{cat_name}_{label}"): selected_tags.append(tag)

    st.markdown("<br>", unsafe_allow_html=True)
    
    OVERPASS_ENDPOINTS = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter"]

    # =============================================================================
    # [ CONFIGURATION BLOCK: SCAN AREA ENGINE ]
    # =============================================================================
    if st.button("Query Area Network", type="secondary", use_container_width=True, key="scan_btn"):
        if not selected_tags:
            st.error("Select ≥ 1 Tag.")
        else:
            status_indicator = st.empty()
            with st.spinner("Extracting spatial nodes..."):
                success = False
                status_indicator.info("Connecting to OSMnx Core...")
                try:
                    ox.settings.use_cache = False
                    ox.settings.log_console = False

                    osmnx_tags = {}
                    for tag_str in selected_tags:
                        match = re.search(r'"([^"]+)"(=|~)"([^"]+)"', tag_str)
                        if match:
                            k, op, v = match.group(1), match.group(2), match.group(3)
                            if v == '.':
                                val = True
                            else:
                                val = v.split('|') if '|' in v else v
                                
                            if k in osmnx_tags:
                                if isinstance(osmnx_tags[k], list):
                                    if isinstance(val, list): osmnx_tags[k].extend(val)
                                    elif val is not True: osmnx_tags[k].append(val)
                                elif isinstance(osmnx_tags[k], str):
                                    if val is True: osmnx_tags[k] = True
                                    else: osmnx_tags[k] = [osmnx_tags[k]] + (val if isinstance(val, list) else [val])
                            else:
                                osmnx_tags[k] = val

                    gdf = ox.features_from_point((lat_coord, lon_coord), tags=osmnx_tags, dist=radius_val)
                    
                    if not gdf.empty:
                        records = []
                        for idx, row in gdf.iterrows():
                            geom = row['geometry']
                            if geom.geom_type == 'Point':
                                p_lat, p_lon = geom.y, geom.x
                            else:
                                centroid = geom.centroid
                                p_lat, p_lon = centroid.y, centroid.x
                            
                            dist = calculate_haversine(lat_coord, lon_coord, p_lat, p_lon)
                            if dist <= radius_val:
                                name = row.get('name', 'Unknown')
                                if pd.isna(name): name = 'Unknown'
                                
                                p_type = 'Node'
                                for k in osmnx_tags.keys():
                                    if k in row and not pd.isna(row[k]):
                                        p_type = str(row[k])
                                        break
                                
                                records.append({
                                    "lat": float(p_lat), 
                                    "lon": float(p_lon), 
                                    "name": str(name), 
                                    "type": str(p_type), 
                                    "geomType": str(geom.geom_type),
                                    "shape": "Pin" 
                                })
                        
                        st.session_state.scanned_records = records
                        st.session_state.last_scan_lat, st.session_state.last_scan_lon = lat_coord, lon_coord
                        success = True
                        status_indicator.success(f"Extracted {len(records)} POIs.")
                    else:
                        st.session_state.scanned_records = []
                        st.session_state.last_scan_lat, st.session_state.last_scan_lon = lat_coord, lon_coord
                        success = True
                        status_indicator.warning("0 POIs found strictly in this radius.")

                except Exception as e:
                    status_indicator.warning("Fallback to Overpass Turbo API...")
                    statements = "\n".join([f"  nwr[{tag}](around:{radius_val},{lat_coord},{lon_coord});" for tag in selected_tags])
                    ql = f"[out:json][timeout:90];(\n{statements}\n);\nout center;"
                    
                    for url in OVERPASS_ENDPOINTS:
                        try:
                            res = requests.post(url, data={"data": ql}, headers={"User-Agent": "TradeAreaScan/5.0"}, timeout=45)
                            if res.status_code == 200:
                                records = []
                                for el in res.json().get('elements', []):
                                    e_lat = el.get('lat') or el.get('center', {}).get('lat')
                                    e_lon = el.get('lon') or el.get('center', {}).get('lon')
                                    
                                    if e_lat and e_lon:
                                        dist = calculate_haversine(lat_coord, lon_coord, float(e_lat), float(e_lon))
                                        if dist <= radius_val:
                                            tags = el.get('tags', {})
                                            p_type = tags.get('amenity') or tags.get('shop') or tags.get('building') or 'Node'
                                            records.append({
                                                "lat": float(e_lat), 
                                                "lon": float(e_lon), 
                                                "name": str(tags.get('name', 'Unknown')), 
                                                "type": str(p_type), 
                                                "geomType": str("Point" if el.get('type') == 'node' else "Polygon"),
                                                "shape": "Pin"
                                            })
                                st.session_state.scanned_records = records
                                st.session_state.last_scan_lat, st.session_state.last_scan_lon = lat_coord, lon_coord
                                success = True
                                status_indicator.success(f"Fallback extracted {len(records)} POIs.")
                                break
                        except Exception:
                            continue
                            
                if success:
                    import time
                    time.sleep(1.0)
                    status_indicator.empty()
                    st.rerun() 
                else:
                    status_indicator.error("Critical Error: Core and Fallback servers failed.")

    if st.button("Clear Buffer", type="primary", key="clear_btn"):
        st.session_state.scanned_records = []
        for key in list(st.session_state.keys()):
            if key.startswith("chk_"):
                st.session_state[key] = False
        st.rerun()

# =============================================================================
# [ CONFIGURATION BLOCK: LEAFLET ENGINE - FELT 1:1 CLONE ]
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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* CORE MAP SETUP */
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; font-family: 'Inter', sans-serif; overflow: hidden; background: #EAEAEB; }
        #map { height: 100vh; width: 100%; z-index: 1;}
        .leaflet-control-zoom { display: none !important; } /* Hide default zoom, we use custom */
        .leaflet-pm-toolbar { display: none !important; } /* Hide default geoman */
        
        /* FELT TOP NAVIGATION BAR */
        #felt-top-nav {
            position: absolute; top: 0; left: 0; right: 0; height: 48px; background: #ffffff;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05); z-index: 2000; display: flex; align-items: center; justify-content: space-between;
            padding: 0 16px; user-select: none;
        }
        
        .nav-group { display: flex; align-items: center; gap: 12px; }
        
        .felt-logo { font-weight: 700; font-size: 16px; color: #111; display: flex; align-items: center; gap: 8px;}
        .felt-breadcrumbs { font-size: 13px; color: #666; font-weight: 500; }
        .felt-breadcrumbs span { color: #aaa; margin: 0 4px; }
        
        .tool-btn { 
            width: 32px; height: 32px; border-radius: 6px; display: flex; align-items: center; justify-content: center;
            cursor: pointer; fill: #555; transition: all 0.15s; background: transparent; border: none;
        }
        .tool-btn:hover { background: #F0F0F0; fill: #111; }
        .tool-btn.active { background: #E5E5E5; fill: #111; }
        
        .divider { width: 1px; height: 24px; background: #E5E5E5; margin: 0 4px; }
        
        .action-btn-pink { 
            background: #FF3366; color: white; border: none; padding: 6px 16px; border-radius: 6px; 
            font-weight: 600; font-size: 13px; cursor: pointer; transition: 0.2s;
        }
        .action-btn-pink:hover { background: #E62E5C; }
        
        .avatar { width: 28px; height: 28px; border-radius: 50%; background: #003366; color: white; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600;}
        
        /* FELT SEARCH BAR FLOATING RIGHT */
        #felt-search {
            position: absolute; top: 64px; right: 24px; z-index: 2000; width: 280px;
            background: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            display: flex; align-items: center; padding: 8px 12px; border: 1px solid #E5E5E5;
        }
        #felt-search input { 
            border: none; outline: none; width: 100%; font-family: 'Inter'; font-size: 13px; color: #333; margin-left: 8px;
        }
        #search-results-dropdown {
            position: absolute; top: 110px; right: 24px; z-index: 2000; width: 280px; background: white;
            border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); display: none; overflow: hidden; border: 1px solid #E5E5E5;
        }
        .search-item-res { padding: 10px 12px; font-size: 12px; color: #333; cursor: pointer; border-bottom: 1px solid #F0F0F0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
        .search-item-res:hover { background: #F9F9F9; }

        /* FELT LEFT ANNOTATIONS MENU */
        #felt-left-tools {
            position: absolute; top: 64px; left: 24px; z-index: 2000; background: white;
            border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #E5E5E5;
            display: flex; flex-direction: column; width: 180px; padding: 8px 0;
        }
        .annotations-header { font-size: 11px; font-weight: 600; color: #888; text-transform: uppercase; padding: 4px 16px 8px 16px; letter-spacing: 0.5px;}
        
        .anno-item {
            display: flex; align-items: center; justify-content: space-between; padding: 8px 16px;
            cursor: pointer; color: #333; font-size: 13px; font-weight: 500; transition: background 0.1s;
        }
        .anno-item:hover { background: #F5F5F5; }
        .anno-item.active { background: #EFEFEF; font-weight: 600; }
        .anno-left { display: flex; align-items: center; gap: 12px; fill: #333; }
        .anno-hotkey { font-size: 11px; color: #aaa; font-family: monospace;}
        .anno-divider { height: 1px; background: #E5E5E5; margin: 8px 16px; }

        /* FELT BOTTOM RIGHT CONTROLS */
        #felt-bottom-right {
            position: absolute; bottom: 24px; right: 24px; z-index: 2000; display: flex; gap: 8px; align-items: center;
        }
        .ctrl-btn {
            background: white; border: 1px solid #E5E5E5; box-shadow: 0 2px 6px rgba(0,0,0,0.05);
            width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center;
            cursor: pointer; fill: #333; transition: 0.15s; font-weight: 600; font-size: 16px;
        }
        .ctrl-btn:hover { background: #F5F5F5; }
        
        /* MAP CUSTOMIZATIONS */
        .leaflet-container { background: #F0F4F8; } /* Matches empty felt canvas */
    </style>
</head>
<body>

    <div id="felt-top-nav">
        <div class="nav-group">
            <div class="felt-logo">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="#111"><path d="M4 4h16v16H4z" opacity="0.1"/><path d="M12 2L2 22h20L12 2zm0 4.5l7 13.5H5l7-13.5z"/></svg>
                Felt
            </div>
            <div class="felt-breadcrumbs">
                Drafts <span>/</span> Trade Area Scan
            </div>
        </div>
        
        <div class="nav-group" style="gap: 4px;">
            <button class="tool-btn active" title="Select" onclick="disableAllDraw()">
                <svg viewBox="0 0 24 24" width="18" height="18"><path d="M7 2l12 11.2-5.8.5 3.3 7.3-2.2 1-3.2-7.4L7 20V2z"/></svg>
            </button>
            <button class="tool-btn" title="Cut Polygon" onclick="enableCut()">
                <svg viewBox="0 0 24 24" width="18" height="18"><path d="M9 3c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zM5.5 10c-1.4 0-2.5 1.1-2.5 2.5s1.1 2.5 2.5 2.5 2.5-1.1 2.5-2.5-1.1-2.5-2.5-2.5zm13 0c-1.4 0-2.5 1.1-2.5 2.5s1.1 2.5 2.5 2.5 2.5-1.1 2.5-2.5-1.1-2.5-2.5-2.5zM9 17c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zM12 2c5.5 0 10 4.5 10 10s-4.5 10-10 10S2 17.5 2 12 6.5 2 12 2zm0 2C7.6 4 4 7.6 4 12s3.6 8 8 8 8-3.6 8-8-3.6-8-8-8z"/></svg>
            </button>
            <button class="tool-btn" title="Library">
                <svg viewBox="0 0 24 24" width="18" height="18"><path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H8V4h12v12zM10 9h8v2h-8zm0 3h4v2h-4zm0-6h8v2h-8z"/></svg>
            </button>
            <button class="tool-btn" title="Upload">
                <svg viewBox="0 0 24 24" width="18" height="18"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z"/></svg>
            </button>
            <button class="tool-btn" title="Link">
                <svg viewBox="0 0 24 24" width="18" height="18"><path d="M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z"/></svg>
            </button>
            <button class="tool-btn" title="Routing Magic">
                <svg viewBox="0 0 24 24" width="18" height="18"><path d="M11 21h-1l1-7H7.5c-.58 0-.57-.32-.38-.66.19-.34.05-.08.08-.13L11.5 2h1l-1 7h3.5c.49 0 .56.33.47.51l-.07.15L11 21z"/></svg>
            </button>
            <button class="tool-btn" title="Settings">
                <svg viewBox="0 0 24 24" width="18" height="18"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.06-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.73 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.06.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .43-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.49-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>
            </button>
        </div>
        
        <div class="nav-group">
            <div class="avatar">DP</div>
            <button class="tool-btn" title="Map Layers">
                <svg viewBox="0 0 24 24" width="18" height="18"><path d="M11.99 18.54l-7.37-5.73L3 14.07l9 7 9-7-1.63-1.27-7.38 5.74zM12 16l7.36-5.73L21 9l-9-7-9 7 1.63 1.27L12 16z"/></svg>
            </button>
            <div class="divider"></div>
            <button class="tool-btn" title="Chat">
                <svg viewBox="0 0 24 24" width="18" height="18"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>
            </button>
            <span style="font-size: 13px; font-weight: 600; margin: 0 8px; cursor:pointer;">Share</span>
            <button class="action-btn-pink">Done</button>
        </div>
    </div>

    <div id="felt-left-tools">
        <div class="annotations-header">Annotations</div>
        
        <div class="anno-item" onclick="triggerDraw('Marker', this)">
            <div class="anno-left"><svg viewBox="0 0 24 24" width="16" height="16"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg> Pin</div>
            <div class="anno-hotkey">P</div>
        </div>
        
        <div class="anno-item" onclick="triggerDraw('Line', this)">
            <div class="anno-left"><svg viewBox="0 0 24 24" width="16" height="16"><path d="M3 21L21 3" stroke="#333" stroke-width="2" stroke-linecap="round"/></svg> Line</div>
            <div class="anno-hotkey">L</div>
        </div>
        
        <div class="anno-item" onclick="triggerDraw('Route', this)">
            <div class="anno-left"><svg viewBox="0 0 24 24" width="16" height="16"><path d="M19.5 9.5c-1.03 0-1.9.62-2.29 1.5h-2.92c-.39-.88-1.26-1.5-2.29-1.5s-1.9.62-2.29 1.5H6.79c-.39-.88-1.26-1.5-2.29-1.5C3.12 9.5 2 10.62 2 12s1.12 2.5 2.5 2.5c1.03 0 1.9-.62 2.29-1.5h2.92c.39.88 1.26 1.5 2.29 1.5s1.9-.62 2.29-1.5h2.92c.39.88 1.26 1.5 2.29 1.5 1.38 0 2.5-1.12 2.5-2.5s-1.12-2.5-2.5-2.5zM4.5 13c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm7.5 0c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm7.5 0c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1z"/></svg> Route</div>
            <div class="anno-hotkey">R</div>
        </div>
        
        <div class="anno-item" onclick="triggerDraw('Polygon', this)">
            <div class="anno-left"><svg viewBox="0 0 24 24" width="16" height="16"><path d="M12 2l-9 9v11h18V11l-9-9z" fill="none" stroke="#333" stroke-width="2"/></svg> Polygon</div>
            <div class="anno-hotkey">O</div>
        </div>
        
        <div class="anno-item" onclick="triggerDraw('Rectangle', this)">
            <div class="anno-left"><svg viewBox="0 0 24 24" width="16" height="16"><rect x="3" y="3" width="18" height="18" fill="none" stroke="#333" stroke-width="2" rx="2"/></svg> Rectangle</div>
            <div class="anno-hotkey">E</div>
        </div>
        
        <div class="anno-item" onclick="triggerDraw('Circle', this)">
            <div class="anno-left"><svg viewBox="0 0 24 24" width="16" height="16"><circle cx="12" cy="12" r="9" fill="none" stroke="#333" stroke-width="2"/></svg> Circle</div>
            <div class="anno-hotkey">I</div>
        </div>
        
        <div class="anno-divider"></div>
        
        <div class="anno-item" onclick="triggerDraw('MarkerPoint', this)">
            <div class="anno-left"><svg viewBox="0 0 24 24" width="16" height="16"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="none" stroke="#333" stroke-width="1.5"/></svg> Marker</div>
            <div class="anno-hotkey">M</div>
        </div>
        
        <div class="anno-item" onclick="triggerDraw('Line', this)">
            <div class="anno-left"><svg viewBox="0 0 24 24" width="16" height="16"><path d="M3 21L21 3" stroke="#FFCC00" stroke-width="4" stroke-linecap="round" opacity="0.6"/></svg> Highlighter</div>
            <div class="anno-hotkey">H</div>
        </div>
        
        <div class="anno-item" onclick="triggerDraw('Text', this)">
            <div class="anno-left"><svg viewBox="0 0 24 24" width="16" height="16"><path d="M5 4v3h5.5v12h3V7H19V4z"/></svg> Text</div>
            <div class="anno-hotkey">T</div>
        </div>
        
        <div class="anno-item">
            <div class="anno-left"><svg viewBox="0 0 24 24" width="16" height="16"><path d="M3 3h18v18H3z" fill="none" stroke="#333" stroke-width="2"/><path d="M7 7h10v2H7zm0 4h10v2H7zm0 4h6v2H7z"/></svg> Note</div>
            <div class="anno-hotkey">N</div>
        </div>
    </div>

    <div id="felt-search">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="#888"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
        <input type="text" id="map-search-input" placeholder="Search locations..." onkeyup="executeSearch(event)">
    </div>
    <div id="search-results-dropdown"></div>

    <div id="felt-bottom-right">
        <div style="display:flex; flex-direction:column; gap:4px;">
            <div class="ctrl-btn" onclick="map.zoomIn()">+</div>
            <div class="ctrl-btn" onclick="map.zoomOut()">−</div>
        </div>
        <div class="ctrl-btn" style="border-radius: 50%;">?</div>
    </div>

    <div id="map"></div>

    <script>
        // =============================================================================
        // [ ENGINE: LEAFLET INIT & CARTO BASEMAP (FELT STYLE) ]
        // =============================================================================
        const map = L.map('map', { zoomControl: false, attributionControl: false }).setView([__LAT__, __LON__], 15);
        
        // Carto Light mimics Felt's minimal aesthetic
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 }).addTo(map);

        // Geoman Initialization
        map.pm.addControls({ position: 'topleft', drawMarker: true, drawPolygon: true, drawPolyline: true, drawRectangle: true, drawCircle: true, editMode: true, dragMode: true, removalMode: true });

        // =============================================================================
        // [ ENGINE: UI INTERACTION BINDINGS ]
        // =============================================================================
        let activeDrawTool = null;
        
        function clearActiveStyles() {
            document.querySelectorAll('.anno-item').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tool-btn').forEach(el => el.classList.remove('active'));
        }

        window.disableAllDraw = function() {
            map.pm.disableDraw();
            clearActiveStyles();
            document.querySelector('.tool-btn[title="Select"]').classList.add('active');
        }
        
        window.enableCut = function() {
            disableAllDraw();
            map.pm.enableGlobalCutMode();
            document.querySelector('.tool-btn[title="Cut Polygon"]').classList.add('active');
        }

        window.triggerDraw = function(toolShape, element) {
            clearActiveStyles();
            element.classList.add('active');
            
            // Map String to Geoman shapes
            let gmShape = 'Marker';
            if(toolShape === 'MarkerPoint') gmShape = 'CircleMarker';
            if(toolShape === 'Line') gmShape = 'Line';
            if(toolShape === 'Polygon') gmShape = 'Polygon';
            if(toolShape === 'Rectangle') gmShape = 'Rectangle';
            if(toolShape === 'Circle') gmShape = 'Circle';
            if(toolShape === 'Text') gmShape = 'Text';
            
            map.pm.enableDraw(gmShape, {
                snappable: true,
                snapDistance: 20,
                pathOptions: { color: '#FF3366', weight: 3 }
            });
        }

        // =============================================================================
        // [ ENGINE: SEARCH LOGIC ]
        // =============================================================================
        let searchTimeout = null;
        window.executeSearch = function(e) {
            clearTimeout(searchTimeout); 
            const q = e.target.value; 
            const resDiv = document.getElementById('search-results-dropdown');
            if (q.length < 3) { resDiv.style.display = 'none'; return; }
            
            searchTimeout = setTimeout(() => {
                fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}&limit=5`)
                    .then(r => r.json()).then(data => {
                        if (data.length > 0) {
                            resDiv.innerHTML = '';
                            data.forEach(item => {
                                const div = document.createElement('div'); 
                                div.className = 'search-item-res'; 
                                div.innerText = item.display_name;
                                div.onclick = () => { map.flyTo([item.lat, item.lon], 16); resDiv.style.display = 'none'; document.getElementById('map-search-input').value = item.display_name; };
                                resDiv.appendChild(div);
                            });
                            resDiv.style.display = 'block';
                        }
                    });
            }, 400);
        }

        // =============================================================================
        // [ ENGINE: RENDER PYTHON DATA (STREAMLIT INTEGRATION) ]
        // =============================================================================
        let pts = __GEOJSON__;
        
        // Render Radius Boundary
        L.circle([__LAT__, __LON__], { radius: __RADIUS__, color: "#111", weight: 1, fillColor: "#111", fillOpacity: 0.04, dashArray: "4 4" }).addTo(map);
        
        // Render Center Star
        L.marker([__LAT__, __LON__], { icon: L.divIcon({ html: '<div style="background:#FF3366; color:white; width:24px; height:24px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:14px; font-weight:800; border:2px solid #fff; box-shadow:0 2px 4px rgba(0,0,0,0.2);">★</div>', className:'', iconSize:[28,28] }), zIndexOffset: 10000 }).addTo(map);

        // Simple render of POIs (Pins)
        if (pts.length > 0) {
            const markers = [];
            pts.forEach(p => {
                const pin = L.marker([p.lat, p.lon], { 
                    icon: L.divIcon({ 
                        html: `<svg viewBox="0 0 24 24" width="24" height="24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="#003366" stroke="#ffffff" stroke-width="1.5"/></svg>`, 
                        className: '', iconSize: [24, 24], iconAnchor: [12, 24] 
                    }) 
                }).bindTooltip(p.name, {className: 'felt-tooltip', direction: 'top'});
                markers.push(pin);
                pin.addTo(map);
            });
            
            if (!__IS_STALE__) {
                const group = new L.featureGroup(markers);
                map.fitBounds(group.getBounds().pad(0.1));
            }
        }
    </script>
</body>
</html>
"""

leaflet_html = (leaflet_template
                .replace("__LAT__", str(lat_coord))
                .replace("__LON__", str(lon_coord))
                .replace("__RADIUS__", str(radius_val))
                .replace("__IS_STALE__", is_stale)
                .replace("__GEOJSON__", geojson_str))

# Injected full screen iframe
st.components.v1.html(leaflet_html, height=850, scrolling=False)
