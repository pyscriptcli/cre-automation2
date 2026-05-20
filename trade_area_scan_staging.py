"""
Trade Area Scan - Seamless Zero-API-Limit Architecture
Features: Client-Side Overpass Fetch, Bi-Directional State Memory, Geoman Editor
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import os
import time
import tempfile
import re
from typing import Dict, List, Tuple, Optional

# =====================================================================
# 1. CONSTANTS & CONFIGURATION
# =====================================================================
DEFAULT_LAT = 14.5995
DEFAULT_LON = 120.9842
DEFAULT_COORDS = f"{DEFAULT_LAT}, {DEFAULT_LON}"

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
    if "app_mode" not in st.session_state:
        st.session_state.app_mode = "SCAN"
    if "editor_layers" not in st.session_state:
        st.session_state.editor_layers = []
    if "active_editor_layer" not in st.session_state:
        st.session_state.active_editor_layer = ""
    if "selected_tags" not in st.session_state:
        st.session_state.selected_tags = []

# =====================================================================
# 3. PAGE CONFIG & THEME
# =====================================================================
def setup_light_mode_lock() -> None:
    config_dir = ".streamlit"
    config_file = os.path.join(config_dir, "config.toml")
    if not os.path.exists(config_file):
        os.makedirs(config_dir, exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            f.write("[theme]\nbase=\"light\"\n")

setup_light_mode_lock()
st.set_page_config(page_title="Trade Area Scan", layout="wide", initial_sidebar_state="expanded")

def apply_global_styles() -> None:
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Montserrat:wght@400;500;600;700;800&display=swap');
        
        :root {{
            --brand-midnight: {COLOR_MIDNIGHT} !important;
            --brand-gold: {COLOR_GOLD} !important;
            --white-clean: {COLOR_WHITE} !important;
            --bg-offwhite: {COLOR_BG_LIGHT} !important;
            --text-muted: {COLOR_TEXT_MUTED} !important;
        }}
        
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
            background-color: var(--white-clean) !important;
            color: var(--brand-midnight) !important;
            font-family: 'Montserrat', sans-serif !important;
        }}
        
        [data-testid="stSidebar"] {{
            background-color: var(--bg-offwhite) !important;
            color: var(--brand-midnight) !important;
            border-right: 1px solid rgba(0, 51, 102, 0.08) !important;
            width: 300px !important; min-width: 300px !important; max-width: 300px !important;
            box-shadow: 2px 0 15px rgba(0,0,0,0.03) !important;
        }}
        
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] {{ display: none !important; }}
        ::-webkit-scrollbar {{ width: 0px !important; background: transparent !important; }}
        
        [data-testid="stHeader"], footer, .stDeployButton {{ display: none !important; }}
        
        [data-testid="stAppViewContainer"] {{ flex-direction: row !important; height: 100vh !important; overflow: hidden !important; }}
        [data-testid="stMain"] {{ width: calc(100vw - 300px) !important; height: 100vh !important; overflow: hidden !important; padding: 0 !important; }}
        .block-container {{ padding: 0px !important; max-width: 100% !important; }}
        iframe {{ height: 100vh !important; width: 100% !important; border: none !important; display: block !important; }}
        
        div[data-baseweb="input"] {{ border: none !important; border-bottom: 1px solid rgba(201, 171, 76, 0.5) !important; border-radius: 0px !important; background: transparent !important; }}
        div[data-baseweb="input"]:focus-within {{ border-bottom: 2px solid var(--brand-gold) !important; }}
        
        div.stButton > button[kind="secondary"] {{ 
            background-color: var(--brand-midnight) !important; border: 1px solid var(--brand-midnight) !important; 
            border-radius: 2px !important; width: 100% !important; padding: 6px !important; transition: all 0.3s ease !important; 
        }}
        div.stButton > button[kind="secondary"]:hover {{ background-color: var(--brand-gold) !important; border-color: var(--brand-gold) !important; }}
        div.stButton > button[kind="secondary"] p {{ color: var(--white-clean) !important; font-weight: 700 !important; font-size: 9px !important; text-transform: uppercase !important; letter-spacing: 1px; }}
        
        [data-testid="stSidebar"] .st-expander {{ border: 1px solid rgba(0, 51, 102, 0.05) !important; background-color: var(--white-clean) !important; border-radius: 2px !important; margin-bottom: 2px !important; }}
        [data-testid="stSidebar"] .st-expander summary p {{ font-size: 9px !important; font-weight: 500 !important; color: var(--brand-midnight) !important; }}
        .stCheckbox label p {{ font-size: 10px !important; font-weight: 500 !important; color: var(--brand-midnight) !important; }}
        
        .brand-title {{ font-family: 'Cormorant Garamond', serif !important; font-style: italic; color: var(--brand-midnight); font-size: 28px; text-align: center; border-bottom: 1px solid var(--brand-gold); padding-bottom: 6px; margin-bottom: 20px; }}
    </style>
    """, unsafe_allow_html=True)

