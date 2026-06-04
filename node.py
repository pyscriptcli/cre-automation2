import streamlit as st
import requests
import re
import json
import os
import matplotlib.pyplot as plt
import io
import base64

# --- PROGRAMMATIC LIGHT MODE LOCK (Must execute before st.set_page_config) ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\n")

# -----------------------------------------------------------------------------
# 1. BRANDED BICHROMATIC THEME & TRUE FULL SCREEN OVERRIDES
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Trade Area Scan",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Montserrat:wght@400;500;600;700;800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0');

        :root {
            --brand-midnight: #003366 !important;
            --brand-gold: #C9AB4C !important;
            --brand-dark: #001F3F !important;
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
            color: var(--brand-midnight) !important;
            border-right: 1px solid rgba(0, 51, 102, 0.08) !important;
            width: 280px !important;
            min-width: 280px !important;
            max-width: 280px !important;
            transform: none !important;
            visibility: visible !important;
            overflow: hidden !important;
            box-shadow: 2px 0 15px rgba(0,0,0,0.03) !important;
        }
        
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] { display: none !important; }
        ::-webkit-scrollbar { width: 0px !important; background: transparent !important; }
        * { scrollbar-width: none !important; -ms-overflow-style: none !important; }
        
        p, label, h1, h2, h3, h4, h5, h6, .stMarkdown, [data-testid="stExpander"] summary p {
            color: var(--brand-midnight) !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        
        [data-testid="stHeader"], header, #stDecoration { display: none !important; }
        
        [data-testid="stAppViewContainer"] { display: flex !important; flex-direction: row !important; width: 100vw !important; height: 100vh !important; overflow: hidden !important; }
        [data-testid="stMain"] { flex-grow: 1 !important; width: calc(100vw - 280px) !important; height: 100vh !important; overflow: hidden !important; margin: 0px !important; padding: 0px !important; }
        .block-container, [data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"], .stElementContainer { padding: 0px !important; margin: 0px !important; max-width: 100% !important; gap: 0rem !important; }
        iframe { height: 100vh !important; width: 100% !important; border: none !important; display: block !important; }
        
        [data-testid="stSidebarUserContent"] {
            padding-top: 12px !important; padding-left: 12px !important; padding-right: 12px !important; height: 100vh !important; overflow-y: auto !important; overflow-x: hidden !important;
        }
        
        div[data-baseweb="input"], div[data-baseweb="select"] { background-color: transparent !important; border: none !important; border-bottom: 1px solid rgba(201, 171, 76, 0.5) !important; border-radius: 0px !important; box-shadow: none !important; }
        div[data-baseweb="input"]:focus-within { border-bottom: 2px solid var(--brand-gold) !important; }
        
        div.stButton > button[kind="secondary"], [data-testid="stPopover"] > button { background-color: var(--brand-midnight) !important; border: 1px solid var(--brand-midnight) !important; border-radius: 2px !important; width: 100% !important; padding: 6px !important; box-shadow: var(--soft-shadow) !important; transition: all 0.3s ease !important; }
        div.stButton > button[kind="secondary"]:hover, [data-testid="stPopover"] > button:hover { background-color: var(--brand-gold) !important; border-color: var(--brand-gold) !important; }
        div.stButton > button[kind="secondary"] p, [data-testid="stPopover"] > button p, [data-testid="stPopover"] > button div, div.stDownloadButton > button p { color: var(--white-clean) !important; font-weight: 700 !important; font-size: 9px !important; text-transform: uppercase !important; letter-spacing: 1px; }
        
        div.stDownloadButton > button { background-color: var(--brand-midnight) !important; border: none !important; border-radius: 2px !important; width: 100% !important; padding: 4px !important; }
        div.stDownloadButton > button:hover { background-color: var(--brand-gold) !important; }
        
        div.stButton > button[kind="primary"] { background: transparent !important; border: none !important; color: var(--text-muted) !important; box-shadow: none !important; padding: 0 !important; margin-top: 2px; display: inline-flex; }
        div.stButton > button[kind="primary"] p { color: var(--text-muted) !important; font-size: 9px !important; font-weight: 600 !important; text-decoration: none !important; text-transform: uppercase; }
        
        [data-testid="stSidebar"] .st-expander { border: 1px solid rgba(0, 51, 102, 0.05) !important; background-color: var(--white-clean) !important; border-radius: 2px !important; margin-bottom: 2px !important; overflow: hidden !important; }
        .stCheckbox label p { font-size: 10px !important; font-weight: 500 !important; }
        
        div[data-baseweb="checkbox"] input:checked + div, div[data-baseweb="checkbox"] div[aria-checked="true"] { background-color: var(--brand-midnight) !important; border-color: var(--brand-midnight) !important; }
        
        .brand-title { font-family: 'Cormorant Garamond', serif !important; font-style: italic; color: var(--brand-midnight); font-size: 30px; text-align: center; border-bottom: 1px solid var(--brand-gold); padding-bottom: 6px; margin-bottom: 30px; }
        .stTextInput label p, .stNumberInput label p { font-size: 9px !important; font-weight: 500 !important; letter-spacing: 0.5px; color: var(--text-muted) !important; }
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

# Layer Preference State Models (Native Python Management Sync)
if 'layer_meta' not in st.session_state: st.session_state.layer_meta = {}
if 'custom_groups' not in st.session_state: st.session_state.custom_groups = {}
if 'target_config' not in st.session_state: st.session_state.target_config = {"size": 24, "color": "#003366", "style": "star"}
if 'radius_config' not in st.session_state: st.session_state.radius_config = {"color": "#003366", "fill_opacity": 0.08, "weight": 1.5}
if 'basemap_style' not in st.session_state: st.session_state.basemap_style = "osm"
if 'show_labels' not in st.session_state: st.session_state.show_labels = True

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

def compile_features_kml(features):
    kml = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scanned POIs</name>'
    for f in features:
        name = f.get('name', 'Asset').replace("&", "&").replace("<", "<").replace(">", ">")
        class_type = f.get('type', 'Node').replace("&", "&").replace("<", "<").replace(">", ">")
        kml += f"<Placemark><name>{name}</name><description>{class_type}</description><Point><coordinates>{f['lon']},{f['lat']},0</coordinates></Point></Placemark>"
    return kml + '</Document></kml>'

# -----------------------------------------------------------------------------
# 3. SIDEBAR WORKSPACE & OSM GEOCODING
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="brand-title">Trade Area Scan</div>', unsafe_allow_html=True)
    
    location_input = st.text_input("COORDINATES", value=st.session_state.geo_coords, key="geo_coords_input")
    radius_val = st.number_input("RADIUS (METERS)", min_value=100, max_value=50000, value=st.session_state.geo_radius, key="geo_radius_input", step=100)
    st.session_state.geo_radius = radius_val

    coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", location_input)
    
    if coord_match:
        lat_coord, lon_coord = float(coord_match.group(1)), float(coord_match.group(2))
        st.session_state.geo_coords = location_input
    else:
        if location_input and location_input != st.session_state.get('last_geocoded_query', ''):
            with st.spinner("Locating via OpenStreetMap..."):
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
                    else:
                        st.error("Location not found.")
                        lat_coord, lon_coord = 14.5995, 120.9842 
                except Exception:
                    lat_coord, lon_coord = 14.5995, 120.9842
        else:
            fallback_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", st.session_state.geo_coords)
            lat_coord, lon_coord = (float(fallback_match.group(1)), float(fallback_match.group(2))) if fallback_match else (14.5995, 120.9842)

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    search_query = st.text_input("SEARCH TAGS", placeholder="Search parameters...").lower()
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    
    selected_tags = []
    for cat_name, node_items in POI_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for label, tag in matched:
                    if st.checkbox(label, key=f"chk_{cat_name}_{label}"): selected_tags.append(tag)

    st.markdown("<div style='font-weight: 700; font-size: 11px; margin-top: 15px; margin-bottom: 8px; color: #003366; letter-spacing: 1px;'>ADVANCED POIs</div>", unsafe_allow_html=True)
    with st.container():
        for cat_name, node_items in ADVANCED_CONFIG.items():
            matched = [item for item in node_items if search_query in item[0].lower()]
            if matched:
                with st.expander(cat_name, expanded=(len(search_query) > 0)):
                    for label, tag in matched:
                        if st.checkbox(label, key=f"chk_adv_{cat_name}_{label}"): selected_tags.append(tag)

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("SCAN AREA", type="secondary", use_container_width=True, key="scan_btn"):
        if not selected_tags:
            st.error("Select ≥ 1 layer.")
        else:
            records = []
            success = False
            
            # Primary: OSMnx Extraction
            try:
                import osmnx as ox
                tags_dict = {}
                for tag in selected_tags:
                    clean = tag.replace('"', '')
                    if '=' in clean:
                        k, v = clean.split('=', 1)
                        if '|' in v: v = [x.strip() for x in v.split('|')]
                        tags_dict[k] = v
                    else:
                        tags_dict[clean] = True
                gdf = ox.geometries_from_point((lat_coord, lon_coord), tags_dict, dist=radius_val)
                if not gdf.empty:
                    for idx, row in gdf.iterrows():
                        if hasattr(row.geometry, 'centroid'):
                            c_lat, c_lon = row.geometry.centroid.y, row.geometry.centroid.x
                        else: continue
                        name = row.get('name', 'Unknown')
                        if isinstance(name, float): name = 'Unknown'
                        matched_type = 'Node'
                        for k in tags_dict.keys():
                            if k in row and row[k]:
                                matched_type = str(row[k])
                                break
                        records.append({
                            "lat": c_lat, "lon": c_lon, "name": str(name), 
                            "type": matched_type, "visible": True, "uid": len(records)
                        })
                    st.session_state.scanned_records = records
                    st.session_state.last_scan_lat = lat_coord
                    st.session_state.last_scan_lon = lon_coord
                    success = True
            except Exception: pass

            # Fallback: Overpass Engine
            if not success:
                url = "https://overpass-api.de/api/interpreter"
                statements = "\n".join([f"  nwr[{tag}](around:{radius_val},{lat_coord},{lon_coord});" for tag in selected_tags])
                ql = f"[out:json][timeout:90];(\n{statements}\n);\nout center;"
                try:
                    res = requests.post(url, data={"data": ql}, headers={"User-Agent": "TradeAreaScan/3.1"}, timeout=90)
                    if res.status_code == 200:
                        for el in res.json().get('elements', []):
                            e_lat = el.get('lat') or el.get('center', {}).get('lat')
                            e_lon = el.get('lon') or el.get('center', {}).get('lon')
                            if e_lat and e_lon:
                                tags = el.get('tags', {})
                                records.append({
                                    "lat": e_lat, "lon": e_lon, "name": tags.get('name', 'Unknown'), 
                                    "type": tags.get('amenity') or tags.get('shop') or tags.get('building') or 'Node',
                                    "visible": True, "uid": len(records)
                                })
                        st.session_state.scanned_records = records
                        st.session_state.last_scan_lat = lat_coord
                        st.session_state.last_scan_lon = lon_coord
                        success = True
                except Exception: pass
            
            if success: st.rerun()

    if st.button("CLEAR ALL", type="primary", key="clear_btn"):
        st.session_state.scanned_records = []
        st.session_state.layer_meta = {}
        st.session_state.custom_groups = {}
        for key in list(st.session_state.keys()):
            if key.startswith("chk_"): st.session_state[key] = False
        st.rerun()

    st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1: st.download_button("JSON", json.dumps(st.session_state.scanned_records), "scan.json", "application/json", use_container_width=True)
    with col2: st.download_button("KML", compile_features_kml(st.session_state.scanned_records), "POIs.kml", "application/vnd.google-earth.kml+xml", use_container_width=True)

# -----------------------------------------------------------------------------
# 4. NATIVE PYTHON LAYER PREFERENCE ENGINE & MATPLOTLIB RENDERER
# -----------------------------------------------------------------------------
active_records = st.session_state.scanned_records
detected_layers = list(set([p.get('type', 'Unclassified') for p in active_records]))
cat_palette = ["#003366", "#C9AB4C", "#1A5A8A", "#A8862E", "#3D7DA8", "#7A5C10", "#6A94B0", "#D4B85A", "#001F3F", "#E8D494"]

# Auto-initialize preference dictionary structures safely
for i, layer in enumerate(detected_layers):
    if layer not in st.session_state.layer_meta:
        st.session_state.layer_meta[layer] = {
            "color": cat_palette[i % len(cat_palette)],
            "style": "dots",
            "size": 14,
            "visible": True
        }

# MATPLOTLIB STATIC CANVAS EXPORTER
def generate_report_canvas_image():
    if not st.session_state.scanned_records:
        return None
    try:
        import contextily as cx
        import geopandas as gpd
        from shapely.geometry import Point
        
        pts = [p for p in st.session_state.scanned_records if p.get('visible', True)]
        fig, ax = plt.subplots(figsize=(10, 10), dpi=300)
        
        center_gdf = gpd.GeoDataFrame(geometry=[Point(lon_coord, lat_coord)], crs="EPSG:4326").to_crs(epsg=3857)
        cx_center = center_gdf.geometry.iloc[0]
        
        buffer_zone = cx_center.buffer(radius_val)
        xmin, ymin, xmax, ymax = buffer_zone.bounds
        
        r_col = str(st.session_state.radius_config["color"])
        r_opacity = float(st.session_state.radius_config["fill_opacity"])
        r_weight = float(st.session_state.radius_config["weight"])
        
        circle_patch = plt.Circle((cx_center.x, cx_center.y), radius_val, fill=True, facecolor=r_col, alpha=r_opacity, edgecolor=r_col, linewidth=r_weight, zorder=2)
        ax.add_patch(circle_patch)
        
        t_size = float(st.session_state.target_config["size"]) * 4
        t_col = str(st.session_state.target_config["color"])
        t_marker = '*' if st.session_state.target_config["style"] == "star" else 'o'
        ax.scatter([cx_center.x], [cx_center.y], color=t_col, edgecolors='#ffffff', s=t_size, marker=t_marker, zorder=10)
        
        for lyr in detected_layers:
            meta = st.session_state.layer_meta[lyr]
            if not meta.get("visible", True):
                continue
                
            cat_pts = [p for p in pts if p.get('type', 'Unclassified') == lyr]
            if not cat_pts:
                continue
                
            pt_gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy([p['lon'] for p in cat_pts], [p['lat'] for p in cat_pts]), crs="EPSG:4326").to_crs(epsg=3857)
            
            c_style = meta.get("style", "dots")
            c_size = float(meta.get("size", 14))
            c_color = meta.get("color", "#003366")
            
            if c_style == 'modern-pin':
                ax.scatter(pt_gdf.geometry.x + (radius_val * 0.015), pt_gdf.geometry.y - (radius_val * 0.015), color='#000000', s=c_size*6, marker='o', alpha=0.25, zorder=4)
                ax.scatter(pt_gdf.geometry.x, pt_gdf.geometry.y, color=c_color, edgecolors='#0A1520', linewidths=0.6, s=c_size*6, marker='o', alpha=1.0, label=lyr, zorder=5)
                ax.scatter(pt_gdf.geometry.x, pt_gdf.geometry.y, color='#FFFFFF', s=c_size*1.2, marker='o', alpha=1.0, zorder=6)
            else:
                m_shape = 'o' if c_style == 'dots' else '^'
                ax.scatter(pt_gdf.geometry.x, pt_gdf.geometry.y, color=c_color, edgecolors='#ffffff', s=c_size*4, marker=m_shape, alpha=0.9, label=lyr, zorder=5)
        
        try: cx.add_basemap(ax, source=cx.providers.CartoDB.Positron, zorder=1)
        except Exception: pass
        
        ax.set_xlim(xmin - (radius_val*0.1), xmax + (radius_val*0.1))
        ax.set_ylim(ymin - (radius_val*0.1), ymax + (radius_val*0.1))
        ax.axis('off')
        ax.legend(loc='upper left', bbox_to_anchor=(0.02, 0.98), frameon=True, facecolor='#ffffff', edgecolor=(0.0, 0.2, 0.4, 0.1), fontsize=7)
        
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png', bbox_inches='tight', dpi=300)
        img_buf.seek(0)
        plt.close(fig)
        return img_buf
    except Exception:
        return None

# -----------------------------------------------------------------------------
# 5. CONTROL PANEL ARCHITECTURE (NATIVE STREAMLIT RIGHT PANEL CONTAINER)
# -----------------------------------------------------------------------------
# Using column segmentation to split the layout seamlessly without external JS panels
main_map_col, right_panel_col = st.columns([3, 1])

with right_panel_col:
    st.markdown("### WORKSPACE PANEL")
    
    # 1. Base Controller Block
    with st.expander("🌐 BASEMAP CONTROLLER", expanded=True):
        st.session_state.basemap_style = st.selectbox("Tile Layer Style", ["osm", "satellite", "carto"], index=["osm", "satellite", "carto"].index(st.session_state.basemap_style))
        st.session_state.show_labels = st.checkbox("Render Text Labels", value=st.session_state.show_labels)
        
    # 2. Functional Layer Group Creation Framework [NEW FEATURE]
    with st.expander("📁 CREATE LAYER GROUP", expanded=False):
        if detected_layers:
            group_name_input = st.text_input("Group Designation Name", placeholder="e.g., Priority Retail Hubs")
            selected_group_layers = []
            st.markdown("<p style='font-size:10px; font-weight:700; margin:0;'>Select Layers to Group:</p>", unsafe_allow_html=True)
            for lyr in detected_layers:
                # Filter out layers already contained inside another group structure
                is_grouped = any(lyr in g_info["layers"] for g_info in st.session_state.custom_groups.values())
                lbl_suffix = " (Grouped)" if is_grouped else ""
                if st.checkbox(f"{lyr}{lbl_suffix}", key=f"grp_sel_{lyr}"):
                    selected_group_layers.append(lyr)
            
            if st.button("ASSEMBLE LAYER GROUP", use_container_width=True):
                if group_name_input.strip() and selected_group_layers:
                    st.session_state.custom_groups[group_name_input.strip()] = {
                        "layers": selected_group_layers,
                        "collapsed": True
                    }
                    st.toast(f"Assembled Group: {group_name_input}", icon="📁")
                    st.columns(1) # Refresh context frame
                    st.rerun()
                else:
                    st.warning("Provide a name and check ≥ 1 layer.")
        else:
            st.caption("Scan an area to extract active operational layers.")

    # 3. Targets and Anchors Configuration Controls
    with st.expander("🎯 TARGET & BUFFER PROFILE", expanded=False):
        st.session_state.target_config["style"] = st.selectbox("Center Anchor", ["star", "circle"], index=0 if st.session_state.target_config["style"] == "star" else 1)
        st.session_state.target_config["color"] = st.color_picker("Anchor Core Hex", value=st.session_state.target_config["color"])
        st.session_state.target_config["size"] = st.slider("Anchor Scale", 10, 60, int(st.session_state.target_config["size"]))
        st.session_state.radius_config["color"] = st.color_picker("Radius Boundary Hex", value=st.session_state.radius_config["color"])
        st.session_state.radius_config["fill_opacity"] = st.slider("Buffer Opacity", 0.0, 1.0, float(st.session_state.radius_config["fill_opacity"]), step=0.01)
        st.session_state.radius_config["weight"] = st.slider("Boundary Thickness", 0.5, 8.0, float(st.session_state.radius_config["weight"]), step=0.5)

    st.markdown("---")
    st.markdown(f"**ACTIVE LAYERS ({len(active_records)})**")
    
    # 4. Managed Active Layers List Rendering Loop
    assigned_grouped_layers = []
    
    # Render Custom Assembled Groups First
    for g_title, g_info in list(st.session_state.custom_groups.items()):
        assigned_grouped_layers.extend(g_info["layers"])
        
        # Calculate total records inside the entire group boundary
        g_count = sum(len([p for p in active_records if p.get('type') == lyr]) for lyr in g_info["layers"])
        
        st.markdown(f"<div style='padding:4px; background:#e2e8f0; font-weight:700; font-size:11px; color:#003366; border-radius:2px; margin-top:6px;'>📁 GROUP: {g_title.upper()} ({g_count})</div>", unsafe_allow_html=True)
        
        # Batch Controller Settings inside Group Header Matrix
        g_vis = st.checkbox("Toggle Group Visibility", value=True, key=f"vis_g_{g_title}")
        g_style = st.selectbox("Batch Marker Style", ["dots", "pin", "modern-pin"], key=f"sty_g_{g_title}")
        g_size = st.slider("Batch Scale", 10, 40, 14, key=f"siz_g_{g_title}")
        g_color = st.color_picker("Batch Hex Override", value="#C9AB4C", key=f"col_g_{g_title}")
        apply_g = st.button("APPLY BATCH OVERRIDES", key=f"btn_g_{g_title}", use_container_width=True)
        
        if apply_g:
            for child_lyr in g_info["layers"]:
                if child_lyr in st.session_state.layer_meta:
                    st.session_state.layer_meta[child_lyr]["visible"] = g_vis
                    st.session_state.layer_meta[child_lyr]["style"] = g_style
                    st.session_state.layer_meta[child_lyr]["size"] = g_size
                    st.session_state.layer_meta[child_lyr]["color"] = g_color
            st.toast(f"Applied layout preferences to {g_title}", icon="⚡")
            
        if st.button("DISSOLVE GROUP STRUCTURE", key=f"del_g_{g_title}", use_container_width=True):
            del st.session_state.custom_groups[g_title]
            st.rerun()
            
        st.markdown("<div style='height:4px; border-bottom:2px dashed #C9AB4C;'></div>", unsafe_allow_html=True)

    # Render Standalone Layer Expanders
    for lyr in detected_layers:
        if lyr in assigned_grouped_layers:
            continue # Skipped because it is handled inside its parent layout group block above
            
        meta = st.session_state.layer_meta[lyr]
        lyr_records = [p for p in active_records if p.get('type', 'Unclassified') == lyr]
        
        with st.expander(f"📍 {lyr.upper()} ({len(lyr_records)})"):
            meta["visible"] = st.checkbox("Layer Visibility", value=meta.get("visible", True), key=f"vis_v_{lyr}")
            meta["style"] = st.selectbox("Marker Style Primitive", ["dots", "pin", "modern-pin"], index=["dots", "pin", "modern-pin"].index(meta.get("style", "dots")), key=f"sty_v_{lyr}")
            meta["size"] = st.slider("Marker Scale Bound", 10, 40, int(meta.get("size", 14)), key=f"siz_v_{lyr}")
            meta["color"] = st.color_picker("Marker Hex Color", value=meta.get("color", "#003366"), key=f"col_v_{lyr}")
            
            # Inline unique record tracking table listing
            for p in lyr_records:
                p_visible = p.get('visible', True)
                if st.checkbox(f"ID: {p.get('uid', 0)} | {p.get('name', 'Unknown')[:18]}", value=p_visible, key=f"poi_v_{p.get('uid')}"):
                    p['visible'] = True
                else:
                    p['visible'] = False

    st.markdown("---")
    # Native Instant Matplotlib Vector Image Exporter Engine Trigger Execution
    if st.button("GENERATE STATIC REPORT CANVAS", type="secondary", use_container_width=True):
        with st.spinner("Processing high-fidelity vectors..."):
            canvas_buffer = generate_report_canvas_image()
            if canvas_buffer:
                st.session_state.cached_export_buffer = canvas_buffer
                st.rerun()

# -----------------------------------------------------------------------------
# 6. ZERO-LATENCY MAP ARCHITECTURE FRAME RENDERING
# -----------------------------------------------------------------------------
with main_map_col:
    # Process visibility mutations inside real-time records payload
    sanatized_records = []
    for p in st.session_state.scanned_records:
        lyr_type = p.get('type', 'Unclassified')
        if lyr_type in st.session_state.layer_meta:
            # Drop record execution node if parent layer visibility mask is toggled off
            if not st.session_state.layer_meta[lyr_type].get("visible", True):
                continue
        if p.get('visible', True):
            sanatized_records.append(p)

    layer_meta_json = json.dumps(st.session_state.layer_meta)
    target_config_json = json.dumps(st.session_state.target_config)
    radius_config_json = json.dumps(st.session_state.radius_config)
    geojson_str = json.dumps(sanatized_records)

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
            body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #ffffff; overflow: hidden; font-family: 'Montserrat', sans-serif; }
            #map { height: 100vh; width: 100%; }
            .poi-text-label { background: #fff; border: 1px solid #003366; padding: 2px 4px; border-radius: 2px; font-size: 9px; font-family: 'Montserrat', sans-serif; font-weight: 700; white-space: nowrap; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .hide-labels .poi-text-label { display: none !important; }
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            // Initialization Pipeline with interactive UI hooks extracted
            const map = L.map('map', { 
                zoomControl: true, 
                attributionControl: false, 
                preferCanvas: true 
            }).setView([__LAT__, __LON__], 14);

            let layerMeta = __LAYER_META_JSON__;
            let targetConfig = __TARGET_CONFIG_JSON__;
            let radiusConfig = __RADIUS_CONFIG_JSON__;
            let pts = __GEOJSON__;

            const basemaps = {
                osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }),
                satellite: L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', { maxZoom: 20 }),
                carto: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 })
            };
            
            // Map Basemap Style preferences natively derived from state assignments
            let activeStyle = "__BASEMAP_STYLE__";
            basemaps[activeStyle].addTo(map);
            
            if (__SHOW_LABELS__ === false) {
                document.getElementById('map').classList.add('hide-labels');
            }

            // Render Center Buffer Rings
            L.circle([__LAT__, __LON__], {
                radius: __RADIUS__, color: radiusConfig.color, weight: parseFloat(radiusConfig.weight),
                fillColor: radiusConfig.color, fillOpacity: parseFloat(radiusConfig.fill_opacity)
            }).addTo(map);

            // Render Center Core Anchor Marker Flag
            const d = targetConfig.size; const c = targetConfig.color;
            const htmlElement = targetConfig.style === "star" 
                ? `<div style="background-color: ${c}; color: #ffffff; width: ${d}px; height: ${d}px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: ${d*0.5}px; border: 2px solid #ffffff; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">★</div>`
                : `<div style="background-color: ${c}; width: ${d}px; height: ${d}px; border-radius: 50%; border: 3px solid #ffffff; box-shadow: 0 2px 6px rgba(0,0,0,0.4);"></div>`;
            
            L.marker([__LAT__, __LON__], { 
                icon: L.divIcon({ className: 'custom-center-icon', html: htmlElement, iconSize: [d, d], iconAnchor: [d/2, d/2] }), zIndexOffset: 999999 
            }).addTo(map);

            // Vector Icon Factory Generator
            const generateMarkerElement = (color, styleMode, sizeDimension) => {
                const sDim = parseInt(sizeDimension);
                if (styleMode === "pin") {
                    return L.divIcon({ 
                        html: `<div class="custom-pin-container"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${sDim*1.3}" height="${sDim*1.3}"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="${color}" stroke="#ffffff" stroke-width="1.5"/></svg></div>`, 
                        className: '', iconSize: [sDim*1.3, sDim*1.3], iconAnchor: [sDim*0.65, sDim*1.3] 
                    });
                } else if (styleMode === "modern-pin") {
                    const w = sDim * 1.5;
                    const h = sDim * 2.2;
                    const customSvg = `
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 60" width="${w}" height="${h}">
                        <defs>
                            <filter id="shadowFilter-${color.replace('#','')}" x="-20%" y="-20%" width="150%" height="150%">
                                <feDropShadow dx="0" dy="4" stdDeviation="2.5" flood-color="#001F3F" flood-opacity="0.4"/>
                            </filter>
                        </defs>
                        <g filter="url(#shadowFilter-${color.replace('#','')})">
                            <path d="M20 20 L20 52" stroke="${color}" stroke-width="3.2" stroke-linecap="round"/>
                            <path d="M20 20 L20 52" stroke="#FFFFFF" stroke-width="1.0" stroke-linecap="round"/>
                            <circle cx="20" cy="20" r="13" fill="${color}" stroke="#0A1520" stroke-width="1.2" />
                            <circle cx="20" cy="20" r="4.2" fill="#FFFFFF"/>
                        </g>
                    </svg>`;
                    return L.divIcon({
                        html: `<div style="transform: translate(-50%, -88%); width: ${w}px; height: ${h}px;">${customSvg}</div>`,
                        className: '', iconSize: [w, h], iconAnchor: [0, 0]
                    });
                }
                return L.divIcon({ 
                    html: `<div style="background-color: ${color}; width: ${sDim}px; height: ${sDim}px; border-radius: 50%; border: 1.5px solid #ffffff; box-shadow: 0 1px 4px rgba(0,0,0,0.2);"></div>`, 
                    className: '', iconSize: [sDim, sDim], iconAnchor: [sDim/2, sDim/2] 
                });
            };

            // Multipoint Geolocation Rendering Block Pipeline
            pts.forEach(p => {
                const lyrKey = p.type || 'Unclassified';
                const meta = layerMeta[lyrKey] || { color: "#003366", style: "dots", size: 14 };
                
                const marker = L.marker([p.lat, p.lon], { icon: generateMarkerElement(meta.color, meta.style, meta.size) })
                                .bindPopup(`<b>${p.name}</b><br><span style="color:#888780;font-size:9px;">${p.type}</span>`);
                if (p.name && p.name !== 'Unknown') {
                    marker.bindTooltip(p.name, { permanent: true, direction: 'top', offset: [0, -10], className: 'poi-text-label' });
                }
                marker.addTo(map);
            });

            // Map Fitting Zoom Constraint Rules Logic
            if (pts.length > 0 && !__IS_STALE__) {
                const validMarkers = pts.map(p => L.marker([p.lat, p.lon]));
                const boundsGroup = L.featureGroup([L.marker([__LAT__, __LON__]), ...validMarkers]);
                map.fitBounds(boundsGroup.getBounds().pad(0.06));
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
                    .replace("__BASEMAP_STYLE__", str(st.session_state.basemap_style))
                    .replace("__SHOW_LABELS__", "true" if st.session_state.show_labels else "false")
                    .replace("__GLOBAL_MARKER_SIZE__", str(st.session_state.global_marker_size))
                    .replace("__GLOBAL_MARKER_COLOR__", str(st.session_state.global_marker_color))
                    .replace("__TARGET_CONFIG_JSON__", target_config_json)
                    .replace("__RADIUS_CONFIG_JSON__", radius_config_json)
                    .replace("__LAYER_META_JSON__", layer_meta_json)
                    .replace("__GEOJSON__", geojson_str))

    st.components.v1.html(leaflet_html, height=850, scrolling=False)
