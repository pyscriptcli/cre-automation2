import streamlit as st
import requests
import re
import json
import os
import time
from datetime import datetime

# --- AUTOMATED LIGHT-MODE THEME LATCH ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\nprimaryColor=\"#003366\"\n")

# --- INITIAL APPLICATION HEADER METADATA ---
st.set_page_config(
    page_title="Open Node AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LUXURY GLASSMORPHISM STYLING OVERRIDES ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,600;1,400&family=Montserrat:wght@400;600;700&display=swap');

        :root {
            --brand-midnight: #003366;
            --brand-gold: #C9AB4C;
            --white-clean: #ffffff;
            --sidebar-bg: rgba(248, 250, 252, 0.92);
        }
        
        /* Full-Screen Canvas Architecture */
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

        /* Floating Panel Controls */
        [data-testid="stSidebar"] {
            position: fixed !important;
            background-color: var(--sidebar-bg) !important;
            backdrop-filter: blur(16px) !important;
            border-right: 1px solid rgba(0, 51, 102, 0.08) !important;
            width: 340px !important;
            box-shadow: 4px 0 30px rgba(0, 31, 63, 0.1) !important;
            z-index: 99999 !important;
        }

        /* Custom UI Micro-Interactions */
        .brand-title {
            font-family: 'Cormorant Garamond', serif !important;
            font-style: italic;
            color: var(--brand-midnight);
            font-size: 36px;
            text-align: center;
            border-bottom: 2px solid var(--brand-gold);
            padding-bottom: 12px;
            margin: 40px 0 20px 0;
        }

        div.stButton > button {
            background-color: var(--brand-midnight) !important;
            color: var(--white-clean) !important;
            border-radius: 6px !important;
            font-weight: 700 !important;
            font-size: 11px !important;
            letter-spacing: 1px;
            text-transform: uppercase;
            transition: all 0.3s ease !important;
        }

        div.stButton > button:hover {
            background-color: var(--brand-gold) !important;
            transform: translateY(-1px);
        }

        /* Clean utilities hidden variables handles */
        [data-testid="stHeader"], header, #stDecoration { display: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- PERSISTENT STATE ARCHITECTURE ---
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'api_logs' not in st.session_state: st.session_state.api_logs = []
if 'map_center' not in st.session_state: st.session_state.map_center = [14.64650, 121.05804]
if 'map_radius' not in st.session_state: st.session_state.map_radius = 1200

def log_pipeline_event(message, level="INFO"):
    t = datetime.now().strftime("%H:%M:%S")
    st.session_state.api_logs.append(f"[{level}] [{t}] {message}")

# --- DICTIONARY DIALECT LOOKUP MATRICES ---
BRAND_REGEX_LOOKUPS = {
    "jollibee": "jollibee|jolibee|jfc",
    "mcdonalds": "mcdonald|mcdo|golden arches",
    "7-eleven": "7-eleven|7/11|711|seven eleven",
    "kfc": "kfc|kentucky fried chicken",
    "starbucks": "starbucks|coffee shop"
}

CATEGORY_TAG_MATRICES = {
    "restaurant": "amenity=restaurant",
    "cafe": "amenity=cafe",
    "pharmacy": "amenity=pharmacy",
    "hospital": "amenity=hospital",
    "gas": "amenity=fuel",
    "supermarket": "shop=supermarket"
}

# --- BULLETPROOF QUERY PARSING GENERATOR ---
def compile_optimized_overpass_ql(lat, lon, radius, raw_query):
    normalized = raw_query.strip().lower()
    log_pipeline_event(f"Compiling optimization schema for '{normalized}'")
    
    clauses = []
    
    # 1. Evaluate Target Value Brand Regex Sequences
    for brand_key, pattern in BRAND_REGEX_LOOKUPS.items():
        if brand_key in normalized or normalized in pattern:
            clauses.append(f'nwr["name"~"{pattern}",i](around:{radius},{lat},{lon});')
            clauses.append(f'nwr["brand"~"{pattern}",i](around:{radius},{lat},{lon});')
            
    # 2. Evaluate Base Infrastructure Functional Tag Keys
    for cat_key, tag_string in CATEGORY_TAG_MATRICES.items():
        if cat_key in normalized:
            clauses.append(f'nwr[{tag_string}](around:{radius},{lat},{lon});')

    # 3. Comprehensive Fallback Safe Vector Clause
    if not clauses:
        escaped_query = re.sub(r'[^a-zA-Z0-9\s]', '', normalized)
        clauses.append(f'nwr["name"~"{escaped_query}",i](around:{radius},{lat},{lon});')
        clauses.append(f'nwr["amenity"~"{escaped_query}",i](around:{radius},{lat},{lon});')

    combined_clauses = "\n  ".join(list(set(clauses)))
    return f'[out:json][timeout:60];\n(\n  {combined_clauses}\n);\nout center;'

# --- GATEWAY OVERPASS CONNECTIONS PIPELINE ---
OVERPASS_GATEWAYS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
]

