import streamlit as st
import requests
import re
import json

# -----------------------------------------------------------------------------
# 1. PRIME BRANDED THEME & TYPOGRAPHY OVERRIDES
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TRADE AREA SCAN | PRIME",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=Montserrat:wght@400;600;800&display=swap');

        :root {
            --midnight-blue: #003366 !important; 
            --prime-gold: #C9AB4C !important; 
            --white-clean: #ffffff !important;
            --grid-line: rgba(128, 128, 128, 0.10) !important;
            --soft-shadow: 0 4px 16px rgba(0, 51, 102, 0.12) !important;
        }
        
        /* Base Typography: Arial/Helvetica for standard reading per guidelines */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: var(--white-clean) !important;
            color: var(--midnight-blue) !important;
            font-family: 'Arial', 'Helvetica', sans-serif !important;
        }
        
        /* Headers and UI Elements: Montserrat */
        h1, h2, h3, h4, h5, h6, button, [data-testid="stExpander"] summary p, label {
            font-family: 'Montserrat', sans-serif !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: var(--white-clean) !important;
            color: var(--midnight-blue) !important;
            border-right: 1px solid var(--grid-line) !important;
            width: 320px !important;
            min-width: 320px !important;
            max-width: 320px !important;
            transform: none !important;
            visibility: visible !important;
            overflow: hidden !important;
            box-shadow: 2px 0 10px rgba(0, 51, 102, 0.05) !important;
        }
        
        [data-testid="collapsedControl"] { display: none !important; }
        ::-webkit-scrollbar { width: 0px !important; background: transparent !important; }
        * { scrollbar-width: none !important; -ms-overflow-style: none !important; }
        
        [data-testid="stHeader"], header, #stDecoration { display: none !important; }
        
        [data-testid="stAppViewContainer"] {
            display: flex !important; flex-direction: row !important;
            width: 100vw !important; height: 100vh !important; overflow: hidden !important;
        }
        
        [data-testid="stMain"] {
            flex-grow: 1 !important; width: calc(100vw - 320px) !important;
            height: 100vh !important; overflow: hidden !important; margin: 0px !important; padding: 0px !important;
        }
        
        .block-container, [data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"], .stElementContainer {
            padding: 0px !important; margin: 0px !important; max-width: 100% !important; gap: 0rem !important;
        }
        
        iframe { height: 100vh !important; width: 100% !important; border: none !important; display: block !important; }
        
        [data-testid="stSidebarUserContent"] {
            padding-top: 24px !important; padding-left: 16px !important; padding-right: 16px !important;
            height: 100vh !important; overflow-y: auto !important; overflow-x: hidden !important;
        }
        
        div[data-baseweb="input"], div[data-baseweb="select"] {
            background-color: transparent !important;
            border: none !important; border-bottom: 2px solid var(--grid-line) !important;
            border-radius: 0px !important; box-shadow: none !important;
        }
        div[data-baseweb="input"]:focus-within { border-bottom: 2px solid var(--midnight-blue) !important; }
        
        /* BUTTONS - Montserrat, Midnight Base with Gold Hover */
        div.stButton > button[kind="secondary"], [data-testid="stPopover"] > button {
            background-color: var(--midnight-blue) !important; 
            border: none !important; border-radius: 4px !important; width: 100% !important; padding: 8px !important;
            box-shadow: var(--soft-shadow) !important; transition: all 0.2s ease !important;
        }
        div.stButton > button[kind="secondary"] p, [data-testid="stPopover"] > button p, div.stDownloadButton > button p {
            color: var(--white-clean) !important; font-weight: 800 !important; font-size: 11px !important; 
            text-transform: uppercase !important; font-family: 'Montserrat', sans-serif !important;
        }
        div.stButton > button[kind="secondary"]:hover, [data-testid="stPopover"] > button:hover {
            background-color: var(--prime-gold) !important;
        }
        
        div.stDownloadButton > button {
            background-color: var(--midnight-blue) !important; 
            border: none !important; border-radius: 4px !important; width: 100% !important; padding: 4px !important;
            box-shadow: var(--soft-shadow) !important; transition: all 0.2s ease !important;
        }
        div.stDownloadButton > button:hover { background-color: var(--prime-gold) !important; }
        
        /* HYPERLINK STYLE CLEAR BUTTON */
        div.stButton > button[kind="primary"] {
            background: transparent !important; border: none !important; color: var(--midnight-blue) !important;
            box-shadow: none !important; padding: 0 !important; margin-top: 4px; display: inline-flex;
        }
        div.stButton > button[kind="primary"] p {
            color: var(--midnight-blue) !important; font-size: 11px !important; font-weight: 800 !important; 
            text-decoration: underline !important; text-transform: uppercase; font-family: 'Montserrat', sans-serif !important;
        }
        div.stButton > button[kind="primary"]:hover p { color: var(--prime-gold) !important; }
        
        [data-testid="stSidebar"] .st-expander {
            border: 1px solid var(--grid-line) !important; background-color: var(--white-clean) !important;
            border-radius: 4px !important; margin-bottom: 4px !important; overflow: hidden !important;
        }
        .stDeployButton, footer { display:none !important; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. STATE PERSISTENCE & DATA MODELS
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
    "RETAIL": [['Mall/Department Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"supermarket|grocery",i'], ['Convenience Store', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"']],
    "FOOD AND BEVERAGES": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee Shop', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"']],
    "INDUSTRIAL": [['Ports & Terminals', '"industrial"="port"'], ['Manufacturing Plants', '"industrial"~"factory|manufacturing|processing",i'], ['Warehouses', '"building"~"warehouse|depot",i']],
    "GOVERNMENT": [['City Hall', '"amenity"="townhall"'], ['Police Station', '"amenity"="police"'], ['Fire Station', '"amenity"="fire_station"']]
}

