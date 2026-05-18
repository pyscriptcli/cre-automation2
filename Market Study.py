import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import math
import re

# Set page configuration to wide mode to emulate native wide map view
st.set_page_config(layout="wide", page_title="Trade Area Scanner")

# Custom CSS theme layout injection
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #001a3d;
        color: #FFFFFF;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
        font-family: Arial, sans-serif !important;
    }
    .stButton>button {
        width: 100%;
        background-color: #FFFFFF !important;
        color: #001a3d !important;
        font-weight: 900 !important;
        border-radius: 8px !important;
        text-transform: uppercase;
        border: none;
    }
    [data-testid="stMetricValue"] {
        color: #001a3d !important;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Session State values to hold query metrics safely across sidebar clicks
if "features_data" not in st.session_state:
    st.session_state.features_data = []
if "counts_summary" not in st.session_state:
    st.session_state.counts_summary = {}

# Define configurations identical to the Userscript
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
    "PLACE OF WORSHIP": [['Church', '"religion"="christian"'], ['Mosque', '"religion"="muslim"'], ['Buddhist Temple', '"religion"="buddhist"'], ['Hindu Temple', '"religion"="hindu"'], ['Synagogue', '"religion"="jewish"'], ['Cemetery', '"landuse"="cemetery"'], ['Alpine Hut', '"tourism"="alpine_hut"'], ['Apartment', '"tourism"="apartment"'], ['Camp Site', '"tourism"="camp_site"'], ['Chalet', '"tourism"="chalet"'], ['Guest House', '"tourism"="guest_house"'], ['Hostel', '"tourism"="hostel"'], ['Hotel', '"tourism"="hotel"'], ['Motel', '"tourism"="motel"'], ['Casino', '"amenity"="casino"'], ['Spa', '"leisure"="spa"'], ['Sauna', '"leisure"="sauna"']],
    "FOOD & BEVERAGE": [['Bar', '"amenity"="bar"'], ['BBQ', '"amenity"="bbq"'], ['Biergarten', '"amenity"="biergarten"'], ['Cafe', '"amenity"="cafe"'], ['Fast food', '"amenity"="fast_food"'], ['Food court', '"amenity"="food_court"'], ['Ice cream', '"amenity"="ice_cream"'], ['Pub', '"amenity"="pub"'], ['Restaurant', '"amenity"="restaurant"']],
    "RETAIL_ADV": [['Beauty', '"shop"="beauty"'], ['Bicycle', '"shop"="bicycle"'], ['Books/Stationary', '"shop"~"books|stationary",i'], ['Car', '"shop"="car"'], ['Chemist', '"shop"="chemist"'], ['Clothes', '"shop"="clothes"'], ['Copyshop', '"shop"="copyshop"'], ['Cosmetics', '"shop"="cosmetics"'], ['Department store', '"shop"="department_store"'], ['DIY/hardware', '"shop"~"hardware|doityourself",i'], ['Garden centre', '"shop"="garden_centre"'], ['General', '"shop"="general"'], ['Gift', '"shop"="gift"'], ['Hairdresser', '"shop"="hairdresser"'], ['Jewelry', '"shop"="jewelry"'], ['Kiosk', '"shop"="kiosk"'], ['Leather', '"shop"="leather"'], ['Marketplace', '"amenity"="marketplace"'], ['Musical instrument', '"shop"="musical_instrument"'], ['Optician', '"shop"="optician"'], ['Pets', '"shop"="pets"'], ['Phone', '"shop"="mobile_phone"'], ['Photo', '"shop"="photo"'], ['Shoes', '"shop"="shoes"'], ['Shopping centre', '"shop"="mall"'], ['Textiles', '"shop"="textiles"'], ['Toys', '"shop"="toys"']],
    "SPORTS": [['American football', '"sport"="american_football"'], ['Baseball', '"sport"="baseball"'], ['Basketball', '"sport"="basketball"'], ['Cycling', '"sport"="cycling"'], ['Gymnastics', '"sport"="gymnastics"'], ['Golf', '"sport"="golf"'], ['Hockey', '"sport"="hockey"'], ['Horse racing', '"sport"="horse_racing"'], ['Ice hockey', '"sport"="ice_hockey"'], ['Soccer', '"sport"="soccer"'], ['Sports centre', '"leisure"="sports_centre"'], ['Surfing', '"sport"="surfing"'], ['Swimming', '"sport"="swimming"'], ['Tennis', '"sport"="tennis"'], ['Volleyball', '"sport"="volleyball"']],
    "MISCELLANEOUS": [['Busstop', '"highway"="bus_stop"'], ['E-bike charging', '"amenity"="charging_station"'], ['Kindergarten', '"amenity"="kindergarten"'], ['Marketplace', '"amenity"="marketplace"'], ['Office', '"office"="yes"'], ['Recycling', '"amenity"="recycling"'], ['Travel agency', '"shop"="travel_agency"'], ['Defibrillator - AED', '"emergency"="defibrillator"'], ['Fire hose/extinguisher', '"emergency"~"fire_hose|fire_extinguisher",i'], ['Fixme', '"fixme"~".",i'], ['Note-Node', '"type"="node"'], ['Note-Way', '"type"="way"'], ['Construction', '"landuse"="construction"'], ['Image', '"image"~".",i'], ['Public camera', '"man_made"="surveillance"'], ['City', '"place"="city"'], ['Town', '"place"="town"'], ['Village', '"place"="village"'], ['Hamlet', '"place"="hamlet"'], ['Suburb', '"place"="suburb"']]
}

