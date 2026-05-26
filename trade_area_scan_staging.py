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

st.set_page_config(page_title="Trade Area Scan Playground", layout="wide", initial_sidebar_state="expanded")

# =============================================================================
# [ CONFIGURATION BLOCK: GLOBAL CSS STYLES (FELT MINIMALISM) ]
# =============================================================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Montserrat:wght@400;500;600;700;800&display=swap');
        
        :root {
            --brand-midnight: #1a1a1a !important; /* Softened dark for modern look */
            --brand-gold: #e84c3d !important;     /* Changed to a Felt-like soft red/orange accent */
            --brand-dark: #0f0f0f !important;     
            --white-clean: #ffffff !important;
            --bg-offwhite: #f9fafb !important;    /* Ultra light gray for sidebar */
            --text-muted: #6b7280 !important;
            --soft-shadow: 0 2px 8px rgba(0, 0, 0, 0.05) !important;
        }
        
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: var(--white-clean) !important; 
            color: var(--brand-midnight) !important; 
            font-family: 'Inter', sans-serif !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: var(--bg-offwhite) !important; 
            color: var(--brand-midnight) !important;
            border-right: 1px solid #e5e7eb !important; 
            width: 300px !important; min-width: 300px !important; max-width: 300px !important;
            box-shadow: var(--soft-shadow) !important;
        }
        
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"], [data-testid="stHeader"], header, #stDecoration, .stDeployButton, footer { display: none !important; }
        ::-webkit-scrollbar { width: 4px !important; background: transparent !important; }
        ::-webkit-scrollbar-thumb { background: #d1d5db !important; border-radius: 4px !important; }
        
        p, label, h1, h2, h3, h4, h5, h6, .stMarkdown, [data-testid="stExpander"] summary p { 
            color: var(--brand-midnight) !important; 
            font-family: 'Inter', sans-serif !important; 
        }
        
        [data-testid="stAppViewContainer"] { display: flex !important; flex-direction: row !important; width: 100vw !important; height: 100vh !important; overflow: hidden !important; }
        [data-testid="stMain"] { flex-grow: 1 !important; width: calc(100vw - 300px) !important; height: 100vh !important; overflow: hidden !important; margin: 0px !important; padding: 0px !important; }
        .block-container, [data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"], .stElementContainer { padding: 0px !important; margin: 0px !important; max-width: 100% !important; gap: 0rem !important; }
        iframe { height: 100vh !important; width: 100% !important; border: none !important; display: block !important; }
        
        [data-testid="stSidebarUserContent"] { padding-top: 24px !important; padding-left: 20px !important; padding-right: 20px !important; height: 100vh !important; overflow-y: auto !important; overflow-x: hidden !important; }
        
        /* Minimalist Inputs */
        div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="number-input"] { 
            background-color: var(--white-clean) !important; 
            border: 1px solid #e5e7eb !important; 
            border-radius: 6px !important; 
            box-shadow: var(--soft-shadow) !important; 
            padding: 2px !important;
        }
        div[data-baseweb="input"]:focus-within, div[data-baseweb="number-input"]:focus-within { 
            border-color: var(--brand-gold) !important; 
            box-shadow: 0 0 0 1px var(--brand-gold) !important;
        }
        
        /* Primary Buttons Customization (Pill Shaped) */
        div.stButton > button[kind="secondary"], div.stDownloadButton > button { 
            background-color: var(--brand-midnight) !important; 
            border: none !important; 
            border-radius: 8px !important; 
            width: 100% !important; 
            padding: 8px 12px !important; 
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important; 
            transition: all 0.2s ease !important; 
        }
        div.stButton > button[kind="secondary"]:hover, div.stDownloadButton > button:hover { 
            background-color: var(--brand-gold) !important; 
            transform: translateY(-1px);
        }
        div.stButton > button[kind="secondary"] p, div.stDownloadButton > button p { 
            color: var(--white-clean) !important; 
            font-weight: 600 !important; 
            font-size: 11px !important; 
            text-transform: uppercase !important; 
            letter-spacing: 0.5px; 
        }
        
        /* Secondary Action Buttons (e.g. Clear All) */
        div.stButton > button[kind="primary"] { background: transparent !important; border: none !important; color: var(--text-muted) !important; box-shadow: none !important; padding: 0 !important; margin-top: 6px; display: inline-flex; }
        div.stButton > button[kind="primary"] p { color: var(--text-muted) !important; font-size: 10px !important; font-weight: 600 !important; text-decoration: none !important; text-transform: uppercase; }
        div.stButton > button[kind="primary"]:hover p { color: var(--brand-gold) !important; }
        
        /* Expanders & Checkboxes */
        [data-testid="stSidebar"] .st-expander { border: 1px solid #e5e7eb !important; background-color: var(--white-clean) !important; border-radius: 8px !important; margin-bottom: 8px !important; overflow: hidden !important; box-shadow: var(--soft-shadow) !important;}
        [data-testid="stSidebar"] .st-expander summary { padding: 12px !important; }
        [data-testid="stSidebar"] .st-expander summary p { font-size: 11px !important; font-weight: 600 !important; }
        .stCheckbox label p { font-size: 12px !important; font-weight: 500 !important; color: #4b5563 !important;}
        div[data-baseweb="checkbox"] input:checked + div, div[data-baseweb="checkbox"] div[aria-checked="true"] { background-color: var(--brand-midnight) !important; border-color: var(--brand-midnight) !important; }
        
        .brand-title { font-family: 'Inter', sans-serif !important; font-weight: 700; color: var(--brand-midnight); font-size: 22px; text-align: left; padding-bottom: 12px; margin-bottom: 20px; }
        .stTextInput label p, .stNumberInput label p { font-size: 10px !important; font-weight: 600 !important; letter-spacing: 0.5px; color: var(--text-muted) !important; text-transform: uppercase;}
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# [ CORE LOGIC: HAVERSINE DISTANCE FILTER ]
# =============================================================================
def calculate_haversine(lat1, lon1, lat2, lon2):
    R = 6371000  
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# =============================================================================
# [ CONFIGURATION BLOCK: SESSION STATE & POI DICTIONARY ]
# =============================================================================
DEFAULT_COORDS = "14.5995, 120.9842"
DEFAULT_RADIUS = 1000

if 'geo_coords' not in st.session_state: st.session_state.geo_coords = DEFAULT_COORDS
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = DEFAULT_RADIUS
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'last_scan_lat' not in st.session_state: st.session_state.last_scan_lat = 14.5995
if 'last_scan_lon' not in st.session_state: st.session_state.last_scan_lon = 120.9842

POI_CONFIG = {
    "COMMERCIAL": [['Corporate Office', '"building"~"office|commercial",i'], ['IT/Tech Center', '"office"~"it|telecommunication",i'], ['Business Center', '"building"="commercial"'], ['Hospital', '"amenity"~"hospital|clinic",i'], ['Hotel', '"tourism"="hotel"'], ['Motel', '"tourism"="motel"']],
    "RESIDENTIAL": [['Apartments', '"building"="apartments"'], ['House', '"building"="house"'], ['Residential Area', '"landuse"="residential"'], ['Condominium', '"building"="residential"']],
    "RETAIL": [['Mall/Department Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"supermarket|grocery",i'], ['Convenience Store', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"']],
    "FOOD AND BEVERAGES": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee Shop', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"'], ['Bar/Pub', '"amenity"~"bar|pub|nightclub",i']],
}

ADVANCED_CONFIG = {
    "AMENITIES": [['ATM', '"amenity"="atm"'], ['Bank', '"amenity"="bank"'], ['Parking', '"amenity"="parking"']],
    "MISCELLANEOUS": [['Busstop', '"highway"="bus_stop"'], ['Construction', '"landuse"="construction"']]
}

# =============================================================================
# [ CONFIGURATION BLOCK: SIDEBAR UI & LOGIC ]
# =============================================================================
with st.sidebar:
    st.markdown('<div class="brand-title">Trade Area Scan</div>', unsafe_allow_html=True)
    
    if st.session_state.scanned_records:
        st.download_button(
            label=f"💾 Export {len(st.session_state.scanned_records)} POIs", 
            data=json.dumps(st.session_state.scanned_records, indent=4), 
            file_name="TradeArea_Data.json", 
            mime="application/json",
            use_container_width=True,
            type="primary"
        )
    else:
        st.download_button(
            label="Save Project (Empty)", 
            data=json.dumps([]), 
            file_name="TradeArea_Data.json", 
            mime="application/json",
            use_container_width=True,
            disabled=True
        )
    
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    location_input = st.text_input("Location Search or Coordinates", value=st.session_state.geo_coords, key="geo_coords_input")
    radius_val = st.number_input("Radius (Meters)", min_value=100, max_value=50000, value=st.session_state.geo_radius, key="geo_radius_input", step=100)
    st.session_state.geo_radius = radius_val

    coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", location_input)
    
    if coord_match:
        lat_coord, lon_coord = float(coord_match.group(1)), float(coord_match.group(2))
        st.session_state.geo_coords = location_input
    else:
        if location_input and location_input != st.session_state.get('last_geocoded_query', ''):
            with st.spinner("Locating via Nominatim..."):
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

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    search_query = st.text_input("Filter Tags", placeholder="e.g. cafe, residential...").lower()
    
    selected_tags = []
    for cat_name, node_items in POI_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for label, tag in matched:
                    if st.checkbox(label, key=f"chk_{cat_name}_{label}"): selected_tags.append(tag)

    st.markdown("<div style='font-weight: 700; font-size: 10px; margin-top: 20px; margin-bottom: 10px; color: #9ca3af; letter-spacing: 1px; text-transform: uppercase;'>Advanced POIs</div>", unsafe_allow_html=True)
    with st.container():
        for cat_name, node_items in ADVANCED_CONFIG.items():
            matched = [item for item in node_items if search_query in item[0].lower()]
            if matched:
                with st.expander(cat_name, expanded=(len(search_query) > 0)):
                    for label, tag in matched:
                        if st.checkbox(label, key=f"chk_adv_{cat_name}_{label}"): selected_tags.append(tag)

    st.markdown("<br>", unsafe_allow_html=True)
    
    OVERPASS_ENDPOINTS = [
        "https://overpass-api.de/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
    ]

    if st.button("Scan Area", type="secondary", use_container_width=True, key="scan_btn"):
        if not selected_tags:
            st.error("Select ≥ 1 tag.")
        else:
            status_indicator = st.empty()
            with st.spinner("Extracting nodes..."):
                success = False
                status_indicator.info("Scanning via OSMnx...")
                try:
                    ox.settings.use_cache = False
                    ox.settings.log_console = False

                    osmnx_tags = {}
                    for tag_str in selected_tags:
                        match = re.search(r'"([^"]+)"(=|~)"([^"]+)"', tag_str)
                        if match:
                            k, op, v = match.group(1), match.group(2), match.group(3)
                            val = True if v == '.' else (v.split('|') if '|' in v else v)
                            
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
                            p_lat, p_lon = (geom.y, geom.x) if geom.geom_type == 'Point' else (geom.centroid.y, geom.centroid.x)
                            
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
                                    "lat": float(p_lat), "lon": float(p_lon), 
                                    "name": str(name), "type": str(p_type), 
                                    "geomType": str(geom.geom_type), "shape": "Drop"
                                })
                        
                        st.session_state.scanned_records = records
                        st.session_state.last_scan_lat, st.session_state.last_scan_lon = lat_coord, lon_coord
                        success = True
                        status_indicator.success(f"Success! Found {len(records)} bounded POIs.")
                    else:
                        st.session_state.scanned_records = []
                        success = True
                        status_indicator.warning("0 POIs found in this radius.")

                except Exception as e:
                    status_indicator.warning("OSMnx failed. Trying Overpass Turbo...")
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
                                                "lat": float(e_lat), "lon": float(e_lon), 
                                                "name": str(tags.get('name', 'Unknown')), 
                                                "type": str(p_type), 
                                                "geomType": str("Point" if el.get('type') == 'node' else "Polygon"),
                                                "shape": "Drop"
                                            })
                                st.session_state.scanned_records = records
                                st.session_state.last_scan_lat, st.session_state.last_scan_lon = lat_coord, lon_coord
                                success = True
                                status_indicator.success(f"Overpass extracted {len(records)} bounded POIs.")
                                break
                        except Exception:
                            continue
                        
                if success:
                    import time
                    time.sleep(1.5)
                    status_indicator.empty()
                    st.rerun() 
                else:
                    status_indicator.error("Critical Error: All extraction engines failed.")

    if st.button("Clear Canvas", type="primary", key="clear_btn"):
        st.session_state.scanned_records = []
        for key in list(st.session_state.keys()):
            if key.startswith("chk_"):
                st.session_state[key] = False
        st.rerun()