def dispatch_overpass_pipeline(query_string):
    for gateway in OVERPASS_GATEWAYS:
        try:
            log_pipeline_event(f"Dispatching runtime load to target: {gateway.split('/')[2]}")
            response = requests.post(gateway, data={"data": query_string}, timeout=45)
            if response.status_code == 200:
                elements = response.json().get("elements", [])
                log_pipeline_event(f"Successfully retrieved {len(elements)} raw elements from cluster")
                return elements
        except Exception as e:
            log_pipeline_event(f"Gateway link dropped: {str(e)[:30]}", "WARN")
            continue
    return []

def translate_elements_to_nodes(elements):
    nodes = []
    for index, element in enumerate(elements):
        lat = element.get("lat") or element.get("center", {}).get("lat")
        lon = element.get("lon") or element.get("center", {}).get("lon")
        if lat and lon:
            tags = element.get("tags", {})
            identity = tags.get("name") or tags.get("brand") or tags.get("amenity") or "Asset Feature Node"
            category = tags.get("amenity") or tags.get("shop") or tags.get("building") or "POI Location"
            nodes.append({
                "uid": f"node_{index}_{int(time.time())}",
                "lat": lat, "lon": lon,
                "name": str(identity).replace('"', '\\"'),
                "type": str(category).replace('_', ' ').capitalize()
            })
    return nodes

# --- CONTROL SIDEBAR PANEL LAYER ---
with st.sidebar:
    st.markdown('<div class="brand-title">Open Node AI</div>', unsafe_allow_html=True)
    
    # Coordinates Parser Setup
    coord_input = st.text_input("ANCHOR GPS POINT", value=f"{st.session_state.map_center[0]}, {st.session_state.map_center[1]}")
    parsed_radius = st.number_input("SCAN RADIUS Envelope (m)", min_value=100, max_value=20000, value=st.session_state.map_radius, step=100)
    
    st.markdown("<hr style='margin:12px 0; opacity:0.1;'>", unsafe_allow_html=True)
    search_term = st.text_input("DISCOVERY QUERY FIELD", placeholder="Search e.g. Jollibee, Cafe")
    
    if st.button("RUN SPATIAL ENVELOPE SCAN", use_container_width=True):
        match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", coord_input)
        if match:
            st.session_state.map_center = [float(match.group(1)), float(match.group(2))]
            st.session_state.map_radius = parsed_radius
            
            with st.spinner("Compiling Cluster Payload..."):
                compiled_ql = compile_optimized_overpass_ql(st.session_state.map_center[0], st.session_state.map_center[1], parsed_radius, search_term)
                raw_data = dispatch_overpass_pipeline(compiled_ql)
                st.session_state.scanned_records = translate_elements_to_nodes(raw_data)
            st.rerun()

    # System Logs Panel Widget
    with st.expander("DIAGNOSTICS PAYLOAD LOGS"):
        if st.session_state.api_logs:
            st.code("\n".join(st.session_state.api_logs[-8:]), language="text")
        else:
            st.caption("Engine states are operational.")

