import streamlit as st
import folium
from streamlit_folium import st_folium
from folium import Element
from geopy.geocoders import Nominatim
import tempfile
import os
import time

# ========== CONFIGURATION ==========
THEMES = {
    "Standard (OSM)": "OpenStreetMap",
    "Midnight": "CartoDB dark_matter",
    "Monochrome": "CartoDB positron",
    "Explorer": "CartoDB voyager",
    "Satellite": "Esri World Imagery",
    "Oceanic": "Esri Ocean Basemap",
    "National Geo": "Esri NatGeoWorldMap",
    "Topographic": "OpenTopoMap",
    "Light Map": "CartoDB positron",
    "Dark Map": "CartoDB dark_matter"
}

FONTS = [
    "Playfair Display", "Cormorant Garamond", "Roboto", "Open Sans", "Montserrat", 
    "Lora", "Raleway", "Merriweather", "Oswald", "Nunito", "Quicksand"
]

# ========== PAGE CONFIG ==========
st.set_page_config(page_title="Poster Studio", page_icon="🎨", layout="wide", initial_sidebar_state="expanded")

# ========== SESSION STATE INIT ==========
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "lat" not in st.session_state:
    st.session_state.lat = 48.8566
    st.session_state.lon = 2.3522
    st.session_state.zoom = 13
    st.session_state.location_name = "Paris, France"
    st.session_state.query = "Paris, France"

# ========== CSS INJECTION ==========
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;700&family=Cormorant+Garamond:wght@400;600&display=swap');

    :root {
        --bg-primary: #0f172a;
        --bg-secondary: #1e293b;
        --bg-tertiary: #334155;
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --accent-primary: #6366f1;
        --accent-secondary: #8b5cf6;
        --border-color: #334155;
        --card-bg: #1e293b;
    }

    /* Hide Streamlit Chrome */
    #MainMenu, footer, header[data-testid="stHeader"] {
        display: none !important;
    }

    /* Keep Sidebar Toggle Button but style it as a floating pill */
    [data-testid="collapsedControl"] {
        display: flex !important;
        position: fixed !important;
        top: 20px !important;
        left: 20px !important;
        z-index: 9999 !important;
        background-color: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        padding: 6px !important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2) !important;
    }
    [data-testid="collapsedControl"] svg {
        fill: var(--text-primary) !important;
        width: 20px !important;
        height: 20px !important;
    }

    /* Global Typography */
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif !important;
        color: var(--text-primary) !important;
    }

    /* App Background */
    .stApp {
        background-color: var(--bg-primary) !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        width: 360px !important;
        background-color: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-color) !important;
    }
    
    section[data-testid="stSidebar"] > div {
        padding: 2rem 1.5rem !important;
        padding-top: 5rem !important; /* Space for fixed toggle button */
    }

    /* Main Content Adjustment */
    .main .block-container {
        padding-top: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }

    /* Cards / Containers */
    .control-card {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .card-header {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--text-secondary);
        margin-bottom: 1.25rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Inputs & Widgets */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: var(--bg-tertiary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        transition: all 0.2s ease;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
    }

    /* Buttons */
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.4) !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 8px -1px rgba(99, 102, 241, 0.5) !important;
    }

    .stButton button[kind="secondary"] {
        background-color: transparent !important;
        color: var(--accent-primary) !important;
        border: 1px solid var(--accent-primary) !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }

    /* Toggle Switches */
    .stToggle div[data-baseweb="toggle"] {
        background-color: var(--bg-tertiary) !important;
    }
    .stToggle div[data-baseweb="toggle"][aria-checked="true"] {
        background-color: var(--accent-primary) !important;
    }

    /* Map Canvas Styling */
    iframe {
        border-radius: 16px !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2) !important;
        height: calc(100vh - 140px) !important;
    }

    /* Typography Preview */
    .font-preview {
        font-family: var(--preview-font), serif;
        font-size: 1.5rem;
        color: var(--text-primary);
        margin-top: 0.5rem;
        margin-bottom: 1rem;
        padding: 0.75rem;
        background: var(--bg-tertiary);
        border-radius: 8px;
        text-align: center;
        border: 1px solid var(--border-color);
    }

    /* Coordinate Helper Text */
    .coord-text {
        font-family: 'Courier New', monospace;
        font-size: 0.75rem;
        color: var(--text-secondary);
        margin-top: -0.5rem;
        margin-bottom: 1.5rem;
        background: var(--bg-tertiary);
        padding: 4px 8px;
        border-radius: 4px;
        display: inline-block;
    }
    
    /* Download Button Special Styling */
    .download-section {
        margin-top: 2rem;
        padding-top: 2rem;
        border-top: 1px solid var(--border-color);
    }
    
    .download-section .stButton button {
        width: 100%;
        padding: 1rem !important;
        font-size: 1.1rem !important;
    }
    
    /* Top Bar Logo */
    .top-bar-logo {
        font-family: 'Playfair Display', serif;
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-primary);
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-left: 40px; /* Space for toggle button */
    }
    
    .top-bar-controls {
        display: flex;
        justify-content: flex-end;
        align-items: center;
    }

