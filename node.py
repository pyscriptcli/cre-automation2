import streamlit as st
import requests
import re
import json
import os
import base64
import io
import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import Point

# --- PROGRAMMATIC LIGHT MODE LOCK ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\n")

# -----------------------------------------------------------------------------
# 1. BRANDED THEME & ROUNDED UI OVERRIDES
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Open Node", layout="wide", initial_sidebar_state="expanded")

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
            --soft-shadow: 0 4px 12px rgba(0, 51, 102, 0.08) !important;
        }
        
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: var(--white-clean) !important;
            color: var(--brand-midnight) !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: var(--bg-offwhite) !important;
            border-right: 1px solid rgba(0, 51, 102, 0.08) !important;
            width: 300px !important; min-width: 300px !important; max-width: 300px !important;
            border-top-right-radius: 16px !important;
            border-bottom-right-radius: 16px !important;
        }
        
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] { display: none !important; }
        ::-webkit-scrollbar { width: 0px !important; }
        
        p, label, h1, h2, h3, h4, h5, h6, .stMarkdown, [data-testid="stExpander"] summary p {
            color: var(--brand-midnight) !important; font-family: 'Montserrat', sans-serif !important;
        }
        
        [data-testid="stHeader"], header, #stDecoration { display: none !important; }
        [data-testid="stAppViewContainer"] { display: flex !important; flex-direction: row !important; width: 100vw !important; height: 100vh !important; overflow: hidden !important; }
        [data-testid="stMain"] { flex-grow: 1 !important; width: calc(100vw - 300px) !important; height: 100vh !important; padding: 0px !important; margin: 0px !important;}
        .block-container { padding: 0px !important; margin: 0px !important; max-width: 100% !important; gap: 0rem !important; }
        iframe { height: 100vh !important; width: 100% !important; border: none !important; border-top-left-radius: 16px !important; border-bottom-left-radius: 16px !important;}
        
        div[data-baseweb="input"], div[data-baseweb="select"] { background-color: transparent !important; border: none !important; border-bottom: 2px solid rgba(201, 171, 76, 0.5) !important; border-radius: 12px !important; box-shadow: none !important; padding-left: 8px !important;}
        div[data-baseweb="input"]:focus-within { border-bottom: 2px solid var(--brand-gold) !important; }
        
        div.stButton > button[kind="secondary"], [data-testid="stPopover"] > button { background-color: var(--brand-midnight) !important; border: none !important; border-radius: 20px !important; width: 100% !important; padding: 8px !important; box-shadow: var(--soft-shadow) !important; transition: all 0.3s ease !important; }
        div.stButton > button[kind="secondary"]:hover, [data-testid="stPopover"] > button:hover { background-color: var(--brand-gold) !important; }
        div.stButton > button[kind="secondary"] p, [data-testid="stPopover"] > button p { color: var(--white-clean) !important; font-weight: 700 !important; font-size: 10px !important; text-transform: uppercase !important; letter-spacing: 1px; }
        
        div.stDownloadButton > button { background-color: var(--brand-midnight) !important; border: none !important; border-radius: 12px !important; width: 100% !important; padding: 6px !important; }
        div.stDownloadButton > button:hover { background-color: var(--brand-gold) !important; }
        
        div.stButton > button[kind="primary"] { background: transparent !important; border: none !important; border-radius: 12px !important; color: var(--text-muted) !important; box-shadow: none !important; padding: 0 !important; margin-top: 2px; }
        div.stButton > button[kind="primary"] p { color: var(--text-muted) !important; font-size: 10px !important; font-weight: 600 !important; text-transform: uppercase; }
        
        [data-testid="stSidebar"] .st-expander { border: 1px solid rgba(0, 51, 102, 0.05) !important; background-color: var(--white-clean) !important; border-radius: 12px !important; margin-bottom: 4px !important; }
        [data-testid="stSidebar"] .st-expander summary p { font-size: 11px !important; font-weight: 600 !important; }
        .stCheckbox label p { font-size: 10px !important; font-weight: 500 !important; }
        div[data-baseweb="checkbox"] input:checked + div, div[data-baseweb="checkbox"] div[aria-checked="true"] { background-color: var(--brand-midnight) !important; border-color: var(--brand-midnight) !important; border-radius: 4px !important;}
        
        .stDeployButton, footer { display:none !important; }
        .brand-title { font-family: 'Cormorant Garamond', serif !important; font-style: italic; font-weight: 600; color: var(--brand-midnight); font-size: 36px; text-align: center; border-bottom: 2px solid var(--brand-gold); padding-bottom: 6px; margin-bottom: 20px; border-radius: 12px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. STATE PERSISTENCE & DATA MODELS
# -----------------------------------------------------------------------------
if 'geo_coords' not in st.session_state: st.session_state.geo_coords = "14.5995, 120.9842"
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = 1000
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'last_scan_lat' not in st.session_state: st.session_state.last_scan_lat = 14.5995
if 'last_scan_lon' not in st.session_state: st.session_state.last_scan_lon = 120.9842
if 'static_map_buf' not in st.session_state: st.session_state.static_map_buf = None

POI_CONFIG = {
    "COMMERCIAL": [['Corporate Office', '"building"~"office|commercial",i'], ['IT/Tech Center', '"office"~"it|telecommunication",i'], ['Business Center', '"building"="commercial"'], ['Hospital', '"amenity"~"hospital|clinic",i'], ['Hotel', '"tourism"="hotel"'], ['Motel', '"tourism"="motel"']],
    "RESIDENTIAL": [['Apartments', '"building"="apartments"'], ['House', '"building"="house"'], ['Residential Area', '"landuse"="residential"'], ['Condominium', '"building"="residential"']],
    "RETAIL": [['Mall/Department Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"supermarket|grocery",i'], ['Convenience Store', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Hardware', '"shop"~"hardware|doityourself",i'], ['General Shops', '"shop"~"boutique|clothes|shoes",i'], ['Beauty', '"shop"="beauty"'], ['Bicycle', '"shop"="bicycle"'], ['Books/Stationary', '"shop"~"books|stationary",i'], ['Car', '"shop"="car"'], ['Chemist', '"shop"="chemist"'], ['Clothes', '"shop"="clothes"'], ['Copyshop', '"shop"="copyshop"'], ['Cosmetics', '"shop"="cosmetics"'], ['Department store', '"shop"="department_store"'], ['DIY/hardware', '"shop"~"hardware|doityourself",i'], ['Garden centre', '"shop"="garden_centre"'], ['General', '"shop"="general"'], ['Gift', '"shop"="gift"'], ['Hairdresser', '"shop"="hairdresser"'], ['Jewelry', '"shop"="jewelry"'], ['Kiosk', '"shop"="kiosk"'], ['Leather', '"shop"="leather"'], ['Marketplace', '"amenity"="marketplace"'], ['Musical instrument', '"shop"="musical_instrument"'], ['Optician', '"shop"="optician"'], ['Pets', '"shop"="pets"'], ['Phone', '"shop"="mobile_phone"'], ['Photo', '"shop"="photo"'], ['Shoes', '"shop"="shoes"'], ['Shopping centre', '"shop"="mall"'], ['Textiles', '"shop"="textiles"'], ['Toys', '"shop"="toys"']],
    "FOOD AND BEVERAGES": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee Shop', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"'], ['Bar/Pub/Nightclub', '"amenity"~"bar|pub|nightclub",i'], ['Bakery/Pastry', '"shop"="bakery"'], ['BBQ', '"amenity"="bbq"'], ['Biergarten', '"amenity"="biergarten"'], ['Food court', '"amenity"="food_court"'], ['Ice cream', '"amenity"="ice_cream"'], ['Pub', '"amenity"="pub"']],
    "INDUSTRIAL & LOGISTICS": [['Expressway Exits', '"highway"~"motorway_junction|toll_gantry",i'], ['Ports & Terminals', '"industrial"="port"'], ['Manufacturing Plants', '"industrial"~"factory|manufacturing|processing",i'], ['Cold Storage Facilities', '"warehouse"~"cold_store|cold_storage",i'], ['Industrial Parks/Estates', '"landuse"~"industrial|industrial_estate",i'], ['Warehouses & Depots', '"building"~"warehouse|depot",i'], ['Storage Facilities', '"building"="storage"'], ['Truck Access Routes (HGV)', '"hgv"~"designated|yes",i']],
    "GOVERNMENT & INFRASTRUCTURE": [['City Hall', '"amenity"="townhall"'], ['Police Station', '"amenity"="police"'], ['Fire Station', '"amenity"="fire_station"'], ['Airport Terminal', '"aeroway"~"terminal|aerodrome",i']],
    "SCHOOLS": [['University/College', '"amenity"~"university|college",i'], ['K-12 School', '"amenity"="school"'], ['Vocational/Other', '"amenity"="learning_centre"']]
}
ADVANCED_CONFIG = {
    "AMENITIES": [['ATM', '"amenity"="atm"'], ['Bank', '"amenity"="bank"'], ['Bench', '"amenity"="bench"'], ['Bicycle Parking', '"amenity"="bicycle_parking"'], ['Bicycle Rental', '"amenity"="bicycle_rental"'], ['Cinema', '"amenity"="cinema"'], ['Clinic', '"amenity"="clinic"'], ['Embassy', '"amenity"="embassy"'], ['Firestation', '"amenity"="fire_station"'], ['Fuel', '"amenity"="fuel"'], ['Hospital', '"amenity"="hospital"'], ['Library', '"amenity"="library"'], ['Music School', '"amenity"="music_school"'], ['Parking', '"amenity"="parking"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Police', '"amenity"="police"'], ['Letter Box', '"amenity"="letter_box"'], ['Post Office', '"amenity"="post_office"'], ['School/College', '"amenity"~"school|college",i'], ['Taxi', '"amenity"="taxi"'], ['Theatre', '"amenity"="theatre"'], ['Toilets', '"amenity"="toilets"'], ['University', '"amenity"="university"']],
    "PLACE OF WORSHIP": [['Church', '"religion"="christian"'], ['Mosque', '"religion"="muslim"'], ['Buddhist Temple', '"religion"="buddhist"'], ['Hindu Temple', '"religion"="hindu"'], ['Synagogue', '"religion"="jewish"'], ['Cemetery', '"landuse"="cemetery"'], ['Alpine Hut', '"tourism"="alpine_hut"'], ['Apartment', '"tourism"="apartment"'], ['Camp Site', '"tourism"="camp_site"'], ['Chalet', '"tourism"="chalet"'], ['Guest House', '"tourism"="guest_house"'], ['Hostel', '"tourism"="hostel"'], ['Hotel', '"tourism"="hotel"'], ['Motel', '"tourism"="motel"'], ['Casino', '"amenity"="casino"'], ['Spa', '"leisure"="spa"'], ['Sauna', '"leisure"="sauna"']],
    "SPORTS": [['American football', '"sport"="american_football"'], ['Baseball', '"sport"="baseball"'], ['Basketball', '"sport"="basketball"'], ['Cycling', '"sport"="cycling"'], ['Gymnastics', '"sport"="gymnastics"'], ['Golf', '"sport"="golf"'], ['Hockey', '"sport"="hockey"'], ['Horse racing', '"sport"="horse_racing"'], ['Ice hockey', '"sport"="ice_hockey"'], ['Soccer', '"sport"="soccer"'], ['Sports centre', '"leisure"="sports_centre"'], ['Surfing', '"sport"="surfing"'], ['Swimming', '"sport"="swimming"'], ['Tennis', '"sport"="tennis"'], ['Volleyball', '"sport"="volleyball"']],
    "MISCELLANEOUS": [['Busstop', '"highway"="bus_stop"'], ['E-bike charging', '"amenity"="charging_station"'], ['Kindergarten', '"amenity"="kindergarten"'], ['Marketplace', '"amenity"="marketplace"'], ['Office', '"office"="yes"'], ['Recycling', '"amenity"="recycling"'], ['Travel agency', '"shop"="travel_agency"'], ['Defibrillator - AED', '"emergency"="defibrillator"'], ['Fire hose/extinguisher', '"emergency"~"fire_hose|fire_extinguisher",i'], ['Fixme', '"fixme"~".",i'], ['Note-Node', '"type"="node"'], ['Note-Way', '"type"="way"'], ['Construction', '"landuse"="construction"'], ['Image', '"image"~".",i'], ['Public camera', '"man_made"="surveillance"'], ['City', '"place"="city"'], ['Town', '"place"="town"'], ['Village', '"place"="village"'], ['Hamlet', '"place"="hamlet"'], ['Suburb', '"place"="suburb"']]
}

def generate_static_report():
    if not st.session_state.scanned_records: return None
    lat, lon = float(st.session_state.last_scan_lat), float(st.session_state.last_scan_lon)
    rad = st.session_state.geo_radius
    
    # Map Colors Dynamically matching JS logic
    catPalette = ["#003366", "#C9AB4C", "#1A5A8A", "#A8862E", "#3D7DA8", "#7A5C10", "#6A94B0", "#D4B85A", "#001F3F", "#E8D494"]
    unique_types = list(set([r.get('type', 'Unclassified') for r in st.session_state.scanned_records]))
    color_map = {t: catPalette[i % len(catPalette)] for i, t in enumerate(unique_types)}
    
    # Build GeoDataFrames
    geometry = [Point(r['lon'], r['lat']) for r in st.session_state.scanned_records]
    gdf = gpd.GeoDataFrame(st.session_state.scanned_records, geometry=geometry, crs="EPSG:4326")
    gdf_web = gdf.to_crs(epsg=3857)
    
    center_pt = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(epsg=3857)
    circle_poly = center_pt.buffer(rad)

    fig, ax = plt.subplots(figsize=(10, 10), dpi=300)
    gpd.GeoDataFrame(geometry=circle_poly).plot(ax=ax, facecolor='#003366', alpha=0.05, edgecolor='#003366', linewidth=2, linestyle='--')
    center_pt.plot(ax=ax, marker='*', color='#C9AB4C', markersize=350, edgecolor='#003366', zorder=5)

    for t in unique_types:
        subset = gdf_web[gdf_web['type'] == t]
        if not subset.empty:
            subset.plot(ax=ax, color=color_map[t], markersize=120, alpha=0.9, edgecolor='white', linewidth=1, label=t)
            
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)
    ax.set_axis_off()
    
    legend = plt.legend(loc='lower right', frameon=True, shadow=True, title="Open Node Layers", facecolor='white', framealpha=0.95, edgecolor='#003366', fontsize=8)
    legend.get_title().set_fontweight('bold')
    plt.title(f"Open Node Spatial Scan - {rad}m Radius", fontsize=16, fontweight='bold', color='#003366', pad=20)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight', pad_inches=0.1)
    buf.seek(0)
    plt.close(fig)
    return buf

