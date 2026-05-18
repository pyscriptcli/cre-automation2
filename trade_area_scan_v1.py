import streamlit as st
import requests
import re
import json

# -----------------------------------------------------------------------------
# 1. PREMIUM BRANDING & TRUE FULL SCREEN OVERRIDES
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SPATIAL INTELLIGENCE",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=Montserrat:wght@400;500;700;800&display=swap');
        
        :root {
            --brand-midnight: #003366 !important;
            --brand-gold: #C9AB4C !important;
            --brand-ocean: #1A5A8A !important;
            --brand-ivory: #ffffff !important;
            --soft-shadow: 0 8px 24px rgba(0, 51, 102, 0.08) !important;
        }
        
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: var(--brand-ivory) !important;
            color: var(--brand-midnight) !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: var(--brand-ivory) !important;
            color: var(--brand-midnight) !important;
            border-right: 1px solid rgba(201, 171, 76, 0.4) !important;
            width: 340px !important;
            min-width: 340px !important;
            max-width: 340px !important;
            transform: none !important;
            visibility: visible !important;
            overflow: hidden !important;
            box-shadow: 4px 0 15px rgba(0, 51, 102, 0.03) !important;
        }
        
        [data-testid="collapsedControl"] { display: none !important; }
        ::-webkit-scrollbar { width: 0px !important; background: transparent !important; }
        * { scrollbar-width: none !important; -ms-overflow-style: none !important; }
        
        /* Typography Enforcement */
        p, span, label, h4, h5, h6, .stMarkdown, [data-testid="stExpander"] summary p {
            color: var(--brand-midnight) !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        
        /* Elegant Serif Headers */
        h1, h2, h3, .serif-header {
            font-family: 'Cormorant Garamond', serif !important;
            color: var(--brand-midnight) !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px !important;
        }
        
        [data-testid="stHeader"], header, #stDecoration { display: none !important; }
        
        [data-testid="stAppViewContainer"] {
            display: flex !important; flex-direction: row !important;
            width: 100vw !important; height: 100vh !important; overflow: hidden !important;
        }
        
        [data-testid="stMain"] {
            flex-grow: 1 !important; width: calc(100vw - 340px) !important;
            height: 100vh !important; overflow: hidden !important; margin: 0px !important; padding: 0px !important;
        }
        
        .block-container, [data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"], .stElementContainer {
            padding: 0px !important; margin: 0px !important; max-width: 100% !important; gap: 0rem !important;
        }
        
        iframe { height: 100vh !important; width: 100% !important; border: none !important; display: block !important; }
        
        [data-testid="stSidebarUserContent"] {
            padding-top: 32px !important; padding-left: 24px !important; padding-right: 24px !important;
            height: 100vh !important; overflow-y: auto !important; overflow-x: hidden !important;
        }
        
        /* Input Fields */
        div[data-baseweb="input"], div[data-baseweb="select"] {
            background-color: transparent !important;
            border: none !important; border-bottom: 1px solid rgba(0, 51, 102, 0.2) !important;
            border-radius: 0px !important; box-shadow: none !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        div[data-baseweb="input"]:focus-within { border-bottom: 2px solid var(--brand-gold) !important; }
        
        /* PRIMARY & POPOVER BUTTONS */
        div.stButton > button[kind="secondary"], [data-testid="stPopover"] > button {
            background-color: var(--brand-midnight) !important; 
            border: 1px solid var(--brand-midnight) !important; 
            border-radius: 2px !important; width: 100% !important; padding: 12px !important;
            box-shadow: var(--soft-shadow) !important; transition: all 0.3s ease !important;
        }
        div.stButton > button[kind="secondary"]:hover, [data-testid="stPopover"] > button:hover {
            background-color: var(--brand-ivory) !important;
            border: 1px solid var(--brand-gold) !important;
        }
        
        div.stButton > button[kind="secondary"] p, [data-testid="stPopover"] > button p, [data-testid="stPopover"] > button div {
            color: var(--brand-ivory) !important; font-weight: 700 !important; font-size: 11px !important; text-transform: uppercase !important; letter-spacing: 1px;
            transition: all 0.3s ease !important;
        }
        div.stButton > button[kind="secondary"]:hover p, [data-testid="stPopover"] > button:hover p {
            color: var(--brand-gold) !important;
        }
        
        /* HYPERLINK STYLE FOR CLEAR BUTTON */
        div.stButton > button[kind="primary"] {
            background: transparent !important; border: none !important; color: var(--brand-ocean) !important;
            box-shadow: none !important; padding: 0 !important; margin-top: 8px; display: inline-flex;
        }
        div.stButton > button[kind="primary"] p {
            color: var(--brand-ocean) !important; font-size: 11px !important; font-weight: 700 !important; text-decoration: underline !important; text-transform: uppercase;
        }
        div.stButton > button[kind="primary"]:hover p { color: var(--brand-gold) !important; }
        
        [data-testid="stSidebar"] .st-expander {
            border: 1px solid rgba(0, 51, 102, 0.08) !important; background-color: #Fcfcfc !important;
            border-radius: 2px !important; margin-bottom: 6px !important; overflow: hidden !important;
        }
        .stDeployButton, footer { display:none !important; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. STATE PERSISTENCE & DATA MODELS (UNCHANGED)
# -----------------------------------------------------------------------------
DEFAULT_COORDS = "14.5995, 120.9842"
DEFAULT_RADIUS = 1000

if 'geo_coords' not in st.session_state: st.session_state.geo_coords = DEFAULT_COORDS
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = DEFAULT_RADIUS
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'last_scan_lat' not in st.session_state: st.session_state.last_scan_lat = 14.5995
if 'last_scan_lon' not in st.session_state: st.session_state.last_scan_lon = 120.9842

POI_CONFIG = {
    "COMMERCIAL": [['Corporate Office', '"building"~"office|commercial",i'], ['IT/Tech Center', '"office"~"it|telecommunication",i'], ['Business Center', '"building"="commercial"'], ['Hospital', '"amenity"~"hospital|clinic",i'], ['Hotel', '"tourism"="hotel"'], ['Motel', '"tourism"="motel"']],
    "RETAIL": [['Mall/Department Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"supermarket|grocery",i'], ['Convenience Store', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Hardware', '"shop"~"hardware|doityourself",i'], ['General Shops', '"shop"~"boutique|clothes|shoes",i']],
    "FOOD AND BEVERAGES": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee Shop', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"'], ['Bar/Pub/Nightclub', '"amenity"~"bar|pub|nightclub",i'], ['Bakery/Pastry', '"shop"="bakery"']]
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
    # Elegantly styled header using the Serif font
    st.markdown('''
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="color: #C9AB4C; font-family: 'Montserrat', sans-serif; font-size: 10px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 4px;">Exclusive Advisory</div>
            <div class="serif-header" style="color: #003366; font-size: 32px; font-weight: 600; line-height: 1.1; font-style: italic;">Trade Area<br>Intelligence</div>
            <div style="height: 2px; width: 40px; background-color: #C9AB4C; margin: 15px auto 0;"></div>
        </div>
    ''', unsafe_allow_html=True)
    
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

    st.markdown("<hr style='margin: 20px 0; border: 0; border-top: 1px solid rgba(201, 171, 76, 0.3);'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("EXPORT PROJ", json.dumps(st.session_state.scanned_records), "scan.json", "application/json", use_container_width=True)
    with col2:
        st.download_button("EXPORT KML", compile_features_kml(st.session_state.scanned_records), "POIs.kml", "application/vnd.google-earth.kml+xml", use_container_width=True)


# -----------------------------------------------------------------------------
# 4. ZERO-LATENCY SPATIAL CANVAS (FULL-BLEED SPLIT VIEW)
# -----------------------------------------------------------------------------
geojson_str = json.dumps(st.session_state.scanned_records)
render_lat = lat_coord
render_lon = lon_coord
is_stale = "true" if (lat_coord != st.session_state.last_scan_lat or lon_coord != st.session_state.last_scan_lon) else "false"

# Updated Leaflet JS to strictly use the categorical palette from the design guide
leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #ffffff; overflow: hidden; font-family: 'Montserrat', sans-serif; }
        #map { height: 100vh; width: 100%; }
        
        #minimal-basemap-panel {
            position: absolute; bottom: 24px; left: 16px; z-index: 1000;
            background: rgba(255, 255, 255, 0.95); border-radius: 2px; border: 1px solid rgba(0, 51, 102, 0.1); 
            display: flex; flex-direction: column; padding: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        #minimal-basemap-panel select {
            border: none; border-bottom: 1px solid #C9AB4C; padding: 6px; font-size: 11px; font-weight: 700;
            color: #003366; background: transparent; outline: none; cursor: pointer; width: 100%; font-family: 'Montserrat', sans-serif;
        }
        .minimal-label {
            font-size: 10px; font-weight: 600; padding: 6px 4px 0 4px; display: flex; align-items: center; gap: 6px; cursor: pointer; color: #003366; margin: 0;
        }

        #scan-results-panel {
            position: absolute; top: 16px; right: 16px; z-index: 1000; background: #ffffff;
            width: 300px; max-height: calc(100vh - 32px); border-radius: 2px; border: 1px solid rgba(201, 171, 76, 0.4); 
            display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 8px 24px rgba(0,51,102,0.12);
        }
        .results-header {
            background: #003366; color: #ffffff; padding: 14px 16px; font-size: 11px; font-weight: 800; letter-spacing: 1px;
            display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; border-bottom: 2px solid #C9AB4C;
        }
        .results-list { overflow-y: auto; flex-grow: 1; padding-bottom: 8px; }
        .layer-category-block { border-bottom: 1px solid rgba(0,51,102,0.05); }
        .layer-category-header {
            background: #ffffff; padding: 12px 16px; display: flex; align-items: center; justify-content: space-between;
            cursor: pointer; user-select: none;
        }
        .layer-category-header:hover { background: #f8f9fa; }
        .layer-header-left { display: flex; align-items: center; gap: 10px; font-size: 11px; font-weight: 700; color: #003366; }
        
        .layer-category-items { padding: 0; background: #fafbfc; }
        .layer-category-items.collapsed { display: none !important; }
        
        .results-item {
            padding: 10px 16px 10px 42px; font-size: 11px; font-weight: 500; color: #333;
            cursor: pointer; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border-left: 2px solid transparent;
        }
        .results-item:hover { background: #f0f4f8; border-left: 2px solid #C9AB4C; color: #003366; font-weight: 600; }

        .poi-text-label { background: rgba(255,255,255,0.9); border: 1px solid #C9AB4C; color: #003366; padding: 3px 6px; border-radius: 2px; font-size: 9px; font-weight: 700; font-family: 'Montserrat', sans-serif; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .hide-labels .poi-text-label { display: none !important; }
        .color-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; border: 1px solid rgba(255,255,255,0.8); box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
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
            <input type="checkbox" id="label-toggle-chk" style="margin:0; cursor: pointer;" onchange="toggleLabelsMatrix(this.checked)"> SHOW LABELS
        </label>
    </div>

    <div id="scan-results-panel">
        <div class="results-header">
            <span>Market Scan Index</span>
            <span id="results-count" style="color: #C9AB4C;">0</span>
        </div>
        <div class="results-list" id="results-list-box"></div>
    </div>

    <script>
        const map = L.map('map', { zoomControl: true, attributionControl: false }).setView([__LAT__, __LON__], 14);
        map.zoomControl.setPosition('topleft');
        
        const basemaps = {
            osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }),
            satellite: L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', { maxZoom: 20 }),
            carto: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 })
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
        
        // Branded Center Icon
        const starIcon = L.divIcon({
            className: 'custom-center-icon',
            html: '<div style="background-color: #003366; color: #C9AB4C; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; border: 2px solid #C9AB4C; box-shadow: 0 4px 10px rgba(0,51,102,0.3);">★</div>',
            iconSize: [28, 28], iconAnchor: [14, 14]
        });
        const centerMarker = L.marker([__LAT__, __LON__], { icon: starIcon, zIndexOffset: 10000 }).addTo(map);
        
        const radiusCircle = L.circle([__LAT__, __LON__], {
            radius: __RADIUS__, color: "#003366", weight: 1.5, fillColor: "#003366", fillOpacity: 0.05, dashArray: "4 4"
        }).addTo(map);
        
        const pts = __GEOJSON__;
        const categoryMap = {};
        const layerGroupsRef = {};
        
        // Official 10-Series Categorical Palette from Brand Guide
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
                    radius: 6, fillColor: pColor, color: "#ffffff", weight: 1.5, opacity: 1, fillOpacity: 0.95
                }).bindPopup("<b style='color:#003366; font-family:Montserrat;'>" + p.name + "</b><br><span style='color:#666; font-size:10px;'>" + p.type + "</span>");
                if (p.name && p.name !== 'Unknown') {
                    marker.bindTooltip(p.name, { permanent: true, direction: 'top', offset: [0, -8], className: 'poi-text-label' });
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
                                <span>${catName} <span style="color: #999; font-size: 10px; font-weight: 500;">(${categoryMap[catName].length})</span></span>
                            </div>
                            <span id="chevron-${catName}" style="font-size: 10px; color: #C9AB4C;">▼</span>
                        </div>
                        <div class="layer-category-items" id="items-${catName}">
                `;
                categoryMap[catName].forEach(p => {
                    htmlPayload += `<div class="results-item" onclick="map.flyTo([${p.lat}, ${p.lon}], 18);">${p.name || 'Unknown'}</div>`;
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
