"""
Trade Area Scan - Unified Engine Version
Features: Seamless Client-Side Map State, Floating Viewport Toggle, Context-Aware Sidebar
"""

import streamlit as st
import requests
import re
import json
import os
import time
from typing import Dict, List, Tuple, Any, Optional

# =====================================================================
# 1. CONSTANTS & CONFIGURATION
# =====================================================================
DEFAULT_LAT = 14.5995
DEFAULT_LON = 120.9842
DEFAULT_COORDS = f"{DEFAULT_LAT}, {DEFAULT_LON}"
DEFAULT_RADIUS = 1000
API_TIMEOUT = 100
NOMINATIM_TIMEOUT = 10
OSM_USER_AGENT = "TradeAreaScan/5.0"

COLOR_MIDNIGHT = "#003366"
COLOR_GOLD = "#C9AB4C"
COLOR_DARK = "#001F3F"
COLOR_WHITE = "#ffffff"
COLOR_BG_LIGHT = "#f8fafc"
COLOR_TEXT_MUTED = "#888780"
SHADOW_SOFT = "0 4px 12px rgba(0, 51, 102, 0.08)"

# =====================================================================
# 2. SESSION STATE INITIALIZATION
# =====================================================================
def init_session_state() -> None:
    if "geo_coords" not in st.session_state:
        st.session_state.geo_coords = DEFAULT_COORDS
    if "geo_radius" not in st.session_state:
        st.session_state.geo_radius = DEFAULT_RADIUS
    if "scanned_records" not in st.session_state:
        st.session_state.scanned_records = []
    if "last_scan_lat" not in st.session_state:
        st.session_state.last_scan_lat = DEFAULT_LAT
    if "last_scan_lon" not in st.session_state:
        st.session_state.last_scan_lon = DEFAULT_LON
    if "last_geocoded_query" not in st.session_state:
        st.session_state.last_geocoded_query = ""
    if "active_module" not in st.session_state:
        st.session_state.active_module = "SCAN"  # Default Mode
    if "editor_layers" not in st.session_state:
        st.session_state.editor_layers = []
    if "active_editor_layer" not in st.session_state:
        st.session_state.active_editor_layer = ""