</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Light Mode Override
if not st.session_state.dark_mode:
    LIGHT_MODE_CSS = """
    <style>
    :root {
        --bg-primary: #ffffff;
        --bg-secondary: #f8fafc;
        --bg-tertiary: #e2e8f0;
        --text-primary: #0f172a;
        --text-secondary: #64748b;
        --accent-primary: #4f46e5;
        --accent-secondary: #7c3aed;
        --border-color: #cbd5e1;
        --card-bg: #ffffff;
    }
    </style>
    """
    st.markdown(LIGHT_MODE_CSS, unsafe_allow_html=True)

# ========== HELPER FUNCTIONS (UNCHANGED BACKEND) ==========
@st.cache_data(ttl=3600)
def geocode_location(query: str):
    geolocator = Nominatim(user_agent="terraink_clone_app_v2_ui")
    try:
        location = geolocator.geocode(query)
        if location:
            return location.latitude, location.longitude, location.address
    except Exception as e:
        st.error(f"Geocoding error: {e}")
    return None, None, None

def generate_map(lat, lon, zoom, theme_name, layers, show_label, font, font_size, location_name):
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles=None)
    folium.TileLayer(THEMES[theme_name], name="Base Map").add_to(m)
    if layers.get("water"):
        folium.TileLayer('OpenSeaMap', name='Water (Sea Overlay)').add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    
    if show_label:
        font_css = f"<link href='https://fonts.googleapis.com/css2?family={font.replace(' ', '+')}:wght@700&display=swap' rel='stylesheet'>"
        html = f"""
        {font_css}
        <div style="position: absolute; 
                    bottom: 8%; left: 50%; 
                    transform: translateX(-50%);
                    background: rgba(255, 255, 255, 0.15);
                    backdrop-filter: blur(12px);
                    -webkit-backdrop-filter: blur(12px);
                    padding: 16px 32px;
                    border-radius: 16px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    color: #ffffff; 
                    font-family: '{font}', serif; 
                    font-size: {font_size}px; 
                    font-weight: 700;
                    z-index: 1000;
                    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
                    text-shadow: 0 2px 4px rgba(0,0,0,0.5);
                    letter-spacing: 1.5px;
                    text-transform: uppercase;">
            {location_name}
        </div>
        """
        m.get_root().html.add_child(Element(html))
    return m

def export_poster(html_content, width, height):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except ImportError:
        st.error("Selenium not installed.")
        return None

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument(f'--window-size={width},{height}')
    
    if os.path.exists("/usr/bin/chromium"):
        options.binary_location = "/usr/bin/chromium"
    
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(html_content)
        temp_path = f.name
        
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(f"file://{temp_path}")
        time.sleep(4)
        png = driver.get_screenshot_as_png()
        driver.quit()
        return png
    except Exception as e:
        st.error(f"Export failed: {e}")
        return None
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

# ========== UI LAYOUT ==========

# Top Bar
top_col1, top_col2 = st.columns([8, 2])
with top_col1:
    st.markdown("<div class='top-bar-logo'>🎨 Poster Studio</div>", unsafe_allow_html=True)
