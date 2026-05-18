import streamlit as st
import urllib.parse

# Force wide-screen layout to map the workspace perfectly
st.set_page_config(layout="wide", page_title="Market Study Dashboard", initial_sidebar_state="expanded")

# --- Custom CSS for UI Overhaul ---
st.markdown("""
    <style>
    /* Dark Theme Sidebar Foundation */
    [data-testid="stSidebar"] {
        background-color: #041221; /* Slightly darker navy for depth */
        color: #E2E8F0;
    }
    
    /* Remove padding to allow full-width components in sidebar */
    [data-testid="stSidebar"] .block-container {
        padding-top: 1rem;
        padding-bottom: 0;
    }

    /* Embossed Container Style for Navigation */
    div.stRadio > div {
        display: flex;
        flex-direction: column;
        gap: 10px;
        padding: 0 10px;
    }
    div.stRadio > div > label {
        background: linear-gradient(145deg, #05182d, #030e1a);
        border: 1px solid #1a365d;
        border-radius: 10px;
        padding: 15px 10px !important;
        box-shadow:  4px 4px 8px #020a12, -4px -4px 8px #061a30;
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: center;
        margin: 0;
    }
    div.stRadio > div > label:hover {
        border-color: #3182ce;
        background: #061f3a;
    }
    /* Style the radio text inside the box */
    div.stRadio > div > label > div[data-testid="stMarkdownContainer"] > p {
        font-weight: 700;
        letter-spacing: 0.5px;
        color: #63b3ed;
        margin: 0;
        font-size: 14px;
        text-transform: uppercase;
    }

    /* Accordion (Expander) Styling for clean POI lists */
    .streamlit-expanderHeader {
        background-color: #0A2540 !important;
        color: #A0AEC0 !important;
        border-radius: 6px;
        font-size: 12px !important;
        text-transform: uppercase;
        border-bottom: 1px solid #1A365D;
    }
    .streamlit-expanderContent {
        background-color: #041221;
        border-left: 2px solid #0A2540;
        padding-left: 10px;
    }

    /* Persistent Action Button Styling */
    .scan-btn-container {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 336px; /* Matches default sidebar width */
        padding: 20px;
        background-color: rgba(4, 18, 33, 0.95);
        backdrop-filter: blur(5px);
        border-top: 1px solid #1A365D;
        z-index: 100;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #3182ce 0%, #2b6cb0 100%) !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        border-radius: 8px !important;
        text-transform: uppercase;
        border: none;
        padding: 12px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.1s;
    }
    .stButton>button:active {
        transform: scale(0.98);
    }

    /* Global Iframe cleanup */
    iframe {
        border: none !important;
        outline: none !important;
        border-radius: 8px; /* Slight rounding for the map container */
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .main .block-container {
        padding-top: 2rem !important;
        max-width: 98% !important; /* Make map wider */
    }
    </style>
""", unsafe_allow_html=True)

# Define configurations identical to the Userscript
POI_CONFIG = {
    "COMMERCIAL": [['Corporate Office', '"building"~"office|commercial",i'], ['IT/Tech Center', '"office"~"it|telecommunication",i'], ['Business Center', '"building"="commercial"'], ['Hospital', '"amenity"~"hospital|clinic",i'], ['Hotel', '"tourism"="hotel"'], ['Motel', '"tourism"="motel"']],
    "RETAIL": [['Mall/Department Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"supermarket|grocery",i'], ['Convenience Store', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Hardware', '"shop"~"hardware|doityourself",i'], ['General Shops', '"shop"~"boutique|clothes|shoes",i']],
    "FOOD & BEVERAGE": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee Shop', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"'], ['Bar/Pub/Nightclub', '"amenity"~"bar|pub|nightclub",i'], ['Bakery/Pastry', '"shop"="blackery"']],
    "INDUSTRIAL": [
        ['Expressways', '"highway"~"motorway_junction|toll_gantry",i'], 
        ['Ports', '"industrial"="port"'], 
        ['Manufacturing', '"industrial"~"factory|manufacturing|processing",i'],
        ['Cold Storage', '"warehouse"~"cold_store|cold_storage",i'],
        ['Industrial Parks', '"landuse"~"industrial|industrial_estate",i'],
        ['Warehouses', '"building"~"warehouse|depot",i']
    ],
    "INFRASTRUCTURE": [['City Hall', '"amenity"="townhall"'], ['Police', '"amenity"="police"'], ['Fire Station', '"amenity"="fire_station"'], ['Airport', '"aeroway"~"terminal|aerodrome",i']],
    "SCHOOLS": [['University', '"amenity"~"university|college",i'], ['K-12 School', '"amenity"="school"']]
}

