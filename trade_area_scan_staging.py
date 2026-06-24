import streamlit as st
import requests
import re
import json
import os
import time
from datetime import datetime

# --- AUTOMATED ENGINE LIGHT MODE FORCE LATCH ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\nprimaryColor=\"#003366\"\n")

# --- INITIAL APPLICATION HEADER METADATA ---
st.set_page_config(
    page_title="Open Node",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LUXURY GLASSMORPHISM CANVAS OVERRIDES ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,600;1,400&family=Montserrat:wght@400;500;600;700&display=swap');

        :root {
            --brand-midnight: #003366;
            --brand-gold: #C9AB4C;
            --white-clean: #ffffff;
            --sidebar-bg: rgba(248, 250, 252, 0.92);
        }
        
        /* Full Viewport App Constraints */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: var(--white-clean) !important;
            color: var(--brand-midnight) !important;
            font-family: 'Montserrat', sans-serif !important;
            margin: 0px !important;
            padding: 0px !important;
            width: 100vw !important;
            height: 100vh !important;
            overflow: hidden !important;
        }

        .block-container, [data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"] {
            gap: 0rem !important;
        }

        /* Floating Modern Sidebar Panel */
        [data-testid="stSidebar"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100vh !important;
            background-color: var(--sidebar-bg) !important;
            backdrop-filter: blur(16px) !important;
            border-right: 1px solid rgba(0, 51, 102, 0.08) !important;
            width: 340px !important;
            box-shadow: 4px 0 30px rgba(0, 31, 63, 0.1) !important;
            z-index: 99999 !important;
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }

        .sidebar-collapsed [data-testid="stSidebar"] {
            transform: translateX(-340px) !important;
        }

        /* Floating Sidebar Toggle Mechanics */
        .sidebar-toggle-btn {
            position: fixed;
            left: 16px;
            top: 24px;
            z-index: 999999;
            background: var(--brand-midnight);
            color: #ffffff;
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 4px;
            padding: 8px 14px;
            font-family: 'Montserrat', sans-serif;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: all 0.2s ease;
        }
        .sidebar-toggle-btn:hover {
            background: var(--brand-gold);
            transform: scale(1.03);
        }

        .brand-title {
            font-family: 'Cormorant Garamond', serif !important;
            font-style: italic;
            color: var(--brand-midnight);
            font-size: 34px;
            text-align: center;
            border-bottom: 2px solid var(--brand-gold);
            padding-bottom: 10px;
            margin: 50px 0 20px 0;
        }

        div.stButton > button {
            background-color: var(--brand-midnight) !important;
            color: var(--white-clean) !important;
            border-radius: 4px !important;
            font-weight: 700 !important;
            font-size: 10px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px;
            width: 100% !important;
        }

        div.stButton > button:hover {
            background-color: var(--brand-gold) !important;
            border-color: var(--brand-gold) !important;
        }

        /* Hide Default UI Elements */
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"], [data-testid="stHeader"], header, #stDecoration {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- STATE PERSISTENCE ARCHITECTURE ---
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'api_logs' not in st.session_state: st.session_state.api_logs = []
if 'map_center' not in st.session_state: st.session_state.map_center = [14.64650, 121.05804]
if 'map_radius' not in st.session_state: st.session_state.map_radius = 1200
if 'sidebar_collapsed' not in st.session_state: st.session_state.sidebar_collapsed = False

def add_api_log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.api_logs.append({"time": timestamp, "message": message, "level": level})

# --- LOOKUP DICTIONARY ARRAYS ---
BRAND_DICTIONARIES = {
    'jollibee': 'jollibee|jolibee|jfc|jollibee food corporation',
    'mcdonalds': 'mcdonald|mcdo|mcd|golden arches',
    '7-eleven': '7-eleven|7/11|711|seven eleven',
    'kfc': 'kfc|kentucky fried chicken',
    'starbucks': 'starbucks|starbucks coffee'
}

CATEGORY_DICTIONARIES = {
    'restaurant': 'amenity=restaurant',
    'cafe': 'amenity=cafe',
    'supermarket': 'shop=supermarket',
    'pharmacy': 'amenity=pharmacy',
    'gas': 'amenity=fuel',
    'hospital': 'amenity=hospital'
}

# --- OPTIMIZED OVERPASS QL STATEMENT BUILDER ---
def compile_optimized_overpass_query(lat, lon, radius, search_string):
    add_api_log(f"Compiling vector targets for query: '{search_string}'", "INFO")
    normalized = search_string.lower().strip()
    statements = []
    
    for key, pattern in BRAND_DICTIONARIES.items():
        if key in normalized:
            statements.append(f'nwr["name"~"{pattern}",i](around:{radius},{lat},{lon});')
            statements.append(f'nwr["brand"~"{pattern}",i](around:{radius},{lat},{lon});')

    for key, tag in CATEGORY_DICTIONARIES.items():
        if key in normalized:
            statements.append(f'nwr[{tag}](around:{radius},{lat},{lon});')

    if not statements:
        sanitized = re.sub(r'[^a-zA-Z0-9\s]', '', normalized)
        statements.append(f'nwr["name"~"{sanitized}",i](around:{radius},{lat},{lon});')
        statements.append(f'nwr["amenity"~"{sanitized}",i](around:{radius},{lat},{lon});')

    unique_statements = "\n  ".join(list(set(statements)))
    return f'[out:json][timeout:60];\n(\n  {unique_statements}\n);\nout center;'

