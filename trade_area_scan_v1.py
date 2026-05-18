import streamlit as st
import urllib.parse
import re

# -----------------------------------------------------------------------------
# 1. APP CONFIGURATION & BRAND CUSTOMIZATION (NAVY, WHITE, GOLD)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TRADE AREA SCAN",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS injection for strict UI color control
st.markdown("""
    <style>
        /* Base Palette Config */
        :root {
            --navy: #001a3d;
            --white: #ffffff;
            --gold: #d4af37;
        }
        
        /* Main canvas configuration */
        .block-container {
            padding: 0rem !important;
        }
        
        /* Sidebar container layout overrides */
        [data-testid="stSidebar"] {
            background-color: var(--navy) !important;
            color: var(--white) !important;
            border-right: 2px solid var(--gold) !important;
        }
        
        /* Typography overrides within the sidebar */
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label {
            color: var(--white) !important;
            font-family: 'Arial', sans-serif !important;
        }
        
        /* Gold styling accent for expands and input highlights */
        [data-testid="stSidebar"] .st-expander {
            border: 1px solid rgba(212, 175, 55, 0.3) !important;
            background-color: rgba(255, 255, 255, 0.05) !important;
            border-radius: 6px;
            margin-bottom: 4px;
        }
        
        /* Form component modifications */
        div.stButton > button:first-child {
            background-color: var(--gold) !important;
            color: var(--navy) !important;
            font-weight: bold !important;
            border: 1px solid var(--gold) !important;
            border-radius: 4px !important;
            width: 100%;
        }
        
        div.stButton > button:first-child:hover {
            background-color: var(--white) !important;
            color: var(--navy) !important;
            border: 1px solid var(--white) !important;
        }

        /* Eradicate native frame paddings */
        iframe {
            border: none !important;
            width: 100% !important;
            height: calc(100vh - 5px) !important;
        }
        
        .stDeployButton, footer, #stDecoration { display:none !important; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. DICTIONARY DEFINITIONS (OSM TAG COMPILER STRUCTURES)
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
    "AMENITIES": [['ATM', '"amenity"="atm"'], ['Bank', '"amenity"="bank"'], ['Bench', '"amenity"="bench"'], ['Bicycle Parking', '"amenity"="bicycle_parking"']],
    "PLACE OF WORSHIP": [['Church', '"religion"="christian"'], ['Mosque', '"religion"="muslim"'], ['Cemetery', '"landuse"="cemetery"']],
    "FOOD & BEVERAGE": [['Bar', '"amenity"="bar"'], ['Cafe', '"amenity"="cafe"'], ['Fast food', '"amenity"="fast_food"'], ['Restaurant', '"amenity"="restaurant"']],
    "RETAIL_ADV": [['Beauty', '"shop"="beauty"'], ['Car', '"shop"="car"'], ['Department store', '"shop"="department_store"'], ['DIY/hardware', '"shop"~"hardware|doityourself",i']]
}

# Default landing dashboard viewport setup (Quezon City circle area baseline)
DEFAULT_URL = "https://overpass-turbo.eu/?C=14.6465;121.0371;14"

if 'target_url' not in st.session_state:
    st.session_state.target_url = DEFAULT_URL

# -----------------------------------------------------------------------------
# 3. CONTROL PANEL GRAPHICS (SIDEBAR COMPONENT ENGINE)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 style='color:#ffffff; margin-top:0;'>TRADE AREA SCAN</h2>", unsafe_allow_html=True)
    
    # Core Parameters Panel
    coords_input = st.text_input("Coordinates Target", value="14.6465, 121.0371")
    radius_input = st.number_input("Scan Radius (Meters)", min_value=100, max_value=100000, value=1000, step=100)
    
    # Parameter Extraction Logic
    coord_match = re.match(r"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", coords_input)
    if coord_match:
        lat, lon = coord_match.group(1), coord_match.group(2)
    else:
        lat, lon = "14.6465", "121.0371"

    # Live Search Bar Optimization
    search_term = st.text_input("🔍 Filter POI Library Options", "").lower()
    
    chosen_tags = []

    # Dynamic Component Processing Framework Loop
    for category, structural_items in POI_CONFIG.items():
        matched_items = [item for item in structural_items if search_term in item[0].lower()]
        if matched_items:
            with st.expander(category, expanded=(len(search_term) > 0)):
                for labels, tag_string in matched_items:
                    if st.checkbox(labels, key=f"core_{category}_{labels}"):
                        chosen_tags.append(tag_string)

    for category, structural_items in ADVANCED_CONFIG.items():
        matched_items = [item for item in structural_items if search_term in item[0].lower()]
        if matched_items:
            with st.expander(f"ADV - {category}", expanded=(len(search_term) > 0)):
                for labels, tag_string in matched_items:
                    if st.checkbox(labels, key=f"adv_{category}_{labels}"):
                        chosen_tags.append(tag_string)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Compilation Execution Trigger
    if st.button("SCAN AREA"):
        if not chosen_tags:
            st.error("Select minimal 1 POI filter query layer to scan.")
        else:
            # Build valid native Q Overpass Turbo statement script strings
            statement_blocks = "\n".join([f"  nwr[{tag}](around:{radius_input},{lat},{lon});" for tag in chosen_tags])
            compiled_overpass_ql = f"[out:json][timeout:120];\n(\n{statement_blocks}\n);\nout center;\n>;\nout skel qt;"
            
            # Formulate the programmatic URL redirect payload with autoplot flags
            encoded_ql = urllib.parse.quote(compiled_overpass_ql)
            
            # R execute flag and structural parameters passed directly inside workspace view
            st.session_state.target_url = f"https://overpass-turbo.eu/?Q={encoded_ql}&R"

# -----------------------------------------------------------------------------
# 4. PRIMARY VIEWPORT WORKSPACE (EDGE-TO-EDGE IFRAME ENGINE)
# -----------------------------------------------------------------------------
# Renders Overpass Turbo engine natively inside the remaining blank viewport canvas
st.components.v1.iframe(st.session_state.target_url)
