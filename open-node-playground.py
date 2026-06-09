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
# GLOBAL GEOPROCESSING REPOSITORIES
# -----------------------------------------------------------------------------
GITHUB_POI_BASE = "https://raw.githubusercontent.com/pyscriptcli/osm-repository/main/data/provinces"
GITHUB_BOUNDARY_BASE = "https://raw.githubusercontent.com/pyscriptcli/osm-repository/main/boundaries"

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
    # Visayas
    "cebu": [123.50, 9.50, 124.20, 11.00],
    "leyte": [124.30, 9.80, 125.60, 11.50],
    "bohol": [123.70, 9.50, 124.60, 10.10],
    "negros_oriental": [122.80, 9.00, 123.50, 10.50],
    "negros_occidental": [122.30, 9.30, 123.40, 11.00],
    "samar": [124.80, 11.00, 125.80, 12.50],
    "biliran": [124.30, 11.40, 124.60, 11.70],
    "siquijor": [123.40, 9.10, 123.70, 9.30],
    # Mindanao
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
# CORE SPATIAL CORE PROCESSING UTILITIES
# -----------------------------------------------------------------------------
@st.cache_data(ttl=86400, show_spinner=False)
def get_province_list():
    url = f"{GITHUB_POI_BASE}/index.json"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return list(response.json().get('provinces', {}).keys())
        return []
    except:
        return list(PROVINCE_BOUNDS.keys())

@st.cache_data(ttl=86400, show_spinner=False)
def load_province_pois(province_name):
    url = f"{GITHUB_POI_BASE}/{province_name}.json"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_province_from_coords(lat, lon):
    for province, bbox in PROVINCE_BOUNDS.items():
        if bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]:
            return province
    return None

def filter_pois_by_radius(pois, center_lat, center_lon, radius_meters):
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return R * (2 * math.asin(math.sqrt(a)))
    
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
                if key in poi_type or value in poi_type:
                    filtered.append(poi)
                    break
            else:
                if tag_clean in poi_type:
                    filtered.append(poi)
                    break
    return filtered

# -----------------------------------------------------------------------------
# MULTI-LAYER OVERPASS FALLBACK POI SCANNER
# -----------------------------------------------------------------------------
def load_pois_from_overpass_fallback(lat, lon, radius_meters, selected_tags):
    """Fallback Engine translating user tags directly to an Overpass QL query"""
    clauses = []
    for tag in selected_tags:
        cleaned = tag.strip()
        match_reg = re.match(r'"([^"]+)"\s*([~=])\s*"([^"]+)"(?:,i)?', cleaned)
        if match_reg:
            k, op, v = match_reg.groups()
            is_i = ",i" in cleaned
            modifier = ",i" if is_i else ""
            if op == '~':
                clauses.append(f'node["{k}"~"{v}"{modifier}](around:{radius_meters},{lat},{lon});')
                clauses.append(f'way["{k}"~"{v}"{modifier}](around:{radius_meters},{lat},{lon});')
            else:
                clauses.append(f'node["{k}"="{v}"](around:{radius_meters},{lat},{lon});')
                clauses.append(f'way["{k}"="{v}"](around:{radius_meters},{lat},{lon});')
        else:
            clauses.append(f'node[{cleaned}](around:{radius_meters},{lat},{lon});')
            clauses.append(f'way[{cleaned}](around:{radius_meters},{lat},{lon});')
            
    if not clauses:
        return []
        
    query = f"""
    [out:json][timeout:30];
    (
      {" ".join(clauses)}
    );
    out body geom;
    """
    try:
        response = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=30)
        if response.status_code == 200:
            raw_elements = response.json().get('elements', [])
            parsed_records = []
            for idx, elem in enumerate(raw_elements):
                lat_val = elem.get('lat') or (elem.get('center', {}).get('lat') if 'center' in elem else None)
                lon_val = elem.get('lon') or (elem.get('center', {}).get('lon') if 'center' in elem else None)
                if not lat_val or not lon_val:
                    continue
                
                tags = elem.get('tags', {})
                name_str = tags.get('name') or tags.get('brand') or 'Unknown Mapped Asset'
                
                # Deduce category classification label
                type_label = "POI"
                for tag_item in selected_tags:
                    m = re.search(r'"([^"]+)"', tag_item)
                    if m and m.group(1) in tags:
                        type_label = f"{m.group(1)}={tags[m.group(1)]}"
                        break

                parsed_records.append({
                    "lat": lat_val,
                    "lon": lon_val,
                    "name": name_str,
                    "type": type_label,
                    "source": "overpass_fallback",
                    "has_footprint": "geometry" in elem,
                    "footprint_geojson": {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[ [pt['lon'], pt['lat']] for pt in elem['geometry'] ]]} } if "geometry" in elem else None,
                    "visible": True,
                    "uid": int(hashlib.sha256(f"{lat_val}{lon_val}{name_str}".encode()).hexdigest(), 16) % 1000000
                })
            return parsed_records
        return []
    except Exception as e:
        add_api_log(f"Overpass POI fallback exception: {str(e)[:100]}", "ERROR")
        return []

