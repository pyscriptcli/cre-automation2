import streamlit as st
import requests
import re
import json
import os
import math
import time
from datetime import datetime

# --- PROGRAMMATIC LIGHT MODE LOCK ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\n")

# -----------------------------------------------------------------------------
# For Maintenance                     
# Ensure the snippet ends exactly with the unsafe_allow_html parameter
st.markdown("""
<div id="maintenance-overlay" style="
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 51, 102, 0.8);
    backdrop-filter: blur(5px);
    z-index: 9999999;
    display: flex;
    justify-content: center;
    align-items: center;
    font-family: 'Montserrat', sans-serif;
">
    <div style="
        background: #ffffff;
        padding: 35px 40px;
        border-radius: 8px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        border-top: 5px solid #C9AB4C;
        text-align: center;
        max-width: 450px;
        width: 90%;
        position: relative;
    ">
        <button onclick="closeMaintenanceOverlay()" style="
            position: absolute;
            top: 12px;
            right: 15px;
            background: none;
            border: none;
            font-size: 20px;
            font-weight: bold;
            color: #888780;
            cursor: pointer;
        ">×</button>
        
        <div style="font-size: 40px; margin-bottom: 15px;">🛠️</div>
        <h3 style="margin: 0 0 10px 0; color: #003366; font-size: 16px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">
            Under Maintenance
        </h3>
        <p style="margin: 0 0 20px 0; color: #555555; font-size: 12px; line-height: 1.6;">
            Sorry for the inconvenience! This web app is currently under development and maintenance. You may dismiss this notice to continue testing.
        </p>
        
        <button onclick="closeMaintenanceOverlay()" style="
            background: #003366;
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 10px 20px;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            cursor: pointer;
            width: 100%;
        ">
            Proceed to Application
        </button>
    </div>
</div>

<script>
    const parentDoc = window.parent.document;

    if (window.parent.sessionStorage.getItem('maintenance_dismissed') === 'true') {
        const overlay = parentDoc.getElementById('maintenance-overlay') || document.getElementById('maintenance-overlay');
        if (overlay) overlay.style.display = 'none';
    }

    function closeMaintenanceOverlay() {
        const localOverlay = document.getElementById('maintenance-overlay');
        const parentOverlay = parentDoc.getElementById('maintenance-overlay');
        
        if (localOverlay) localOverlay.style.display = 'none';
        if (parentOverlay) parentOverlay.style.display = 'none';
        
        window.parent.sessionStorage.setItem('maintenance_dismissed', 'true');
    }
</script>
""", unsafe_allow_html=True)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# 1. BRANDED THEME & STRUCTURAL FULL OVERRIDES
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Open Node",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Montserrat:wght@400;500;600;700;800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20,400,0,0');

        :root {
            --brand-midnight: #003366 !important;
            --brand-gold: #C9AB4C !important;
            --white-clean: #ffffff !important;
            --bg-offwhite: #f8fafc !important;
            --text-muted: #888780 !important;
            --soft-shadow: 0 4px 12px rgba(0, 51, 102, 0.08) !important;
        }
        
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
            background-color: var(--white-clean) !important;
            color: var(--brand-midnight) !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: var(--bg-offwhite) !important;
            color: var(--brand-midnight) !important;
            border-right: 1px solid rgba(0, 51, 102, 0.08) !important;
            width: 280px !important;
            min-width: 280px !important;
            max-width: 280px !important;
            transform: none !important;
            visibility: visible !important;
            overflow: hidden !important;
            box-shadow: 2px 0 15px rgba(0,0,0,0.03) !important;
        }
        
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] { display: none !important; }
        ::-webkit-scrollbar { width: 0px !important; background: transparent !important; }
        * { scrollbar-width: none !important; -ms-overflow-style: none !important; }
        
        p, label, h1, h2, h3, h4, h5, h6, .stMarkdown, [data-testid="stExpander"] summary p {
            color: var(--brand-midnight) !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        
        [data-testid="stHeader"], header, #stDecoration { display: none !important; }
        
        [data-testid="stAppViewContainer"] { display: flex !important; flex-direction: row !important; width: 100vw !important; height: 100vh !important; overflow: hidden !important; }
        [data-testid="stMain"] { flex-grow: 1 !important; width: calc(100vw - 280px) !important; height: 100vh !important; overflow: hidden !important; margin: 0px !important; padding: 0px !important; }
        .block-container, [data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"], .stElementContainer { padding: 0px !important; margin: 0px !important; max-width: 100% !important; gap: 0rem !important; }
        iframe { height: 100vh !important; width: 100% !important; border: none !important; display: block !important; }
        
        div[data-baseweb="input"], div[data-baseweb="select"] { background-color: transparent !important; border: none !important; border-bottom: 1px solid rgba(201, 171, 76, 0.5) !important; border-radius: 0px !important; box-shadow: none !important; }
        
        div.stButton > button[kind="secondary"], [data-testid="stPopover"] > button { background-color: var(--brand-midnight) !important; border: 1px solid var(--brand-midnight) !important; border-radius: 2px !important; width: 100% !important; padding: 4px !important; box-shadow: var(--soft-shadow) !important; }
        div.stButton > button[kind="secondary"]:hover, [data-testid="stPopover"] > button:hover { background-color: var(--brand-gold) !important; border-color: var(--brand-gold) !important; }
        div.stButton > button[kind="secondary"] p, [data-testid="stPopover"] > button p, [data-testid="stPopover"] > button div, div.stDownloadButton > button p { color: var(--white-clean) !important; font-weight: 700 !important; font-size: 9px !important; text-transform: uppercase !important; letter-spacing: 1px; }
        
        div.stDownloadButton > button { background-color: var(--brand-midnight) !important; border: none !important; border-radius: 2px !important; width: 100% !important; padding: 4px !important; }
        div.stDownloadButton > button:hover { background-color: var(--brand-gold) !important; }
        
        div.stButton > button[kind="primary"] { background: transparent !important; border: none !important; color: var(--text-muted) !important; padding: 0 !important; margin-top: 2px; }
        div.stButton > button[kind="primary"] p { color: var(--text-muted) !important; font-size: 9px !important; font-weight: 600; text-transform: uppercase; }
        
        [data-testid="stSidebar"] .st-expander { border: 1px solid rgba(0, 51, 102, 0.05) !important; background-color: var(--white-clean) !important; border-radius: 2px !important; margin-bottom: 2px !important; }
        
        .stCheckbox { display: flex !important; align-items: center !important; margin-bottom: 2px !important; }
        .stCheckbox label { display: inline-flex !important; align-items: center !important; gap: 6px !important; margin: 0px !important; padding: 0px !important; }
        .stCheckbox label p { font-size: 10px !important; font-weight: 500 !important; color: var(--brand-midnight) !important; display: inline-block !important; margin: 0 !important; line-height: 1.2 !important; }
        div[data-baseweb="checkbox"] { align-self: center !important; }
        
        div[data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"] {
            background-color: #003366 !important;
            border-color: #003366 !important;
        }
        div[data-baseweb="checkbox"] input:checked + div, 
        div[data-baseweb="checkbox"] div[aria-checked="true"],
        div[data-baseweb="checkbox"] [role="checkbox"][aria-checked="true"] > div { 
            background-color: #003366 !important; 
            border-color: #003366 !important; 
        }
        
        .brand-title { font-family: 'Cormorant Garamond', serif !important; font-style: italic; color: var(--brand-midnight); font-size: 30px; text-align: center; border-bottom: 1px solid var(--brand-gold); padding-bottom: 6px; margin-bottom: 10px; }
        .stTextInput label p, .stNumberInput label p { font-size: 9px !important; font-weight: 500 !important; color: var(--text-muted) !important; }
        
        /* Clear All hyperlink style */
        .clear-all-hyperlink button {
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            margin: 0 !important;
            color: #888780 !important;
            font-size: 10px !important;
            font-weight: 500 !important;
            text-decoration: underline !important;
            text-underline-offset: 3px !important;
            cursor: pointer !important;
            box-shadow: none !important;
        }
        .clear-all-hyperlink button:hover {
            color: #003366 !important;
            background: transparent !important;
        }
        .clear-all-hyperlink button p {
            color: inherit !important;
            font-size: 10px !important;
        }
        
        /* Loading overlay styles */
        .custom-loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.65);
            backdrop-filter: blur(2px);
            z-index: 999999;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Montserrat', sans-serif;
        }
        
        .loading-card {
            background: white;
            padding: 32px 48px;
            border-radius: 16px;
            min-width: 380px;
            text-align: center;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(0, 51, 102, 0.2);
            animation: fadeIn 0.3s ease;
        }
        
        .spinner {
            width: 52px;
            height: 52px;
            border: 4px solid #e0e0e0;
            border-top-color: #003366;
            border-radius: 50%;
            margin: 0 auto 20px auto;
            animation: spin 0.8s linear infinite;
        }
        
        .loading-title {
            font-size: 15px;
            font-weight: 800;
            color: #003366;
            text-transform: uppercase;
            letter-spacing: 2.5px;
            margin-bottom: 18px;
        }
        
        .source-box {
            background: #f0f2f6;
            padding: 12px 16px;
            border-radius: 12px;
            margin-bottom: 18px;
        }
        
        .source-icon {
            font-size: 28px;
            margin-bottom: 6px;
        }
        
        .source-message {
            font-size: 11px;
            font-weight: 600;
            color: #003366;
        }
        
        .step-text {
            font-size: 10px;
            color: #666;
            margin-bottom: 16px;
            font-family: 'Courier New', monospace;
        }
        
        .progress-container {
            width: 100%;
            height: 5px;
            background: #e8e8e8;
            border-radius: 5px;
            overflow: hidden;
            margin-bottom: 10px;
        }
        
        .progress-bar {
            width: 0%;
            height: 100%;
            background: #003366;
            transition: width 0.3s ease;
            border-radius: 5px;
        }
        
        .progress-text {
            font-size: 10px;
            color: #999;
            font-weight: 500;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: scale(0.95); }
            to { opacity: 1; transform: scale(1); }
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# API LOGGING SYSTEM
# -----------------------------------------------------------------------------
if 'api_logs' not in st.session_state:
    st.session_state.api_logs = []

