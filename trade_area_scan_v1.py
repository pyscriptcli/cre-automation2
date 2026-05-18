import streamlit as st
import urllib.parse

# Force wide-screen layout to map the workspace perfectly
st.set_page_config(layout="wide", page_title="Overpass Trade Area Scanner")

# Custom CSS styling to lock the sidebar to the original dark extension theme
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
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

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

# Extension State Variable Persistence
if "target_url" not in st.session_state:
    st.session_state.target_url = "https://overpass-turbo.eu/"

# Sidebar: Query Generator Pane
st.sidebar.title("TRADE AREA SCANNER")
st.sidebar.caption("Industrial Logistics Extension Framework")

coords_input = st.sidebar.text_input("Coordinates", value="14.6465, 121.0371")
radius_input = st.sidebar.number_input("Radius (M)", value=1000, step=100)

try:
    lat, lon = map(float, coords_input.split(","))
except ValueError:
    st.sidebar.error("Invalid format. Use: lat, lon")
    st.stop()

search_term = st.sidebar.text_input("SEARCH POI:", "").lower()

selected_queries = []

# Populate Category Checkboxes with unique namespacing keys
for cat, items in POI_CONFIG.items():
    filtered_items = [i for i in items if search_term in i[0].lower()]
    if filtered_items:
        st.sidebar.markdown(f"**{cat}**")
        for label, q_str in filtered_items:
            if st.sidebar.checkbox(label, key=f"core_{cat}_{label}"):
                selected_queries.append(q_str)

with st.sidebar.expander("ADVANCED POI LIBRARY", expanded=bool(search_term)):
    for cat, items in ADVANCED_CONFIG.items():
        filtered_items = [i for i in items if search_term in i[0].lower()]
        if filtered_items:
            st.sidebar.caption(cat)
            for label, q_str in filtered_items:
                if st.sidebar.checkbox(label, key=f"adv_{cat}_{label}"):
                    selected_queries.append(q_str)

st.sidebar.markdown("---")
scan_triggered = st.sidebar.button("Run Scan in Overpass")

# Generate Overpass QL Payload on trigger
if scan_triggered:
    if not selected_queries:
        st.sidebar.warning("Select at least one POI option.")
    else:
        clauses = "\n".join([f"  nwr[{q}](around:{radius_input},{lat},{lon});" for q in selected_queries])
        overpass_ql = f"[out:json][timeout:120];\n(\n{clauses}\n);\nout center;"
        
        # URL encode and append parameters exactly matching the original userscript behavior
        encoded_query = urllib.parse.quote(overpass_ql)
        st.session_state.target_url = f"https://overpass-turbo.eu/?Q={encoded_query}&R"

# --- Main Workspace Area ---
# Action bar providing both direct breakout links and embedded workspace states
col_title, col_action = st.columns([3, 1])
with col_title:
    st.subheader("Overpass Turbo Integration Canvas")
with col_action:
    st.markdown(f'<a href="{st.session_state.target_url}" target="_blank"><button style="width:100%; height:38px; background-color:#001a3d; color:white; border-radius:8px; font-weight:bold; border:none; cursor:pointer;">LAUNCH EXTERNAL WINDOW</button></a>', unsafe_allow_html=True)

# Native Workspace Embed Environment
st.components.v1.iframe(st.session_state.target_url, height=800, scrolling=True)