# -----------------------------------------------------------------------------
# GEOMETRIC BOUNDARY FUNCTIONS
# -----------------------------------------------------------------------------
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
                filtered = [f for f in data.get('features', []) if f.get('properties', {}).get('name', '').lower() == area_name.lower()]
                if filtered:
                    return {"type": "FeatureCollection", "features": filtered}
            return data
        return None
    except Exception as e:
        add_api_log(f"GitHub boundary engine fault for {area_name}: {str(e)[:100]}", "WARNING")
        return None

@st.cache_data(ttl=86400, show_spinner=False)
def reverse_geocode_location(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"
        response = requests.get(url, headers={"User-Agent": "OpenNode/1.0"}, timeout=10)
        if response.status_code == 200:
            addr = response.json().get('address', {})
            return {
                "region": addr.get('state', ''),
                "province": addr.get('province', '') or addr.get('state_district', ''),
                "city": addr.get('city', '') or addr.get('municipality', '') or addr.get('town', '') or addr.get('en', ''),
                "barangay": addr.get('suburb', '') or addr.get('neighbourhood', '') or addr.get('village', '') or addr.get('quarter', ''),
                "lat": lat, "lon": lon
            }
        return None
    except Exception as e:
        add_api_log(f"Reverse geocode engine fault: {str(e)[:100]}", "ERROR")
        return None

@st.cache_data(ttl=86400, show_spinner=False)
def get_boundary_geojson(area_name, admin_level):
    if not area_name:
        return None
    
    boundary_type_map = {"4": "region", "5": "province", "6": "city", "7": "city", "8": "barangay", "9": "barangay"}
    boundary_type = boundary_type_map.get(str(admin_level), "province")
    
    # Primary Source: GitHub Repositories
    github_data = load_github_boundary(area_name, boundary_type)
    if github_data and github_data.get('features'):
        add_api_log(f"Extracted dynamic polygon for [{area_name}] via GitHub Engine", "INFO")
        return github_data
    
    # Fallback Source: Overpass API
    add_api_log(f"GitHub polygon missing for [{area_name}]. Executing Overpass fallback...", "WARNING")
    query = f"""
    [out:json][timeout:30];
    (
      relation["admin_level"="{admin_level}"]["name"="{area_name}"];
      relation["admin_level"="{admin_level}"]["name:en"="{area_name}"];
    );
    out geom;
    """
    try:
        response = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=30)
        if response.status_code == 200:
            elements = response.json().get('elements', [])
            features = []
            for element in elements:
                if element.get('type') == 'relation' and 'bounds' in element:
                    coords = []
                    # Transform standard relation geometry nodes directly to a closed LinearRing polygon loop
                    for member in element.get('members', []):
                        if 'geometry' in member:
                            for pt in member['geometry']:
                                coords.append([pt['lon'], pt['lat']])
                    if len(coords) >= 3:
                        features.append({
                            "type": "Feature",
                            "geometry": {"type": "Polygon", "coordinates": [coords]},
                            "properties": {"name": element.get('tags', {}).get('name', area_name), "admin_level": admin_level}
                        })
            if features:
                return {"type": "FeatureCollection", "features": features}
        return None
    except Exception as e:
        add_api_log(f"Overpass boundary resolution failure: {str(e)[:100]}", "ERROR")
        return None