def match_feature_to_query(props, query_str):
    match = re.match(r'"([^"]+)"\s*(=|~)\s*"([^"]+)"', query_str)
    if not match:
        return False
    key, op, val = match.groups()
    if key not in props:
        return False
    prop_val = str(props[key])
    if op == '=':
        return prop_val.lower() == val.lower()
    if op == '~':
        clean_val = val.replace(',i', '')
        return bool(re.search(clean_val, prop_val, re.IGNORECASE))
    return False

# Sidebar Config Canvas
st.sidebar.title("TRADE AREA SCANNER")

coords_input = st.sidebar.text_input("Coordinates", value="14.6465, 121.0371")
radius_input = st.sidebar.number_input("Radius (M)", value=1000, step=100)

try:
    lat, lon = map(float, coords_input.split(","))
except ValueError:
    st.sidebar.error("Invalid coordinates format. Use: lat, lon")
    st.stop()

search_term = st.sidebar.text_input("SEARCH POI:", "").lower()

selected_queries = []
selected_labels = {}

# Build Category Trees
for cat, items in POI_CONFIG.items():
    filtered_items = [i for i in items if search_term in i[0].lower()]
    if filtered_items:
        st.sidebar.markdown(f"**{cat}**")
        for label, q_str in filtered_items:
            if st.sidebar.checkbox(label, key=f"core_{cat}_{label}"):
                selected_queries.append(q_str)
                selected_labels[q_str] = label

with st.sidebar.expander("ADVANCED POI LIBRARY", expanded=bool(search_term)):
    for cat, items in ADVANCED_CONFIG.items():
        filtered_items = [i for i in items if search_term in i[0].lower()]
        if filtered_items:
            st.sidebar.caption(cat)
            for label, q_str in filtered_items:
                if st.sidebar.checkbox(label, key=f"adv_{cat}_{label}"):
                    selected_queries.append(q_str)
                    selected_labels[q_str] = label

st.sidebar.markdown("---")
scan_triggered = st.sidebar.button("Scan Area")

# Calculate KML Polygons
kml_str = f'<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Radius Scan</name><Placemark><Polygon><outerBoundaryIs><LinearRing><coordinates>'
for i in range(37):
    angle = (i * 10) * math.pi / 180
    dLat = (radius_input / 6371000) * math.cos(angle)
    dLon = (radius_input / (6371000 * math.cos(lat * math.pi / 180))) * math.sin(angle)
    kml_str += f"{lon + (dLon * 180 / math.pi)},{lat + (dLat * 180 / math.pi)},0 "
kml_str += f'</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></Document></kml>'

st.sidebar.download_button(
    label="Export Radius (KML)",
    data=kml_str,
    file_name=f"Radius_{coords_input.strip()}_{radius_input}m.kml",
    mime="application/vnd.google-earth.kml+xml"
)

# Main Application Board Area
st.title("Industrial Logistics Framework — Dashboard View")