# Condensed Advanced Config for demo purposes (you can expand this back to your full list)
ADVANCED_CONFIG = {
    "AMENITIES": [['ATM', '"amenity"="atm"'], ['Bank', '"amenity"="bank"'], ['Clinic', '"amenity"="clinic"'], ['Parking', '"amenity"="parking"']],
    "MISC": [['Busstop', '"highway"="bus_stop"'], ['City', '"place"="city"'], ['Town', '"place"="town"']]
}

# Extension State Variable Persistence
if "target_url" not in st.session_state:
    st.session_state.target_url = "https://overpass-turbo.eu/"

# --- Navigation Section ---
st.sidebar.markdown("<h2 style='text-align: center; color: #fff; font-weight: 800; letter-spacing: 1px; margin-bottom: 20px;'>MARKET STUDY</h2>", unsafe_allow_html=True)

# The styled radio buttons act as the embossed containers
app_mode = st.sidebar.radio(
    "Select Module",
    ["Trade Area Scan", "UMap Integration", "Demographics Hub"],
    label_visibility="collapsed"
)

st.sidebar.markdown("<br>", unsafe_allow_html=True)

# --- Routing Engine ---
if app_mode == "Trade Area Scan":
    
    # 1. Load POI Generator
    st.sidebar.markdown("<div style='padding: 0 10px;'>", unsafe_allow_html=True) # Inner padding container
    
    col1, col2 = st.sidebar.columns([2, 1])
    with col1:
        coords_input = st.text_input("Target Coordinates", value="14.6465, 121.0371", help="Format: Lat, Lon")
    with col2:
        radius_input = st.number_input("Radius (M)", value=1000, step=100)

    try:
        lat, lon = map(float, coords_input.split(","))
    except ValueError:
        st.sidebar.error("Invalid format. Use: lat, lon")
        st.stop()

    search_term = st.sidebar.text_input("🔍 Quick Search POI:", "").lower()
    st.sidebar.markdown("<hr style='margin: 10px 0; border-color: #1A365D;'>", unsafe_allow_html=True)
    
    selected_queries = []

    # Accordion Layout for POIs (The fix for the endless scroll)
    st.sidebar.caption("SELECT TARGET ASSETS")
    
    for cat, items in POI_CONFIG.items():
        filtered_items = [i for i in items if search_term in i[0].lower()]
        if filtered_items:
            # Use expander for each category. Expand automatically if searching.
            with st.sidebar.expander(f"📁 {cat}", expanded=bool(search_term)):
                for label, q_str in filtered_items:
                    if st.checkbox(label, key=f"core_{cat}_{label}"):
                        selected_queries.append(q_str)

    with st.sidebar.expander("⚙️ ADVANCED POI LIBRARY", expanded=bool(search_term)):
        for cat, items in ADVANCED_CONFIG.items():
            filtered_items = [i for i in items if search_term in i[0].lower()]
            if filtered_items:
                st.markdown(f"<small style='color:#718096;'><b>{cat}</b></small>", unsafe_allow_html=True)
                for label, q_str in filtered_items:
                    if st.checkbox(label, key=f"adv_{cat}_{label}"):
                        selected_queries.append(q_str)

    # Add space at the bottom so the last items aren't hidden by the floating button
    st.sidebar.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown("</div>", unsafe_allow_html=True) # End inner padding container

    # Persistent Bottom Button using empty container hack
    scan_container = st.sidebar.container()
    with scan_container:
        st.markdown("<div class='scan-btn-container'>", unsafe_allow_html=True)
        scan_triggered = st.button("🚀 EXECUTE OVERPASS SCAN")
        st.markdown("</div>", unsafe_allow_html=True)

    if scan_triggered:
        if not selected_queries:
            st.sidebar.warning("Select at least one POI option.")
        else:
            clauses = "\n".join([f"  nwr[{q}](around:{radius_input},{lat},{lon});" for q in selected_queries])
            overpass_ql = f"[out:json][timeout:120];\n(\n{clauses}\n);\nout center;"
            encoded_query = urllib.parse.quote(overpass_ql)
            st.session_state.target_url = f"https://overpass-turbo.eu/?Q={encoded_query}&R"

    # Main Area Output
    st.markdown("<h3 style='color: #2b6cb0; font-weight: 800;'>Trade Area Scan Workbench</h3>", unsafe_allow_html=True)
    st.components.v1.iframe(st.session_state.target_url, height=850, scrolling=True)

elif app_mode == "UMap Integration":
    st.markdown("<h3 style='color: #2b6cb0; font-weight: 800;'>UMap Interactive Editor</h3>", unsafe_allow_html=True)
    st.components.v1.iframe("https://umap.openstreetmap.fr/en/", height=850, scrolling=True)

elif app_mode == "Demographics Hub":
    st.markdown("<h3 style='color: #2b6cb0; font-weight: 800;'>Population Analytics</h3>", unsafe_allow_html=True)
    st.info("🚧 Data visualization models are currently provisioning. Check back soon.")