# =====================================================================
# 4. CONFIGURATIONS
# =====================================================================
POI_CONFIG: Dict[str, List[List[str]]] = {
    "COMMERCIAL": [["Corporate Office", '"building"~"office|commercial",i'], ["IT/Tech Center", '"office"~"it|telecommunication",i'], ["Hospital", '"amenity"~"hospital|clinic",i']],
    "RESIDENTIAL": [["Apartments", '"building"="apartments"'], ["House", '"building"="house"'], ["Condominium", '"building"="residential"']],
    "RETAIL": [["Mall/Department Store", '"shop"~"mall|department_store",i'], ["Supermarket", '"shop"~"supermarket|grocery",i'], ["Convenience Store", '"shop"="convenience"'], ["Pharmacy", '"amenity"="pharmacy"'], ["General Shops", '"shop"~"boutique|clothes|shoes",i']],
    "FOOD & BEVERAGE": [["Restaurant", '"amenity"="restaurant"'], ["Cafe/Coffee Shop", '"amenity"~"cafe|coffee",i'], ["Fast Food", '"amenity"="fast_food"'], ["Bar/Pub", '"amenity"~"bar|pub",i']]
}

def parse_coordinates(coords_str: str) -> Optional[Tuple[float, float]]:
    match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", coords_str)
    return (float(match.group(1)), float(match.group(2))) if match else None