def add_api_log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.api_logs.append({
        "time": timestamp,
        "message": message,
        "level": level
    })
    if len(st.session_state.api_logs) > 100:
        st.session_state.api_logs = st.session_state.api_logs[-100:]

def clear_api_logs():
    st.session_state.api_logs = []

# -----------------------------------------------------------------------------
# 2. STATE PERSISTENCE & DATA CONFIGURATIONS
# -----------------------------------------------------------------------------
DEFAULT_COORDS = "14.5995, 120.9842"
DEFAULT_RADIUS = 1000

# Loading screen state variables
if 'loading_source' not in st.session_state:
    st.session_state.loading_source = ""
if 'loading_step' not in st.session_state:
    st.session_state.loading_step = 0
if 'loading_progress' not in st.session_state:
    st.session_state.loading_progress = 0
if 'loading_message' not in st.session_state:
    st.session_state.loading_message = "Initializing..."

if 'geo_coords' not in st.session_state: st.session_state.geo_coords = DEFAULT_COORDS
if 'geo_radius' not in st.session_state: st.session_state.geo_radius = DEFAULT_RADIUS
if 'scanned_records' not in st.session_state: st.session_state.scanned_records = []
if 'last_scan_lat' not in st.session_state: st.session_state.last_scan_lat = 14.5995
if 'last_scan_lon' not in st.session_state: st.session_state.last_scan_lon = 120.9842
if 'layer_meta' not in st.session_state: st.session_state.layer_meta = {}
if 'layer_groups' not in st.session_state: st.session_state.layer_groups = {}
if 'scan_active_loading' not in st.session_state: st.session_state.scan_active_loading = False

if 'target_config' not in st.session_state:
    st.session_state.target_config = {"size": 24, "color": "#003366", "style": "star"}

if 'radius_config' not in st.session_state:
    st.session_state.radius_config = {"color": "#003366", "fill_opacity": 0.08, "weight": 1.5}

if 'global_marker_style' not in st.session_state: st.session_state.global_marker_style = "modern-pin"
if 'global_marker_size' not in st.session_state: st.session_state.global_marker_size = 20
if 'global_marker_color' not in st.session_state: st.session_state.global_marker_color = "#003366"

POI_CONFIG = {
    "FOOD & BEVERAGES": [
        ("Restaurants & Dining", "amenity=restaurant"),
        ("Fast Food", "amenity=fast_food"),
        ("Cafes & Coffee Shops", "amenity=cafe"),
        ("Bakeries & Panaderia", "shop=bakery"),
        ("Food Courts", "amenity=food_court"),
        ("Bars & Pubs", "amenity=bar"),
    ],
    
    "RETAIL & SHOPPING": [
        ("Malls", "shop=mall"),
        ("Supermarkets & Groceries", "shop=supermarket|grocery"),
        ("Convenience Stores", "shop=convenience"),
        ("Pharmacies & Drugstores", "amenity=pharmacy"),
        ("Public Markets / Palengke", "amenity=marketplace"),
        ("Hardware Stores", "shop=hardware"),
        ("Department Stores", "shop=department_store"),
        ("Bookstores", "shop=books"),
        ("Clothing & Apparel Stores", "shop=clothes"),
        ("Electronics Stores", "shop=electronics"),
        ("Mobile Phone Stores", "shop=mobile_phone"),
        ("Pawnshops", "shop=pawnbroker"),
    ],
    
    "HEALTH & EMERGENCY": [
        ("Hospitals", "amenity=hospital"),
        ("Clinics & Health Centers", "amenity=clinic"),
        ("Police Stations", "amenity=police"),
        ("Fire Stations", "amenity=fire_station"),
    ],
    
    "GOVERNMENT & PUBLIC SERVICES": [
        ("City / Municipal Halls", "amenity=townhall"),
        ("Barangay Halls", "amenity=townhall"),
        ("Post Offices", "amenity=post_office"),
        ("Public Libraries", "amenity=library"),
        ("Government Offices (General)", "office=government"),
        ("Courts / Hall of Justice", "amenity=courthouse"),
    ],
    
    "EDUCATION": [
        ("Universities", "amenity=university"),
        ("Colleges", "amenity=college"),
        ("Schools (High School & Elementary)", "amenity=school"),
        ("Kindergarten & Daycares", "amenity=kindergarten"),
    ],
    
    "RELIGIOUS SITES": [
        ("Churches, Chapels & Religious Establishments", "building~church|cathedral|chapel|religious|mosque|temple"),
    ],
    
    "TRANSPORTATION": [
        ("Bus Stops & Terminals", "highway=bus_stop"),
        ("Jeepney & Tricycle Terminals", "amenity=taxi"),
        ("Train Stations (PNR, LRT, MRT)", "railway=station"),
        ("Ferry Terminals & Piers", "amenity=ferry_terminal"),
        ("Airports", "aeroway=aerodrome"),
        ("Gas Stations", "amenity=fuel"),
        ("Parking Lots", "amenity=parking"),
    ],
    
    "FINANCIAL SERVICES": [
        ("ATMs", "amenity=atm"),
        ("Banks", "amenity=bank"),
        ("Money Remittance Centers", "amenity=money_transfer"),
    ],
    
    "TELECOM & UTILITIES": [
        ("Mobile Phone Stores (Globe, Smart, DITO)", "shop=mobile_phone"),
        ("Internet Cafes / Computer Shops", "amenity=internet_cafe"),
        ("Water Refilling Stations", "amenity=water_point"),
        ("Courier & Shipping Services", "office=courier"),
    ],
    
    "OFFICE": [
        ("Offices", "office~'.*'"),
    ],
    
    "PARKS & RECREATION": [
        ("Parks & Plazas", "leisure=park"),
        ("Playgrounds", "leisure=playground"),
        ("Sports Centers & Gyms", "leisure=sports_centre"),
        ("Basketball Courts", "sport=basketball"),
        ("Stadiums & Arenas", "leisure=stadium"),
        ("Cinemas & Theaters", "amenity=cinema"),
        ("Museums", "tourism=museum"),
    ],
    
    "SERVICES & REPAIRS": [
        ("Car Repair & Vulcanizing Shops", "shop=car_repair"),
        ("Car Washes", "amenity=car_wash"),
        ("Tailors & Dress Shops", "shop=tailor"),
        ("Electronics & Phone Repair", "shop=electronics_repair"),
        ("Printing & Photocopy Shops", "shop=printing"),
    ],
    
    "ACCOMMODATION": [
        ("Hotels", "tourism=hotel"),
        ("Resorts", "tourism=resort"),
        ("Motels & Inns", "tourism=motel"),
        ("Hostels & Backpackers", "tourism=hostel"),
    ],
}

ADVANCED_CONFIG = {}