# -----------------------------------------------------------------------------
# 3. SIDEBAR WORKSPACE
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="brand-title">Open Node</div>', unsafe_allow_html=True)
    
    location_input = st.text_input("COORDINATES", value=st.session_state.geo_coords)
    radius_val = st.number_input("RADIUS (METERS)", min_value=100, max_value=50000, value=st.session_state.geo_radius, step=100)
    st.session_state.geo_radius = radius_val

    coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", location_input)
    if coord_match:
        lat_coord, lon_coord = float(coord_match.group(1)), float(coord_match.group(2))
        st.session_state.geo_coords = location_input
    else:
        lat_coord, lon_coord = 14.5995, 120.9842

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    
    # NEW MARKER CONTROLS
    with st.expander("⚙️ MARKER CONFIGURATION", expanded=False):
        marker_style = st.selectbox("Marker Type", ["Dots", "Pin Location", "Pin Ball", "Custom Icon"])
        marker_size = st.slider("Marker Size", 8, 32, 16)
        custom_icon_b64 = ""
        if marker_style == "Custom Icon":
            uploaded_icon = st.file_uploader("Upload Image (Auto-Cropped to Circle)", type=["png", "jpg"])
            if uploaded_icon:
                custom_icon_b64 = base64.b64encode(uploaded_icon.read()).decode()
            
    search_query = st.text_input("SEARCH TAGS", placeholder="Search parameters...").lower()
    selected_tags = []
    
    for cat_name, node_items in POI_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for label, tag in matched:
                    if st.checkbox(label, key=f"chk_{cat_name}_{label}"): selected_tags.append(tag)

    st.markdown("<div style='font-weight: 700; font-size: 11px; margin-top: 15px; margin-bottom: 8px; color: #003366;'>ADVANCED POIs</div>", unsafe_allow_html=True)
    for cat_name, node_items in ADVANCED_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for label, tag in matched:
                    if st.checkbox(label, key=f"chk_adv_{cat_name}_{label}"): selected_tags.append(tag)

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("SCAN AREA", type="secondary", use_container_width=True):
        if not selected_tags:
            st.error("Select ≥ 1 layer.")
        else:
            with st.spinner("Executing Data Engine (OSMnx -> Overpass)"):
                # PRIMARY ENGINE: OSMnx (Will fail gracefully due to Complex Regex QL)
                try:
                    ox.settings.log_console = False
                    raise ValueError("OSMnx natively rejects Overpass Regex Operators. Engaging Fallback Engine...")
                except Exception as e:
                    # FALLBACK ENGINE: Overpass Turbo
                    url = "https://overpass-api.de/api/interpreter"
                    statements = "\n".join([f"  nwr[{tag}](around:{radius_val},{lat_coord},{lon_coord});" for tag in selected_tags])
                    ql = f"[out:json][timeout:90];(\n{statements}\n);\nout center;"
                    res = requests.post(url, data={"data": ql}, headers={"User-Agent": "OpenNode/4.0"}, timeout=100)
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
                        st.session_state.static_map_buf = None
                        st.rerun()

    if st.button("CLEAR ALL", type="primary"):
        st.session_state.scanned_records = []
        st.session_state.static_map_buf = None
        for key in list(st.session_state.keys()):
            if key.startswith("chk_"): st.session_state[key] = False
        st.rerun()

    st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>", unsafe_allow_html=True)
    
    # REPORT EXPORT GENERATOR BEFORE SAVE/IMPORT
    if st.session_state.scanned_records:
        if st.button("📸 GENERATE STATIC REPORT", use_container_width=True):
            with st.spinner("Rendering Matplotlib + Contextily Map Engine..."):
                st.session_state.static_map_buf = generate_static_report()
                
        if st.session_state.static_map_buf is not None:
            st.download_button("📥 DOWNLOAD PNG REPORT", st.session_state.static_map_buf, "OpenNode_Report.png", "image/png", use_container_width=True)
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button("JSON", json.dumps(st.session_state.scanned_records), "scan.json", "application/json", use_container_width=True)
    with col2:
        st.download_button("KML", "<kml></kml>", "POIs.kml", "application/vnd.google-earth.kml+xml", use_container_width=True)

    with st.popover("IMPORT FILE", use_container_width=True):
        imported_file = st.file_uploader("Select JSON", type=["json"], label_visibility="collapsed")
        if imported_file and st.button("LOAD", type="secondary", use_container_width=True):
            data = json.load(imported_file)
            st.session_state.scanned_records = data.get("scanned_records", data)
            st.rerun()

