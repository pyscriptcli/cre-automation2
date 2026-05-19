import streamlit as st
import requests
import re
import json
import os
import importlib

# --- PROGRAMMATIC LIGHT MODE LOCK ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\n")

# -----------------------------------------------------------------------------
# 1. ORCHESTRATION ROUTER ENGINE (FIXED & COUPLING FORTIFIED)
# -----------------------------------------------------------------------------
if "active_module" not in st.session_state:
    st.session_state.active_module = "SCANNER"

st.set_page_config(
    page_title="Trade Area Scan Cluster",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. INTERFACE DECOUPLING LAYER
# -----------------------------------------------------------------------------
if st.session_state.active_module == "EDITOR":
    try:
        import trade_area_editor
        importlib.reload(trade_area_editor)
        trade_area_editor.render_editor_workspace()
    except ModuleNotFoundError:
        st.error("Engine Error: trade_area_editor.py not found within workspace cluster.")
        st.session_state.active_module = "SCANNER"
        st.rerun()
    st.stop()

# -----------------------------------------------------------------------------
# 3. GLOBAL WORKSPACE STYLES & INJECTIONS
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Montserrat:wght@400;500;600;700;800&display=swap');
        
        :root {
            --brand-midnight: #003366 !important;
            --brand-gold: #C9AB4C !important;
            --brand-dark: #001F3F !important;
            --white-clean: #ffffff !important;
            --bg-offwhite: #f8fafc !important;
            --text-muted: #888780 !important;
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
            width: 320px !important;
            min-width: 320px !important;
            max-width: 320px !important;
        }
        
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] { display: none !important; }
        ::-webkit-scrollbar { width: 0px !important; background: transparent !important; }
        * { scrollbar-width: none !important; -ms-overflow-style: none !important; }
        
        [data-testid="stHeader"], header, #stDecoration { display: none !important; }
        .block-container, [data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"], .stElementContainer { padding: 0px !important; margin: 0px !important; max-width: 100% !important; gap: 0rem !important; }
        iframe { height: 100vh !important; width: 100% !important; border: none !important; display: block !important; }
        
        /* Form factor fixes for inputs */
        div[data-baseweb="input"], div[data-baseweb="select"] { background-color: transparent !important; border: none !important; border-bottom: 1px solid rgba(201, 171, 76, 0.5) !important; border-radius: 0px !important; }
        
        /* Tab Selection Row Buttons styling */
        div.stButton > button { border-radius: 2px !important; letter-spacing: 1px; text-transform: uppercase; font-family: 'Montserrat', sans-serif !important; }
        
        .brand-title { font-family: 'Cormorant Garamond', serif !important; font-style: italic; color: var(--brand-midnight); font-size: 32px; text-align: center; font-weight: 600; margin-bottom: 5px; }
        .brand-subtitle { font-family: 'Montserrat', sans-serif !important; font-size: 9px; text-align: center; color: var(--text-muted); letter-spacing: 2px; text-transform: uppercase; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. STATE PERSISTENCE & DATA MODELS
# -----------------------------------------------------------------------------
DEFAULT_COORDS = "14.5995, 120.9842"
DEFAULT_RADIUS = 1000

if 'geo_coords' not in st.session_state: st.session_state.geo_coords = DEFAULT_COORDS
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = DEFAULT_RADIUS
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'last_scan_lat' not in st.session_state: st.session_state.last_scan_lat = 14.5995
if 'last_scan_lon' not in st.session_state: st.session_state.last_scan_lon = 120.9842

POI_CONFIG = {
    "COMMERCIAL": [['Corporate Office', '"building"~"office|commercial",i'], ['IT/Tech Center', '"office"~"it|telecommunication",i'], ['Business Center', '"building"="commercial"'], ['Hospital', '"amenity"~"hospital|clinic",i'], ['Hotel', '"tourism"="hotel"']],
    "RESIDENTIAL": [['Apartments', '"building"="apartments"'], ['House', '"building"="house"'], ['Residential Area', '"landuse"="residential"'], ['Condominium', '"building"="residential"']],
    "RETAIL": [['Mall/Department Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"supermarket|grocery",i'], ['Convenience Store', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"'], ['General Shops', '"shop"~"boutique|clothes|shoes",i']],
    "FOOD AND BEVERAGES": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee Shop', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"'], ['Bar/Pub/Nightclub', '"amenity"~"bar|pub|nightclub",i']],
    "INDUSTRIAL & LOGISTICS": [['Expressway Exits', '"highway"~"motorway_junction|toll_gantry",i'], ['Ports & Terminals', '"industrial"="port"'], ['Manufacturing Plants', '"industrial"~"factory|manufacturing|processing",i'], ['Warehouses & Depots', '"building"~"warehouse|depot",i']],
    "GOVERNMENT & INFRASTRUCTURE": [['City Hall', '"amenity"="townhall"'], ['Police Station', '"amenity"="police"'], ['Fire Station', '"amenity"="fire_station"']],
    "SCHOOLS": [['University/College', '"amenity"~"university|college",i'], ['K-12 School', '"amenity"="school"']]
}

ADVANCED_CONFIG = {
    "AMENITIES": [['ATM', '"amenity"="atm"'], ['Bank', '"amenity"="bank"'], ['Fuel', '"amenity"="fuel"'], ['Parking', '"amenity"="parking"']],
    "PLACE OF WORSHIP": [['Church', '"religion"="christian"'], ['Mosque', '"religion"="muslim"'], ['Spa', '"leisure"="spa"']],
    "SPORTS": [['Basketball', '"sport"="basketball"'], ['Gymnastics', '"sport"="gymnastics"'], ['Sports centre', '"leisure"="sports_centre"']],
    "MISCELLANEOUS": [['Busstop', '"highway"="bus_stop"'], ['Office', '"office"="yes"'], ['Construction', '"landuse"="construction"']]
}

def compile_features_kml(features):
    kml = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.org/kml/2.2"><Document><name>Scanned POIs</name>'
    for f in features:
        name = f.get('name', 'Asset').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        class_type = f.get('type', 'Node').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        kml += f"<Placemark><name>{name}</name><description>{class_type}</description><Point><coordinates>{f['lon']},{f['lat']},0</coordinates></Point></Placemark>"
    return kml + '</Document></kml>'

# -----------------------------------------------------------------------------
# 5. SIDEBAR DESIGN WORKSPACE (IMPROVED BICHROMATIC ROUTER)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="brand-title">TRADE AREA</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-subtitle">Spatial Intelligence Engine</div>', unsafe_allow_html=True)
    
    # IMPROVED INTERFACE LAYER SELECTOR (SCAN BUTTON vs EDIT BUTTON)
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("SCANNER", use_container_width=True, type="secondary" if st.session_state.active_module == "SCANNER" else "primary"):
            st.session_state.active_module = "SCANNER"
            st.rerun()
    with btn_col2:
        if st.button("EDITOR", use_container_width=True, type="secondary" if st.session_state.active_module == "EDITOR" else "primary"):
            st.session_state.active_module = "EDITOR"
            st.rerun()
            
    st.markdown("<hr style='margin: 15px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.1);'>", unsafe_allow_html=True)
    
    location_input = st.text_input("LOCATION SEARCH OR COORDINATES", value=st.session_state.geo_coords)
    radius_val = st.number_input("RADIUS (METERS)", min_value=100, max_value=50000, value=st.session_state.geo_radius, step=100)
    st.session_state.geo_radius = radius_val

    coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", location_input)
    if coord_match:
        lat_coord, lon_coord = float(coord_match.group(1)), float(coord_match.group(2))
        st.session_state.geo_coords = location_input
    else:
        if location_input and location_input != st.session_state.get('last_geocoded_query', ''):
            with st.spinner("Locating via Nominatim..."):
                try:
                    headers = {'User-Agent': 'TradeAreaScan/3.1'}
                    osm_url = f"https://nominatim.openstreetmap.org/search?q={location_input}&format=json&limit=1"
                    resp = requests.get(osm_url, headers=headers, timeout=10).json()
                    if resp:
                        new_lat = float(resp[0]['lat'])
                        new_lon = float(resp[0]['lon'])
                        st.session_state.geo_coords = f"{new_lat:.5f}, {new_lon:.5f}"
                        st.session_state.last_geocoded_query = location_input
                        st.rerun()
                except Exception:
                    lat_coord, lon_coord = 14.5995, 120.9842
        fallback_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", st.session_state.geo_coords)
        lat_coord, lon_coord = (float(fallback_match.group(1)), float(fallback_match.group(2))) if fallback_match else (14.5995, 120.9842)

    search_query = st.text_input("FILTER POI LAYERS", placeholder="Type parameters...").lower()
    
    selected_tags = []
    for cat_name, node_items in POI_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for label, tag in matched:
                    if st.checkbox(label, key=f"chk_{cat_name}_{label}"): selected_tags.append(tag)

    st.markdown("<div style='font-weight:700; font-size:10px; margin-top:15px; margin-bottom:5px; color:#003366; letter-spacing:1px; text-transform:uppercase;'>Advanced Core Layers</div>", unsafe_allow_html=True)
    for cat_name, node_items in ADVANCED_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for label, tag in matched:
                    if st.checkbox(label, key=f"chk_adv_{cat_name}_{label}"): selected_tags.append(tag)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    
    if st.button("RUN SCANNER ANALYSIS", type="primary", use_container_width=True):
        if not selected_tags:
            st.error("Select at least 1 layer.")
        else:
            url = "https://overpass-api.de/api/interpreter"
            statements = "\n".join([f"  nwr[{tag}](around:{radius_val},{lat_coord},{lon_coord});" for tag in selected_tags])
            ql = f"[out:json][timeout:90];(\n{statements}\n);\nout center;"
            with st.spinner("Querying Overpass Vector Grid..."):
                try:
                    res = requests.post(url, data={"data": ql}, headers={"User-Agent": "TradeAreaScan/3.1"}, timeout=100)
                    if res.status_code == 200:
                        records = []
                        for el in res.json().get('elements', []):
                            e_lat = el.get('lat') or el.get('center', {}).get('lat')
                            e_lon = el.get('lon') or el.get('center', {}).get('lon')
                            if e_lat and e_lon:
                                tags = el.get('tags', {})
                                records.append({
                                    "lat": e_lat, 
                                    "lon": e_lon, 
                                    "name": tags.get('name', 'Unknown Feature'), 
                                    "type": tags.get('amenity') or tags.get('shop') or tags.get('building') or 'Node Asset'
                                })
                        st.session_state.scanned_records = records
                        st.session_state.last_scan_lat = lat_coord
                        st.session_state.last_scan_lon = lon_coord
                        st.rerun()
                except Exception:
                    st.error("Overpass Server Latency Timeout")

    if st.button("CLEAR MATRIX SPACE", type="secondary", use_container_width=True):
        st.session_state.scanned_records = []
        for key in list(st.session_state.keys()):
            if key.startswith("chk_"): st.session_state[key] = False
        st.rerun()

    st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("EXPORT JSON", json.dumps(st.session_state.scanned_records), "scan.json", "application/json", use_container_width=True)
    with col2:
        st.download_button("EXPORT KML", compile_features_kml(st.session_state.scanned_records), "POIs.kml", "application/vnd.google-earth.kml+xml", use_container_width=True)

# -----------------------------------------------------------------------------
# 6. SPATIAL CANVAS ENGINE (FIXED STRING ESCAPES & UI UPGRADE)
# -----------------------------------------------------------------------------
geojson_str = json.dumps(st.session_state.scanned_records)
render_lat = lat_coord
render_lon = lon_coord
is_stale = "true" if (lat_coord != st.session_state.last_scan_lat or lon_coord != st.session_state.last_scan_lon) else "false"

leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; overflow: hidden; font-family: 'Montserrat', sans-serif; }
        #map { height: 100vh; width: 100%; }
        
        #scan-results-panel { position: absolute; top: 15px; right: 15px; z-index: 1000; background: #ffffff; width: 280px; max-height: calc(100vh - 40px); border-radius: 4px; border: 1px solid rgba(0, 51, 102, 0.1); display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 20px rgba(0, 51, 102, 0.15); }
        .results-header { background: #003366; color: #ffffff; padding: 12px; font-size: 11px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; border-bottom: 2px solid #C9AB4C; letter-spacing: 1px; }
        .results-list { overflow-y: auto; flex-grow: 1; background: #ffffff; }
        .layer-category-block { border-bottom: 1px solid #f1f5f9; }
        .layer-category-header { background: #f8fafc; padding: 10px 12px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; user-select: none; }
        .layer-header-left { display: flex; align-items: center; gap: 8px; font-size: 10px; font-weight: 700; color: #003366; text-transform: uppercase; }
        .layer-category-items { padding: 0; background: #ffffff; }
        .layer-category-items.collapsed { display: none !important; }
        
        .results-item { padding: 8px 12px 8px 32px; font-size: 10px; font-weight: 600; color: #475569; display: flex; justify-content: space-between; align-items: center; cursor: pointer; border-bottom: 1px solid #f8fafc; }
        .results-item:hover { background: #f1f5f9; color: #003366; }
        .delete-poi-icon { cursor: pointer; display: flex; align-items: center; justify-content: center; width: 20px; height: 20px; }
        .delete-poi-icon svg { fill: #94a3b8; transition: fill 0.2s; }
        .delete-poi-icon:hover svg { fill: #ef4444; }

        .poi-text-label { background: #ffffff; border: 1px solid #003366; padding: 2px 6px; border-radius: 3px; font-size: 9px; font-family: 'Montserrat', sans-serif; font-weight: 700; color: #003366; box-shadow: 0 2px 4px rgba(0,0,0,0.08); }
        .color-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; border: 1px solid rgba(0,0,0,0.15); }
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div id="scan-results-panel">
        <div class="results-header">
            <span>Scan Layer Output</span>
            <span id="results-count" style="background:#C9AB4C; color:#003366; padding:2px 8px; border-radius:10px; font-size:9px;">0</span>
        </div>
        <div class="results-list" id="results-list-box"></div>
    </div>

    <script>
        const map = L.map('map', { zoomControl: true, attributionControl: false }).setView([__LAT__, __LON__], 14);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 }).addTo(map);

        L.marker([__LAT__, __LON__], {
            icon: L.divIcon({
                className: '',
                html: '<div style="background-color: #003366; color: #C9AB4C; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; border: 2px solid #ffffff; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">★</div>',
                iconSize: [24, 24], iconAnchor: [12, 12]
            })
        }).addTo(map);
        
        L.circle([__LAT__, __LON__], { radius: __RADIUS__, color: "#003366", weight: 2, fillColor: "#003366", fillOpacity: 0.05 }).addTo(map);
        
        let pts = __GEOJSON__;
        let globalIdCounter = 0;
        
        const categoryMap = {};
        const layerGroupsRef = {};
        const catPalette = ["#003366", "#C9AB4C", "#1E40AF", "#B45309", "#047857", "#4338CA", "#BE185D", "#111827"];
        const categoryColors = {}; 
        let colorIndex = 0;

        pts.forEach(p => {
            p._uid = globalIdCounter++;
            const layerKey = p.type || 'Unclassified Asset';
            if (!categoryMap[layerKey]) {
                categoryMap[layerKey] = [];
                categoryColors[layerKey] = catPalette[colorIndex % catPalette.length];
                colorIndex++;
            }
            categoryMap[layerKey].push(p);
        });
        
        Object.keys(categoryMap).forEach(key => {
            layerGroupsRef[key] = L.layerGroup().addTo(map);
            const pColor = categoryColors[key];
            
            categoryMap[key].forEach(p => {
                const markerSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="26" height="26"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="${pColor}" stroke="#ffffff" stroke-width="1.5"/></svg>`;
                const marker = L.marker([p.lat, p.lon], {
                    icon: L.divIcon({ html: `<div style="display:flex;align-items:center;justify-content:center;">${markerSvg}</div>`, className: '', iconSize: [26, 26], iconAnchor: [13, 26] })
                }).bindPopup(`<b style="color:#003366;">${p.name}</b><br><span style="color:#64748b;font-size:10px;">${p.type}</span>`);
                
                if (p.name && p.name !== 'Unknown') {
                    marker.bindTooltip(p.name, { permanent: false, direction: 'top', className: 'poi-text-label' });
                }
                p._marker = marker;
                marker.addTo(layerGroupsRef[key]);
            });
        });

        const listBox = document.getElementById('results-list-box');
        document.getElementById('results-count').innerText = pts.length;
        
        if (pts.length > 0) {
            let htmlPayload = '';
            const trashSvg = `<svg xmlns="http://www.w3.org/2000/svg" height="14" viewBox="0 -960 960 960" width="14"><path d="M280-120q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Zm400-600H280v520h400v-520ZM360-280h80v-360h-80v360Zm160 0h80v-360h-80v360ZM280-720v520-520Z"/></svg>`;

            Object.keys(categoryMap).forEach(catName => {
                const dotColor = categoryColors[catName];
                htmlPayload += `
                    <div class="layer-category-block" id="cat-block-${catName.replace(/[^a-zA-Z0-9]/g, '_')}">
                        <div class="layer-category-header" onclick="toggleAccordionCollapse('${catName.replace(/[^a-zA-Z0-9]/g, '_')}')">
                            <div class="layer-header-left">
                                <input type="checkbox" checked onclick="event.stopPropagation(); toggleCategoryVisibility('${catName}', this.checked)">
                                <span class="color-dot" style="background: ${dotColor};"></span>
                                <span>${catName} <span id="count-${catName.replace(/[^a-zA-Z0-9]/g, '_')}" style="color: #C9AB4C; font-size: 9px;">(${categoryMap[catName].length})</span></span>
                            </div>
                            <span id="chevron-${catName.replace(/[^a-zA-Z0-9]/g, '_')}" style="font-size: 9px; color:#C9AB4C;">▼</span>
                        </div>
                        <div class="layer-category-items" id="items-${catName.replace(/[^a-zA-Z0-9]/g, '_')}">
                `;
                
                categoryMap[catName].forEach(p => {
                    htmlPayload += `
                    <div class="results-item" id="res-item-${p._uid}" onclick="map.flyTo([${p.lat}, ${p.lon}], 17);">
                        <div style="flex-grow:1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${p.name}</div>
                        <div class="delete-poi-icon" title="Remove POI" onclick="event.stopPropagation(); removePoiInstance(${p._uid}, '${catName}', '${catName.replace(/[^a-zA-Z0-9]/g, '_')}')">
                            ${trashSvg}
                        </div>
                    </div>`;
                });
                htmlPayload += '</div></div>';
            });
            listBox.innerHTML = htmlPayload;
        }

        function removePoiInstance(uid, catKey, safeCatId) {
            const index = pts.findIndex(item => item._uid === uid);
            if (index > -1) {
                const p = pts[index];
                if(p._marker) layerGroupsRef[catKey].removeLayer(p._marker);
                pts.splice(index, 1);
            }
            const el = document.getElementById('res-item-' + uid);
            if(el) el.remove();
            
            const countEl = document.getElementById('count-' + safeCatId);
            if(countEl) {
                const currentCount = categoryMap[catKey].length - 1;
                countEl.innerText = `(${currentCount})`;
                if (currentCount === 0) { 
                    document.getElementById('cat-block-' + safeCatId).style.display = 'none'; 
                }
            }
            const totalEl = document.getElementById('results-count');
            if(totalEl) totalEl.innerText = parseInt(totalEl.innerText) - 1;
        }

        function toggleCategoryVisibility(catKey, isVisible) {
            if (isVisible) map.addLayer(layerGroupsRef[catKey]);
            else map.removeLayer(layerGroupsRef[catKey]);
        }

        function toggleAccordionCollapse(safeCatId) {
            const panel = document.getElementById('items-' + safeCatId);
            const chev = document.getElementById('chevron-' + safeCatId);
            panel.classList.toggle('collapsed');
            chev.innerText = panel.classList.contains('collapsed') ? '▲' : '▼';
        }

        if (pts.length > 0 && !__IS_STALE__) {
            const bounds = L.featureGroup(pts.map(p => L.marker([p.lat, p.lon]))).getBounds();
            map.fitBounds(bounds.pad(0.1));
        }
    </script>
</body>
</html>
"""

leaflet_html = (leaflet_template
                .replace("__LAT__", str(render_lat))
                .replace("__LON__", str(render_lon))
                .replace("__RADIUS__", str(radius_val))
                .replace("__IS_STALE__", is_stale)
                .replace("__GEOJSON__", geojson_str))

st.components.v1.html(leaflet_html, height=850, scrolling=False)
