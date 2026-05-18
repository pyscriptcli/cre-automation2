import streamlit as st
import urllib.parse

# Enforce clean wide layout viewport mapping
st.set_page_config(layout="wide", page_title="Market Study Deck Engine", initial_sidebar_state="expanded")

# --- Initialize Global Framework Persistence Keys ---
if "map_fullscreen" not in st.session_state:
    st.session_state.map_fullscreen = False

if "target_url" not in st.session_state:
    st.session_state.target_url = "https://overpass-turbo.eu/"

def toggle_workspace_dimension():
    st.session_state.map_fullscreen = not st.session_state.map_fullscreen

# --- Custom Premium CSS Blueprint Engine ---
st.markdown("""
    <style>
    /* Baseline Background Profiles */
    .stApp {
        background-color: #0A192F !important; /* Deep Imperial Navy Canvas */
    }
    
    [data-testid="stSidebar"] {
        background-color: #0D203D !important; /* Premium Executive Slate Blue */
        border-right: 2px solid #1E3A63 !important;
        box-shadow: 4px 0px 15px rgba(0, 0, 0, 0.5);
    }

    /* Core Typographic Sanitization Rules */
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label, 
    .stMarkdown p {
        color: #FFFFFF !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, Arial, sans-serif !important;
    }
    
    /* Category Header Accentuation */
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] strong {
        color: #D4AF37 !important; /* Brushed Champagne Gold Accent */
        font-weight: 700 !important;
        letter-spacing: 0.5px;
    }

    /* Remove Streamlit Default Overhead Footprints */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    footer {
        display: none !important;
    }

    /* Navigation Radio Architecture - Embossed High-End Border Cards */
    div.stRadio > div {
        gap: 14px;
        padding: 5px 10px;
    }
    div.stRadio > div > label {
        background: linear-gradient(135deg, #132A4A 0%, #0E1E38 100%);
        border: 1px solid #234375;
        border-radius: 14px !important;
        padding: 14px 12px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.1), 0 8px 16px rgba(0,0,0,0.3);
        cursor: pointer;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        text-align: center;
        margin: 0;
    }
    div.stRadio > div > label:hover {
        border-color: #D4AF37 !important;
        background: #17355E !important;
        transform: translateY(-1px);
    }
    div.stRadio > div > label[data-baseweb="radio"] > div:first-child {
        display: none !important; /* Strip default round indicator node */
    }
    div.stRadio > div > label > div[data-testid="stMarkdownContainer"] > p {
        font-weight: 800 !important;
        color: #FFFFFF !important;
        font-size: 13px !important;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    }

    /* Rounded Text Field Container Interfaces */
    .stTextInput input, .stNumberInput input {
        border-radius: 12px !important;
        background-color: #112544 !important;
        border: 1px solid #234375 !important;
        color: #FFFFFF !important;
        padding: 10px 14px !important;
        font-size: 13px !important;
        transition: border-color 0.2s;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #D4AF37 !important;
        box-shadow: 0 0 0 1px #D4AF37 !important;
    }

    /* Accordion Layer Boxes (Excluding Text Collision Loops) */
    .streamlit-expanderHeader {
        background-color: #112544 !important;
        border-radius: 12px !important;
        border: 1px solid #234375 !important;
        padding: 10px 14px !important;
        margin-bottom: 6px;
    }
    .streamlit-expanderHeader:hover {
        border-color: #D4AF37 !important;
    }
    .streamlit-expanderHeader p {
        font-size: 12px !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        color: #E2E8F0 !important;
    }
    .streamlit-expanderContent {
        background-color: transparent !important;
        border: none !important;
        padding: 8px 12px 14px 12px !important;
    }

    /* Checkbox Interface Formats */
    .stCheckbox > label > div[role="checkbox"] {
        border-radius: 6px !important;
        background-color: #112544 !important;
        border: 1px solid #2C4D7A !important;
    }
    .stCheckbox > label > div[role="checkbox"][aria-checked="true"] {
        background-color: #D4AF37 !important;
        border-color: #D4AF37 !important;
    }

    /* Sticky Sidebar Layout Control Footer Overlay */
    .scan-btn-container {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 336px;
        padding: 24px 20px;
        background: linear-gradient(180deg, rgba(13,32,61,0) 0%, #0D203D 25%, #0D203D 100%);
        z-index: 100;
    }
    div.scan-btn-container div[data-testid="stButton"] > button {
        width: 100%;
        background: #FFFFFF !important; /* Polished Pure White Solid Background */
        color: #0A192F !important;      /* Contrast Dark Navy Text */
        font-weight: 900 !important;
        border-radius: 24px !important;
        border: 2px solid #FFFFFF !important;
        padding: 12px 0 !important;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.4);
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 13px !important;
    }
    div.scan-btn-container div[data-testid="stButton"] > button:hover {
        background: #F7FAFC !important;
        transform: translateY(-2px);
        box-shadow: 0 12px 24px rgba(255, 255, 255, 0.15);
    }

    /* Upper-Right Corner Window Dimension Button */
    .toggle-btn-wrapper {
        display: flex;
        justify-content: flex-end;
        padding-bottom: 12px;
        margin-top: -10px;
    }
    .toggle-btn-wrapper div[data-testid="stButton"] > button {
        background: #112544 !important;
        color: #D4AF37 !important;
        border: 1px solid #234375 !important;
        border-radius: 10px !important;
        padding: 6px 14px !important;
        font-size: 11px !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        transition: all 0.2s;
    }
    .toggle-btn-wrapper div[data-testid="stButton"] > button:hover {
        border-color: #D4AF37 !important;
        background: #162E54 !important;
    }

    /* Main Window Frame Structural Cleanup */
    iframe {
        border-radius: 16px;
        border: 2px solid #1E3A63 !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.6);
        background-color: #FFFFFF;
    }
    .main .block-container {
        padding: 1.5rem 2rem !important;
        max-width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Balanced Dictionary Configurations Mapping ---
POI_CONFIG = {
    "COMMERCIAL LAYER": [['Corporate Office', '"building"~"office|commercial",i'], ['IT/Tech Center', '"office"~"it|telecommunication",i'], ['Business Center', '"building"="commercial"'], ['Hospital Facility', '"amenity"~"hospital|clinic",i'], ['Hotel Assets', '"tourism"="hotel"']],
    "RETAIL INFRASTRUCTURE": [['Mall/Dept Store', '"shop"~"mall|department_store",i'], ['Supermarket Hub', '"shop"~"supermarket|grocery",i'], ['Convenience Store', '"shop"="convenience"'], ['Commercial Pharmacy', '"amenity"="pharmacy"'], ['Hardware & DIY', '"shop"~"hardware|doityourself",i']],
    "FOOD & BEVERAGE LOGISTICS": [['Standard Restaurant', '"amenity"="restaurant"'], ['Cafe/Coffee Venue', '"amenity"~"cafe|coffee",i'], ['Fast Food Outlet', '"amenity"="fast_food"'], ['Bar & Nightclub', '"amenity"~"bar|pub|nightclub",i']],
    "INDUSTRIAL & LOGISTICS": [['Expressway Access Points', '"highway"~"motorway_junction|toll_gantry",i'], ['Port Terminals', '"industrial"="port"'], ['Manufacturing Plants', '"industrial"~"factory|manufacturing|processing",i'], ['Cold Storage Depots', '"warehouse"~"cold_store|cold_storage",i'], ['Industrial Estates', '"landuse"~"industrial|industrial_estate",i'], ['Warehouses/Depots', '"building"~"warehouse|depot",i']],
    "GOVERNMENTAL ZONES": [['City/Town Hall', '"amenity"="townhall"'], ['Police Precinct', '"amenity"="police"'], ['Fire Station Hub', '"amenity"="fire_station"'], ['Airport Terminals', '"aeroway"~"terminal|aerodrome",i']],
    "EDUCATIONAL CENTERS": [['University Campus', '"amenity"~"university|college",i'], ['K-12 School Facility', '"amenity"="school"']]
}

ADVANCED_CONFIG = {
    "FINANCIAL & ACCESS": [['ATM Terminals', '"amenity"="atm"'], ['Banking Branches', '"amenity"="bank"'], ['Parking Structures', '"amenity"="parking"']],
    "MACRO BOUNDARIES": [['Transit Bus Stops', '"highway"="bus_stop"'], ['City Coordinates', '"place"="city"'], ['Town Coordinates', '"place"="town"']]
}

ICON_MAP = {
    "COMMERCIAL LAYER": "🏢", "RETAIL INFRASTRUCTURE": "🛒", "FOOD & BEVERAGE LOGISTICS": "🍽️", 
    "INDUSTRIAL & LOGISTICS": "🏭", "GOVERNMENTAL ZONES": "🏛️", "EDUCATIONAL CENTERS": "🎓"
}

# --- Sidebar Controls Dashboard View ---
st.sidebar.markdown("<div style='text-align: center; margin-bottom: 20px;'><h2 style='color: #FFFFFF; font-weight: 900; letter-spacing: 2px;'>MARKET STUDY</h2></div>", unsafe_allow_html=True)

# Navigation block acts as high-end choice panels
app_mode = st.sidebar.radio("Module Selection", ["Trade Area Scan", "UMap Integration", "Demographics Hub"], label_visibility="collapsed")
st.sidebar.markdown("<br>", unsafe_allow_html=True)

if app_mode == "Trade Area Scan":
    st.sidebar.markdown("<div style='padding: 0 5px;'>", unsafe_allow_html=True)
    
    # Coordinate Configuration Matrix
    col_latlon, col_rad = st.sidebar.columns([1.8, 1])
    with col_latlon:
        coords_input = st.text_input("Coordinates", value="14.6465, 121.0371")
    with col_rad:
        radius_input = st.number_input("Radius (M)", value=1000, step=100)

    try:
        lat, lon = map(float, coords_input.split(","))
    except ValueError:
        st.sidebar.error("Syntax Error: Use Lat, Lon")
        st.stop()

    # Search Bar Normalization Block
    search_term = st.sidebar.text_input("Search", "").lower()
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    selected_queries = []

    # Map Layer Generators
    for cat, items in POI_CONFIG.items():
        filtered_items = [i for i in items if search_term in i[0].lower()]
        if filtered_items:
            category_icon = ICON_MAP.get(cat, "📁")
            with st.sidebar.expander(f"{category_icon} {cat}", expanded=bool(search_term)):
                for label, q_str in filtered_items:
                    if st.checkbox(label, key=f"core_{cat}_{label}"):
                        selected_queries.append(q_str)

    with st.sidebar.expander("⚙️ ADVANCED ATTRIBUTES", expanded=bool(search_term)):
        for cat, items in ADVANCED_CONFIG.items():
            filtered_items = [i for i in items if search_term in i[0].lower()]
            if filtered_items:
                st.markdown(f"<div style='font-size:11px; font-weight:bold; color:#D4AF37; margin: 4px 0;'>{cat}</div>", unsafe_allow_html=True)
                for label, q_str in filtered_items:
                    if st.checkbox(label, key=f"adv_{cat}_{label}"):
                        selected_queries.append(q_str)

    # Protection Spacing for Fixed Footer
    st.sidebar.markdown("<div style='height: 120px;'></div></div>", unsafe_allow_html=True)

    # Fixed Sidebar Action Control Base
    with st.sidebar.container():
        st.markdown("<div class='scan-btn-container'>", unsafe_allow_html=True)
        scan_triggered = st.button("Scan Area")
        st.markdown("</div>", unsafe_allow_html=True)

    if scan_triggered:
        if not selected_queries:
            st.sidebar.warning("Select target parameters.")
        else:
            clauses = "\n".join([f"  nwr[{q}](around:{radius_input},{lat},{lon});" for q in selected_queries])
            overpass_ql = f"[out:json][timeout:120];\n(\n{clauses}\n);\nout center;"
            encoded_query = urllib.parse.quote(overpass_ql)
            st.session_state.target_url = f"https://overpass-turbo.eu/?Q={encoded_query}&R"

    # --- Main Screen Workspace Matrix ---
    st.markdown("<div class='toggle-btn-wrapper'>", unsafe_allow_html=True)
    if st.button("⛶ Fullscreen" if not st.session_state.map_fullscreen else "🗗 Original Size", on_click=toggle_workspace_dimension):
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
        
    workspace_height = 980 if st.session_state.map_fullscreen else 680
    st.components.v1.iframe(st.session_state.target_url, height=workspace_height, scrolling=False)

elif app_mode == "UMap Integration":
    st.components.v1.iframe("https://umap.openstreetmap.fr/en/", height=850, scrolling=False)

elif app_mode == "Demographics Hub":
    st.markdown("<div style='padding: 60px; text-align: center;'><h2 style='color: #D4AF37; font-weight: 900; letter-spacing:1px;'>POPULATION INSIGHTS</h2><br><p style='color:#FFFFFF; font-size:14px;'>🚧 Spatial demographics models are initializing. Access parameters provisioning shortly.</p></div>", unsafe_allow_html=True)
