import streamlit as st
import requests
import re
import json
import os
import hashlib
import time
import math
import traceback
from datetime import datetime

# --- PROGRAMMATIC LIGHT MODE LOCK (Must execute before st.set_page_config) ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\n")

# -----------------------------------------------------------------------------
# RESOURCE ENDPOINTS & BASES
# -----------------------------------------------------------------------------
GITHUB_POI_BASE = "https://raw.githubusercontent.com/pyscriptcli/osm-repository/main/data/provinces"
GITHUB_BOUNDARY_BASE = "https://raw.githubusercontent.com/pyscriptcli/osm-repository/main/boundaries"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Province bounding boxes for reverse geocoding
PROVINCE_BOUNDS = {
    "metro_manila": [120.90, 14.40, 121.10, 14.80],
    "cavite": [120.60, 14.10, 121.00, 14.50],
    "laguna": [121.00, 14.00, 121.60, 14.50],
    "bulacan": [120.70, 14.70, 121.20, 15.30],
    "batangas": [120.70, 13.60, 121.40, 14.20],
    "rizal": [121.00, 14.40, 121.60, 14.90],
    "pampanga": [120.50, 14.90, 121.00, 15.40],
    "nueva_ecija": [120.60, 15.20, 121.50, 16.00],
    "zambales": [119.80, 14.60, 120.60, 15.80],
    "tarlac": [120.30, 15.30, 121.00, 15.90],
    "pangasinan": [119.80, 15.60, 121.00, 16.50],
    "la_union": [120.20, 16.40, 120.80, 17.00],
    "ilocos_norte": [120.30, 17.80, 121.00, 18.70],
    "ilocos_sur": [120.20, 16.90, 120.80, 17.80],
    "cebu": [123.50, 9.50, 124.20, 11.00],
    "leyte": [124.30, 9.80, 125.60, 11.50],
    "bohol": [123.70, 9.50, 124.60, 10.10],
    "negros_oriental": [122.80, 9.00, 123.50, 10.50],
    "negros_occidental": [122.30, 9.30, 123.40, 11.00],
    "samar": [124.80, 11.00, 125.80, 12.50],
    "biliran": [124.30, 11.40, 124.60, 11.70],
    "siquijor": [123.40, 9.10, 123.70, 9.30],
    "davao_city": [125.40, 6.90, 125.70, 7.40],
    "davao_del_sur": [125.00, 6.00, 125.80, 7.00],
    "davao_oriental": [126.00, 6.50, 126.80, 7.80],
    "north_cotabato": [124.50, 6.80, 125.30, 7.80],
    "south_cotabato": [124.50, 5.80, 125.30, 6.80],
    "sultan_kudarat": [123.80, 6.20, 124.80, 7.20],
    "zamboanga_del_sur": [122.00, 7.00, 123.80, 8.20],
    "zamboanga_del_norte": [121.80, 7.50, 123.00, 8.80],
    "misamis_oriental": [124.00, 8.00, 125.20, 9.30],
    "misamis_occidental": [123.30, 7.80, 124.00, 8.70],
    "bukidnon": [124.30, 7.00, 125.50, 8.50],
    "agusan_del_norte": [125.00, 8.20, 126.00, 9.30],
    "agusan_del_sur": [125.00, 7.60, 126.20, 8.80],
    "surigao_del_norte": [125.20, 9.30, 126.30, 10.20],
    "surigao_del_sur": [125.80, 8.00, 126.50, 9.00],
    "lanao_del_norte": [123.50, 7.50, 124.50, 8.30],
    "lanao_del_sur": [123.80, 7.00, 124.80, 8.20],
    "basilan": [121.80, 6.30, 122.50, 6.80],
    "sulu": [120.80, 5.50, 121.50, 6.30],
    "tawi_tawi": [119.50, 4.50, 120.50, 5.50],
    "dinagat_islands": [125.30, 9.80, 125.80, 10.50],
}

# -----------------------------------------------------------------------------
# API LOGGING SYSTEM
# -----------------------------------------------------------------------------
if 'api_logs' not in st.session_state:
    st.session_state.api_logs = []

def add_api_log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.api_logs.append({
        "time": timestamp,
        "message": message,
        "level": level
    })
    if len(st.session_state.api_logs) > 100:
        st.session_state.api_logs = st.session_state.api_logs[-100:]

def clear_api_logs():
    st.session_state.api_logs = []

# -----------------------------------------------------------------------------
# GEOPROCESSING MATH UTILITIES
# -----------------------------------------------------------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def get_province_from_coords(lat, lon):
    for province, bbox in PROVINCE_BOUNDS.items():
        if bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]:
            return province
    return None

# -----------------------------------------------------------------------------
# CORE SPATIAL FETCH ENGINES (POIs)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=86400, show_spinner=False)
def load_province_pois(province_name):
    url = f"{GITHUB_POI_BASE}/{province_name}.json"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None