# --- LEAFLET GLOBAL ENGINE COMPILER LAYER ---
leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700&display=swap" rel="stylesheet">
    <style>
        body, html, #map { margin: 0; padding: 0; height: 100vh; width: 100vw; background: #fff; font-family: 'Montserrat', sans-serif; }
        .popup-editor { padding: 4px; min-width: 180px; }
        .popup-editor h4 { margin: 0 0 6px 0; color: #003366; font-size: 13px; }
        .popup-editor input { width: 90%; padding: 4px; font-size: 11px; margin-bottom: 6px; border: 1px solid #ccc; border-radius: 4px; }
        .popup-editor button { background: #003366; color: #fff; border: none; padding: 4px 8px; font-size: 10px; font-weight: 700; border-radius: 3px; cursor: pointer; text-transform: uppercase; }
        .popup-editor button:hover { background: #C9AB4C; }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        // Init Base Structural Map
        const map = L.map('map', { zoomControl: false, attributionControl: false }).setView([__LAT__, __LON__], 14);
        L.control.zoom({ position: 'topright' }).addTo(map);

        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 }).addTo(map);

        // Core Editable Radius Envelope Circle Layer
        let analyticalRadiusCircle = L.circle([__LAT__, __LON__], {
            radius: __RADIUS__,
            color: "#003366",
            weight: 2,
            fillColor: "#003366",
            fillOpacity: 0.06
        }).addTo(map);

        // Center Point Vector Marker Pin
        const baseCenterIcon = L.divIcon({
            html: `<div style="background-color: #003366; color:#fff; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:14px; border:2px solid #fff; box-shadow:0 2px 10px rgba(0,0,0,0.3)">★</div>`,
            className: '', iconSize: [28, 28], iconAnchor: [14, 14]
        });
        
        let centerMarker = L.marker([__LAT__, __LON__], { icon: baseCenterIcon, draggable: true }).addTo(map);
        
        // Handle Core Structural Drag Events to Dynamic Readjust Envelope Sizes
        centerMarker.on('dragend', function(e) {
            let newPosition = centerMarker.getLatLng();
            analyticalRadiusCircle.setLatLng(newPosition);
        });

        // Click Logic on Circle to dynamically Adjust Radius Weights
        analyticalRadiusCircle.on('click', function(e) {
            let currentRadius = analyticalRadiusCircle.getRadius();
            let secondaryPromptRadius = prompt("Set new Envelope scan Radius bounds (meters):", currentRadius);
            if (secondaryPromptRadius != null) {
                analyticalRadiusCircle.setRadius(parseInt(secondaryPromptRadius));
            }
        });

        // Processing Runtime Nodes Layer Vectors 
        const featuresDataset = __GEOJSON_PAYLOAD__;
        
        featuresDataset.forEach(node => {
            let itemMarkerIcon = L.divIcon({
                html: `<div style="background-color:#C9AB4C; width:14px; height:14px; border-radius:50%; border:2px solid #fff; box-shadow:0 2px 6px rgba(0,0,0,0.3);"></div>`,
                className: '', iconSize: [14, 14], iconAnchor: [7, 7]
            });

            let mapMarkerInstance = L.marker([node.lat, node.lon], { icon: itemMarkerIcon }).addTo(map);
            
            // Dynamic Interactive HTML Injected Inline Editors
            let interactivePopupFormHtml = `
                <div class="popup-editor">
                    <h4>Edit Node Configuration</h4>
                    <input type="text" id="input_name_${node.uid}" value="${node.name}" placeholder="Label Name"/>
                    <input type="text" id="input_type_${node.uid}" value="${node.type}" placeholder="Type Classification"/>
                    <button onclick="saveNodeOverride('${node.uid}')">Apply Saves</button>
                </div>
            `;
            mapMarkerInstance.bindPopup(interactivePopupFormHtml);
        });

        function saveNodeOverride(nodeUid) {
            let updatedNameVal = document.getElementById(`input_name_${nodeUid}`).value;
            let updatedTypeVal = document.getElementById(`input_type_${nodeUid}`).value;
            alert("Local Node Profile Vector updated:\\nName: " + updatedNameVal + "\\nType: " + updatedTypeVal);
        }

        // Auto framing boundary computations
        if (featuresDataset.length > 0) {
            let trackingMarkersGroup = L.featureGroup(featuresDataset.map(n => L.marker([n.lat, n.lon])));
            map.fitBounds(trackingMarkersGroup.getBounds().pad(0.1));
        }
    </script>
</body>
</html>
"""

# --- INJECTION RUNTIME COMPILER STAGE ---
compiled_html_payload = (leaflet_template
    .replace("__LAT__", str(st.session_state.map_center[0]))
    .replace("__LON__", str(st.session_state.map_center[1]))
    .replace("__RADIUS__", str(st.session_state.map_radius))
    .replace("__GEOJSON_PAYLOAD__", json.dumps(st.session_state.scanned_records)))

# Render full screen canvas out
st.components.v1.html(compiled_html_payload, height=1200, scrolling=False)