def setup_light_mode_lock() -> None:
    config_dir = ".streamlit"
    config_file = os.path.join(config_dir, "config.toml")
    if not os.path.exists(config_file):
        os.makedirs(config_dir, exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            f.write("[theme]\nbase=\"light\"\n")

setup_light_mode_lock()
st.set_page_config(page_title="Trade Area Scan", layout="wide", initial_sidebar_state="expanded")

# =====================================================================
# 3. GLOBAL STYLES
# =====================================================================
def apply_global_styles() -> None:
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Montserrat:wght@400;500;600;700;800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0');

        :root {{
            --brand-midnight: {COLOR_MIDNIGHT} !important;
            --brand-gold: {COLOR_GOLD} !important;
            --brand-dark: {COLOR_DARK} !important;
            --white-clean: {COLOR_WHITE} !important;
            --bg-offwhite: {COLOR_BG_LIGHT} !important;
            --text-muted: {COLOR_TEXT_MUTED} !important;
            --soft-shadow: {SHADOW_SOFT} !important;
        }}
        
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {{
            background-color: var(--white-clean) !important;
            color: var(--brand-midnight) !important;
            font-family: 'Montserrat', sans-serif !important;
        }}
        
        [data-testid="stSidebar"] {{
            background-color: var(--bg-offwhite) !important;
            color: var(--brand-midnight) !important;
            border-right: 1px solid rgba(0, 51, 102, 0.08) !important;
            width: 280px !important; min-width: 280px !important; max-width: 280px !important;
            box-shadow: 2px 0 15px rgba(0,0,0,0.03) !important;
        }}
        
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] {{ display: none !important; }}
        ::-webkit-scrollbar {{ width: 0px !important; background: transparent !important; }}
        * {{ scrollbar-width: none !important; -ms-overflow-style: none !important; }}
        
        [data-testid="stHeader"], header, #stDecoration {{ display: none !important; }}
        [data-testid="stAppViewContainer"] {{ display: flex !important; flex-direction: row !important; width: 100vw !important; height: 100vh !important; overflow: hidden !important; }}
        [data-testid="stMain"] {{ flex-grow: 1 !important; width: calc(100vw - 280px) !important; height: 100vh !important; overflow: hidden !important; margin: 0px !important; padding: 0px !important; }}
        .block-container, [data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"], .stElementContainer {{ padding: 0px !important; margin: 0px !important; max-width: 100% !important; gap: 0rem !important; }}
        iframe {{ height: 100vh !important; width: 100% !important; border: none !important; display: block !important; }}
        
        [data-testid="stSidebarUserContent"] {{
            padding-top: 12px !important; padding-left: 12px !important; padding-right: 12px !important; 
            height: 100vh !important; overflow-y: auto !important; overflow-x: hidden !important;
        }}
        
        div[data-baseweb="input"], div[data-baseweb="select"] {{ 
            background-color: transparent !important; border: none !important; 
            border-bottom: 1px solid rgba(201, 171, 76, 0.5) !important; border-radius: 0px !important; 
            box-shadow: none !important; 
        }}
        div[data-baseweb="input"]:focus-within {{ border-bottom: 2px solid var(--brand-gold) !important; }}
        
        div.stButton > button[kind="secondary"], [data-testid="stPopover"] > button {{ 
            background-color: var(--brand-midnight) !important; border: 1px solid var(--brand-midnight) !important; 
            border-radius: 2px !important; width: 100% !important; padding: 6px !important; 
            box-shadow: var(--soft-shadow) !important; transition: all 0.3s ease !important; 
        }}
        div.stButton > button[kind="secondary"]:hover, [data-testid="stPopover"] > button:hover {{ 
            background-color: var(--brand-gold) !important; border-color: var(--brand-gold) !important; 
        }}
        div.stButton > button[kind="secondary"] p, [data-testid="stPopover"] > button p, div.stDownloadButton > button p {{ 
            color: var(--white-clean) !important; font-weight: 700 !important; font-size: 9px !important; 
            text-transform: uppercase !important; letter-spacing: 1px; 
        }}
        div.stDownloadButton > button {{ background-color: var(--brand-midnight) !important; border: none !important; border-radius: 2px !important; width: 100% !important; padding: 4px !important; }}
        div.stDownloadButton > button:hover {{ background-color: var(--brand-gold) !important; }}
        
        div.stButton > button[kind="primary"] {{ background: transparent !important; border: none !important; color: var(--text-muted) !important; box-shadow: none !important; padding: 0 !important; margin-top: 2px; display: inline-flex; }}
        div.stButton > button[kind="primary"] p {{ color: var(--text-muted) !important; font-size: 9px !important; font-weight: 600 !important; text-decoration: none !important; text-transform: uppercase; }}
        div.stButton > button[kind="primary"]:hover p {{ color: #AA2E20 !important; }}
        
        [data-testid="stSidebar"] .st-expander {{ border: 1px solid rgba(0, 51, 102, 0.05) !important; background-color: var(--white-clean) !important; border-radius: 2px !important; margin-bottom: 2px !important; overflow: hidden !important; }}
        [data-testid="stSidebar"] .st-expander summary p {{ font-size: 9px !important; font-weight: 500 !important; }}
        .stCheckbox label p {{ font-size: 10px !important; font-weight: 500 !important; }}
        div[data-baseweb="checkbox"] input:checked + div, div[data-baseweb="checkbox"] div[aria-checked="true"] {{ background-color: var(--brand-midnight) !important; border-color: var(--brand-midnight) !important; }}
        
        .brand-title {{ font-family: 'Cormorant Garamond', serif !important; font-style: italic; color: var(--brand-midnight); font-size: 28px; text-align: center; border-bottom: 1px solid var(--brand-gold); padding-bottom: 6px; margin-bottom: 20px; }}
        .stTextInput label p, .stNumberInput label p {{ font-size: 9px !important; font-weight: 500 !important; letter-spacing: 0.5px; color: var(--text-muted) !important; }}
        
        /* Bridge Visibility Control */
        div[data-testid="stTextInput"]:has(input[aria-label="bridge_mode_sync"]) { display: none !important; height: 0 !important; overflow: hidden !important; }
    </style>
    """, unsafe_allow_html=True)

# =====================================================================
# 4. JS-TO-PYTHON STATE BRIDGE
# =====================================================================
def run_state_bridge():
    """Listens for Mode changes pushed from the JavaScript map context."""
    sync_val = st.text_input("bridge_mode_sync", value="", key="bridge_mode_sync_input", label_visibility="collapsed")
    if sync_val and sync_val != st.session_state.active_module:
        st.session_state.active_module = sync_val
        st.rerun()

# =====================================================================
# 5. POI CONFIGURATION
# =====================================================================
POI_CONFIG: Dict[str, List[List[str]]] = {
    "COMMERCIAL": [
        ["Corporate Office", '"building"~"office|commercial",i'], ["IT/Tech Center", '"office"~"it|telecommunication",i'],
        ["Business Center", '"building"="commercial"'], ["Hospital", '"amenity"~"hospital|clinic",i'],
        ["Hotel", '"tourism"="hotel"'], ["Motel", '"tourism"="motel"'],
    ],
    "RESIDENTIAL": [
        ["Apartments", '"building"="apartments"'], ["House", '"building"="house"'],
        ["Residential Area", '"landuse"="residential"'], ["Condominium", '"building"="residential"'],
    ],
    "RETAIL": [
        ["Mall/Department Store", '"shop"~"mall|department_store",i'], ["Supermarket", '"shop"~"supermarket|grocery",i'],
        ["Convenience Store", '"shop"="convenience"'], ["Pharmacy", '"amenity"="pharmacy"'],
        ["Hardware", '"shop"~"hardware|doityourself",i'], ["General Shops", '"shop"~"boutique|clothes|shoes",i'],
    ],
    "FOOD AND BEVERAGES": [
        ["Restaurant", '"amenity"="restaurant"'], ["Cafe/Coffee Shop", '"amenity"~"cafe|coffee",i'],
        ["Fast Food", '"amenity"="fast_food"'], ["Bar/Pub/Nightclub", '"amenity"~"bar|pub|nightclub",i'],
    ]
}

# =====================================================================
# 6. UTILITY FUNCTIONS
# =====================================================================
def escape_xml(text: str) -> str:
    return text.replace("&", "&").replace("<", "<").replace(">", ">").replace('"', """).replace("'", "'")

def escape_javascript(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r").replace("</", "<\\/")

def parse_coordinates(coords_str: str) -> Optional[Tuple[float, float]]:
    match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", coords_str)
    if match: return float(match.group(1)), float(match.group(2))
    return None

def geocode_location(location_input: str) -> Optional[Tuple[float, float]]:
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={location_input}&format=json&limit=1"
        res = requests.get(url, headers={"User-Agent": OSM_USER_AGENT}, timeout=NOMINATIM_TIMEOUT)
        res.raise_for_status()
        data = res.json()
        if data: return float(data[0]["lat"]), float(data[0]["lon"])
    except: pass
    return None

def compile_features_kml(features: List[Dict[str, Any]]) -> str:
    kml = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scanned POIs</name>'
    for feature in features:
        name = escape_xml(feature.get("name", "Asset"))
        class_type = escape_xml(feature.get("type", "Node"))
        lat, lon = feature.get("lat", 0), feature.get("lon", 0)
        kml += f"<Placemark><name>{name}</name><description>{class_type}</description><Point><coordinates>{lon},{lat},0</coordinates></Point></Placemark>"
    kml += "</Document></kml>"
    return kml

def query_overpass(lat: float, lon: float, radius: int, selected_tags: List[str]) -> List[Dict[str, Any]]:
    if not selected_tags: return []
    statements = "\n".join([f"  nwr[{tag}](around:{radius},{lat},{lon});" for tag in selected_tags])
    query = f"[out:json][timeout:90];\n(\n{statements}\n);\nout center;"
    try:
        response = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, headers={"User-Agent": OSM_USER_AGENT}, timeout=API_TIMEOUT)
        response.raise_for_status()
        records = []
        for element in response.json().get("elements", []):
            lat_val = element.get("lat") or element.get("center", {}).get("lat")
            lon_val = element.get("lon") or element.get("center", {}).get("lon")
            if lat_val and lon_val:
                tags = element.get("tags", {})
                records.append({
                    "lat": lat_val, "lon": lon_val, "name": tags.get("name", "Unknown"),
                    "type": tags.get("amenity") or tags.get("shop") or tags.get("building") or "Node",
                })
        return records
    except: return []

# =====================================================================
# 7. CONTEXT-AWARE SIDEBAR
# =====================================================================
def render_sidebar() -> None:
    with st.sidebar:
        st.markdown('<div class="brand-title">Trade Area Scan</div>', unsafe_allow_html=True)
        run_state_bridge()
        
        # Dynamic Sidebar Layout based on Client-Side State
        if st.session_state.active_module == "SCAN":
            render_sidebar_scan()
        else:
            render_sidebar_editor()

def render_sidebar_scan() -> None:
    location_input = st.text_input("LOCATION SEARCH OR COORDINATES", value=st.session_state.geo_coords, key="geo_coords_input")
    radius_val = st.number_input("RADIUS (METERS)", min_value=100, max_value=50000, value=st.session_state.geo_radius, step=100)
    st.session_state.geo_radius = radius_val

    coords = parse_coordinates(location_input)
    if coords:
        st.session_state.geo_coords = location_input
        lat_coord, lon_coord = coords
    elif location_input and location_input != st.session_state.get("last_geocoded_query", ""):
        with st.spinner("Locating..."):
            geocoded = geocode_location(location_input)
            if geocoded:
                lat_coord, lon_coord = geocoded
                st.session_state.geo_coords = f"{lat_coord:.5f}, {lon_coord:.5f}"
                st.session_state.last_geocoded_query = location_input
                st.rerun()
            else:
                lat_coord, lon_coord = DEFAULT_LAT, DEFAULT_LON
    else:
        lat_coord, lon_coord = parse_coordinates(st.session_state.geo_coords) or (DEFAULT_LAT, DEFAULT_LON)

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    search_query = st.text_input("SEARCH TAGS", placeholder="Search parameters...").lower()
    
    selected_tags = []
    for cat_name, node_items in POI_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for label, tag in matched:
                    if st.checkbox(label, key=f"chk_{cat_name}_{label}"): selected_tags.append(tag)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("SCAN AREA", type="secondary", use_container_width=True):
        if selected_tags:
            with st.spinner("Extracting nodes..."):
                records = query_overpass(lat_coord, lon_coord, radius_val, selected_tags)
                if records:
                    st.session_state.scanned_records = records
                    st.session_state.last_scan_lat = lat_coord
                    st.session_state.last_scan_lon = lon_coord
                    st.rerun()

    if st.button("CLEAR ALL", type="primary", use_container_width=True):
        st.session_state.scanned_records = []
        for key in list(st.session_state.keys()):
            if key.startswith("chk_"): st.session_state[key] = False
        st.rerun()

    st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1: st.download_button("JSON", json.dumps(st.session_state.scanned_records), "scan.json", "application/json", use_container_width=True)
    with col2: st.download_button("KML", compile_features_kml(st.session_state.scanned_records), "POIs.kml", "application/vnd.google-earth.kml+xml", use_container_width=True)

def render_sidebar_editor() -> None:
    st.markdown("<div style='font-size:10px; font-weight:600; color:#888780; text-transform:uppercase; text-align:center; margin-bottom:12px;'>Layer Management</div>", unsafe_allow_html=True)
    new_layer_name = st.text_input("NEW LAYER NAME", placeholder="e.g. Trade Zone A", key="new_layer_name")
    if st.button("ADD LAYER", type="secondary", use_container_width=True):
        if new_layer_name.strip():
            layer_id = f"layer_{len(st.session_state.editor_layers)}_{int(time.time())}"
            st.session_state.editor_layers.append({
                "id": layer_id, "name": new_layer_name.strip(), "visible": True, "color": COLOR_MIDNIGHT,
                "fill_color": COLOR_GOLD, "fill_opacity": 0.4, "weight": 2.0, "icon_shape": "pin", "icon_size": 24,
            })
            st.session_state.active_editor_layer = layer_id
            st.rerun()

    st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>", unsafe_allow_html=True)

    if st.session_state.editor_layers:
        for idx, layer in enumerate(st.session_state.editor_layers):
            with st.expander(f"{layer['name']}", expanded=False):
                layer["visible"] = st.checkbox("Visible", value=layer["visible"], key=f"vis_{layer['id']}")
                col1, col2 = st.columns(2)
                with col1: layer["color"] = st.color_picker("Stroke", layer["color"], key=f"col_{layer['id']}")
                with col2: layer["fill_color"] = st.color_picker("Fill", layer["fill_color"], key=f"fill_{layer['id']}")
                layer["fill_opacity"] = st.slider("Fill Opacity", 0.0, 1.0, layer["fill_opacity"], 0.1, key=f"op_{layer['id']}")
                layer["weight"] = st.slider("Stroke Weight", 0.5, 5.0, layer["weight"], 0.5, key=f"wt_{layer['id']}")
                if st.button("DELETE LAYER", type="primary", use_container_width=True, key=f"del_{layer['id']}"):
                    st.session_state.editor_layers.pop(idx)
                    st.rerun()

        layer_names = [l["name"] for l in st.session_state.editor_layers]
        layer_ids = [l["id"] for l in st.session_state.editor_layers]
        active_idx = layer_ids.index(st.session_state.active_editor_layer) if st.session_state.active_editor_layer in layer_ids else 0
        selected = st.selectbox("DRAW TO LAYER", layer_names, index=active_idx)
        st.session_state.active_editor_layer = layer_ids[layer_names.index(selected)]
    else:
        st.markdown("<div style='font-size:10px; color:#888780; text-align:center; padding:20px 0;'>No layers yet.<br>Add a layer to start drawing.</div>", unsafe_allow_html=True)

# =====================================================================
# 8. UNIFIED LEAFLET ENGINE (NO HARD RELOADS ON TOGGLE)
# =====================================================================
def get_unified_leaflet_template() -> str:
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <link rel="stylesheet" href="https://unpkg.com/@geoman-io/leaflet-geoman-free@latest/dist/leaflet-geoman.css" />
        <script src="https://unpkg.com/@geoman-io/leaflet-geoman-free@latest/dist/leaflet-geoman.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,1,0" rel="stylesheet" />
        <style>
            body, html { margin: 0; padding: 0; height: 100%; width: 100%; overflow: hidden; font-family: 'Montserrat', sans-serif; }
            #map { height: 100vh; width: 100%; z-index: 1; }

            /* Map UI Controls & State Toggle Pill */
            .mode-toggle-container { display: flex; background: #ffffff; border-radius: 30px; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.15); overflow: hidden; border: 2px solid #003366; pointer-events: auto; }
            .mode-toggle-btn { display: flex; align-items: center; gap: 6px; padding: 8px 16px; font-size: 11px; font-weight: 800; font-family: 'Montserrat', sans-serif; color: #003366; cursor: pointer; transition: all 0.3s ease; text-transform: uppercase; letter-spacing: 1px; }
            .mode-toggle-btn.active { background: #003366; color: #C9AB4C; }
            .mode-toggle-btn:not(.active):hover { background: #f8fafc; }
            .mode-toggle-btn span { font-size: 18px; }

            /* Scan Specific Overlays */
            #scan-results-panel { position: absolute; top: 60px; right: 10px; z-index: 1000; background: #ffffff; width: 250px; max-height: calc(100vh - 80px); border-radius: 2px; border: 1px solid rgba(0, 51, 102, 0.1); display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); }
            .results-header { background: #003366; color: #ffffff; padding: 10px 12px; font-size: 10px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; border-bottom: 2px solid #C9AB4C; letter-spacing: 1px; }
            .results-list { overflow-y: auto; flex-grow: 1; padding-bottom: 8px; }
            .layer-category-block { border-bottom: 1px solid #f0f0f0; }
            .layer-category-header { background: #ffffff; padding: 8px 12px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; }
            .layer-header-left { display: flex; align-items: center; gap: 6px; font-size: 9px; font-weight: 700; color: #003366; text-transform: uppercase; }
            .layer-category-items { background: #f8fafc; }
            .layer-category-items.collapsed { display: none !important; }
            .results-item { padding: 6px 12px 6px 28px; font-size: 9px; font-weight: 600; color: #888780; display: flex; justify-content: space-between; align-items: center; cursor: pointer; border-bottom: 1px solid #f0f0f0; }
            .results-item:hover { background: #ffffff; color: #003366; }
            .color-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }

            /* Editor Specific Overlays */
            #layer-panel { position: absolute; top: 60px; right: 10px; z-index: 1000; background: #ffffff; width: 260px; max-height: calc(50vh - 20px); border-radius: 4px; border: 1px solid rgba(0, 51, 102, 0.1); display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 20px rgba(0, 51, 102, 0.15); }
            .layer-panel-header { background: #003366; color: #ffffff; padding: 10px 12px; font-size: 10px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; border-bottom: 2px solid #C9AB4C; letter-spacing: 1px; }
            .layer-list { overflow-y: auto; flex-grow: 1; background: #ffffff; }
            .layer-row { padding: 8px 12px; display: flex; align-items: center; gap: 8px; cursor: pointer; border-bottom: 1px solid #f1f5f9; }
            .layer-row:hover { background: #f8fafc; }
            .layer-row.active { background: #e0e7ff; border-left: 3px solid #003366; }
            .layer-name { font-size: 10px; font-weight: 600; color: #003366; flex-grow: 1; }

            /* Geoman Toolbar Overrides */
            .leaflet-pm-toolbar { display: none; } /* Default Hidden till Edit mode */
            .leaflet-pm-toolbar .leaflet-buttons-control-button { background: #ffffff !important; border-color: rgba(0,51,102,0.15) !important; }
            .leaflet-pm-toolbar .active .leaflet-buttons-control-button { background: #003366 !important; }
            .leaflet-pm-toolbar .active .leaflet-pm-icon { filter: invert(80%) sepia(40%) saturate(500%) hue-rotate(10deg); }
        </style>
    </head>
    <body>
        <div id="map"></div>
        
        <div id="scan-results-panel">
            <div class="results-header"><span>SEARCH RESULTS</span><span id="results-count" style="color:#C9AB4C;">0</span></div>
            <div class="results-list" id="results-list-box"></div>
        </div>
        
        <div id="layer-panel">
            <div class="layer-panel-header"><span>Editor Layers</span><span id="layer-total-count" style="color:#C9AB4C; font-size:9px;">0</span></div>
            <div class="layer-list" id="layer-list-box"></div>
        </div>

        <script>
            // Init Engine
            const map = L.map('map', { zoomControl: true, attributionControl: false }).setView([__LAT__, __LON__], 14);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 }).addTo(map);
            L.circle([__LAT__, __LON__], { radius: __RADIUS__, color: "#003366", weight: 1.5, fillColor: "#003366", fillOpacity: 0.08 }).addTo(map);

            // Floating Pill Architecture
            const modeControl = L.control({position: 'topright'});
            modeControl.onAdd = function () {
                const div = L.DomUtil.create('div', 'mode-toggle-container leaflet-control');
                div.innerHTML = `
                    <div class="mode-toggle-btn active" id="btn-scan" onclick="switchMapMode('SCAN')">
                        <span class="material-symbols-rounded">radar</span> SCAN
                    </div>
                    <div class="mode-toggle-btn" id="btn-edit" onclick="switchMapMode('EDITOR')">
                        <span class="material-symbols-rounded">draw</span> EDIT
                    </div>
                `;
                L.DomEvent.disableClickPropagation(div);
                return div;
            };
            modeControl.addTo(map);

            // Setup Geoman (Hidden init)
            map.pm.addControls({ position: 'topleft', drawMarker: true, drawPolygon: true, drawPolyline: true, drawCircle: true, editMode: true, removalMode: true });
            
            // Client State Variables
            let pts = __GEOJSON__;
            let layerConfigs = __LAYER_CONFIG__;
            let activeLayerId = __ACTIVE_LAYER__;
            let allFeatures = [];
            let featureCounter = 0;

            // ===============================================
            // STATE SYNC BRIDGE (MAP -> STREAMLIT)
            // ===============================================
            function switchMapMode(mode) {
                // Update Local UI
                document.getElementById('btn-scan').classList.toggle('active', mode === 'SCAN');
                document.getElementById('btn-edit').classList.toggle('active', mode === 'EDITOR');
                
                document.querySelector('.leaflet-pm-toolbar').style.display = mode === 'EDITOR' ? 'block' : 'none';
                document.getElementById('scan-results-panel').style.display = mode === 'SCAN' ? 'flex' : 'none';
                document.getElementById('layer-panel').style.display = mode === 'EDITOR' ? 'flex' : 'none';

                // Sync Context to Streamlit Parent 
                const parentDoc = window.parent.document;
                const input = parentDoc.querySelector('input[aria-label="bridge_mode_sync"]');
                if (input && input.value !== mode) {
                    let nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                    nativeSetter.call(input, mode);
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }

            // Sync with Initial Python State cleanly without breaking HTML String diffing
            setTimeout(() => {
                const parentDoc = window.parent.document;
                const activeStateInput = parentDoc.querySelector('input[aria-label="bridge_mode_sync"]');
                if(activeStateInput && activeStateInput.value) { switchMapMode(activeStateInput.value); } 
                else { switchMapMode('SCAN'); }
            }, 100);

            // ===============================================
            // SCAN ENGINE LOGIC
            // ===============================================
            const categoryMap = {};
            const layerGroupsRef = {};
            const catPalette = ["#003366", "#C9AB4C", "#1A5A8A", "#A8862E", "#3D7DA8", "#7A5C10", "#6A94B0", "#D4B85A", "#001F3F", "#E8D494"];
            let colorIndex = 0;

            pts.forEach(p => {
                p._uid = featureCounter++;
                const layerKey = p.type || 'Unclassified';
                if (!categoryMap[layerKey]) { categoryMap[layerKey] = []; categoryColors[layerKey] = catPalette[colorIndex % catPalette.length]; colorIndex++; }
                categoryMap[layerKey].push(p);
            });

            const categoryColors = {}; 
            const createPinIcon = (color) => L.divIcon({ html: `<div style="display:flex;align-items:center;justify-content:center;"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="${color}" stroke="#ffffff" stroke-width="1.5"/></svg></div>`, iconSize: [24, 24], iconAnchor: [12, 24] });

            Object.keys(categoryMap).forEach(key => {
                layerGroupsRef[key] = L.layerGroup().addTo(map);
                categoryMap[key].forEach(p => {
                    const marker = L.marker([p.lat, p.lon], { icon: createPinIcon(categoryColors[key]) }).bindPopup("<b style='color:#003366; font-family:Montserrat;'>" + p.name + "</b><br><span style='color:#888780; font-size:9px;'>" + p.type + "</span>");
                    p._marker = marker; marker.addTo(layerGroupsRef[key]);
                });
            });

            if (pts.length > 0) {
                document.getElementById('results-count').innerText = pts.length;
                let htmlPayload = '';
                Object.keys(categoryMap).forEach(catName => {
                    htmlPayload += `<div class="layer-category-block"><div class="layer-category-header"><div class="layer-header-left"><span class="color-dot" style="background-color: ${categoryColors[catName]};"></span><span>${catName} <span style="color: #C9AB4C; font-size: 8px;">(${categoryMap[catName].length})</span></span></div></div></div>`;
                });
                document.getElementById('results-list-box').innerHTML = htmlPayload;
            }

            // ===============================================
            // EDITOR ENGINE LOGIC
            // ===============================================
            function getLayerConfig(id) { return layerConfigs.find(l => l.id === id) || layerConfigs[0] || {color: '#003366', fill_color: '#C9AB4C', fill_opacity: 0.4, weight: 2.0}; }
            
            function renderLayerPanel() {
                let html = '';
                layerConfigs.forEach(lc => {
                    html += `<div class="layer-row ${lc.id === activeLayerId ? 'active' : ''}"><span class="color-dot" style="background:${lc.color};"></span><span class="layer-name">${lc.name}</span></div>`;
                });
                document.getElementById('layer-list-box').innerHTML = html;
                document.getElementById('layer-total-count').innerText = layerConfigs.length;
            }
            renderLayerPanel();

            map.on('pm:create', function(e) {
                const shape = e.shape; const layer = e.layer; const cfg = getLayerConfig(activeLayerId);
                
                if (shape === 'Circle') {
                    layer.setStyle({ color: cfg.color, fillColor: cfg.fill_color, fillOpacity: cfg.fill_opacity, weight: cfg.weight });
                } else if (shape === 'Polygon' || shape === 'Line' || shape === 'Rectangle') {
                    layer.setStyle({ color: cfg.color, fillColor: cfg.fill_color, fillOpacity: cfg.fill_opacity, weight: cfg.weight });
                } else if (shape === 'Marker') {
                    layer.setIcon(createPinIcon(cfg.color));
                }
                
                allFeatures.push({ layer: layer, featureId: 'drawn_' + featureCounter++, layerId: activeLayerId });
            });
            
            if (pts.length > 0) map.fitBounds(L.featureGroup(pts.map(p => L.marker([p.lat, p.lon]))).getBounds().pad(0.1));
        </script>
    </body>
    </html>
    """

def render_unified_map() -> None:
    """Renders the immutable map string. Prevents hard reloads on state toggle."""
    coords = parse_coordinates(st.session_state.geo_coords)
    lat_coord, lon_coord = coords if coords else (DEFAULT_LAT, DEFAULT_LON)

    # Convert configs to JS arrays
    layer_config = json.dumps(st.session_state.editor_layers)
    active_layer = json.dumps(st.session_state.get("active_editor_layer", ""))
    geojson_escaped = escape_javascript(json.dumps(st.session_state.scanned_records))
    
    # We explicitly exclude st.session_state.active_module from the template.
    # This ensures the hash of the HTML string remains 100% identical when toggling modes.
    template = get_unified_leaflet_template()
    leaflet_html = (
        template.replace("__LAT__", str(lat_coord))
        .replace("__LON__", str(lon_coord))
        .replace("__RADIUS__", str(st.session_state.geo_radius))
        .replace("__GEOJSON__", geojson_escaped)
        .replace("__LAYER_CONFIG__", layer_config)
        .replace("__ACTIVE_LAYER__", active_layer)
    )

    st.components.v1.html(leaflet_html, height=850, scrolling=False)

# =====================================================================
# 9. MAIN APP ENTRY
# =====================================================================
def main() -> None:
    init_session_state()
    apply_global_styles()
    render_sidebar()
    render_unified_map()

if __name__ == "__main__":
    main()