if scan_triggered:
    if not selected_queries:
        st.warning("Please select at least one POI option from the sidebar scanner configuration.")
    else:
        with st.spinner("Executing Overpass API Trade Area Scan..."):
            clauses = "\n".join([f"  nwr[{q}](around:{radius_input},{lat},{lon});" for q in selected_queries])
            overpass_query = f"[out:json][timeout:120];\n(\n{clauses}\n);\nout center;"
            
            url = "https://overpass-api.de/api/interpreter"
            try:
                response = requests.post(url, data={"data": overpass_query}, timeout=130)
                if response.status_code == 200:
                    osm_data = response.json()
                    st.session_state.features_data = osm_data.get("elements", [])
                    
                    temp_counts = {}
                    for elem in st.session_state.features_data:
                        props = elem.get("tags", {})
                        for q_str in selected_queries:
                            if match_feature_to_query(props, q_str):
                                label = selected_labels[q_str]
                                temp_counts[label] = temp_counts.get(label, 0) + 1
                    st.session_state.counts_summary = temp_counts
                else:
                    st.error(f"Overpass API Error Status: {response.status_code}")
            except Exception as e:
                st.error(f"Network Connection Failure: {str(e)}")

# UI Analytics Metrics
if st.session_state.counts_summary:
    st.subheader("PRIME Philippines - Trade Area Scan Summary")
    cols = st.columns(min(len(st.session_state.counts_summary), 4))
    for idx, (label, count) in enumerate(st.session_state.counts_summary.items()):
        col_target = cols[idx % 4]
        col_target.metric(label=label, value=f"{count} Node(s)")
    
    with st.expander("Detailed Data Inspector Table", expanded=False):
        df_metrics = pd.DataFrame(list(st.session_state.counts_summary.items()), columns=["POI Target Type", "Detected Nodes Count"])
        st.dataframe(df_metrics, use_container_width=True)

# --- MAP RENDERING ENGINE BLOCK ---
trade_map = folium.Map(location=[lat, lon], zoom_start=14)

# Main target asset marker placement
folium.CircleMarker(
    location=[lat, lon],
    radius=8,
    color="#ffffff",
    fill=True,
    fill_color="#ff3333",
    fill_opacity=1,
    weight=2,
    popup=f"<b>PRIME TARGET ASSET</b><br>Lat: {lat}<br>Lon: {lon}"
).add_to(trade_map) # FIXED: Changed from .addTo() to .add_to()

# Radius layout ring construction
folium.Circle(
    location=[lat, lon],
    radius=radius_input,
    color="#001a3d",
    fill=True,
    fill_color="#001a3d",
    fill_opacity=0.06,
    weight=1.5
).add_to(trade_map) # FIXED: Changed from .addTo() to .add_to()

# Marker cluster mapping for heavy node loads
marker_cluster = MarkerCluster(name="Extracted POI Nodes").add_to(trade_map) # FIXED: Changed from .addTo() to .add_to()

# Map over elements to populate external markers
for elem in st.session_state.features_data:
    center_geometry = elem.get("center") or {}
    e_lat = elem.get("lat") or center_geometry.get("lat")
    e_lon = elem.get("lon") or center_geometry.get("lon")
    
    if e_lat and e_lon:
        tags = elem.get("tags", {})
        name = tags.get("name", "Unnamed Feature / Asset")
        
        popup_html = f"<b>{name}</b><hr style='margin:4px 0;'>"
        popup_html += "".join([f"<div style='font-size:11px;'><b>{k}:</b> {v}</div>" for k, v in tags.items() if k != "name"])
        
        folium.Marker(
            location=[e_lat, e_lon],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color="cadetblue", icon="building", prefix="fa")
        ).add_to(marker_cluster) # FIXED: Changed from .addTo() to .add_to()

# Final render invocation mapping
st_folium(trade_map, width=1300, height=650, key="trade_area_map_canvas")

with st.expander("MAPPING LINKS", expanded=False):
    st.markdown("- [uMap Dashboard](https://umap.openstreetmap.fr/en/)")
    st.markdown("- [OpenPOIMap Viewer](https://openpoimap.org/)")
    st.markdown("- [GeoJSON Editor](https://geojson.io/)")
