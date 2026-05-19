import streamlit as st
import requests
import re
import json
import os

# --- PROGRAMMATIC LIGHT MODE LOCK ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\n")

# -----------------------------------------------------------------------------
# 1. ORCHESTRATION ROUTER & STATE PERSISTENCE
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Trade Area Matrix", layout="wide", initial_sidebar_state="expanded")

if "active_module" not in st.session_state: st.session_state.active_module = "SCANNER"
if 'geo_coords' not in st.session_state: st.session_state.geo_coords = "14.5995, 120.9842"
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = 1000
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'last_scan_lat' not in st.session_state: st.session_state.last_scan_lat = 14.5995
if 'last_scan_lon' not in st.session_state: st.session_state.last_scan_lon = 120.9842

# -----------------------------------------------------------------------------
# 2. GLOBAL STYLES & BRAND INJECTIONS
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Montserrat:wght@400;500;600;700;800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0');

        :root {
            --brand-midnight: #003366 !important;
            --brand-gold: #C9AB4C !important;
            --white-clean: #ffffff !important;
            --bg-offwhite: #f8fafc !important;
            --text-muted: #888780 !important;
        }
        
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container { background-color: var(--white-clean) !important; color: var(--brand-midnight) !important; font-family: 'Montserrat', sans-serif !important; }
        [data-testid="stSidebar"] { background-color: var(--bg-offwhite) !important; border-right: 1px solid rgba(0, 51, 102, 0.08) !important; width: 300px !important; min-width: 300px !important; max-width: 300px !important; overflow: hidden !important; }
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] { display: none !important; }
        ::-webkit-scrollbar { width: 0px !important; background: transparent !important; }
        
        [data-testid="stHeader"], header, #stDecoration { display: none !important; }
        [data-testid="stAppViewContainer"] { display: flex !important; flex-direction: row !important; width: 100vw !important; height: 100vh !important; overflow: hidden !important; }
        [data-testid="stMain"] { flex-grow: 1 !important; width: calc(100vw - 300px) !important; height: 100vh !important; overflow: hidden !important; margin: 0px !important; padding: 0px !important; }
        .block-container { padding: 0px !important; margin: 0px !important; max-width: 100% !important; gap: 0rem !important; }
        iframe { height: 100vh !important; width: 100% !important; border: none !important; display: block !important; }
        [data-testid="stSidebarUserContent"] { padding: 12px !important; height: 100vh !important; overflow-y: auto !important; overflow-x: hidden !important; }
        
        /* Unified Input Form Factors */
        div[data-baseweb="input"], div[data-baseweb="select"] { background-color: transparent !important; border: none !important; border-bottom: 1px solid rgba(201, 171, 76, 0.5) !important; border-radius: 0px !important; box-shadow: none !important; }
        div[data-baseweb="input"]:focus-within { border-bottom: 2px solid var(--brand-gold) !important; }
        .stTextInput label p, .stNumberInput label p { font-size: 9px !important; font-weight: 600 !important; letter-spacing: 0.5px; color: var(--text-muted) !important; text-transform: uppercase; }
        
        /* Bichromatic Router Buttons */
        div.stButton > button[kind="secondary"], [data-testid="stPopover"] > button, div.stDownloadButton > button { background-color: var(--brand-midnight) !important; border: 1px solid var(--brand-midnight) !important; border-radius: 2px !important; width: 100% !important; padding: 6px !important; transition: all 0.3s ease !important; }
        div.stButton > button[kind="secondary"]:hover, [data-testid="stPopover"] > button:hover, div.stDownloadButton > button:hover { background-color: var(--brand-gold) !important; border-color: var(--brand-gold) !important; }
        div.stButton > button[kind="secondary"] p, [data-testid="stPopover"] > button p, div.stDownloadButton > button p { color: var(--white-clean) !important; font-weight: 700 !important; font-size: 9px !important; text-transform: uppercase !important; letter-spacing: 1px; }
        
        /* Active State Button Hack (Primary) */
        div.stButton > button[kind="primary"] { background-color: var(--brand-gold) !important; border: 1px solid var(--brand-gold) !important; border-radius: 2px !important; width: 100% !important; padding: 6px !important; pointer-events: none; }
        div.stButton > button[kind="primary"] p { color: var(--brand-midnight) !important; font-weight: 800 !important; font-size: 9px !important; text-transform: uppercase !important; letter-spacing: 1px; }
        
        /* Subtle Clear Button */
        div[data-testid="stHorizontalBlock"] div.stButton > button[kind="secondary"] { background-color: transparent !important; border: 1px solid var(--brand-midnight) !important; }
        div[data-testid="stHorizontalBlock"] div.stButton > button[kind="secondary"] p { color: var(--brand-midnight) !important; }
        div[data-testid="stHorizontalBlock"] div.stButton > button[kind="secondary"]:hover { background-color: rgba(201, 171, 76, 0.1) !important; border-color: var(--brand-gold) !important; }
        
        [data-testid="stSidebar"] .st-expander { border: 1px solid rgba(0, 51, 102, 0.05) !important; background-color: var(--white-clean) !important; border-radius: 2px !important; margin-bottom: 2px !important; }
        [data-testid="stSidebar"] .st-expander summary p { font-size: 10px !important; font-weight: 600 !important; text-transform: uppercase; }
        .stCheckbox label p { font-size: 10px !important; font-weight: 500 !important; }
        div[data-baseweb="checkbox"] input:checked + div, div[data-baseweb="checkbox"] div[aria-checked="true"] { background-color: var(--brand-midnight) !important; border-color: var(--brand-midnight) !important; }
        
        .brand-title { font-family: 'Cormorant Garamond', serif !important; font-style: italic; color: var(--brand-midnight); font-size: 28px; text-align: center; margin-bottom: 5px; font-weight: 600; }
        .brand-subtitle { font-family: 'Montserrat', sans-serif !important; font-size: 8px; text-align: center; color: var(--text-muted); letter-spacing: 2px; text-transform: uppercase; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. DATA DICTIONARIES
# -----------------------------------------------------------------------------
POI_CONFIG = {
    "COMMERCIAL": [['Corporate Office', '"building"~"office|commercial",i'], ['IT/Tech Center', '"office"~"it|telecommunication",i'], ['Business Center', '"building"="commercial"'], ['Hospital', '"amenity"~"hospital|clinic",i'], ['Hotel', '"tourism"="hotel"']],
    "RESIDENTIAL": [['Apartments', '"building"="apartments"'], ['House', '"building"="house"'], ['Residential Area', '"landuse"="residential"'], ['Condominium', '"building"="residential"']],
    "RETAIL": [['Mall/Department Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"supermarket|grocery",i'], ['Convenience Store', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"']],
    "FOOD AND BEVERAGES": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee Shop', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"'], ['Bar/Pub', '"amenity"~"bar|pub|nightclub",i']]
}

ADVANCED_CONFIG = {
    "AMENITIES": [['ATM', '"amenity"="atm"'], ['Bank', '"amenity"="bank"'], ['Parking', '"amenity"="parking"']],
    "INDUSTRIAL & LOGISTICS": [['Ports & Terminals', '"industrial"="port"'], ['Warehouses', '"building"~"warehouse|depot",i']],
    "GOVERNMENT": [['City Hall', '"amenity"="townhall"'], ['Police Station', '"amenity"="police"']],
    "SCHOOLS": [['University', '"amenity"~"university|college",i'], ['K-12 School', '"amenity"="school"']]
}

def compile_features_kml(features):
    kml = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scanned POIs</name>'
    for f in features:
        name = f.get('name', 'Asset').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        class_type = f.get('type', 'Node').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        kml += f"<Placemark><name>{name}</name><description>{class_type}</description><Point><coordinates>{f['lon']},{f['lat']},0</coordinates></Point></Placemark>"
    return kml + '</Document></kml>'

# -----------------------------------------------------------------------------
# 4. UNIFIED SIDEBAR ROUTING ENGINE
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="brand-title">Trade Area Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-subtitle">Spatial Processing Module</div>', unsafe_allow_html=True)
    
    # CORE BICHROMATIC TOGGLE
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("SCANNER", use_container_width=True, type="primary" if st.session_state.active_module == "SCANNER" else "secondary"):
            st.session_state.active_module = "SCANNER"
            st.rerun()
    with btn_col2:
        if st.button("EDITOR", use_container_width=True, type="primary" if st.session_state.active_module == "EDITOR" else "secondary"):
            st.session_state.active_module = "EDITOR"
            st.rerun()

    st.markdown("<hr style='margin: 15px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.1);'>", unsafe_allow_html=True)

    # =========================================================================
    # A. SCANNER SIDEBAR CONTROLS
    # =========================================================================
    if st.session_state.active_module == "SCANNER":
        location_input = st.text_input("LOCATION SEARCH / COORDINATES", value=st.session_state.geo_coords)
        radius_val = st.number_input("RADIUS (METERS)", min_value=100, max_value=50000, value=st.session_state.geo_radius, step=100)
        st.session_state.geo_radius = radius_val

        coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", location_input)
        if coord_match:
            lat_coord, lon_coord = float(coord_match.group(1)), float(coord_match.group(2))
            st.session_state.geo_coords = location_input
        else:
            if location_input and location_input != st.session_state.get('last_geocoded_query', ''):
                with st.spinner("Locating via OSM..."):
                    try:
                        resp = requests.get(f"https://nominatim.openstreetmap.org/search?q={location_input}&format=json&limit=1", headers={'User-Agent': 'TradeArea/3.1'}, timeout=10).json()
                        if resp:
                            st.session_state.geo_coords = f"{float(resp[0]['lat']):.5f}, {float(resp[0]['lon']):.5f}"
                            st.session_state.last_geocoded_query = location_input
                            st.rerun()
                    except: pass
            fallback_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", st.session_state.geo_coords)
            lat_coord, lon_coord = (float(fallback_match.group(1)), float(fallback_match.group(2))) if fallback_match else (14.5995, 120.9842)

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        search_query = st.text_input("FILTER POI LAYERS", placeholder="Type to filter...").lower()
        
        selected_tags = []
        for cat_name, node_items in POI_CONFIG.items():
            matched = [item for item in node_items if search_query in item[0].lower()]
            if matched:
                with st.expander(cat_name, expanded=(len(search_query) > 0)):
                    for label, tag in matched:
                        if st.checkbox(label, key=f"chk_{cat_name}_{label}"): selected_tags.append(tag)

        st.markdown("<div style='font-weight:700; font-size:9px; margin-top:15px; margin-bottom:5px; color:#888780; letter-spacing:1px;'>ADVANCED ASSETS</div>", unsafe_allow_html=True)
        for cat_name, node_items in ADVANCED_CONFIG.items():
            matched = [item for item in node_items if search_query in item[0].lower()]
            if matched:
                with st.expander(cat_name, expanded=(len(search_query) > 0)):
                    for label, tag in matched:
                        if st.checkbox(label, key=f"chk_adv_{cat_name}_{label}"): selected_tags.append(tag)

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        act_col1, act_col2 = st.columns([2, 1])
        with act_col1:
            if st.button("RUN SCAN", type="secondary", use_container_width=True):
                if selected_tags:
                    url = "https://overpass-api.de/api/interpreter"
                    statements = "\n".join([f"  nwr[{tag}](around:{radius_val},{lat_coord},{lon_coord});" for tag in selected_tags])
                    ql = f"[out:json][timeout:90];(\n{statements}\n);\nout center;"
                    with st.spinner("Extracting nodes..."):
                        try:
                            res = requests.post(url, data={"data": ql}, timeout=100)
                            if res.status_code == 200:
                                records = []
                                for el in res.json().get('elements', []):
                                    e_lat, e_lon = el.get('lat') or el.get('center', {}).get('lat'), el.get('lon') or el.get('center', {}).get('lon')
                                    if e_lat and e_lon:
                                        tags = el.get('tags', {})
                                        records.append({"lat": e_lat, "lon": e_lon, "name": tags.get('name', 'Unknown'), "type": tags.get('amenity') or tags.get('shop') or tags.get('building') or 'Node'})
                                st.session_state.scanned_records = records
                                st.session_state.last_scan_lat = lat_coord
                                st.session_state.last_scan_lon = lon_coord
                                st.rerun()
                        except: st.error("Timeout")
        with act_col2:
            if st.button("CLEAR", type="secondary", use_container_width=True):
                st.session_state.scanned_records = []
                for key in list(st.session_state.keys()):
                    if key.startswith("chk_"): st.session_state[key] = False
                st.rerun()

        st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>", unsafe_allow_html=True)
        exp_col1, exp_col2 = st.columns(2)
        with exp_col1: st.download_button("JSON", json.dumps(st.session_state.scanned_records), "scan.json", "application/json", use_container_width=True)
        with exp_col2: st.download_button("KML", compile_features_kml(st.session_state.scanned_records), "POIs.kml", "application/vnd.google-earth.kml+xml", use_container_width=True)

        with st.popover("IMPORT PROJECT FILE", use_container_width=True):
            imported_file = st.file_uploader("Select JSON", type=["json"], label_visibility="collapsed")
            if imported_file and st.button("LOAD", type="secondary", use_container_width=True):
                data = json.load(imported_file)
                st.session_state.scanned_records = data.get("scanned_records", data)
                st.session_state.geo_coords = data.get("coords", st.session_state.geo_coords)
                st.session_state.geo_radius = data.get("radius", st.session_state.geo_radius)
                st.rerun()

    # =========================================================================
    # B. EDITOR SIDEBAR CONTROLS
    # =========================================================================
    else:
        st.markdown(
            "<div style='font-size: 10px; font-weight:600; color:#888780; line-height: 1.5; text-align: justify; padding: 10px 0;'>"
            "Direct Vector Engineering Mode active. Select assets directly on the canvas or via the log block to manipulate properties, colors, and geometries. Changes are retained in session state."
            "</div>", 
            unsafe_allow_html=True
        )
        st.info("Feature styling overrides map cache. To extract customized markers, use the JSON export in Scanner Mode after edits.")

# -----------------------------------------------------------------------------
# 5. MAIN CANVAS ROUTING (LEAFLET INJECTION)
# -----------------------------------------------------------------------------
# Prepare standard variables
render_coords = st.session_state.geo_coords
coord_match = re.match(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", render_coords)
render_lat, render_lon = (float(coord_match.group(1)), float(coord_match.group(2))) if coord_match else (14.5995, 120.9842)
radius_val = st.session_state.geo_radius

# Pre-process records for Editor defaults
for idx, record in enumerate(st.session_state.scanned_records):
    if "_uid" not in record: record["_uid"] = idx
    if "visible" not in record: record["visible"] = True
    if "style" not in record:
        record["style"] = {
            "color": "#003366", "icon_shape": "circle", "icon_size": 24, "icon_symbol": "", "icon_opacity": 1.0,
            "fill_color": "#C9AB4C", "fill_opacity": 0.4, "weight": 2.0, "fill": True
        }

geojson_str = json.dumps(st.session_state.scanned_records)
is_stale = "true" if (render_lat != st.session_state.last_scan_lat or render_lon != st.session_state.last_scan_lon) else "false"

# --- SCANNER HTML TEMPLATE ---
if st.session_state.active_module == "SCANNER":
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap" rel="stylesheet">
        <style>
            body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #ffffff; overflow: hidden; font-family: 'Montserrat', sans-serif; }
            #map { height: 100vh; width: 100%; }
            #scan-results-panel { position: absolute; top: 15px; right: 15px; z-index: 1000; background: #ffffff; width: 280px; max-height: calc(100vh - 30px); border-radius: 4px; border: 1px solid rgba(0, 51, 102, 0.1); display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 20px rgba(0, 51, 102, 0.1); }
            .results-header { background: #003366; color: #ffffff; padding: 12px; font-size: 10px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; border-bottom: 2px solid #C9AB4C; letter-spacing: 1px; }
            .results-list { overflow-y: auto; flex-grow: 1; padding-bottom: 8px; }
            .layer-category-header { background: #f8fafc; padding: 10px 12px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; user-select: none; border-bottom: 1px solid #f0f0f0; }
            .layer-header-left { display: flex; align-items: center; gap: 6px; font-size: 9px; font-weight: 700; color: #003366; text-transform: uppercase;}
            .layer-category-items { background: #ffffff; }
            .layer-category-items.collapsed { display: none !important; }
            .results-item { padding: 8px 12px 8px 28px; font-size: 9px; font-weight: 600; color: #888780; display: flex; justify-content: space-between; align-items: center; cursor: pointer; border-bottom: 1px solid #f8fafc; }
            .results-item:hover { background: #f8fafc; color: #003366; }
            .poi-text-label { background: #fff; border: 1px solid #003366; padding: 2px 4px; border-radius: 2px; font-size: 9px; font-weight: 700; color: #003366; white-space: nowrap; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .color-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; border: 1px solid rgba(0,0,0,0.2); }
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div id="scan-results-panel">
            <div class="results-header"><span>SEARCH RESULTS</span><span id="results-count" style="color:#C9AB4C;">0</span></div>
            <div class="results-list" id="results-list-box"></div>
        </div>

        <script>
            const map = L.map('map', { zoomControl: true, attributionControl: false }).setView([__LAT__, __LON__], 14);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(map);

            const starIcon = L.divIcon({ html: '<div style="background-color: #003366; color: #C9AB4C; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; border: 2px solid #ffffff; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">★</div>', className: '', iconSize: [24, 24], iconAnchor: [12, 12] });
            L.marker([__LAT__, __LON__], { icon: starIcon, zIndexOffset: 1000 }).addTo(map);
            L.circle([__LAT__, __LON__], { radius: __RADIUS__, color: "#003366", weight: 1.5, fillColor: "#003366", fillOpacity: 0.05 }).addTo(map);
            
            let pts = __GEOJSON__;
            let globalIdCounter = 0;
            const categoryMap = {}; const layerGroupsRef = {};
            const catPalette = ["#003366", "#C9AB4C", "#1A5A8A", "#A8862E", "#3D7DA8", "#7A5C10", "#6A94B0", "#D4B85A", "#001F3F", "#E8D494"];
            const categoryColors = {}; let colorIndex = 0;
            
            pts.forEach(p => {
                p._uid = globalIdCounter++;
                const layerKey = p.type || 'Unclassified';
                if (!categoryMap[layerKey]) { categoryMap[layerKey] = []; categoryColors[layerKey] = catPalette[colorIndex % catPalette.length]; colorIndex++; }
                categoryMap[layerKey].push(p);
            });

            Object.keys(categoryMap).forEach(key => {
                layerGroupsRef[key] = L.layerGroup().addTo(map);
                const pColor = categoryColors[key];
                const svgIcon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22"><circle cx="12" cy="12" r="10" fill="${pColor}" stroke="#ffffff" stroke-width="1.5"/></svg>`;
                const iconDef = L.divIcon({ html: `<div style="display:flex;align-items:center;justify-content:center;">${svgIcon}</div>`, className: '', iconSize: [22, 22], iconAnchor: [11, 11] });
                
                categoryMap[key].forEach(p => {
                    const marker = L.marker([p.lat, p.lon], { icon: iconDef }).bindPopup(`<b style="color:#003366;">${p.name}</b><br><span style="color:#888780;font-size:9px;">${p.type}</span>`);
                    if (p.name && p.name !== 'Unknown') marker.bindTooltip(p.name, { permanent: false, direction: 'top', className: 'poi-text-label' });
                    p._marker = marker;
                    marker.addTo(layerGroupsRef[key]);
                });
            });

            const listBox = document.getElementById('results-list-box');
            document.getElementById('results-count').innerText = pts.length;
            
            if (pts.length > 0) {
                let htmlPayload = '';
                Object.keys(categoryMap).forEach(catName => {
                    const safeId = catName.replace(/[^a-zA-Z0-9]/g, '_');
                    htmlPayload += `
                        <div class="layer-category-header" onclick="document.getElementById('items-${safeId}').classList.toggle('collapsed');">
                            <div class="layer-header-left">
                                <input type="checkbox" checked onclick="event.stopPropagation(); if(this.checked) map.addLayer(layerGroupsRef['${catName}']); else map.removeLayer(layerGroupsRef['${catName}']);">
                                <span class="color-dot" style="background-color: ${categoryColors[catName]};"></span>
                                <span>${catName} <span style="color:#C9AB4C;">(${categoryMap[catName].length})</span></span>
                            </div>
                        </div>
                        <div class="layer-category-items" id="items-${safeId}">`;
                    categoryMap[catName].forEach(p => {
                        htmlPayload += `<div class="results-item" onclick="map.flyTo([${p.lat}, ${p.lon}], 17);"><div style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${p.name}</div></div>`;
                    });
                    htmlPayload += '</div>';
                });
                listBox.innerHTML = htmlPayload;
            }

            if (pts.length > 0 && !__IS_STALE__) {
                const bounds = L.featureGroup([L.marker([__LAT__, __LON__]), ...pts.map(p => L.marker([p.lat, p.lon]))]).getBounds();
                map.fitBounds(bounds.pad(0.1));
            }
        </script>
    </body>
    </html>
    """

# --- EDITOR HTML TEMPLATE ---
else:
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <link rel="stylesheet" href="https://unpkg.com/@geoman-io/leaflet-geoman-free@latest/dist/leaflet-geoman.css" />
        <script src="https://unpkg.com/@geoman-io/leaflet-geoman-free@latest/dist/leaflet-geoman.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0" rel="stylesheet">
        <style>
            body, html { margin: 0; padding: 0; height: 100%; width: 100%; overflow: hidden; font-family: 'Montserrat', sans-serif; }
            #map { height: 100vh; width: 100%; }
            #feature-properties-panel { position: absolute; bottom: 20px; right: 20px; z-index: 1000; background: #ffffff; width: 280px; border-radius: 4px; border: 1px solid rgba(0, 51, 102, 0.1); box-shadow: 0 4px 20px rgba(0, 51, 102, 0.15); display: none; flex-direction: column; }
            .panel-header { background: #003366; color: #ffffff; padding: 12px; font-size: 10px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; border-bottom: 2px solid #C9AB4C; }
            .panel-body { padding: 15px; display: flex; flex-direction: column; gap: 12px; max-height: 50vh; overflow-y: auto; }
            .control-group label { font-size: 9px; font-weight: 700; color: #888780; display: block; margin-bottom: 4px; }
            .control-group input[type="text"], .control-group select, .control-group input[type="number"] { width: 100%; padding: 6px; font-size: 11px; font-family: 'Montserrat', sans-serif; color: #003366; border: none; border-bottom: 1px solid #e2e8f0; outline: none; box-sizing: border-box; }
            .control-group input[type="text"]:focus, .control-group select:focus { border-bottom: 2px solid #C9AB4C; }
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div id="feature-properties-panel">
            <div class="panel-header"><span>Mutate Attributes</span><span style="cursor:pointer;color:#C9AB4C;" onclick="document.getElementById('feature-properties-panel').style.display='none'">✖</span></div>
            <div class="panel-body">
                <div class="control-group"><label>Title</label><input type="text" id="prop-name" onchange="commitChanges()"></div>
                <div class="control-group"><label>Hex Color</label><input type="text" id="prop-color" onchange="commitChanges()"></div>
                <div class="control-group" id="grp-shape"><label>Icon Shape</label><select id="prop-shape" onchange="commitChanges()"><option value="circle">Circle</option><option value="pin">Pin</option><option value="square">Square</option></select></div>
                <div class="control-group" id="grp-sym"><label>Material Symbol</label><input type="text" id="prop-sym" onchange="commitChanges()"></div>
            </div>
        </div>

        <script>
            const map = L.map('map', { zoomControl: true, attributionControl: false }).setView([__LAT__, __LON__], 14);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 }).addTo(map);
            map.pm.addControls({ position: 'topleft', drawMarker: true, drawPolygon: true, editMode: true, removalMode: true });

            L.circle([__LAT__, __LON__], { radius: __RADIUS__, color: "#003366", weight: 1.5, fillColor: "#003366", fillOpacity: 0.05 }).addTo(map);

            let pts = __GEOJSON__;
            let activeFeature = null; let activeLayer = null;

            function renderIcon(color, shape, size, sym) {
                let svg = '';
                if(shape === 'circle') svg = `<svg viewBox="0 0 24 24" width="24" height="24"><circle cx="12" cy="12" r="10" fill="${color}" stroke="#fff" stroke-width="1.5"/><text x="12" y="15" font-family="Material Symbols Rounded" font-size="11px" fill="#fff" text-anchor="middle">${sym||''}</text></svg>`;
                else if(shape === 'square') svg = `<svg viewBox="0 0 24 24" width="24" height="24"><rect x="3" y="3" width="18" height="18" rx="2" fill="${color}" stroke="#fff" stroke-width="1.5"/><text x="12" y="15" font-family="Material Symbols Rounded" font-size="11px" fill="#fff" text-anchor="middle">${sym||''}</text></svg>`;
                else svg = `<svg viewBox="0 0 24 24" width="26" height="26"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" fill="${color}" stroke="#fff" stroke-width="1.5"/><text x="12" y="11" font-family="Material Symbols Rounded" font-size="9px" fill="#fff" text-anchor="middle">${sym||''}</text></svg>`;
                return L.divIcon({ html: `<div style="display:flex;justify-content:center;">${svg}</div>`, className: '', iconSize:[26,26], iconAnchor:[13,26] });
            }

            pts.forEach(p => {
                let layer = p.geom_type === 'Polygon' ? L.polygon(p.coordinates, { color: p.style.color }) : L.marker([p.lat, p.lon], { icon: renderIcon(p.style.color, p.style.icon_shape, 24, p.style.icon_symbol) });
                layer.addTo(map);
                layer.on('click', (e) => {
                    L.DomEvent.stopPropagation(e);
                    activeFeature = p; activeLayer = layer;
                    document.getElementById('prop-name').value = p.name; document.getElementById('prop-color').value = p.style.color;
                    if(p.geom_type !== 'Polygon') {
                        document.getElementById('grp-shape').style.display = 'block'; document.getElementById('grp-sym').style.display = 'block';
                        document.getElementById('prop-shape').value = p.style.icon_shape; document.getElementById('prop-sym').value = p.style.icon_symbol || '';
                    } else {
                        document.getElementById('grp-shape').style.display = 'none'; document.getElementById('grp-sym').style.display = 'none';
                    }
                    document.getElementById('feature-properties-panel').style.display = 'flex';
                });
            });

            function commitChanges() {
                if(!activeFeature) return;
                activeFeature.name = document.getElementById('prop-name').value;
                activeFeature.style.color = document.getElementById('prop-color').value;
                if(activeFeature.geom_type !== 'Polygon') {
                    activeFeature.style.icon_shape = document.getElementById('prop-shape').value;
                    activeFeature.style.icon_symbol = document.getElementById('prop-sym').value;
                    activeLayer.setIcon(renderIcon(activeFeature.style.color, activeFeature.style.icon_shape, 24, activeFeature.style.icon_symbol));
                } else {
                    activeLayer.setStyle({ color: activeFeature.style.color });
                }
            }
        </script>
    </body>
    </html>
    """

# Inject Final Template
final_html = (html_template
              .replace("__LAT__", str(render_lat))
              .replace("__LON__", str(render_lon))
              .replace("__RADIUS__", str(radius_val))
              .replace("__IS_STALE__", is_stale)
              .replace("__GEOJSON__", geojson_str))

st.components.v1.html(final_html, height=850, scrolling=False)