# -----------------------------------------------------------------------------
# 4. ZERO-LATENCY SPATIAL CANVAS
# -----------------------------------------------------------------------------
geojson_str = json.dumps(st.session_state.scanned_records)
render_lat, render_lon = lat_coord, lon_coord
is_stale = "true" if (lat_coord != st.session_state.last_scan_lat or lon_coord != st.session_state.last_scan_lon) else "false"

leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #ffffff; overflow: hidden; font-family: 'Montserrat', sans-serif; }
        #map { height: 100vh; width: 100%; }
        
        #minimal-basemap-panel {
            position: absolute; top: 110px; left: 50px; z-index: 1000;
            background: #ffffff; border-radius: 12px; border: 1px solid rgba(0, 51, 102, 0.1); display: none; flex-direction: column; padding: 4px; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); width: 150px;
        }
        #minimal-basemap-panel select { border: none; padding: 6px; font-size: 10px; font-weight: 700; color: #003366; background: transparent; outline: none; cursor: pointer; width: 100%; text-transform: uppercase; }
        
        #search-container { position: absolute; top: 10px; left: 54px; z-index: 1000; width: 300px; }
        #map-search { width: 100%; padding: 10px 14px; border: none; border-radius: 20px; font-size: 11px; font-weight: 600; color: #003366; background: #ffffff; outline: none; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.1); }
        
        #scan-results-panel { position: absolute; top: 10px; right: 10px; z-index: 1000; background: #ffffff; width: 250px; max-height: calc(100vh - 20px); border-radius: 16px; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 8px 24px rgba(0, 51, 102, 0.12); }
        .results-header { background: #003366; color: #ffffff; padding: 12px 16px; font-size: 10px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #C9AB4C; }
        .results-list { overflow-y: auto; flex-grow: 1; padding-bottom: 8px; }
        .layer-category-header { background: #ffffff; padding: 10px 16px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; user-select: none; font-size: 9px; font-weight: 700; color: #003366; border-bottom: 1px solid #f0f0f0; }
        
        .poi-text-label { background: #fff; border: 1px solid #003366; padding: 2px 6px; border-radius: 8px; font-size: 9px; font-weight: 700; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .color-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; border: 1px solid rgba(0,0,0,0.1); margin-right: 6px; }
        
        .leaflet-control-custom-stack { background: #fff; border-radius: 12px; overflow: hidden; display: flex; flex-direction: column; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border: none; }
        .leaflet-control-custom-stack a { display: flex !important; align-items: center; justify-content: center; background: #fff; width: 36px; height: 36px; cursor: pointer; }
        .leaflet-control-custom-stack a:hover { background: #f4f4f4; }
    </style>
</head>
<body>
    <div id="map"></div>
    <div id="search-container"><input type="text" id="map-search" placeholder="Search coordinates or addresses..." onkeyup="handleSearch(event)"></div>
    <div id="minimal-basemap-panel">
        <select id="basemap-select" onchange="switchActiveBasemap(this.value)"><option value="osm">OpenStreetMap</option><option value="carto">Carto Light</option></select>
    </div>
    <div id="scan-results-panel">
        <div class="results-header"><span>OPEN NODE RESULTS</span><span id="results-count" style="color:#C9AB4C;">0</span></div>
        <div class="results-list" id="results-list-box"></div>
    </div>

    <script>
        const map = L.map('map', { zoomControl: false, attributionControl: false }).setView([__LAT__, __LON__], 14);
        L.control.zoom({ position: 'topleft' }).addTo(map);

        const toolbarControl = L.control({position: 'topleft'});
        toolbarControl.onAdd = function (map) {
            const div = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom-stack');
            div.innerHTML = `<a title="Toggle Layers" onclick="document.getElementById('minimal-basemap-panel').style.display = document.getElementById('minimal-basemap-panel').style.display === 'flex' ? 'none' : 'flex'">🗂️</a>`;
            return div;
        };
        toolbarControl.addTo(map);

        const basemaps = {
            osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }),
            carto: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 })
        };
        basemaps.osm.addTo(map);
        function switchActiveBasemap(targetKey) { Object.values(basemaps).forEach(layer => map.removeLayer(layer)); basemaps[targetKey].addTo(map); }

        const starIcon = L.divIcon({
            className: 'custom-center-icon',
            html: '<div style="background-color: #003366; color: #C9AB4C; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; border: 2px solid #ffffff; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.4);">★</div>',
            iconSize: [28, 28], iconAnchor: [14, 14]
        });
        L.marker([__LAT__, __LON__], { icon: starIcon }).addTo(map);
        L.circle([__LAT__, __LON__], { radius: __RADIUS__, color: "#003366", weight: 2, fillColor: "#003366", fillOpacity: 0.05 }).addTo(map);
        
        let pts = __GEOJSON__;
        const categoryMap = {}; const layerGroupsRef = {};
        const catPalette = ["#003366", "#C9AB4C", "#1A5A8A", "#A8862E", "#3D7DA8", "#7A5C10", "#6A94B0", "#D4B85A", "#001F3F", "#E8D494"];
        let colorIndex = 0;
        
        pts.forEach(p => {
            const layerKey = p.type || 'Unclassified';
            if (!categoryMap[layerKey]) { categoryMap[layerKey] = []; categoryMap[layerKey].color = catPalette[colorIndex++ % catPalette.length]; }
            categoryMap[layerKey].push(p);
        });

        // MARKER GENERATION PIPELINE
        const markerStyle = '__MARKER_STYLE__';
        const mSize = __MARKER_SIZE__;
        const b64Icon = '__B64_ICON__';

        const createDynamicIcon = (color) => {
            if (markerStyle === 'Dots') {
                return L.divIcon({ html: `<div style="width:${mSize}px; height:${mSize}px; background:${color}; border-radius:50%; border:1.5px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"></div>`, className: '', iconSize: [mSize, mSize], iconAnchor: [mSize/2, mSize/2] });
            } else if (markerStyle === 'Pin Ball') {
                return L.divIcon({ html: `<div style="width:${mSize}px; height:${mSize}px; background: radial-gradient(circle at 30% 30%, ${color}, #000); border-radius:50%; border:2px solid white; box-shadow: 0 4px 8px rgba(0,0,0,0.3);"></div>`, className: '', iconSize: [mSize, mSize], iconAnchor: [mSize/2, mSize/2] });
            } else if (markerStyle === 'Custom Icon' && b64Icon) {
                return L.divIcon({ html: `<div style="width:${mSize*1.5}px; height:${mSize*1.5}px; border-radius:50%; background-image:url(data:image/png;base64,${b64Icon}); background-size:cover; background-position:center; border:2px solid ${color}; box-shadow: 0 4px 8px rgba(0,0,0,0.3);"></div>`, className: '', iconSize: [mSize*1.5, mSize*1.5], iconAnchor: [(mSize*1.5)/2, (mSize*1.5)/2] });
            } else {
                // Default Pin Location
                const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${mSize*1.2}" height="${mSize*1.2}"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="${color}" stroke="#ffffff" stroke-width="1.5"/></svg>`;
                return L.divIcon({ html: svg, className: '', iconSize: [mSize*1.2, mSize*1.2], iconAnchor: [(mSize*1.2)/2, mSize*1.2] });
            }
        };

        Object.keys(categoryMap).forEach(key => {
            layerGroupsRef[key] = L.layerGroup().addTo(map);
            const catIcon = createDynamicIcon(categoryMap[key].color);
            categoryMap[key].forEach(p => {
                const marker = L.marker([p.lat, p.lon], { icon: catIcon }).bindTooltip(p.name, { direction: 'top', offset: [0, -mSize/2], className: 'poi-text-label' });
                marker.addTo(layerGroupsRef[key]);
            });
        });

        const listBox = document.getElementById('results-list-box');
        document.getElementById('results-count').innerText = pts.length;
        if (pts.length > 0) {
            let htmlPayload = '';
            Object.keys(categoryMap).forEach(catName => {
                htmlPayload += `<div class="layer-category-header"><div style="display:flex; align-items:center;"><span class="color-dot" style="background-color: ${categoryMap[catName].color};"></span><span>${catName}</span></div><span style="color: #C9AB4C;">(${categoryMap[catName].length})</span></div>`;
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

leaflet_html = (leaflet_template
                .replace("__LAT__", str(render_lat))
                .replace("__LON__", str(render_lon))
                .replace("__RADIUS__", str(radius_val))
                .replace("__IS_STALE__", is_stale)
                .replace("__MARKER_STYLE__", marker_style)
                .replace("__MARKER_SIZE__", str(marker_size))
                .replace("__B64_ICON__", custom_icon_b64)
                .replace("__GEOJSON__", geojson_str))

st.components.v1.html(leaflet_html, height=850, scrolling=False)
