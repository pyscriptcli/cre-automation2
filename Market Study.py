import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import math
import re

# Set page configuration to wide mode to emulate native wide map
st.set_page_config(layout="wide", page_title="Trade Area Scanner")

# Custom CSS to mimic the original dark navy/slate theme in the sidebar
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
    </style>
""", unsafe_index=True)

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

# Helper to verify Overpass regex filters match features locally
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

# Sidebar Panels
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

# Process Core Categories
for cat, items in POI_CONFIG.items():
    filtered_items = [i for i in items if search_term in i[0].lower()]
    if filtered_items:
        st.sidebar.markdown(f"**{cat}**")
        for label, q_str in filtered_items:
            if st.sidebar.checkbox(label, key=f"core_{label}"):
                selected_queries.append(q_str)
                selected_labels[q_str] = label

# Process Advanced Section
with st.sidebar.expander("ADVANCED POI LIBRARY", expanded=bool(search_term)):
    for cat, items in ADVANCED_CONFIG.items():
        filtered_items = [i for i in items if search_term in i[0].lower()]
        if filtered_items:
            st.sidebar.caption(cat)
            for label, q_str in filtered_items:
                if st.sidebar.checkbox(label, key=f"adv_{label}"):
                    selected_queries.append(q_str)
                    selected_labels[q_str] = label

# Bottom Action items
st.sidebar.markdown("---")
scan_triggered = st.sidebar.button("Scan Area")

# Calculate KML Generation Payload
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

# Main Dashboard Frame Area
st.title("Industrial Logistics Framework — Dashboard View")

# Run Overpass engine logic synchronously on click
features_data = []
counts_summary = {}

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
                    features_data = osm_data.get("elements", [])
                    
                    # Compute frequencies per active selection
                    for elem in features_data:
                        props = elem.get("tags", {})
                        for q_str in selected_queries:
                            if match_feature_to_query(props, q_str):
                                label = selected_labels[q_str]
                                counts_summary[label] = counts_summary.get(label, 0) + 1
                else:
                    st.error(f"Overpass API Error Status: {response.status_code}")
            except Exception as e:
                st.error(f"Network Connection Timeout/Failure: {str(e)}")

# Display Data KPI Metrics
if counts_summary:
    st.subheader("PRIME Philippines - Trade Area Scan Summary")
    df_metrics = pd.DataFrame(list(counts_summary.items()), columns=["POI Target Type", "Detected Nodes/Structures Count"])
    st.table(df_metrics)

# Base Map Layer Construction
m = folium.Map(location=[lat, lon], zoom_start=14, control_scale=True)

# Main red core asset target marker setup
folium.CircleMarker(
    location=[lat, lon],
    radius=7,
    color="#ffffff",
    fill=True,
    fill_color="#ff3333",
    fill_opacity=1,
    weight=2,
    popup=f"<b>PRIME TARGET ASSET</b><br>Lat: {lat}<br>Lon: {lon}"
).addTo(m)

# Enclosing visual radius perimeter limit
folium.Circle(
    location=[lat, lon],
    radius=radius_input,
    color="#001a3d",
    fill=True,
    fill_color="#001a3d",
    fill_opacity=0.1,
    weight=1
).addTo(m)

# Populating external OSM nodes found via engine
for elem in features_data:
    e_lat = elem.get("lat") or elem.get("center", {}).get("lat")
    e_lon = elem.get("lon") or elem.get("center", {}).get("lon")
    if e_lat and e_lon:
        tags = elem.get("tags", {})
        name = tags.get("name", "Unnamed Feature")
        amenity = tags.get("amenity") or tags.get("building") or tags.get("shop") or "POI Asset"
        
        folium.Marker(
            location=[e_lat, e_lon],
            popup=f"<b>{name}</b><br>Type: {amenity}",
            icon=folium.Icon(color="blue", icon="info-sign")
        ).addTo(m)

# Render Folium component output inside wide frame canvas space
st_folium(m, width="100%", height=600, returned_objects=[])

with st.expander("MAPPING LINKS", expanded=False):
    st.markdown("- [uMap Dashboard](https://umap.openstreetmap.fr/en/)")
    st.markdown("- [OpenPOIMap Viewer](https://openpoimap.org/)")
    st.markdown("- [GeoJSON Editor](https://geojson.io/)")