def compile_features_kml(features):
    kml = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scanned POIs</name>'
    for f in features:
        name = f.get('name', 'Asset').replace("&", "&").replace("<", "<").replace(">", ">")
        class_type = f.get('type', 'Node').replace("&", "&").replace("<", "<").replace(">", ">")
        kml += f"<Placemark><name>{name}</name><description>{class_type}</description><Point><coordinates>{f['lon']},{f['lat']},0</coordinates></Point></Placemark>"
    return kml + '</Document></kml>'

# -----------------------------------------------------------------------------
# 3. SIDEBAR WORKSPACE
# -----------------------------------------------------------------------------
with st.sidebar:
    # Title uses Cormorant Garamond for high-level editorial hierarchy
    st.markdown('<div style="font-family: \'Cormorant Garamond\', serif; color: #003366; font-size: 24px; font-weight: 700; letter-spacing: 1px; margin-bottom: 24px; text-align: center;">PRIME TRADE SCAN</div>', unsafe_allow_html=True)
    
    coords_val = st.text_input("COORDINATES", key="geo_coords")
    radius_val = st.number_input("RADIUS (METERS)", min_value=100, max_value=50000, key="geo_radius", step=100)

    coord_match = re.match(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", coords_val)
    lat_coord, lon_coord = (float(coord_match.group(1)), float(coord_match.group(2))) if coord_match else (14.5995, 120.9842)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    search_query = st.text_input("SEARCH TAGS", placeholder="Search...").lower()
    
    selected_tags = []
    for cat_name, node_items in POI_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for label, tag in matched:
                    if st.checkbox(label, key=f"chk_{cat_name}_{label}"): selected_tags.append(tag)

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("RUN SPATIAL SCAN", type="secondary", use_container_width=True):
        if not selected_tags:
            st.error("Select ≥ 1 layer.")
        else:
            url = "https://overpass-api.de/api/interpreter"
            statements = "\n".join([f"  nwr[{tag}](around:{radius_val},{lat_coord},{lon_coord});" for tag in selected_tags])
            ql = f"[out:json][timeout:90];(\n{statements}\n);\nout center;"
            with st.spinner("Extracting nodes..."):
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
                except Exception as e: st.error("Timeout")

    if st.button("Clear All POIs", type="primary"):
        st.session_state.scanned_records = []
        st.rerun()

    st.markdown("<hr style='margin: 16px 0; border: 0; border-top: 1px solid rgba(128, 128, 128, 0.1);'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("EXPORT JSON", json.dumps(st.session_state.scanned_records), "scan.json", "application/json", use_container_width=True)
    with col2:
        st.download_button("EXPORT KML", compile_features_kml(st.session_state.scanned_records), "POIs.kml", "application/vnd.google-earth.kml+xml", use_container_width=True)

# -----------------------------------------------------------------------------
# 4. ZERO-LATENCY SPATIAL CANVAS (HTML/JS)
# -----------------------------------------------------------------------------
geojson_str = json.dumps(st.session_state.scanned_records)
render_lat = lat_coord
render_lon = lon_coord
is_stale = "true" if (lat_coord != st.session_state.last_scan_lat or lon_coord != st.session_state.last_scan_lon) else "false"

leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #ffffff; overflow: hidden; font-family: 'Arial', 'Helvetica', sans-serif; }
        #map { height: 100vh; width: 100%; }
        
        #minimal-basemap-panel {
            position: absolute; bottom: 20px; left: 10px; z-index: 1000;
            background: #ffffff; border-radius: 4px; border: 1px solid rgba(128,128,128,0.1); background-clip: padding-box;
            display: flex; flex-direction: column; padding: 2px; font-family: 'Montserrat', sans-serif;
        }
        #minimal-basemap-panel select {
            border: none; border-bottom: 1px solid rgba(128,128,128,0.1); padding: 4px; font-size: 11px; font-weight: bold;
            color: #003366; background: transparent; outline: none; cursor: pointer; width: 100%; font-family: 'Montserrat', sans-serif;
        }
        .minimal-label {
            font-size: 10px; font-weight: 600; padding: 4px; display: flex; align-items: center; gap: 4px; cursor: pointer; color: #333; margin: 0;
        }

        #scan-results-panel {
            position: absolute; top: 10px; right: 10px; z-index: 1000; background: #ffffff;
            width: 280px; max-height: calc(100vh - 20px); border-radius: 4px; border: 1px solid rgba(128,128,128,0.1); background-clip: padding-box;
            display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 12px rgba(0,51,102,0.1);
        }
        .results-header {
            background: #003366; color: #ffffff; padding: 12px 14px; font-size: 13px; font-weight: 800;
            display: flex; justify-content: space-between; align-items: center; text-transform: uppercase;
            font-family: 'Montserrat', sans-serif;
        }
        .results-list { overflow-y: auto; flex-grow: 1; padding-bottom: 8px; }
        .layer-category-block { border-bottom: 1px solid rgba(128,128,128,0.1); }
        .layer-category-header {
            background: #ffffff; padding: 10px 14px; display: flex; align-items: center; justify-content: space-between;
            cursor: pointer; user-select: none; font-family: 'Montserrat', sans-serif;
        }
        .layer-category-header:hover { background: #fafafa; }
        .layer-header-left { display: flex; align-items: center; gap: 8px; font-size: 11px; font-weight: 600; color: #003366; }
        
        .layer-category-items { padding: 0; background: #fafafa; }
        .layer-category-items.collapsed { display: none !important; }
        
        .results-item {
            padding: 8px 14px 8px 34px; font-size: 11px; color: #333;
            cursor: pointer; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .results-item:hover { background: #eaeaea; }

        /* Typography Override per guidelines: Arial 10px, #888780 */
        .poi-text-label { background: #fff; border: 1px solid rgba(128,128,128,0.1); padding: 2px 4px; border-radius: 2px; font-size: 10px; font-family: 'Arial', sans-serif; color: #888780; white-space: nowrap; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .hide-labels .poi-text-label { display: none !important; }
        
        /* 10x10px squares per Legend rules */
        .color-dot { width: 10px; height: 10px; border-radius: 2px; display: inline-block; border: none; }

    </style>
</head>
<body>
    <div id="map"></div>

    <div id="minimal-basemap-panel">
        <select id="basemap-select" onchange="switchActiveBasemap(this.value)">
            <option value="carto">Carto Light</option>
            <option value="osm">OpenStreetMap</option>
            <option value="satellite">Google Satellite</option>
        </select>
        <label class="minimal-label" for="label-toggle-chk">
            <input type="checkbox" id="label-toggle-chk" style="margin:0; cursor: pointer;" onchange="toggleLabelsMatrix(this.checked)"> Show Labels
        </label>
    </div>

    <div id="scan-results-panel">
        <div class="results-header">
            <span>INDEX</span>
            <span id="results-count">0</span>
        </div>
        <div class="results-list" id="results-list-box"></div>
        <div style="padding: 8px; text-align: center; font-size: 8.5px; font-style: italic; color: #999999;">PRIME Analytics Framework</div>
    </div>

    <script>
        const map = L.map('map', { zoomControl: true, attributionControl: false }).setView([__LAT__, __LON__], 14);
        map.zoomControl.setPosition('topleft');
        
        const basemaps = {
            carto: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 }),
            osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }),
            satellite: L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', { maxZoom: 20 })
        };
        
        let activeBasemapKey = localStorage.getItem('ts_persistent_basemap') || 'carto';
        if (!basemaps[activeBasemapKey]) activeBasemapKey = 'carto';
        document.getElementById('basemap-select').value = activeBasemapKey;
        basemaps[activeBasemapKey].addTo(map);
        
        function switchActiveBasemap(targetKey) {
            map.removeLayer(basemaps[activeBasemapKey]);
            basemaps[targetKey].addTo(map);
            activeBasemapKey = targetKey;
            localStorage.setItem('ts_persistent_basemap', targetKey);
        }
        
        let labelsActive = localStorage.getItem('ts_persistent_labels') !== 'false';
        document.getElementById('label-toggle-chk').checked = labelsActive;
        if (!labelsActive) document.getElementById('map').classList.add('hide-labels');
        
        function toggleLabelsMatrix(isShown) {
            if (isShown) document.getElementById('map').classList.remove('hide-labels');
            else document.getElementById('map').classList.add('hide-labels');
            localStorage.setItem('ts_persistent_labels', isShown);
        }
        
        /* Center point marked by PRIME Gold Anchor */
        const starIcon = L.divIcon({
            className: 'custom-center-icon',
            html: '<div style="background-color: #C9AB4C; color: #003366; width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; border: 2px solid #ffffff; box-shadow: 0 2px 6px rgba(0,0,0,0.5);">★</div>',
            iconSize: [26, 26], iconAnchor: [13, 13]
        });
        L.marker([__LAT__, __LON__], { icon: starIcon, zIndexOffset: 10000 }).addTo(map);
        
        L.circle([__LAT__, __LON__], {
            radius: __RADIUS__, color: "#003366", weight: 2, fillColor: "#003366", fillOpacity: 0.05
        }).addTo(map);
        
        const pts = __GEOJSON__;
        const categoryMap = {};
        const layerGroupsRef = {};
        
        // PRIME 9-Series Categorical Palette (S1 to S9) - S10 Champagne Excluded
        const catPalette = ["#003366", "#C9AB4C", "#1A5A8A", "#A8862E", "#3D7DA8", "#7A5C10", "#6A94B0", "#D4B85A", "#001F3F"];
        const categoryColors = {}; let colorIndex = 0;
        
        pts.forEach(p => {
            const layerKey = p.type || 'Unclassified';
            if (!categoryMap[layerKey]) {
                categoryMap[layerKey] = []; categoryColors[layerKey] = catPalette[colorIndex % catPalette.length]; colorIndex++;
            }
            categoryMap[layerKey].push(p);
        });
        
        Object.keys(categoryMap).forEach(key => {
            layerGroupsRef[key] = L.layerGroup().addTo(map);
            const pColor = categoryColors[key];
            categoryMap[key].forEach(p => {
                const marker = L.circleMarker([p.lat, p.lon], {
                    radius: 5, fillColor: pColor, color: "#ffffff", weight: 1, opacity: 1, fillOpacity: 0.95
                }).bindPopup("<div style='font-family: Montserrat; font-size: 11px;'><b>" + p.name + "</b><br>" + p.type + "</div>");
                
                if (p.name && p.name !== 'Unknown') {
                    marker.bindTooltip(p.name, { permanent: true, direction: 'top', offset: [0, -6], className: 'poi-text-label' });
                }
                marker.addTo(layerGroupsRef[key]);
            });
        });

        const listBox = document.getElementById('results-list-box');
        document.getElementById('results-count').innerText = pts.length;
        
        if (pts.length > 0) {
            let htmlPayload = '';
            Object.keys(categoryMap).forEach(catName => {
                const dotColor = categoryColors[catName];
                htmlPayload += `
                    <div class="layer-category-block">
                        <div class="layer-category-header" onclick="toggleAccordionCollapse('${catName}')">
                            <div class="layer-header-left">
                                <input type="checkbox" checked onclick="event.stopPropagation(); toggleCategoryVisibility('${catName}', this.checked)">
                                <span class="color-dot" style="background-color: ${dotColor};"></span>
                                <span>${catName} <span style="color: #888; font-size: 10px;">(${categoryMap[catName].length})</span></span>
                            </div>
                            <span id="chevron-${catName}" style="font-size: 10px; color: #003366;">▼</span>
                        </div>
                        <div class="layer-category-items" id="items-${catName}">
                `;
                categoryMap[catName].forEach(p => {
                    htmlPayload += `<div class="results-item" onclick="map.flyTo([${p.lat}, ${p.lon}], 17);">${p.name || 'Unknown'}</div>`;
                });
                htmlPayload += '</div></div>';
            });
            listBox.innerHTML = htmlPayload;
        }

        function toggleCategoryVisibility(catKey, isVisible) {
            if (isVisible) map.addLayer(layerGroupsRef[catKey]);
            else map.removeLayer(layerGroupsRef[catKey]);
        }

        function toggleAccordionCollapse(catKey) {
            const panel = document.getElementById('items-' + catKey);
            const chev = document.getElementById('chevron-' + catKey);
            panel.classList.toggle('collapsed');
            chev.innerText = panel.classList.contains('collapsed') ? '▲' : '▼';
        }

        if (pts.length > 0 && !__IS_STALE__) {
            const bounds = L.featureGroup([L.marker([__LAT__, __LON__]), ...pts.map(p => L.marker([p.lat, p.lon]))]).getBounds();
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
