import streamlit as st
import requests
import re
import math
import json

# -----------------------------------------------------------------------------
# 1. THEME VARIABLES INITIALIZATION & CONFIGURATION
# -----------------------------------------------------------------------------
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# EXTRACT CURRENT THEME MONOCHROME VECTOR STATE
if st.session_state.dark_mode:
    bg_color = "#001a3d"
    text_color = "#ffffff"
    border_color = "#ffffff"
    contrast_bg = "#ffffff"
    contrast_text = "#001a3d"
else:
    bg_color = "#ffffff"
    text_color = "#001a3d"
    border_color = "#001a3d"
    contrast_bg = "#001a3d"
    contrast_text = "#ffffff"

st.set_page_config(
    page_title="TRADE AREA SCAN",
    layout="wide",
    initial_sidebar_state="expanded"
)

# BRUTE FORCE COMPONENT INJECTION FOR FLAT MULTI-MODE OVERRIDES
st.markdown(f"""
    <style>
        :root {{
            --bg-main: {bg_color};
            --text-main: {text_color};
            --border-main: {border_color};
            --contrast-bg: {contrast_bg};
            --contrast-text: {contrast_text};
        }}
        
        /* THEME LOCK ACROSS STREAMLIT CONCRETE ELEMENTS */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {{
            background-color: var(--bg-main) !important;
            color: var(--text-main) !important;
            color-scheme: {"dark" if st.session_state.dark_mode else "light"} !important;
        }}
        
        p, span, label, h1, h2, h3, h4, h5, h6, .stMarkdown, [data-testid="stExpander"] summary p {{
            color: var(--text-main) !important;
        }}
        
        /* ELIMINATE STREAMLIT CONTROL CORES */
        [data-testid="stHeader"], header, #stDecoration {{
            height: 0px !important;
            min-height: 0px !important;
            display: none !important;
        }}
        
        /* FORCE SIDEBAR STYLING - ABSOLUTE SCROLLBAR REMOVAL */
        [data-testid="stSidebar"] {{
            background-color: var(--bg-main) !important;
            color: var(--text-main) !important;
            border-right: 1px solid var(--border-main) !important;
            width: 320px !important;
            min-width: 320px !important;
            max-width: 320px !important;
            transform: none !important;
            visibility: visible !important;
            overflow: hidden !important;
            scrollbar-width: none !important;
        }}
        [data-testid="stSidebar"]::-webkit-scrollbar {{
            display: none !important;
        }}
        [data-testid="stSidebarUserContent"] {{
            padding-top: 16px !important;
            padding-left: 12px !important;
            padding-right: 12px !important;
            height: 100vh !important;
            display: flex !important;
            flex-direction: column !important;
            overflow: hidden !important;
        }}
        
        /* STRIP EXPANDER CHEVRON ARROWS AND SYMBOLS COMPLETELY */
        div[data-testid="stExpander"] details summary svg {{
            display: none !important;
        }}
        div[data-testid="stExpander"] details summary {{
            list-style: none !important;
            list-style-type: none !important;
        }}
        div[data-testid="stExpander"] details summary::-webkit-details-marker {{
            display: none !important;
        }}
        [data-testid="stExpander"] {{
            border: 1px solid var(--border-main) !important;
            background-color: var(--bg-main) !important;
            border-radius: 0px !important;
            margin-bottom: 4px !important;
        }}

        /* FIXED FLAT BUTTON CONTROLS */
        button, .stDownloadButton > button {{
            background-color: var(--contrast-bg) !important;
            color: var(--contrast-text) !important;
            border: 1px solid var(--border-main) !important;
            border-radius: 0px !important;
            font-size: 10px !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            width: 100% !important;
            padding: 4px !important;
        }}
        
        button[kind="tertiary"] {{
            background: transparent !important;
            color: var(--text-main) !important;
            text-decoration: underline !important;
            border: none !important;
        }}

        /* MINIFY NATIVE FILE UPLOADER DESIGN FOR SIDEBAR CORNER LAYOUTS */
        div[data-testid="stFileUploader"] section {{
            padding: 4px !important;
            border: 1px dashed var(--border-main) !important;
            background: transparent !important;
        }}
        div[data-testid="stFileUploader"] label, div[data-testid="stFileUploader"] small {{
            display: none !important;
        }}

        [data-testid="stAppViewBlockContainer"] {{
            padding: 0rem !important;
            margin: 0px !important;
            width: 100% !important;
            height: 100vh !important;
        }}
        iframe {{
            height: 100vh !important;
            width: 100% !important;
            border: none !important;
            display: block !important;
        }}
        .stDeployButton, footer {{ display:none !important; }}
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. STATE PERSISTENCE & DATA MODELS
# -----------------------------------------------------------------------------
DEFAULT_COORDS = "14.6465, 121.0371"
DEFAULT_RADIUS = 1000

if 'geo_coords' not in st.session_state: st.session_state.geo_coords = DEFAULT_COORDS
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = DEFAULT_RADIUS
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'last_scan_lat' not in st.session_state: st.session_state.last_scan_lat = 14.6465
if 'last_scan_lon' not in st.session_state: st.session_state.last_scan_lon = 121.0371
if 'map_styles' not in st.session_state:
    st.session_state.map_styles = {
        "pin_color": "#001a3d",
        "radius_color": "#001a3d",
        "radius_opacity": 0.1,
        "poi_color": "#001a3d",
        "poi_opacity": 0.8
    }

def execute_global_purge():
    st.session_state.geo_coords = DEFAULT_COORDS
    st.session_state.geo_radius = DEFAULT_RADIUS
    st.session_state.scanned_records = []
    st.session_state.last_scan_lat = 14.6465
    st.session_state.last_scan_lon = 121.0371
    st.session_state.map_styles = {
        "pin_color": "#001a3d",
        "radius_color": "#001a3d",
        "radius_opacity": 0.1,
        "poi_color": "#001a3d",
        "poi_opacity": 0.8
    }
    for key in list(st.session_state.keys()):
        if key.startswith("chk_"): st.session_state[key] = False

POI_CONFIG = {
    "COMMERCIAL": [['Corporate Office', '"building"~"office|commercial",i'], ['IT/Tech Center', '"office"~"it|telecommunication",i'], ['Business Center', '"building"="commercial"']],
    "RETAIL": [['Mall/Dept Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"supermarket|grocery",i'], ['Convenience', '"shop"="convenience"']],
    "FOOD & BEVERAGES": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"']]
}

# -----------------------------------------------------------------------------
# 3. SIDEBAR LAYOUT STREAMS
# -----------------------------------------------------------------------------
# CONTROL ELEMENT 1: DYNAMIC LIGHT/DARK ALTERNATOR AT APEX WALL
theme_btn_label = "THEME: ACTIVE LIGHT" if not st.session_state.dark_mode else "THEME: ACTIVE DARK"
if st.button(theme_btn_label, key="theme_toggle_apex_btn"):
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.rerun()

if st.button("CLEAR ALL PARAMETERS", key="master_purge_btn", type="tertiary"):
    execute_global_purge()
    st.rerun()

# MAIN CONFIGURATION FIELDS CONTAINER
st.markdown("<p style='font-size:9px; font-weight:900; margin-top:10px;'>TARGET PROFILE</p>", unsafe_allow_html=True)
coords_val = st.text_input("Target Coordinates", key="geo_coords", label_visibility="collapsed")
radius_val = st.number_input("Radius (Meters)", min_value=100, max_value=50000, key="geo_radius", step=100)

coord_match = re.match(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", coords_val)
lat_coord, lon_coord = (float(coord_match.group(1)), float(coord_match.group(2))) if coord_match else (14.6465, 121.0371)

search_query = st.text_input("Filter Catalog", placeholder="Search categories...").lower()

# EXPANDABLE POI LAYERS COMPONENT BOX
selected_tags = []
for cat_name, node_items in POI_CONFIG.items():
    matched = [item for item in node_items if search_query in item[0].lower()]
    if matched:
        with st.expander(cat_name, expanded=True):
            for label, tag in matched:
                if st.checkbox(label, key=f"chk_{cat_name}_{label}"): 
                    selected_tags.append(tag)

if st.button("🚀 EXECUTE SCAN AREA", use_container_width=True, key="trigger_scan_proc"):
    if selected_tags:
        url = "https://overpass-api.de/api/interpreter"
        statements = "\n".join([f"  nwr[{tag}](around:{radius_val},{lat_coord},{lon_coord});" for tag in selected_tags])
        ql = f"[out:json][timeout:90];(\n{statements}\n);\nout center;"
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
        except Exception: pass

# BOTTOM ATTACHED RUNTIME EXPORT MAPPING PANELS
st.markdown("<div style='flex-grow: 1;'></div>", unsafe_allow_html=True)
st.markdown("<hr style='margin: 8px 0; border-color: var(--border-main);'>", unsafe_allow_html=True)
st.markdown("<p style='font-size:9px; font-weight:900; margin-bottom:4px;'>PROJECT REPOSITORY</p>", unsafe_allow_html=True)

col_imp, col_exp = st.columns(2)
with col_imp:
    imported_project = st.file_uploader("Import JSON", type=["json"], key="project_loader_node")
    if imported_project is not None:
        try:
            p_load = json.load(imported_project)
            st.session_state.geo_coords = p_load.get("geo_coords", DEFAULT_COORDS)
            st.session_state.geo_radius = p_load.get("geo_radius", DEFAULT_RADIUS)
            st.session_state.scanned_records = p_load.get("scanned_records", [])
            st.session_state.last_scan_lat = p_load.get("last_scan_lat", 14.6465)
            st.session_state.last_scan_lon = p_load.get("last_scan_lon", 121.0371)
            if "map_styles" in p_load: st.session_state.map_styles = p_load["map_styles"]
            st.rerun()
        except Exception: pass
with col_exp:
    exp_fmt = st.selectbox("Export Options", ["Select...", "KML Radius", "KML POIs", "JSON Project"], label_visibility="collapsed")
    if exp_fmt == "KML Radius":
        st.download_button("Get Radius", f'<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Radius</name></Document></kml>', "Radius.kml")
    elif exp_fmt == "KML POIs":
        st.download_button("Get POIs", f'<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>POIs</name></Document></kml>', "POIs.kml")
    elif exp_fmt == "JSON Project":
        project_bundle = {"geo_coords": coords_val, "geo_radius": radius_val, "scanned_records": st.session_state.scanned_records, "last_scan_lat": st.session_state.last_scan_lat, "last_scan_lon": st.session_state.last_scan_lon, "map_styles": st.session_state.map_styles}
        st.download_button("Get Project", json.dumps(project_bundle, indent=2), "project.json", "application/json")

# -----------------------------------------------------------------------------
# 4. LEAFLET HIGH-FIDELITY VIEWPORT CANVAS INJECTION
# -----------------------------------------------------------------------------
geojson_str = json.dumps(st.session_state.scanned_records)
style_bundle_str = json.dumps(st.session_state.map_styles)
dark_mode_token = "true" if st.session_state.dark_mode else "false"

leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        :root { --bg-panel: #ffffff; --text-panel: #001a3d; --border-panel: #001a3d; }
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; overflow: hidden; background: var(--bg-panel); }
        #map { height: 100vh; width: 100%; }
        
        /* MONOCHROME FLAT OVERLAY INTERFACE PANELS */
        #search-container {
            position: absolute; top: 12px; left: 12px; z-index: 1000;
            background: var(--bg-panel); border: 2px solid var(--border-panel); width: 240px; font-family: sans-serif;
        }
        #search-input {
            width: 100%; border: none; padding: 8px; font-size: 11px; outline: none;
            background: var(--bg-panel); color: var(--text-panel); box-sizing: border-box; font-weight: 700;
        }
        #search-results-box {
            background: var(--bg-panel); border-top: 1px solid var(--border-panel); display: none; max-height: 180px; overflow-y: auto;
        }
        .search-suggest-item {
            padding: 6px 10px; font-size: 10px; color: var(--text-panel); cursor: pointer; border-bottom: 1px solid #f1f5f9;
        }
        .search-suggest-item:hover { background: var(--text-panel); color: var(--bg-panel); }

        #map-action-toolbar {
            position: absolute; top: 82px; left: 12px; z-index: 1000; display: flex; flex-direction: column; gap: 4px;
        }
        .toolbar-trigger-btn {
            background: var(--bg-panel); width: 30px; height: 30px; border: 2px solid var(--border-panel);
            display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 10px; font-weight: 900; color: var(--text-panel);
        }
        .toolbar-trigger-btn:hover { background: var(--text-panel); color: var(--bg-panel); }

        .toolbar-floating-menu {
            position: absolute; left: 48px; background: var(--bg-panel); border: 2px solid var(--border-panel);
            padding: 8px; font-family: sans-serif; color: var(--text-panel); width: 160px; display: none; box-shadow: none;
        }
        #basemap-menu-container { top: 0px; } #style-menu-container { top: 34px; }
        .panel-row { margin-bottom: 6px; } .panel-row:last-child { margin-bottom: 0; }
        .panel-row label { display: block; font-size: 8px; font-weight: 900; margin-bottom: 2px; text-transform: uppercase; }
        .panel-row select, .panel-row input[type="text"], .panel-row input[type="range"] {
            width: 100%; font-size: 9px; padding: 2px; border: 1px solid var(--border-panel); background: var(--bg-panel); color: var(--text-panel); box-sizing: border-box;
        }

        /* RIGHT HAND LAYER WALL & PANEL CAPTURE MATRIX */
        #scan-results-panel {
            position: absolute; top: 12px; right: 12px; z-index: 1000; background: var(--bg-panel);
            width: 280px; height: calc(100vh - 24px); border: 2px solid var(--border-panel);
            display: flex; flex-direction: column; overflow: hidden; font-family: sans-serif;
        }
        .results-header {
            background: var(--text-panel); color: var(--bg-panel); padding: 8px 10px; font-size: 10px; font-weight: 900;
            display: flex; justify-content: space-between; align-items: center; text-transform: uppercase;
        }
        .results-badge { background: var(--bg-panel); color: var(--text-panel); padding: 1px 5px; font-weight: 900; font-size: 9px; }
        .panel-control-action-btn { cursor: pointer; border: 1px solid var(--bg-panel); padding: 1px 4px; font-size: 8px; margin-left: 4px; font-weight: 900; }
        .results-list { overflow-y: auto; flex-grow: 1; }
        
        .layer-category-block { border-bottom: 1px solid var(--border-panel); }
        .layer-category-header {
            background: var(--bg-panel); padding: 6px 10px; display: flex; align-items: center; justify-content: space-between; cursor: pointer;
        }
        .layer-header-left { display: flex; align-items: center; gap: 6px; font-size: 10px; font-weight: 900; color: var(--text-panel); }
        .layer-category-items { padding: 2px 0; background: var(--bg-panel); }
        .layer-category-items.collapsed { display: none !important; }
        .results-item { padding: 4px 12px 4px 26px; font-size: 10px; color: var(--text-panel); cursor: pointer; }
        .results-item:hover { background: var(--text-panel); color: var(--bg-panel); font-weight: 700; }

        /* RIGHT CLICK CONTEXT COMPONENT MENU FLAT BOX */
        #custom-context-menu {
            position: absolute; z-index: 10000; background: var(--bg-panel); border: 2px solid var(--border-panel);
            width: 130px; font-family: sans-serif; display: none;
        }
        .context-option {
            padding: 6px 10px; font-size: 10px; color: var(--text-panel); cursor: pointer; font-weight: 700;
        }
        .context-option:hover { background: var(--text-panel); color: var(--bg-panel); }

        .poi-text-label {
            background: var(--bg-panel); border: 1px solid var(--border-panel); padding: 1px 3px; font-size: 9px; font-weight: 700; color: var(--text-panel); white-space: nowrap;
        }
        .hide-labels .poi-text-label { display: none !important; }
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div id="search-container">
        <input type="text" id="search-input" placeholder="SEARCH LOCATION..." oninput="fetchGeocodeSuggestions(this.value)">
        <div id="search-results-box"></div>
    </div>

    <div id="map-action-toolbar">
        <div class="toolbar-trigger-btn" onclick="toggleMenuPanel('basemap-menu-container')">MAP</div>
        <div class="toolbar-trigger-btn" onclick="toggleMenuPanel('style-menu-container')">EDIT</div>
    </div>
    
    <div id="basemap-menu-container" class="toolbar-floating-menu">
        <div class="panel-row">
            <label>Basemap Core</label>
            <select id="basemap-select" onchange="applyMapLayer(this.value)">
                <option value="osm">OpenStreetMap</option>
                <option value="satellite">Satellite View</option>
                <option value="carto">Carto Minimal</option>
            </select>
        </div>
        <div class="panel-row" style="display:flex; align-items:center; gap:4px;">
            <input type="checkbox" id="label-toggle-chk" checked onchange="toggleLabelCanvas(this.checked)">
            <label style="margin:0;" for="label-toggle-chk">Show Text Labels</label>
        </div>
    </div>
    
    <div id="style-menu-container" class="toolbar-floating-menu">
        <div class="panel-row">
            <label>Stroke Hex Code</label>
            <input type="text" id="hex-style-input" placeholder="#001a3d" onchange="updateStylesRuntime(this.value)">
        </div>
        <div class="panel-row">
            <label>Radius Fill Opacity</label>
            <input type="range" id="opac-style-slider" min="0" max="1" step="0.05" oninput="updateOpacityRuntime(this.value)">
        </div>
    </div>

    <div id="scan-results-panel">
        <div class="results-header">
            <span id="panel-title-node">Layers & POIs</span>
            <div>
                <span class="results-badge" id="results-count">0</span>
                <span class="panel-control-action-btn" id="fs-pane-btn" style="display:none;" onclick="launchFullscreenExt()">FULLSCREEN</span>
                <span class="panel-control-action-btn" id="close-pane-btn" style="display:none;" onclick="exitExternalPane()">CLOSE</span>
            </div>
        </div>
        <div class="results-list" id="results-list-box"></div>
        <div id="iframe-view-wrapper" style="display:none; flex-grow:1; width:100%; height:100%;">
            <iframe id="external-pane-iframe" src=""></iframe>
        </div>
    </div>

    <div id="custom-context-menu">
        <div class="context-option" onclick="fireContextRoute('coords')">Coordinates</div>
        <div class="context-option" onclick="fireContextRoute('routes')">Routes</div>
        <div class="context-option" onclick="fireContextRoute('streetview')">Streetview</div>
    </div>

    <script>
        // EVALUATE ACTIVE RUNTIME MONOCHROME COLORS BASED ON SIDEBAR SELECTION
        const isDark = __DARK_MODE_STATUS__;
        if(isDark) {
            document.documentElement.style.setProperty('--bg-panel', '#001a3d');
            document.documentElement.style.setProperty('--text-panel', '#ffffff');
            document.documentElement.style.setProperty('--border-panel', '#ffffff');
        } else {
            document.documentElement.style.setProperty('--bg-panel', '#ffffff');
            document.documentElement.style.setProperty('--text-panel', '#001a3d');
            document.documentElement.style.setProperty('--border-panel', '#001a3d');
        }

        const map = L.map('map', { zoomControl: true, attributionControl: false }).setView([__LAT__, __LON__], 14);
        const basemaps = {
            osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }),
            satellite: L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', { maxZoom: 20 }),
            carto: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 })
        };
        
        let activeLayerKey = localStorage.getItem('ts_persistent_basemap') || 'osm';
        if(!basemaps[activeLayerKey]) activeLayerKey = 'osm';
        document.getElementById('basemap-select').value = activeLayerKey;
        basemaps[activeLayerKey].addTo(map);

        function applyMapLayer(k) {
            map.removeLayer(basemaps[activeLayerKey]); basemaps[k].addTo(map); activeLayerKey = k;
            localStorage.setItem('ts_persistent_basemap', k);
        }

        // PREVENT LEAFLET LAYER CLICK FROM CLOSING PANELS
        L.DomEvent.disableClickPropagation(document.getElementById('search-container'));
        L.DomEvent.disableClickPropagation(document.getElementById('map-action-toolbar'));
        L.DomEvent.disableClickPropagation(document.getElementById('basemap-menu-container'));
        L.DomEvent.disableClickPropagation(document.getElementById('style-menu-container'));
        L.DomEvent.disableClickPropagation(document.getElementById('scan-results-panel'));
        L.DomEvent.disableClickPropagation(document.getElementById('custom-context-menu'));

        function toggleMenuPanel(pId) {
            const el = document.getElementById(pId); const isShown = el.style.display === 'block';
            document.querySelectorAll('.toolbar-floating-menu').forEach(m => m.style.display = 'none');
            if(!isShown) el.style.display = 'block';
        }

        function toggleLabelCanvas(v) {
            if(v) document.getElementById('map').classList.remove('hide-labels');
            else document.getElementById('map').classList.add('hide-labels');
        }

        // PLOT PRIMARY BASE GEOMETRIES
        const centerMarker = L.circleMarker([__LAT__, __LON__], { radius: 7, fillColor: isDark ? '#ffffff' : '#001a3d', color: '#ffffff', weight: 2, fillOpacity: 1 }).addTo(map);
        const radiusCircle = L.circle([__LAT__, __LON__], { radius: __RADIUS__, color: isDark ? '#ffffff' : '#001a3d', weight: 2, fillColor: isDark ? '#ffffff' : '#001a3d', fillOpacity: 0.15 }).addTo(map);

        const pts = __GEOJSON__; const categoryMap = {}; const layerGroups = {};
        pts.forEach(p => { const k = p.type || 'POI Layer'; if(!categoryMap[k]) categoryMap[k] = []; categoryMap[k].push(p); });

        Object.keys(categoryMap).forEach(k => {
            layerGroups[k] = L.layerGroup().addTo(map);
            categoryMap[k].forEach(p => {
                const marker = L.circleMarker([p.lat, p.lon], { radius: 5, fillColor: isDark ? '#ffffff' : '#001a3d', color: isDark ? '#001a3d' : '#ffffff', weight: 1, fillOpacity: 0.8 });
                if(p.name && p.name !== 'Unknown') marker.bindTooltip(p.name, { permanent: true, direction: 'top', offset: [0, -4], className: 'poi-text-label' });
                marker.bindPopup("<b>" + p.name + "</b><br>" + p.type);
                marker.addTo(layerGroups[k]);
            });
        });

        // DRAW COMPACT OVERLAY ACCORDION ENTRIES
        const listBox = document.getElementById('results-list-box');
        document.getElementById('results-count').innerText = pts.length;
        if(pts.length === 0) {
            listBox.innerHTML = '<div class="results-item" style="font-style:italic;">No active assets.</div>';
        } else {
            let html = '';
            Object.keys(categoryMap).forEach(k => {
                html += `
                    <div class="layer-category-block">
                        <div class="layer-category-header" onclick="toggleAccordionNode('${k}')">
                            <div class="layer-header-left">
                                <input type="checkbox" checked onclick="event.stopPropagation(); setLayerVisibility('${k}', this.checked)">
                                <span>${k.toUpperCase()} [${categoryMap[k].length}]</span>
                            </div>
                        </div>
                        <div class="layer-category-items collapsed" id="layer-box-${k}">
                `;
                categoryMap[k].forEach(p => {
                    html += `<div class="results-item" onclick="focusPoiPoint(${p.lat}, ${p.lon})">${p.name}</div>`;
                });
                html += '</div></div>';
            });
            listBox.innerHTML = html;
        }

        function setLayerVisibility(k, v) { if(v) map.addLayer(layerGroups[k]); else map.removeLayer(layerGroups[k]); }
        function toggleAccordionNode(k) { document.getElementById('layer-box-' + k).classList.toggle('collapsed'); }
        function focusPoiPoint(lat, lon) { map.flyTo([lat, lon], 17); }

        function updateStylesRuntime(hex) { radiusCircle.setStyle({ color: hex, fillColor: hex }); }
        function updateOpacityRuntime(v) { radiusCircle.setStyle({ fillOpacity: parseFloat(v) }); }

        // GOOGLE STYLE LOCATION AUTOCOMPLETE SEARCH ENGINE
        function fetchGeocodeSuggestions(q) {
            const box = document.getElementById('search-results-box'); if(q.length < 3) { box.style.display = 'none'; return; }
            fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}&limit=4`)
                .then(r => r.json()).then(data => {
                    box.innerHTML = ''; if(data.length === 0) { box.style.display = 'none'; return; }
                    data.forEach(item => {
                        const div = document.createElement('div'); div.className = 'search-suggest-item'; div.innerText = item.display_name;
                        div.onclick = () => { map.panTo([parseFloat(item.lat), parseFloat(item.lon)]); box.style.display = 'none'; document.getElementById('search-input').value = item.display_name; };
                        box.appendChild(div);
                    });
                    box.style.display = 'block';
                });
        }

        // CONTEXT MENU ROUTINES MAPPED VIA CANVAS RIGHT-CLICK
        let activeContextLatLng = null; let activePaneType = null;
        map.on('contextmenu', function(e) {
            activeContextLatLng = e.latlng; const menu = document.getElementById('custom-context-menu');
            menu.style.top = e.containerPoint.y + 'px'; menu.style.left = e.containerPoint.x + 'px'; menu.style.display = 'block';
        });
        map.on('click', function() { document.getElementById('custom-context-menu').style.display = 'none'; });

        function fireContextRoute(t) {
            document.getElementById('custom-context-menu').style.display = 'none'; if(!activeContextLatLng) return;
            const lat = activeContextLatLng.lat.toFixed(5); const lon = activeContextLatLng.lng.toFixed(5);
            
            if(t === 'coords') {
                navigator.clipboard.writeText(lat + ", " + lon); alert("Copied: " + lat + ", " + lon);
            } else {
                activePaneType = t; document.getElementById('results-list-box').style.display = 'none';
                document.getElementById('fs-pane-btn').style.display = 'inline-block';
                document.getElementById('close-pane-btn').style.display = 'inline-block';
                document.getElementById('iframe-view-wrapper').style.display = 'block';
                const f = document.getElementById('external-pane-iframe');
                if(t === 'routes') {
                    document.getElementById('panel-title-node').innerText = "ROUTES VIEW";
                    f.src = `https://maps.google.com/maps?q=${lat},${lon}&ie=UTF8&output=embed`;
                } else {
                    document.getElementById('panel-title-node').innerText = "STREETVIEW WINDOW";
                    f.src = `https://maps.google.com/maps?layer=c&cbll=${lat},${lon}&output=svembed`;
                }
            }
        }

        function exitExternalPane() {
            document.getElementById('iframe-view-wrapper').style.display = 'none';
            document.getElementById('fs-pane-btn').style.display = 'none';
            document.getElementById('close-pane-btn').style.display = 'none';
            document.getElementById('results-list-box').style.display = 'block';
            document.getElementById('panel-title-node').innerText = "LAYERS & POIS";
        }

        function launchFullscreenExt() {
            if(!activeContextLatLng) return;
            let targetUrl = '';
            if(activePaneType === 'routes') targetUrl = `https://www.google.com/maps/dir/?api=1&destination=${activeContextLatLng.lat},${activeContextLatLng.lng}`;
            else targetUrl = `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${activeContextLatLng.lat},${activeContextLatLng.lng}`;
            window.open(targetUrl, '_blank');
        }

        if (pts.length > 0 && !__IS_STALE__) {
            const group = L.featureGroup([L.marker([__LAT__, __LON__]), ...pts.map(p => L.marker([p.lat, p.lon]))]);
            map.fitBounds(group.getBounds().pad(0.1));
        } else {
            map.setView([__LAT__, __LON__], 15);
        }
        setTimeout(() => map.invalidateSize(), 200);
    </script>
</body>
</html>
"""

leaflet_html = (leaflet_template
                .replace("__LAT__", str(render_lat))
                .replace("__LON__", str(render_lon))
                .replace("__RADIUS__", str(radius_val))
                .replace("__IS_STALE__", is_stale)
                .replace("__DARK_MODE_STATUS__", dark_mode_token)
                .replace("__GEOJSON__", geojson_str))

st.components.v1.html(leaflet_html, scrolling=False)
