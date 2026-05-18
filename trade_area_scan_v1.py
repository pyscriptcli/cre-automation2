import streamlit as st
import requests
import re
import math
import json

# -----------------------------------------------------------------------------
# 1. HIGH-DENSITY BRUTE FORCE LIGHT MODE & FULL SCREEN OVERRIDES
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TRADE AREA SCAN",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        :root {
            --navy-brand: #001a3d;
            --white-clean: #ffffff;
            --gold-accent: #d4af37;
            --border-gray: #cbd5e1;
            --link-muted: #64748b;
        }
        
        /* FORCE UNYIELDING LIGHT MODE MATRIX ACROSS ALL STREAMLIT NODES */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], [data-testid="stMain"], .main, .block-container {
            background-color: var(--white-clean) !important;
            color: var(--navy-brand) !important;
            color-scheme: light !important;
        }
        
        /* RECOLOR TEXT, MARARKDOWN AND HEADER ELEMENTS TO NAVY BRAND ONLY */
        p, span, label, h1, h2, h3, h4, h5, h6, .stMarkdown, [data-testid="stExpander"] summary p {
            color: var(--navy-brand) !important;
        }
        
        /* RESTYLE OVERRIDE CONTROLS FOR INPUTS AND SELECTBOX dropdowns */
        div[data-baseweb="input"], div[data-baseweb="select"], input, select, .stSelectbox, .stTextInput, .stNumberInput {
            background-color: var(--white-clean) !important;
            color: var(--navy-brand) !important;
            border-radius: 4px !important;
            min-height: 32px !important;
        }
        
        /* ELIMINATE STREAMLIT HEADER ZONE */
        [data-testid="stHeader"], header, #stDecoration {
            height: 0px !important;
            min-height: 0px !important;
            display: none !important;
        }
        
        /* FORCE ROOT FLEX MATRIX TO PREVENT LAYOUT COLLAPSE */
        [data-testid="stAppViewContainer"] {
            display: flex !important;
            flex-direction: row !important;
            width: 100vw !important;
            height: 100vh !important;
            overflow: hidden !important;
        }
        
        /* FORCE SIDEBAR TO REMAIN FIXED, VISIBLE, AND UNCHANGED BY INTERNAL STATES */
        [data-testid="stSidebar"] {
            background-color: var(--white-clean) !important;
            color: var(--navy-brand) !important;
            border-right: 1px solid var(--border-gray) !important;
            width: 320px !important;
            min-width: 320px !important;
            max-width: 320px !important;
            transform: none !important;
            visibility: visible !important;
        }
        
        /* INTERCEPT AND DESTROY COLLAPSE CHEVRON CLICK TARGETS */
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        
        /* LOCK MAIN AREA TO FILL THE EXACT REMAINING SPACE CLEANLY */
        [data-testid="stMain"] {
            flex-grow: 1 !important;
            width: calc(100vw - 320px) !important;
            height: 100vh !important;
            overflow: hidden !important;
            margin: 0px !important;
            padding: 0px !important;
        }
        
        /* STRIP INNER PADDING FROM THE CONTENT BLOCK COMPONENT */
        .block-container, [data-testid="stAppViewBlockContainer"] {
            padding-top: 0rem !important; 
            padding-bottom: 0rem !important;
            padding-left: 0rem !important;
            padding-right: 0rem !important;
            max-width: 100% !important; 
            width: 100% !important;
            height: 100vh !important;
            margin: 0px !important;
        }
        
        /* REMOVE INNER GAP ELEMENTS IN ALL STREAMLIT WRAPPER BLOCKS */
        [data-testid="stVerticalBlock"], 
        [data-testid="stVerticalBlockWrapper"],
        .stElementContainer {
            gap: 0rem !important;
            padding: 0px !important;
            margin: 0px !important;
        }
        
        /* FORCE LEAFLET IFRAME TO MAP EXACTLY TO THE VIEWPORT WINDOW */
        iframe {
            height: 100vh !important;
            width: 100% !important;
            border: none !important;
            margin: 0px !important;
            padding: 0px !important;
            display: block !important;
        }
        
        [data-testid="stSidebarUserContent"] {
            padding-top: 24px !important;
            padding-left: 12px !important;
            padding-right: 12px !important;
        }
        
        .clear-link-container {
            text-align: center !important;
            margin-top: 0px !important;
            margin-bottom: 16px !important;
            width: 100% !important;
        }
        
        /* Hyperlink Emulation for Tertiary Button */
        button[kind="tertiary"] {
            background: transparent !important;
            border: none !important;
            color: var(--link-muted) !important;
            text-decoration: underline !important;
            font-weight: 600 !important;
            font-size: 11px !important;
            padding: 0 !important;
            margin: 0 !important;
            box-shadow: none !important;
            min-height: 0 !important;
            height: auto !important;
            display: inline-block !important;
        }
        button[kind="tertiary"]:hover {
            color: var(--navy-brand) !important;
        }
        
        [data-testid="stSidebar"] label p {
            color: var(--navy-brand) !important;
            font-weight: 800 !important;
            font-size: 10px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            margin-bottom: -6px !important;
        }
        
        div[data-baseweb="input"] { border: 1px solid var(--border-gray) !important; }
        div[data-baseweb="input"]:focus-within { border-color: var(--navy-brand) !important; }
        div[data-baseweb="select"] { border: 1px solid var(--border-gray) !important; }
        
        .action-tray div.stButton > button[kind="secondary"], div.stDownloadButton > button {
            background-color: var(--navy-brand) !important;
            color: var(--white-clean) !important;
            font-weight: 800 !important;
            font-size: 11px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            border: none !important;
            border-radius: 6px !important;
            width: 100% !important;
            padding: 6px !important;
            transition: all 0.1s ease-in-out !important;
            margin-top: 5px !important;
        }
        .action-tray div.stButton > button[kind="secondary"]:hover, div.stDownloadButton > button:hover {
            background-color: var(--gold-accent) !important;
            color: var(--navy-brand) !important;
        }
        
        [data-testid="stSidebar"] .st-expander {
            border: 1px solid var(--border-gray) !important;
            background-color: #f8fafc !important;
            border-radius: 4px !important;
            margin-bottom: 2px !important;
        }
        [data-testid="stSidebar"] .st-expander details summary {
            padding-top: 4px !important;
            padding-bottom: 4px !important;
        }
        
        .stDeployButton, footer { display:none !important; }
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
        "pin_color": "#e11d48",
        "radius_color": "#001a3d",
        "radius_opacity": 0.1,
        "poi_color": "#d4af37",
        "poi_opacity": 0.9
    }