# Clear all POIs function (clears both data and selections)
def clear_all_pois():
    """Clear all POI data and unselect all checkboxes"""
    st.session_state.scanned_records = []
    st.session_state.layer_meta = {}
    st.session_state.layer_groups = {}
    st.session_state.scan_active_loading = False
    # Unselect all POI category checkboxes
    for key in list(st.session_state.keys()):
        if key.startswith("chk_"):
            st.session_state[key] = False
    add_api_log("All POIs cleared and selections reset", "INFO")

def compile_features_kml(features):
    kml = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scanned POIs</name>'
    for f in features:
        if not f.get('visible', True): continue
        name = f.get('name', 'Asset').replace("&", "&").replace("<", "<").replace(">", ">")
        class_type = f.get('type', 'Node').replace("&", "&").replace("<", "<").replace(">", ">")
        kml += f"<Placemark><name>{name}</name><description>{class_type}</description><Point><coordinates>{f['lon']},{f['lat']},0</coordinates></Point></Placemark>"
    return kml + '</Document></kml>'

# -----------------------------------------------------------------------------
# LOADING SCREEN FUNCTION
# -----------------------------------------------------------------------------
def show_loading_overlay():
    """Display loading overlay with current status"""
    source = st.session_state.get('loading_source', 'starting')
    progress = st.session_state.get('loading_progress', 0)
    message = st.session_state.get('loading_message', 'Initializing...')
    
    source_display = {
        "starting": ("", "Initializing..."),
        "detecting": ("", "Detecting region (Luzon/Visayas/Mindanao)..."),
        "github_primary": ("", "Luzon detected - Using GitHub pre-processed data..."),
        "overpass_primary": ("", "Visayas/Mindanao detected - Using Overpass live API..."),
        "github": ("", "Loading from GitHub pre-processed data..."),
        "overpass": ("", "Loading from Overpass live API..."),
        "complete": ("", "Complete! Rendering map..."),
    }
    
    icon, source_message = source_display.get(source, ("⏳", "Loading..."))
    
    loading_html = f"""
    <div class="custom-loading-overlay" id="loadingOverlay">
        <div class="loading-card">
            <div class="spinner"></div>
            <div class="loading-title">SCANNING AREA</div>
            <div class="source-box">
                <div class="source-icon">{icon}</div>
                <div class="source-message">{source_message}</div>
            </div>
            <div class="step-text">{message}</div>
            <div class="progress-container">
                <div class="progress-bar" style="width: {progress}%;"></div>
            </div>
            <div class="progress-text">{progress}% complete</div>
        </div>
    </div>
    """
    
    return loading_html

# -----------------------------------------------------------------------------
# HYBRID ENGINE ARCHITECTURE
# -----------------------------------------------------------------------------
GITHUB_POI_BASE = "https://raw.githubusercontent.com/pyscriptcli/osm-repository/main/data/provinces"

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

PROVINCE_BOUNDS = {
    "metro_manila": [120.90, 14.40, 121.10, 14.80],
    "cavite": [120.60, 14.10, 121.00, 14.50],
    "laguna": [121.00, 14.00, 121.60, 14.50],
    "bulacan": [120.70, 14.70, 121.20, 15.30],
    "batangas": [120.70, 13.60, 121.40, 14.20],
    "rizal": [121.00, 14.40, 121.60, 14.90],
    "pampanga": [120.50, 14.90, 121.00, 15.40],
    "nueva_ecija": [120.60, 15.20, 121.50, 16.00],
    "zambales": [119.80, 14.60, 120.60, 15.80],
    "tarlac": [120.30, 15.30, 121.00, 15.90],
    "pangasinan": [119.80, 15.60, 121.00, 16.50],
    "la_union": [120.20, 16.40, 120.80, 17.00],
    "ilocos_norte": [120.30, 17.80, 121.00, 18.70],
    "ilocos_sur": [120.20, 16.90, 120.80, 17.80],
    "cebu": [123.00, 9.40, 124.20, 11.20],
    "leyte": [124.30, 9.80, 125.60, 11.50],
    "bohol": [123.70, 9.50, 124.60, 10.10],
    "negros_oriental": [122.80, 9.00, 123.50, 10.50],
    "negros_occidental": [122.30, 9.30, 123.40, 11.00],
    "samar": [124.80, 11.00, 125.80, 12.50],
    "biliran": [124.30, 11.40, 124.60, 11.70],
    "siquijor": [123.40, 9.10, 123.70, 9.30],
    "davao_city": [125.40, 6.90, 125.70, 7.40],
    "davao_del_sur": [125.00, 6.00, 125.80, 7.00],
    "davao_oriental": [126.00, 6.50, 126.80, 7.80],
    "north_cotabato": [124.50, 6.80, 125.30, 7.80],
    "south_cotabato": [124.50, 5.80, 125.30, 6.80],
    "sultan_kudarat": [123.80, 6.20, 124.80, 7.20],
    "zamboanga_del_sur": [122.00, 7.00, 123.80, 8.20],
    "zamboanga_del_norte": [121.80, 7.50, 123.00, 8.80],
    "misamis_oriental": [124.00, 8.00, 125.20, 9.30],
    "misamis_occidental": [123.30, 7.80, 124.00, 8.70],
    "bukidnon": [124.30, 7.00, 125.50, 8.50],
    "agusan_del_norte": [125.00, 8.20, 126.00, 9.30],
    "agusan_del_sur": [125.00, 7.60, 126.20, 8.80],
    "surigao_del_norte": [125.20, 9.30, 126.30, 10.20],
    "surigao_del_sur": [125.80, 8.00, 126.50, 9.00],
    "lanao_del_norte": [123.50, 7.50, 124.50, 8.30],
    "lanao_del_sur": [123.80, 7.00, 124.80, 8.20],
    "basilan": [121.80, 6.30, 122.50, 6.80],
    "sulu": [120.80, 5.50, 121.50, 6.30],
    "tawi_tawi": [119.50, 4.50, 120.50, 5.50],
    "dinagat_islands": [125.30, 9.80, 125.80, 10.50],
    "zamboanga": [121.80, 6.80, 123.80, 8.50],
}

def get_province_from_coords(lat, lon):
    for province, bbox in PROVINCE_BOUNDS.items():
        if bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]:
            return province
    return None

@st.cache_data(ttl=86400, show_spinner=False)
def load_province_pois(province_name):
    url = f"{GITHUB_POI_BASE}/{province_name}.json"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

def filter_pois_by_radius(pois, center_lat, center_lon, radius_meters):
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    
    filtered = []
    for poi in pois:
        dist = haversine(center_lat, center_lon, poi['lat'], poi['lon'])
        if dist <= radius_meters:
            poi_copy = poi.copy()
            poi_copy['distance_m'] = round(dist)
            filtered.append(poi_copy)
    return filtered

def filter_pois_by_tags(pois, selected_tags):
    if not selected_tags:
        return pois
    filtered = []
    
    # Compile a flat set of valid individual sub-tags from pipe-delimited values
    valid_targets = []
    for tag in selected_tags:
        valid_targets.extend(tag.replace('"', '').lower().split('|'))

    for poi in pois:
        poi_type = poi.get('type', '').lower()
        
        for target in valid_targets:
            if '=' in target:
                # Splitting shop=mall into ['shop', 'mall']
                tgt_key, tgt_val = target.split('=', 1)
                # If the key or value perfectly matches the point type, pass it
                if poi_type == tgt_val or poi_type == tgt_key:
                    filtered.append(poi)
                    break
            else:
                if target == poi_type:
                    filtered.append(poi)
                    break
    return filtered

def build_ql(lat, lon, radius, tags):
    statements = "\n".join([f"  nwr[{tag}](around:{radius},{lat},{lon});" for tag in tags])
    return f"[out:json][timeout:90];(\n{statements}\n);out center;"

def query_overpass_robust(ql, max_retries=2, timeout=90):
    for endpoint in OVERPASS_ENDPOINTS:
        for attempt in range(max_retries):
            try:
                res = requests.post(endpoint, data={"data": ql}, headers={"User-Agent": "OpenNode/3.5"}, timeout=timeout)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("elements", [])
                elif res.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    break
            except Exception:
                continue
    return []