# -----------------------------------------------------------------------------
# INTERFACE STYLE MANUAL OVERRIDES
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Open Node", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Montserrat:wght@400;500;600;700;800&display=swap');
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
            width: 280px !important; min-width: 280px !important; max-width: 280px !important;
            box-shadow: 2px 0 15px rgba(0,0,0,0.03) !important;
        }
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] { display: none !important; }
        ::-webkit-scrollbar { width: 0px !important; }
        * { scrollbar-width: none !important; }
        [data-testid="stHeader"], header, #stDecoration { display: none !important; }
        [data-testid="stAppViewContainer"] { display: flex !important; width: 100vw !important; height: 100vh !important; overflow: hidden !important; }
        [data-testid="stMain"] { flex-grow: 1 !important; width: calc(100vw - 280px) !important; height: 100vh !important; overflow: hidden !important; }
        .block-container, [data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"], .stElementContainer { padding: 0px !important; margin: 0px !important; max-width: 100% !important; gap: 0rem !important; }
        iframe { height: 100vh !important; width: 100% !important; border: none !important; display: block !important; }
        div[data-baseweb="input"], div[data-baseweb="select"] { background-color: transparent !important; border: none !important; border-bottom: 1px solid rgba(201, 171, 76, 0.5) !important; border-radius: 0px !important; }
        div.stButton > button[kind="secondary"], [data-testid="stPopover"] > button { background-color: var(--brand-midnight) !important; border: 1px solid var(--brand-midnight) !important; border-radius: 2px !important; width: 100% !important; padding: 4px !important; }
        div.stButton > button[kind="secondary"]:hover, [data-testid="stPopover"] > button:hover { background-color: var(--brand-gold) !important; border-color: var(--brand-gold) !important; }
        div.stButton > button[kind="secondary"] p, [data-testid="stPopover"] > button p { color: var(--white-clean) !important; font-weight: 700 !important; font-size: 9px !important; text-transform: uppercase !important; }
        div.stDownloadButton > button { background-color: var(--brand-midnight) !important; border: none !important; border-radius: 2px !important; width: 100% !important; }
        div.stDownloadButton > button:hover { background-color: var(--brand-gold) !important; }
        div.stButton > button[kind="primary"] { background: transparent !important; border: none !important; margin-top: 2px; }
        div.stButton > button[kind="primary"] p { color: var(--text-muted) !important; font-size: 9px !important; }
        .brand-title { font-family: 'Cormorant Garamond', serif !important; font-style: italic; color: var(--brand-midnight); font-size: 30px; text-align: center; border-bottom: 1px solid var(--brand-gold); padding-bottom: 6px; margin-bottom: 10px; }
        .py-loading-container { position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%); width: 340px; background: #ffffff; padding: 24px; border-radius: 4px; border: 1px solid rgba(0, 51, 102, 0.15); box-shadow: 0 10px 30px rgba(0, 51, 102, 0.15); text-align: center; z-index: 999999; }
        .py-spinner { width: 40px; height: 40px; border: 4px solid rgba(0, 51, 102, 0.1); border-left-color: #003366; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 16px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .api-log-container { position: absolute; bottom: 12px; right: 12px; width: 380px; max-height: 280px; background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(8px); border-radius: 8px; border-left: 3px solid #C9AB4C; z-index: 10000; color: #e0e0e0; font-size: 10px; display: flex; flex-direction: column; }
        .api-log-header { padding: 6px 10px; background: rgba(0,0,0,0.6); font-weight: 700; display: flex; justify-content: space-between; cursor: pointer; color: #C9AB4C; }
        .api-log-content { overflow-y: auto; padding: 6px; flex-grow: 1; max-height: 220px; font-family: monospace; }
        .api-log-entry { border-bottom: 1px solid rgba(255,255,255,0.1); padding: 4px 0; }
        .api-log-info { color: #88ffaa; } .api-log-error { color: #ff8888; } .api-log-warning { color: #ffaa66; }
        .boundary-tooltip { font-family: 'Montserrat', sans-serif; font-size: 9px; font-weight: 600; background: rgba(0, 51, 102, 0.9); color: white; padding: 2px 6px; border-radius: 2px; }
        .boundary-legend { background: rgba(255,255,255,0.95); padding: 6px 10px; border-radius: 4px; font-size: 9px; color: #003366; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CORE LOGGING AND STATE PIPELINE INITIALIZATION
# -----------------------------------------------------------------------------
if 'api_logs' not in st.session_state: st.session_state.api_logs = []
def add_api_log(message, level="INFO"):
    st.session_state.api_logs.append({"time": datetime.now().strftime("%H:%M:%S"), "message": message, "level": level})
    if len(st.session_state.api_logs) > 100: st.session_state.api_logs = st.session_state.api_logs[-100:]

DEFAULT_COORDS = "14.5995, 120.9842"
if 'geo_coords' not in st.session_state: st.session_state.geo_coords = DEFAULT_COORDS
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = 1000
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'last_scan_lat' not in st.session_state: st.session_state.last_scan_lat = 14.5995
if 'last_scan_lon' not in st.session_state: st.session_state.last_scan_lon = 120.9842
if 'layer_meta' not in st.session_state: st.session_state.layer_meta = {}
if 'scan_active_loading' not in st.session_state: st.session_state.scan_active_loading = False
if 'show_boundaries' not in st.session_state: st.session_state.show_boundaries = False
if 'boundary_levels' not in st.session_state: st.session_state.boundary_levels = []
if 'current_location_info' not in st.session_state: st.session_state.current_location_info = None
if 'boundary_geojson_data' not in st.session_state: st.session_state.boundary_geojson_data = {}

if 'target_config' not in st.session_state: st.session_state.target_config = {"size": 24, "color": "#003366", "style": "star"}
if 'radius_config' not in st.session_state: st.session_state.radius_config = {"color": "#003366", "fill_opacity": 0.08, "weight": 1.5}
if 'global_marker_style' not in st.session_state: st.session_state.global_marker_style = "modern-pin"
if 'global_marker_size' not in st.session_state: st.session_state.global_marker_size = 16
if 'global_marker_color' not in st.session_state: st.session_state.global_marker_color = "#003366"

POI_CONFIG = {
    "COMMERCIAL & OFFICES": [['Corporate Office', '"building"~"office|commercial",i'], ['Bank', '"amenity"="bank"'], ['ATM', '"amenity"="atm"']],
    "RETAIL": [['Mall/Department Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"market|grocery",i'], ['Convenience Store', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"']],
    "FOOD & HOSPITALITY": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee Shop', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"'], ['Hotel', '"tourism"="hotel"']],
    "HEALTH & EMERGENCY": [['Hospital', '"amenity"~"hospital|clinic",i'], ['Police Station', '"amenity"="police"'], ['Fire Station', '"amenity"="fire_station"']]
}

# -----------------------------------------------------------------------------
# SIDEBAR REACTION CONTROL CONTROLLERS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="brand-title">Open Node</div>', unsafe_allow_html=True)
    selected_tags = []
    scan_triggered = st.button("SCAN AREA", type="secondary", use_container_width=True)
    
    location_input = st.text_input("COORDINATES", value=st.session_state.geo_coords)
    radius_val = st.number_input("RADIUS (METERS)", min_value=100, max_value=50000, value=st.session_state.geo_radius, step=100)
    st.session_state.geo_radius = radius_val

    coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", location_input)
    if coord_match:
        lat_coord, lon_coord = float(coord_match.group(1)), float(coord_match.group(2))
        st.session_state.geo_coords = location_input
    else:
        lat_coord, lon_coord = 14.5995, 120.9842

    search_query = st.text_input("FILTER CONFIGS", value="").lower()
    for cat_name, node_items in POI_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for label, tag in matched:
                    if st.checkbox(label, key=f"chk_{cat_name}_{label}"): selected_tags.append(tag)

    st.markdown("<hr style='margin:12px 0; border:0; border-top:1px solid rgba(0,0,0,0.08);'>", unsafe_allow_html=True)
    show_boundaries_toggle = st.checkbox("Show Administrative Boundaries", value=st.session_state.show_boundaries)
    
    if show_boundaries_toggle:
        st.session_state.show_boundaries = True
        boundary_options = st.multiselect("Select boundary layers:", options=["Region", "Province", "City/Municipality", "Barangay"], default=st.session_state.boundary_levels)
        st.session_state.boundary_levels = boundary_options
    else:
        st.session_state.show_boundaries = False
        st.session_state.boundary_levels = []
        st.session_state.boundary_geojson_data = {}

    if scan_triggered:
        if not selected_tags:
            st.error("Select ≥ 1 layer parameters.")
        else:
            st.session_state.scan_active_loading = True
            st.rerun()

    if st.button("RESET SIMULATOR", type="primary"):
        st.session_state.scanned_records = []
        st.session_state.boundary_geojson_data = {}
        st.session_state.current_location_info = None
        st.session_state.api_logs = []
        st.rerun()

# -----------------------------------------------------------------------------
# DUAL SOURCE ENGINE EXECUTION PIPELINE
# -----------------------------------------------------------------------------
if st.session_state.scan_active_loading:
    records = []
    add_api_log("Initializing dual-source spatial index engine query", "INFO")
    
    # Executing Primary Phase: GitHub Repository Index Mapping
    province_name = get_province_from_coords(lat_coord, lon_coord)
    github_success = False
    
    if province_name:
        add_api_log(f"Mapping coordinates to bounded cluster: {province_name}", "INFO")
        all_province_pois = load_province_pois(province_name)
        if all_province_pois:
            radius_filtered = filter_pois_by_radius(all_province_pois, lat_coord, lon_coord, radius_val)
            tag_filtered = filter_pois_by_tags(radius_filtered, selected_tags)
            
            for idx, poi in enumerate(tag_filtered):
                records.append({
                    "lat": poi['lat'], "lon": poi['lon'], "name": poi.get('name', 'Unknown Asset'),
                    "type": poi.get('type', 'Unclassified POI'), "source": "github",
                    "has_footprint": False, "footprint_geojson": None, "visible": True, "uid": idx
                })
            if records:
                github_success = True
                add_api_log(f"Successfully unpacked {len(records)} items via static primary repository.", "INFO")

    # Executing Secondary Fallback Phase: Multi-Layer Overpass Fetching
    if not github_success:
        add_api_log("Primary repository trace out-of-bounds or empty. Engaging multi-layer Overpass fallback protocol.", "WARNING")
        records = load_pois_from_overpass_fallback(lat_coord, lon_coord, radius_val, selected_tags)
        if records:
            add_api_log(f"Fallback engine processed {len(records)} dynamic elements from Overpass network API.", "INFO")
        else:
            add_api_log("Dual-source lookup failed to fetch matching criteria parameters.", "ERROR")

    st.session_state.scanned_records = records
    st.session_state.last_scan_lat = lat_coord
    st.session_state.last_scan_lon = lon_coord
    
    # Process Boundary Spatial Entities instantly if checked
    if st.session_state.show_boundaries:
        st.session_state.current_location_info = reverse_geocode_location(lat_coord, lon_coord)
        if st.session_state.current_location_info:
            loc = st.session_state.current_location_info
            level_mapping = {"Region": (loc.get('region'), 4), "Province": (loc.get('province'), 5), "City/Municipality": (loc.get('city'), 6), "Barangay": (loc.get('barangay'), 8)}
            
            boundaries_built = {}
            for level_name in st.session_state.boundary_levels:
                area_name, adv_lvl = level_mapping.get(level_name, (None, None))
                if area_name:
                    poly_geojson = get_boundary_geojson(area_name, adv_lvl)
                    if poly_geojson:
                        boundaries_built[level_name.lower().replace("/municipality", "")] = poly_geojson
            st.session_state.boundary_geojson_data = boundaries_built

    st.session_state.scan_active_loading = False
    st.rerun()

# -----------------------------------------------------------------------------
# GRAPHICS TRANSFORMATION & MAP COMPONENT GENERATION
# -----------------------------------------------------------------------------
pts_active = st.session_state.scanned_records
unique_layers = list(set([p.get('type', 'Unclassified') for p in pts_active]))
cat_palette = ["#003366", "#C9AB4C", "#1A5A8A", "#A8862E", "#3D7DA8"]

for idx, layer in enumerate(unique_layers):
    if layer not in st.session_state.layer_meta:
        st.session_state.layer_meta[layer] = {
            "color": cat_palette[idx % len(cat_palette)],
            "style": st.session_state.global_marker_style,
            "size": st.session_state.global_marker_size
        }

# Build log HTML panel component
api_logs_html = "".join([f'<div class="api-log-entry"><span style="color:#C9AB4C;">[{l["time"]}]</span> <span class="api-log-{l["level"].lower()}">{l["message"]}</span></div>' for l in st.session_state.api_logs[-20:]])
api_log_panel = f'<div class="api-log-container"><div class="api-log-header">📡 LIVE ENGINE ACTIVITY LOG</div><div class="api-log-content">{api_logs_html or "System ready. Click SCAN AREA."}</div></div>'

# Mapping Variable Injections
leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body, html, #map { margin:0; padding:0; height:100vh; width:100%; background:#fff; font-family:sans-serif; }
        #scan-results-panel { position:absolute; top:10px; right:10px; z-index:1000; background:#fff; width:280px; max-height:80vh; border-radius:4px; border:1px solid rgba(0,0,0,0.1); display:flex; flex-direction:column; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.1); }
        .results-header { background:#003366; color:#fff; padding:10px; font-size:10px; font-weight:800; display:flex; justify-content:space-between; text-transform:uppercase; border-bottom:2px solid #C9AB4C; }
        .results-list { overflow-y:auto; padding:5px; font-size:11px; }
        .poi-text-label { background:#fff; border:1px solid #003366; padding:1px 4px; border-radius:2px; font-size:9px; font-weight:700; }
        .boundary-tooltip { background: rgba(0, 51, 102, 0.9); color:#fff; font-size:9px; padding:2px 6px; border-radius:2px; font-weight:bold; }
        .boundary-legend { background:#fff; padding:6px; font-size:9px; border-radius:4px; border:1px solid rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div id="map"></div>
    <div id="scan-results-panel">
        <div class="results-header"><span>WORKSPACE CONTROL</span><span style="color:#C9AB4C;">PINS: __COUNT__</span></div>
        <div class="results-list" id="list-box">__LIST_DATA__</div>
    </div>
    __API_PANEL__

    <script>
        const map = L.map('map', { zoomControl:false, attributionControl:false }).setView([__LAT__, __LON__], 14);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom:20 }).addTo(map);
        
        // Render Radius Boundary
        L.circle([__LAT__, __LON__], { radius: __RADIUS__, color: '#003366', weight:1.5, fillColor:'#003366', fillOpacity:0.05 }).addTo(map);
        L.marker([__LAT__, __LON__]).addTo(map);

        // Render Dynamic Administrative Boundary Polygons
        const boundaryData = __BOUNDARY_DATA__;
        const bStyles = { region: "#FF6B6B", province: "#4ECDC4", city: "#45B7D1", barangay: "#96CEB4" };
        
        for (const [layerKey, geojson] of Object.entries(boundaryData)) {
            if (geojson && geojson.features) {
                L.geoJSON(geojson, {
                    style: { color: bStyles[layerKey] || "#003366", weight: 2, fillOpacity: 0.06 },
                    onEachFeature: function(f, layer) {
                        if (f.properties && f.properties.name) {
                            layer.bindTooltip(f.properties.name, { sticky: true, className: 'boundary-tooltip' });
                        }
                    }
                }).addTo(map);
            }
        }

        // Render Loaded Asset Pins
        const pts = __GEOJSON__;
        const meta = __LAYER_META__;
        pts.forEach(p => {
            const lyrMeta = meta[p.type] || { color: "#003366" };
            if (p.has_footprint && p.footprint_geojson) {
                L.geoJSON(p.footprint_geojson, { style: { color: lyrMeta.color, fillColor: lyrMeta.color, fillOpacity: 0.3 } }).addTo(map);
            }
            const marker = L.circleMarker([p.lat, p.lon], { radius: 6, fillColor: lyrMeta.color, color: "#fff", weight: 1, fillOpacity: 0.9 }).addTo(map);
            marker.bindPopup(`<b>${p.name}</b><br><span style="color:#888; font-size:9px;">${p.type} [${p.source}]</span>`);
        });
    </script>
</body>
</html>
"""

# Compile element listing DOM values
list_data_html = "".join([f'<div style="padding:4px; border-bottom:1px solid #eee;"><b>{p["name"]}</b><br><span style="font-size:9px; color:#888;">{p["type"]} ({p["source"]})</span></div>' for p in pts_active])

html_payload = (leaflet_template
                .replace("__LAT__", str(lat_coord))
                .replace("__LON__", str(lon_coord))
                .replace("__RADIUS__", str(st.session_state.geo_radius))
                .replace("__COUNT__", str(len(pts_active)))
                .replace("__LIST_DATA__", list_data_html if list_data_html else '<div style="color:#888; padding:10px;">Execute a spatial scan query.</div>')
                .replace("__GEOJSON__", json.dumps(pts_active))
                .replace("__LAYER_META__", json.dumps(st.session_state.layer_meta))
                .replace("__API_PANEL__", api_log_panel)
                .replace("__BOUNDARY_DATA__", json.dumps(st.session_state.boundary_geojson_data)))

st.components.v1.html(html_payload, height=850, scrolling=False)