@st.cache_data(ttl=86400, show_spinner=False)
def load_overpass_pois_fallback(lat, lon, radius_meters, selected_tags):
    """
    Multi-layer Fallback Engine: Builds and dispatches a compiled direct query 
    to Overpass API targeting matching statements.
    """
    filters = []
    for tag in selected_tags:
        clean_tag = tag.replace('"', '')
        if '=' in clean_tag:
            key, val = clean_tag.split('=', 1)
            if '~' in val or '|' in val:
                val_clean = val.replace('~', '')
                filters.append(f'node["{key}"~"{val_clean}"](around:{radius_meters},{lat},{lon});')
                filters.append(f'way["{key}"~"{val_clean}"](around:{radius_meters},{lat},{lon});')
            else:
                filters.append(f'node["{key}"="{val}"](around:{radius_meters},{lat},{lon});')
                filters.append(f'way["{key}"="{val}"](around:{radius_meters},{lat},{lon});')
        else:
            filters.append(f'node["{clean_tag}"](around:{radius_meters},{lat},{lon});')
            filters.append(f'way["{clean_tag}"](around:{radius_meters},{lat},{lon});')
            
    combined_statements = "\n  ".join(filters)
    query = f"""[out:json][timeout:30];
(
  {combined_statements}
);
out center;"""
    
    try:
        response = requests.post(OVERPASS_URL, data={"data": query}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            elements = data.get('elements', [])
            pois = []
            for el in elements:
                p_lat = el.get('lat') or el.get('center', {}).get('lat')
                p_lon = el.get('lon') or el.get('center', {}).get('lon')
                if not p_lat or not p_lon:
                    continue
                
                # Determine clean display type string
                tags = el.get('tags', {})
                discovered_type = "poi"
                for t_item in selected_tags:
                    t_clean = t_item.replace('"', '')
                    if '=' in t_clean:
                        k, v = t_clean.split('=', 1)
                        if k in tags:
                            discovered_type = f"{k}={tags[k]}"
                            break
                    elif t_clean in tags:
                        discovered_type = t_clean
                        break

                pois.append({
                    "lat": p_lat,
                    "lon": p_lon,
                    "name": tags.get('name') or tags.get('brand') or tags.get('operator') or 'Unknown',
                    "type": discovered_type
                })
            return pois
        return []
    except Exception as e:
        return []

def filter_pois_by_radius(pois, center_lat, center_lon, radius_meters):
    filtered = []
    for poi in pois:
        dist = haversine(center_lat, center_lon, poi['lat'], poi['lon'])
        if dist <= radius_meters:
            poi_copy = poi.copy()
            poi_copy['distance_m'] = round(dist)
            filtered.append(poi_copy)
    return filtered

def filter_pois_by_tags(pois, selected_tags):
    if not selected_tags:
        return pois
    filtered = []
    for poi in pois:
        poi_type = poi.get('type', '').lower()
        for tag in selected_tags:
            tag_clean = tag.replace('"', '').lower()
            if '=' in tag_clean:
                key, value = tag_clean.split('=', 1)
                value_clean = value.replace('~', '').replace('|', '')
                if key in poi_type or value_clean in poi_type:
                    filtered.append(poi)
                    break
            else:
                if tag_clean in poi_type:
                    filtered.append(poi)
                    break
    return filtered

# -----------------------------------------------------------------------------
# ADMINISTRATIVE BOUNDARY FETCH ENGINES
# -----------------------------------------------------------------------------
@st.cache_data(ttl=86400, show_spinner=False)
def reverse_geocode_location(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"
        headers = {"User-Agent": "OpenNode/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            address = data.get('address', {})
            return {
                "region": address.get('state', ''),
                "province": address.get('province', '') or address.get('state_district', ''),
                "city": address.get('city', '') or address.get('municipality', '') or address.get('town', ''),
                "barangay": address.get('suburb', '') or address.get('neighbourhood', '') or address.get('village', ''),
                "lat": lat,
                "lon": lon
            }
        return None
    except Exception as e:
        return None

def load_github_boundary(area_name, boundary_type):
    filename_map = {"region": "regions.geojson", "province": "provinces.geojson", "city": "cities.geojson"}
    filename = filename_map.get(boundary_type)
    if not filename:
        return None
    
    url = f"{GITHUB_BOUNDARY_BASE}/{filename}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if area_name:
                filtered_features = []
                for feature in data.get('features', []):
                    props = feature.get('properties', {})
                    # Standardize names to check for intersection matches
                    f_name = props.get('name', '').lower()
                    a_name = area_name.lower()
                    if f_name == a_name or a_name in f_name or f_name in a_name:
                        filtered_features.append(feature)
                if filtered_features:
                    return {"type": "FeatureCollection", "features": filtered_features}
            return None
        return None
    except Exception as e:
        return None

def load_overpass_boundary(area_name, admin_level):
    query = f"""[out:json][timeout:30];
(
  relation["admin_level"="{admin_level}"]["name"="{area_name}"];
  relation["admin_level"="{admin_level}"]["name:en"="{area_name}"];
);
out body;
>;
out skel qt;"""
    try:
        response = requests.post(OVERPASS_URL, data={"data": query}, timeout=30)
        if response.status_code != 200:
            return None
        
        osm_data = response.json()
        elements = osm_data.get('elements', [])
        
        # Build node coordinate dictionary map
        nodes = {el['id']: (el['lon'], el['lat']) for el in elements if el['type'] == 'node'}
        ways = {}
        for el in elements:
            if el['type'] == 'way' and 'nodes' in el:
                ways[el['id']] = [nodes[nid] for nid in el['nodes'] if nid in nodes]
                
        features = []
        for el in elements:
            if el['type'] == 'relation':
                polygon_coords = []
                for member in el.get('members', []):
                    if member['type'] == 'way' and member['ref'] in ways:
                        w_coords = ways[member['ref']]
                        if w_coords:
                            polygon_coords.extend(w_coords)
                
                # Check completeness of polygon wireframe loop
                if len(polygon_coords) >= 3:
                    if polygon_coords[0] != polygon_coords[-1]:
                        polygon_coords.append(polygon_coords[0])
                    features.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [polygon_coords]
                        },
                        "properties": {
                            "name": el.get('tags', {}).get('name', area_name),
                            "admin_level": admin_level
                        }
                    })
        if features:
            return {"type": "FeatureCollection", "features": features}
        return None
    except Exception as e:
        return None

@st.cache_data(ttl=86400, show_spinner=False)
def get_boundary_geojson(area_name, admin_level):
    if not area_name:
        return None
    
    boundary_type_map = {"4": "region", "5": "province", "6": "city", "7": "city", "8": "barangay"}
    boundary_type = boundary_type_map.get(str(admin_level), "province")
    
    # Primary pipeline strategy: GitHub Endpoints
    github_data = load_github_boundary(area_name, boundary_type)
    if github_data and github_data.get('features'):
        add_api_log(f"Boundaries: Loaded '{area_name}' from GitHub repository layer", "INFO")
        return github_data
        
    # Secondary resilient fallback strategy: Overpass API Element Parsing
    add_api_log(f"Boundaries: Missing GitHub map layer for '{area_name}'. Relaying query to Overpass API...", "WARNING")
    overpass_data = load_overpass_boundary(area_name, admin_level)
    if overpass_data:
        add_api_log(f"Boundaries: Rendered structural polygon for '{area_name}' via Overpass Engine.", "INFO")
        return overpass_data
        
    add_api_log(f"Boundaries: Failed parsing vectors for target boundary '{area_name}' on all servers.", "ERROR")
    return None

