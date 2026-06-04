import streamlit as st
import requests
import re
import json
import os
import io
import pandas as pd
import numpy as np

# --- PROGRAMMATIC LIGHT MODE LOCK ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\n")

# -----------------------------------------------------------------------------
# 1. BRANDED BICHROMATIC THEME & OVERRIDES (OPEN NODE)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Open Node | Spatial Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        :root {
            --brand-primary: #111827 !important;
            --brand-accent: #3B82F6 !important;
            --white-clean: #ffffff !important;
            --bg-offwhite: #F3F4F6 !important;
            --text-muted: #6B7280 !important;
            --soft-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        }
        
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: var(--white-clean) !important;
            color: var(--brand-primary) !important;
            font-family: 'Inter', sans-serif !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: var(--bg-offwhite) !important;
            color: var(--brand-primary) !important;
            border-right: 1px solid #E5E7EB !important;
            width: 320px !important;
            min-width: 320px !important;
            max-width: 320px !important;
        }
        
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"], [data-testid="stHeader"], header, #stDecoration { display: none !important; }
        ::-webkit-scrollbar { width: 0px !important; background: transparent !important; }
        
        [data-testid="stAppViewContainer"] { display: flex !important; flex-direction: row !important; width: 100vw !important; height: 100vh !important; overflow: hidden !important; }
        [data-testid="stMain"] { flex-grow: 1 !important; width: calc(100vw - 320px) !important; height: 100vh !important; overflow: hidden !important; margin: 0px !important; padding: 0px !important; }
        .block-container { padding: 0px !important; margin: 0px !important; max-width: 100% !important; gap: 0rem !important; }
        iframe { height: 100vh !important; width: 100% !important; border: none !important; display: block !important; }
        
        div[data-baseweb="input"], div[data-baseweb="select"] { background-color: #ffffff !important; border: 1px solid #D1D5DB !important; border-radius: 4px !important; box-shadow: none !important; padding: 2px !important;}
        div[data-baseweb="input"]:focus-within { border-color: var(--brand-accent) !important; box-shadow: 0 0 0 1px var(--brand-accent) !important; }
        
        div.stButton > button { border-radius: 4px !important; font-weight: 600 !important; font-size: 11px !important; text-transform: uppercase !important; letter-spacing: 0.5px; padding: 8px 16px !important; width: 100% !important; transition: all 0.2s ease !important; border: none !important; }
        div.stButton > button[kind="secondary"] { background-color: var(--brand-primary) !important; color: var(--white-clean) !important; box-shadow: var(--soft-shadow) !important; }
        div.stButton > button[kind="secondary"]:hover { background-color: var(--brand-accent) !important; }
        div.stButton > button[kind="primary"] { background-color: transparent !important; color: var(--text-muted) !important; border: 1px solid #D1D5DB !important; }
        div.stButton > button[kind="primary"]:hover { background-color: #FEE2E2 !important; color: #DC2626 !important; border-color: #FCA5A5 !important; }
        
        div.stDownloadButton > button { background-color: #E5E7EB !important; color: var(--brand-primary) !important; border-radius: 4px !important; width: 100% !important; font-size: 10px !important; font-weight: 600 !important; text-transform: uppercase !important; border: none !important;}
        div.stDownloadButton > button:hover { background-color: #D1D5DB !important; }
        
        .brand-title { font-family: 'Inter', sans-serif !important; font-weight: 800; color: var(--brand-primary); font-size: 24px; text-align: left; padding-bottom: 12px; margin-bottom: 20px; letter-spacing: -0.5px; border-bottom: 2px solid var(--brand-primary); }
        .stTextInput label p, .stNumberInput label p { font-size: 10px !important; font-weight: 600 !important; letter-spacing: 0.5px; color: var(--text-muted) !important; text-transform: uppercase; }
        
        [data-testid="stSidebar"] .st-expander { border: 1px solid #E5E7EB !important; background-color: #ffffff !important; border-radius: 4px !important; margin-bottom: 4px !important; box-shadow: none !important;}
        [data-testid="stSidebar"] .st-expander summary p { font-size: 11px !important; font-weight: 600 !important; color: var(--brand-primary) !important; }
        .stCheckbox label p { font-size: 11px !important; font-weight: 500 !important; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. STATE PERSISTENCE & CONFIG
# -----------------------------------------------------------------------------
DEFAULT_COORDS = "14.5995, 120.9842"
DEFAULT_RADIUS = 1000

if 'geo_coords' not in st.session_state: st.session_state.geo_coords = DEFAULT_COORDS
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = DEFAULT_RADIUS
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'last_scan_lat' not in st.session_state: st.session_state.last_scan_lat = 14.5995
if 'last_scan_lon' not in st.session_state: st.session_state.last_scan_lon = 120.9842

POI_CONFIG = {
    "COMMERCIAL": [['Corporate Office', '"building"~"office|commercial",i'], ['Business Center', '"building"="commercial"'], ['Hospital', '"amenity"~"hospital|clinic",i'], ['Hotel', '"tourism"="hotel"']],
    "RESIDENTIAL": [['Apartments', '"building"="apartments"'], ['House', '"building"="house"'], ['Residential Area', '"landuse"="residential"']],
    "RETAIL": [['Mall/Department Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"supermarket|grocery",i'], ['Convenience Store', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"']],
    "FOOD_BEVERAGE": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee Shop', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"']]
}

# -----------------------------------------------------------------------------
# 3. EXPORT MODULE (CONTEXTILY & MATPLOTLIB)
# -----------------------------------------------------------------------------
def generate_static_report():
    if not st.session_state.scanned_records:
        st.error("No data to export. Run a scan first.")
        return None
        
    try:
        import geopandas as gpd
        import matplotlib.pyplot as plt
        import contextily as cx
        from shapely.geometry import Point
        
        with st.spinner("Generating High-Resolution Static Report..."):
            records = st.session_state.scanned_records
            center_lat, center_lon = st.session_state.last_scan_lat, st.session_state.last_scan_lon
            radius = st.session_state.geo_radius
            
            # DataFrame preparation
            df = pd.DataFrame(records)
            geometry = [Point(xy) for xy in zip(df['lon'], df['lat'])]
            gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
            gdf = gdf.to_crs(epsg=3857) # Convert to Web Mercator for Contextily
            
            center_pt = gpd.GeoDataFrame(geometry=[Point(center_lon, center_lat)], crs="EPSG:4326").to_crs(epsg=3857)
            radius_poly = center_pt.geometry.buffer(radius)
            
            fig, ax = plt.subplots(figsize=(12, 12), dpi=300)
            
            # Plot Radius Buffer
            gpd.GeoSeries(radius_poly).plot(ax=ax, color='#3B82F6', alpha=0.1, edgecolor='#111827', linewidth=2)
            
            # Plot POIs by Category
            unique_types = gdf['type'].unique()
            colors = plt.cm.tab20(np.linspace(0, 1, len(unique_types)))
            
            for p_type, color in zip(unique_types, colors):
                subset = gdf[gdf['type'] == p_type]
                subset.plot(ax=ax, color=color, markersize=40, label=p_type, edgecolor='white', linewidth=0.5)
            
            # Plot Center
            center_pt.plot(ax=ax, color='#DC2626', marker='*', markersize=300, edgecolor='white', linewidth=1.5, label='Target Center', zorder=10)
            
            # Basemap
            cx.add_basemap(ax, source=cx.providers.CartoDB.Positron)
            
            # Aesthetics
            ax.set_axis_off()
            ax.set_title(f"Open Node Spatial Report\nRadius: {radius}m | Total POIs: {len(records)}", fontsize=16, fontweight='bold', pad=20, fontname='Arial')
            
            # Legend Configuration
            box = ax.get_position()
            ax.set_position([box.x0, box.y0, box.width * 0.85, box.height])
            ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8, title="Categories", title_fontsize=10, frameon=True, shadow=True)
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.5, facecolor='white')
            buf.seek(0)
            plt.close(fig)
            return buf
            
    except ImportError:
        st.error("Missing libraries: geopandas, matplotlib, or contextily.")
        return None
    except Exception as e:
        st.error(f"Render Error: {str(e)}")
        return None

# -----------------------------------------------------------------------------
# 4. SIDEBAR WORKSPACE
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="brand-title">OPEN NODE</div>', unsafe_allow_html=True)
    
    # SCAN BUTTON MOVED TO TOP
    if st.button("SCAN AREA", type="secondary", use_container_width=True, key="scan_btn_top"):
        selected_tags = []
        for key, val in st.session_state.items():
            if key.startswith("chk_") and val is True:
                # Extract tag string
                layer_name = key.split("_")[-1]
                for cat, items in POI_CONFIG.items():
                    for item in items:
                        if item[0] == layer_name: selected_tags.append(item[1])

        if not selected_tags:
            st.error("Select ≥ 1 layer.")
        else:
            lat_coord, lon_coord = float(st.session_state.geo_coords.split(',')[0]), float(st.session_state.geo_coords.split(',')[1])
            radius_val = st.session_state.geo_radius
            records = []
            
            with st.spinner("Executing Spatial Extraction (OSMnx / Overpass)..."):
                engine_used = "Overpass"
                try:
                    # PRIMARY ENGINE: OSMnx (Attempting extraction if library exists)
                    import osmnx as ox
                    # Setup broad tags for osmnx to avoid regex parsing issues on strict dicts
                    ox_tags = {'amenity': True, 'building': True, 'shop': True, 'leisure': True, 'tourism': True}
                    gdf = ox.features_from_point((lat_coord, lon_coord), tags=ox_tags, dist=radius_val)
                    
                    if not gdf.empty:
                        engine_used = "OSMnx"
                        for idx, row in gdf.iterrows():
                            # Simplified local filtering map based on existence of columns
                            p_type = row.get('amenity') or row.get('shop') or row.get('building') or 'Node'
                            if pd.notna(p_type):
                                e_lat = row.geometry.centroid.y if row.geometry.type != 'Point' else row.geometry.y
                                e_lon = row.geometry.centroid.x if row.geometry.type != 'Point' else row.geometry.x
                                records.append({
                                    "lat": float(e_lat), 
                                    "lon": float(e_lon), 
                                    "name": str(row.get('name', 'Unknown')) if 'name' in row else 'Unknown', 
                                    "type": str(p_type)
                                })
                except Exception as e:
                    # SECONDARY FALLBACK: Raw Overpass QL
                    engine_used = "Overpass Fallback"
                    url = "https://overpass-api.de/api/interpreter"
                    statements = "\n".join([f"  nwr[{tag}](around:{radius_val},{lat_coord},{lon_coord});" for tag in selected_tags])
                    ql = f"[out:json][timeout:90];(\n{statements}\n);\nout center;"
                    res = requests.post(url, data={"data": ql}, headers={"User-Agent": "OpenNode/4.0"}, timeout=100)
                    if res.status_code == 200:
                        for el in res.json().get('elements', []):
                            e_lat = el.get('lat') or el.get('center', {}).get('lat')
                            e_lon = el.get('lon') or el.get('center', {}).get('lon')
                            if e_lat and e_lon:
                                tags = el.get('tags', {})
                                records.append({"lat": e_lat, "lon": e_lon, "name": tags.get('name', 'Unknown'), "type": tags.get('amenity') or tags.get('shop') or tags.get('building') or 'Node'})
                
                if records:
                    st.session_state.scanned_records = records
                    st.session_state.last_scan_lat = lat_coord
                    st.session_state.last_scan_lon = lon_coord
                    st.success(f"Extracted {len(records)} POIs via {engine_used}")
                    st.rerun()
                else:
                    st.warning("No POIs found in radius.")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    
    # Dual-purpose Location Search & Coordinates Input
    location_input = st.text_input("COORDINATES", value=st.session_state.geo_coords, key="geo_coords_input")
    radius_val = st.number_input("RADIUS (METERS)", min_value=100, max_value=50000, value=st.session_state.geo_radius, key="geo_radius_input", step=100)
    st.session_state.geo_radius = radius_val

    coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", location_input)
    if coord_match:
        lat_coord, lon_coord = float(coord_match.group(1)), float(coord_match.group(2))
        st.session_state.geo_coords = location_input
    else:
        if location_input and location_input != st.session_state.get('last_geocoded_query', ''):
            with st.spinner("Geocoding..."):
                try:
                    headers = {'User-Agent': 'OpenNode/4.0'}
                    osm_url = f"https://nominatim.openstreetmap.org/search?q={location_input}&format=json&limit=1"
                    resp = requests.get(osm_url, headers=headers, timeout=10).json()
                    if resp:
                        new_lat = float(resp[0]['lat'])
                        new_lon = float(resp[0]['lon'])
                        st.session_state.geo_coords = f"{new_lat:.5f}, {new_lon:.5f}"
                        st.session_state.last_geocoded_query = location_input
                        st.rerun()
                except Exception: pass
        lat_coord, lon_coord = float(st.session_state.geo_coords.split(',')[0]), float(st.session_state.geo_coords.split(',')[1])

    st.markdown("<hr style='margin: 16px 0; border: 0; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)
    
    st.markdown("<div style='font-weight: 700; font-size: 11px; margin-bottom: 8px; color: #6B7280; letter-spacing: 1px;'>LAYER SELECTION</div>", unsafe_allow_html=True)
    for cat_name, node_items in POI_CONFIG.items():
        with st.expander(cat_name.replace("_", " "), expanded=False):
            for label, tag in node_items:
                st.checkbox(label, key=f"chk_{cat_name}_{label}")

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("CLEAR CANVAS", type="primary", key="clear_btn"):
        st.session_state.scanned_records = []
        st.rerun()

    st.markdown("<hr style='margin: 16px 0; border: 0; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)
    
    # EXPORT BUTTON SEQUENCE
    if st.button("GENERATE STATIC REPORT (PNG)", type="secondary"):
        img_buffer = generate_static_report()
        if img_buffer:
            st.download_button(
                label="DOWNLOAD REPORT PNG",
                data=img_buffer,
                file_name=f"OpenNode_Report_{lat_coord}_{lon_coord}.png",
                mime="image/png",
                use_container_width=True
            )

    col1, col2 = st.columns(2)
    with col1:
        st.download_button("DATA (JSON)", json.dumps(st.session_state.scanned_records), "OpenNode.json", "application/json", use_container_width=True)
    with col2:
        st.download_button("DATA (CSV)", pd.DataFrame(st.session_state.scanned_records).to_csv(index=False) if st.session_state.scanned_records else "", "OpenNode.csv", "text/csv", use_container_width=True)

# -----------------------------------------------------------------------------
# 5. ZERO-LATENCY SPATIAL CANVAS (LEAFLET WITH EMBEDDED CONFIGURATOR)
# -----------------------------------------------------------------------------
geojson_str = json.dumps(st.session_state.scanned_records)
render_lat = lat_coord
render_lon = lon_coord

leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #ffffff; overflow: hidden; font-family: 'Inter', sans-serif; }
        #map { height: 100vh; width: 100%; }
        
        #scan-results-panel { 
            position: absolute; top: 10px; right: 10px; z-index: 1000; background: #ffffff; width: 300px; 
            max-height: calc(100vh - 20px); border-radius: 6px; border: 1px solid #E5E7EB; 
            display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); 
        }
        .results-header { background: #111827; color: #ffffff; padding: 12px; font-size: 11px; font-weight: 700; display: flex; justify-content: space-between; align-items: center; letter-spacing: 0.5px; }
        
        .panel-section-title { font-size: 10px; font-weight: 700; color: #6B7280; text-transform: uppercase; padding: 12px 12px 4px 12px; letter-spacing: 1px; border-top: 1px solid #E5E7EB; margin-top: 8px;}
        
        /* MARKER CONFIGURATION CONTROLS */
        .config-row { padding: 8px 12px; display: flex; justify-content: space-between; align-items: center; font-size: 11px; font-weight: 500; color: #111827; }
        .config-row select, .config-row input[type="range"] { width: 120px; border: 1px solid #D1D5DB; border-radius: 4px; padding: 4px; font-family: 'Inter', sans-serif; font-size: 10px;}
        .config-row input[type="file"] { width: 120px; font-size: 9px; }
        
        .results-list { overflow-y: auto; flex-grow: 1; padding-bottom: 8px; border-top: 1px solid #E5E7EB; margin-top: 8px;}
        .layer-category-header { background: #ffffff; padding: 8px 12px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; border-bottom: 1px solid #F3F4F6; }
        .layer-category-header:hover { background: #F9FAFB; }
        .layer-header-left { display: flex; align-items: center; gap: 8px; font-size: 11px; font-weight: 600; color: #111827; }
        .layer-category-items { padding: 0; background: #F9FAFB; }
        .layer-category-items.collapsed { display: none !important; }
        
        .poi-text-label { background: #111827; color: #fff; border: none; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; white-space: nowrap; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
        .hide-labels .poi-text-label { display: none !important; }
        .color-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
        
        /* Custom Marker CSS */
        .custom-marker-dot { border-radius: 50%; border: 2px solid #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }
        .custom-marker-pin { display: flex; align-items: center; justify-content: center; }
        .custom-marker-img { border-radius: 50%; object-fit: cover; border: 2px solid #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.3); background: white;}
    </style>
</head>
<body>
    <div id="map"></div>

    <div id="scan-results-panel">
        <div class="results-header">
            <span>LAYERS & CONFIGURATION</span>
            <span id="results-count" style="color:#3B82F6;">0</span>
        </div>
        
        <div class="panel-section-title">Marker Styles</div>
        <div class="config-row">
            <span>Icon Type</span>
            <select id="marker-style-select" onchange="updateAllMarkers()">
                <option value="dot">Solid Dots</option>
                <option value="pin">SVG Pin</option>
                <option value="custom">Custom Image</option>
            </select>
        </div>
        <div class="config-row" id="custom-upload-row" style="display:none;">
            <span>Upload PNG/JPG</span>
            <input type="file" id="custom-icon-upload" accept="image/png, image/jpeg" onchange="handleCustomIconUpload(event)">
        </div>
        <div class="config-row">
            <span>Marker Size</span>
            <input type="range" id="marker-size-slider" min="8" max="48" value="16" oninput="updateAllMarkers()">
        </div>
        
        <div class="panel-section-title">Data Layers</div>
        <div class="results-list" id="results-list-box"></div>
    </div>

    <script>
        const map = L.map('map', { zoomControl: true, attributionControl: false }).setView([__LAT__, __LON__], 14);
        map.zoomControl.setPosition('topleft');
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 }).addTo(map);

        // ALWAYS ON TOP CENTER TARGET
        const centerIcon = L.divIcon({
            className: 'custom-center-icon',
            html: '<div style="background-color: #DC2626; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; border: 3px solid #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">★</div>',
            iconSize: [30, 30], iconAnchor: [15, 15]
        });
        L.marker([__LAT__, __LON__], { icon: centerIcon, zIndexOffset: 10000 }).addTo(map);
        L.circle([__LAT__, __LON__], { radius: __RADIUS__, color: "#3B82F6", weight: 2, fillColor: "#3B82F6", fillOpacity: 0.1 }).addTo(map);
        
        let pts = __GEOJSON__;
        const categoryMap = {}; 
        const layerGroupsRef = {};
        const catPalette = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899", "#14B8A6", "#F97316"];
        const categoryColors = {}; 
        let colorIndex = 0;
        
        let customIconBase64 = null; // Stores uploaded image

        pts.forEach(p => {
            const layerKey = p.type || 'Unclassified';
            if (!categoryMap[layerKey]) {
                categoryMap[layerKey] = []; 
                categoryColors[layerKey] = catPalette[colorIndex % catPalette.length]; 
                colorIndex++;
                layerGroupsRef[layerKey] = L.layerGroup().addTo(map);
            }
            categoryMap[layerKey].push(p);
        });

        // NATIVE CLIENT-SIDE MARKER REGENERATION
        function generateIcon(color) {
            const style = document.getElementById('marker-style-select').value;
            const size = parseInt(document.getElementById('marker-size-slider').value);
            
            if (style === 'custom' && customIconBase64) {
                return L.divIcon({
                    html: `<img src="${customIconBase64}" class="custom-marker-img" style="width:${size}px; height:${size}px;">`,
                    className: '', iconSize: [size, size], iconAnchor: [size/2, size/2]
                });
            } else if (style === 'pin') {
                const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${size}" height="${size}"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="${color}" stroke="#ffffff" stroke-width="1.5"/></svg>`;
                return L.divIcon({ html: `<div class="custom-marker-pin">${svg}</div>`, className: '', iconSize: [size, size], iconAnchor: [size/2, size] });
            } else {
                // Default Dot
                return L.divIcon({
                    html: `<div class="custom-marker-dot" style="background-color: ${color}; width: ${size}px; height: ${size}px;"></div>`,
                    className: '', iconSize: [size, size], iconAnchor: [size/2, size/2]
                });
            }
        }

        function updateAllMarkers() {
            const style = document.getElementById('marker-style-select').value;
            document.getElementById('custom-upload-row').style.display = (style === 'custom') ? 'flex' : 'none';
            
            Object.keys(categoryMap).forEach(key => {
                layerGroupsRef[key].clearLayers();
                const catIcon = generateIcon(categoryColors[key]);
                
                categoryMap[key].forEach(p => {
                    const marker = L.marker([p.lat, p.lon], { icon: catIcon })
                                    .bindPopup(`<b>${p.name}</b><br><span>${p.type}</span>`);
                    if (p.name && p.name !== 'Unknown') {
                        marker.bindTooltip(p.name, { permanent: false, direction: 'top', className: 'poi-text-label' });
                    }
                    marker.addTo(layerGroupsRef[key]);
                });
            });
        }

        function handleCustomIconUpload(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    customIconBase64 = e.target.result;
                    updateAllMarkers();
                };
                reader.readAsDataURL(file);
            }
        }

        // Initialize UI Panel
        const listBox = document.getElementById('results-list-box');
        document.getElementById('results-count').innerText = pts.length;
        
        if (pts.length > 0) {
            let htmlPayload = '';
            Object.keys(categoryMap).forEach(catName => {
                const dotColor = categoryColors[catName];
                htmlPayload += `
                    <div class="layer-category-header" onclick="toggleCategoryVisibility('${catName}', this)">
                        <div class="layer-header-left">
                            <input type="checkbox" checked onclick="event.stopPropagation(); toggleCategoryVisibility('${catName}', this)">
                            <span class="color-dot" style="background-color: ${dotColor};"></span>
                            <span>${catName} <span style="color: #9CA3AF; font-size: 9px;">(${categoryMap[catName].length})</span></span>
                        </div>
                    </div>`;
            });
            listBox.innerHTML = htmlPayload;
            updateAllMarkers(); // Initial Draw
            
            // Auto-fit bounds
            const bounds = L.featureGroup([L.marker([__LAT__, __LON__]), ...pts.map(p => L.marker([p.lat, p.lon]))]).getBounds();
            map.fitBounds(bounds.pad(0.1));
        }

        function toggleCategoryVisibility(catKey, elem) {
            const checkbox = elem.tagName === 'INPUT' ? elem : elem.querySelector('input');
            if (elem.tagName !== 'INPUT') checkbox.checked = !checkbox.checked;
            
            if (checkbox.checked) map.addLayer(layerGroupsRef[catKey]);
            else map.removeLayer(layerGroupsRef[catKey]);
        }
    </script>
</body>
</html>
"""

leaflet_html = leaflet_template.replace("__LAT__", str(render_lat)).replace("__LON__", str(render_lon)).replace("__RADIUS__", str(radius_val)).replace("__GEOJSON__", geojson_str)
st.components.v1.html(leaflet_html, height=850, scrolling=False)