def execute_global_purge():
    st.session_state.geo_coords = DEFAULT_COORDS
    st.session_state.geo_radius = DEFAULT_RADIUS
    st.session_state.scanned_records = []
    st.session_state.last_scan_lat = 14.6465
    st.session_state.last_scan_lon = 121.0371
    st.session_state.map_styles = {
        "pin_color": "#e11d48",
        "radius_color": "#001a3d",
        "radius_opacity": 0.1,
        "poi_color": "#d4af37",
        "poi_opacity": 0.9
    }
    for key in list(st.session_state.keys()):
        if key.startswith("chk_"): st.session_state[key] = False

POI_CONFIG = {
    "COMMERCIAL": [['Corporate Office', '"building"~"office|commercial",i'], ['IT/Tech Center', '"office"~"it|telecommunication",i'], ['Business Center', '"building"="commercial"'], ['Hospital', '"amenity"~"hospital|clinic",i'], ['Hotel', '"tourism"="hotel"'], ['Motel', '"tourism"="motel"']],
    "RETAIL": [['Mall/Dept Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"supermarket|grocery",i'], ['Convenience', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Hardware', '"shop"~"hardware|doityourself",i'], ['General Shops', '"shop"~"boutique|clothes|shoes",i']],
    "FOOD & BEVERAGES": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"'], ['Bar/Pub/Club', '"amenity"~"bar|pub|nightclub",i'], ['Bakery', '"shop"="bakery"']],
    "INDUSTRIAL & LOGISTICS": [
        ['Expressway Exits', '"highway"~"motorway_junction|toll_gantry",i'], 
        ['Ports & Terms', '"industrial"="port"'], 
        ['Mfg Plants', '"industrial"~"factory|manufacturing|processing",i'],
        ['Cold Storage', '"warehouse"~"cold_store|cold_storage",i'],
        ['Ind. Parks', '"landuse"~"industrial|industrial_estate",i'],
        ['Warehouses', '"building"~"warehouse|depot",i'],
        ['Storage Facs', '"building"="storage"'],
        ['Truck Routes', '"hgv"~"designated|yes",i']
    ],
    "GOV & INFRASTRUCTURE": [['City Hall', '"amenity"="townhall"'], ['Police Station', '"amenity"="police"'], ['Fire Station', '"amenity"="fire_station"'], ['Airport', '"aeroway"~"terminal|aerodrome",i']],
    "SCHOOLS": [['University', '"amenity"~"university|college",i'], ['K-12 School', '"amenity"="school"'], ['Vocational', '"amenity"="learning_centre"']]
}

ADVANCED_CONFIG = {
    "AMENITIES": [['ATM', '"amenity"="atm"'], ['Bank', '"amenity"="bank"'], ['Bench', '"amenity"="bench"'], ['Bicycle Parking', '"amenity"="bicycle_parking"'], ['Bicycle Rental', '"amenity"="bicycle_rental"'], ['Cinema', '"amenity"="cinema"'], ['Clinic', '"amenity"="clinic"'], ['Embassy', '"amenity"="embassy"'], ['Firestation', '"amenity"="fire_station"'], ['Fuel', '"amenity"="fuel"'], ['Hospital', '"amenity"="hospital"'], ['Library', '"amenity"="library"'], ['Music School', '"amenity"="music_school"'], ['Parking', '"amenity"="parking"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Police', '"amenity"="police"'], ['Letter Box', '"amenity"="letter_box"'], ['Post Office', '"amenity"="post_office"'], ['School/College', '"amenity"~"school|college",i'], ['Taxi', '"amenity"="taxi"'], ['Theatre', '"amenity"="theatre"'], ['Toilets', '"amenity"="toilets"'], ['University', '"amenity"="university"']],
    "PLACE OF WORSHIP": [['Church', '"religion"="christian"'], ['Mosque', '"religion"="muslim"'], ['Buddhist Temple', '"religion"="buddhist"'], ['Hindu Temple', '"religion"="hindu"'], ['Synagogue', '"religion"="jewish"'], ['Cemetery', '"landuse"="cemetery"'], ['Alpine Hut', '"tourism"="alpine_hut"'], ['Apartment', '"tourism"="apartment"'], ['Camp Site', '"tourism"="camp_site"'], ['Chalet', '"tourism"="chalet"'], ['Guest House', '"tourism"="guest_house"'], ['Hostel', '"tourism"="hostel"'], ['Hotel', '"tourism"="hotel"'], ['Motel', '"tourism"="motel"'], ['Casino', '"amenity"="casino"'], ['Spa', '"leisure"="spa"'], ['Sauna', '"leisure"="sauna"']],
    "FOOD & BEVERAGE": [['Bar', '"amenity"="bar"'], ['BBQ', '"amenity"="bbq"'], ['Biergarten', '"amenity"="biergarten"'], ['Cafe', '"amenity"="cafe"'], ['Fast food', '"amenity"="fast_food"'], ['Food court', '"amenity"="food_court"'], ['Ice cream', '"amenity"="ice_cream"'], ['Pub', '"amenity"="pub"'], ['Restaurant', '"amenity"="restaurant"']],
    "RETAIL_ADV": [['Beauty', '"shop"="beauty"'], ['Bicycle', '"shop"="bicycle"'], ['Books/Stationary', '"shop"~"books|stationary",i'], ['Car', '"shop"="car"'], ['Chemist', '"shop"="chemist"'], ['Clothes', '"shop"="clothes"'], ['Copyshop', '"shop"="copyshop"'], ['Cosmetics', '"shop"="cosmetics"'], ['Department store', '"shop"="department_store"'], ['DIY/hardware', '"shop"~"hardware|doityourself",i'], ['Garden centre', '"shop"="garden_centre"'], ['General', '"shop"="general"'], ['Gift', '"shop"="gift"'], ['Hairdresser', '"shop"="hairdresser"'], ['Jewelry', '"shop"="jewelry"'], ['Kiosk', '"shop"="kiosk"'], ['Leather', '"shop"="leather"'], ['Marketplace', '"amenity"="marketplace"'], ['Musical instrument', '"shop"="musical_instrument"'], ['Optician', '"shop"="optician"'], ['Pets', '"shop"="pets"'], ['Phone', '"shop"="mobile_phone"'], ['Photo', '"shop"="photo"'], ['Shoes', '"shop"="shoes"'], ['Shopping centre', '"shop"="mall"'], ['Textiles', '"shop"="textiles"'], ['Toys', '"shop"="toys"']],
    "SPORTS": [['American football', '"sport"="american_football"'], ['Baseball', '"sport"="baseball"'], ['Basketball', '"sport"="basketball"'], ['Cycling', '"sport"="cycling"'], ['Gymnastics', '"sport"="gymnastics"'], ['Golf', '"sport"="golf"'], ['Hockey', '"sport"="hockey"'], ['Horse racing', '"sport"="horse_racing"'], ['Ice hockey', '"sport"="ice_hockey"'], ['Soccer', '"sport"="soccer"'], ['Sports centre', '"leisure"="sports_centre"'], ['Surfing', '"sport"="surfing"'], ['Swimming', '"sport"="swimming"'], ['Tennis', '"sport"="tennis"'], ['Volleyball', '"sport"="volleyball"']],
    "MISCELLANEOUS": [['Busstop', '"highway"="bus_stop"'], ['E-bike charging', '"amenity"="charging_station"'], ['Kindergarten', '"amenity"="kindergarten"'], ['Marketplace', '"amenity"="marketplace"'], ['Office', '"office"="yes"'], ['Recycling', '"amenity"="recycling"'], ['Travel agency', '"shop"="travel_agency"'], ['Defibrillator - AED', '"emergency"="defibrillator"'], ['Fire hose/exting.', '"emergency"~"fire_hose|fire_extinguisher",i'], ['Fixme', '"fixme"~".",i'], ['Note-Node', '"type"="node"'], ['Note-Way', '"type"="way"'], ['Construction', '"landuse"="construction"'], ['Image', '"image"~".",i'], ['Public camera', '"man_made"="surveillance"'], ['City', '"place"="city"'], ['Town', '"place"="town"'], ['Village', '"place"="village"'], ['Hamlet', '"place"="hamlet"'], ['Suburb', '"place"="suburb"']]
}

# -----------------------------------------------------------------------------
# 3. KML COMPILATION ENGINES
# -----------------------------------------------------------------------------
def compile_radius_kml(lat, lon, r_meters):
    kml = f'<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scan Radius</name><Placemark><name>Buffer Zone</name><Style><LineStyle><color>ff3d1a00</color><width>3</width></LineStyle><PolyStyle><fill>0</fill></PolyStyle></Style><Polygon><outerBoundaryIs><LinearRing><coordinates>'
    for i in range(37):
        angle = (i * 10) * math.pi / 180
        d_lat = (r_meters / 6371000) * math.cos(angle)
        d_lon = (r_meters / (6371000 * math.cos(lat * math.pi / 180))) * math.sin(angle)
        kml += f"{lon + (d_lon * 180 / math.pi)},{lat + (d_lat * 180 / math.pi)},0 "
    return kml + '</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></Document></kml>'

def compile_features_kml(features):
    kml = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scanned POIs</name>'
    for f in features:
        name = f.get('name', 'Asset').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        class_type = f.get('type', 'Node').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        kml += f"<Placemark><name>{name}</name><description>{class_type}</description><Point><coordinates>{f['lon']},{f['lat']},0</coordinates></Point></Placemark>"
    return kml + '</Document></kml>'

# -----------------------------------------------------------------------------
# 4. SIDEBAR WORKSPACE
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="clear-link-container">', unsafe_allow_html=True)
    if st.button("Clear All", key="master_purge_btn", type="tertiary"):
        execute_global_purge()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # NATIVE PROJECT INPUT FILE STREAM FOR PARSING SAVED JSON SETTINGS
    st.markdown("<p style='color:#001a3d; font-size:10px; font-weight:800; margin-top:0px; margin-bottom:4px;'>IMPORT CONFIGURATION</p>", unsafe_allow_html=True)
    imported_project = st.file_uploader("Upload JSON configuration", type=["json"], label_visibility="collapsed")
    if imported_project is not None:
        try:
            config_payload = json.load(imported_project)
            st.session_state.geo_coords = config_payload.get("geo_coords", DEFAULT_COORDS)
            st.session_state.geo_radius = config_payload.get("geo_radius", DEFAULT_RADIUS)
            st.session_state.scanned_records = config_payload.get("scanned_records", [])
            st.session_state.last_scan_lat = config_payload.get("last_scan_lat", 14.6465)
            st.session_state.last_scan_lon = config_payload.get("last_scan_lon", 121.0371)
            if "map_styles" in config_payload:
                st.session_state.map_styles = config_payload["map_styles"]
            st.rerun()
        except Exception as err:
            st.sidebar.error("Corrupted Project Structure")

    st.markdown("<hr style='margin: 10px 0; border-color: #cbd5e1;'>", unsafe_allow_html=True)

    coords_val = st.text_input("Target Coordinates", key="geo_coords")
    radius_val = st.number_input("Radius (Meters)", min_value=100, max_value=50000, key="geo_radius", step=100)

    coord_match = re.match(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", coords_val)
    lat_coord, lon_coord = (float(coord_match.group(1)), float(coord_match.group(2))) if coord_match else (14.6465, 121.0371)

    search_query = st.text_input("Filter Catalog", placeholder="Search tags...").lower()
    
    selected_tags = []
    
    for cat_name, node_items in POI_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                cols = st.columns(2)
                for i, (label, tag) in enumerate(matched):
                    with cols[i % 2]:
                        if st.checkbox(label, key=f"chk_{cat_name}_{label}"): 
                            selected_tags.append(tag)

    for cat_name, node_items in ADVANCED_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(f"ADV - {cat_name}", expanded=(len(search_query) > 0)):
                cols = st.columns(2)
                for i, (label, tag) in enumerate(matched):
                    with cols[i % 2]:
                        if st.checkbox(label, key=f"chk_adv_{cat_name}_{label}"): 
                            selected_tags.append(tag)

    st.markdown("<hr style='margin: 10px 0; border-color: #cbd5e1;'>", unsafe_allow_html=True)
    
    st.markdown('<div class="action-tray">', unsafe_allow_html=True)
    if st.button("🚀 SCAN AREA", use_container_width=True):
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
                    else: st.sidebar.error(f"Error {res.status_code}")
                except Exception as e: st.sidebar.error("Timeout")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<p style='color:#001a3d; font-size:10px; font-weight:800; margin-top:15px; margin-bottom:0;'>DATA EXPORTS</p>", unsafe_allow_html=True)
    exp_fmt = st.selectbox("Format", ["Select Format...", "Export Radius (KML)", "Export POIs (KML)", "Export Project (JSON)"], label_visibility="collapsed")
    
    if exp_fmt == "Export Radius (KML)":
        st.download_button("Download File", compile_radius_kml(lat_coord, lon_coord, radius_val), f"Radius_{radius_val}m.kml", "application/vnd.google-earth.kml+xml")
    elif exp_fmt == "Export POIs (KML)":
        st.download_button("Download File", compile_features_kml(st.session_state.scanned_records), "POIs.kml", "application/vnd.google-earth.kml+xml", disabled=not st.session_state.scanned_records)
    elif exp_fmt == "Export Project (JSON)":
        project_bundle = {
            "geo_coords": coords_val,
            "geo_radius": radius_val,
            "scanned_records": st.session_state.scanned_records,
            "last_scan_lat": st.session_state.last_scan_lat,
            "last_scan_lon": st.session_state.last_scan_lon,
            "map_styles": st.session_state.map_styles
        }
        st.download_button("Download Project", json.dumps(project_bundle, indent=2), "trade_area_scan_project.json", "application/json")

# -----------------------------------------------------------------------------
# 5. ZERO-LATENCY SPATIAL CANVAS (FULL-BLEED SPLIT VIEW)
# -----------------------------------------------------------------------------
geojson_str = json.dumps(st.session_state.scanned_records)
render_lat = lat_coord
render_lon = lon_coord

is_stale = "true" if (lat_coord != st.session_state.last_scan_lat or lon_coord != st.session_state.last_scan_lon) else "false"
style_bundle_str = json.dumps(st.session_state.map_styles)

leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #f8fafc; overflow: hidden; }
        #map { height: 100vh; width: 100%; }
        
        /* UNYIELDING MAP CONTROLS COLUMN SEATED DIRECTLY UNDER ZOOM BUTTONS */
        #map-action-toolbar {
            position: absolute;
            top: 80px;
            left: 12px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        .toolbar-trigger-btn {
            background: #ffffff;
            width: 30px;
            height: 30px;
            border-radius: 4px;
            box-shadow: 0 1px 5px rgba(0,0,0,0.3);
            border: 1px solid rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 13px;
            user-select: none;
        }
        .toolbar-trigger-btn:hover { background: #f1f5f9; }
        
        /* OVERLAY CONTROL SLIDE OUT MENU BLOCKS */
        .toolbar-floating-menu {
            position: absolute;
            left: 42px;
            background: #ffffff;
            border-radius: 6px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.15);
            border: 1px solid #cbd5e1;
            padding: 10px;
            font-family: 'Arial', sans-serif;
            color: #001a3d;
            width: 165px;
            display: none;
        }
        #basemap-menu-container { top: 0px; }
        #style-menu-container { top: 35px; }
        
        .panel-row { margin-bottom: 8px; }
        .panel-row:last-child { margin-bottom: 0; }
        .panel-row label {
            display: block;
            font-size: 8px;
            font-weight: 800;
            margin-bottom: 3px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .panel-row select, .panel-row input[type="text"] {
            width: 100%;
            font-size: 10px;
            padding: 3px;
            border-radius: 3px;
            border: 1px solid #cbd5e1;
            color: #001a3d;
            box-sizing: border-box;
        }
        
        .color-presets-matrix {
            display: flex;
            gap: 4px;
            margin-bottom: 4px;
        }
        .preset-color-dot {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            cursor: pointer;
            border: 1px solid rgba(0,0,0,0.15);
        }
        .style-slider-input {
            width: 100%;
            margin: 2px 0 0 0;
            cursor: pointer;
        }

        /* LAYER DATA INDEX CONSOLE (TOP-RIGHT RECTANGLE WALL) */
        #scan-results-panel {
            position: absolute;
            top: 12px;
            right: 12px;
            z-index: 1000;
            background: #ffffff;
            width: 270px;
            max-height: calc(100vh - 40px);
            border-radius: 6px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.15);
            font-family: 'Arial', sans-serif;
            border: 1px solid #cbd5e1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .results-header {
            background: #001a3d;
            color: #ffffff;
            padding: 8px 12px;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .results-badge {
            background: #d4af37;
            color: #001a3d;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 9px;
            font-weight: 900;
        }
        .results-list {
            overflow-y: auto;
            flex-grow: 1;
            padding: 4px 0;
        }
        
        /* CATEGORIZED ACCORDION COMPONENT LAYOUT MATRIX */
        .layer-category-block {
            border-bottom: 1px solid #f1f5f9;
        }
        .layer-category-header {
            background: #f8fafc;
            padding: 6px 10px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            user-select: none;
        }
        .layer-category-header:hover { background: #cbd5e1; }
        .layer-header-left {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            font-weight: 700;
            color: #001a3d;
        }
        .layer-header-left input[type="checkbox"] { transform: scale(0.9); margin: 0; cursor: pointer; }
        .layer-chevron { font-size: 9px; color: #64748b; font-weight: bold; }
        
        .layer-category-items {
            padding: 2px 0;
        }
        .layer-category-items.collapsed { display: none !important; }
        
        .results-item {
            padding: 5px 12px 5px 28px;
            font-size: 11px;
            color: #334155;
            cursor: pointer;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .results-item:hover {
            background: #f1f5f9;
            color: #d4af37;
            font-weight: 700;
        }
        .no-results {
            padding: 24px 16px;
            text-align: center;
            font-size: 11px;
            color: #64748b;
            font-style: italic;
        }
        
        .poi-text-label {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid #001a3d;
            border-radius: 3px;
            padding: 1px 4px;
            font-size: 10px;
            font-weight: 700;
            color: #001a3d;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            white-space: nowrap;
        }
        .hide-labels .poi-text-label { display: none !important; }
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div id="map-action-toolbar">
        <div class="toolbar-trigger-btn" title="Basemap Config" onclick="toggleMenuPanel('basemap-menu-container')">🗺️</div>
        <div class="toolbar-trigger-btn" title="Style Adjustments" onclick="toggleMenuPanel('style-menu-container')">✏️</div>
    </div>
    
    <div id="basemap-menu-container" class="toolbar-floating-menu">
        <div class="panel-row">
            <label>Map View Style</label>
            <select id="basemap-select" onchange="switchActiveBasemap(this.value)">
                <option value="osm">OpenStreetMap</option>
                <option value="satellite">Google Satellite</option>
                <option value="carto">Carto Light</option>
            </select>
        </div>
        <div class="panel-row" style="display:flex; align-items:center; gap:6px; margin-top:4px;">
            <input type="checkbox" id="label-toggle-chk" style="margin:0; transform:scale(0.9);" onchange="toggleLabelsMatrix(this.checked)">
            <label style="margin:0; cursor:pointer;" for="label-toggle-chk">Show Text Labels</label>
        </div>
    </div>
    
    <div id="style-menu-container" class="toolbar-floating-menu">
        <div class="panel-row">
            <label>Center Pin Color</label>
            <div class="color-presets-matrix">
                <div class="preset-color-dot" style="background:#e11d48;" onclick="setCustomElementStyle('pin', '#e11d48')"></div>
                <div class="preset-color-dot" style="background:#2563eb;" onclick="setCustomElementStyle('pin', '#2563eb')"></div>
                <div class="preset-color-dot" style="background:#16a34a;" onclick="setCustomElementStyle('pin', '#16a34a')"></div>
            </div>
            <input type="text" id="hex-pin-input" placeholder="#e11d48" onchange="setCustomElementStyle('pin', this.value)">
        </div>
        
        <div class="panel-row">
            <label>Radius Circle</label>
            <div class="color-presets-matrix">
                <div class="preset-color-dot" style="background:#001a3d;" onclick="setCustomElementStyle('radius', '#001a3d')"></div>
                <div class="preset-color-dot" style="background:#7c3aed;" onclick="setCustomElementStyle('radius', '#7c3aed')"></div>
                <div class="preset-color-dot" style="background:#ea580c;" onclick="setCustomElementStyle('radius', '#ea580c')"></div>
            </div>
            <input type="text" id="hex-radius-input" placeholder="#001a3d" onchange="setCustomElementStyle('radius', this.value)">
            <input type="range" id="opac-radius-slider" class="style-slider-input" min="0" max="1" step="0.05" oninput="setCustomElementOpacity('radius', this.value)">
        </div>
        
        <div class="panel-row">
            <label>POI Points Color</label>
            <div class="color-presets-matrix">
                <div class="preset-color-dot" style="background:#d4af37;" onclick="setCustomElementStyle('poi', '#d4af37')"></div>
                <div class="preset-color-dot" style="background:#06b6d4;" onclick="setCustomElementStyle('poi', '#06b6d4')"></div>
                <div class="preset-color-dot" style="background:#ec4899;" onclick="setCustomElementStyle('poi', '#ec4899')"></div>
            </div>
            <input type="text" id="hex-poi-input" placeholder="#d4af37" onchange="setCustomElementStyle('poi', this.value)">
            <input type="range" id="opac-poi-slider" class="style-slider-input" min="0" max="1" step="0.05" oninput="setCustomElementOpacity('poi', this.value)">
        </div>
    </div>

    <div id="scan-results-panel">
        <div class="results-header">
            <span>Layers & POIs</span>
            <div class="results-badge" id="results-count">0</div>
        </div>
        <div class="results-list" id="results-list-box"></div>
    </div>

    <script>
        const map = L.map('map', { zoomControl: true, attributionControl: false }).setView([__LAT__, __LON__], 14);
        
        const basemaps = {
            osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }),
            satellite: L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', { maxZoom: 20 }),
            carto: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 })
        };
        
        // RECONSTRUCT ARCHIVE SYSTEM FALLBACK STYLE PRESETS
        const defaults = __DEFAULTS__;
        let p_pinColor = localStorage.getItem('ts_style_pin') || defaults.pin_color;
        let p_radiusColor = localStorage.getItem('ts_style_radius') || defaults.radius_color;
        let p_radiusOpac = parseFloat(localStorage.getItem('ts_style_radius_opac') || defaults.radius_opacity);
        let p_poiColor = localStorage.getItem('ts_style_poi') || defaults.poi_color;
        let p_poiOpac = parseFloat(localStorage.getItem('ts_style_poi_opac') || defaults.poi_opacity);

        document.getElementById('hex-pin-input').value = p_pinColor;
        document.getElementById('hex-radius-input').value = p_radiusColor;
        document.getElementById('opac-radius-slider').value = p_radiusOpac;
        document.getElementById('hex-poi-input').value = p_poiColor;
        document.getElementById('opac-poi-slider').value = p_poiOpac;

        let activeBasemapKey = localStorage.getItem('ts_persistent_basemap') || 'osm';
        if (!basemaps[activeBasemapKey]) activeBasemapKey = 'osm';
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
        
        function toggleMenuPanel(panelId) {
            const el = document.getElementById(panelId);
            const activeNow = el.style.display === 'block';
            document.querySelectorAll('.toolbar-floating-menu').forEach(p => p.style.display = 'none');
            if (!activeNow) el.style.display = 'block';
        }
        
        // PLOT MAP BASE LAYERS AND ASSIGN VARIABLE HANDLES
        const centerMarker = L.circleMarker([__LAT__, __LON__], {
            radius: 7, fillColor: p_pinColor, color: "#ffffff", weight: 2, opacity: 1, fillOpacity: 1
        }).addTo(map).bindPopup("<b>TARGET COORDINATES</b>");
        
        const radiusCircle = L.circle([__LAT__, __LON__], {
            radius: __RADIUS__, color: p_radiusColor, weight: 2, fillColor: p_radiusColor, fillOpacity: p_radiusOpac
        }).addTo(map);
        
        // INITIALIZE POINT RECONSTRUCTION AND GROUP LAYERS CONTROL
        const pts = __GEOJSON__;
        const categoryMap = {};
        const layerGroupsRef = {};
        
        pts.forEach(p => {
            const layerKey = p.type || 'Unclassified';
            if (!categoryMap[layerKey]) categoryMap[layerKey] = [];
            categoryMap[layerKey].push(p);
        });
        
        Object.keys(categoryMap).forEach(key => {
            layerGroupsRef[key] = L.layerGroup().addTo(map);
            categoryMap[key].forEach(p => {
                const marker = L.circleMarker([p.lat, p.lon], {
                    radius: 5, fillColor: p_poiColor, color: "#001a3d", weight: 1, opacity: 1, fillOpacity: p_poiOpac
                }).bindPopup("<b>" + p.name + "</b><br>" + p.type);
                
                if (p.name && p.name !== 'Unknown') {
                    marker.bindTooltip(p.name, {
                        permanent: true, direction: 'top', offset: [0, -4], className: 'poi-text-label'
                    });
                }
                marker.addTo(layerGroupsRef[key]);
            });
        });

        // POPULATE INTERACTIVE ACCORDION SECTIONS INSIDE RIGHT OVERLAY LIST
        const listBox = document.getElementById('results-list-box');
        document.getElementById('results-count').innerText = pts.length;
        
        if (pts.length === 0) {
            listBox.innerHTML = '<div class="no-results">No active scan data.</div>';
        } else {
            let htmlPayload = '';
            Object.keys(categoryMap).forEach(catName => {
                htmlPayload += `
                    <div class="layer-category-block">
                        <div class="layer-category-header" onclick="toggleAccordionCollapse('${catName}')">
                            <div class="layer-header-left">
                                <input type="checkbox" checked onclick="event.stopPropagation(); toggleCategoryVisibility('${catName}', this.checked)">
                                <span>${catName} (${categoryMap[catName].length})</span>
                            </div>
                            <span class="layer-chevron" id="chevron-${catName}">▼</span>
                        </div>
                        <div class="layer-category-items collapsed" id="items-${catName}">
                `;
                categoryMap[catName].forEach(p => {
                    htmlPayload += `
                        <div class="results-item" onclick="flyToAndHighlightPoint(${p.lat}, ${p.lon})">
                            ${p.name || 'Unknown Location'}
                        </div>
                    `;
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
            if (panel.classList.contains('collapsed')) {
                panel.classList.remove('collapsed');
                chev.innerText = '▲';
            } else {
                panel.classList.add('collapsed');
                chev.innerText = '▼';
            }
        }

        function flyToAndHighlightPoint(lat, lon) {
            map.flyTo([lat, lon], 17);
            map.eachLayer(layer => {
                if (layer instanceof L.CircleMarker && layer.getLatLng) {
                    const loc = layer.getLatLng();
                    if (Math.abs(loc.lat - lat) < 0.00001 && Math.abs(loc.lng - lon) < 0.00001) {
                        setTimeout(() => layer.openPopup(), 300);
                    }
                }
            });
        }

        // CONTROL STYLE ELEMENT SETTERS LIVE VIA CANVAS PARAMETERS
        function setCustomElementStyle(layerType, colorHex) {
            if(!colorHex.startsWith('#') && colorHex.length === 6) colorHex = '#' + colorHex;
            if (layerType === 'pin') {
                centerMarker.setStyle({ fillColor: colorHex });
                localStorage.setItem('ts_style_pin', colorHex);
            } else if (layerType === 'radius') {
                radiusCircle.setStyle({ color: colorHex, fillColor: colorHex });
                localStorage.setItem('ts_style_radius', colorHex);
            } else if (layerType === 'poi') {
                p_poiColor = colorHex;
                Object.keys(layerGroupsRef).forEach(k => {
                    layerGroupsRef[k].eachLayer(m => m.setStyle({ fillColor: colorHex }));
                });
                localStorage.setItem('ts_style_poi', colorHex);
            }
        }

        function setCustomElementOpacity(layerType, val) {
            const opac = parseFloat(val);
            if (layerType === 'radius') {
                radiusCircle.setStyle({ fillOpacity: opac });
                localStorage.setItem('ts_style_radius_opac', opac);
            } else if (layerType === 'poi') {
                p_poiOpac = opac;
                Object.keys(layerGroupsRef).forEach(k => {
                    layerGroupsRef[k].eachLayer(m => m.setStyle({ fillOpacity: opac }));
                });
                localStorage.setItem('ts_style_poi_opac', opac);
            }
        }
        
        if (pts.length > 0 && !__IS_STALE__) {
            const bounds = L.featureGroup([L.marker([__LAT__, __LON__]), ...pts.map(p => L.marker([p.lat, p.lon]))]).getBounds();
            map.fitBounds(bounds.pad(0.1));
        } else {
            map.setView([__LAT__, __LON__], 15);
        }
        
        map.on('contextmenu', function(e) {
            const lat = e.latlng.lat.toFixed(5);
            const lon = e.latlng.lng.toFixed(5);
            const coordString = lat + ", " + lon;
            
            navigator.clipboard.writeText(coordString).then(() => {
                L.popup()
                    .setLatLng(e.latlng)
                    .setContent("<div style='font-family:sans-serif;font-size:11px;'>Copied:<br><b>" + coordString + "</b></div>")
                    .openOn(map);
            });
        });
        
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
                .replace("__DEFAULTS__", style_bundle_str)
                .replace("__GEOJSON__", geojson_str))

st.components.v1.html(leaflet_html, scrolling=False)