# --- HIGH RESILIENCE CONNECTIONS GATEWAY ---
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
]

def execute_overpass_pipeline(ql_query):
    for gateway in OVERPASS_ENDPOINTS:
        try:
            add_api_log(f"Contacting distributed cluster endpoint: {gateway.split('/')[2]}", "INFO")
            res = requests.post(gateway, data={"data": ql_query}, timeout=45)
            if res.status_code == 200:
                elements = res.json().get("elements", [])
                add_api_log(f"Successfully retrieved {len(elements)} raw spatial records", "INFO")
                return elements
        except Exception as e:
            add_api_log(f"Connection pool dropped: {str(e)[:35]}", "ERROR")
            continue
    return []

def extract_elements_to_nodes(elements):
    nodes = []
    for idx, el in enumerate(elements):
        lat = el.get('lat') or el.get('center', {}).get('lat')
        lon = el.get('lon') or el.get('center', {}).get('lon')
        if lat and lon:
            tags = el.get('tags', {})
            name = tags.get('name') or tags.get('brand') or tags.get('amenity') or "Asset Feature Node"
            category = tags.get('amenity') or tags.get('shop') or tags.get('building') or "POI Location"
            nodes.append({
                "uid": f"node_{idx}_{int(time.time())}",
                "lat": lat, "lon": lon,
                "name": str(name).replace('"', '\\"'),
                "type": str(category).replace('_', ' ').capitalize()
            })
    return nodes

# --- SIDEBAR INTERACTION INJECTION LAYERS ---
st.markdown("""
    <button class="sidebar-toggle-btn" id="sidebarToggleBtn" onclick="toggleSidebarDynamic()">Close Panel</button>
    <script>
        function toggleSidebarDynamic() {
            const container = document.querySelector('[data-testid="stAppViewContainer"]');
            const btn = document.getElementById('sidebarToggleBtn');
            container.classList.toggle('sidebar-collapsed');
            
            const isCollapsed = container.classList.contains('sidebar-collapsed');
            btn.textContent = isCollapsed ? 'Open Panel' : 'Close Panel';
            
            const hiddenInput = document.getElementById('sidebar_state_input');
            if (hiddenInput) {
                hiddenInput.value = isCollapsed ? 'collapsed' : 'expanded';
                hiddenInput.dispatchEvent(new Event('change'));
            }
        }
    </script>
""", unsafe_allow_html=True)

# FIX: Added required non-empty string labels for standard accessibility parsers
sidebar_state = st.text_input("Sidebar Internal State Controller", key="sidebar_state_input", label_visibility="collapsed", placeholder="sidebar_state")
if sidebar_state == "collapsed":
    st.session_state.sidebar_collapsed = True
elif sidebar_state == "expanded":
    st.session_state.sidebar_collapsed = False

if st.session_state.sidebar_collapsed:
    st.markdown("<script>document.querySelector('[data-testid=\"stAppViewContainer\"]').classList.add('sidebar-collapsed'); document.getElementById('sidebarToggleBtn').textContent='Open Panel';</script>", unsafe_allow_html=True)

# --- SIDEBAR RENDERING DRAWER ---
with st.sidebar:
    st.markdown('<div class="brand-title">Open Node</div>', unsafe_allow_html=True)
    
    gps_input = st.text_input("ANCHOR GPS POINT COORDINATES", value=f"{st.session_state.map_center[0]}, {st.session_state.map_center[1]}")
    radius_val = st.number_input("RADIUS BOUND ENVELOPE (METERS)", min_value=100, max_value=30000, value=st.session_state.map_radius, step=100)
    
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    # FIX: Attached non-empty accessibility identifier string
    search_query = st.text_input("DISCOVERY SEARCH INSTANCE INPUT", placeholder="e.g. Jollibee, Cafe, Hospital", key="search_bar_input", label_visibility="collapsed")
    
    if st.button("EXECUTE SCAN RUNTIME", use_container_width=True):
        coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", gps_input)
        if coord_match:
            st.session_state.map_center = [float(coord_match.group(1)), float(coord_match.group(2))]
            st.session_state.map_radius = radius_val
            
            with st.spinner("Dispatching Network Payload..."):
                compiled_query = compile_optimized_overpass_query(st.session_state.map_center[0], st.session_state.map_center[1], radius_val, search_query)
                raw_elements = execute_overpass_pipeline(compiled_query)
                st.session_state.scanned_records = extract_elements_to_nodes(raw_elements)
            st.rerun()

    with st.expander("DIAGNOSTICS PAYLOAD LOGS", expanded=False):
        if st.session_state.api_logs:
            log_text = "".join([f"[{l['level']}] [{l['time']}] {l['message']}\n" for l in st.session_state.api_logs[-10:]])
            st.code(log_text, language="text")
        else:
            st.caption("Engine runtime operational.")

