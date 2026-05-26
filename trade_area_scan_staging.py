import streamlit as st
import requests
import re
import json
import os
import math
import osmnx as ox
import pandas as pd

# =============================================================================
# [ CONFIGURATION BLOCK: STREAMLIT THEME & SETUP ]
# Ensures the app always loads in Light Mode to match the custom CSS variables.
# =============================================================================
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\n")

st.set_page_config(page_title="Trade Area Scan Playground", layout="wide", initial_sidebar_state="expanded")

# =============================================================================
# [ CONFIGURATION BLOCK: GLOBAL CSS STYLES ]
# Edit the :root variables below to change the primary brand colors globally.
# =============================================================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Montserrat:wght@400;500;600;700;800&display=swap');
        
        :root {
            --brand-midnight: #003366 !important; /* Primary Dark Blue */
            --brand-gold: #C9AB4C !important;     /* Primary Gold Accent */
            --brand-dark: #001F3F !important;     
            --white-clean: #ffffff !important;
            --bg-offwhite: #f8fafc !important;    /* Sidebar Background */
            --text-muted: #888780 !important;
            --soft-shadow: 0 4px 12px rgba(0, 51, 102, 0.08) !important;
        }
        
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: var(--white-clean) !important; color: var(--brand-midnight) !important; font-family: 'Montserrat', sans-serif !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: var(--bg-offwhite) !important; color: var(--brand-midnight) !important;
            border-right: 1px solid rgba(0, 51, 102, 0.08) !important; width: 280px !important; min-width: 280px !important; max-width: 280px !important;
            box-shadow: 2px 0 15px rgba(0,0,0,0.03) !important;
        }
        
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"], [data-testid="stHeader"], header, #stDecoration, .stDeployButton, footer { display: none !important; }
        ::-webkit-scrollbar { width: 0px !important; background: transparent !important; }
        * { scrollbar-width: none !important; -ms-overflow-style: none !important; }
        
        p, label, h1, h2, h3, h4, h5, h6, .stMarkdown, [data-testid="stExpander"] summary p { color: var(--brand-midnight) !important; font-family: 'Montserrat', sans-serif !important; }
        
        [data-testid="stAppViewContainer"] { display: flex !important; flex-direction: row !important; width: 100vw !important; height: 100vh !important; overflow: hidden !important; }
        [data-testid="stMain"] { flex-grow: 1 !important; width: calc(100vw - 280px) !important; height: 100vh !important; overflow: hidden !important; margin: 0px !important; padding: 0px !important; }
        .block-container, [data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"], .stElementContainer { padding: 0px !important; margin: 0px !important; max-width: 100% !important; gap: 0rem !important; }
        iframe { height: 100vh !important; width: 100% !important; border: none !important; display: block !important; }
        
        [data-testid="stSidebarUserContent"] { padding-top: 12px !important; padding-left: 12px !important; padding-right: 12px !important; height: 100vh !important; overflow-y: auto !important; overflow-x: hidden !important; }
        
        div[data-baseweb="input"], div[data-baseweb="select"] { background-color: transparent !important; border: none !important; border-bottom: 1px solid rgba(201, 171, 76, 0.5) !important; border-radius: 0px !important; box-shadow: none !important; }
        div[data-baseweb="input"]:focus-within { border-bottom: 2px solid var(--brand-gold) !important; }
        
        /* Primary Buttons Customization */
        div.stButton > button[kind="secondary"], div.stDownloadButton > button { background-color: var(--brand-midnight) !important; border: 1px solid var(--brand-midnight) !important; border-radius: 2px !important; width: 100% !important; padding: 6px !important; box-shadow: var(--soft-shadow) !important; transition: all 0.3s ease !important; }
        div.stButton > button[kind="secondary"]:hover, div.stDownloadButton > button:hover { background-color: var(--brand-gold) !important; border-color: var(--brand-gold) !important; }
        div.stButton > button[kind="secondary"] p, div.stDownloadButton > button p { color: var(--white-clean) !important; font-weight: 700 !important; font-size: 9px !important; text-transform: uppercase !important; letter-spacing: 1px; }
        
        /* Secondary Action Buttons (e.g. Clear All) */
        div.stButton > button[kind="primary"] { background: transparent !important; border: none !important; color: var(--text-muted) !important; box-shadow: none !important; padding: 0 !important; margin-top: 2px; display: inline-flex; }
        div.stButton > button[kind="primary"] p { color: var(--text-muted) !important; font-size: 9px !important; font-weight: 600 !important; text-decoration: none !important; text-transform: uppercase; }
        div.stButton > button[kind="primary"]:hover p { color: #AA2E20 !important; }
        
        [data-testid="stSidebar"] .st-expander { border: 1px solid rgba(0, 51, 102, 0.05) !important; background-color: var(--white-clean) !important; border-radius: 2px !important; margin-bottom: 2px !important; overflow: hidden !important; }
        [data-testid="stSidebar"] .st-expander summary p { font-size: 5px !important; font-weight: 500 !important; }
        .stCheckbox label p { font-size: 10px !important; font-weight: 500 !important; }
        div[data-baseweb="checkbox"] input:checked + div, div[data-baseweb="checkbox"] div[aria-checked="true"] { background-color: var(--brand-midnight) !important; border-color: var(--brand-midnight) !important; }
        
        .brand-title { font-family: 'Cormorant Garamond', serif !important; font-style: italic; color: var(--brand-midnight); font-size: 30px; text-align: center; border-bottom: 1px solid var(--brand-gold); padding-bottom: 6px; margin-bottom: 15px; }
        .stTextInput label p, .stNumberInput label p { font-size: 9px !important; font-weight: 500 !important; letter-spacing: 0.5px; color: var(--text-muted) !important; }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# [ CORE LOGIC: HAVERSINE DISTANCE FILTER ]
# Purges any coordinate outside the exact radius mathematically.
# =============================================================================
def calculate_haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Radius of Earth in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# =============================================================================
# [ CONFIGURATION BLOCK: SESSION STATE INITIALIZATION ]
# =============================================================================
DEFAULT_COORDS = "14.5995, 120.9842"
DEFAULT_RADIUS = 1000

if 'geo_coords' not in st.session_state: st.session_state.geo_coords = DEFAULT_COORDS
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = DEFAULT_RADIUS
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'last_scan_lat' not in st.session_state: st.session_state.last_scan_lat = 14.5995
if 'last_scan_lon' not in st.session_state: st.session_state.last_scan_lon = 120.9842

# =============================================================================
# [ CONFIGURATION BLOCK: POI DICTIONARY ]
# =============================================================================
POI_CONFIG = {
    "COMMERCIAL": [['Corporate Office', '"building"~"office|commercial",i'], ['IT/Tech Center', '"office"~"it|telecommunication",i'], ['Business Center', '"building"="commercial"'], ['Hospital', '"amenity"~"hospital|clinic",i'], ['Hotel', '"tourism"="hotel"'], ['Motel', '"tourism"="motel"']],
    "RESIDENTIAL": [['Apartments', '"building"="apartments"'], ['House', '"building"="house"'], ['Residential Area', '"landuse"="residential"'], ['Condominium', '"building"="residential"']],
    "RETAIL": [['Mall/Department Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"supermarket|grocery",i'], ['Convenience Store', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Hardware', '"shop"~"hardware|doityourself",i'], ['General Shops', '"shop"~"boutique|clothes|shoes",i'], ['Beauty', '"shop"="beauty"'], ['Bicycle', '"shop"="bicycle"'], ['Books/Stationary', '"shop"~"books|stationary",i'], ['Car', '"shop"="car"'], ['Chemist', '"shop"="chemist"'], ['Clothes', '"shop"="clothes"'], ['Copyshop', '"shop"="copyshop"'], ['Cosmetics', '"shop"="cosmetics"'], ['Department store', '"shop"="department_store"'], ['DIY/hardware', '"shop"~"hardware|doityourself",i'], ['Garden centre', '"shop"="garden_centre"'], ['General', '"shop"="general"'], ['Gift', '"shop"="gift"'], ['Hairdresser', '"shop"="hairdresser"'], ['Jewelry', '"shop"="jewelry"'], ['Kiosk', '"shop"="kiosk"'], ['Leather', '"shop"="leather"'], ['Marketplace', '"amenity"="marketplace"'], ['Musical instrument', '"shop"="musical_instrument"'], ['Optician', '"shop"="optician"'], ['Pets', '"shop"="pets"'], ['Phone', '"shop"="mobile_phone"'], ['Photo', '"shop"="photo"'], ['Shoes', '"shop"="shoes"'], ['Shopping centre', '"shop"="mall"'], ['Textiles', '"shop"="textiles"'], ['Toys', '"shop"="toys"']],
    "FOOD AND BEVERAGES": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee Shop', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"'], ['Bar/Pub/Nightclub', '"amenity"~"bar|pub|nightclub",i'], ['Bakery/Pastry', '"shop"="bakery"'], ['BBQ', '"amenity"="bbq"'], ['Biergarten', '"amenity"="biergarten"'], ['Food court', '"amenity"="food_court"'], ['Ice cream', '"amenity"="ice_cream"'], ['Pub', '"amenity"="pub"']],
    "INDUSTRIAL": [['Expressway Exits', '"highway"~"motorway_junction|toll_gantry",i'], ['Ports & Terminals', '"industrial"="port"'], ['Manufacturing Plants', '"industrial"~"factory|manufacturing|processing",i'], ['Cold Storage Facilities', '"warehouse"~"cold_store|cold_storage",i'], ['Industrial Parks/Estates', '"landuse"~"industrial|industrial_estate",i'], ['Warehouses & Depots', '"building"~"warehouse|depot",i'], ['Storage Facilities', '"building"="storage"'], ['Truck Access Routes (HGV)', '"hgv"~"designated|yes",i']],
    "GOVERNMENT": [['City Hall', '"amenity"="townhall"'], ['Police Station', '"amenity"="police"'], ['Fire Station', '"amenity"="fire_station"'], ['Airport Terminal', '"aeroway"~"terminal|aerodrome",i']],
    "SCHOOLS": [['University/College', '"amenity"~"university|college",i'], ['K-12 School', '"amenity"="school"'], ['Vocational/Other', '"amenity"="learning_centre"']]
}

ADVANCED_CONFIG = {
    "AMENITIES": [['ATM', '"amenity"="atm"'], ['Bank', '"amenity"="bank"'], ['Bench', '"amenity"="bench"'], ['Bicycle Parking', '"amenity"="bicycle_parking"'], ['Bicycle Rental', '"amenity"="bicycle_rental"'], ['Cinema', '"amenity"="cinema"'], ['Clinic', '"amenity"="clinic"'], ['Embassy', '"amenity"="embassy"'], ['Firestation', '"amenity"="fire_station"'], ['Fuel', '"amenity"="fuel"'], ['Hospital', '"amenity"="hospital"'], ['Library', '"amenity"="library"'], ['Music School', '"amenity"="music_school"'], ['Parking', '"amenity"="parking"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Police', '"amenity"="police"'], ['Letter Box', '"amenity"="letter_box"'], ['Post Office', '"amenity"="post_office"'], ['School/College', '"amenity"~"school|college",i'], ['Taxi', '"amenity"="taxi"'], ['Theatre', '"amenity"="theatre"'], ['Toilets', '"amenity"="toilets"'], ['University', '"amenity"="university"']],
    "PLACE OF WORSHIP": [['Church', '"religion"="christian"'], ['Mosque', '"religion"="muslim"'], ['Buddhist Temple', '"religion"="buddhist"'], ['Hindu Temple', '"religion"="hindu"'], ['Synagogue', '"religion"="jewish"'], ['Cemetery', '"landuse"="cemetery"'], ['Alpine Hut', '"tourism"="alpine_hut"'], ['Apartment', '"tourism"="apartment"'], ['Camp Site', '"tourism"="camp_site"'], ['Chalet', '"tourism"="chalet"'], ['Guest House', '"tourism"="guest_house"'], ['Hostel', '"tourism"="hostel"'], ['Hotel', '"tourism"="hotel"'], ['Motel', '"tourism"="motel"'], ['Casino', '"amenity"="casino"'], ['Spa', '"leisure"="spa"'], ['Sauna', '"leisure"="sauna"']],
    "SPORTS": [['American football', '"sport"="american_football"'], ['Baseball', '"sport"="baseball"'], ['Basketball', '"sport"="basketball"'], ['Cycling', '"sport"="cycling"'], ['Gymnastics', '"sport"="gymnastics"'], ['Golf', '"sport"="golf"'], ['Hockey', '"sport"="hockey"'], ['Horse racing', '"sport"="horse_racing"'], ['Ice hockey', '"sport"="ice_hockey"'], ['Soccer', '"sport"="soccer"'], ['Sports centre', '"leisure"="sports_centre"'], ['Surfing', '"sport"="surfing"'], ['Swimming', '"sport"="swimming"'], ['Tennis', '"sport"="tennis"'], ['Volleyball', '"sport"="volleyball"']],
    "MISCELLANEOUS": [['Busstop', '"highway"="bus_stop"'], ['E-bike charging', '"amenity"="charging_station"'], ['Kindergarten', '"amenity"="kindergarten"'], ['Marketplace', '"amenity"="marketplace"'], ['Office', '"office"="yes"'], ['Recycling', '"amenity"="recycling"'], ['Travel agency', '"shop"="travel_agency"'], ['Defibrillator - AED', '"emergency"="defibrillator"'], ['Fire hose/extinguisher', '"emergency"~"fire_hose|fire_extinguisher",i'], ['Fixme', '"fixme"~".",i'], ['Note-Node', '"type"="node"'], ['Note-Way', '"type"="way"'], ['Construction', '"landuse"="construction"'], ['Image', '"image"~".",i'], ['Public camera', '"man_made"="surveillance"'], ['City', '"place"="city"'], ['Town', '"place"="town"'], ['Village', '"place"="village"'], ['Hamlet', '"place"="hamlet"'], ['Suburb', '"place"="suburb"']]
}

# =============================================================================
# [ CONFIGURATION BLOCK: SIDEBAR UI & LOGIC ]
# =============================================================================
with st.sidebar:
    st.markdown('<div class="brand-title">Trade Area Scan</div>', unsafe_allow_html=True)
    
    # DYNAMIC EXPORT BUTTON: Only shows relevant data post-scan
    if st.session_state.scanned_records:
        st.download_button(
            label=f"💾 EXPORT {len(st.session_state.scanned_records)} POIs", 
            data=json.dumps(st.session_state.scanned_records, indent=4), 
            file_name="TradeArea_Data.json", 
            mime="application/json",
            use_container_width=True,
            type="primary"
        )
    else:
        st.download_button(
            label="SAVE PROJECT (EMPTY)", 
            data=json.dumps([]), 
            file_name="TradeArea_Data.json", 
            mime="application/json",
            use_container_width=True,
            disabled=True
        )
    
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    location_input = st.text_input("LOCATION SEARCH OR COORDINATES", value=st.session_state.geo_coords, key="geo_coords_input")
    radius_val = st.number_input("RADIUS (METERS)", min_value=100, max_value=50000, value=st.session_state.geo_radius, key="geo_radius_input", step=100)
    st.session_state.geo_radius = radius_val

    coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", location_input)
    
    if coord_match:
        lat_coord, lon_coord = float(coord_match.group(1)), float(coord_match.group(2))
        st.session_state.geo_coords = location_input
    else:
        if location_input and location_input != st.session_state.get('last_geocoded_query', ''):
            with st.spinner("Locating via Nominatim..."):
                try:
                    headers = {'User-Agent': 'TradeAreaScan/4.0'}
                    osm_url = f"https://nominatim.openstreetmap.org/search?q={location_input}&format=json&limit=1"
                    resp = requests.get(osm_url, headers=headers, timeout=10).json()
                    if resp:
                        new_lat, new_lon = float(resp[0]['lat']), float(resp[0]['lon'])
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
    
    OVERPASS_ENDPOINTS = [
        "https://overpass-api.de/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
        "https://overpass.private.coffee/api/interpreter"
    ]

    # =============================================================================
    # [ CONFIGURATION BLOCK: SCAN AREA ENGINE (OSMNX + OVERPASS FALLBACK) ]
    # =============================================================================
    if st.button("SCAN AREA", type="secondary", use_container_width=True, key="scan_btn"):
        if not selected_tags:
            st.error("Select ≥ 1 .")
        else:
            status_indicator = st.empty()
            
            with st.spinner("Extracting nodes..."):
                success = False
                
                # -------------------------------------------------------------
                # ATTEMPT 1: OSMnx (Primary Extraction Method)
                # -------------------------------------------------------------
                status_indicator.info("Extracting POIs using OSMnx (Primary Engine)...")
                try:
                    ox.settings.use_cache = False
                    ox.settings.log_console = False

                    osmnx_tags = {}
                    for tag_str in selected_tags:
                        match = re.search(r'"([^"]+)"(=|~)"([^"]+)"', tag_str)
                        if match:
                            k, op, v = match.group(1), match.group(2), match.group(3)
                            
                            if v == '.':
                                val = True
                            else:
                                val = v.split('|') if '|' in v else v
                                
                            if k in osmnx_tags:
                                if isinstance(osmnx_tags[k], list):
                                    if isinstance(val, list): osmnx_tags[k].extend(val)
                                    elif val is not True: osmnx_tags[k].append(val)
                                elif isinstance(osmnx_tags[k], str):
                                    if val is True: osmnx_tags[k] = True
                                    else: osmnx_tags[k] = [osmnx_tags[k]] + (val if isinstance(val, list) else [val])
                            else:
                                osmnx_tags[k] = val

                    # Extract geometries
                    gdf = ox.features_from_point((lat_coord, lon_coord), tags=osmnx_tags, dist=radius_val)
                    
                    if not gdf.empty:
                        records = []
                        for idx, row in gdf.iterrows():
                            geom = row['geometry']
                            if geom.geom_type == 'Point':
                                p_lat, p_lon = geom.y, geom.x
                            else:
                                centroid = geom.centroid
                                p_lat, p_lon = centroid.y, centroid.x
                            
                            # STRICT RADIUS CLAMPING
                            dist = calculate_haversine(lat_coord, lon_coord, p_lat, p_lon)
                            if dist <= radius_val:
                                name = row.get('name', 'Unknown')
                                if pd.isna(name): name = 'Unknown'
                                
                                p_type = 'Node'
                                for k in osmnx_tags.keys():
                                    if k in row and not pd.isna(row[k]):
                                        p_type = str(row[k])
                                        break
                                
                                records.append({
                                    "lat": float(p_lat), 
                                    "lon": float(p_lon), 
                                    "name": str(name), 
                                    "type": str(p_type), 
                                    "geomType": str(geom.geom_type),
                                    "shape": "Drop" # Default Icon Shape
                                })
                        
                        st.session_state.scanned_records = records
                        st.session_state.last_scan_lat, st.session_state.last_scan_lon = lat_coord, lon_coord
                        success = True
                        status_indicator.success(f"Success! OSMnx extracted {len(records)} bounded POIs.")
                    else:
                        st.session_state.scanned_records = []
                        st.session_state.last_scan_lat, st.session_state.last_scan_lon = lat_coord, lon_coord
                        success = True
                        status_indicator.warning("OSMnx completed: 0 POIs found strictly in this radius.")

                # -------------------------------------------------------------
                # ATTEMPT 2: Overpass Turbo (Fallback Extraction Method)
                # -------------------------------------------------------------
                except Exception as e:
                    status_indicator.warning("OSMnx timed out or failed. Falling back to Overpass Turbo API...")
                    
                    statements = "\n".join([f"  nwr[{tag}](around:{radius_val},{lat_coord},{lon_coord});" for tag in selected_tags])
                    ql = f"[out:json][timeout:90];(\n{statements}\n);\nout center;"
                    
                    for url in OVERPASS_ENDPOINTS:
                        try:
                            res = requests.post(url, data={"data": ql}, headers={"User-Agent": "TradeAreaScan/5.0"}, timeout=45)
                            if res.status_code == 200:
                                records = []
                                for el in res.json().get('elements', []):
                                    e_lat = el.get('lat') or el.get('center', {}).get('lat')
                                    e_lon = el.get('lon') or el.get('center', {}).get('lon')
                                    
                                    if e_lat and e_lon:
                                        # STRICT RADIUS CLAMPING
                                        dist = calculate_haversine(lat_coord, lon_coord, float(e_lat), float(e_lon))
                                        if dist <= radius_val:
                                            tags = el.get('tags', {})
                                            p_type = tags.get('amenity') or tags.get('shop') or tags.get('building') or 'Node'
                                            
                                            records.append({
                                                "lat": float(e_lat), 
                                                "lon": float(e_lon), 
                                                "name": str(tags.get('name', 'Unknown')), 
                                                "type": str(p_type), 
                                                "geomType": str("Point" if el.get('type') == 'node' else "Polygon"),
                                                "shape": "Drop" # Default Icon Shape
                                            })
                                st.session_state.scanned_records = records
                                st.session_state.last_scan_lat, st.session_state.last_scan_lon = lat_coord, lon_coord
                                success = True
                                status_indicator.success(f"Success! Overpass Turbo Backup extracted {len(records)} bounded POIs.")
                                break
                        except Exception:
                            continue
                            
                if success:
                    import time
                    time.sleep(1.5)
                    status_indicator.empty()
                    st.rerun() # Refresh to populate the download button top-of-sidebar
                else:
                    status_indicator.error("Critical Error: Both OSMnx and all Overpass Backup servers failed.")

    if st.button("CLEAR ALL", type="primary", key="clear_btn"):
        st.session_state.scanned_records = []
        for key in list(st.session_state.keys()):
            if key.startswith("chk_"):
                st.session_state[key] = False
        st.rerun()

# =============================================================================
# [ CONFIGURATION BLOCK: LEAFLET ENGINE (HTML/JS) ]
# =============================================================================
geojson_str = json.dumps(st.session_state.scanned_records)
is_stale = "true" if (lat_coord != st.session_state.last_scan_lat or lon_coord != st.session_state.last_scan_lon) else "false"

leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="https://unpkg.com/@geoman-io/leaflet-geoman-free@2.14.2/dist/leaflet-geoman.css" />
    
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/@geoman-io/leaflet-geoman-free@2.14.2/dist/leaflet-geoman.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js"></script>
    
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        /* --- CORE MAP CSS --- */
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #ffffff; overflow: hidden; font-family: 'Montserrat', sans-serif; }
        #map { height: 100vh; width: 100%; }
        
        /* --- ROUTING UI INDICATOR --- */
        .routing-active-indicator { display: none; position: absolute; top: 20px; left: 50%; transform: translateX(-50%); background: #AA2E20; color: #fff; font-weight: 800; padding: 8px 20px; border-radius: 4px; z-index: 2000; font-size: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); text-transform: uppercase; cursor: pointer;}
        body.routing-mode .routing-active-indicator { display: block; }
        body.routing-mode #map { cursor: crosshair !important; }

        /* --- SEARCH BAR UI (Positioned to clear toolbars) --- */
        #search-container { position: absolute; top: 15px; left: 60px; z-index: 1000; width: 300px; }
        #map-search { width: 100%; padding: 8px 12px; border: 1px solid rgba(0, 51, 102, 0.1); border-radius: 4px; font-size: 11px; font-weight: 600; color: #003366; outline: none; box-sizing: border-box; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); }
        #map-search:focus { border-bottom: 2px solid #C9AB4C; }
        #search-results { position: absolute; top: 38px; left: 0; width: 100%; background: #ffffff; border-radius: 2px; display: none; max-height: 250px; overflow-y: auto; border: 1px solid rgba(0, 51, 102, 0.1); z-index: 1001; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); }
        .search-item { padding: 8px 12px; font-size: 10px; font-weight: 600; cursor: pointer; border-bottom: 1px solid #f8fafc; color: #003366; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .search-item:hover { background: #f8fafc; color: #C9AB4C; }

        /* --- FLOATING BASEMAP TOGGLE PANEL --- */
        #minimal-basemap-panel { position: absolute; top: 110px; left: 60px; z-index: 1000; background: #ffffff; border-radius: 4px; border: 1px solid rgba(0, 51, 102, 0.1); display: none; flex-direction: column; padding: 4px; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); width: 160px; }
        #minimal-basemap-panel select { border: none; border-bottom: 1px solid #f0f0f0; padding: 6px; font-size: 10px; font-weight: 700; color: #003366; background: transparent; outline: none; cursor: pointer; width: 100%; text-transform: uppercase; font-family: inherit;}
        .minimal-label { font-size: 9px; font-weight: 700; padding: 6px; display: flex; align-items: center; gap: 4px; cursor: pointer; color: #888780; margin: 0; text-transform: uppercase; border-top: 1px solid #f8fafc;}

        /* --- DYNAMIC SIDEBAR LIST UI --- */
        /* Updated max-height to clear the native Streamlit Manage App button in the corner */
        #scan-results-panel { position: absolute; top: 10px; right: 10px; z-index: 1000; background: #ffffff; width: 280px; max-height: calc(100vh - 100px); border-radius: 2px; border: 1px solid rgba(0, 51, 102, 0.1); display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); }
        .results-header { background: #003366; color: #ffffff; padding: 10px 12px; font-size: 10px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; border-bottom: 2px solid #C9AB4C; }
        
        .manage-s-btn { background: #f8fafc; color: #003366; padding: 6px; text-align: center; font-size: 9px; font-weight: 800; border-bottom: 1px solid #e0e0e0; cursor: pointer; text-transform: uppercase; transition: background 0.2s;}
        .manage-s-btn:hover { background: #e0e0e0; }

        .results-list { overflow-y: auto; flex-grow: 1; padding-bottom: 8px; }
        .-category-block { border-bottom: 1px solid #f0f0f0; background: #fff;}
        .-category-header { background: #ffffff; padding: 8px 12px; display: flex; align-items: center; justify-content: space-between; user-select: none; border-left: 3px solid transparent;}
        .-category-header:hover { background: #f8fafc; border-left: 3px solid #C9AB4C;}
        .-header-left { display: flex; align-items: center; gap: 6px; font-size: 9px; font-weight: 700; color: #003366; text-transform: uppercase;}
        .-category-items { padding: 0; background: #f8fafc; min-height: 10px;}
        .-category-items.collapsed { display: none !important; }
        
        .results-item { padding: 6px 12px 6px 28px; font-size: 9px; font-weight: 600; color: #888780; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f0f0f0; background: #fff;}
        .results-item:hover { background: #f0f4f8; color: #003366; }
        
        /* --- MANAGE MODE TOGGLE CSS --- */
        .manage-tools { display: none; }
        .manage-mode-active .manage-tools { display: flex; }
        .manage-mode-active .layer-category-header, .manage-mode-active .results-item { cursor: move; }

        .icon-btn { cursor: pointer; padding: 2px; margin-left:4px; fill: #888780; transition: fill 0.2s;}
        .icon-btn:hover { fill: #003366; }
        .icon-btn.del:hover { fill: #AA2E20; }
        .add-layer-btn { display: block; width: 100%; text-align: center; padding: 8px; background: #f8fafc; color: #003366; font-size: 9px; font-weight: 800; cursor: pointer; border-top: 1px solid #e0e0e0; text-transform: uppercase;}
        .add-layer-btn:hover { background: #C9AB4C; color: #fff;}

        /* Map Labels */
        .poi-text-label { background: #fff; border: 1px solid #003366; padding: 2px 4px; border-radius: 2px; font-size: 9px; font-family: 'Montserrat', sans-serif; font-weight: 700; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .hide-labels .poi-text-label { display: none !important; }
        .color-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; border: 1px solid rgba(0,0,0,0.2); cursor: pointer;}
        
        /* --- CUSTOM EDIT POPUP CSS --- */
        .edit-form-container { display: flex; flex-direction: column; gap: 6px; font-family: 'Montserrat', sans-serif; min-width: 180px;}
        .edit-form-container label { font-size: 8px; font-weight: 700; color: #888780; text-transform: uppercase; margin-bottom: -4px;}
        .edit-form-container input[type="text"], .edit-form-container input[type="color"], .edit-form-container select { width: 100%; border: none; border-bottom: 1px solid #C9AB4C; padding: 4px 0; font-family: inherit; font-size: 11px; font-weight: 600; color: #003366; outline: none; background: transparent;}
        .edit-form-container input[type="range"] { width: 100%; cursor: pointer;}
        .edit-form-container button { background: #003366; color: white; border: none; padding: 6px; border-radius: 2px; cursor: pointer; font-size: 9px; font-weight: 700; text-transform: uppercase; margin-top: 4px;}
        .edit-form-container button:hover { background: #C9AB4C; }
        
        /* Custom Left Toolbar */
        .leaflet-control-custom-stack { background: #fff; border: 2px solid rgba(0,0,0,0.2); border-radius: 4px; display: flex; flex-direction: column; }
        .leaflet-control-custom-stack a { display: flex !important; align-items: center; justify-content: center; width: 34px; height: 34px; border-bottom: 1px solid #ccc; cursor: pointer;}
        .leaflet-control-custom-stack a:hover { background: #f4f4f4; }
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="routing-active-indicator" onclick="cancelRouting()">CANCEL ROUTING (CLICK POINT A, THEN B)</div>
    
    <div id="search-container">
        <input type="text" id="map-search" placeholder="Nominatim Search..." onkeyup="handleSearch(event)">
        <div id="search-results"></div>
    </div>

    <div id="minimal-basemap-panel">
        <select id="basemap-select" onchange="switchActiveBasemap(this.value)">
            <option value="osm">OpenStreetMap</option>
            <option value="satellite">Google Satellite</option>
            <option value="carto">Carto Light</option>
        </select>
        <label class="minimal-label" for="label-toggle-chk">
            <input type="checkbox" id="label-toggle-chk" checked style="margin:0; cursor: pointer;" onchange="toggleLabelsMatrix(this.checked)"> Show POI Labels
        </label>
    </div>

    <div id="scan-results-panel">
        <div class="results-header"><span>LAYERS</span><span id="results-count" style="color:#C9AB4C;">0</span></div>
        <div class="manage-layers-btn" onclick="toggleManageLayers()">⚙️ Manage Layers</div>
        <div class="results-list" id="results-list-box"></div>
        <div class="add-layer-btn" onclick="createNewLayer()">+ Add Custom Layer</div>
    </div>

    <script>
        // =============================================================================
        // [ CONFIGURATION BLOCK: LEAFLET INIT & BASEMAPS ]
        // =============================================================================
        const map = L.map('map', { zoomControl: false, attributionControl: false }).setView([__LAT__, __LON__], 14);
        L.control.zoom({ position: 'bottomright' }).addTo(map);

        const basemaps = {
            osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }),
            satellite: L.tileLayer('http://www.google.cn/maps/vt?lyrs=s@189&gl=cn&x={x}&y={y}&z={z}', { maxZoom: 20 }),
            carto: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 })
        };
        
        let activeBasemapKey = 'osm';
        basemaps[activeBasemapKey].addTo(map);

        function switchActiveBasemap(targetKey) {
            map.removeLayer(basemaps[activeBasemapKey]);
            basemaps[targetKey].addTo(map);
            activeBasemapKey = targetKey;
        }

        function toggleLabelsMatrix(isShown) {
            if (isShown) document.getElementById('map').classList.remove('hide-labels');
            else document.getElementById('map').classList.add('hide-labels');
        }

        // =============================================================================
        // [ CONFIGURATION BLOCK: TOOLBARS (Geoman & Custom) ]
        // =============================================================================
        map.pm.addControls({ position: 'topleft', drawMarker: true, drawCircleMarker: false, drawPolyline: true, drawRectangle: true, drawPolygon: true, drawCircle: true, editMode: true, dragMode: true, cutPolygon: false, removalMode: true });
        
        const customToolbar = L.control({position: 'topleft'});
        customToolbar.onAdd = function () {
            const div = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom-stack');
            div.innerHTML = `
                <a title="Toggle Layers/Basemaps" onclick="toggleLayerMenu(event)"><svg viewBox="0 0 24 24" width="18" height="18" fill="#003366"><path d="M11.99 18.54l-7.37-5.73L3 14.07l9 7 9-7-1.63-1.27-7.38 5.74zM12 16l7.36-5.73L21 9l-9-7-9 7 1.63 1.27L12 16z"/></svg></a>
                <a title="Draw Route (A to B)" onclick="startRouting(event)"><svg viewBox="0 0 24 24" width="18" height="18" fill="#003366"><path d="M19.5 9.5c-1.03 0-1.9.62-2.29 1.5h-2.92c-.39-.88-1.26-1.5-2.29-1.5s-1.9.62-2.29 1.5H6.79c-.39-.88-1.26-1.5-2.29-1.5C3.12 9.5 2 10.62 2 12s1.12 2.5 2.5 2.5c1.03 0 1.9-.62 2.29-1.5h2.92c.39.88 1.26 1.5 2.29 1.5s1.9-.62 2.29-1.5h2.92c.39.88 1.26 1.5 2.29 1.5 1.38 0 2.5-1.12 2.5-2.5s-1.12-2.5-2.5-2.5zM4.5 13c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm7.5 0c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm7.5 0c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1z"/></svg></a>
            `;
            return div;
        };
        customToolbar.addTo(map);

        function toggleLayerMenu(e) { 
            e.preventDefault(); 
            const panel = document.getElementById('minimal-basemap-panel'); 
            panel.style.display = panel.style.display === 'flex' ? 'none' : 'flex'; 
        }

        // =============================================================================
        // [ CONFIGURATION BLOCK: NOMINATIM SEARCH ]
        // =============================================================================
        let searchTimeout = null;
        function handleSearch(e) {
            clearTimeout(searchTimeout); const q = e.target.value; const resDiv = document.getElementById('search-results');
            if (q.length < 3) { resDiv.style.display = 'none'; return; }
            searchTimeout = setTimeout(() => {
                fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}&limit=5`)
                    .then(r => r.json()).then(data => {
                        if (data.length > 0) {
                            resDiv.innerHTML = '';
                            data.forEach(item => {
                                const div = document.createElement('div'); div.className = 'search-item'; div.innerText = item.display_name;
                                div.onclick = () => { map.flyTo([item.lat, item.lon], 16); resDiv.style.display = 'none'; document.getElementById('map-search').value = ''; };
                                resDiv.appendChild(div);
                            });
                            resDiv.style.display = 'block';
                        }
                    });
            }, 500);
        }

        // =============================================================================
        // [ CONFIGURATION BLOCK: STATE ENGINE & CONTEXT MENUS ]
        // =============================================================================
        let pts = __GEOJSON__;
        let globalIdCounter = 0; pts.forEach(p => p._uid = globalIdCounter++);
        
        const catPalette = ["#003366", "#C9AB4C", "#1A5A8A", "#A8862E", "#3D7DA8", "#7A5C10", "#6A94B0", "#D4B85A", "#001F3F", "#E8D494"];
        let layerGroupsRef = {};
        let categoryColors = {}; let colorIndex = 0;
        let globalSortableInstances = [];

        map.on('contextmenu', function(e) {
            const lat = e.latlng.lat, lng = e.latlng.lng;
            const content = `
                <div style="font-family: Montserrat; font-size: 9px; color: #003366;">
                    <div style="font-weight: 800; border-bottom: 1px solid #C9AB4C; margin-bottom: 4px;">MAP UTILITIES</div>
                    <div style="cursor:pointer; padding:2px 0; font-weight:700;" onclick="navigator.clipboard.writeText('${lat.toFixed(5)},${lng.toFixed(5)}'); map.closePopup();">Copy Coordinates</div>
                    <div style="cursor:pointer; padding:2px 0; font-weight:700;" onclick="window.open('https://www.google.com/maps?q=$${lat},${lng}', '_blank'); map.closePopup();">Open Google Maps</div>
                    <div style="cursor:pointer; padding:2px 0; font-weight:700;" onclick="window.open('https://www.google.com/maps?layer=c&cbll=$${lat},${lng}', '_blank'); map.closePopup();">Open Street View</div>
                </div>`;
            L.popup().setLatLng(e.latlng).setContent(content).openOn(map);
        });

        // =============================================================================
        // [ CONFIGURATION BLOCK: FREE-FORM OSRM ROUTING ]
        // =============================================================================
        let isRoutingMode = false; let routeWaypoints = []; 
        let tempMarker1 = null; let tempMarker2 = null;

        window.startRouting = function(e) { e.preventDefault(); isRoutingMode = true; routeWaypoints = []; document.body.classList.add('routing-mode'); }
        window.cancelRouting = function() { 
            isRoutingMode = false; routeWaypoints = []; document.body.classList.remove('routing-mode'); 
            if(tempMarker1) map.removeLayer(tempMarker1); 
            if(tempMarker2) map.removeLayer(tempMarker2);
        }
        
        map.on('click', function(e) {
            if(!isRoutingMode) return;
            routeWaypoints.push(e.latlng);
            
            if(routeWaypoints.length === 1) {
                tempMarker1 = L.circleMarker(e.latlng, {radius: 6, color: '#AA2E20', fillOpacity: 1}).addTo(map);
            } else if(routeWaypoints.length === 2) {
                tempMarker2 = L.circleMarker(e.latlng, {radius: 6, color: '#AA2E20', fillOpacity: 1}).addTo(map);
                
                const url = `https://router.project-osrm.org/route/v1/driving/${routeWaypoints[0].lng},${routeWaypoints[0].lat};${routeWaypoints[1].lng},${routeWaypoints[1].lat}?geometries=geojson`;
                fetch(url).then(r=>r.json()).then(data => {
                    if(data.routes && data.routes.length > 0) {
                        const coords = data.routes[0].geometry.coordinates.map(c => [c[1], c[0]]);
                        const routePoly = L.polyline(coords, {color: '#AA2E20', weight: 4, dashArray: '5, 10'}).addTo(map);
                        
                        const newUid = globalIdCounter++;
                        pts.push({ _uid: newUid, name: 'Driving Route', type: 'Routes', geomType: 'Polyline', _layer: routePoly, color: '#AA2E20', weight: 4 });
                        routePoly.on('contextmenu', (evt) => openStyleEditor(evt, newUid));
                        renderSidebar();
                    }
                });
                cancelRouting();
            }
        });

        // =============================================================================
        // [ CONFIGURATION BLOCK: LEAFLET GEOMAN DRAWING BINDS ]
        // =============================================================================
        map.on('pm:create', (e) => {
            const layer = e.layer;
            const newUid = globalIdCounter++;
            let gType = e.shape; 
            
            if (gType === 'Circle') {
                layer.bindTooltip(`Radius: ${Math.round(layer.getRadius())}m`, {permanent: true, direction: 'center', className: 'poi-text-label'});
            }

            pts.push({ _uid: newUid, name: 'New ' + gType, type: 'Custom Drawn', geomType: gType, _layer: layer, color: '#C9AB4C', opacity: 0.5, weight: 3 });
            layer.on('contextmenu', (evt) => openStyleEditor(evt, newUid));
            layer.on('pm:edit', (evt) => { if(gType === 'Circle') layer.setTooltipContent(`Radius: ${Math.round(layer.getRadius())}m`); });
            
            renderSidebar();
        });

        // =============================================================================
        // [ CONFIGURATION BLOCK: DYNAMIC ICON MORPHOLOGY (SHAPES) ]
        // =============================================================================
        const createPinIcon = (color, shapeStr) => {
            let svgMarkup = '';
            if (shapeStr === 'Circle') {
                svgMarkup = `<svg viewBox="0 0 24 24" width="16" height="16"><circle cx="12" cy="12" r="10" fill="${color}" stroke="#ffffff" stroke-width="2"/></svg>`;
            } else if (shapeStr === 'Ball') {
                svgMarkup = `<svg viewBox="0 0 24 24" width="20" height="20"><circle cx="12" cy="12" r="10" fill="${color}" stroke="#333" stroke-width="1"/><circle cx="10" cy="9" r="3" fill="#fff" opacity="0.6"/></svg>`;
            } else {
                // Default 'Drop' style
                svgMarkup = `<svg viewBox="0 0 24 24" width="24" height="24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="${color}" stroke="#ffffff" stroke-width="1.5"/></svg>`;
            }
            return L.divIcon({ html: svgMarkup, className: '', iconSize: [24, 24], iconAnchor: [12, 24] });
        };

        // =============================================================================
        // [ CONFIGURATION BLOCK: MASTER RENDER ENGINE & SORTABLE JS ]
        // =============================================================================
        function renderSidebar() {
            const categoryMap = {};
            pts.forEach(p => {
                const layerKey = p.type || 'Unclassified';
                if (!categoryMap[layerKey]) { categoryMap[layerKey] = []; if(!categoryColors[layerKey]) categoryColors[layerKey] = catPalette[colorIndex++ % catPalette.length]; }
                categoryMap[layerKey].push(p);
            });

            Object.values(layerGroupsRef).forEach(layer => map.removeLayer(layer)); layerGroupsRef = {};
            
            Object.keys(categoryMap).forEach(key => {
                layerGroupsRef[key] = L.layerGroup().addTo(map);
                const pColor = categoryColors[key];
                
                categoryMap[key].forEach(p => {
                    if(!p._layer) {
                        p._layer = L.marker([p.lat, p.lon], { icon: createPinIcon(p.color || pColor, p.shape) });
                        if(p.name && p.name !== 'Unknown') p._layer.bindTooltip(p.name, { permanent: true, direction: 'top', offset: [0, -18], className: 'poi-text-label' });
                        p._layer.on('contextmenu', (evt) => openStyleEditor(evt, p._uid));
                    }
                    if(!map.hasLayer(p._layer)) p._layer.addTo(layerGroupsRef[key]);
                });
            });

            const listBox = document.getElementById('results-list-box');
            document.getElementById('results-count').innerText = pts.length;
            let htmlPayload = '';

            const pencilSvg = `<svg height="14" viewBox="0 -960 960 960" width="14"><path d="M200-200h57l391-391-57-57-391 391v57Zm-80 80v-170l528-527q12-11 26.5-17t30.5-6q16 0 31 6t26 18l55 56q12 11 17.5 26t5.5 30q0 16-5.5 30.5T817-647L290-120H120Z"/></svg>`;
            const trashSvg = `<svg height="14" viewBox="0 -960 960 960" width="14"><path d="M280-120q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Z"/></svg>`;

            Object.keys(categoryMap).forEach(catName => {
                htmlPayload += `
                    <div class="layer-category-block" data-id="${catName}">
                        <div class="layer-category-header">
                            <div class="layer-header-left">
                                <input type="checkbox" checked onclick="toggleCategoryVisibility('${catName}', this.checked)">
                                <span class="color-dot" style="background-color: ${categoryColors[catName]};"></span>
                                <span onclick="toggleAccordionCollapse('${catName}')">${catName} <span style="color:#C9AB4C">(${categoryMap[catName].length})</span></span>
                            </div>
                            <div class="manage-tools">
                                <div class="icon-btn" title="Batch Edit Layer" onclick="batchEditLayer('${catName}')">${pencilSvg}</div>
                            </div>
                        </div>
                        <div class="layer-category-items" id="items-${catName.replace(/\\s/g, '')}">
                `;
                categoryMap[catName].forEach(p => {
                    htmlPayload += `
                    <div class="results-item" data-uid="${p._uid}">
                        <div style="flex-grow:1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" onclick="map.flyTo(${p.lat ? `[${p.lat}, ${p.lon}]` : `pts.find(x=>x._uid==${p._uid})._layer.getBounds().getCenter()`}, 17);">${p.name || 'Asset'}</div>
                        <div class="manage-tools">
                            <div class="icon-btn" onclick="openStyleEditor(null, ${p._uid})">${pencilSvg}</div>
                            <div class="icon-btn del" onclick="removePoiInstance(${p._uid})">${trashSvg}</div>
                        </div>
                    </div>`;
                });
                htmlPayload += '</div></div>';
            });
            listBox.innerHTML = htmlPayload;

            globalSortableInstances.forEach(inst => inst.destroy()); globalSortableInstances = [];
            globalSortableInstances.push(new Sortable(listBox, { animation: 150, handle: '.layer-category-header', filter: ':not(.manage-mode-active *)' }));
            
            document.querySelectorAll('.layer-category-items').forEach(el => {
                globalSortableInstances.push(new Sortable(el, {
                    group: 'shared', animation: 150, filter: ':not(.manage-mode-active *)',
                    onEnd: function (evt) {
                        const itemUid = parseInt(evt.item.getAttribute('data-uid'));
                        const newCat = evt.to.parentElement.getAttribute('data-id');
                        const p = pts.find(x => x._uid === itemUid);
                        if(p && newCat) p.type = newCat;
                        setTimeout(renderSidebar, 50);
                    }
                }));
            });
        }

        // =============================================================================
        // [ CONFIGURATION BLOCK: STYLE EDITORS & LAYER MANAGEMENT ]
        // =============================================================================
        window.toggleManageLayers = function() {
            document.getElementById('scan-results-panel').classList.toggle('manage-mode-active');
        }

        window.openStyleEditor = function(e, uid) {
            const p = pts.find(x => x._uid === uid); if(!p) return;
            const isMarker = (!p.geomType || p.geomType === 'Point' || p.geomType === 'Marker');
            
            const formHtml = `
                <div class="edit-form-container">
                    <label>Asset Name</label>
                    <input type="text" id="edit-name-${uid}" value="${p.name || ''}">
                    <label>Layer Assignment</label>
                    <input type="text" id="edit-type-${uid}" value="${p.type || ''}">
                    <label>Color (Hex)</label>
                    <input type="color" id="edit-color-${uid}" value="${p.color || categoryColors[p.type] || '#003366'}">
                    ${isMarker ? `
                    <label>Icon Shape</label>
                    <select id="edit-shape-${uid}">
                        <option value="Drop" ${(!p.shape || p.shape === 'Drop') ? 'selected' : ''}>Drop Pin</option>
                        <option value="Circle" ${p.shape === 'Circle' ? 'selected' : ''}>Circle Dot</option>
                        <option value="Ball" ${p.shape === 'Ball' ? 'selected' : ''}>3D Ball</option>
                    </select>` : ''}
                    ${!isMarker ? `<label>Line Weight (Thickness)</label><input type="range" id="edit-wt-${uid}" min="1" max="10" step="1" value="${p.weight || 3}">` : ''}
                    ${(!isMarker && p.geomType !== 'Polyline') ? `<label>Fill Opacity</label><input type="range" id="edit-op-${uid}" min="0" max="1" step="0.1" value="${p.opacity || 0.5}">` : ''}
                    <button onclick="saveStyleEditor(${uid})">Apply Settings</button>
                </div>
            `;
            const loc = e ? e.latlng : (p.lat ? [p.lat, p.lon] : p._layer.getBounds().getCenter());
            L.popup().setLatLng(loc).setContent(formHtml).openOn(map);
        }

        window.saveStyleEditor = function(uid) {
            const p = pts.find(x => x._uid === uid); if(!p) return;
            p.name = document.getElementById(`edit-name-${uid}`).value;
            p.type = document.getElementById(`edit-type-${uid}`).value;
            p.color = document.getElementById(`edit-color-${uid}`).value;
            
            if(!p.geomType || p.geomType === 'Point' || p.geomType === 'Marker') {
                p.shape = document.getElementById(`edit-shape-${uid}`) ? document.getElementById(`edit-shape-${uid}`).value : 'Drop';
                p._layer.setIcon(createPinIcon(p.color, p.shape));
            } else {
                p.weight = document.getElementById(`edit-wt-${uid}`) ? document.getElementById(`edit-wt-${uid}`).value : 3;
                p.opacity = document.getElementById(`edit-op-${uid}`) ? document.getElementById(`edit-op-${uid}`).value : 0.5;
                p._layer.setStyle({color: p.color, fillColor: p.color, fillOpacity: p.opacity, weight: p.weight});
            }
            map.closePopup(); renderSidebar();
        }

        window.batchEditLayer = function(catKey) {
            const newColor = prompt(`Enter HEX color to override all styles in [${catKey}] layer:`, categoryColors[catKey]);
            if(newColor && /^#[0-9A-F]{6}$/i.test(newColor)) {
                categoryColors[catKey] = newColor;
                pts.filter(p => p.type === catKey).forEach(p => { 
                    p.color = newColor; 
                    if(p._layer && (!p.geomType || p.geomType === 'Point')) p._layer.setIcon(createPinIcon(newColor, p.shape)); 
                    if(p._layer && p.geomType && p.geomType !== 'Point') p._layer.setStyle({color: newColor, fillColor: newColor});
                });
                renderSidebar();
            }
        }

        window.removePoiInstance = function(uid) {
            const idx = pts.findIndex(item => item._uid === uid);
            if (idx > -1) { const p = pts[idx]; if(p._layer) map.removeLayer(p._layer); pts.splice(idx, 1); renderSidebar(); }
        }
        window.toggleCategoryVisibility = function(catKey, isVis) { if (isVis) map.addLayer(layerGroupsRef[catKey]); else map.removeLayer(layerGroupsRef[catKey]); }
        window.toggleAccordionCollapse = function(catKey) { document.getElementById('items-' + catKey.replace(/\\s/g, '')).classList.toggle('collapsed'); }
        window.createNewLayer = function() {
            const name = prompt("Enter new Custom Layer name:");
            if(name) { categoryColors[name] = catPalette[colorIndex++ % catPalette.length]; pts.push({_uid: globalIdCounter++, name: 'Dummy Node (Hidden)', type: name, lat:0, lon:0, shape: 'Drop'}); renderSidebar(); }
        }

        // =============================================================================
        // [ CONFIGURATION BLOCK: INITIALIZATION ]
        // =============================================================================
        L.circle([__LAT__, __LON__], { radius: __RADIUS__, color: "#003366", weight: 1.5, fillColor: "#003366", fillOpacity: 0.08 }).addTo(map);
        L.marker([__LAT__, __LON__], { icon: L.divIcon({ html: '<div style="background:#003366; color:#C9AB4C; width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:20px; border:2px solid #fff;">★</div>', className:'', iconSize:[36,36] }), zIndexOffset: 10000 }).addTo(map);

        renderSidebar(); 
        if (pts.length > 0 && !__IS_STALE__) {
            const group = new L.featureGroup(pts.filter(p=>p.lat).map(p => L.marker([p.lat, p.lon])));
            map.fitBounds(group.getBounds().pad(0.1));
        }
    </script>
</body>
</html>
"""

leaflet_html = (leaflet_template
                .replace("__LAT__", str(lat_coord))
                .replace("__LON__", str(lon_coord))
                .replace("__RADIUS__", str(radius_val))
                .replace("__IS_STALE__", is_stale)
                .replace("__GEOJSON__", geojson_str))

st.components.v1.html(leaflet_html, height=850, scrolling=False)