def adaptive_radius_query(lat, lon, radius, tags, max_chunk=2000):
    if radius <= max_chunk:
        return query_overpass_robust(build_ql(lat, lon, radius, tags))
    offset = radius / (2 * math.sqrt(2) * 111320)
    quadrants = [(lat + offset, lon + offset), (lat + offset, lon - offset), (lat - offset, lon + offset), (lat - offset, lon - offset)]
    all_results, seen_ids = [], set()
    for q_lat, q_lon in quadrants:
        chunk_results = query_overpass_robust(build_ql(q_lat, q_lon, radius // 2, tags))
        for el in chunk_results:
            if el.get("id") not in seen_ids:
                seen_ids.add(el["id"])
                all_results.append(el)
    return all_results

def load_pois_smart_hybrid(province_name, lat_coord, lon_coord, radius_val, selected_tags):
    records = []
    seen_locations = {}
    
    def add_poi(poi, source_priority):
        lat_key = round(poi['lat'] * 1000) / 1000
        lon_key = round(poi['lon'] * 1000) / 1000
        key = (lat_key, lon_key)
        
        if key not in seen_locations:
            seen_locations[key] = source_priority
            records.append(poi)
        else:
            existing_priority = seen_locations[key]
            if source_priority > existing_priority:
                for i, r in enumerate(records):
                    if abs(r['lat'] - poi['lat']) < 0.001 and abs(r['lon'] - poi['lon']) < 0.001:
                        records[i] = poi
                        break
                seen_locations[key] = source_priority
    
    luzon_provinces = [
        "metro_manila", "cavite", "laguna", "bulacan", "batangas", "rizal",
        "pampanga", "nueva_ecija", "zambales", "tarlac", "pangasinan",
        "la_union", "ilocos_norte", "ilocos_sur"
    ]
    
    is_luzon = province_name in luzon_provinces if province_name else False
    github_priority = 2 if is_luzon else 1
    overpass_priority = 1 if is_luzon else 2
    
    if is_luzon:
        st.session_state.loading_source = "github_primary"
        add_api_log(f"Smart hybrid: Luzon detected - using GitHub as primary", "INFO")
    else:
        st.session_state.loading_source = "overpass_primary"
        add_api_log(f"Smart hybrid: Visayas/Mindanao detected - using Overpass as primary", "INFO")
    
    st.session_state.loading_progress = 20
    st.session_state.loading_message = "Analyzing coordinates..."
    
    add_api_log(f"Smart hybrid: {'Luzon' if is_luzon else 'Visayas/Mindanao'}", "INFO")
    add_api_log(f"Priority: GitHub={github_priority}, Overpass={overpass_priority}", "INFO")
    
    if province_name:
        st.session_state.loading_source = "github"
        st.session_state.loading_progress = 40
        st.session_state.loading_message = "Fetching from GitHub repository..."
        
        all_province_pois = load_province_pois(province_name)
        if all_province_pois:
            radius_filtered = filter_pois_by_radius(all_province_pois, lat_coord, lon_coord, radius_val)
            tag_filtered = filter_pois_by_tags(radius_filtered, selected_tags)
            for poi in tag_filtered:
                add_poi({
                    "lat": poi['lat'],
                    "lon": poi['lon'],
                    "name": poi.get('name', 'Unknown'),
                    "type": poi.get('type', 'poi'),
                    "source": "github",
                    "visible": True,
                }, github_priority)
            add_api_log(f"GitHub loaded {len(tag_filtered)} POIs", "INFO")
        else:
            add_api_log(f"No GitHub data for {province_name}", "WARNING")
    
    st.session_state.loading_source = "overpass"
    st.session_state.loading_progress = 70
    st.session_state.loading_message = "Querying Overpass API..."
    
    add_api_log(f"Overpass query for {lat_coord}, {lon_coord}", "INFO")
    elements = adaptive_radius_query(lat_coord, lon_coord, radius_val, selected_tags)
    
    overpass_count = 0
    for el in elements:
        e_lat = el.get('lat') or el.get('center', {}).get('lat')
        e_lon = el.get('lon') or el.get('center', {}).get('lon')
        if e_lat and e_lon:
            tags = el.get('tags', {})
            name = tags.get('name', 'Unknown')
            if not name or str(name).strip().lower() in ['unknown', '', 'nan', 'none']:
                continue
            poi_type = tags.get('amenity') or tags.get('shop') or tags.get('tourism') or tags.get('building') or 'poi'
            add_poi({
                "lat": e_lat,
                "lon": e_lon,
                "name": name,
                "type": poi_type,
                "source": "overpass",
                "visible": True,
            }, overpass_priority)
            overpass_count += 1
    
    add_api_log(f"Overpass loaded {overpass_count} POIs", "INFO")
    
    st.session_state.loading_progress = 90
    st.session_state.loading_message = "Processing results..."
    
    for idx, record in enumerate(records):
        record['uid'] = idx
    
    github_final = sum(1 for r in records if r['source'] == 'github')
    overpass_final = sum(1 for r in records if r['source'] == 'overpass')
    add_api_log(f"FINAL: {len(records)} unique POIs (GitHub: {github_final}, Overpass: {overpass_final})", "INFO")
    
    st.session_state.loading_source = "complete"
    st.session_state.loading_progress = 100
    st.session_state.loading_message = "Complete!"
    
    if len(records) < 20 and selected_tags:
        add_api_log(f"Low POI count ({len(records)}) found for specific tags.", "INFO")
        return records

# -----------------------------------------------------------------------------
# 3. SIDEBAR CONTROLS & GEOPROCESSING
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="brand-title">Open Node</div>', unsafe_allow_html=True)
    
    selected_tags = []
    scan_triggered = st.button("SCAN AREA", type="secondary", use_container_width=True, key="scan_btn")
    
    location_input = st.text_input("COORDINATES", value=st.session_state.geo_coords, key="geo_coords_input")
    radius_val = st.number_input("RADIUS (METERS)", min_value=100, max_value=50000, value=st.session_state.geo_radius, key="geo_radius_input", step=100)
    st.session_state.geo_radius = radius_val

    coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", location_input)
    if coord_match:
        lat_coord, lon_coord = float(coord_match.group(1)), float(coord_match.group(2))
        st.session_state.geo_coords = location_input
    else:
        fallback_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", st.session_state.geo_coords)
        lat_coord, lon_coord = (float(fallback_match.group(1)), float(fallback_match.group(2))) if fallback_match else (14.5995, 120.9842)

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    search_query = st.text_input("SEARCH TAGS", placeholder="Search parameters...").lower()
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    
    # Clear All hyperlink button
    st.markdown('<div class="clear-all-hyperlink">', unsafe_allow_html=True)
    if st.button("Clear All Selections", key="clear_all_btn", use_container_width=True):
        clear_all_pois()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    
    for cat_name, node_items in POI_CONFIG.items():
        matched = [item for item in node_items if search_query in item[0].lower()]
        if matched:
            with st.expander(cat_name, expanded=(len(search_query) > 0)):
                for label, tag in matched:
                    if st.checkbox(label, key=f"chk_{cat_name}_{label}"):
                        selected_tags.append(tag)

    st.markdown("<div style='font-weight: 700; font-size: 11px; margin-top: 15px; margin-bottom: 8px; color: #003366; letter-spacing: 1px;'>ADVANCED POIs</div>", unsafe_allow_html=True)
    with st.container():
        for cat_name, node_items in ADVANCED_CONFIG.items():
            matched = [item for item in node_items if search_query in item[0].lower()]
            if matched:
                with st.expander(cat_name, expanded=(len(search_query) > 0)):
                    for label, tag in matched:
                        if st.checkbox(label, key=f"chk_adv_{cat_name}_{label}"):
                            selected_tags.append(tag)

    if scan_triggered:
        if not selected_tags:
            st.error("Select ≥ 1 layer.")
        else:
            st.session_state.scan_active_loading = True
            st.rerun()

# -----------------------------------------------------------------------------
# PIPELINE EXECUTION FORWARD CONTROL (WITH LOADING OVERLAY)
# -----------------------------------------------------------------------------

# Show loading screen while scanning
if st.session_state.scan_active_loading:
    # Display the loading overlay
    st.markdown(show_loading_overlay(), unsafe_allow_html=True)
    
    # Reset loading state
    st.session_state.loading_source = "detecting"
    st.session_state.loading_progress = 0
    st.session_state.loading_message = "Initializing..."
    
    province_name = get_province_from_coords(lat_coord, lon_coord)
    
    # Set source based on region
    luzon_provinces_list = ["metro_manila", "cavite", "laguna", "bulacan", "batangas", "rizal", 
                            "pampanga", "nueva_ecija", "zambales", "tarlac", "pangasinan", 
                            "la_union", "ilocos_norte", "ilocos_sur"]
    is_luzon = province_name in luzon_provinces_list if province_name else False
    
    if is_luzon:
        st.session_state.loading_source = "github_primary"
        st.session_state.loading_message = "Luzon detected - Loading from GitHub..."
    else:
        st.session_state.loading_source = "overpass_primary"
        st.session_state.loading_message = "Visayas/Mindanao detected - Loading from Overpass..."
    
    st.session_state.loading_progress = 25
    
    # Load data
    if is_luzon:
        st.session_state.loading_source = "github"
    else:
        st.session_state.loading_source = "overpass"
    
    st.session_state.loading_progress = 40
    st.session_state.loading_message = "Fetching POI data..."
    
    records = load_pois_smart_hybrid(province_name, lat_coord, lon_coord, radius_val, selected_tags)
    
    st.session_state.loading_progress = 85
    st.session_state.loading_message = "Processing results..."
    
    if records:
        st.session_state.scanned_records = records
        st.session_state.last_scan_lat = lat_coord
        st.session_state.last_scan_lon = lon_coord
        st.session_state.loading_source = "complete"
        st.session_state.loading_progress = 100
        st.session_state.loading_message = f"Complete! Found {len(records)} POIs"
    else:
        st.session_state.scanned_records = []
        st.session_state.loading_source = "complete"
        st.session_state.loading_progress = 100
        st.session_state.loading_message = "No POIs found in this area"
    
    time.sleep(0.5)
    st.session_state.scan_active_loading = False
    st.rerun()

# --- CONTINUATION OF SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Clear All Data button
    st.markdown('<div class="clear-all-hyperlink" style="margin-top: 8px;">', unsafe_allow_html=True)
    if st.button("Clear All Data", key="clear_data_btn", use_container_width=True):
        clear_all_pois()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    visible_only_records = [p for p in st.session_state.scanned_records if p.get('visible', True)]
    
    with col1: st.download_button("RADIUS", json.dumps(visible_only_records), "scan.json", "application/json", use_container_width=True)
    with col2: st.download_button("MARKERS", compile_features_kml(st.session_state.scanned_records), "POIs.kml", "application/vnd.google-earth.kml+xml", use_container_width=True)

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

    with st.popover("IMPORT FILE", use_container_width=True):
        imported_file = st.file_uploader("Select JSON", type=["json"], label_visibility="collapsed")
        if imported_file is not None:
            if st.button("LOAD", type="secondary", use_container_width=True):
                try:
                    data = json.load(imported_file)
                    st.session_state.scanned_records = data.get("scanned_records", data)
                    st.session_state.geo_coords = data.get("coords", st.session_state.geo_coords)
                    st.session_state.geo_radius = data.get("radius", st.session_state.geo_radius)
                    st.rerun()
                except Exception: st.error("Invalid File")

# -----------------------------------------------------------------------------
# 4. MAP FRAME RENDERING ENGINE
# -----------------------------------------------------------------------------
pts_active = st.session_state.scanned_records
unique_layers = list(set([p.get('type', 'Unclassified') for p in pts_active]))
cat_palette = ["#003366", "#C9AB4C", "#1A5A8A", "#A8862E", "#3D7DA8", "#7A5C10", "#6A94B0", "#D4B85A", "#001F3F", "#E8D494"]

for idx, layer in enumerate(unique_layers):
    if layer not in st.session_state.layer_meta:
        st.session_state.layer_meta[layer] = {
            "color": cat_palette[idx % len(cat_palette)],
            "style": st.session_state.global_marker_style,
            "size": st.session_state.global_marker_size
        }

layer_meta_json = json.dumps(st.session_state.layer_meta)
target_config_json = json.dumps(st.session_state.target_config)
radius_config_json = json.dumps(st.session_state.radius_config)
geojson_str = json.dumps(pts_active)

fallback_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", st.session_state.geo_coords)
render_lat, render_lon = (float(fallback_match.group(1)), float(fallback_match.group(2))) if fallback_match else (14.5995, 120.9842)

is_stale = "true" if (lat_coord != st.session_state.last_scan_lat or lon_coord != st.session_state.last_scan_lon) else "false"

leaflet_template = """
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; background: #ffffff; overflow: hidden; font-family: 'Montserrat', sans-serif; }
        #map-container { position: relative; width: 100%; height: 100vh; }
        #map { height: 100vh; width: 100%; z-index: 1; }

        #scan-results-panel { 
            position: absolute; top: 10px; right: 10px; z-index: 1000; background: #ffffff; width: 310px; 
            max-height: calc(100vh - 40px); border-radius: 4px; border: 1px solid rgba(0, 51, 102, 0.1); 
            background-clip: padding-box; display: flex; flex-direction: column; overflow: hidden; 
            box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); 
        }
        .results-header { background: #003366; color: #ffffff; padding: 10px 12px; font-size: 10px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; border-bottom: 2px solid #C9AB4C; letter-spacing: 1px; }
        .results-list { overflow-y: auto; flex-grow: 1; padding-bottom: 0px; }
        .layer-category-block { border-bottom: 1px solid #f0f0f0; }
        .layer-category-header { background: #ffffff; padding: 6px 10px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; user-select: none; }
        .layer-header-left { display: flex; align-items: center; gap: 6px; font-size: 9px; font-weight: 700; color: #003366; text-transform: uppercase; flex-grow: 1; overflow: hidden;}
        .layer-category-items { padding: 0; background: #f8fafc; }
        .layer-category-items.collapsed { display: none !important; }
        
        .results-item { padding: 4px 8px 4px 16px; font-size: 9px; font-weight: 600; color: #888780; display: flex; justify-content: space-between; align-items: center; cursor: pointer; border-bottom: 1px solid #f0f0f0; }
        .results-item:hover { background: #ffffff; color: #003366; }
        
        .action-icon-trigger { cursor: pointer; padding: 2px; display: inline-flex; align-items: center; justify-content: center; width: 18px; height: 18px; border-radius: 2px; transition: all 0.15s; }
        .action-icon-trigger:hover { background: rgba(0, 51, 102, 0.05); }
        .action-icon-trigger svg { fill: #888780; width: 12px; height: 12px; }
        .action-icon-trigger:hover svg { fill: #003366; }
        .action-icon-trigger.delete-btn:hover svg { fill: #AA2E20; }

        .poi-text-label { background: #fff; border: 1px solid #003366; padding: 2px 4px; border-radius: 2px; font-size: 9px; font-family: 'Montserrat', sans-serif; font-weight: 700; white-space: nowrap; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .hide-labels .poi-text-label { display: none !important; }
        .color-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; border: 1px solid rgba(0,0,0,0.1); }
        
        .config-block-wrapper { padding: 6px 12px; background: #f8fafc; border-bottom: 1px solid rgba(0, 51, 102, 0.08); display: flex; flex-direction: column; gap: 4px; }
        .config-headline { font-size: 8px; font-weight: 800; color: #003366; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }
        .config-flex-row { display: flex; align-items: center; justify-content: space-between; font-size: 9px; font-weight: 600; color: #003366; gap: 6px; }
        .config-flex-row select, .config-flex-row input { font-size: 9px; font-family: 'Montserrat', sans-serif; color: #003366; background: #ffffff; border: 1px solid rgba(0, 51, 102, 0.15); border-radius: 2px; padding: 1px 3px; outline: none; }
        .slider-control-element { flex-grow: 1; margin: 0; -webkit-appearance: none; height: 4px; background: rgba(0,51,102,0.1); border-radius: 2px; outline: none; }
        .slider-control-element::-webkit-slider-thumb { -webkit-appearance: none; width: 10px; height: 10px; border-radius: 50%; background: #003366; cursor: pointer; }

        .group-cluster-block { background: #f1f5f9; border-left: 3px solid #C9AB4C; margin-bottom: 4px; border-bottom: 1px solid rgba(0,51,102,0.08); }
        .group-cluster-header { background: #e2e8f0; padding: 6px 10px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; }
        .group-cluster-title { font-size: 9px; font-weight: 800; color: #003366; text-transform: uppercase; display: flex; align-items: center; gap: 6px; }
        .cluster-popover-modal { display: none; position: absolute; top: 40px; left: 10px; right: 10px; background: #ffffff; border: 1px solid #003366; z-index: 2000; border-radius: 3px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); padding: 10px; }
        .cluster-popover-modal.active { display: block; }
        .cluster-selection-row { display: flex; align-items: center; gap: 8px; font-size: 9px; padding: 4px 0; color: #003366; font-weight: 600; }
    </style>
</head>
<body>
    <div id="map-container">
        <div id="map"></div>

        <div id="scan-results-panel">
            <div class="results-header">
                <span>WORKSPACE</span>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span id="group-layers-trigger-btn" onclick="openClusterModalWindow()" style="color: #ffffff; font-size: 8px; font-weight: 700; border: 1px solid #C9AB4C; padding: 2px 4px; border-radius: 2px; cursor: pointer;">GROUP LAYERS</span>
                    <span id="results-count" style="color:#C9AB4C;">0</span>
                </div>
            </div>

            <div id="cluster-modal-overlay" class="cluster-popover-modal">
                <div style="font-size: 9px; font-weight: 800; color: #003366; border-bottom: 1px solid #C9AB4C; padding-bottom: 4px; margin-bottom: 8px;">CREATE LAYER CLUSTER GROUP</div>
                <div style="margin-bottom: 8px;">
                    <input type="text" id="new-cluster-name-input" placeholder="Enter cluster namespace..." style="width: calc(100% - 10px); font-family: Montserrat; font-size: 9px; padding: 4px; border: 1px solid rgba(0,51,102,0.2);">
                </div>
                <div id="cluster-checkbox-target-mount" style="max-height: 140px; overflow-y: auto; margin-bottom: 8px;"></div>
                <div style="display: flex; gap: 4px;">
                    <button onclick="commitStructuralLayerCluster()" style="flex:1; background: #003366; color:#fff; border:none; padding: 4px; font-size:9px; font-weight:700; cursor:pointer;">BUILD</button>
                    <button onclick="closeClusterModalWindow()" style="flex:1; background: #888780; color:#fff; border:none; padding: 4px; font-size:9px; font-weight:700; cursor:pointer;">CANCEL</button>
                </div>
            </div>
            
            <div class="config-block-wrapper" style="border-bottom: 2px solid var(--brand-gold);">
                <div class="config-headline">Basemap Controller</div>
                <div class="config-flex-row">
                    <span>Tile Style:</span>
                    <select id="basemap-select" onchange="switchActiveBasemap(this.value)">
                        <option value="osm">OpenStreetMap</option>
                        <option value="satellite">Satellite View</option>
                        <option value="carto">Carto Light</option>
                    </select>
                    <label style="font-size:9px; font-weight:700; color:#003366; display:flex; align-items:center; gap:3px; cursor:pointer;">
                        <input type="checkbox" id="label-toggle-chk" onchange="toggleLabelsMatrix(this.checked)" style="accent-color: #003366;"> Labels
                    </label>
                </div>
            </div>
            
            <div class="config-block-wrapper">
                <div class="config-headline">Global Markers</div>
                <div class="config-flex-row">
                    <span>Style:</span>
                    <select id="gl-marker-style" onchange="patchGlobalMarkerStyle(this.value)">
                        <option value="dots">Dots</option>
                        <option value="pin">Pin Location</option>
                        <option value="modern-pin" selected>Modern Drop-Pin</option>
                    </select>
                    <span>Size:</span>
                    <input type="range" min="10" max="40" value="__GLOBAL_MARKER_SIZE__" class="slider-control-element" id="gl-marker-size" oninput="patchGlobalMarkerSize(this.value)">
                </div>
                <div class="config-flex-row">
                    <span>Color:</span>
                    <input type="color" id="gl-marker-color" value="__GLOBAL_MARKER_COLOR__" onchange="patchGlobalMarkerColor(this.value)">
                    <select onchange="document.getElementById('gl-marker-color').value=this.value; patchGlobalMarkerColor(this.value);" style="width:70px;">
                        <option value="">Preset</option>
                        <option value="#003366">Midnight</option>
                        <option value="#C9AB4C">Gold</option>
                        <option value="#AA2E20">Crimson</option>
                    </select>
                </div>
            </div>

            <div class="config-block-wrapper">
                <div class="config-headline">Target Coordinates & Radius Layer</div>
                <div class="config-flex-row">
                    <span>Target:</span>
                    <select onchange="patchTargetCenterConfig('style', this.value)">
                        <option value="star">Star</option>
                        <option value="circle">Dot</option>
                    </select>
                    <input type="color" value="#003366" onchange="patchTargetCenterConfig('color', this.value)">
                    <input type="range" min="10" max="60" value="24" class="slider-control-element" oninput="patchTargetCenterConfig('size', this.value)">
                </div>
                <div class="config-flex-row">
                    <span>Radius Fill:</span>
                    <input type="color" value="#003366" onchange="patchRadiusLayerConfig('color', this.value)">
                    <span>Opacity:</span>
                    <input type="range" min="0" max="1" step="0.01" value="0.08" class="slider-control-element" oninput="patchRadiusLayerConfig('fill_opacity', this.value)">
                </div>
                <div class="config-flex-row">
                    <span>Thickness:</span>
                    <input type="range" min="0.5" max="8" step="0.5" value="1.5" class="slider-control-element" oninput="patchRadiusLayerConfig('weight', this.value)">
                </div>
            </div>
            
            <div class="results-list" id="results-list-box"></div>
        </div>
    </div>

    <script>
        const map = L.map('map', { zoomControl: false, attributionControl: false, preferCanvas: true }).setView([__LAT__, __LON__], 14);
        let layerMeta = __LAYER_META_JSON__;
        let targetConfig = __TARGET_CONFIG_JSON__;
        let radiusConfig = __RADIUS_CONFIG_JSON__;
        let pts = __GEOJSON__;
        let clusters = {}; 

        const basemaps = {
            osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }),
            satellite: L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', { maxZoom: 20 }),
            carto: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 })
        };
        basemaps[(localStorage.getItem('ts_persistent_basemap') || 'osm')].addTo(map);
        
        function switchActiveBasemap(targetKey) {
            Object.keys(basemaps).forEach(k => { if(map.hasLayer(basemaps[k])) map.removeLayer(basemaps[k]); });
            basemaps[targetKey].addTo(map); localStorage.setItem('ts_persistent_basemap', targetKey);
        }

        let labelsActive = localStorage.getItem('ts_persistent_labels') !== 'false';
        document.getElementById('label-toggle-chk').checked = labelsActive;
        if (!labelsActive) document.getElementById('map').classList.add('hide-labels');
        
        function toggleLabelsMatrix(isShown) {
            if (isShown) document.getElementById('map').classList.remove('hide-labels');
            else document.getElementById('map').classList.add('hide-labels');
            localStorage.setItem('ts_persistent_labels', isShown);
        }

        let radiusCircle = null;
        function renderRadiusCircleBounds() {
            if (radiusCircle) map.removeLayer(radiusCircle);
            radiusCircle = L.circle([__LAT__, __LON__], {
                radius: __RADIUS__, color: radiusConfig.color, weight: parseFloat(radiusConfig.weight),
                fillColor: radiusConfig.color, fillOpacity: parseFloat(radiusConfig.fill_opacity)
            }).addTo(map);
        }

        let centerMarker = null;
        function renderTargetCenterIcon() {
            if (centerMarker) map.removeLayer(centerMarker);
            const d = targetConfig.size; const c = targetConfig.color;
            const htmlElement = targetConfig.style === "star" 
                ? `<div style="background-color: ${c}; color: #ffffff; width: ${d}px; height: ${d}px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: ${d*0.5}px; border: 2px solid #ffffff; box-shadow: 0 2px 6px rgba(0, 51, 102, 0.4);">★</div>`
                : `<div style="background-color: ${c}; width: ${d}px; height: ${d}px; border-radius: 50%; border: 3px solid #ffffff; box-shadow: 0 2px 6px rgba(0, 51, 102, 0.4);"></div>`;
            
            centerMarker = L.marker([__LAT__, __LON__], { 
                icon: L.divIcon({ className: 'custom-center-icon', html: htmlElement, iconSize: [d, d], iconAnchor: [d/2, d/2] }), zIndexOffset: 999999 
            }).addTo(map);
        }

        const generateMarkerElement = (color, styleMode, sizeDimension) => {
            const d = parseInt(sizeDimension);
            if (styleMode === "pin") {
                return L.divIcon({ 
                    html: `<div class="custom-pin-container"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${d*1.3}" height="${d*1.3}"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="${color}" stroke="#ffffff" stroke-width="1.5"/></svg></div>`, 
                    className: '', iconSize: [d*1.3, d*1.3], iconAnchor: [d*0.65, d*1.3] 
                });
            } else if (styleMode === "modern-pin") {
                const w = d * 1.5; const h = d * 2.5; const r = d * 0.45; 
                const customSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 65" width="${w}" height="${h}"><defs><radialGradient id="groundShadow" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#000000" stop-opacity="1.0"/><stop offset="100%" stop-color="#000000" stop-opacity="0"/></radialGradient><radialGradient id="sphereGloss-${color.replace('#','')}" cx="35%" cy="35%" r="65%"><stop offset="0%" stop-color="#ffffff" stop-opacity="0.9"/><stop offset="50%" stop-color="${color}"/><stop offset="100%" stop-color="${color}" stop-opacity="0.75"/></radialGradient></defs><ellipse cx="20" cy="44" rx="12" ry="3.5" fill="url(#groundShadow)" /><path d="M20 20 L20 44" stroke="#222222" stroke-width="2.5" stroke-linecap="round"/><path d="M20 20 L20 44" stroke="#888888" stroke-width="0.8" stroke-linecap="round"/><circle cx="20" cy="20" r="${r}" fill="url(#sphereGloss-${color.replace('#','')})"/></svg>`;
                return L.divIcon({ html: `<div style="transform: translate(-50%, -92%); width: ${w}px; height: ${h}px;">${customSvg}</div>`, className: '', iconSize: [w, h], iconAnchor: [0, 0] });
            }
            return L.divIcon({ html: `<div style="background-color: ${color}; width: ${d}px; height: ${d}px; border-radius: 50%; border: 1.5px solid #ffffff; box-shadow: 0 1px 4px rgba(0,0,0,0.2);"></div>`, className: '', iconSize: [d, d], iconAnchor: [d/2, d/2] });
        };

        const layerGroupsRef = {}; const categoryMap = {};

        function compileLayersAndRenderPoints() {
            Object.keys(layerGroupsRef).forEach(k => { map.removeLayer(layerGroupsRef[k]); delete layerGroupsRef[k]; });
            Object.keys(categoryMap).forEach(k => delete categoryMap[k]);
            pts.forEach(p => {
                const layerKey = p.type || 'Unclassified';
                if (!categoryMap[layerKey]) categoryMap[layerKey] = []; categoryMap[layerKey].push(p);
            });
            Object.keys(categoryMap).forEach(key => {
                layerGroupsRef[key] = L.layerGroup().addTo(map);
                const meta = layerMeta[key] || { color: "#003366", style: "modern-pin", size: 20 };
                categoryMap[key].forEach(p => {
                    if (p.visible === false) return;
                    const marker = L.marker([p.lat, p.lon], { icon: generateMarkerElement(meta.color, meta.style, meta.size) })
                                    .bindPopup(`<b>${p.name}</b><br><span style="color:#888780;font-size:9px;">${p.type}</span>`);
                    if (p.name && p.name !== 'Unknown') {
                        marker.bindTooltip(p.name, { permanent: true, direction: 'top', offset: [0, -10], className: 'poi-text-label' });
                    }
                    marker.addTo(layerGroupsRef[key]);
                });
            });
        }

        window.openClusterModalWindow = function() {
            const container = document.getElementById('cluster-checkbox-target-mount');
            container.innerHTML = '';
            const layers = Object.keys(categoryMap);
            if(layers.length === 0) {
                container.innerHTML = '<div style="font-size:9px; padding:4px; color:#888780;">No active layers to compile.</div>';
            } else {
                layers.forEach(lyr => {
                    container.innerHTML += `<div class="cluster-selection-row"><input type="checkbox" class="cluster-matrix-select-target" value="${lyr}" style="accent-color:#003366;"><span>${lyr} (${categoryMap[lyr].length})</span></div>`;
                });
            }
            document.getElementById('cluster-modal-overlay').classList.add('active');
        };

        window.closeClusterModalWindow = function() {
            document.getElementById('cluster-modal-overlay').classList.remove('active');
            document.getElementById('new-cluster-name-input').value = '';
        };

        window.commitStructuralLayerCluster = function() {
            const titleInput = document.getElementById('new-cluster-name-input').value.trim();
            if (!titleInput) { alert('Cluster designation namespace required.'); return; }
            const selectedCheckboxes = document.querySelectorAll('.cluster-matrix-select-target:checked');
            const layerKeys = Array.from(selectedCheckboxes).map(cb => cb.value);
            if (layerKeys.length === 0) { alert('Select at least 1 layer entry.'); return; }
            clusters[titleInput] = layerKeys;
            closeClusterModalWindow();
            rebuildSidebarControlLayout();
        };

        window.destroyClusterGroupReference = function(clusterId) { delete clusters[clusterId]; rebuildSidebarControlLayout(); };
        window.toggleClusterGroupVisibility = function(clusterId, currentlyVisible) {
            const targetedLayers = clusters[clusterId] || [];
            pts.forEach(p => { if (targetedLayers.includes(p.type)) p.visible = !currentlyVisible; });
            compileLayersAndRenderPoints(); rebuildSidebarControlLayout();
        };

        window.batchStyleGroupCluster = function(clusterId, property, value) {
            const targetedLayers = clusters[clusterId] || [];
            targetedLayers.forEach(layerKey => { if (!layerMeta[layerKey]) layerMeta[layerKey] = {}; layerMeta[layerKey][property] = property === 'size' ? parseInt(value) : value; });
            compileLayersAndRenderPoints(); rebuildSidebarControlLayout();
        };

        window.patchGlobalMarkerStyle = function(v) { Object.keys(layerMeta).forEach(k => layerMeta[k].style = v); compileLayersAndRenderPoints(); };
        window.patchGlobalMarkerSize = function(v) { Object.keys(layerMeta).forEach(k => layerMeta[k].size = parseInt(v)); compileLayersAndRenderPoints(); };
        window.patchGlobalMarkerColor = function(v) { Object.keys(layerMeta).forEach(k => layerMeta[k].color = v); compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); };
        window.patchTargetCenterConfig = function(key, val) { targetConfig[key] = val; renderTargetCenterIcon(); };
        window.patchRadiusLayerConfig = function(key, val) { radiusConfig[key] = val; renderRadiusCircleBounds(); };
        window.triggerLayerUpdate = function(layerKey, property, value) { if (!layerMeta[layerKey]) layerMeta[layerKey] = {}; layerMeta[layerKey][property] = property === 'size' ? parseInt(value) : value; compileLayersAndRenderPoints(); };

        function rebuildSidebarControlLayout() {
            const listBox = document.getElementById('results-list-box');
            document.getElementById('results-count').innerText = pts.length;
            if (pts.length === 0) { listBox.innerHTML = "<div style='font-size:9px; padding:12px; color:#888780;'>No items mapped.</div>"; return; }
            let htmlPayload = '';
            const trashSvg = `<svg viewBox="0 0 24 24"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>`;
            const eyeSvg = `<svg viewBox="0 0 24 24"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>`;
            const editSvg = `<svg viewBox="0 0 24 24"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a.996.996 0 0 0 0-1.41l-2.34-2.34a.996.996 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>`;

            Object.keys(clusters).forEach(clusterName => {
                const assignedLayers = clusters[clusterName] || [];
                let aggregatedCount = 0;
                let groupIsVisible = false;
                assignedLayers.forEach(lKey => { if (categoryMap[lKey]) { aggregatedCount += categoryMap[lKey].length; if (categoryMap[lKey].some(p => p.visible !== false)) groupIsVisible = true; } });
                htmlPayload += `<div class="group-cluster-block" id="cluster-block-${clusterName}"><div class="group-cluster-header"><div class="group-cluster-title" onclick="toggleAccordionCollapse('cluster-items-${clusterName}')"><span style="color:#C9AB4C;">⚡</span><span>${clusterName} <span style="font-weight:500; font-size:8px; opacity:0.75;">(${aggregatedCount} PINS)</span></span></div><div style="display:flex; align-items:center; gap:2px;"><a class="action-icon-trigger" title="Hide/Show Group" onclick="toggleClusterGroupVisibility('${clusterName}', ${groupIsVisible})">${eyeSvg}</a><a class="action-icon-trigger delete-btn" title="Dissolve Group" onclick="destroyClusterGroupReference('${clusterName}')">${trashSvg}</a><span id="chevron-cluster-items-${clusterName}" onclick="toggleAccordionCollapse('cluster-items-${clusterName}')" style="font-size: 8px; color:#003366; margin-left:4px; cursor:pointer;">▼</span></div></div><div class="config-block-wrapper" style="background: #e2e8f0; border-bottom: 1px solid rgba(0,51,102,0.15);"><div class="config-headline" style="font-size:7.5px; opacity:0.8;">Batch Group Style Controller</div><div class="config-flex-row"><select onchange="batchStyleGroupCluster('${clusterName}', 'style', this.value)"><option value="dots">Dots</option><option value="pin">Pin</option><option value="modern-pin" selected>Modern Pin</option></select><input type="range" min="10" max="40" value="20" class="slider-control-element" oninput="batchStyleGroupCluster('${clusterName}', 'size', this.value)"><input type="color" value="#003366" onchange="batchStyleGroupCluster('${clusterName}', 'color', this.value)"></div></div><div class="layer-category-items collapsed" id="items-cluster-items-${clusterName}" style="padding-left: 8px; background: rgba(0,0,0,0.02);">`;
                assignedLayers.forEach(catName => { if(!categoryMap[catName]) return; const meta = layerMeta[catName] || { color: "#003366", style: "modern-pin", size: 20 }; const layerPts = categoryMap[catName] || []; const isLayerVisible = layerPts.some(p => p.visible !== false); htmlPayload += injectLayerItemDOMElements(catName, meta, layerPts, isLayerVisible, editSvg, eyeSvg, trashSvg); });
                htmlPayload += '</div></div>';
            });

            Object.keys(categoryMap).forEach(catName => {
                let insideClusterGroup = false; Object.values(clusters).forEach(layerArr => { if(layerArr.includes(catName)) insideClusterGroup = true; }); if (insideClusterGroup) return;
                const meta = layerMeta[catName] || { color: "#003366", style: "modern-pin", size: 20 }; const layerPts = categoryMap[catName] || []; const isLayerVisible = layerPts.some(p => p.visible !== false);
                htmlPayload += `<div class="layer-category-block" id="cat-block-${catName}">`; htmlPayload += injectLayerItemDOMElements(catName, meta, layerPts, isLayerVisible, editSvg, eyeSvg, trashSvg); htmlPayload += '</div>';
            });
            listBox.innerHTML = htmlPayload;
        }

        function injectLayerItemDOMElements(catName, meta, layerPts, isLayerVisible, editSvg, eyeSvg, trashSvg) {
            let chunk = `<div class="layer-category-header"><div class="layer-header-left" onclick="toggleAccordionCollapse('${catName}')"><span class="color-dot" style="background-color: ${meta.color};"></span><span style="font-weight:700;">${catName} <span style="color:#C9AB4C; font-size:8px;">(${layerPts.length})</span></span></div><div style="display:flex; align-items:center; gap:1px;"><a class="action-icon-trigger" title="Rename" onclick="promptRenameLayer('${catName}')">${editSvg}</a><a class="action-icon-trigger" title="Hide/Show" onclick="toggleLayerWorkspaceVisibility('${catName}', ${isLayerVisible})">${eyeSvg}</a><a class="action-icon-trigger delete-btn" title="Delete" onclick="triggerLayerDeletion('${catName}')">${trashSvg}</a><span id="chevron-${catName}" onclick="toggleAccordionCollapse('${catName}')" style="font-size: 8px; color:#C9AB4C; margin-left:4px; cursor:pointer;">▼</span></div></div><div class="config-block-wrapper" style="background:#ffffff; border-bottom:1px dashed rgba(0,51,102,0.05);"><div class="config-flex-row"><select onchange="triggerLayerUpdate('${catName}', 'style', this.value)"><option value="dots" ${meta.style==='dots'?'selected':''}>Dots</option><option value="pin" ${meta.style==='pin'?'selected':''}>Pin</option><option value="modern-pin" ${meta.style==='modern-pin'?'selected':''}>Modern Drop-Pin</option></select><input type="range" min="10" max="40" value="${meta.size}" class="slider-control-element" oninput="triggerLayerUpdate('${catName}', 'size', this.value)"><input type="color" value="${meta.color}" onchange="triggerLayerUpdate('${catName}', 'color', this.value); rebuildSidebarControlLayout();"></div></div><div class="layer-category-items collapsed" id="items-${catName}">`;
            layerPts.forEach(p => { const itemVisible = p.visible !== false; chunk += `<div class="results-item" id="res-item-${p.uid}" style="${itemVisible ? '' : 'opacity:0.4;'}"><div style="flex-grow:1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${p.name || 'Unknown'}" onclick="map.flyTo([${p.lat}, ${p.lon}], 17);">${p.name || 'Unknown'}</div><div style="display:flex; align-items:center; gap:1px;"><a class="action-icon-trigger" onclick="promptRenamePoi(${p.uid}, '${p.name}')">${editSvg}</a><a class="action-icon-trigger" onclick="togglePoiVisibility(${p.uid})">${eyeSvg}</a><a class="action-icon-trigger delete-btn" onclick="removePoiInstance(${p.uid}, '${catName}')">${trashSvg}</a></div></div>`; });
            chunk += '</div>'; return chunk;
        }

        window.toggleAccordionCollapse = function(catKey) { const panel = document.getElementById('items-' + catKey); const chev = document.getElementById('chevron-' + catKey); if(panel) { panel.classList.toggle('collapsed'); chev.innerText = panel.classList.contains('collapsed') ? '▼' : '▲'; } };
        window.togglePoiVisibility = function(uid) { const p = pts.find(item => item.uid === uid); if (p) { p.visible = (p.visible === false); compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); } };
        window.promptRenamePoi = function(uid, oldName) { const newName = prompt("Rename asset description Name:", oldName); if (newName && newName.trim() !== "") { const p = pts.find(item => item.uid === uid); if (p) { p.name = newName; compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); } } };
        window.removePoiInstance = function(uid, catKey) { pts = pts.filter(item => item.uid !== uid); compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); };
        window.toggleLayerWorkspaceVisibility = function(catKey, currentlyVisible) { pts.forEach(p => { if (p.type === catKey) p.visible = !currentlyVisible; }); compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); };
        window.promptRenameLayer = function(oldKey) { const newKey = prompt("Rename layer designation path description:", oldKey); if (newKey && newKey.trim() !== "" && newKey !== oldKey) { pts.forEach(p => { if (p.type === oldKey) p.type = newKey; }); if (layerMeta[oldKey]) { layerMeta[newKey] = layerMeta[oldKey]; delete layerMeta[oldKey]; } Object.keys(clusters).forEach(cName => { clusters[cName] = clusters[cName].map(item => item === oldKey ? newKey : item); }); compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); } };
        window.triggerLayerDeletion = function(catKey) { if (confirm(`Remove entire layer cluster: "${catKey}"?`)) { pts = pts.filter(p => p.type !== catKey); delete layerMeta[catKey]; Object.keys(clusters).forEach(cName => { clusters[cName] = clusters[cName].filter(item => item !== catKey); }); compileLayersAndRenderPoints(); rebuildSidebarControlLayout(); } };

        map.on('contextmenu', function(e) {
            const lat = e.latlng.lat; const lng = e.latlng.lng;
            const menuHtml = `<div style="font-family: Montserrat, sans-serif; font-size: 10px; color: #003366; min-width: 140px; background:#fff; padding:4px;"><div style="font-weight: 800; border-bottom: 1px solid #C9AB4C; padding-bottom: 4px; margin-bottom: 6px; letter-spacing: 0.5px;">MAP OPTIONS</div><div style="padding: 5px 2px; cursor: pointer; font-weight: 700;" onclick="navigator.clipboard.writeText('${lat.toFixed(5)}, ${lng.toFixed(5)}'); map.closePopup();">Copy Coordinates</div><div style="padding: 5px 2px; cursor: pointer; font-weight: 700;" onclick="window.open('https://www.google.com/maps/search/?api=1&query=${lat},${lng}', '_blank'); map.closePopup();">Open in Google Maps</div><div style="padding: 5px 2px; cursor: pointer; font-weight: 700;" onclick="window.open('https://www.google.com/maps?layer=c&cbll=${lat},${lng}', '_blank'); map.closePopup();">Open in Streetview</div></div>`;
            L.popup().setLatLng(e.latlng).setContent(menuHtml).openOn(map);
        });

        renderTargetCenterIcon(); renderRadiusCircleBounds(); compileLayersAndRenderPoints(); rebuildSidebarControlLayout();
        if (pts.length > 0 && !__IS_STALE__) {
            const validPts = pts.filter(p => p.visible !== false);
            if (validPts.length > 0) { map.fitBounds(L.featureGroup([L.marker([__LAT__, __LON__]), ...validPts.map(p => L.marker([p.lat, p.lon]))]).getBounds().pad(0.05)); }
        }
    </script>
</body>
</html>
"""

leaflet_html = (leaflet_template
                .replace("__LAT__", str(render_lat))
                .replace("__LON__", str(render_lon))
                .replace("__RADIUS__", str(radius_val))
                .replace("__IS_STALE__", is_stale)
                .replace("__GLOBAL_MARKER_SIZE__", str(st.session_state.global_marker_size))
                .replace("__GLOBAL_MARKER_COLOR__", str(st.session_state.global_marker_color))
                .replace("__TARGET_CONFIG_JSON__", target_config_json)
                .replace("__RADIUS_CONFIG_JSON__", radius_config_json)
                .replace("__LAYER_META_JSON__", layer_meta_json)
                .replace("__GEOJSON__", geojson_str))

st.components.v1.html(leaflet_html, height=850, scrolling=False)
