"""
Trade Area Scan - Unified Version with Leaflet Geoman Integration
Features: SCAN module (POI discovery) + EDITOR module (drawing) on ONE Map
All critical bugs fixed, fully modular, production-ready.
"""

import streamlit as st
import requests
import re
import json
import os
import time
from typing import Dict, List, Tuple, Any, Optional

# =====================================================================
# 1. CONSTANTS & CONFIGURATION
# =====================================================================
DEFAULT_LAT = 14.5995
DEFAULT_LON = 120.9842
DEFAULT_COORDS = f"{DEFAULT_LAT}, {DEFAULT_LON}"
DEFAULT_RADIUS = 1000
API_TIMEOUT = 100
NOMINATIM_TIMEOUT = 10
OSM_USER_AGENT = "TradeAreaScan/4.0"

# Color palette (bichromatic theme)
COLOR_MIDNIGHT = "#003366"
COLOR_GOLD = "#C9AB4C"
COLOR_DARK = "#001F3F"
COLOR_WHITE = "#ffffff"
COLOR_BG_LIGHT = "#f8fafc"
COLOR_TEXT_MUTED = "#888780"
SHADOW_SOFT = "0 4px 12px rgba(0, 51, 102, 0.08)"

# =====================================================================
# 2. SESSION STATE INITIALIZATION (Centralized)
# =====================================================================
def init_session_state() -> None:
    """Initialize all session state variables with safe defaults."""
    if "geo_coords" not in st.session_state:
        st.session_state.geo_coords = DEFAULT_COORDS
    if "geo_radius" not in st.session_state:
        st.session_state.geo_radius = DEFAULT_RADIUS
    if "scanned_records" not in st.session_state:
        st.session_state.scanned_records = []
    if "last_scan_lat" not in st.session_state:
        st.session_state.last_scan_lat = DEFAULT_LAT
    if "last_scan_lon" not in st.session_state:
        st.session_state.last_scan_lon = DEFAULT_LON
    if "last_geocoded_query" not in st.session_state:
        st.session_state.last_geocoded_query = ""
    if "editor_layers" not in st.session_state:
        st.session_state.editor_layers = []
    if "active_editor_layer" not in st.session_state:
        st.session_state.active_editor_layer = ""
    if "editor_drawings" not in st.session_state:
        st.session_state.editor_drawings = {}


