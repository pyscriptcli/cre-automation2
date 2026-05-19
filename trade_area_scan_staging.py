import streamlit as st
import requests
import re
import json
import os

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
        
        .material-symbols-rounded, span[class*="material-symbols"] {
            font-family: 'Material Symbols Rounded' !important; font-weight: normal !important; font-style: normal !important; font-size: 18px !important; line-height: 1 !important; letter-spacing: normal !important; text-transform: none !important; display: inline-block !important; white-space: nowrap !important; word-wrap: normal !important; direction: ltr !important;
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
        div.stButton > button[kind="primary"]:hover p { color: #AA2E20 !important; }
        
        [data-testid="stSidebar"] .st-expander { border: 1px solid rgba(0, 51, 102, 0.05) !important; background-color: var(--white-clean) !important; border-radius: 2px !important; margin-bottom: 2px !important; overflow: hidden !important; }
        [data-testid="stSidebar"] .st-expander summary p { font-size: 5px !important; font-weight: 500 !important; }
        .stCheckbox label p { font-size: 10px !important; font-weight: 500 !important; }
        
        div[data-baseweb="checkbox"] input:checked + div, div[data-baseweb="checkbox"] div[aria-checked="true"] { background-color: var(--brand-midnight) !important; border-color: var(--brand-midnight) !important; }
        
        .stDeployButton, footer { display:none !important; }
        
        .brand-title { font-family: 'Cormorant Garamond', serif !important; font-style: italic; color: var(--brand-midnight); font-size: 30px; text-align: center; border-bottom: 1px solid var(--brand-gold); padding-bottom: 6px; margin-bottom: 30px; }
        .stTextInput label p, .stNumberInput label p { font-size: 9px !important; font-weight: 500 !important; letter-spacing: 0.5px; color: var(--text-muted) !important; }
        
        /* MODULE TOGGLE BUTTON STYLES */
        .module-toggle-container {
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
        }
        .module-toggle-btn {
            flex: 1;
            text-align: center;
            padding: 10px 0;
            cursor: pointer;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            background: transparent;
            border: 1px solid var(--brand-midnight);
            border-radius: 2px;
            transition: all 0.3s ease;
        }
        .module-toggle-btn.active {
            background: var(--brand-midnight);
            color: var(--white-clean);
            border-color: var(--brand-midnight);
        }
        .module-toggle-btn.inactive {
            background: transparent;
            color: var(--brand-midnight);
            border-color: rgba(0, 51, 102, 0.3);
        }
        .module-toggle-btn.inactive:hover {
            background: rgba(0, 51, 102, 0.05);
            border-color: var(--brand-midnight);
        }
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
if 'active_module' not in st.session_state: st.session_state.active_module = "SCANNER"

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
        name = f.get('name', 'Asset').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        class_type = f.get('type', 'Node').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        kml += f"<Placemark><name>{name}</name><description>{class_type}</description><Point><coordinates>{f['lon']},{f['lat']},0</coordinates></Point></Placemark>"
    return kml + '</Document></kml>'

# -----------------------------------------------------------------------------
# 3. SIDEBAR WORKSPACE WITH MODULE TOGGLE & SCANNER UI
# -----------------------------------------------------------------------------
with st.sidebar:
    # Module Toggle Buttons
    st.markdown('<div class="brand-title">Trade Area Scan</div>', unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("SCAN", use_container_width=True, type="secondary" if st.session_state.active_module == "EDITOR" else "primary"):
            st.session_state.active_module = "SCANNER"
            st.rerun()
    with col_b:
        if st.button("EDIT", use_container_width=True, type="secondary" if st.session_state.active_module == "SCANNER" else "primary"):
            st.session_state.active_module = "EDITOR"
            st.rerun()
    
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    
    # Conditionally render Scanner UI or Editor UI in sidebar
    if st.session_state.active_module == "SCANNER":
        # --- SCANNER MODULE SIDEBAR UI (PRESERVED ORIGINAL) ---
        # Dual-purpose Location Search & Coordinates Input
        location_input = st.text_input("LOCATION SEARCH OR COORDINATES", value=st.session_state.geo_coords, key="geo_coords_input", label_visibility="visible")
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
                        st.error("API Error: Nominatim Timeout")
                        lat_coord, lon_coord = 14.5995, 120.9842
            else:
                fallback_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", st.session_state.geo_coords)
                if fallback_match:
                    lat_coord, lon_coord = float(fallback_match.group(1)), float(fallback_match.group(2))
                else:
                    lat_coord, lon_coord = 14.5995, 120.9842

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
        adv_container = st.container()
        
        with adv_container:
            for cat_name, node_items in ADVANCED_CONFIG.items():
                matched = [item for item in node_items if search_query in item[0].lower()]
                if matched:
                    with st.expander(cat_name, expanded=(len(search_query) > 0)):
                        for label, tag in matched:
                            if st.checkbox(label, key=f"chk_adv_{cat_name}_{label}"): selected_tags.append(tag)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # ACTION BUTTONS (NON-PERSISTENT)
        if st.button("SCAN AREA", type="secondary", use_container_width=True, key="scan_btn"):
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

        if st.button("CLEAR ALL", type="primary", key="clear_btn"):
            st.session_state.scanned_records = []
            for key in list(st.session_state.keys()):
                if key.startswith("chk_"):
                    st.session_state[key] = False
            st.rerun()

        st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("JSON", json.dumps(st.session_state.scanned_records), "scan.json", "application/json", use_container_width=True)
        with col2:
            st.download_button("KML", compile_features_kml(st.session_state.scanned_records), "POIs.kml", "application/vnd.google-earth.kml+xml", use_container_width=True)

        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

        with st.popover("IMPORT FILE", use_container_width=True):
            imported_file = st.file_uploader("Select JSON", type=["json"], label_visibility="collapsed")
            if imported_file is not None:
                if st.button("LOAD", type="secondary", use_container_width=True):
                    try:
                        data = json.load(imported_file)
                        st.session_state.scanned_records = data.get("scanned_records", data)
                        st.session_state.geo_coords = data.get("coords", st.session_state.geo_coords)
                        st.session_state.geo_radius = data.get("radius", st.session_state.geo_radius)
                        st.rerun()
                    except Exception:
                        st.error("Invalid File")
    
    else:
        # --- EDITOR MODULE SIDEBAR UI ---
        st.markdown(
            "<div style='font-size: 10px; font-weight:600; color:#888780; margin-bottom:15px; text-align:center; text-transform:uppercase; letter-spacing:0.5px;'>"
            "Vector Engineering Workspace Mode"
            "</div>", 
            unsafe_allow_html=True
        )
        
        st.markdown(
            "<div style='font-size: 9px; font-weight: 500; color: #888780; line-height: 1.4; text-align: justify;'>"
            "Select assets directly on the map canvas or results log block to trigger the contextual styling control board overlay."
            "</div>", 
            unsafe_allow_html=True
        )
        
        st.markdown("<hr style='margin: 20px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>", unsafe_allow_html=True)
        
        # Export buttons for Editor mode
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("JSON", json.dumps(st.session_state.scanned_records), "editor_export.json", "application/json", use_container_width=True)
        with col2:
            st.download_button("KML", compile_features_kml(st.session_state.scanned_records), "editor_POIs.kml", "application/vnd.google-earth.kml+xml", use_container_width=True)

# -----------------------------------------------------------------------------
# 4. ZERO-LATENCY SPATIAL CANVAS (CONDITIONAL RENDERING BASED ON MODULE)
# -----------------------------------------------------------------------------
# Extract coordinates for rendering
coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", st.session_state.geo_coords)
if coord_match:
    lat_coord, lon_coord = float(coord_match.group(1)), float(coord_match.group(2))
else:
    lat_coord, lon_coord = 14.5995, 120.9842

radius_val = st.session_state.geo_radius

if st.session_state.active_module == "SCANNER":
    # --- SCANNER MODULE MAP (PRESERVED ORIGINAL) ---
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
            body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #ffffff; overflow: hidden; font-family: 'Montserrat', sans-serif; }
            #map { height: 100vh; width: 100%; }
            
            #minimal-basemap-panel {
                position: absolute; top: 110px; left: 50px; z-index: 1000;
                background: #ffffff; border-radius: 4px; border: 1px solid rgba(0, 51, 102, 0.1); background-clip: padding-box;
                display: none; flex-direction: column; padding: 4px; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); width: 150px;
            }
            #minimal-basemap-panel select {
                border: none; border-bottom: 1px solid #f0f0f0; padding: 6px; font-size: 10px; font-weight: 700; font-family: 'Montserrat', sans-serif;
                color: #003366; background: transparent; outline: none; cursor: pointer; width: 100%; text-transform: uppercase;
            }
            .minimal-label { font-size: 9px; font-weight: 700; padding: 6px; display: flex; align-items: center; gap: 4px; cursor: pointer; color: #888780; margin: 0; text-transform: uppercase; border-top: 1px solid #f8fafc;}

            #search-container { position: absolute; top: 10px; left: 54px; z-index: 1000; width: 300px; }
            #map-search {
                width: 100%; padding: 8px 12px; border: 1px solid rgba(0, 51, 102, 0.1); border-radius: 4px; background-clip: padding-box;
                font-size: 11px; font-family: 'Montserrat', sans-serif; font-weight: 600; color: #003366; background: #ffffff; outline: none; box-sizing: border-box; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08);
            }
            #map-search:focus { border-bottom: 2px solid #C9AB4C; }
            #search-results { position: absolute; top: 38px; left: 0; width: 100%; background: #ffffff; border-radius: 2px; display: none; max-height: 250px; overflow-x: hidden; overflow-y: auto; border: 1px solid rgba(0, 51, 102, 0.1); box-sizing: border-box; z-index: 1001; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); }
            .search-item { padding: 8px 12px; font-size: 10px; font-weight: 600; cursor: pointer; border-bottom: 1px solid #f8fafc;