with top_col2:
    st.markdown("<div class='top-bar-controls'>", unsafe_allow_html=True)
    dark_mode = st.toggle("Dark Mode", value=st.session_state.dark_mode, key="theme_toggle")
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr style='margin: 1rem 0 2rem 0; border-color: var(--border-color); opacity: 0.3;'>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("<div class='card-header'>📍 LOCATION</div>", unsafe_allow_html=True)
    search_col1, search_col2 = st.columns([4, 1])
    with search_col1:
        query = st.text_input("Search", value=st.session_state.query, label_visibility="collapsed", placeholder="Search for a place...")
    with search_col2:
        search_btn = st.button("🌍", use_container_width=True, help="Search Location")
        
    st.markdown(f"<div class='coord-text'>Lat: {st.session_state.lat:.4f}, Lon: {st.session_state.lon:.4f}</div>", unsafe_allow_html=True)
    
    if search_btn:
        with st.spinner("Searching..."):
            lat, lon, name = geocode_location(query)
            if lat:
                st.session_state.lat = lat
                st.session_state.lon = lon
                st.session_state.location_name = name
                st.session_state.query = query
                st.session_state.zoom = 13
                st.toast(f"Found: {name}", icon="📍")
                st.rerun()
            else:
                st.warning("Location not found. Try a different search term.")

    st.markdown("<div class='control-card'><div class='card-header'>🎨 THEME & COLORS</div>", unsafe_allow_html=True)
    theme = st.selectbox("Map Style", list(THEMES.keys()))
    c1, c2 = st.columns(2)
    with c1:
        road_color = st.color_picker("Roads", "#ffffff")
        water_color = st.color_picker("Water", "#000000")
    with c2:
        park_color = st.color_picker("Parks", "#000000")
        bldg_color = st.color_picker("Buildings", "#000000")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='control-card'><div class='card-header'>🗺️ MAP LAYERS</div>", unsafe_allow_html=True)
    roads = st.toggle("Roads", value=True)
    water = st.toggle("Water", value=True)
    parks = st.toggle("Parks", value=True)
    buildings = st.toggle("Buildings", value=False)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='control-card'><div class='card-header'>✍️ TYPOGRAPHY</div>", unsafe_allow_html=True)
    show_label = st.toggle("Show Title", value=True)
    font = st.selectbox("Font Family", FONTS)
    st.markdown(f"<div class='font-preview' style='--preview-font: \"{font}\"'>{st.session_state.location_name}</div>", unsafe_allow_html=True)
    font_size = st.slider("Size", 16, 72, 36)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='download-section'><div class='card-header'>📸 EXPORT</div>", unsafe_allow_html=True)
    exp_c1, exp_c2 = st.columns(2)
    with exp_c1: width = st.number_input("W", value=1200, step=100)
    with exp_c2: height = st.number_input("H", value=1600, step=100)
    export_clicked = st.button("⬇️ Download High-Res Poster", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Main Canvas
map_obj = generate_map(
    st.session_state.lat, st.session_state.lon, st.session_state.zoom,
    theme, {"roads": roads, "water": water, "parks": parks, "buildings": buildings},
    show_label, font, font_size, st.session_state.location_name
)

map_data = st_folium(map_obj, width=None, height=800, returned_objects=["center", "zoom"])

if map_data and map_data.get("center"):
    if map_data["center"]["lat"] != st.session_state.lat or map_data["center"]["lng"] != st.session_state.lon:
        st.session_state.lat = map_data["center"]["lat"]
        st.session_state.lon = map_data["center"]["lng"]
        st.session_state.zoom = map_data["zoom"]
        
if export_clicked:
    with st.spinner("Rendering your poster..."):
        export_m = generate_map(
            st.session_state.lat, st.session_state.lon, st.session_state.zoom,
            theme, {"roads": roads, "water": water, "parks": parks, "buildings": buildings},
            show_label, font, font_size, st.session_state.location_name
        )
        export_m.get_root().width = f"{width}px"
        export_m.get_root().height = f"{height}px"
        
        html_str = export_m.get_root().render()
        png_data = export_poster(html_str, width, height)
        
        if png_data:
            st.toast("Poster ready! Downloading...", icon="✅")
            st.download_button(
                label="Click here to save your PNG",
                data=png_data,
                file_name=f"poster_{st.session_state.location_name.replace(' ', '_')}_{width}x{height}.png",
                mime="image/png",
                type="primary",
                use_container_width=True
            )