# -----------------------------------------------------------------------------
# 1. BRANDED THEME & STRUCTURAL FULL OVERRIDES
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Open Node",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Montserrat:wght@400;500;600;700;800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20,400,0,0');

        :root {
            --brand-midnight: #003366 !important;
            --brand-gold: #C9AB4C !important;
            --white-clean: #ffffff !important;
            --bg-offwhite: #f8fafc !important;
            --text-muted: #888780 !important;
            --soft-shadow: 0 4px 12px rgba(0, 51, 102, 0.08) !important;
        }
        
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: var(--white-clean) !important;
            color: var(--brand-midnight) !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: var(--bg-offwhite) !important;
            color: var(--brand-midnight) !important;
            border-right: 1px solid rgba(0, 51, 102, 0.08) !important;
            width: 280px !important;
            min-width: 280px !important;
            max-width: 280px !important;
            transform: none !important;
            visibility: visible !important;
            overflow: hidden !important;
            box-shadow: 2px 0 15px rgba(0,0,0,0.03) !important;
        }
        
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] { display: none !important; }
        ::-webkit-scrollbar { width: 0px !important; background: transparent !important; }
        * { scrollbar-width: none !important; -ms-overflow-style: none !important; }
        
        p, label, h1, h2, h3, h4, h5, h6, .stMarkdown, [data-testid="stExpander"] summary p {
            color: var(--brand-midnight) !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        
        [data-testid="stHeader"], header, #stDecoration { display: none !important; }
        
        [data-testid="stAppViewContainer"] { display: flex !important; flex-direction: row !important; width: 100vw !important; height: 100vh !important; overflow: hidden !important; }
        [data-testid="stMain"] { flex-grow: 1 !important; width: calc(100vw - 280px) !important; height: 100vh !important; overflow: hidden !important; margin: 0px !important; padding: 0px !important; }
        .block-container, [data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"], .stElementContainer { padding: 0px !important; margin: 0px !important; max-width: 100% !important; gap: 0rem !important; }
        iframe { height: 100vh !important; width: 100% !important; border: none !important; display: block !important; }
        
        div[data-baseweb="input"], div[data-baseweb="select"] { background-color: transparent !important; border: none !important; border-bottom: 1px solid rgba(201, 171, 76, 0.5) !important; border-radius: 0px !important; box-shadow: none !important; }
        
        div.stButton > button[kind="secondary"], [data-testid="stPopover"] > button { background-color: var(--brand-midnight) !important; border: 1px solid var(--brand-midnight) !important; border-radius: 2px !important; width: 100% !important; padding: 4px !important; box-shadow: var(--soft-shadow) !important; }
        div.stButton > button[kind="secondary"]:hover, [data-testid="stPopover"] > button:hover { background-color: var(--brand-gold) !important; border-color: var(--brand-gold) !important; }
        div.stButton > button[kind="secondary"] p, [data-testid="stPopover"] > button p, [data-testid="stPopover"] > button div, div.stDownloadButton > button p { color: var(--white-clean) !important; font-weight: 700 !important; font-size: 9px !important; text-transform: uppercase !important; letter-spacing: 1px; }
        
        div.stDownloadButton > button { background-color: var(--brand-midnight) !important; border: none !important; border-radius: 2px !important; width: 100% !important; padding: 4px !important; }
        div.stDownloadButton > button:hover { background-color: var(--brand-gold) !important; }
        
        div.stButton > button[kind="primary"] { background: transparent !important; border: none !important; color: var(--text-muted) !important; padding: 0 !important; margin-top: 2px; }
        div.stButton > button[kind="primary"] p { color: var(--text-muted) !important; font-size: 9px !important; font-weight: 600; text-transform: uppercase; }
        
        [data-testid="stSidebar"] .st-expander { border: 1px solid rgba(0, 51, 102, 0.05) !important; background-color: var(--white-clean) !important; border-radius: 2px !important; margin-bottom: 2px !important; }
        
        .stCheckbox { display: flex !important; align-items: center !important; margin-bottom: 2px !important; }
        .stCheckbox label { display: inline-flex !important; align-items: center !important; gap: 6px !important; margin: 0px !important; padding: 0px !important; }
        .stCheckbox label p { font-size: 10px !important; font-weight: 500 !important; color: var(--brand-midnight) !important; display: inline-block !important; margin: 0 !important; line-height: 1.2 !important; }
        div[data-baseweb="checkbox"] { align-self: center !important; }
        
        div[data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"] { background-color: #003366 !important; border-color: #003366 !important; }
        div[data-baseweb="checkbox"] input:checked + div, div[data-baseweb="checkbox"] div[aria-checked="true"], div[data-baseweb="checkbox"] [role="checkbox"][aria-checked="true"] > div { background-color: #003366 !important; border-color: #003366 !important; }
        
        .brand-title { font-family: 'Cormorant Garamond', serif !important; font-style: italic; color: var(--brand-midnight); font-size: 30px; text-align: center; border-bottom: 1px solid var(--brand-gold); padding-bottom: 6px; margin-bottom: 10px; }
        .stTextInput label p, .stNumberInput label p { font-size: 9px !important; font-weight: 500 !important; color: var(--text-muted) !important; }

        [data-testid="stColorPicker"] div[data-baseweb="select"] { text-transform: uppercase !important; }
        div[data-baseweb="color-picker-popover"] div[data-baseweb="select"] { display: none !important; }
        div[data-baseweb="color-picker-popover"] div:has(> input) + div { display: none !important; }
        div[data-baseweb="color-picker-popover"] label, div[data-baseweb="color-picker-popover"] span { display: none !important; }
        div[data-baseweb="color-picker-popover"] input[type="number"] { display: none !important; }
        div[data-baseweb="color-picker-popover"] input[type="text"] { width: 100% !important; text-transform: uppercase !important; font-family: 'Montserrat', sans-serif !important; font-weight: 700 !important; font-size: 11px !important; text-align: center !important; color: var(--brand-midnight) !important; }
        
        .py-loading-container {
            position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%);
            width: 340px; background: #ffffff; padding: 24px; border-radius: 4px;
            border: 1px solid rgba(0, 51, 102, 0.15); box-shadow: 0 10px 30px rgba(0, 51, 102, 0.15);
            text-align: center; z-index: 999999; font-family: 'Montserrat', sans-serif;
        }
        .py-spinner {
            width: 40px; height: 40px; border: 4px solid rgba(0, 51, 102, 0.1);
            border-left-color: #003366; border-radius: 50%; animation: spin 1s linear infinite;
            margin: 0 auto 16px auto;
        }
        .py-loading-title { font-size: 11px; font-weight: 800; color: #003366; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 6px; }
        .py-loading-subtitle { font-size: 10px; font-weight: 600; color: #C9AB4C; font-family: monospace; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        .api-log-container {
            position: absolute; bottom: 12px; right: 12px; width: 380px; max-height: 280px;
            background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(8px); border-radius: 8px;
            border-left: 3px solid #C9AB4C; z-index: 10000; font-family: 'Monaco', monospace;
            font-size: 10px; display: flex; flex-direction: column; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: all 0.2s ease; color: #e0e0e0;
        }
        .api-log-header {
            padding: 6px 10px; background: rgba(0,0,0,0.6); border-radius: 8px 8px 0 0;
            font-weight: 700; font-size: 9px; letter-spacing: 1px; text-transform: uppercase;
            display: flex; justify-content: space-between; align-items: center; cursor: pointer;
            color: #C9AB4C; border-bottom: 1px solid rgba(201, 171, 76, 0.3);
        }
        .api-log-content { overflow-y: auto; padding: 6px; flex-grow: 1; max-height: 220px; scrollbar-width: thin; }
        .api-log-entry { border-bottom: 1px solid rgba(255,255,255,0.1); padding: 6px 4px; font-family: monospace; font-size: 9px; word-break: break-word; }
        .api-log-time { color: #C9AB4C; font-weight: 600; margin-right: 8px; }
        .api-log-info { color: #88ffaa; }
        .api-log-error { color: #ff8888; }
        .api-log-warning { color: #ffaa66; }
        .api-log-close { cursor: pointer; padding: 0 6px; font-size: 14px; line-height: 1; }
        .api-log-close:hover { color: #ff8888; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# GLOBAL HELPER DEFINITIONS
# -----------------------------------------------------------------------------
def compile_features_kml(features):
    kml = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scanned POIs</name>'
    for f in features:
        if not f.get('visible', True): continue
        name = f.get('name', 'Asset').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        class_type = f.get('type', 'Node').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        kml += f"<Placemark><name>{name}</name><description>{class_type}</description><Point><coordinates>{f['lon']},{f['lat']},0</coordinates></Point></Placemark>"
    return kml + '</Document></kml>'

# -----------------------------------------------------------------------------
# 2. STATE PERSISTENCE & DATA CONFIGURATIONS
# -----------------------------------------------------------------------------
DEFAULT_COORDS = "14.5995, 120.9842"
DEFAULT_RADIUS = 1000

if 'geo_coords' not in st.session_state: st.session_state.geo_coords = DEFAULT_COORDS
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = DEFAULT_RADIUS
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'last_scan_lat' not in st.session_state: st.session_state.last_scan_lat = 14.5995
if 'last_scan_lon' not in st.session_state: st.session_state.last_scan_lon = 120.9842
if 'layer_meta' not in st.session_state: st.session_state.layer_meta = {}
if 'layer_groups' not in st.session_state: st.session_state.layer_groups = {}
if 'scan_active_loading' not in st.session_state: st.session_state.scan_active_loading = False
if 'network_stats' not in st.session_state: st.session_state.network_stats = None

if 'target_config' not in st.session_state: st.session_state.target_config = {"size": 24, "color": "#003366", "style": "star"}
if 'radius_config' not in st.session_state: st.session_state.radius_config = {"color": "#003366", "fill_opacity": 0.08, "weight": 1.5}
if 'global_marker_style' not in st.session_state: st.session_state.global_marker_style = "modern-pin"
if 'global_marker_size' not in st.session_state: st.session_state.global_marker_size = 16
if 'global_marker_color' not in st.session_state: st.session_state.global_marker_color = "#003366"

# Boundary state variables
if 'show_boundaries' not in st.session_state: st.session_state.show_boundaries = False
if 'boundary_levels' not in st.session_state: st.session_state.boundary_levels = []
if 'current_location_info' not in st.session_state: st.session_state.current_location_info = None
if 'boundary_geojson_data' not in st.session_state: st.session_state.boundary_geojson_data = {}

POI_CONFIG = {
    "COMMERCIAL & OFFICES": [['Corporate Office', '"building"~"office|commercial",i'], ['IT/Tech Center', '"office"~"it|telecommunication",i'], ['Business Center', '"building"="commercial"'], ['Bank', '"amenity"="bank"'], ['ATM', '"amenity"="atm"'], ['Office', '"office"="yes"']],
    "RETAIL": [['Mall/Department Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"market|grocery",i'], ['Convenience Store', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Hardware', '"shop"~"hardware|doityourself",i'], ['General Shops', '"shop"~"boutique|clothes|shoes",i']],
    "FOOD, BEVERAGE & HOSPITALITY": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee Shop', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"'], ['Bar/Pub/Nightclub', '"amenity"~"bar|pub|nightclub",i'], ['Bakery/Pastry', '"shop"="bakery"'], ['Hotel', '"tourism"="hotel"']],
    "RESIDENTIAL": [['Apartments', '"building"="apartments"'], ['House', '"building"="house"'], ['Residential Area', '"landuse"="residential"'], ['Condominium', '"building"="residential"']],
    "INDUSTRIAL & LOGISTICS": [['Expressway Exits', '"highway"~"motorway_junction|toll_gantry",i'], ['Ports & Terminals', '"industrial"="port"'], ['Warehouses & Depots', '"building"~"warehouse|depot",i']],
    "HEALTH & EMERGENCY SERVICES": [['Hospital', '"amenity"~"hospital|clinic",i'], ['Clinic', '"amenity"="clinic"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Police Station', '"amenity"="police"'], ['Fire Station', '"amenity"="fire_station"']],
    "GOVERNMENT, EDUCATION & INFRASTRUCTURE": [['City Hall', '"amenity"="townhall"'], ['Airport Terminal', '"aeroway"~"terminal|aerodrome",i'], ['University/College', '"amenity"~"university|college",i'], ['K-12 School', '"amenity"="school"']],
    "LEISURE, SPORTS & PUBLIC SPACES": [['Church', '"religion"="christian"'], ['Mosque', '"religion"="muslim"'], ['Fuel', '"amenity"="fuel"'], ['Parking', '"amenity"="parking"']]
}

# -----------------------------------------------------------------------------
# 3. SIDEBAR CONTROLS & SPATIAL ENGINE MANAGER
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="brand-title">Open Node</div>', unsafe_allow_html=True)
    
    selected_tags = []
    scan_triggered = st.button("SCAN AREA", type="secondary", use_container_width=True, key="scan_btn")
    
    location_input = st.text_input("COORDINATES", value=st.session_state.geo_coords, key="geo_coords_input")
    radius_val = st.number_input("RADIUS (METERS)", min_value=100, max_value=50000, value=st.session_state.geo_radius, key="geo_radius_input", step=100)
    st.session_state.geo_radius = radius_val

    coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", location_input)
    if coord_match:
        lat_coord, lon_coord = float(coord_match.group(1)), float(coord_match.group(2))
        st.session_state.geo_coords = location_input
    else:
        fallback_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", st.session_state.geo_coords)
        lat_coord, lon_coord = (float(fallback_match.group(1)), float(fallback_match.group(2))) if fallback_match else (14.5995, 120.9842)

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    search_query = st.text_input("SEARCH TAGS", placeholder="Search parameters...").lower()
    
    for cat_name, node_items in POI_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for label, tag in matched:
                    if st.checkbox(label, key=f"chk_{cat_name}_{label}"): 
                        selected_tags.append(tag)

    # ADMINISTRATIVE BOUNDARIES WIDGET
    st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>", unsafe_allow_html=True)
    st.markdown("<div style='font-weight: 700; font-size: 11px; margin-bottom: 8px; color: #003366; letter-spacing: 1px;'>🗺️ ADMINISTRATIVE BOUNDARIES</div>", unsafe_allow_html=True)
    
    show_boundaries_toggle = st.checkbox("Show Administrative Boundaries", key="show_boundaries_toggle", value=st.session_state.show_boundaries)
    
    if show_boundaries_toggle:
        st.session_state.show_boundaries = True
        boundary_options = st.multiselect(
            "Select boundary layers:",
            options=["Region", "Province", "City/Municipality", "Barangay"],
            default=st.session_state.boundary_levels,
            key="boundary_selector"
        )
        st.session_state.boundary_levels = boundary_options
    else:
        st.session_state.show_boundaries = False
        st.session_state.boundary_levels = []

    if scan_triggered:
        if not selected_tags and not show_boundaries_toggle:
            st.error("Select ≥ 1 layer or boundary.")
            add_api_log("Scan attempted with no active query options", "ERROR")
        else:
            add_api_log(f"Scan initiated | Radius: {radius_val}m | Layers: {len(selected_tags)}", "INFO")
            st.session_state.scan_active_loading = True
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("CLEAR ALL", type="primary", key="clear_btn"):
        st.session_state.scanned_records = []
        st.session_state.layer_meta = {}
        st.session_state.layer_groups = {}
        st.session_state.network_stats = None
        st.session_state.scan_active_loading = False
        st.session_state.show_boundaries = False
        st.session_state.boundary_levels = []
        st.session_state.current_location_info = None
        st.session_state.boundary_geojson_data = {}
        clear_api_logs()
        for key in list(st.session_state.keys()):
            if key.startswith("chk_"): st.session_state[key] = False
        add_api_log("Cleared workspace state and data caches", "INFO")
        st.rerun()

    st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    visible_only_records = [p for p in st.session_state.scanned_records if p.get('visible', True)]
    with col1: st.download_button("RADIUS", json.dumps(visible_only_records), "scan.json", "application/json", use_container_width=True)
    with col2: st.download_button("MARKERS", compile_features_kml(st.session_state.scanned_records), "POIs.kml", "application/vnd.google-earth.kml+xml", use_container_width=True)

# -----------------------------------------------------------------------------
# PIPELINE DATA EXECUTION CONTROL ENGINE
# -----------------------------------------------------------------------------
main_canvas = st.empty()

if st.session_state.scan_active_loading:
    records = []
    scan_success = False
    
    main_canvas.markdown(f'''
        <div class="py-loading-container">
            <div class="py-spinner"></div>
            <div class="py-loading-title">Processing Queries</div>
            <div class="py-loading-subtitle">Resolving spatial repository lookups...</div>
        </div>
    ''', unsafe_allow_html=True)
    
    # --------------------------------
    # POI DATA RESOLUTION PIPELINE
    # --------------------------------
    if selected_tags:
        province_name = get_province_from_coords(lat_coord, lon_coord)
        raw_pois = None
        
        # Primary Action: Attempt GitHub data loading
        if province_name:
            add_api_log(f"POIs [Primary]: Geocoded position to province '{province_name}'. Loading from GitHub...", "INFO")
            raw_pois = load_province_pois(province_name)
            
        if raw_pois:
            add_api_log(f"POIs [Primary]: Retracted {len(raw_pois)} records from GitHub cache.", "INFO")
            radius_filtered = filter_pois_by_radius(raw_pois, lat_coord, lon_coord, radius_val)
            tag_filtered = filter_pois_by_tags(radius_filtered, selected_tags)
            
            for idx, poi in enumerate(tag_filtered):
                records.append({
                    "lat": poi['lat'], "lon": poi['lon'],
                    "name": poi.get('name', 'Unknown'), "type": poi.get('type', 'poi'),
                    "source": "github", "has_footprint": False, "footprint_geojson": None, "visible": True, "uid": idx
                })
            scan_success = True
        else:
            # Resilient Fallback: Query direct Multi-Layer Overpass API
            add_api_log("POIs [Fallback]: GitHub entry unavailable. Initializing multi-layer Overpass query over live grid...", "WARNING")
            fallback_pois = load_overpass_pois_fallback(lat_coord, lon_coord, radius_val, selected_tags)
            
            if fallback_pois:
                for idx, poi in enumerate(fallback_pois):
                    records.append({
                        "lat": poi['lat'], "lon": poi['lon'],
                        "name": poi['name'], "type": poi['type'],
                        "source": "overpass", "has_footprint": False, "footprint_geojson": None, "visible": True, "uid": idx
                    })
                add_api_log(f"POIs [Fallback]: Extracted {len(records)} elements from live Overpass compilation.", "INFO")
                scan_success = True
            else:
                add_api_log("POIs [Error]: All spatial source engines exhausted with empty records.", "ERROR")
                
        st.session_state.scanned_records = records
        st.session_state.last_scan_lat = lat_coord
        st.session_state.last_scan_lon = lon_coord

    # --------------------------------
    # BOUNDARY DATA RESOLUTION PIPELINE
    # --------------------------------
    if st.session_state.show_boundaries and st.session_state.boundary_levels:
        add_api_log("Boundaries: Reverse-geocoding center focus vector...", "INFO")
        loc_hierarchy = reverse_geocode_location(lat_coord, lon_coord)
        st.session_state.current_location_info = loc_hierarchy
        
        compiled_boundaries = {}
        if loc_hierarchy:
            level_mapping = {
                "Region": (loc_hierarchy.get('region'), 4),
                "Province": (loc_hierarchy.get('province'), 5),
                "City/Municipality": (loc_hierarchy.get('city'), 6),
                "Barangay": (loc_hierarchy.get('barangay'), 8)
            }
            
            for lvl_label in st.session_state.boundary_levels:
                area_name, admin_idx = level_mapping.get(lvl_label, (None, None))
                if area_name:
                    geojson_res = get_boundary_geojson(area_name, admin_idx)
                    if geojson_res:
                        compiled_boundaries[lvl_label.lower().replace('/municipality', '')] = geojson_res
                        
        st.session_state.boundary_geojson_data = compiled_boundaries

    st.session_state.scan_active_loading = False
    st.rerun()

# -----------------------------------------------------------------------------
# 4. LEAFLET MAP INTERACTION GENERATOR
# -----------------------------------------------------------------------------
pts_active = st.session_state.scanned_records
unique_layers = list(set([p.get('type', 'Unclassified') for p in pts_active]))
cat_palette = ["#003366", "#C9AB4C", "#1A5A8A", "#A8862E", "#3D7DA8", "#7A5C10", "#6A94B0"]

for idx, layer in enumerate(unique_layers):
    if layer not in st.session_state.layer_meta:
        st.session_state.layer_meta[layer] = {
            "color": cat_palette[idx % len(cat_palette)],
            "style": st.session_state.global_marker_style,
            "size": st.session_state.global_marker_size
        }

layer_meta_json = json.dumps(st.session_state.layer_meta)
target_config_json = json.dumps(st.session_state.target_config)
radius_config_json = json.dumps(st.session_state.radius_config)
geojson_str = json.dumps(pts_active)

render_lat, render_lon = lat_coord, lon_coord
is_stale = "true" if (lat_coord != st.session_state.last_scan_lat or lon_coord != st.session_state.last_scan_lon) else "false"

boundary_geojson_data = st.session_state.get('boundary_geojson_data', {})
boundary_data_json = json.dumps(boundary_geojson_data)

# Inject logs into the monitor UI terminal
api_logs_html = ""
for log in st.session_state.api_logs[-30:]:
    level_class = f"api-log-{log['level'].lower()}"
    api_logs_html += f'<div class="api-log-entry"><span class="api-log-time">[{log["time"]}]</span> <span class="{level_class}">{log["message"]}</span></div>'

api_log_panel = f'''
<div class="api-log-container" id="apiLogPanel">
    <div class="api-log-header" onclick="toggleApiLog()">
        <span>📡 LIVE CORE DATA RUNTIME LOG</span>
        <span class="api-log-close" onclick="event.stopPropagation(); clearApiLogsFromUI();">✕</span>
    </div>
    <div class="api-log-content" id="apiLogContent">
        {api_logs_html if api_logs_html else '<div class="api-log-entry"><span class="api-log-time">[--:--:--]</span> <span>Workspace idle. Select target parameters.</span></div>'}
    </div>
</div>
<script>
    function toggleApiLog() {{
        const content = document.getElementById('apiLogContent');
        if (content) content.style.display = content.style.display === 'none' ? 'block' : 'none';
    }}
    function clearApiLogsFromUI() {{
        const content = document.getElementById('apiLogContent');
        if (content) content.innerHTML = '<div class="api-log-entry"><span class="api-log-time">[--:--:--]</span> <span>Runtime logs flushed.</span></div>';
    }}
</script>
'''

leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #ffffff; overflow: hidden; font-family: 'Montserrat', sans-serif; }
        #map-container { position: relative; width: 100%; height: 100vh; }
        #map { height: 100vh; width: 100%; z-index: 1; }
        #scan-results-panel {
            position: absolute; top: 10px; right: 10px; z-index: 1000; background: #ffffff; width: 310px; max-height: calc(100vh - 40px); border-radius: 4px; border: 1px solid rgba(0, 51, 102, 0.1); display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08);
        }
        .results-header { background: #003366; color: #ffffff; padding: 10px 12px; font-size: 10px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; border-bottom: 2px solid #C9AB4C; letter-spacing: 1px; }
        .results-list { overflow-y: auto; flex-grow: 1; padding-bottom: 0px; max-height: calc(100vh - 280px); }
        .layer-category-block { border-bottom: 1px solid #f0f0f0; }
        .layer-category-header { background: #ffffff; padding: 6px 10px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; user-select: none; }
        .layer-header-left { display: flex; align-items: center; gap: 6px; font-size: 9px; font-weight: 700; color: #003366; text-transform: uppercase; flex-grow: 1; overflow: hidden;}
        .layer-category-items { padding: 0; background: #f8fafc; }
        .layer-category-items.collapsed { display: none !important; }
        .results-item { padding: 4px 8px 4px 16px; font-size: 9px; font-weight: 600; color: #888780; display: flex; justify-content: space-between; align-items: center; cursor: pointer; border-bottom: 1px solid #f0f0f0; }
        .results-item:hover { background: #ffffff; color: #003366; }
        .action-icon-trigger { cursor: pointer; padding: 2px; display: inline-flex; align-items: center; justify-content: center; width: 18px; height: 18px; border-radius: 2px; transition: all 0.15s; }
        .action-icon-trigger:hover { background: rgba(0, 51, 102, 0.05); }
        .action-icon-trigger svg { fill: #888780; width: 12px; height: 12px; }
        .action-icon-trigger:hover svg { fill: #003366; }
        .action-icon-trigger.delete-btn:hover svg { fill: #AA2E20; }
        .poi-text-label { background: #fff; border: 1px solid #003366; padding: 2px 4px; border-radius: 2px; font-size: 9px; font-family: 'Montserrat', sans-serif; font-weight: 700; white-space: nowrap; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .hide-labels .poi-text-label { display: none !important; }
        .color-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; border: 1px solid rgba(0,0,0,0.1); }
        .config-block-wrapper { padding: 6px 12px; background: #f8fafc; border-bottom: 1px solid rgba(0, 51, 102, 0.08); display: flex; flex-direction: column; gap: 4px; }
        .config-headline { font-size: 8px; font-weight: 800; color: #003366; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }
        .config-flex-row { display: flex; align-items: center; justify-content: space-between; font-size: 9px; font-weight: 600; color: #003366; gap: 6px; }
        .config-flex-row select, .config-flex-row input { font-size: 9px; font-family: 'Montserrat', sans-serif; color: #003366; background: #ffffff; border: 1px solid rgba(0, 51, 102, 0.15); border-radius: 2px; padding: 1px 3px; outline: none; }
        .slider-control-element { flex-grow: 1; margin: 0; -webkit-appearance: none; height: 4px; background: rgba(0,51,102,0.1); border-radius: 2px; outline: none; }
        .slider-control-element::-webkit-slider-thumb { -webkit-appearance: none; width: 10px; height: 10px; border-radius: 50%; background: #003366; cursor: pointer; }
        
        .boundary-tooltip { font-family: 'Montserrat', sans-serif; font-size: 9px; font-weight: 600; background: rgba(0, 51, 102, 0.9); color: white; padding: 2px 6px; border-radius: 2px; border-left: 2px solid #C9AB4C; }
        .boundary-legend { background: rgba(255,255,255,0.95); padding: 6px 10px; border-radius: 4px; font-size: 9px; font-family: 'Montserrat', sans-serif; font-weight: 600; color: #003366; border: 1px solid rgba(0,51,102,0.1); box-shadow: 0 2px 6px rgba(0,0,0,0.1); position: absolute; bottom: 20px; left: 20px; z-index: 11000; }
    </style>
</head>
<body>
    <div id="map-container">
        <div id="map"></div>
        <div id="scan-results-panel">
            <div class="results-header"><span>WORKSPACE GRAPH</span><div style="display: flex; align-items: center; gap: 8px;"><span id="results-count" style="color:#C9AB4C;">0</span></div></div>
            <div class="config-block-wrapper" style="border-bottom: 2px solid var(--brand-gold);"><div class="config-headline">Basemap Controller</div><div class="config-flex-row"><span>Tile Style:</span><select id="basemap-select" onchange="switchActiveBasemap(this.value)"><option value="osm">OpenStreetMap</option><option value="satellite">Satellite View</option><option value="carto">Carto Light</option></select><label style="font-size:9px; font-weight:700; color:#003366; display:flex; align-items:center; gap:3px; cursor:pointer;"><input type="checkbox" id="label-toggle-chk" onchange="toggleLabelsMatrix(this.checked)" style="accent-color: #003366;"> Labels</label></div></div>
            <div class="config-block-wrapper"><div class="config-headline">Global Markers</div><div class="config-flex-row"><span>Style:</span><select id="gl-marker-style" onchange="patchGlobalMarkerStyle(this.value)"><option value="dots">Dots</option><option value="pin">Pin Location</option><option value="modern-pin" selected>Modern Drop-Pin</option></select><input type="range" min="10" max="40" value="__GLOBAL_MARKER_SIZE__" class="slider-control-element" id="gl-marker-size" oninput="patchGlobalMarkerSize(this.value)"></div><div class="config-flex-row"><span>Color:</span><input type="color" id="gl-marker-color" value="__GLOBAL_MARKER_COLOR__" onchange="patchGlobalMarkerColor(this.value)"></div></div>
            <div class="results-list" id="results-list-box"></div>
        </div>
        __API_LOG_PANEL__
    </div>

    <script>
        const map = L.map('map', { zoomControl: false, attributionControl: false, preferCanvas: true }).setView([__LAT__, __LON__], 14);
        let layerMeta = __LAYER_META_JSON__; let targetConfig = __TARGET_CONFIG_JSON__; let radiusConfig = __RADIUS_CONFIG_JSON__; let pts = __GEOJSON__;
        let boundaryLayers = { region: null, province: null, city: null, barangay: null };

        const basemaps = {
            osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }),
            satellite: L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', { maxZoom: 20 }),
            carto: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 })
        };
        basemaps[(localStorage.getItem('ts_persistent_basemap') || 'osm')].addTo(map);
        
        function switchActiveBasemap(targetKey) {
            Object.keys(basemaps).forEach(k => { if(map.hasLayer(basemaps[k])) map.removeLayer(basemaps[k]); });
            basemaps[targetKey].addTo(map); localStorage.setItem('ts_persistent_basemap', targetKey);
        }

        let labelsActive = localStorage.getItem('ts_persistent_labels') !== 'false';
        document.getElementById('label-toggle-chk').checked = labelsActive;
        if (!labelsActive) document.getElementById('map').classList.add('hide-labels');
        
        function toggleLabelsMatrix(isShown) {
            if (isShown) document.getElementById('map').classList.remove('hide-labels');
            else document.getElementById('map').classList.add('hide-labels');
            localStorage.setItem('ts_persistent_labels', isShown);
        }

        let radiusCircle = null;
        function renderRadiusCircleBounds() {
            if (radiusCircle) map.removeLayer(radiusCircle);
            radiusCircle = L.circle([__LAT__, __LON__], { radius: __RADIUS__, color: radiusConfig.color, weight: parseFloat(radiusConfig.weight), fillColor: radiusConfig.color, fillOpacity: parseFloat(radiusConfig.fill_opacity) }).addTo(map);
        }

        let centerMarker = null;
        function renderTargetCenterIcon() {
            if (centerMarker) map.removeLayer(centerMarker);
            const d = targetConfig.size; const c = targetConfig.color;
            const htmlElement = targetConfig.style === "star" ? `<div style="background-color: ${c}; color: #ffffff; width: ${d}px; height: ${d}px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: ${d*0.5}px; border: 2px solid #ffffff; box-shadow: 0 2px 6px rgba(0, 51, 102, 0.4);">★</div>` : `<div style="background-color: ${c}; width: ${d}px; height: ${d}px; border-radius: 50%; border: 3px solid #ffffff; box-shadow: 0 2px 6px rgba(0, 51, 102, 0.4);"></div>`;
            centerMarker = L.marker([__LAT__, __LON__], { icon: L.divIcon({ className: 'custom-center-icon', html: htmlElement, iconSize: [d, d], iconAnchor: [d/2, d/2] }) }).addTo(map);
        }

        const generateMarkerElement = (color, styleMode, sizeDimension) => {
            const d = parseInt(sizeDimension);
            if (styleMode === "pin") {
                return L.divIcon({ html: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${d*1.3}" height="${d*1.3}"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="${color}" stroke="#ffffff" stroke-width="1.5"/></svg>`, className: '', iconSize: [d*1.3, d*1.3], iconAnchor: [d*0.65, d*1.3] });
            } else if (styleMode === "modern-pin") {
                const w = d * 1.5; const h = d * 2.5; const r = d * 0.45; 
                const customSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 65" width="${w}" height="${h}"><defs><radialGradient id="groundShadow" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#000000" stop-opacity="0.6"/><stop offset="100%" stop-color="#000000" stop-opacity="0"/></radialGradient></defs><ellipse cx="20" cy="55" rx="10" ry="3" fill="url(#groundShadow)" /><path d="M20 18 L20 55" stroke="#222222" stroke-width="2"/><circle cx="20" cy="18" r="${r}" fill="${color}" stroke="#ffffff" stroke-width="1.5"/></svg>`;
                return L.divIcon({ html: `<div style="transform: translate(-50%, -85%); width: ${w}px; height: ${h}px;">${customSvg}</div>`, className: '', iconSize: [w, h], iconAnchor: [0, 0] });
            }
            return L.divIcon({ html: `<div style="background-color: ${color}; width: ${d}px; height: ${d}px; border-radius: 50%; border: 1.5px solid #ffffff; box-shadow: 0 1px 4px rgba(0,0,0,0.2);"></div>`, className: '', iconSize: [d, d], iconAnchor: [d/2, d/2] });
        };

        const layerGroupsRef = {}; const categoryMap = {};

        function compileLayersAndRenderPoints() {
            Object.keys(layerGroupsRef).forEach(k => { map.removeLayer(layerGroupsRef[k]); delete layerGroupsRef[k]; });
            Object.keys(categoryMap).forEach(k => delete categoryMap[k]);
            pts.forEach(p => {
                const layerKey = p.type || 'Unclassified';
                if (!categoryMap[layerKey]) categoryMap[layerKey] = []; categoryMap[layerKey].push(p);
            });
            Object.keys(categoryMap).forEach(key => {
                layerGroupsRef[key] = L.layerGroup().addTo(map);
                const meta = layerMeta[key] || { color: "#003366", style: "modern-pin", size: 16 };
                categoryMap[key].forEach(p => {
                    if (p.visible === false) return;
                    const marker = L.marker([p.lat, p.lon], { icon: generateMarkerElement(meta.color, meta.style, meta.size) }).bindPopup(`<b>${p.name}</b><br><span style="color:#888780;font-size:9px;">${p.type} (${p.source || 'cached'})</span>`);
                    if (p.name && p.name !== 'Unknown') marker.bindTooltip(p.name, { permanent: true, direction: 'top', offset: [0, -10], className: 'poi-text-label' });
                    marker.addTo(layerGroupsRef[key]);
                });
            });
        }
        
        function renderBoundaries(boundaryData) {
            clearBoundaries();
            const styles = {
                region: { color: "#FF6B6B", weight: 2.5, fillOpacity: 0.1, opacity: 0.85, dashArray: "4, 6" },
                province: { color: "#4ECDC4", weight: 2, fillOpacity: 0.08, opacity: 0.8, dashArray: "3, 5" },
                city: { color: "#45B7D1", weight: 1.5, fillOpacity: 0.05, opacity: 0.7 },
                barangay: { color: "#96CEB4", weight: 1, fillOpacity: 0.03, opacity: 0.6 }
            };
            
            let added = false;
            const containerDiv = document.createElement('div');
            containerDiv.id = 'boundary-legend';
            containerDiv.className = 'boundary-legend';
            containerDiv.innerHTML = '<div style="font-weight:800; margin-bottom:4px; font-size:8.5px;">BOUNDARIES</div>';

            for (const [key, data] of Object.entries(boundaryData)) {
                if (data && data.features && data.features.length > 0) {
                    boundaryLayers[key] = L.geoJSON(data, {
                        style: styles[key],
                        onEachFeature: function(feature, layer) {
                            const name = feature.properties?.name || key.toUpperCase();
                            layer.bindTooltip(name, { sticky: true, className: 'boundary-tooltip' });
                        }
                    }).addTo(map);
                    
                    containerDiv.innerHTML += `<div style="display:flex; align-items:center; gap:6px; margin-top:2px;"><div style="width:10px; height:10px; background:${styles[key].color}; opacity:0.7;"></div><span>${key.toUpperCase()}</span></div>`;
                    added = true;
                }
            }
            if (added) document.getElementById('map-container').appendChild(containerDiv);
        }
        
        function clearBoundaries() {
            Object.keys(boundaryLayers).forEach(k => { if (boundaryLayers[k]) { map.removeLayer(boundaryLayers[k]); boundaryLayers[k] = null; } });
            const el = document.getElementById('boundary-legend'); if(el) el.remove();
        }

        window.patchGlobalMarkerStyle = function(v) { Object.keys(layerMeta).forEach(k => layerMeta[k].style = v); compileLayersAndRenderPoints(); };
        window.patchGlobalMarkerSize = function(v) { Object.keys(layerMeta).forEach(k => layerMeta[k].size = parseInt(v)); compileLayersAndRenderPoints(); };
        window.patchGlobalMarkerColor = function(v) { Object.keys(layerMeta).forEach(k => layerMeta[k].color = v); compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); };
        window.triggerLayerUpdate = function(layerKey, property, value) { if (!layerMeta[layerKey]) layerMeta[layerKey] = {}; layerMeta[layerKey][property] = property === 'size' ? parseInt(value) : value; compileLayersAndRenderPoints(); };

        function rebuildSidebarControlLayout() {
            const listBox = document.getElementById('results-list-box'); document.getElementById('results-count').innerText = pts.length;
            if (pts.length === 0) { listBox.innerHTML = "<div style='font-size:9px; padding:12px; color:#888780;'>No elements caught inside context.</div>"; return; }
            let htmlPayload = '';
            const trashSvg = `<svg viewBox="0 0 24 24"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>`;
            const eyeSvg = `<svg viewBox="0 0 24 24"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>`;

            Object.keys(categoryMap).forEach(catName => {
                const meta = layerMeta[catName] || { color: "#003366", style: "modern-pin", size: 16 }; const layerPts = categoryMap[catName] || []; const isLayerVisible = layerPts.some(p => p.visible !== false);
                htmlPayload += `<div class="layer-category-block" id="cat-block-${catName}"><div class="layer-category-header"><div class="layer-header-left" onclick="toggleAccordionCollapse('${catName}')"><span class="color-dot" style="background-color: ${meta.color};"></span><span>${catName} <span style="color:#C9AB4C; font-size:8px;">(${layerPts.length})</span></span></div><div style="display:flex; align-items:center; gap:2px;"><a class="action-icon-trigger" onclick="toggleLayerWorkspaceVisibility('${catName}', ${isLayerVisible})">${eyeSvg}</a><a class="action-icon-trigger delete-btn" onclick="triggerLayerDeletion('${catName}')">${trashSvg}</a><span id="chevron-${catName}" onclick="toggleAccordionCollapse('${catName}')" style="font-size: 8px; color:#C9AB4C; margin-left:4px; cursor:pointer;">▼</span></div></div><div class="config-block-wrapper" style="background:#ffffff; border-bottom:1px dashed rgba(0,51,102,0.05);"><div class="config-flex-row"><select onchange="triggerLayerUpdate('${catName}', 'style', this.value)"><option value="dots" ${meta.style==='dots'?'selected':''}>Dots</option><option value="pin" ${meta.style==='pin'?'selected':''}>Pin</option><option value="modern-pin" ${meta.style==='modern-pin'?'selected':''}>Modern Pin</option></select><input type="range" min="10" max="40" value="${meta.size}" class="slider-control-element" oninput="triggerLayerUpdate('${catName}', 'size', this.value)"><input type="color" value="${meta.color}" onchange="triggerLayerUpdate('${catName}', 'color', this.value); rebuildSidebarControlLayout();"></div></div><div class="layer-category-items collapsed" id="items-${catName}">`;
                layerPts.forEach(p => { const itemVisible = p.visible !== false; htmlPayload += `<div class="results-item" id="res-item-${p.uid}" style="${itemVisible ? '' : 'opacity:0.3;'}"><div style="flex-grow:1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" onclick="map.flyTo([${p.lat}, ${p.lon}], 17);">${p.name || 'Unknown'}</div><div style="display:flex; align-items:center;"><a class="action-icon-trigger" onclick="togglePoiVisibility(${p.uid})">${eyeSvg}</a><a class="action-icon-trigger delete-btn" onclick="removePoiInstance(${p.uid})">${trashSvg}</a></div></div>`; });
                htmlPayload += '</div></div>';
            });
            listBox.innerHTML = htmlPayload;
        }

        window.toggleAccordionCollapse = function(catKey) { const panel = document.getElementById('items-' + catKey); const chev = document.getElementById('chevron-' + catKey); if(panel) { panel.classList.toggle('collapsed'); chev.innerText = panel.classList.contains('collapsed') ? '▼' : '▲'; } };
        window.togglePoiVisibility = function(uid) { const p = pts.find(item => item.uid === uid); if (p) { p.visible = (p.visible === false); compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); } };
        window.removePoiInstance = function(uid) { pts = pts.filter(item => item.uid !== uid); compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); };
        window.toggleLayerWorkspaceVisibility = function(catKey, currentlyVisible) { pts.forEach(p => { if (p.type === catKey) p.visible = !currentlyVisible; }); compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); };
        window.triggerLayerDeletion = function(catKey) { pts = pts.filter(p => p.type !== catKey); delete layerMeta[catKey]; compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); };

        renderTargetCenterIcon(); renderRadiusCircleBounds(); compileLayersAndRenderPoints(); rebuildSidebarControlLayout();
        
        if (pts.length > 0 && !__IS_STALE__) {
            const validPts = pts.filter(p => p.visible !== false); 
            if (validPts.length > 0) map.fitBounds(L.featureGroup([L.marker([__LAT__, __LON__]), ...validPts.map(p => L.marker([p.lat, p.lon]))]).getBounds().pad(0.05));
        }
        
        const boundaryData = __BOUNDARY_DATA__;
        if (boundaryData && Object.keys(boundaryData).length > 0) renderBoundaries(boundaryData);
    </script>
</body>
</html>
"""

# HTML Template variable compilation
fallback_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", st.session_state.geo_coords)
render_lat, render_lon = (float(fallback_match.group(1)), float(fallback_match.group(2))) if fallback_match else (14.5995, 120.9842)

leaflet_html = (leaflet_template
                .replace("__LAT__", str(render_lat))
                .replace("__LON__", str(render_lon))
                .replace("__RADIUS__", str(radius_val))
                .replace("__IS_STALE__", "true" if (lat_coord != st.session_state.last_scan_lat or lon_coord != st.session_state.last_scan_lon) else "false")
                .replace("__GLOBAL_MARKER_SIZE__", str(st.session_state.global_marker_size))
                .replace("__GLOBAL_MARKER_COLOR__", str(st.session_state.global_marker_color))
                .replace("__TARGET_CONFIG_JSON__", target_config_json)
                .replace("__RADIUS_CONFIG_JSON__", radius_config_json)
                .replace("__LAYER_META_JSON__", layer_meta_json)
                .replace("__GEOJSON__", geojson_str)
                .replace("__API_LOG_PANEL__", api_log_panel)
                .replace("__BOUNDARY_DATA__", boundary_data_json))

st.components.v1.html(leaflet_html, height=850, scrolling=False)