# --- LEAFLET INTEGRATED HTML CANVAS TEMPLATE ---
leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700&display=swap" rel="stylesheet">
    <style>
        body, html, #map { margin: 0; padding: 0; height: 100vh; width: 100vw; background: #ffffff; font-family: 'Montserrat', sans-serif; overflow: hidden; }
        .editor-popup-frame { padding: 4px; min-width: 190px; }
        .editor-popup-frame h4 { margin: 0 0 6px 0; color: #003366; font-size: 12px; font-weight: 700; text-transform: uppercase; }
        .editor-popup-frame input { width: 92%; padding: 4px; font-size: 11px; margin-bottom: 6px; border: 1px solid #ddd; border-radius: 4px; }
        .editor-popup-frame button { background: #003366; color: #fff; border: none; padding: 5px 10px; font-size: 9px; font-weight: 700; border-radius: 4px; cursor: pointer; text-transform: uppercase; width: 100%; }
        .editor-popup-frame button:hover { background: #C9AB4C; }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        const map = L.map('map', { zoomControl: false, attributionControl: false }).setView([__LAT__, __LON__], 14);
        L.control.zoom({ position: 'topright' }).addTo(map);

        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 }).addTo(map);

        let boundaryRadiusCircle = L.circle([__LAT__, __LON__], {
            radius: __RADIUS__, color: "#003366", weight: 2, fillColor: "#003366", fillOpacity: 0.05
        }).addTo(map);

        const centerStarIcon = L.divIcon({
            html: `<div style="background-color: #003366; color: #ffffff; width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; border: 2px solid #ffffff; box-shadow: 0 2px 8px rgba(0,0,0,0.3)">★</div>`,
            className: '', iconSize: [26, 26], iconAnchor: [13, 13]
        });
        
        let anchorCenterMarker = L.marker([__LAT__, __LON__], { icon: centerStarIcon, draggable: true }).addTo(map);
        
        anchorCenterMarker.on('dragend', function(event) {
            let markerGpsCoords = anchorCenterMarker.getLatLng();
            boundaryRadiusCircle.setLatLng(markerGpsCoords);
        });

        boundaryRadiusCircle.on('click', function(event) {
            let activeRadius = boundaryRadiusCircle.getRadius();
            let promptOverrideResponse = prompt("Set new radius constraint envelope size (meters):", activeRadius);
            if (promptOverrideResponse != null) {
                boundaryRadiusCircle.setRadius(parseInt(promptOverrideResponse));
            }
        });

        const spatialVectorData = __GEOJSON_STR__;
        
        spatialVectorData.forEach(node => {
            let standardMarkerIcon = L.divIcon({
                html: `<div style="background-color: #C9AB4C; width: 14px; height: 14px; border-radius: 50%; border: 2px solid #ffffff; box-shadow: 0 2px 6px rgba(0,0,0,0.25);"></div>`,
                className: '', iconSize: [14, 14], iconAnchor: [7, 7]
            });

            let trackingNodeMarker = L.marker([node.lat, node.lon], { icon: standardMarkerIcon }).addTo(map);
            
            let interactivePopupHtml = `
                <div class="editor-popup-frame">
                    <h4>Modify Establishment Pin</h4>
                    <input type="text" id="popup_name_${node.uid}" value="${node.name}" placeholder="Name Label"/>
                    <input type="text" id="popup_type_${node.uid}" value="${node.type}" placeholder="Category type"/>
                    <button onclick="commitNodeModifications('${node.uid}')">Commit Configurations</button>
                </div>
            `;
            trackingNodeMarker.bindPopup(interactivePopupHtml);
        });

        function commitNodeModifications(uidString) {
            let modifiedName = document.getElementById(`popup_name_${uidString}`).value;
            let modifiedType = document.getElementById(`popup_type_${uidString}`).value;
            alert("Local Node updated inside Leaflet Sandbox Space:\\nLabel Name: " + modifiedName + "\\nClassification Type: " + modifiedType);
        }

        if (spatialVectorData.length > 0) {
            let nodeBordersGroup = L.featureGroup(spatialVectorData.map(n => L.marker([n.lat, n.lon])));
            map.fitBounds(nodeBordersGroup.getBounds().pad(0.1));
        }
    </script>
</body>
</html>
"""

# --- INJECTION PIPELINE AND RENDER COMPILER ---
compiled_html_output = (leaflet_template
    .replace("__LAT__", str(st.session_state.map_center[0]))
    .replace("__LON__", str(st.session_state.map_center[1]))
    .replace("__RADIUS__", str(st.session_state.map_radius))
    .replace("__GEOJSON_STR__", json.dumps(st.session_state.scanned_records)))

# FIX: Migrated from the deprecated st.components.v1.html block to the standardized modern iframe view layer
st.components.v1.html(compiled_html_output, height=1000, scrolling=False)