# =============================================================================
# [ CONFIGURATION BLOCK: LEAFLET ENGINE (FELT UI OVERHAUL) ]
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
    
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* --- CORE MAP CSS --- */
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #f3f4f6; overflow: hidden; font-family: 'Inter', sans-serif; }
        #map { height: 100vh; width: 100%; }
        
        /* --- FELT-STYLE TOP CENTER TOOLBAR --- */
        .felt-top-toolbar {
            position: absolute;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #ffffff;
            border-radius: 12px;
            display: flex;
            align-items: center;
            padding: 6px 12px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.05);
            z-index: 2000;
            border: 1px solid #f3f4f6;
            gap: 12px;
        }
        .felt-tool-btn {
            background: transparent;
            border: none;
            cursor: pointer;
            padding: 8px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #4b5563;
            transition: all 0.2s;
        }
        .felt-tool-btn:hover { background: #f3f4f6; color: #111827; }
        .felt-tool-btn svg { width: 18px; height: 18px; fill: currentColor; }
        
        /* --- SEARCH BAR UI (Floating Top Left) --- */
        #search-container { position: absolute; top: 20px; left: 20px; z-index: 1000; width: 280px; }
        #map-search { 
            width: 100%; padding: 12px 16px 12px 40px; 
            border: 1px solid #f3f4f6; border-radius: 12px; 
            font-size: 13px; font-weight: 500; color: #111827; 
            outline: none; box-sizing: border-box; 
            box-shadow: 0 4px 16px rgba(0,0,0,0.08); 
            background: #ffffff url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%239ca3af" width="16" height="16"><path d="M10 2a8 8 0 105.293 14.707l5 5a1 1 0 001.414-1.414l-5-5A8 8 0 0010 2zm0 2a6 6 0 110 12 6 6 0 010-12z"/></svg>') no-repeat 14px center;
        }
        #map-search:focus { box-shadow: 0 4px 16px rgba(0,0,0,0.12), 0 0 0 2px #e84c3d; }
        #search-results { position: absolute; top: 52px; left: 0; width: 100%; background: #ffffff; border-radius: 8px; display: none; max-height: 250px; overflow-y: auto; border: 1px solid #f3f4f6; z-index: 1001; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin-top: 8px;}
        .search-item { padding: 10px 16px; font-size: 12px; font-weight: 500; cursor: pointer; border-bottom: 1px solid #f9fafb; color: #374151; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .search-item:hover { background: #f9fafb; color: #e84c3d; }

        /* --- FLOATING BASEMAP PANEL --- */
        #minimal-basemap-panel { 
            position: absolute; top: 70px; left: 50%; transform: translateX(-50%); 
            z-index: 2000; background: #ffffff; border-radius: 12px; 
            border: 1px solid #f3f4f6; display: none; flex-direction: column; 
            padding: 8px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); width: 200px; 
        }
        #minimal-basemap-panel select { border: 1px solid #e5e7eb; border-radius: 6px; padding: 8px; font-size: 12px; font-weight: 500; color: #111827; background: #f9fafb; outline: none; cursor: pointer; width: 100%; margin-bottom: 8px;}
        .minimal-label { font-size: 11px; font-weight: 600; padding: 6px; display: flex; align-items: center; gap: 8px; cursor: pointer; color: #4b5563; margin: 0; }

        /* --- DYNAMIC SIDEBAR LIST UI (Floating Card) --- */
        #scan-results-panel { 
            position: absolute; top: 20px; right: 20px; z-index: 1000; 
            background: #ffffff; width: 300px; max-height: calc(100vh - 40px); 
            border-radius: 12px; border: 1px solid #f3f4f6; 
            display: flex; flex-direction: column; overflow: hidden; 
            box-shadow: 0 10px 25px rgba(0,0,0,0.08); 
        }
        .results-header { background: #ffffff; color: #111827; padding: 14px 16px; font-size: 14px; font-weight: 700; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f3f4f6; }
        .manage-layers-btn { background: #f9fafb; color: #4b5563; padding: 8px; text-align: center; font-size: 11px; font-weight: 600; border-bottom: 1px solid #e5e7eb; cursor: pointer; text-transform: uppercase; transition: background 0.2s;}
        .manage-layers-btn:hover { background: #f3f4f6; color: #111827;}

        .results-list { overflow-y: auto; flex-grow: 1; padding-bottom: 8px; }
        .layer-category-block { border-bottom: 1px solid #f3f4f6; background: #fff;}
        .layer-category-header { background: #ffffff; padding: 10px 16px; display: flex; align-items: center; justify-content: space-between; user-select: none; border-left: 3px solid transparent;}
        .layer-category-header:hover { background: #f9fafb; border-left: 3px solid #e84c3d;}
        .layer-header-left { display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 600; color: #374151;}
        .layer-category-items { padding: 0; background: #f9fafb; }
        .layer-category-items.collapsed { display: none !important; }
        
        .results-item { padding: 8px 16px 8px 32px; font-size: 11px; font-weight: 500; color: #6b7280; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f3f4f6; background: #fff;}
        .results-item:hover { background: #f9fafb; color: #111827; }
        
        /* Manage Mode Controls */
        .manage-tools { display: none; }
        .manage-mode-active .manage-tools { display: flex; }
        .icon-btn { cursor: pointer; padding: 4px; margin-left:4px; fill: #9ca3af; transition: fill 0.2s; border-radius: 4px;}
        .icon-btn:hover { fill: #111827; background: #f3f4f6;}
        .icon-btn.del:hover { fill: #ef4444; background: #fee2e2;}
        .add-layer-btn { display: block; width: 100%; text-align: center; padding: 12px; background: #f9fafb; color: #4b5563; font-size: 11px; font-weight: 600; cursor: pointer; border-top: 1px solid #f3f4f6; text-transform: uppercase;}
        .add-layer-btn:hover { background: #f3f4f6; color: #111827;}

        /* Map Labels */
        .poi-text-label { background: #ffffff; border: none; padding: 4px 6px; border-radius: 4px; font-size: 10px; font-family: 'Inter', sans-serif; font-weight: 600; box-shadow: 0 2px 6px rgba(0,0,0,0.15); color: #111827;}
        .hide-labels .poi-text-label { display: none !important; }
        .color-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; cursor: pointer;}
        
        /* Geoman Tool Overrides - Tucked away */
        .leaflet-pm-toolbar { margin-top: 80px !important; margin-left: 20px !important; box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important; border: none !important; border-radius: 8px !important; overflow: hidden; }
        
        /* Edit Popup */
        .edit-form-container { display: flex; flex-direction: column; gap: 8px; font-family: 'Inter', sans-serif; min-width: 200px;}
        .edit-form-container label { font-size: 10px; font-weight: 600; color: #6b7280; text-transform: uppercase; margin-bottom: -4px;}
        .edit-form-container input[type="text"], .edit-form-container select { width: 100%; border: 1px solid #e5e7eb; border-radius: 4px; padding: 6px; font-family: inherit; font-size: 12px; font-weight: 500; color: #111827; outline: none; background: #f9fafb;}
        .edit-form-container button { background: #111827; color: white; border: none; padding: 8px; border-radius: 4px; cursor: pointer; font-size: 11px; font-weight: 600; margin-top: 4px;}
        .edit-form-container button:hover { background: #e84c3d; }
        
        .routing-active-indicator { display: none; position: absolute; bottom: 30px; left: 50%; transform: translateX(-50%); background: #111827; color: #fff; font-weight: 600; padding: 10px 24px; border-radius: 30px; z-index: 2000; font-size: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); cursor: pointer;}
        body.routing-mode .routing-active-indicator { display: block; }
        body.routing-mode #map { cursor: crosshair !important; }
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="routing-active-indicator" onclick="cancelRouting()">Cancel Routing (Click Point A, then B)</div>
    
    <div id="search-container">
        <input type="text" id="map-search" placeholder="Search locations..." onkeyup="handleSearch(event)">
        <div id="search-results"></div>
    </div>

    <div class="felt-top-toolbar">
        <button class="felt-tool-btn" title="Map Settings" onclick="toggleLayerMenu(event)">
            <svg viewBox="0 0 24 24"><path d="M11.99 18.54l-7.37-5.73L3 14.07l9 7 9-7-1.63-1.27-7.38 5.74zM12 16l7.36-5.73L21 9l-9-7-9 7 1.63 1.27L12 16z"/></svg>
        </button>
        <div style="width: 1px; height: 20px; background: #e5e7eb;"></div>
        <button class="felt-tool-btn" title="Draw Route" onclick="startRouting(event)">
            <svg viewBox="0 0 24 24"><path d="M19.5 9.5c-1.03 0-1.9.62-2.29 1.5h-2.92c-.39-.88-1.26-1.5-2.29-1.5s-1.9.62-2.29 1.5H6.79c-.39-.88-1.26-1.5-2.29-1.5C3.12 9.5 2 10.62 2 12s1.12 2.5 2.5 2.5c1.03 0 1.9-.62 2.29-1.5h2.92c.39.88 1.26 1.5 2.29 1.5s1.9-.62 2.29-1.5h2.92c.39.88 1.26 1.5 2.29 1.5 1.38 0 2.5-1.12 2.5-2.5s-1.12-2.5-2.5-2.5zM4.5 13c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm7.5 0c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm7.5 0c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1z"/></svg>
        </button>
    </div>

    <div id="minimal-basemap-panel">
        <select id="basemap-select" onchange="switchActiveBasemap(this.value)">
            <option value="carto">Carto Light (Clean)</option>
            <option value="osm">OpenStreetMap</option>
            <option value="satellite">Google Satellite</option>
        </select>
        <label class="minimal-label" for="label-toggle-chk">
            <input type="checkbox" id="label-toggle-chk" checked style="margin:0; cursor: pointer;" onchange="toggleLabelsMatrix(this.checked)"> Show POI Labels
        </label>
    </div>

    <div id="scan-results-panel">
        <div class="results-header"><span>Map Layers</span><span id="results-count" style="color:#e84c3d; background: #fee2e2; padding: 2px 8px; border-radius: 12px; font-size: 12px;">0</span></div>
        <div class="manage-layers-btn" onclick="toggleManageLayers()">⚙️ Manage Map Elements</div>
        <div class="results-list" id="results-list-box"></div>
        <div class="add-layer-btn" onclick="createNewLayer()">+ Add Layer Group</div>
    </div>

    <script>
        const map = L.map('map', { zoomControl: false, attributionControl: false }).setView([__LAT__, __LON__], 14);
        L.control.zoom({ position: 'bottomleft' }).addTo(map);

        const basemaps = {
            osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }),
            satellite: L.tileLayer('http://www.google.cn/maps/vt?lyrs=s@189&gl=cn&x={x}&y={y}&z={z}', { maxZoom: 20 }),
            carto: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 })
        };
        
        let activeBasemapKey = 'carto';
        basemaps[activeBasemapKey].addTo(map);

        function switchActiveBasemap(targetKey) {
            map.removeLayer(basemaps[activeBasemapKey]);
            basemaps[targetKey].addTo(map);
            activeBasemapKey = targetKey;
        }

        function toggleLabelsMatrix(isShown) {
            if (isShown) document.getElementById('map').classList.remove('hide-labels');
            else document.getElementById('map').classList.add('hide-labels');
        }

        map.pm.addControls({ position: 'topleft', drawMarker: true, drawCircleMarker: false, drawPolyline: true, drawRectangle: true, drawPolygon: true, drawCircle: true, editMode: true, dragMode: true, cutPolygon: false, removalMode: true });

        function toggleLayerMenu(e) { 
            e.preventDefault(); 
            const panel = document.getElementById('minimal-basemap-panel'); 
            panel.style.display = panel.style.display === 'flex' ? 'none' : 'flex'; 
        }

        let searchTimeout = null;
        function handleSearch(e) {
            clearTimeout(searchTimeout); const q = e.target.value; const resDiv = document.getElementById('search-results');
            if (q.length < 3) { resDiv.style.display = 'none'; return; }
            searchTimeout = setTimeout(() => {
                fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}&limit=5`)
                    .then(r => r.json()).then(data => {
                        if (data.length > 0) {
                            resDiv.innerHTML = '';
                            data.forEach(item => {
                                const div = document.createElement('div'); div.className = 'search-item'; div.innerText = item.display_name;
                                div.onclick = () => { map.flyTo([item.lat, item.lon], 16); resDiv.style.display = 'none'; document.getElementById('map-search').value = ''; };
                                resDiv.appendChild(div);
                            });
                            resDiv.style.display = 'block';
                        }
                    });
            }, 500);
        }

        let pts = __GEOJSON__;
        let globalIdCounter = 0; pts.forEach(p => p._uid = globalIdCounter++);
        
        const catPalette = ["#111827", "#e84c3d", "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#14b8a6", "#64748b"];
        let layerGroupsRef = {};
        let categoryColors = {}; let colorIndex = 0;
        let globalSortableInstances = [];

        map.on('contextmenu', function(e) {
            const lat = e.latlng.lat, lng = e.latlng.lng;
            const content = `
                <div style="font-family: Inter; font-size: 11px; color: #111827;">
                    <div style="font-weight: 700; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; margin-bottom: 6px;">Location Actions</div>
                    <div style="cursor:pointer; padding:4px 0; color: #4b5563;" onclick="navigator.clipboard.writeText('${lat.toFixed(5)},${lng.toFixed(5)}'); map.closePopup();">Copy Coordinates</div>
                    <div style="cursor:pointer; padding:4px 0; color: #4b5563;" onclick="window.open('https://www.google.com/maps?q=$${lat},${lng}', '_blank'); map.closePopup();">Open in Google Maps</div>
                </div>`;
            L.popup({className: 'minimal-popup'}).setLatLng(e.latlng).setContent(content).openOn(map);
        });

        let isRoutingMode = false; let routeWaypoints = []; 
        let tempMarker1 = null; let tempMarker2 = null;

        window.startRouting = function(e) { e.preventDefault(); isRoutingMode = true; routeWaypoints = []; document.body.classList.add('routing-mode'); }
        window.cancelRouting = function() { 
            isRoutingMode = false; routeWaypoints = []; document.body.classList.remove('routing-mode'); 
            if(tempMarker1) map.removeLayer(tempMarker1); 
            if(tempMarker2) map.removeLayer(tempMarker2);
        }
        
        map.on('click', function(e) {
            if(!isRoutingMode) return;
            routeWaypoints.push(e.latlng);
            
            if(routeWaypoints.length === 1) {
                tempMarker1 = L.circleMarker(e.latlng, {radius: 6, color: '#e84c3d', fillOpacity: 1}).addTo(map);
            } else if(routeWaypoints.length === 2) {
                tempMarker2 = L.circleMarker(e.latlng, {radius: 6, color: '#e84c3d', fillOpacity: 1}).addTo(map);
                
                const url = `https://router.project-osrm.org/route/v1/driving/${routeWaypoints[0].lng},${routeWaypoints[0].lat};${routeWaypoints[1].lng},${routeWaypoints[1].lat}?geometries=geojson`;
                fetch(url).then(r=>r.json()).then(data => {
                    if(data.routes && data.routes.length > 0) {
                        const coords = data.routes[0].geometry.coordinates.map(c => [c[1], c[0]]);
                        const routePoly = L.polyline(coords, {color: '#e84c3d', weight: 4, dashArray: '5, 10'}).addTo(map);
                        
                        const newUid = globalIdCounter++;
                        pts.push({ _uid: newUid, name: 'Driving Route', type: 'Routes', geomType: 'Polyline', _layer: routePoly, color: '#e84c3d', weight: 4 });
                        routePoly.on('contextmenu', (evt) => openStyleEditor(evt, newUid));
                        renderSidebar();
                    }
                });
                cancelRouting();
            }
        });

        map.on('pm:create', (e) => {
            const layer = e.layer;
            const newUid = globalIdCounter++;
            let gType = e.shape; 
            
            if (gType === 'Circle') {
                layer.bindTooltip(`Rad: ${Math.round(layer.getRadius())}m`, {permanent: true, direction: 'center', className: 'poi-text-label'});
            }

            pts.push({ _uid: newUid, name: 'Drawn ' + gType, type: 'Annotations', geomType: gType, _layer: layer, color: '#3b82f6', opacity: 0.2, weight: 2 });
            layer.on('contextmenu', (evt) => openStyleEditor(evt, newUid));
            layer.on('pm:edit', (evt) => { if(gType === 'Circle') layer.setTooltipContent(`Rad: ${Math.round(layer.getRadius())}m`); });
            
            renderSidebar();
        });

        const createPinIcon = (color, shapeStr) => {
            let svgMarkup = '';
            if (shapeStr === 'Circle') {
                svgMarkup = `<svg viewBox="0 0 24 24" width="14" height="14"><circle cx="12" cy="12" r="10" fill="${color}" stroke="#ffffff" stroke-width="3"/></svg>`;
            } else {
                // Modern Felt-like Pin
                svgMarkup = `<svg viewBox="0 0 24 24" width="28" height="28"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="${color}" stroke="#ffffff" stroke-width="1.5" style="filter: drop-shadow(0px 4px 4px rgba(0,0,0,0.15));"/></svg>`;
            }
            return L.divIcon({ html: svgMarkup, className: '', iconSize: [28, 28], iconAnchor: [14, 28] });
        };

        function renderSidebar() {
            const categoryMap = {};
            pts.forEach(p => {
                const layerKey = p.type || 'Unclassified';
                if (!categoryMap[layerKey]) { categoryMap[layerKey] = []; if(!categoryColors[layerKey]) categoryColors[layerKey] = catPalette[colorIndex++ % catPalette.length]; }
                categoryMap[layerKey].push(p);
            });

            Object.values(layerGroupsRef).forEach(layer => map.removeLayer(layer)); layerGroupsRef = {};
            
            Object.keys(categoryMap).forEach(key => {
                layerGroupsRef[key] = L.layerGroup().addTo(map);
                const pColor = categoryColors[key];
                
                categoryMap[key].forEach(p => {
                    if(!p._layer) {
                        p._layer = L.marker([p.lat, p.lon], { icon: createPinIcon(p.color || pColor, p.shape) });
                        if(p.name && p.name !== 'Unknown') p._layer.bindTooltip(p.name, { permanent: true, direction: 'top', offset: [0, -20], className: 'poi-text-label' });
                        p._layer.on('contextmenu', (evt) => openStyleEditor(evt, p._uid));
                    }
                    if(!map.hasLayer(p._layer)) p._layer.addTo(layerGroupsRef[key]);
                });
            });

            const listBox = document.getElementById('results-list-box');
            document.getElementById('results-count').innerText = pts.length;
            let htmlPayload = '';

            const pencilSvg = `<svg height="14" viewBox="0 -960 960 960" width="14"><path d="M200-200h57l391-391-57-57-391 391v57Zm-80 80v-170l528-527q12-11 26.5-17t30.5-6q16 0 31 6t26 18l55 56q12 11 17.5 26t5.5 30q0 16-5.5 30.5T817-647L290-120H120Z"/></svg>`;
            const trashSvg = `<svg height="14" viewBox="0 -960 960 960" width="14"><path d="M280-120q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Z"/></svg>`;

            Object.keys(categoryMap).forEach(catName => {
                htmlPayload += `
                    <div class="layer-category-block" data-id="${catName}">
                        <div class="layer-category-header">
                            <div class="layer-header-left">
                                <input type="checkbox" checked onclick="toggleCategoryVisibility('${catName}', this.checked)" style="accent-color: #111827;">
                                <span class="color-dot" style="background-color: ${categoryColors[catName]};"></span>
                                <span onclick="toggleAccordionCollapse('${catName}')" style="cursor:pointer;">${catName} <span style="color:#9ca3af; font-size:10px;">(${categoryMap[catName].length})</span></span>
                            </div>
                            <div class="manage-tools">
                                <div class="icon-btn" title="Edit Color" onclick="batchEditLayer('${catName}')">${pencilSvg}</div>
                            </div>
                        </div>
                        <div class="layer-category-items" id="items-${catName.replace(/\\s/g, '')}">
                `;
                categoryMap[catName].forEach(p => {
                    htmlPayload += `
                    <div class="results-item" data-uid="${p._uid}">
                        <div style="flex-grow:1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; cursor:pointer;" onclick="map.flyTo(${p.lat ? `[${p.lat}, ${p.lon}]` : `pts.find(x=>x._uid==${p._uid})._layer.getBounds().getCenter()`}, 17);">${p.name || 'Asset'}</div>
                        <div class="manage-tools">
                            <div class="icon-btn" onclick="openStyleEditor(null, ${p._uid})">${pencilSvg}</div>
                            <div class="icon-btn del" onclick="removePoiInstance(${p._uid})">${trashSvg}</div>
                        </div>
                    </div>`;
                });
                htmlPayload += '</div></div>';
            });
            listBox.innerHTML = htmlPayload;

            globalSortableInstances.forEach(inst => inst.destroy()); globalSortableInstances = [];
            globalSortableInstances.push(new Sortable(listBox, { animation: 150, handle: '.layer-category-header', filter: ':not(.manage-mode-active *)' }));
            
            document.querySelectorAll('.layer-category-items').forEach(el => {
                globalSortableInstances.push(new Sortable(el, {
                    group: 'shared', animation: 150, filter: ':not(.manage-mode-active *)',
                    onEnd: function (evt) {
                        const itemUid = parseInt(evt.item.getAttribute('data-uid'));
                        const newCat = evt.to.parentElement.getAttribute('data-id');
                        const p = pts.find(x => x._uid === itemUid);
                        if(p && newCat) p.type = newCat;
                        setTimeout(renderSidebar, 50);
                    }
                }));
            });
        }

        window.toggleManageLayers = function() {
            document.getElementById('scan-results-panel').classList.toggle('manage-mode-active');
        }

        window.openStyleEditor = function(e, uid) {
            const p = pts.find(x => x._uid === uid); if(!p) return;
            const isMarker = (!p.geomType || p.geomType === 'Point' || p.geomType === 'Marker');
            
            const formHtml = `
                <div class="edit-form-container">
                    <label>Element Label</label>
                    <input type="text" id="edit-name-${uid}" value="${p.name || ''}">
                    <label>Group</label>
                    <input type="text" id="edit-type-${uid}" value="${p.type || ''}">
                    <label>Color</label>
                    <input type="color" id="edit-color-${uid}" value="${p.color || categoryColors[p.type] || '#111827'}" style="height:30px; padding:0; border:none;">
                    ${isMarker ? `
                    <label>Marker Style</label>
                    <select id="edit-shape-${uid}">
                        <option value="Drop" ${(!p.shape || p.shape === 'Drop') ? 'selected' : ''}>Felt Pin</option>
                        <option value="Circle" ${p.shape === 'Circle' ? 'selected' : ''}>Minimal Dot</option>
                    </select>` : ''}
                    <button onclick="saveStyleEditor(${uid})">Save Changes</button>
                </div>
            `;
            const loc = e ? e.latlng : (p.lat ? [p.lat, p.lon] : p._layer.getBounds().getCenter());
            L.popup().setLatLng(loc).setContent(formHtml).openOn(map);
        }

        window.saveStyleEditor = function(uid) {
            const p = pts.find(x => x._uid === uid); if(!p) return;
            p.name = document.getElementById(`edit-name-${uid}`).value;
            p.type = document.getElementById(`edit-type-${uid}`).value;
            p.color = document.getElementById(`edit-color-${uid}`).value;
            
            if(!p.geomType || p.geomType === 'Point' || p.geomType === 'Marker') {
                p.shape = document.getElementById(`edit-shape-${uid}`) ? document.getElementById(`edit-shape-${uid}`).value : 'Drop';
                p._layer.setIcon(createPinIcon(p.color, p.shape));
            } else {
                p._layer.setStyle({color: p.color, fillColor: p.color});
            }
            map.closePopup(); renderSidebar();
        }

        window.batchEditLayer = function(catKey) {
            const newColor = prompt(`Enter HEX color to override all elements in [${catKey}]:`, categoryColors[catKey]);
            if(newColor && /^#[0-9A-F]{6}$/i.test(newColor)) {
                categoryColors[catKey] = newColor;
                pts.filter(p => p.type === catKey).forEach(p => { 
                    p.color = newColor; 
                    if(p._layer && (!p.geomType || p.geomType === 'Point')) p._layer.setIcon(createPinIcon(newColor, p.shape)); 
                    if(p._layer && p.geomType && p.geomType !== 'Point') p._layer.setStyle({color: newColor, fillColor: newColor});
                });
                renderSidebar();
            }
        }

        window.removePoiInstance = function(uid) {
            const idx = pts.findIndex(item => item._uid === uid);
            if (idx > -1) { const p = pts[idx]; if(p._layer) map.removeLayer(p._layer); pts.splice(idx, 1); renderSidebar(); }
        }
        window.toggleCategoryVisibility = function(catKey, isVis) { if (isVis) map.addLayer(layerGroupsRef[catKey]); else map.removeLayer(layerGroupsRef[catKey]); }
        window.toggleAccordionCollapse = function(catKey) { document.getElementById('items-' + catKey.replace(/\\s/g, '')).classList.toggle('collapsed'); }
        window.createNewLayer = function() {
            const name = prompt("Enter new Group name:");
            if(name) { categoryColors[name] = catPalette[colorIndex++ % catPalette.length]; pts.push({_uid: globalIdCounter++, name: 'Dummy Node (Hidden)', type: name, lat:0, lon:0, shape: 'Drop'}); renderSidebar(); }
        }

        // Initialize Map
        L.circle([__LAT__, __LON__], { radius: __RADIUS__, color: "#111827", weight: 1, fillColor: "#111827", fillOpacity: 0.05, dashArray: '4,4' }).addTo(map);
        L.marker([__LAT__, __LON__], { icon: L.divIcon({ html: '<div style="background:#111827; color:#fff; width:24px; height:24px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:14px; border:2px solid #fff; box-shadow: 0 2px 6px rgba(0,0,0,0.2);">★</div>', className:'', iconSize:[28,28] }), zIndexOffset: 10000 }).addTo(map);

        renderSidebar(); 
        if (pts.length > 0 && !__IS_STALE__) {
            const group = new L.featureGroup(pts.filter(p=>p.lat).map(p => L.marker([p.lat, p.lon])));
            map.fitBounds(group.getBounds().pad(0.1));
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

st.components.v1.html(leaflet_html, height=850, scrolling=False)