# =====================================================================
# 5. JAVASCRIPT/LEAFLET BRIDGE ARCHITECTURE
# =====================================================================
def generate_map_html() -> str:
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <link rel="stylesheet" href="https://unpkg.com/@geoman-io/leaflet-geoman-free@latest/dist/leaflet-geoman.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script src="https://unpkg.com/@geoman-io/leaflet-geoman-free@latest/dist/leaflet-geoman.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/streamlit-component-lib@1.3.0/dist/streamlit.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap" rel="stylesheet">
        <style>
            body, html { margin: 0; padding: 0; height: 100vh; width: 100vw; overflow: hidden; font-family: 'Montserrat', sans-serif; }
            #map { height: 100%; width: 100%; }
            
            #loader-overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(255,255,255,0.4); z-index: 9999; display: none; backdrop-filter: blur(2px); }
            #loader-box { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: #003366; color: #C9AB4C; padding: 15px 30px; border-radius: 4px; font-weight: 700; font-size: 11px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); border: 1px solid #C9AB4C; display: flex; align-items: center; gap: 10px; text-transform: uppercase; letter-spacing: 1px; }
            .spinner { width: 16px; height: 16px; border: 2px solid #C9AB4C; border-top-color: transparent; border-radius: 50%; animation: spin 1s linear infinite; }
            @keyframes spin { 100% { transform: rotate(360deg); } }

            .custom-editor-toggle { background: #fff; border: 2px solid rgba(0,0,0,0.2); border-radius: 4px; overflow: hidden; cursor: pointer; }
            .custom-editor-toggle a { color: #003366 !important; padding: 8px 12px !important; display: block; text-decoration: none; font-weight: 800; font-size: 11px; }
            .custom-editor-toggle a:hover { background: #f8fafc; }
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div id="loader-overlay"><div id="loader-box"><div class="spinner"></div><span>Analyzing Spatial Cells via API...</span></div></div>
        
        <script>
            let map;
            let poiLayer;
            let currentMode = 'SCAN';
            let activeTags = [];
            
            function initMap(lat, lon) {
                map = L.map('map', { zoomControl: false }).setView([lat, lon], 14);
                L.control.zoom({ position: 'topright' }).addTo(map);
                L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(map);
                
                poiLayer = L.featureGroup().addTo(map);
                
                // Editor Toggle Control
                L.Control.EditorToggle = L.Control.extend({
                    onAdd: function(map) {
                        let div = L.DomUtil.create('div', 'leaflet-bar leaflet-control custom-editor-toggle');
                        div.innerHTML = `<a id="toggle-btn" href="#">⚙ EDIT FEATURES / BOUNDARIES</a>`;
                        div.onclick = function(e) {
                            e.preventDefault();
                            currentMode = currentMode === 'SCAN' ? 'EDIT' : 'SCAN';
                            applyModeState();
                            
                            // Send state back to Streamlit to update the sidebar
                            Streamlit.setComponentValue({ mode: currentMode });
                        };
                        return div;
                    }
                });
                new L.Control.EditorToggle({ position: 'topleft' }).addTo(map);

                // Auto-fetch within bounded box drawing
                map.on('pm:create', function(e) {
                    if ((e.shape === 'Rectangle' || e.shape === 'Polygon') && activeTags.length > 0) {
                        executeOverpassQuery(activeTags, e.layer.getBounds());
                    }
                });
            }

            function applyModeState() {
                const btn = document.getElementById('toggle-btn');
                if (currentMode === 'EDIT') {
                    map.pm.addControls({ position: 'topleft', drawMarker: true, drawPolygon: true, drawRectangle: true, editMode: true, removalMode: true });
                    btn.innerText = "✓ EXIT EDIT MODE";
                    btn.style.color = "#C9AB4C";
                    btn.style.background = "#003366";
                } else {
                    map.pm.removeControls();
                    btn.innerText = "⚙ EDIT FEATURES / BOUNDARIES";
                    btn.style.color = "#003366";
                    btn.style.background = "#ffffff";
                }
            }

            async function executeOverpassQuery(tags, bounds = null) {
                document.getElementById('loader-overlay').style.display = 'block';
                
                if (!bounds) bounds = map.getBounds();
                const s = bounds.getSouth(), w = bounds.getWest(), n = bounds.getNorth(), e = bounds.getEast();
                const bbox = `${s},${w},${n},${e}`;
                
                const stmts = tags.map(t => `nwr[${t}](${bbox});`).join('\\n');
                const query = `[out:json][timeout:25];\\n(\\n${stmts}\\n);\\nout center;`;
                
                try {
                    const res = await fetch('https://overpass-api.de/api/interpreter', {
                        method: 'POST',
                        body: "data=" + encodeURIComponent(query)
                    });
                    const data = await res.json();
                    
                    poiLayer.clearLayers();
                    
                    data.elements.forEach(el => {
                        const lat = el.lat || (el.center && el.center.lat);
                        const lon = el.lon || (el.center && el.center.lon);
                        if (lat && lon) {
                            const marker = L.circleMarker([lat, lon], { radius: 6, color: '#003366', weight: 1.5, fillColor: '#C9AB4C', fillOpacity: 0.8 });
                            marker.bindPopup(`<b style="color:#003366;font-family:Montserrat;">${el.tags?.name || 'Asset'}</b><br/><span style="font-size:9px;color:#888780;">${el.tags?.amenity || el.tags?.shop || el.tags?.building || 'Node'}</span>`);
                            poiLayer.addLayer(marker);
                        }
                    });
                } catch(err) {
                    console.error("Overpass API Error:", err);
                } finally {
                    document.getElementById('loader-overlay').style.display = 'none';
                }
            }

            function onRender(event) {
                const data = event.detail.args;
                
                if (!window.mapInitialized) {
                    const [lat, lon] = data.coords.split(',').map(Number);
                    initMap(lat, lon);
                    window.mapInitialized = true;
                    
                    if (data.mode) {
                        currentMode = data.mode;
                        applyModeState();
                    }
                }
                
                // Track selected POI tags sent from Python Sidebar
                const newTags = data.tags || [];
                if (JSON.stringify(newTags) !== JSON.stringify(activeTags)) {
                    activeTags = newTags;
                    if (activeTags.length > 0) {
                        executeOverpassQuery(activeTags);
                    } else {
                        poiLayer.clearLayers();
                    }
                }
                
                Streamlit.setFrameHeight(window.innerHeight);
            }

            Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
            Streamlit.setComponentReady();
        </script>
    </body>
    </html>
    """

@st.cache_resource
def get_map_component():
    """Generates the bidirectional HTML component in a temporary directory to maintain state memory."""
    temp_dir = os.path.join(tempfile.gettempdir(), "trade_area_unified_map")
    os.makedirs(temp_dir, exist_ok=True)
    html_path = os.path.join(temp_dir, "index.html")
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(generate_map_html())
        
    return components.declare_component("trade_area_map", path=temp_dir)

# =====================================================================
# 6. SIDEBAR CONTROLS
# =====================================================================
def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="brand-title">Trade Area Scan</div>', unsafe_allow_html=True)
        
        if st.session_state.app_mode == "SCAN":
            st.text_input("COORDINATES", value=st.session_state.geo_coords, key="geo_coords_input")
            
            st.markdown("<div style='font-weight: 700; font-size: 11px; margin-top: 15px; margin-bottom: 8px; color: #003366; letter-spacing: 1px;'>POI CLASSIFICATION</div>", unsafe_allow_html=True)
            
            selected_tags = []
            for cat_name, node_items in POI_CONFIG.items():
                with st.expander(cat_name, expanded=False):
                    for label, tag in node_items:
                        if st.checkbox(label, key=f"chk_{label}"):
                            selected_tags.append(tag)
            
            # Automatically push state changes to trigger JS
            st.session_state.selected_tags = selected_tags
            
        elif st.session_state.app_mode == "EDIT":
            st.markdown("<div style='font-weight: 700; font-size: 11px; margin-top: 15px; margin-bottom: 8px; color: #003366; letter-spacing: 1px;'>LAYER MANAGEMENT</div>", unsafe_allow_html=True)
            
            new_layer_name = st.text_input("NEW LAYER NAME", placeholder="e.g. Trade Zone A")
            if st.button("ADD LAYER", type="secondary", use_container_width=True):
                if new_layer_name.strip():
                    layer_id = f"layer_{len(st.session_state.editor_layers)}_{int(time.time())}"
                    st.session_state.editor_layers.append({
                        "id": layer_id, "name": new_layer_name.strip(), "color": COLOR_MIDNIGHT, "fill_color": COLOR_GOLD
                    })
                    st.session_state.active_editor_layer = layer_id
                    st.rerun()

            if st.session_state.editor_layers:
                st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>", unsafe_allow_html=True)
                for layer in st.session_state.editor_layers:
                    with st.expander(f"{layer['name']}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1: layer["color"] = st.color_picker("Stroke", layer["color"], key=f"col_{layer['id']}")
                        with col2: layer["fill_color"] = st.color_picker("Fill", layer["fill_color"], key=f"fill_{layer['id']}")

# =====================================================================
# 7. MAIN EXECUTION
# =====================================================================
def main():
    init_session_state()
    apply_global_styles()
    render_sidebar()
    
    MapComponent = get_map_component()
    map_state = MapComponent(
        coords=st.session_state.geo_coords,
        tags=st.session_state.selected_tags,
        mode=st.session_state.app_mode,
        key="unified_map_instance"
    )
    
    # Bi-Directional State Capture: If JS clicks "EDIT FEATURES", update Python sidebar UI
    if map_state and isinstance(map_state, dict):
        new_mode = map_state.get("mode")
        if new_mode and new_mode != st.session_state.app_mode:
            st.session_state.app_mode = new_mode
            st.rerun()

if __name__ == "__main__":
    main()
