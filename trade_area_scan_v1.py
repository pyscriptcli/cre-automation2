import streamlit as st
import urllib.parse

# Force wide-screen layout
st.set_page_config(layout="wide", page_title="Market Study Dashboard", initial_sidebar_state="expanded")

# Initialize State Variables
if "map_fullscreen" not in st.session_state:
    st.session_state.map_fullscreen = False

if "target_url" not in st.session_state:
    st.session_state.target_url = "https://overpass-turbo.eu/"

def toggle_fullscreen():
    st.session_state.map_fullscreen = not st.session_state.map_fullscreen

# --- Custom CSS: Navy, White, & Gold Theme ---
st.markdown("""
    <style>
    /* Global Backgrounds */
    .stApp {
        background-color: #050a15; /* Deep rich space navy */
    }
    
    [data-testid="stSidebar"] {
        background-color: #0b1528 !important; /* Lighter navy for sidebar */
        border-right: 1px solid #1a2942;
    }

    /* Targeted Text Coloring (Fixes overlapping arrow icons) */
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, .stMarkdown p {
        color: #ffffff !important;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
    }

    /* Hide Top Header entirely */
    header[data-testid="stHeader"] {
        display: none !important;
    }

    /* Navigation Radio Buttons - Embossed Rounded Cards */
    div.stRadio > div {
        gap: 12px;
        padding: 0 5px;
    }
    div.stRadio > div > label {
        background: linear-gradient(145deg, #13223b, #0e192c);
        border: 1px solid #1e3354;
        border-radius: 16px;
        padding: 16px 12px !important;
        box-shadow: 3px 3px 6px #050a14, -3px -3px 6px #11203c;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;
        margin: 0;
    }
    div.stRadio > div > label:hover {
        border-color: #d4af37; /* Gold Accent */
        background: #1a2e4c;
    }
    div.stRadio > div > label[data-baseweb="radio"] > div:first-child {
        display: none; /* Hide default radio circle */
    }
    div.stRadio > div > label > div[data-testid="stMarkdownContainer"] > p {
        font-weight: 800;
        letter-spacing: 0.5px;
        color: #ffffff !important;
        margin: 0;
        font-size: 14px;
        text-transform: uppercase;
    }

    /* Inputs (Text & Number) - Rounded */
    .stTextInput input, .stNumberInput input {
        border-radius: 12px !important;
        background-color: #121e36 !important;
        border: 1px solid #1e3354 !important;
        color: #ffffff !important;
        padding: 10px 15px !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #d4af37 !important;
        box-shadow: 0 0 0 1px #d4af37 !important;
    }

    /* Accordion / Expander - Rounded & Styled */
    .streamlit-expanderHeader {
        background-color: #121e36 !important;
        border-radius: 12px !important;
        border: 1px solid #1e3354 !important;
        color: #ffffff !important;
        font-size: 13px !important;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    .streamlit-expanderHeader:hover {
        border-color: #4a6fa5 !important;
    }
    .streamlit-expanderContent {
        background-color: transparent !important;
        border: none !important;
        padding: 5px 10px 15px 10px !important;
    }

    /* Checkboxes */
    .stCheckbox > label > div[role="checkbox"] {
        border-radius: 6px !important;
        background-color: #121e36 !important;
        border: 1px solid #2a3f5f !important;
    }
    .stCheckbox > label > div[role="checkbox"][aria-checked="true"] {
        background-color: #d4af37 !important;
        border-color: #d4af37 !important;
    }

    /* Fixed Gold Scan Button at Bottom */
    .scan-btn-container {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 336px; /* Streamlit sidebar default width */
        padding: 20px;
        background: linear-gradient(0deg, #0b1528 80%, rgba(11,21,40,0) 100%);
        z-index: 100;
    }
    /* Target the primary action button */
    div.scan-btn-container div[data-testid="stButton"] > button {
        width: 100%;
        background: linear-gradient(135deg, #d4af37 0%, #b5952f 100%) !important;
        color: #050a15 !important; /* Dark text for high contrast on gold */
        font-weight: 900 !important;
        border-radius: 20px !important;
        border: none !important;
        padding: 14px 0 !important;
        box-shadow: 0 4px 10px rgba(212, 175, 55, 0.3);
        transition: all 0.2s;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div.scan-btn-container div[data-testid="stButton"] > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(212, 175, 55, 0.4);
    }
    div.scan-btn-container div[data-testid="stButton"] > button:active {
        transform: scale(0.98);
    }

    /* Top Corner Toggle Button Styling */
    .toggle-btn div[data-testid="stButton"] > button {
        background: #121e36 !important;
        color: #d4af37 !important;
        border: 1px solid #1e3354 !important;
        border-radius: 12px !important;
        padding: 4px 16px !important;
        font-size: 12px !important;
        font-weight: bold;
    }
    .toggle-btn div[data-testid="stButton"] > button:hover {
        border-color: #d4af37 !important;
    }

    /* Map Iframe Styling */
    iframe {
        border-radius: 16px;
        border: 2px solid #1e3354 !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    
    .main .block-container {
        padding: 1rem 1.5rem !important;
        max-width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)

# Configurations Data
POI_CONFIG = {
    "COMMERCIAL": [['Corporate Office', '"building"~"office|commercial",i'], ['IT/Tech Center', '"office"~"it|telecommunication",i'], ['Business Center', '"building"="commercial"'], ['Hospital', '"amenity"~"hospital|clinic",i'], ['Hotel', '"tourism"="hotel"'], ['Motel', '"tourism"="motel"']],
    "RETAIL": [['Mall/Dept Store', '"shop"~"mall|department_store",i'], ['Supermarket', '"shop"~"supermarket|grocery",i'], ['Convenience', '"shop"="convenience"'], ['Pharmacy', '"amenity"="pharmacy"'], ['Hardware', '"shop"~"hardware|doityourself",i']],
    "FOOD & BEVERAGE": [['Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee', '"amenity"~"cafe|coffee",i'], ['Fast Food', '"amenity"="fast_food"'], ['Bar/Pub', '"amenity"~"bar|pub|nightclub",i']],
    "INDUSTRIAL": [['Expressways', '"highway"~"motorway_junction|toll_gantry",i'], ['Ports', '"industrial"="port"'], ['Manufacturing', '"industrial"~"factory|manufacturing|processing",i'], ['Warehouses', '"building"~"warehouse|depot",i']],
    "INFRASTRUCTURE": [['City Hall', '"amenity"="townhall"'], ['Police', '"amenity"="police"'], ['Fire Station', '"amenity"="fire_station"']],
    "SCHOOLS": [['University', '"amenity"~"university|college",i'], ['K-12 School', '"amenity"="school"']]
}

ADVANCED_CONFIG = {
    "AMENITIES": [['ATM', '"amenity"="atm"'], ['Bank', '"amenity"="bank"'], ['Clinic', '"amenity"="clinic"'], ['Parking', '"amenity"="parking"']],
    "MISC": [['Busstop', '"highway"="bus_stop"'], ['City', '"place"="city"']]
}

# Icon Dictionary for Categories
ICON_MAP = {
    "COMMERCIAL": "🏢", "RETAIL": "🛒", "FOOD & BEVERAGE": "🍽️", 
    "INDUSTRIAL": "🏭", "INFRASTRUCTURE": "🏛️", "SCHOOLS": "🎓"
}

# --- Sidebar Header ---
st.sidebar.markdown("<div style='text-align: center; margin-bottom: 25px;'><h2 style='color: #ffffff; font-weight: 900; letter-spacing: 2px; margin-top: 10px;'>MARKET STUDY</h2></div>", unsafe_allow_html=True)

app_mode = st.sidebar.radio("Module", ["Trade Area Scan", "UMap Integration", "Demographics Hub"], label_visibility="collapsed")
st.sidebar.markdown("<br>", unsafe_allow_html=True)

# --- Routing Engine ---
if app_mode == "Trade Area Scan":
    
    st.sidebar.markdown("<div style='padding: 0 5px;'>", unsafe_allow_html=True)
    
    col1, col2 = st.sidebar.columns([2, 1])
    with col1:
        coords_input = st.text_input("Coordinates", value="14.6465, 121.0371")
    with col2:
        radius_input = st.number_input("Radius (M)", value=1000, step=100)

    try:
        lat, lon = map(float, coords_input.split(","))
    except ValueError:
        st.sidebar.error("Invalid format.")
        st.stop()

    search_term = st.sidebar.text_input("Search", "").lower()
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    selected_queries = []

    # Map POI Expanders with Icons
    for cat, items in POI_CONFIG.items():
        filtered_items = [i for i in items if search_term in i[0].lower()]
        if filtered_items:
            icon = ICON_MAP.get(cat, "📁")
            with st.sidebar.expander(f"{icon} {cat}", expanded=bool(search_term)):
                for label, q_str in filtered_items:
                    if st.checkbox(label, key=f"core_{cat}_{label}"):
                        selected_queries.append(q_str)

    with st.sidebar.expander("⚙️ ADVANCED POI", expanded=bool(search_term)):
        for cat, items in ADVANCED_CONFIG.items():
            filtered_items = [i for i in items if search_term in i[0].lower()]
            if filtered_items:
                st.markdown(f"<small style='color:#a0aec0; font-weight: bold;'>{cat}</small>", unsafe_allow_html=True)
                for label, q_str in filtered_items:
                    if st.checkbox(label, key=f"adv_{cat}_{label}"):
                        selected_queries.append(q_str)

    st.sidebar.markdown("<div style='height: 120px;'></div></div>", unsafe_allow_html=True)

    # Persistent Action Button
    with st.sidebar.container():
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

    # Screen Toggling Controls
    col_empty, col_toggle = st.columns([8, 1])
    with col_toggle:
        st.markdown("<div class='toggle-btn'>", unsafe_allow_html=True)
        if st.button("⛶ FULLSCREEN" if not st.session_state.map_fullscreen else "🗗 MINIMIZE"):
            toggle_fullscreen()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
    iframe_height = 950 if st.session_state.map_fullscreen else 650
    st.components.v1.iframe(st.session_state.target_url, height=iframe_height, scrolling=False)

elif app_mode == "UMap Integration":
    st.components.v1.iframe("https://umap.openstreetmap.fr/en/", height=850, scrolling=False)

elif app_mode == "Demographics Hub":
    st.markdown("<div style='padding: 40px; text-align: center;'><h2 style='color: #d4af37; font-weight: 900;'>POPULATION ANALYTICS</h2><br><p style='color:white;'>🚧 Data visualization models are currently provisioning. Check back soon.</p></div>", unsafe_allow_html=True)
