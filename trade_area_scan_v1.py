import streamlit as st
import requests
import pandas as pd
import numpy as np
import re
import math

# -----------------------------------------------------------------------------
# 1. PAGE INITIALIZATION & THEME INJECTION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Trade Area Scanner",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom geometric CSS styling overrides to replicate the high-performance dark/light look
st.markdown("""
    <style>
        /* Block containment modifications */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        /* Custom card elements mimicking legacy input panels */
        div[data-testid="stVerticalBlock"] > div {
            border-radius: 8px;
        }
        /* Custom Scrollbar optimization */
        ::-webkit-scrollbar {
            display: none;
        }
        /* Eliminate redundant widget header spacings */
        .stDeployButton { display:none; }
        footer { visibility: hidden; }
        #stDecoration { display:none; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. STATIC POI DICTIONARY CONFIGURATIONS
# -----------------------------------------------------------------------------
POI_CONFIG = {
    "COMMERCIAL": [['Corporate Office', '"building"~"office|commercial",i'], ['IT/Tech Center', '"office"~"it|telecommunication",i'], ['Business Center', '"building"="commercial"'], ['Hospital', '"amenity"~"hospital|clinic",i'], ['Hotel', '"tourism"="hotel"'], ['Motel', '"tourism"="motel"']],
    "RETAIL": [['Mall/Department Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"supermarket|grocery",i'], ['Convenience Store', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Hardware', '"shop"~"hardware|doityourself",i'], ['General Shops', '"shop"~"boutique|clothes|shoes",i']],
    "FOOD AND BEVERAGES": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee Shop', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"'], ['Bar/Pub/Nightclub', '"amenity"~"bar|pub|nightclub",i'], ['Bakery/Pastry', '"shop"="blackery"']],
    "INDUSTRIAL & LOGISTICS": [
        ['Expressway Exits', '"highway"~"motorway_junction|toll_gantry",i'], 
        ['Ports & Terminals', '"industrial"="port"'], 
        ['Manufacturing Plants', '"industrial"~"factory|manufacturing|processing",i'],
        ['Cold Storage Facilities', '"warehouse"~"cold_store|cold_storage",i'],
        ['Industrial Parks/Estates', '"landuse"~"industrial|industrial_estate",i'],
        ['Warehouses & Depots', '"building"~"warehouse|depot",i'],
        ['Storage Facilities', '"building"="storage"'],
        ['Truck Access Routes (HGV)', '"hgv"~"designated|yes",i']
    ],
    "GOVERNMENT & INFRASTRUCTURE": [['City Hall', '"amenity"="townhall"'], ['Police Station', '"amenity"="police"'], ['Fire Station', '"amenity"="fire_station"'], ['Airport Terminal', '"aeroway"~"terminal|aerodrome",i']],
    "SCHOOLS": [['University/College', '"amenity"~"university|college",i'], ['K-12 School', '"amenity"="school"'], ['Vocational/Other', '"amenity"="learning_centre"']]
}

ADVANCED_CONFIG = {
    "AMENITIES": [['ATM', '"amenity"="atm"'], ['Bank', '"amenity"="bank"'], ['Bench', '"amenity"="bench"'], ['Bicycle Parking', '"amenity"="bicycle_parking"'], ['Bicycle Rental', '"amenity"="bicycle_rental"'], ['Cinema', '"amenity"="cinema"'], ['Clinic', '"amenity"="clinic"'], ['Embassy', '"amenity"="embassy"'], ['Firestation', '"amenity"="fire_station"'], ['Fuel', '"amenity"="fuel"'], ['Hospital', '"amenity"="hospital"'], ['Library', '"amenity"="library"'], ['Music School', '"amenity"="music_school"'], ['Parking', '"amenity"="parking"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Police', '"amenity"="police"'], ['Letter Box', '"amenity"="letter_box"'], ['Post Office', '"amenity"="post_office"'], ['School/College', '"amenity"~"school|college",i'], ['Taxi', '"amenity"="taxi"'], ['Theatre', '"amenity"="theatre"'], ['Toilets', '"amenity"="toilets"'], ['University', '"amenity"="university"']],
    "PLACE OF WORSHIP": [['Church', '"religion"="christian"'], ['Mosque', '"religion"="muslim"'], ['Buddhist Temple', '"religion"="buddhist"'], ['Hindu Temple', '"religion"="hindu"'], ['Synagogue', '"religion"="jewish"'], ['Cemetery', '"landuse"="cemetery"']],
    "FOOD & BEVERAGE": [['Bar', '"amenity"="bar"'], ['BBQ', '"amenity"="bbq"'], ['Biergarten', '"amenity"="biergarten"'], ['Cafe', '"amenity"="cafe"'], ['Fast food', '"amenity"="fast_food"'], ['Food court', '"amenity"="food_court"'], ['Ice cream', '"amenity"="ice_cream"'], ['Pub', '"amenity"="pub"'], ['Restaurant', '"amenity"="restaurant"']],
    "RETAIL_ADV": [['Beauty', '"shop"="beauty"'], ['Bicycle', '"shop"="bicycle"'], ['Books/Stationary', '"shop"~"books|stationary",i'], ['Car', '"shop"="car"'], ['Chemist', '"shop"="chemist"'], ['Clothes', '"shop"="clothes"'], ['Copyshop', '"shop"="copyshop"'], ['Cosmetics', '"shop"="cosmetics"'], ['Department store', '"shop"="department_store"'], ['DIY/hardware', '"shop"~"hardware|doityourself",i'], ['Garden centre', '"shop"="garden_centre"']],
    "SPORTS": [['American football', '"sport"="american_football"'], ['Baseball', '"sport"="baseball"'], ['Basketball', '"sport"="basketball"'], ['Cycling', '"sport"="cycling"'], ['Gymnastics', '"sport"="gymnastics"'], ['Golf', '"sport"="golf"'], ['Soccer', '"sport"="soccer"'], ['Sports centre', '"leisure"="sports_centre"']],
    "MISCELLANEOUS": [['Busstop', '"highway"="bus_stop"'], ['E-bike charging', '"amenity"="charging_station"'], ['Kindergarten', '"amenity"="kindergarten"'], ['Office', '"office"="yes"'], ['Recycling', '"amenity"="recycling"'], ['City', '"place"="city"'], ['Town', '"place"="town"'], ['Village', '"place"="village"']]
}

# -----------------------------------------------------------------------------
# 3. STATE MANAGEMENT ENGINE
# -----------------------------------------------------------------------------
if 'scan_data' not in st.session_state:
    st.session_state.scan_data = None
if 'active_queries' not in st.session_state:
    st.session_state.active_queries = {}

# Helper function to wipe selections
def reset_all_states():
    st.session_state.scan_data = None
    st.session_state.active_queries = {}
    st.rerun()

# -----------------------------------------------------------------------------
# 4. BACKEND BUSINESS LOGIC (KML & OVERPASS API ENGINE)
# -----------------------------------------------------------------------------
def generate_kml_radius(lat, lon, radius_meters):
    """Generates KML coordinate string for localized geofences."""
    kml_header = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Radius Scan</name><Placemark><Polygon><outerBoundaryIs><LinearRing><coordinates>'
    kml_footer = '</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></Document></kml>'
    
    coordinates_points = []
    for i in range(37):
        angle = (i * 10) * math.pi / 180
        delta_lat = (radius_meters / 6371000) * math.cos(angle)
        delta_lon = (radius_meters / (6371000 * math.cos(lat * math.pi / 180))) * math.sin(angle)
        pt_lat = lat + (delta_lat * 180 / math.pi)
        pt_lon = lon + (delta_lon * 180 / math.pi)
        coordinates_points.append(f"{pt_lon},{pt_lat},0")
        
    return kml_header + " ".join(coordinates_points) + kml_footer

def execute_overpass_scan(lat, lon, radius, queries):
    """Hits Overpass API interpreter, structures raw JSON to Pandas Dataframe."""
    if not queries:
        return None
        
    url = "https://overpass-api.de/api/interpreter"
    around_clause = f"(around:{radius},{lat},{lon})"
    
    compiled_statements = []
    for q_str in queries:
        compiled_statements.append(f"nwr[{q_str}]{around_clause};")
        
    query_body = f"[out:json][timeout:120];(\n" + "\n".join(compiled_statements) + "\n);\nout center;"
    
    try:
        response = requests.post(url, data={"data": query_body}, timeout=130)
        if response.status_code == 200:
            elements = response.json().get('elements', [])
            records = []
            for el in elements:
                # Handle points vs shapes with centers
                lat_val = el.get('lat') or el.get('center', {}).get('lat')
                lon_val = el.get('lon') or el.get('center', {}).get('lon')
                if lat_val and lon_val:
                    tags = el.get('tags', {})
                    records.append({
                        "id": el.get('id'),
                        "latitude": lat_val,
                        "longitude": lon_val,
                        "name": tags.get('name', 'Unnamed Location'),
                        "amenity": tags.get('amenity') or tags.get('shop') or tags.get('building') or tags.get('industrial', 'Other')
                    })
            return pd.DataFrame(records) if records else pd.DataFrame()
        else:
            st.error(f"API Error Code: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Network Connection Failed: {str(e)}")
        return None

# -----------------------------------------------------------------------------
# 5. CONTROL INTERFACE (SIDEBAR WORKSPACE)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("Trade Area UI Controller")
    
    col_reset, col_clear = st.columns(2)
    with col_reset:
        if st.button("RESET GEOGRAPHY", use_container_width=True):
            reset_all_states()
            
    # Geolocation Inputs
    coords_input = st.text_input("Coordinates (LAT, LON)", value="14.6465, 121.0371")
    radius_input = st.number_input("Radius (Meters)", min_value=100, max_value=50000, value=1000, step=100)
    
    # Coordinates Parser Regex Match
    coord_match = re.match(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", coords_input)
    if coord_match:
        center_lat = float(coord_match.group(1))
        center_lon = float(coord_match.group(2))
    else:
        st.error("Invalid coordinates signature format.")
        center_lat, center_lon = 14.6465, 121.0371

    # Real-time Filter Query Search Engine
    search_term = st.text_input("🔍 Search Core/Advanced POIs", "").lower()

    # Dynamic Filter Mapping Engine
    chosen_queries = []
    
    st.subheader("Core POI Categories")
    for category, elements in POI_CONFIG.items():
        filtered_elements = [el for el in elements if search_term in el[0].lower() or search_term in el[1].lower()]
        if filtered_elements:
            with st.expander(category, expanded=(len(search_term) > 0)):
                for name, tag_query in filtered_elements:
                    # Maintain structural persistence via query string registry keys
                    cb_key = f"cb_{category}_{name}"
                    if st.checkbox(name, key=cb_key):
                        chosen_queries.append(tag_query)

    st.subheader("Advanced POI Library")
    for category, elements in ADVANCED_CONFIG.items():
        filtered_elements = [el for el in elements if search_term in el[0].lower() or search_term in el[1].lower()]
        if filtered_elements:
            with st.expander(f"ADV - {category}", expanded=(len(search_term) > 0)):
                for name, tag_query in filtered_elements:
                    cb_key = f"cb_adv_{category}_{name}"
                    if st.checkbox(name, key=cb_key):
                        chosen_queries.append(tag_query)

    st.markdown("---")
    
    # Process Buttons Layout Frame
    col_kml, col_scan = st.columns(2)
    with col_kml:
        kml_string = generate_kml_radius(center_lat, center_lon, radius_input)
        st.download_button(
            label="EXPORT RADIUS",
            data=kml_string,
            file_name=f"Radius_{center_lat}_{center_lon}_{radius_input}m.kml",
            mime="application/vnd.google-earth.kml+xml",
            use_container_width=True
        )
    with col_scan:
        if st.button("SCAN AREA", type="primary", use_container_width=True):
            if not chosen_queries:
                st.warning("Please activate checkboxes.")
            else:
                with st.spinner("Compiling Overpass Nodes..."):
                    st.session_state.scan_data = execute_overpass_scan(center_lat, center_lon, radius_input, chosen_queries)

# -----------------------------------------------------------------------------
# 6. WORKSPACE MAIN DISPLAY AREA
# -----------------------------------------------------------------------------
# Map Layer DataFrame Assembly
target_layer = pd.DataFrame([{"latitude": center_lat, "longitude": center_lon, "name": "PRIME TARGET ASSET", "color": "#FF0000"}])

if st.session_state.scan_data is not None and not st.session_state.scan_data.empty:
    scanned_df = st.session_state.scan_data.copy()
    scanned_df['color'] = "#001a3d"
    map_visualization_dataframe = pd.concat([target_layer, scanned_df], ignore_index=True)
else:
    map_visualization_dataframe = target_layer

# Viewport Rendering
st.map(map_visualization_dataframe, latitude='latitude', longitude='longitude', size=20, use_container_width=True)

# Metrics Grid Display Footer
if st.session_state.scan_data is not None:
    st.markdown("### Trade Area Infrastructure Breakdown")
    if not st.session_state.scan_data.empty:
        # Frequency counts matching legacy `displayPoiCountSummary` functional loops
        summary_counts = st.session_state.scan_data['amenity'].value_counts().reset_index()
        summary_counts.columns = ['Detected Node Class', 'Volume Count']
        
        col_metric, col_grid = st.columns([1, 2])
        with col_metric:
            st.metric(label="Total Volumetric POI Yield", value=int(len(st.session_state.scan_data)))
        with col_grid:
            st.dataframe(summary_counts, hide_index=True, use_container_width=True)
    else:
        st.info("Zero active nodes found inside the target viewport bounds.")
