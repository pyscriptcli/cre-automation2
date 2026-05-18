import streamlit as st
import requests
import re
import math
import json

# -----------------------------------------------------------------------------
# 0. GLOBAL DISPLAY CONFIGURATION
# -----------------------------------------------------------------------------
MAP_PANEL_HEIGHT = 900  # Adjust this pixel value to resize the spatial canvas

# -----------------------------------------------------------------------------
# 1. HIGH-DENSITY LIGHT MODE & HYPERLINK OVERRIDES
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
        
        .block-container {
            padding: 0rem !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: var(--white-clean) !important;
            color: var(--navy-brand) !important;
            border-right: 1px solid var(--border-gray) !important;
            width: 320px !important;
        }
        
        [data-testid="stSidebarUserContent"] {
            padding-top: 16px !important;
            padding-left: 12px !important;
            padding-right: 12px !important;
        }
        
        .sidebar-title {
            color: var(--navy-brand) !important;
            font-size: 24px !important;
            font-weight: 900 !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
            text-align: left !important;
            margin-bottom: 2px !important;
            font-family: 'Arial', sans-serif !important;
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
            margin-top: 10px !important;
            box-shadow: none !important;
            min-height: 0 !important;
            height: auto !important;
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
        
        div[data-baseweb="input"], div[data-baseweb="select"], .stSelectbox, .stTextInput, .stNumberInput {
            border-radius: 4px !important;
            min-height: 32px !important;
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
        
        .stDeployButton, footer, #stDecoration { display:none !important; }
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

def execute_global_purge():
    st.session_state.geo_coords = DEFAULT_COORDS
    st.session_state.geo_radius = DEFAULT_RADIUS
    st.session_state.scanned_records = []
    st.session_state.last_scan_lat = 14.6465
    st.session_state.last_scan_lon = 121.0371
    for key in list(st.session_state.keys()):
        if key.startswith("chk_"): st.session_state[key] = False

# Fully mapped taxonomy injection
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
    kml = 'xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scanned POIs</name>'
    for f in features:
        name = f.get('name', 'Asset').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        class_type = f.get('type', 'Node').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        kml += f"<Placemark><name>{name}</name><description>{class_type}</description><Point><coordinates>{f['lon']},{f['lat']},0</coordinates></Point></Placemark>"
    return kml + '</Document></kml>'

# -----------------------------------------------------------------------------
# 4. SIDEBAR WORKSPACE
# -----------------------------------------------------------------------------
with st.sidebar:
    # Header & Micro-Hyperlink Purge Button
    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.markdown('<div class="sidebar-title">TRADE AREA</div>', unsafe_allow_html=True)
    with head_col2:
        if st.button("Clear All", key="master_purge_btn", type="tertiary"):
            execute_global_purge()
            st.rerun()

    coords_val = st.text_input("Target Coordinates", key="geo_coords")
    radius_val = st.number_input("Radius (Meters)", min_value=100, max_value=50000, key="geo_radius", step=100)

    coord_match = re.match(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", coords_val)
    lat_coord, lon_coord = (float(coord_match.group(1)), float(coord_match.group(2))) if coord_match else (14.6465, 121.0371)

    search_query = st.text_input("Filter Catalog", placeholder="Search tags...").lower()
    
    selected_tags = []
    
    # Standard POI Generation in 2-Column Grid
    for cat_name, node_items in POI_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                cols = st.columns(2)
                for i, (label, tag) in enumerate(matched):
                    with cols[i % 2]:
                        if st.checkbox(label, key=f"chk_{cat_name}_{label}"): 
                            selected_tags.append(tag)

    # Advanced POI Generation in 2-Column Grid
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
    if st.button("🚀 SCAN AREA PROFILE", use_container_width=True):
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

    # Simplified Data Exports Tray
    st.markdown("<p style='color:#001a3d; font-size:10px; font-weight:800; margin-top:15px; margin-bottom:0;'>DATA EXPORTS</p>", unsafe_allow_html=True)
    exp_fmt = st.selectbox("Format", ["Select Format...", "Export Radius (KML)", "Export POIs (KML)"], label_visibility="collapsed")
    
    if exp_fmt == "Export Radius (KML)":
        st.download_button("Download File", compile_radius_kml(lat_coord, lon_coord, radius_val), f"Radius_{radius_val}m.kml", "application/vnd.google-earth.kml+xml")
    elif exp_fmt == "Export POIs (KML)":
        st.download_button("Download File", compile_features_kml(st.session_state.scanned_records), "POIs.kml", "application/vnd.google-earth.kml+xml", disabled=not st.session_state.scanned_records)

# -----------------------------------------------------------------------------
# 5. ZERO-LATENCY SPATIAL CANVAS
# -----------------------------------------------------------------------------
geojson_str = json.dumps(st.session_state.scanned_records)
render_lat = st.session_state.last_scan_lat
render_lon = st.session_state.last_scan_lon

# Clean literal template to eliminate Python f-string bracket compilation limits
leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>body, html, #map { margin: 0; padding: 0; height: 100vh; width: 100vw; background: #f8fafc; }</style>
</head>
<body>
    <div id="map"></div>
    <script>
        const map = L.map('map', { zoomControl: true, attributionControl: false }).setView([__LAT__, __LON__], 14);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);
        
        L.circleMarker([__LAT__, __LON__], {
            radius: 7, fillColor: "#e11d48", color: "#ffffff", weight: 2, opacity: 1, fillOpacity: 1
        }).addTo(map).bindPopup("<b>TARGET COORDINATES</b>");
        
        L.circle([__LAT__, __LON__], {
            radius: __RADIUS__, color: "#001a3d", weight: 2, fillColor: "#001a3d", fillOpacity: 0.1
        }).addTo(map);
        
        const pts = __GEOJSON__;
        pts.forEach(p => {
            L.circleMarker([p.lat, p.lon], {
                radius: 5, fillColor: "#d4af37", color: "#001a3d", weight: 1, opacity: 1, fillOpacity: 0.9
            }).addTo(map).bindPopup("<b>" + p.name + "</b><br>" + p.type);
        });
        
        if(pts.length > 0) {
            const bounds = L.featureGroup([L.marker([__LAT__, __LON__]), ...pts.map(p => L.marker([p.lat, p.lon]))]).getBounds();
            map.fitBounds(bounds.pad(0.1));
        }
        
        setTimeout(() => map.invalidateSize(), 200);
    </script>
</body>
</html>
"""

# Structural programmatic token injection
leaflet_html = (leaflet_template
                .replace("__LAT__", str(render_lat))
                .replace("__LON__", str(render_lon))
                .replace("__RADIUS__", str(radius_val))
                .replace("__GEOJSON__", geojson_str))

st.components.v1.html(leaflet_html, height=MAP_PANEL_HEIGHT, scrolling=False)
