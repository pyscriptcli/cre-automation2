import streamlit as st
import urllib.parse

# Force wide-screen layout to map the workspace perfectly
st.set_page_config(layout="wide", page_title="Market Study Dashboard", initial_sidebar_state="expanded")

# --- Custom CSS for Light Theme & Full-Screen Map ---
st.markdown("""
    <style>
    /* Light Theme Sidebar Foundation */
    [data-testid="stSidebar"] {
        background-color: #f7f9fc; /* Soft light gray */
    }
    
    [data-testid="stSidebar"] * {
        color: #2d3748 !important; /* Dark slate text */
        font-family: Arial, sans-serif !important;
    }

    /* Remove padding to allow full-width components in sidebar */
    [data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
        padding-bottom: 0;
    }

    /* Embossed Container Style for Navigation (Light Mode) */
    div.stRadio > div {
        display: flex;
        flex-direction: column;
        gap: 10px;
        padding: 0 10px;
    }
    div.stRadio > div > label {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 10px !important;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.04);
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: center;
        margin: 0;
    }
    div.stRadio > div > label:hover {
        border-color: #cbd5e0;
        background: #f7fafc;
        box-shadow: 3px 3px 8px rgba(0,0,0,0.08);
    }
    /* Style the radio text inside the box */
    div.stRadio > div > label > div[data-testid="stMarkdownContainer"] > p {
        font-weight: 800;
        letter-spacing: 0.5px;
        color: #2b6cb0 !important;
        margin: 0;
        font-size: 14px;
        text-transform: uppercase;
    }

    /* Accordion (Expander) Styling for clean POI lists */
    .streamlit-expanderHeader {
        background-color: #edf2f7 !important;
        color: #4a5568 !important;
        border-radius: 6px;
        font-size: 12px !important;
        font-weight: 700;
        text-transform: uppercase;
        border: 1px solid #e2e8f0;
    }
    .streamlit-expanderContent {
        background-color: #ffffff;
        border-left: 2px solid #cbd5e0;
        padding-left: 10px;
    }

    /* Persistent Action Button Styling - White Button */
    .scan-btn-container {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 336px; /* Matches default sidebar width */
        padding: 20px;
        background-color: rgba(247, 249, 252, 0.95);
        backdrop-filter: blur(5px);
        border-top: 1px solid #e2e8f0;
        z-index: 100;
    }
    .stButton>button {
        width: 100%;
        background: #ffffff !important;
        color: #1a202c !important;
        font-weight: 900 !important;
        border-radius: 8px !important;
        text-transform: uppercase;
        border: 2px solid #e2e8f0 !important;
        padding: 12px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: transform 0.1s, box-shadow 0.1s;
    }
    .stButton>button:hover {
        border-color: #cbd5e0 !important;
        box-shadow: 0 6px 8px rgba(0,0,0,0.08);
    }
    .stButton>button:active {
        transform: scale(0.98);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Absolute Full-Screen Iframe Setup */
    iframe {
        border: none !important;
        outline: none !important;
        width: 100%;
    }
    
    /* Eradicate main area padding and margins to let map hit the edges */
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    
    /* Hide Streamlit top header bar for pure app view */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Hide Streamlit footer */
    footer {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# Define configurations
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

ADVANCED_CONFIG = {
    "AMENITIES": [['ATM', '"amenity"="atm"'], ['Bank', '"amenity"="bank"'], ['Clinic', '"amenity"="clinic"'], ['Parking', '"amenity"="parking"']],
    "MISC": [['Busstop', '"highway"="bus_stop"'], ['City', '"place"="city"'], ['Town', '"place"="town"']]
}

# Extension State Variable Persistence
if "target_url" not in st.session_state:
    st.session_state.target_url = "https://overpass-turbo.eu/"

# --- Navigation Section ---
st.sidebar.markdown("<h2 style='text-align: center; color: #1a202c; font-weight: 900; letter-spacing: 1px; margin-bottom: 20px;'>MARKET STUDY</h2>", unsafe_allow_html=True)

# The styled radio buttons act as the embossed containers
app_mode = st.sidebar.radio(
    "Select Module",
    ["Trade Area Scan", "UMap Integration", "Demographics Hub"],
    label_visibility="collapsed"
)

st.sidebar.markdown("<br>", unsafe_allow_html=True)

# --- Routing Engine ---
if app_mode == "Trade Area Scan":
    
    st.sidebar.markdown("<div style='padding: 0 10px;'>", unsafe_allow_html=True) 
    
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
    st.sidebar.markdown("<hr style='margin: 10px 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)
    
    selected_queries = []

    st.sidebar.markdown("<small style='color:#718096; font-weight: bold;'>SELECT TARGET ASSETS</small>", unsafe_allow_html=True)
    
    for cat, items in POI_CONFIG.items():
        filtered_items = [i for i in items if search_term in i[0].lower()]
        if filtered_items:
            with st.sidebar.expander(f"📁 {cat}", expanded=bool(search_term)):
                for label, q_str in filtered_items:
                    if st.checkbox(label, key=f"core_{cat}_{label}"):
                        selected_queries.append(q_str)

    with st.sidebar.expander("⚙️ ADVANCED POI LIBRARY", expanded=bool(search_term)):
        for cat, items in ADVANCED_CONFIG.items():
            filtered_items = [i for i in items if search_term in i[0].lower()]
            if filtered_items:
                st.markdown(f"<small style='color:#a0aec0;'><b>{cat}</b></small>", unsafe_allow_html=True)
                for label, q_str in filtered_items:
                    if st.checkbox(label, key=f"adv_{cat}_{label}"):
                        selected_queries.append(q_str)

    # Padding to prevent button overlap
    st.sidebar.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

    # Persistent Bottom Button Layout
    scan_container = st.sidebar.container()
    with scan_container:
        st.markdown("<div class='scan-btn-container'>", unsafe_allow_html=True)
        scan_triggered = st.button("SCAN AREA")
        st.markdown("</div>", unsafe_allow_html=True)

    if scan_triggered:
        if not selected_queries:
            st.sidebar.warning("Select at least one POI option.")
        else:
            clauses = "\n".join([f"  nwr[{q}](around:{radius_input},{lat},{lon});" for q in selected_queries])
            overpass_ql = f"[out:json][timeout:120];\n(\n{clauses}\n);\nout center;"
            encoded_query = urllib.parse.quote(overpass_ql)
            st.session_state.target_url = f"https://overpass-turbo.eu/?Q={encoded_query}&R"

    # Borderless, Title-less Workspace Map. 
    # Height set to an aggressive 1000px so it automatically clips to the edge of standard monitors.
    st.components.v1.iframe(st.session_state.target_url, height=1000, scrolling=False)

elif app_mode == "UMap Integration":
    st.components.v1.iframe("https://umap.openstreetmap.fr/en/", height=1000, scrolling=False)

elif app_mode == "Demographics Hub":
    # Fallback padding just for the 'coming soon' page so text isn't stuck to the very edge.
    st.markdown("<div style='padding: 40px;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #2b6cb0; font-weight: 800;'>Population Analytics</h3>", unsafe_allow_html=True)
    st.info("🚧 Data visualization models are currently provisioning. Check back soon.")
    st.markdown("</div>", unsafe_allow_html=True)