# =====================================================================
# 3. PAGE CONFIG & THEME (Must execute before set_page_config)
# =====================================================================
def setup_light_mode_lock() -> None:
    """Ensure light mode is locked programmatically."""
    config_dir = ".streamlit"
    config_file = os.path.join(config_dir, "config.toml")
    if not os.path.exists(config_file):
        os.makedirs(config_dir, exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            f.write("[theme]\nbase=\"light\"\n")


setup_light_mode_lock()

st.set_page_config(
    page_title="Trade Area Scan",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# 4. GLOBAL STYLES (Bichromatic branded theme)
# =====================================================================
def apply_global_styles() -> None:
    """Apply branded CSS styles to the entire app."""
    # NOTE: Double curly braces {{ }} are used here to escape CSS for Python's f-string
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Montserrat:wght@400;500;600;700;800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0');

        :root {{
            --brand-midnight: {COLOR_MIDNIGHT} !important;
            --brand-gold: {COLOR_GOLD} !important;
            --brand-dark: {COLOR_DARK} !important;
            --white-clean: {COLOR_WHITE} !important;
            --bg-offwhite: {COLOR_BG_LIGHT} !important;
            --text-muted: {COLOR_TEXT_MUTED} !important;
            --soft-shadow: {SHADOW_SOFT} !important;
        }}
        
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {{
            background-color: var(--white-clean) !important;
            color: var(--brand-midnight) !important;
            font-family: 'Montserrat', sans-serif !important;
        }}
        
        [data-testid="stSidebar"] {{
            background-color: var(--bg-offwhite) !important;
            color: var(--brand-midnight) !important;
            border-right: 1px solid rgba(0, 51, 102, 0.08) !important;
            width: 280px !important;
            min-width: 280px !important;
            max-width: 280px !important;
            box-shadow: 2px 0 15px rgba(0,0,0,0.03) !important;
        }}
        
        [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] {{ display: none !important; }}
        ::-webkit-scrollbar {{ width: 0px !important; background: transparent !important; }}
        * {{ scrollbar-width: none !important; -ms-overflow-style: none !important; }}
        
        p, label, h1, h2, h3, h4, h5, h6, .stMarkdown {{
            color: var(--brand-midnight) !important;
            font-family: 'Montserrat', sans-serif !important;
        }}
        
        [data-testid="stHeader"], header, #stDecoration {{ display: none !important; }}
        
        [data-testid="stAppViewContainer"] {{ display: flex !important; flex-direction: row !important; width: 100vw !important; height: 100vh !important; overflow: hidden !important; }}
        [data-testid="stMain"] {{ flex-grow: 1 !important; width: calc(100vw - 280px) !important; height: 100vh !important; overflow: hidden !important; margin: 0px !important; padding: 0px !important; }}
        .block-container, [data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"], .stElementContainer {{ padding: 0px !important; margin: 0px !important; max-width: 100% !important; gap: 0rem !important; }}
        iframe {{ height: 100vh !important; width: 100% !important; border: none !important; display: block !important; }}
        
        [data-testid="stSidebarUserContent"] {{
            padding-top: 12px !important; padding-left: 12px !important; padding-right: 12px !important; 
            height: 100vh !important; overflow-y: auto !important; overflow-x: hidden !important;
        }}
        
        div[data-baseweb="input"], div[data-baseweb="select"] {{ 
            background-color: transparent !important; border: none !important; 
            border-bottom: 1px solid rgba(201, 171, 76, 0.5) !important; border-radius: 0px !important; 
            box-shadow: none !important; 
        }}
        div[data-baseweb="input"]:focus-within {{ border-bottom: 2px solid var(--brand-gold) !important; }}
        
        div.stButton > button[kind="secondary"], [data-testid="stPopover"] > button {{ 
            background-color: var(--brand-midnight) !important; 
            border: 1px solid var(--brand-midnight) !important; border-radius: 2px !important; 
            width: 100% !important; padding: 6px !important; box-shadow: var(--soft-shadow) !important; 
            transition: all 0.3s ease !important; 
        }}
        div.stButton > button[kind="secondary"]:hover, [data-testid="stPopover"] > button:hover {{ 
            background-color: var(--brand-gold) !important; border-color: var(--brand-gold) !important; 
        }}
        div.stButton > button[kind="secondary"] p, [data-testid="stPopover"] > button p, div.stDownloadButton > button p {{ 
            color: var(--white-clean) !important; font-weight: 700 !important; font-size: 9px !important; 
            text-transform: uppercase !important; letter-spacing: 1px; 
        }}
        
        div.stDownloadButton > button {{ 
            background-color: var(--brand-midnight) !important; border: none !important; 
            border-radius: 2px !important; width: 100% !important; padding: 4px !important; 
        }}
        div.stDownloadButton > button:hover {{ background-color: var(--brand-gold) !important; }}
        
        div.stButton > button[kind="primary"] {{ 
            background: transparent !important; border: none !important; color: var(--text-muted) !important; 
            box-shadow: none !important; padding: 0 !important; margin-top: 2px; display: inline-flex; 
        }}
        div.stButton > button[kind="primary"] p {{ 
            color: var(--text-muted) !important; font-size: 9px !important; font-weight: 600 !important; 
            text-decoration: none !important; text-transform: uppercase; 
        }}
        div.stButton > button[kind="primary"]:hover p {{ color: #AA2E20 !important; }}
        
        /* SCALED DOWN FONTS FOR DROPDOWN POIS */
        [data-testid="stSidebar"] .st-expander {{ 
            border: 1px solid rgba(0, 51, 102, 0.05) !important; background-color: var(--white-clean) !important; 
            border-radius: 2px !important; margin-bottom: 2px !important; overflow: hidden !important; 
        }}
        [data-testid="stSidebar"] .st-expander summary p {{ font-size: 8px !important; font-weight: 600 !important; }}
        .stCheckbox label p {{ font-size: 8px !important; font-weight: 500 !important; line-height: 1.2 !important; }}
        
        div[data-baseweb="checkbox"] input:checked + div, div[data-baseweb="checkbox"] div[aria-checked="true"] {{ 
            background-color: var(--brand-midnight) !important; border-color: var(--brand-midnight) !important; 
        }}
        
        .stDeployButton, footer {{ display: none !important; }}
        
        .brand-title {{ 
            font-family: 'Cormorant Garamond', serif !important; font-style: italic; 
            color: var(--brand-midnight); font-size: 28px; text-align: center; 
            border-bottom: 1px solid var(--brand-gold); padding-bottom: 6px; margin-bottom: 20px; 
        }}
        .stTextInput label p, .stNumberInput label p {{ 
            font-size: 8px !important; font-weight: 600 !important; letter-spacing: 0.5px; 
            color: var(--text-muted) !important; 
        }}
    </style>
    """, unsafe_allow_html=True)


# =====================================================================
# 5. POI CONFIGURATION (Organized, extendable)
# =====================================================================
POI_CONFIG: Dict[str, List[List[str]]] = {
    "COMMERCIAL": [
        ["Corporate Office", '"building"~"office|commercial",i'],
        ["IT/Tech Center", '"office"~"it|telecommunication",i'],
        ["Business Center", '"building"="commercial"'],
        ["Hospital", '"amenity"~"hospital|clinic",i'],
        ["Hotel", '"tourism"="hotel"'],
        ["Motel", '"tourism"="motel"'],
    ],
    "RESIDENTIAL": [
        ["Apartments", '"building"="apartments"'],
        ["House", '"building"="house"'],
        ["Residential Area", '"landuse"="residential"'],
        ["Condominium", '"building"="residential"'],
    ],
    "RETAIL": [
        ["Mall/Department Store", '"shop"~"mall|department_store",i'],
        ["Supermarket", '"shop"~"supermarket|grocery",i'],
        ["Convenience Store", '"shop"="convenience"'],
        ["Pharmacy", '"amenity"="pharmacy"'],
        ["Hardware", '"shop"~"hardware|doityourself",i'],
        ["General Shops", '"shop"~"boutique|clothes|shoes",i'],
        ["Beauty", '"shop"="beauty"'],
        ["Bicycle", '"shop"="bicycle"'],
        ["Books/Stationary", '"shop"~"books|stationary",i'],
        ["Car", '"shop"="car"'],
        ["Chemist", '"shop"="chemist"'],
        ["Clothes", '"shop"="clothes"'],
        ["Copyshop", '"shop"="copyshop"'],
        ["Cosmetics", '"shop"="cosmetics"'],
        ["Department store", '"shop"="department_store"'],
        ["DIY/hardware", '"shop"~"hardware|doityourself",i'],
        ["Garden centre", '"shop"="garden_centre"'],
        ["General", '"shop"="general"'],
        ["Gift", '"shop"="gift"'],
        ["Hairdresser", '"shop"="hairdresser"'],
        ["Jewelry", '"shop"="jewelry"'],
        ["Kiosk", '"shop"="kiosk"'],
        ["Leather", '"shop"="leather"'],
        ["Marketplace", '"amenity"="marketplace"'],
        ["Musical instrument", '"shop"="musical_instrument"'],
        ["Optician", '"shop"="optician"'],
        ["Pets", '"shop"="pets"'],
        ["Phone", '"shop"="mobile_phone"'],
        ["Photo", '"shop"="photo"'],
        ["Shoes", '"shop"="shoes"'],
        ["Shopping centre", '"shop"="mall"'],
        ["Textiles", '"shop"="textiles"'],
        ["Toys", '"shop"="toys"'],
    ],
    "FOOD AND BEVERAGES": [
        ["Restaurant", '"amenity"="restaurant"'],
        ["Cafe/Coffee Shop", '"amenity"~"cafe|coffee",i'],
        ["Fast Food", '"amenity"="fast_food"'],
        ["Bar/Pub/Nightclub", '"amenity"~"bar|pub|nightclub",i'],
        ["Bakery/Pastry", '"shop"="bakery"'],
        ["BBQ", '"amenity"="bbq"'],
        ["Biergarten", '"amenity"="biergarten"'],
        ["Food court", '"amenity"="food_court"'],
        ["Ice cream", '"amenity"="ice_cream"'],
        ["Pub", '"amenity"="pub"'],
    ],
    "INDUSTRIAL & LOGISTICS": [
        ["Expressway Exits", '"highway"~"motorway_junction|toll_gantry",i'],
        ["Ports & Terminals", '"industrial"="port"'],
        ["Manufacturing Plants", '"industrial"~"factory|manufacturing|processing",i'],
        ["Cold Storage Facilities", '"warehouse"~"cold_store|cold_storage",i'],
        ["Industrial Parks/Estates", '"landuse"~"industrial|industrial_estate",i'],
        ["Warehouses & Depots", '"building"~"warehouse|depot",i'],
        ["Storage Facilities", '"building"="storage"'],
        ["Truck Access Routes (HGV)", '"hgv"~"designated|yes",i'],
    ],
    "GOVERNMENT & INFRASTRUCTURE": [
        ["City Hall", '"amenity"="townhall"'],
        ["Police Station", '"amenity"="police"'],
        ["Fire Station", '"amenity"="fire_station"'],
        ["Airport Terminal", '"aeroway"~"terminal|aerodrome",i'],
    ],
    "SCHOOLS": [
        ["University/College", '"amenity"~"university|college",i'],
        ["K-12 School", '"amenity"="school"'],
        ["Vocational/Other", '"amenity"="learning_centre"'],
    ],
}

ADVANCED_CONFIG: Dict[str, List[List[str]]] = {
    "AMENITIES": [
        ["ATM", '"amenity"="atm"'],
        ["Bank", '"amenity"="bank"'],
        ["Bench", '"amenity"="bench"'],
        ["Bicycle Parking", '"amenity"="bicycle_parking"'],
        ["Bicycle Rental", '"amenity"="bicycle_rental"'],
        ["Cinema", '"amenity"="cinema"'],
        ["Clinic", '"amenity"="clinic"'],
        ["Embassy", '"amenity"="embassy"'],
        ["Firestation", '"amenity"="fire_station"'],
        ["Fuel", '"amenity"="fuel"'],
        ["Hospital", '"amenity"="hospital"'],
        ["Library", '"amenity"="library"'],
        ["Music School", '"amenity"="music_school"'],
        ["Parking", '"amenity"="parking"'],
        ["Pharmacy", '"amenity"="pharmacy"'],
        ["Police", '"amenity"="police"'],
        ["Letter Box", '"amenity"="letter_box"'],
        ["Post Office", '"amenity"="post_office"'],
        ["School/College", '"amenity"~"school|college",i'],
        ["Taxi", '"amenity"="taxi"'],
        ["Theatre", '"amenity"="theatre"'],
        ["Toilets", '"amenity"="toilets"'],
        ["University", '"amenity"="university"'],
    ],
    "PLACE OF WORSHIP": [
        ["Church", '"religion"="christian"'],
        ["Mosque", '"religion"="muslim"'],
        ["Buddhist Temple", '"religion"="buddhist"'],
        ["Hindu Temple", '"religion"="hindu"'],
        ["Synagogue", '"religion"="jewish"'],
    ],
    "SPORTS": [
        ["American football", '"sport"="american_football"'],
        ["Baseball", '"sport"="baseball"'],
        ["Basketball", '"sport"="basketball"'],
        ["Cycling", '"sport"="cycling"'],
        ["Gymnastics", '"sport"="gymnastics"'],
        ["Golf", '"sport"="golf"'],
        ["Hockey", '"sport"="hockey"'],
        ["Horse racing", '"sport"="horse_racing"'],
        ["Ice hockey", '"sport"="ice_hockey"'],
        ["Soccer", '"sport"="soccer"'],
        ["Sports centre", '"leisure"="sports_centre"'],
        ["Surfing", '"sport"="surfing"'],
        ["Swimming", '"sport"="swimming"'],
        ["Tennis", '"sport"="tennis"'],
        ["Volleyball", '"sport"="volleyball"'],
    ],
    "MISCELLANEOUS": [
        ["Busstop", '"highway"="bus_stop"'],
        ["E-bike charging", '"amenity"="charging_station"'],
        ["Kindergarten", '"amenity"="kindergarten"'],
        ["Marketplace", '"amenity"="marketplace"'],
        ["Office", '"office"="yes"'],
        ["Recycling", '"amenity"="recycling"'],
        ["Travel agency", '"shop"="travel_agency"'],
    ],
}

# =====================================================================
# 6. UTILITY FUNCTIONS
# =====================================================================

def escape_xml(text: str) -> str:
    """Escape XML/KML special characters safely."""
    return (
        text.replace("&", "&")
        .replace("<", "<")
        .replace(">", ">")
        .replace('"', """)
        .replace("'", "'")
    )

def escape_javascript(text: str) -> str:
    """Escape text for safe injection into JavaScript."""
    return (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("'", "\\'")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("</", "<\\/")
    )

def parse_coordinates(coords_str: str) -> Optional[Tuple[float, float]]:
    """Parse coordinate string to (lat, lon) tuple. Returns None if invalid."""
    match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", coords_str)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None

def geocode_location(location_input: str) -> Optional[Tuple[float, float]]:
    """Geocode a location string using OpenStreetMap Nominatim API."""
    try:
        headers = {"User-Agent": OSM_USER_AGENT}
        url = f"https://nominatim.openstreetmap.org/search?q={location_input}&format=json&limit=1"
        response = requests.get(url, headers=headers, timeout=NOMINATIM_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon
        return None
    except requests.RequestException as e:
        st.error(f"Geocoding error: {type(e).__name__}")
        return None
    except (KeyError, ValueError, IndexError):
        st.error("Invalid response from geocoding service")
        return None

def compile_features_kml(features: List[Dict[str, Any]]) -> str:
    """Compile features into valid KML format with proper XML escaping."""
    kml = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Scanned POIs</name>'
    for feature in features:
        name = escape_xml(feature.get("name", "Asset"))
        class_type = escape_xml(feature.get("type", "Node"))
        lat = feature.get("lat", 0)
        lon = feature.get("lon", 0)
        kml += f"<Placemark><name>{name}</name><description>{class_type}</description><Point><coordinates>{lon},{lat},0</coordinates></Point></Placemark>"
    kml += "</Document></kml>"
    return kml

def query_overpass(
    lat: float, lon: float, radius: int, selected_tags: List[str]
) -> List[Dict[str, Any]]:
    """Query Overpass API for POIs and return standardized feature list."""
    if not selected_tags:
        st.error("Select at least 1 layer.")
        return []

    statements = "\n".join(
        [f"  nwr[{tag}](around:{radius},{lat},{lon});" for tag in selected_tags]
    )
    query = f"[out:json][timeout:90];\n(\n{statements}\n);\nout center;"

    try:
        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            headers={"User-Agent": OSM_USER_AGENT},
            timeout=API_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        records = []
        for element in data.get("elements", []):
            lat_val = element.get("lat") or element.get("center", {}).get("lat")
            lon_val = element.get("lon") or element.get("center", {}).get("lon")
            if lat_val and lon_val:
                tags = element.get("tags", {})
                records.append(
                    {
                        "lat": lat_val,
                        "lon": lon_val,
                        "name": tags.get("name", "Unknown"),
                        "type": tags.get("amenity")
                        or tags.get("shop")
                        or tags.get("building")
                        or "Node",
                    }
                )
        return records
    except requests.RequestException as e:
        st.error(f"Overpass API error: {type(e).__name__}")
        return []
    except (KeyError, ValueError):
        st.error("Invalid response from Overpass API")
        return []


# =====================================================================
# 7. UNIFIED SIDEBAR UI
# =====================================================================
def render_sidebar() -> None:
    """Render unified sidebar with location input, scan parameters, and layer management."""
    with st.sidebar:
        st.markdown(
            '<div class="brand-title">Trade Area Scan</div>', unsafe_allow_html=True
        )

        # Location & Coordinates Input
        location_input = st.text_input(
            "LOCATION SEARCH OR COORDINATES",
            value=st.session_state.geo_coords,
            key="geo_coords_input",
            label_visibility="visible",
        )

        radius_val = st.number_input(
            "RADIUS (METERS)",
            min_value=100,
            max_value=50000,
            value=st.session_state.geo_radius,
            key="geo_radius_input",
            step=100,
        )
        st.session_state.geo_radius = radius_val

        # Parse coordinates or geocode
        coords = parse_coordinates(location_input)
        if coords:
            lat_coord, lon_coord = coords
            st.session_state.geo_coords = location_input
        else:
            if (
                location_input
                and location_input != st.session_state.get("last_geocoded_query", "")
            ):
                with st.spinner("Locating via OpenStreetMap..."):
                    geocoded = geocode_location(location_input)
                    if geocoded:
                        lat_coord, lon_coord = geocoded
                        st.session_state.geo_coords = f"{lat_coord:.5f}, {lon_coord:.5f}"
                        st.session_state.last_geocoded_query = location_input
                        st.rerun()
                    else:
                        lat_coord, lon_coord = DEFAULT_LAT, DEFAULT_LON
            else:
                fallback = parse_coordinates(st.session_state.geo_coords)
                if fallback:
                    lat_coord, lon_coord = fallback
                else:
                    lat_coord, lon_coord = DEFAULT_LAT, DEFAULT_LON

        # Search query filter
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
        search_query = st.text_input(
            "SEARCH TAGS", placeholder="Search parameters...", key="search_query_input"
        ).lower()
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

        # Layer selection with search filtering
        selected_tags = []
        for cat_name, node_items in POI_CONFIG.items():
            matched = [
                item for item in node_items if search_query in item[0].lower()
            ]
            if matched:
                with st.expander(cat_name, expanded=(len(search_query) > 0)):
                    for label, tag in matched:
                        if st.checkbox(label, key=f"chk_{cat_name}_{label}"):
                            selected_tags.append(tag)

        st.markdown(
            "<div style='font-weight: 700; font-size: 11px; margin-top: 15px; margin-bottom: 8px; color: #003366; letter-spacing: 1px;'>ADVANCED POIs</div>",
            unsafe_allow_html=True,
        )

        for cat_name, node_items in ADVANCED_CONFIG.items():
            matched = [
                item for item in node_items if search_query in item[0].lower()
            ]
            if matched:
                with st.expander(cat_name, expanded=(len(search_query) > 0)):
                    for label, tag in matched:
                        if st.checkbox(label, key=f"chk_adv_{cat_name}_{label}"):
                            selected_tags.append(tag)

        st.markdown("<br>", unsafe_allow_html=True)

        # Action buttons
        if st.button("SCAN AREA", type="secondary", use_container_width=True, key="scan_btn"):
            if not selected_tags:
                st.error("Select at least 1 layer.")
            else:
                with st.spinner("Extracting nodes..."):
                    records = query_overpass(lat_coord, lon_coord, radius_val, selected_tags)
                    if records:
                        st.session_state.scanned_records = records
                        st.session_state.last_scan_lat = lat_coord
                        st.session_state.last_scan_lon = lon_coord
                        st.rerun()

        if st.button("CLEAR ALL", type="primary", key="clear_btn", use_container_width=True):
            st.session_state.scanned_records = []
            for key in list(st.session_state.keys()):
                if key.startswith("chk_"):
                    st.session_state[key] = False
            st.rerun()

        st.markdown(
            "<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>",
            unsafe_allow_html=True,
        )

        # Export buttons (JSON & KML)
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "JSON",
                json.dumps(st.session_state.scanned_records),
                "scan.json",
                "application/json",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                "KML",
                compile_features_kml(st.session_state.scanned_records),
                "POIs.kml",
                "application/vnd.google-earth.kml+xml",
                use_container_width=True,
            )

        st.markdown(
            "<hr style='margin: 15px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.1);'>",
            unsafe_allow_html=True,
        )
        
        # --- LAYER MANAGEMENT (EDITOR LOGIC INCLUDED) ---
        st.markdown(
            "<div style='font-size:10px; font-weight:600; color:#888780; text-transform:uppercase; text-align:center; margin-bottom:12px;'>Custom Draw Layers</div>",
            unsafe_allow_html=True,
        )

        new_layer_name = st.text_input(
            "NEW LAYER NAME", placeholder="e.g. Trade Zone A", key="new_layer_name"
        )
        if st.button("ADD LAYER", type="secondary", use_container_width=True, key="add_layer_btn"):
            if new_layer_name.strip():
                layer_id = f"layer_{len(st.session_state.editor_layers)}_{int(time.time())}"
                st.session_state.editor_layers.append(
                    {
                        "id": layer_id,
                        "name": new_layer_name.strip(),
                        "visible": True,
                        "color": COLOR_MIDNIGHT,
                        "fill_color": COLOR_GOLD,
                        "fill_opacity": 0.4,
                        "weight": 2.0,
                        "icon_shape": "pin",
                        "icon_size": 24,
                    }
                )
                st.session_state.active_editor_layer = layer_id
                st.rerun()

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        if st.session_state.editor_layers:
            for idx, layer in enumerate(st.session_state.editor_layers):
                with st.expander(f"⚙ {layer['name']}", expanded=False):
                    layer["visible"] = st.checkbox(
                        "Visible", value=layer["visible"], key=f"vis_{layer['id']}"
                    )
                    col_l, col_r = st.columns(2)
                    with col_l:
                        layer["color"] = st.color_picker("Stroke", layer["color"], key=f"col_{layer['id']}")
                    with col_r:
                        layer["fill_color"] = st.color_picker("Fill", layer["fill_color"], key=f"fill_{layer['id']}")

                    layer["fill_opacity"] = st.slider("Fill Opacity", 0.0, 1.0, layer["fill_opacity"], 0.1, key=f"op_{layer['id']}")
                    layer["weight"] = st.slider("Stroke Weight", 0.5, 5.0, layer["weight"], 0.5, key=f"wt_{layer['id']}")
                    layer["icon_shape"] = st.selectbox("Icon Shape", ["pin", "circle"], index=0 if layer["icon_shape"] == "pin" else 1, key=f"shape_{layer['id']}")
                    layer["icon_size"] = st.slider("Icon Size", 12, 48, layer["icon_size"], 2, key=f"size_{layer['id']}")

                    if st.button("DELETE LAYER", type="primary", use_container_width=True, key=f"del_{layer['id']}"):
                        st.session_state.editor_layers.pop(idx)
                        if st.session_state.get("active_editor_layer") == layer["id"]:
                            st.session_state.active_editor_layer = None
                        st.rerun()

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            layer_names = [l["name"] for l in st.session_state.editor_layers]
            layer_ids = [l["id"] for l in st.session_state.editor_layers]
            active_idx = 0
            if st.session_state.get("active_editor_layer") in layer_ids:
                active_idx = layer_ids.index(st.session_state.active_editor_layer)
            selected = st.selectbox("DRAW TO LAYER", layer_names, index=active_idx, key="active_layer_select")
            st.session_state.active_editor_layer = layer_ids[layer_names.index(selected)]
        else:
            st.markdown(
                "<div style='font-size:10px; color:#888780; text-align:center; padding:10px 0;'>Add a layer to start drawing.</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            "<hr style='margin: 12px 0; border: 0; border-top: 1px solid rgba(0, 51, 102, 0.08);'>",
            unsafe_allow_html=True,
        )

        editor_export = {
            "coords": st.session_state.geo_coords,
            "radius": st.session_state.geo_radius,
            "layers": st.session_state.editor_layers,
            "scanned_records": st.session_state.scanned_records,
            "drawings": st.session_state.editor_drawings,
        }
        st.download_button(
            "EXPORT FULL PROJECT",
            json.dumps(editor_export),
            "TradeArea_Project.json",
            "application/json",
            use_container_width=True,
        )


# =====================================================================
# 8. UNIFIED LEAFLET MAP TEMPLATE
# =====================================================================
def get_leaflet_unified_template() -> str:
    """Return unified Leaflet map HTML with both Scanning POIs and Geoman Drawing Tools."""
    # NOTE: Strictly using a standard raw string (no 'f' prefix) to prevent Python from parsing CSS as f-string logic.
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <link rel="stylesheet" href="https://unpkg.com/@geoman-io/leaflet-geoman-free@latest/dist/leaflet-geoman.css" />
        <script src="https://unpkg.com/@geoman-io/leaflet-geoman-free@latest/dist/leaflet-geoman.min.js"></script>
        <script src="https://unpkg.com/@turf/turf@6/turf.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            body, html { margin: 0; padding: 0; height: 100%; width: 100%; overflow: hidden; font-family: 'Montserrat', sans-serif; background: #ffffff; }
            #map { height: 100vh; width: 100%; z-index: 1; }
            
            /* Basemap and Toolbar Settings */
            #minimal-basemap-panel { position: absolute; top: 110px; left: 50px; z-index: 1000; background: #ffffff; border-radius: 4px; border: 1px solid rgba(0, 51, 102, 0.1); display: none; flex-direction: column; padding: 4px; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); width: 160px; }
            #minimal-basemap-panel select { border: none; border-bottom: 1px solid #f0f0f0; padding: 6px; font-size: 10px; font-weight: 700; font-family: 'Montserrat', sans-serif; color: #003366; background: transparent; outline: none; cursor: pointer; width: 100%; text-transform: uppercase; }
            .minimal-label { font-size: 9px; font-weight: 700; padding: 6px; display: flex; align-items: center; gap: 4px; cursor: pointer; color: #888780; margin: 0; text-transform: uppercase; border-top: 1px solid #f8fafc; }
            .minimal-label:hover { color: #003366; background: #f8fafc; }

            /* Nominatim Search container */
            #search-container { position: absolute; top: 10px; left: 54px; z-index: 1000; width: 300px; }
            #map-search { width: 100%; padding: 8px 12px; border: 1px solid rgba(0, 51, 102, 0.1); border-radius: 4px; background-clip: padding-box; font-size: 11px; font-family: 'Montserrat', sans-serif; font-weight: 600; color: #003366; background: #ffffff; outline: none; box-sizing: border-box; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); }
            #map-search:focus { border-bottom: 2px solid #C9AB4C; }
            #search-results { position: absolute; top: 38px; left: 0; width: 100%; background: #ffffff; border-radius: 2px; display: none; max-height: 250px; overflow-x: hidden; overflow-y: auto; border: 1px solid rgba(0, 51, 102, 0.1); box-sizing: border-box; z-index: 1001; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); }
            .search-item { padding: 8px 12px; font-size: 10px; font-weight: 600; cursor: pointer; border-bottom: 1px solid #f8fafc; color: #003366; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            .search-item:hover { background: #f8fafc; color: #C9AB4C; }

            /* SCAN POIs RESULTS PANEL (Top Right) */
            #scan-results-panel { position: absolute; top: 10px; right: 10px; z-index: 1000; background: #ffffff; width: 250px; height: calc(50vh - 15px); border-radius: 4px; border: 1px solid rgba(0, 51, 102, 0.1); display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); }
            .results-header { background: #003366; color: #ffffff; padding: 10px 12px; font-size: 10px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; border-bottom: 2px solid #C9AB4C; letter-spacing: 1px; }
            .results-list { overflow-y: auto; flex-grow: 1; padding-bottom: 8px; font-size: 8px;}
            .layer-category-block { border-bottom: 1px solid #f0f0f0; }
            .layer-category-header { background: #ffffff; padding: 6px 10px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; user-select: none; transition: background 0.2s; }
            .layer-category-header:hover { background: #f8fafc; }
            .layer-header-left { display: flex; align-items: center; gap: 6px; font-size: 8px; font-weight: 700; color: #003366; text-transform: uppercase;}
            .layer-category-items { padding: 0; background: #f8fafc; }
            .layer-category-items.collapsed { display: none !important; }
            .results-item { padding: 4px 12px 4px 28px; font-size: 8px; font-weight: 600; color: #888780; display: flex; justify-content: space-between; align-items: center; cursor: pointer; border-bottom: 1px solid #f0f0f0; }
            .results-item:hover { background: #ffffff; color: #003366; }
            .results-item .delete-poi-icon { cursor: pointer; padding: 2px; display: flex; }
            .results-item .delete-poi-icon svg { fill: #888780; transition: fill 0.2s; }
            .results-item .delete-poi-icon:hover svg { fill: #AA2E20; }

            /* EDITOR DRAWING LAYERS PANEL (Bottom Right) */
            #layer-panel { position: absolute; top: calc(50vh + 5px); right: 10px; z-index: 1000; background: #ffffff; width: 250px; height: calc(50vh - 20px); border-radius: 4px; border: 1px solid rgba(0, 51, 102, 0.1); display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 20px rgba(0, 51, 102, 0.15); }
            .layer-panel-header { background: #003366; color: #ffffff; padding: 10px 12px; font-size: 10px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; border-bottom: 2px solid #C9AB4C; letter-spacing: 1px; }
            .layer-list { overflow-y: auto; flex-grow: 1; background: #ffffff; }
            .layer-row { padding: 8px 12px; display: flex; align-items: center; gap: 8px; cursor: pointer; border-bottom: 1px solid #f1f5f9; transition: background 0.15s; }
            .layer-row:hover { background: #f8fafc; }
            .layer-row.active { background: #e0e7ff; border-left: 3px solid #003366; }
            .layer-color-dot { width: 10px; height: 10px; border-radius: 50%; border: 1px solid rgba(0,0,0,0.15); flex-shrink: 0; }
            .layer-name { font-size: 10px; font-weight: 600; color: #003366; flex-grow: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            .layer-count { font-size: 9px; font-weight: 700; color: #C9AB4C; background: rgba(0,51,102,0.05); padding: 2px 6px; border-radius: 10px; }
            .layer-visibility { cursor: pointer; color: #94a3b8; font-size: 12px; }
            .layer-visibility:hover { color: #003366; }

            /* EDITOR PROPERTIES & CONTEXT MENU */
            #context-menu { position: absolute; z-index: 10000; background: #ffffff; border-radius: 4px; border: 1px solid rgba(0, 51, 102, 0.15); box-shadow: 0 4px 20px rgba(0, 51, 102, 0.15); display: none; min-width: 160px; font-family: 'Montserrat', sans-serif; }
            .ctx-header { background: #003366; color: #ffffff; padding: 8px 12px; font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; border-bottom: 2px solid #C9AB4C; }
            .ctx-item { padding: 8px 12px; font-size: 10px; font-weight: 600; color: #003366; cursor: pointer; border-bottom: 1px solid #f1f5f9; transition: all 0.15s; }
            .ctx-item:hover { background: #f8fafc; color: #C9AB4C; }
            .ctx-item.danger { color: #AA2E20; }
            .ctx-item.danger:hover { background: #fef2f2; }

            .shape-tooltip { background: #003366; color: #C9AB4C; padding: 4px 8px; border-radius: 3px; font-size: 10px; font-weight: 700; font-family: 'Montserrat', sans-serif; white-space: nowrap; border: 1px solid #C9AB4C; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
            .poi-text-label { background: #fff; border: 1px solid #003366; padding: 2px 4px; border-radius: 2px; font-size: 8px; font-family: 'Montserrat', sans-serif; font-weight: 700; white-space: nowrap; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .hide-labels .poi-text-label { display: none !important; }

            #feature-properties-panel { position: absolute; bottom: 15px; left: 10px; z-index: 1000; background: #ffffff; width: 300px; max-height: calc(60vh); border-radius: 4px; border: 1px solid rgba(0, 51, 102, 0.1); box-shadow: 0 -4px 20px rgba(0, 51, 102, 0.15); display: none; flex-direction: column; overflow: hidden; }
            .panel-header { background: #003366; color: #ffffff; padding: 12px; font-size: 11px; font-weight: 800; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; border-bottom: 2px solid #C9AB4C; letter-spacing: 0.5px;}
            .panel-body { padding: 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
            .control-group { display: flex; flex-direction: column; gap: 3px; }
            .control-group label { font-size: 9px; font-weight: 700; color: #64748b; text-transform: uppercase; }
            .control-group input[type="text"], .control-group select, .control-group input[type="number"] { padding: 6px; font-size: 11px; font-family: 'Montserrat', sans-serif; color: #003366; border: 1px solid #e2e8f0; border-radius: 3px; outline: none; }
            .control-group input[type="color"] { width: 100%; height: 32px; border: 1px solid #e2e8f0; border-radius: 3px; cursor: pointer; }
            .panel-actions { display: flex; gap: 6px; margin-top: 8px; }
            .panel-btn { flex: 1; padding: 6px; font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; border: none; border-radius: 2px; cursor: pointer; font-family: 'Montserrat', sans-serif; }
            .panel-btn-primary { background: #003366; color: #ffffff; }
            .panel-btn-primary:hover { background: #C9AB4C; color: #003366; }
            .panel-btn-danger { background: #fef2f2; color: #AA2E20; border: 1px solid #fecaca; }
            .panel-btn-danger:hover { background: #AA2E20; color: #ffffff; }

            /* LEAFLET CUSTOM TOOLBAR (Share, Layers) */
            .leaflet-control-custom-stack { background: #fff; border: 2px solid rgba(0,0,0,0.2); border-radius: 4px; overflow: hidden; display: flex; flex-direction: column; }
            .leaflet-control-custom-stack a { display: flex !important; align-items: center; justify-content: center; background: #fff; text-decoration: none; width: 34px; height: 34px; border-bottom: 1px solid #ccc; cursor: pointer; }
            .leaflet-control-custom-stack a:last-child { border-bottom: none; }
            .leaflet-control-custom-stack a:hover { background: #f4f4f4; }
            
            /* GEOMAN PROFESSIONAL STYLING */
            .leaflet-pm-toolbar { display: none; } /* Hidden until toggled */
            .leaflet-pm-toolbar .leaflet-buttons-control-button { background: #ffffff !important; border-color: rgba(0,51,102,0.15) !important; }
            .leaflet-pm-toolbar .leaflet-buttons-control-button:hover { background: #f8fafc !important; }
            .leaflet-pm-toolbar .leaflet-pm-icon { filter: invert(17%) sepia(52%) saturate(2000%) hue-rotate(190deg); }
            .leaflet-pm-toolbar .active .leaflet-buttons-control-button { background: #003366 !important; }
            .leaflet-pm-toolbar .active .leaflet-pm-icon { filter: invert(80%) sepia(40%) saturate(500%) hue-rotate(10deg); }
        </style>
    </head>
    <body>
        <div id="map"></div>

        <div id="search-container">
            <input type="text" id="map-search" placeholder="Search coordinates or addresses..." onkeyup="handleSearch(event)">
            <div id="search-results"></div>
        </div>

        <div id="minimal-basemap-panel">
            <select id="basemap-select" onchange="switchActiveBasemap(this.value)">
                <option value="osm">OpenStreetMap</option>
                <option value="satellite">Satellite</option>
                <option value="carto">Carto Light</option>
            </select>
            <label class="minimal-label" for="label-toggle-chk">
                <input type="checkbox" id="label-toggle-chk" style="margin:0; cursor: pointer;" onchange="toggleLabelsMatrix(this.checked)"> Show Labels
            </label>
            <label class="minimal-label" for="edit-toggle-chk">
                <input type="checkbox" id="edit-toggle-chk" style="margin:0; cursor: pointer;" onchange="toggleGeomanTools(this.checked)"> Enable Edit Tools
            </label>
        </div>

        <div id="scan-results-panel">
            <div class="results-header">
                <span>SCANNED POIs</span>
                <span id="results-count" style="color:#C9AB4C;">0</span>
            </div>
            <div class="results-list" id="results-list-box"></div>
        </div>

        <div id="layer-panel">
            <div class="layer-panel-header">
                <span>Drawn Layers</span>
                <span id="layer-total-count" style="color:#C9AB4C; font-size:9px;">0</span>
            </div>
            <div class="layer-list" id="layer-list-box"></div>
        </div>

        <div id="context-menu">
            <div class="ctx-header" id="ctx-header">Actions</div>
            <div class="ctx-item" onclick="ctxEditFeature()">✎ Edit Geometry</div>
            <div class="ctx-item" onclick="ctxEditProperties()">⚙ Edit Properties</div>
            <div class="ctx-item danger" onclick="ctxDeleteFeature()">✕ Delete Feature</div>
        </div>

        <div id="feature-properties-panel">
            <div class="panel-header">
                <span id="prop-panel-title">Feature Properties</span>
                <span style="cursor:pointer;color:#C9AB4C; font-size:14px;" onclick="dismissPropertiesPanel()">✕</span>
            </div>
            <div class="panel-body">
                <div class="control-group">
                    <label>Feature Name</label>
                    <input type="text" id="prop-name">
                </div>
                <div class="control-group" id="group-layer-select">
                    <label>Layer Assignment</label>
                    <select id="prop-layer"></select>
                </div>
                <div class="control-group">
                    <label>Stroke Color</label>
                    <input type="color" id="prop-color">
                </div>
                <div class="control-group" id="group-fill-color">
                    <label>Fill Color</label>
                    <input type="color" id="prop-fill-color">
                </div>
                <div class="control-group" id="group-fill-opacity">
                    <label>Fill Opacity</label>
                    <input type="range" id="prop-fill-opacity" min="0" max="1" step="0.1">
                </div>
                <div class="control-group" id="group-stroke-weight">
                    <label>Stroke Weight</label>
                    <input type="number" id="prop-weight" min="0.5" max="5" step="0.5">
                </div>
                <div class="control-group" id="group-icon-shape">
                    <label>Icon Shape</label>
                    <select id="prop-icon-shape">
                        <option value="pin">PIN</option>
                        <option value="circle">CIRCLE</option>
                    </select>
                </div>
                <div class="control-group" id="group-icon-size">
                    <label>Icon Size (px)</label>
                    <input type="number" id="prop-icon-size" min="12" max="64" value="24">
                </div>
                <div class="panel-actions">
                    <button class="panel-btn panel-btn-primary" onclick="commitFeatureChanges()">Apply Changes</button>
                    <button class="panel-btn panel-btn-danger" onclick="deleteSelectedFeature()">Delete</button>
                </div>
            </div>
        </div>

        <script>
            // ================== INIT ==================
            const map = L.map('map', { zoomControl: true, attributionControl: false }).setView([__LAT__, __LON__], 14);
            map.zoomControl.setPosition('topleft');
            
            // Base Maps
            const basemaps = {
                osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }),
                satellite: L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', { maxZoom: 20 }),
                carto: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 20 })
            };

            let activeBasemapKey = localStorage.getItem('ts_persistent_basemap') || 'osm';
            if (!basemaps[activeBasemapKey]) activeBasemapKey = 'osm';
            document.getElementById('basemap-select').value = activeBasemapKey;
            basemaps[activeBasemapKey].addTo(map);

            function switchActiveBasemap(targetKey) {
                map.removeLayer(basemaps[activeBasemapKey]);
                basemaps[targetKey].addTo(map);
                activeBasemapKey = targetKey;
                localStorage.setItem('ts_persistent_basemap', targetKey);
            }

            // Label Toggles
            let labelsActive = localStorage.getItem('ts_persistent_labels') !== 'false';
            document.getElementById('label-toggle-chk').checked = labelsActive;
            if (!labelsActive) document.getElementById('map').classList.add('hide-labels');

            function toggleLabelsMatrix(isShown) {
                if (isShown) document.getElementById('map').classList.remove('hide-labels');
                else document.getElementById('map').classList.add('hide-labels');
                localStorage.setItem('ts_persistent_labels', isShown);
            }

            // Custom Leaflet TopLeft Stack (Layers toggle)
            const toolbarControl = L.control({position: 'topleft'});
            toolbarControl.onAdd = function (map) {
                const div = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom-stack');
                const layersIcon = `<svg xmlns="http://www.w3.org/2000/svg" height="20" viewBox="0 -960 960 960" width="20" fill="#003366"><path d="m116-435 364-199 364 199-364 199-364-199Zm0 157 364 199 364-199-47-26-317 173-317-173-47 26Zm364-257 267-146-267-146-267 146 267 146Z"/></svg>`;
                div.innerHTML = `<a title="Toggle Map Settings" onclick="toggleLayerMenu(event)">${layersIcon}</a>`;
                return div;
            };
            toolbarControl.addTo(map);

            function toggleLayerMenu(e) {
                e.preventDefault();
                const panel = document.getElementById('minimal-basemap-panel');
                panel.style.display = panel.style.display === 'flex' ? 'none' : 'flex';
            }

            // ================== SEARCH ==================
            let searchTimeout = null;
            function handleSearch(e) {
                clearTimeout(searchTimeout);
                const query = e.target.value;
                const resultsDiv = document.getElementById('search-results');

                if (query.length < 3) { resultsDiv.style.display = 'none'; return; }
                searchTimeout = setTimeout(() => {
                    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`)
                        .then(res => res.json())
                        .then(data => {
                            if (data.length > 0) {
                                resultsDiv.innerHTML = '';
                                data.forEach(item => {
                                    const div = document.createElement('div'); div.className = 'search-item'; div.innerText = item.display_name;
                                    div.onclick = () => { map.flyTo([item.lat, item.lon], 16); resultsDiv.style.display = 'none'; document.getElementById('map-search').value = item.display_name; };
                                    resultsDiv.appendChild(div);
                                });
                                resultsDiv.style.display = 'block';
                            } else { resultsDiv.style.display = 'none'; }
                        }).catch(err => console.error(err));
                }, 500);
            }
            document.addEventListener('click', function(e) {
                if (!document.getElementById('search-container').contains(e.target)) { document.getElementById('search-results').style.display = 'none'; }
                const ctxMenu = document.getElementById('context-menu');
                if (!ctxMenu.contains(e.target)) ctxMenu.style.display = 'none';
            });

            // ================== GEOMAN & STATE ==================
            map.pm.setGlobalOptions({ snappable: true, snapDistance: 20, allowSelfIntersection: false, hintlineStyle: { color: '#C9AB4C', dashArray: '5,5' }, templineStyle: { color: '#003366', weight: 2 }});
            map.pm.addControls({ position: 'topleft', drawMarker: true, drawPolygon: true, drawPolyline: true, drawCircle: true, drawRectangle: true, drawCircleMarker: false, editMode: true, dragMode: true, cutPolygon: true, removalMode: true, rotateMode: true });

            function toggleGeomanTools(show) {
                const container = document.querySelector('.leaflet-pm-toolbar');
                if (container) { container.style.display = show ? 'block' : 'none'; }
            }

            // Static Map Elements
            const starIcon = L.divIcon({ className: 'custom-center-icon', html: '<div style="background-color: #003366; color: #C9AB4C; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; border: 2px solid #ffffff; box-shadow: 0 2px 6px rgba(0, 51, 102, 0.4);">★</div>', iconSize: [24, 24], iconAnchor: [12, 12]});
            L.marker([__LAT__, __LON__], { icon: starIcon, zIndexOffset: 10000 }).addTo(map);
            L.circle([__LAT__, __LON__], { radius: __RADIUS__, color: "#003366", weight: 1.5, fillColor: "#003366", fillOpacity: 0.03 }).addTo(map);

            // App State
            let pts = __GEOJSON__;
            let layerConfigs = __LAYER_CONFIG__;
            let activeLayerId = __ACTIVE_LAYER__;
            let allFeatures = [];
            let scannedFeatures = []; // Separate tracking for POIs
            let selectedFeature = null;
            let ctxTargetFeature = null;
            let featureCounter = 0;
            let globalIdCounter = 0;
            
            if (layerConfigs.length === 0) {
                layerConfigs = [{ id: 'default_layer', name: 'Default Layer', visible: true, color: '#003366', fill_color: '#C9AB4C', fill_opacity: 0.4, weight: 2.0, icon_shape: 'pin', icon_size: 24 }];
                activeLayerId = 'default_layer';
            }
            
            function getLayerConfig(id) { return layerConfigs.find(l => l.id === id) || layerConfigs[0]; }
            function getActiveLayerConfig() { return getLayerConfig(activeLayerId) || layerConfigs[0]; }

            function renderVectorPinIcon(color, shape, size) {
                const baseSize = size || 24;
                let svg = shape === 'circle' 
                    ? `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${baseSize}" height="${baseSize}"><circle cx="12" cy="12" r="10" fill="${color}" stroke="#ffffff" stroke-width="2"/></svg>`
                    : `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${baseSize}" height="${baseSize}"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" fill="${color}" stroke="#ffffff" stroke-width="1.5"/></svg>`;
                return L.divIcon({ html: `<div style="display:flex;align-items:center;justify-content:center;">${svg}</div>`, className: '', iconSize: [baseSize, baseSize], iconAnchor: [baseSize/2, baseSize] });
            }

            function syncGeometryState(featObj) {
                const l = featObj.layer;
                if (featObj.type === 'circle') { featObj.data.radius = l.getRadius(); featObj.data.latlng = l.getLatLng(); } 
                else if (featObj.type === 'marker') { featObj.data.latlng = l.getLatLng(); } 
                else { featObj.data.latlngs = l.getLatLngs(); }
            }

            function updateShapeTooltip(leafletLayer, shapeType) {
                let label = '';
                try {
                    if (shapeType === 'circle') { const r = leafletLayer.getRadius(); label = r >= 1000 ? (r / 1000).toFixed(2) + ' km' : Math.round(r) + ' m'; } 
                    else if (shapeType === 'polygon' && typeof turf !== 'undefined') { const area = turf.area(leafletLayer.toGeoJSON()); label = area >= 1000000 ? (area / 1000000).toFixed(2) + ' km²' : Math.round(area) + ' m²'; } 
                    else if (shapeType === 'polyline' && typeof turf !== 'undefined') { const length = turf.length(leafletLayer.toGeoJSON(), {units: 'meters'}); label = length >= 1000 ? (length / 1000).toFixed(2) + ' km' : Math.round(length) + ' m'; }
                } catch(e) { label = ''; }
                if(!label) return;
                let centerPoint = leafletLayer.getBounds ? leafletLayer.getBounds().getCenter() : leafletLayer.getLatLng();
                if (leafletLayer._shapeTooltip) { leafletLayer._shapeTooltip.setContent(label); leafletLayer._shapeTooltip.setLatLng(centerPoint); } 
                else { leafletLayer._shapeTooltip = L.tooltip({ permanent: true, direction: 'center', className: 'shape-tooltip', offset: [0, 0] }).setContent(label).setLatLng(centerPoint).addTo(map); }
            }

            // ================== INIT POIs & FEATURES ==================
            const categoryMap = {};
            const layerGroupsRef = {};
            const catPalette = ["#003366", "#C9AB4C", "#1A5A8A", "#A8862E", "#3D7DA8", "#7A5C10", "#6A94B0", "#D4B85A", "#001F3F", "#E8D494"];
            const categoryColors = {}; 
            let colorIndex = 0;

            function initializeData() {
                // Initialize Scanned POIs
                pts.forEach(p => {
                    p._uid = globalIdCounter++;
                    const layerKey = p.type || 'Unclassified';
                    if (!categoryMap[layerKey]) { categoryMap[layerKey] = []; categoryColors[layerKey] = catPalette[colorIndex % catPalette.length]; colorIndex++; layerGroupsRef[layerKey] = L.layerGroup().addTo(map); }
                    
                    const pColor = categoryColors[layerKey];
                    const marker = L.marker([p.lat, p.lon], { icon: renderVectorPinIcon(pColor, 'pin', 24) });
                    
                    if (p.name && p.name !== 'Unknown') marker.bindTooltip(p.name, { permanent: true, direction: 'top', offset: [0, -18], className: 'poi-text-label' });
                    
                    categoryMap[layerKey].push(p);
                    marker.addTo(layerGroupsRef[layerKey]);
                    
                    // Make it an editable feature object
                    const feat = { layer: marker, type: 'marker', data: p, featureId: 'scanned_' + p._uid, isScanned: true, category: layerKey };
                    scannedFeatures.push(feat);
                    attachLifecycleHooks(marker, feat);
                });
                
                renderScanPanel();
                renderLayerPanel();
                
                if (pts.length > 0) {
                    const bounds = L.featureGroup([L.marker([__LAT__, __LON__]), ...pts.map(p => L.marker([p.lat, p.lon]))]).getBounds();
                    map.fitBounds(bounds.pad(0.1));
                }
            }

            // ================== UI RENDERING ==================
            function renderScanPanel() {
                const listBox = document.getElementById('results-list-box');
                document.getElementById('results-count').innerText = pts.length;
                let htmlPayload = '';
                const trashSvg = `<svg xmlns="http://www.w3.org/2000/svg" height="12" viewBox="0 -960 960 960" width="12"><path d="M280-120q-33 0-56.5-23.5T200-200v-520h-40v-80h200v-40h240v40h200v80h-40v520q0 33-23.5 56.5T680-120H280Zm400-600H280v520h400v-520ZM360-280h80v-360h-80v360Zm160 0h80v-360h-80v360ZM280-720v520-520Z"/></svg>`;

                Object.keys(categoryMap).forEach(catName => {
                    const count = categoryMap[catName].length;
                    if(count === 0) return;
                    const dotColor = categoryColors[catName];
                    htmlPayload += `
                        <div class="layer-category-block" id="cat-block-${catName}">
                            <div class="layer-category-header" onclick="toggleAccordionCollapse('${catName}')">
                                <div class="layer-header-left">
                                    <input type="checkbox" checked onclick="event.stopPropagation(); toggleCategoryVisibility('${catName}', this.checked)">
                                    <span class="color-dot" style="background-color: ${dotColor}; width:8px; height:8px; border-radius:50%; display:inline-block;"></span>
                                    <span>${catName} <span id="count-${catName}" style="color: #C9AB4C; font-size: 8px;">(${count})</span></span>
                                </div>
                                <span id="chevron-${catName}" style="font-size: 8px; color:#C9AB4C;">▼</span>
                            </div>
                            <div class="layer-category-items" id="items-${catName}">`;
                    categoryMap[catName].forEach(p => {
                        htmlPayload += `
                        <div class="results-item" id="res-item-${p._uid}" onclick="map.flyTo([${p.lat}, ${p.lon}], 17);">
                            <div style="flex-grow:1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${p.name || 'Unknown'}">${p.name || 'Unknown'}</div>
                            <div class="delete-poi-icon" title="Remove POI" onclick="event.stopPropagation(); removeScannedFeature(${p._uid})">${trashSvg}</div>
                        </div>`;
                    });
                    htmlPayload += '</div></div>';
                });
                listBox.innerHTML = htmlPayload;
            }

            function renderLayerPanel() {
                const listBox = document.getElementById('layer-list-box');
                const counts = {};
                allFeatures.forEach(f => { counts[f.layerId] = (counts[f.layerId] || 0) + 1; });
                
                let html = '';
                layerConfigs.forEach(lc => {
                    const count = counts[lc.id] || 0;
                    const isActive = lc.id === activeLayerId;
                    html += `
                        <div class="layer-row ${isActive ? 'active' : ''}" onclick="setActiveLayer('${lc.id}')">
                            <span class="layer-color-dot" style="background:${lc.color};"></span>
                            <span class="layer-name">${lc.name}</span>
                            <span class="layer-count">${count}</span>
                            <span class="layer-visibility" onclick="event.stopPropagation(); toggleCustomLayerVisibility('${lc.id}')">${lc.visible !== false ? '👁' : '👁‍🗨'}</span>
                        </div>`;
                });
                listBox.innerHTML = html;
                document.getElementById('layer-total-count').innerText = allFeatures.length;
            }

            // ================== TOGGLES & ACTIONS ==================
            function toggleAccordionCollapse(catKey) {
                const panel = document.getElementById('items-' + catKey);
                const chev = document.getElementById('chevron-' + catKey);
                panel.classList.toggle('collapsed');
                chev.innerText = panel.classList.contains('collapsed') ? '▲' : '▼';
            }

            function toggleCategoryVisibility(catKey, isVisible) {
                if (isVisible) map.addLayer(layerGroupsRef[catKey]);
                else map.removeLayer(layerGroupsRef[catKey]);
            }

            function toggleCustomLayerVisibility(layerId) {
                const cfg = getLayerConfig(layerId);
                if (cfg) {
                    cfg.visible = cfg.visible === false ? true : false;
                    allFeatures.forEach(f => {
                        if (f.layerId === layerId) {
                            if (cfg.visible) { map.addLayer(f.layer); if(f.layer._shapeTooltip) map.addLayer(f.layer._shapeTooltip); } 
                            else { map.removeLayer(f.layer); if(f.layer._shapeTooltip) map.removeLayer(f.layer._shapeTooltip); }
                        }
                    });
                    renderLayerPanel();
                }
            }
            function setActiveLayer(layerId) { activeLayerId = layerId; renderLayerPanel(); }

            // ================== LIFECYCLE HOOKS ==================
            function attachLifecycleHooks(leafletLayer, featureObj) {
                leafletLayer.on('contextmenu', function(e) { L.DomEvent.stopPropagation(e); ctxTargetFeature = featureObj; showContextMenu(e.originalEvent.pageX, e.originalEvent.pageY, featureObj); });
                leafletLayer.on('click', function(e) { L.DomEvent.stopPropagation(e); selectFeature(featureObj); });
                leafletLayer.on('pm:edit', function(e) { syncGeometryState(featureObj); updateShapeTooltip(leafletLayer, featureObj.type); });
                leafletLayer.on('pm:dragend', function(e) { syncGeometryState(featureObj); updateShapeTooltip(leafletLayer, featureObj.type); });
                leafletLayer.on('pm:rotateend', function(e) { syncGeometryState(featureObj); });
            }

            // ================== PROPERTIES & EDITING ==================
            function showContextMenu(x, y, feature) {
                const menu = document.getElementById('context-menu');
                document.getElementById('ctx-header').innerText = feature.data.name || 'Feature';
                menu.style.display = 'block'; menu.style.left = x + 'px'; menu.style.top = y + 'px';
            }
            function ctxEditFeature() { document.getElementById('context-menu').style.display = 'none'; if (ctxTargetFeature && ctxTargetFeature.layer.pm) { ctxTargetFeature.layer.pm.enable(); } }
            function ctxEditProperties() { document.getElementById('context-menu').style.display = 'none'; if (ctxTargetFeature) selectFeature(ctxTargetFeature); }
            function ctxDeleteFeature() { document.getElementById('context-menu').style.display = 'none'; if (ctxTargetFeature) deleteFeatureEngine(ctxTargetFeature); }

            function selectFeature(featureObj) {
                selectedFeature = featureObj;
                const d = featureObj.data;
                const isScanned = featureObj.isScanned;
                
                document.getElementById('prop-name').value = d.name || '';
                
                if(isScanned) {
                    const pColor = categoryColors[featureObj.category];
                    document.getElementById('prop-color').value = d.color || pColor;
                    document.getElementById('group-layer-select').style.display = 'none';
                    document.getElementById('group-fill-color').style.display = 'none';
                    document.getElementById('group-fill-opacity').style.display = 'none';
                    document.getElementById('group-stroke-weight').style.display = 'none';
                    document.getElementById('prop-icon-shape').value = 'pin';
                    document.getElementById('prop-icon-size').value = 24;
                } else {
                    const cfg = getLayerConfig(featureObj.layerId);
                    document.getElementById('prop-color').value = d.color || cfg.color;
                    document.getElementById('prop-fill-color').value = d.fill_color || cfg.fill_color;
                    document.getElementById('prop-fill-opacity').value = d.fill_opacity !== undefined ? d.fill_opacity : cfg.fill_opacity;
                    document.getElementById('prop-weight').value = d.weight !== undefined ? d.weight : cfg.weight;
                    document.getElementById('prop-icon-shape').value = d.icon_shape || cfg.icon_shape || 'pin';
                    document.getElementById('prop-icon-size').value = d.icon_size || cfg.icon_size || 24;
                    
                    const layerSelect = document.getElementById('prop-layer');
                    layerSelect.innerHTML = '';
                    layerConfigs.forEach(lc => { const opt = document.createElement('option'); opt.value = lc.id; opt.innerText = lc.name; if (lc.id === featureObj.layerId) opt.selected = true; layerSelect.appendChild(opt); });
                    
                    document.getElementById('group-layer-select').style.display = 'flex';
                    document.getElementById('group-fill-color').style.display = 'flex';
                    document.getElementById('group-fill-opacity').style.display = 'flex';
                    document.getElementById('group-stroke-weight').style.display = 'flex';
                }
                
                const isMarker = featureObj.type === 'marker' || featureObj.type === 'circlemarker';
                document.getElementById('group-icon-shape').style.display = isMarker ? 'flex' : 'none';
                document.getElementById('group-icon-size').style.display = isMarker ? 'flex' : 'none';
                document.getElementById('feature-properties-panel').style.display = 'flex';
            }

            function dismissPropertiesPanel() { document.getElementById('feature-properties-panel').style.display = 'none'; selectedFeature = null; }

            function commitFeatureChanges() {
                if (!selectedFeature) return;
                const f = selectedFeature; const d = f.data;
                d.name = document.getElementById('prop-name').value;
                d.color = document.getElementById('prop-color').value;
                
                if(f.isScanned) {
                    if (f.layer.setIcon) f.layer.setIcon(renderVectorPinIcon(d.color, 'pin', 24));
                    if (d.name && d.name !== 'Unknown') { f.layer.unbindTooltip(); f.layer.bindTooltip(d.name, { permanent: true, direction: 'top', offset: [0, -18], className: 'poi-text-label' }); }
                    
                    // Update list text
                    const el = document.getElementById('res-item-' + d._uid);
                    if(el) el.querySelector('div').innerText = d.name;
                    
                } else {
                    d.fill_color = document.getElementById('prop-fill-color').value;
                    d.fill_opacity = parseFloat(document.getElementById('prop-fill-opacity').value);
                    d.weight = parseFloat(document.getElementById('prop-weight').value);
                    d.icon_shape = document.getElementById('prop-icon-shape').value;
                    d.icon_size = parseInt(document.getElementById('prop-icon-size').value);
                    
                    const newLayerId = document.getElementById('prop-layer').value;
                    if (newLayerId !== f.layerId) { f.layerId = newLayerId; f.layer._layerId = newLayerId; }
                    
                    if (f.type === 'marker' || f.type === 'circlemarker') { if (f.layer.setIcon) f.layer.setIcon(renderVectorPinIcon(d.color, d.icon_shape, d.icon_size)); } 
                    else { f.layer.setStyle({ color: d.color, fillColor: d.fill_color, fillOpacity: d.fill_opacity, weight: d.weight }); }
                    renderLayerPanel();
                }
            }

            function deleteSelectedFeature() { if (selectedFeature) { deleteFeatureEngine(selectedFeature); dismissPropertiesPanel(); } }
            
            function removeScannedFeature(uid) {
                const idx = scannedFeatures.findIndex(item => item.data._uid === uid);
                if (idx > -1) { deleteFeatureEngine(scannedFeatures[idx]); }
            }

            function deleteFeatureEngine(featureObj) {
                if (featureObj.layer) {
                    map.removeLayer(featureObj.layer);
                    if (featureObj.layer._shapeTooltip) map.removeLayer(featureObj.layer._shapeTooltip);
                }
                if(featureObj.isScanned) {
                    const idx = scannedFeatures.indexOf(featureObj);
                    if (idx > -1) scannedFeatures.splice(idx, 1);
                    
                    const el = document.getElementById('res-item-' + featureObj.data._uid);
                    if(el) el.remove();
                    
                    const catKey = featureObj.category;
                    const catArr = categoryMap[catKey];
                    if(catArr) {
                        const pIdx = catArr.findIndex(p => p._uid === featureObj.data._uid);
                        if(pIdx > -1) catArr.splice(pIdx, 1);
                        const countEl = document.getElementById('count-' + catKey);
                        if(countEl) { countEl.innerText = `(${catArr.length})`; if (catArr.length === 0) document.getElementById('cat-block-' + catKey).style.display = 'none'; }
                    }
                    const totalEl = document.getElementById('results-count');
                    if(totalEl) totalEl.innerText = parseInt(totalEl.innerText) - 1;
                } else {
                    const idx = allFeatures.indexOf(featureObj);
                    if (idx > -1) allFeatures.splice(idx, 1);
                    renderLayerPanel();
                }
            }

            // ================== GEOMAN CREATION ==================
            map.on('pm:create', function(e) {
                const shape = e.shape; const layer = e.layer;
                const cfg = getActiveLayerConfig();
                const featId = 'drawn_' + featureCounter++;
                
                let data = { name: shape.charAt(0).toUpperCase() + shape.slice(1) + ' ' + featureCounter, color: cfg.color, fill_color: cfg.fill_color, fill_opacity: cfg.fill_opacity, weight: cfg.weight, icon_shape: cfg.icon_shape, icon_size: cfg.icon_size };
                let type = shape.toLowerCase();
                if (shape === 'Marker') type = 'marker'; if (shape === 'CircleMarker') type = 'circlemarker';
                if (shape === 'Circle') { type = 'circle'; data.radius = layer.getRadius(); }
                if (shape === 'Polygon' || shape === 'Rectangle') type = 'polygon';
                if (shape === 'Line' || shape === 'Polyline') type = 'polyline';
                
                if (type === 'circle' || type === 'polygon' || type === 'polyline') { layer.setStyle({ color: cfg.color, fillColor: cfg.fill_color, fillOpacity: cfg.fill_opacity, weight: cfg.weight }); } 
                else if (type === 'marker' || type === 'circlemarker') { if (layer.setIcon) layer.setIcon(renderVectorPinIcon(cfg.color, cfg.icon_shape, cfg.icon_size)); }
                
                const feat = { layer: layer, type: type, data: data, featureId: featId, layerId: activeLayerId, isScanned: false };
                layer._featureId = featId; layer._layerId = activeLayerId;
                
                allFeatures.push(feat);
                syncGeometryState(feat); updateShapeTooltip(layer, type); attachLifecycleHooks(layer, feat);
                
                renderLayerPanel(); selectFeature(feat);
            });
            
            map.on('pm:remove', function(e) {
                const layer = e.layer;
                const idx = allFeatures.findIndex(f => f.layer === layer);
                if (idx > -1) { if (allFeatures[idx].layer._shapeTooltip) map.removeLayer(allFeatures[idx].layer._shapeTooltip); allFeatures.splice(idx, 1); renderLayerPanel(); }
                
                // Check if user native deleted a Scanned POI
                const scIdx = scannedFeatures.findIndex(f => f.layer === layer);
                if (scIdx > -1) removeScannedFeature(scannedFeatures[scIdx].data._uid);
            });
            
            // Map Context Menu
            map.on('contextmenu', function(e) {
                const coordStr = e.latlng.lat.toFixed(5) + ', ' + e.latlng.lng.toFixed(5);
                const menuHtml = `
                    <div style="font-family: Montserrat, sans-serif; font-size: 9px; color: #003366; min-width: 140px;">
                        <div style="font-weight: 800; border-bottom: 1px solid #C9AB4C; padding-bottom: 4px; margin-bottom: 6px; letter-spacing: 0.5px;">MAP ACTIONS</div>
                        <div style="padding: 4px 0; cursor: pointer; font-weight: 700;" onmouseover="this.style.color='#C9AB4C'" onmouseout="this.style.color='#003366'" onclick="navigator.clipboard.writeText('${coordStr}'); map.closePopup();">Copy Coordinates</div>
                        <div style="padding: 4px 0; cursor: pointer; font-weight: 700;" onmouseover="this.style.color='#C9AB4C'" onmouseout="this.style.color='#003366'" onclick="window.open('https://www.google.com/maps?q=${e.latlng.lat},${e.latlng.lng}', '_blank'); map.closePopup();">Google Maps</div>
                    </div>`;
                L.popup().setLatLng(e.latlng).setContent(menuHtml).openOn(map);
            });
            
            window.onload = () => { initializeData(); };
        </script>
    </body>
    </html>
    """

def render_unified_map() -> None:
    """Render the single unified map module."""
    coords = parse_coordinates(st.session_state.geo_coords)
    if coords:
        lat_coord, lon_coord = coords
    else:
        lat_coord, lon_coord = DEFAULT_LAT, DEFAULT_LON

    layer_config = json.dumps(st.session_state.editor_layers)
    active_layer = st.session_state.get("active_editor_layer", "")

    geojson_escaped = escape_javascript(json.dumps(st.session_state.scanned_records))
    
    template = get_leaflet_unified_template()
    leaflet_html = (
        template.replace("__LAT__", str(lat_coord))
        .replace("__LON__", str(lon_coord))
        .replace("__RADIUS__", str(st.session_state.geo_radius))
        .replace("__GEOJSON__", geojson_escaped)
        .replace("__LAYER_CONFIG__", layer_config)
        .replace("__ACTIVE_LAYER__", json.dumps(active_layer))
    )

    st.components.v1.html(leaflet_html, height=850, scrolling=False)


# =====================================================================
# 9. MAIN APP ENTRY
# =====================================================================
def main() -> None:
    """Main application entry point."""
    init_session_state()
    apply_global_styles()
    render_sidebar()
    render_unified_map()

if __name__ == "__main__":
    main()
