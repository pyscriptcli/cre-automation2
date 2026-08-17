# ========== IMPORTS ==========
import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import osmnx as ox
import geopandas as gpd
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import io

# ========== PAGE CONFIGURATION ==========
st.set_page_config(
    page_title="Poster Studio",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== SESSION STATE INIT ==========
if "lat" not in st.session_state:
    st.session_state.lat = 48.8566
    st.session_state.lon = 2.3522
    st.session_state.location_name = "Paris, France"
if "display_name" not in st.session_state:
    st.session_state.display_name = "PARIS"
if "theme" not in st.session_state:
    st.session_state.theme = "Midnight"
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "ready_png" not in st.session_state:
    st.session_state.ready_png = None

# ========== CSS OVERRIDES (THE UI/UX REDESIGN) ==========
# Dynamic CSS variables based on Light/Dark mode state
THEME_VARS = """
    :root {
        --bg-main: #121212;
        --sidebar-bg: #18181B;
        --text-main: #F3F4F6;
        --text-muted: #9CA3AF;
        --border-color: #27272A;
        --card-bg: #27272A;
        --accent1: #4F46E5;
        --accent2: #7C3AED;
    }
""" if st.session_state.dark_mode else """
    :root {
        --bg-main: #F8F9FA;
        --sidebar-bg: #FFFFFF;
        --text-main: #18181B;
        --text-muted: #71717A;
        --border-color: #E4E4E7;
        --card-bg: #F4F4F5;
        --accent1: #4F46E5;
        --accent2: #7C3AED;
    }
"""

CUSTOM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

    {THEME_VARS}

    /* 1. Global Typography & Backgrounds */
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif !important;
        background-color: var(--bg-main) !important;
        color: var(--text-main) !important;
    }}

    /* 2. Hide Default Streamlit Chrome */
    header[data-testid="stHeader"] {{ display: none !important; }}
    footer {{ display: none !important; }}
    #MainMenu {{ display: none !important; }}
    [data-testid="stToolbar"] {{ display: none !important; }}
    .stDeployButton {{ display: none !important; }}

    /* 3. Studio Layout - Canvas area takes full screen without padding */
    .block-container {{
        padding: 0rem !important;
        max-width: 100% !important;
        margin: 0 !important;
    }}

    /* 4. Sidebar Styling (The Control Panel) */
    [data-testid="stSidebar"] {{
        background-color: var(--sidebar-bg) !important;
        border-right: 1px solid var(--border-color) !important;
        min-width: 380px !important;
        max-width: 380px !important;
    }}
    [data-testid="stSidebar"] > div:first-child {{
        padding-top: 2rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }}
    
    /* Sidebar Headers */
    [data-testid="stSidebar"] h3 {{
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-muted) !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 0.5rem;
    }}

    /* 5. Inputs & Widgets Styling */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {{
        background-color: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        transition: all 0.2s ease;
    }}
    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within {{
        border-color: var(--accent1) !important;
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2) !important;
    }}
    
    /* 6. Buttons Styling */
    /* Primary Buttons (Gradients, Hover animations) */
    div[data-testid="stButton"] button[kind="primary"],
    div[data-testid="stDownloadButton"] button[kind="primary"] {{
        background: linear-gradient(135deg, var(--accent1), var(--accent2)) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }}
    div[data-testid="stButton"] button[kind="primary"]:hover,
    div[data-testid="stDownloadButton"] button[kind="primary"]:hover {{
        transform: scale(1.02) !important;
        box-shadow: 0 6px 15px rgba(79, 70, 229, 0.4) !important;
    }}

    /* Secondary Buttons */
    div[data-testid="stButton"] button[kind="secondary"] {{
        background-color: var(--card-bg) !important;
        color: var(--text-main) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }}
    div[data-testid="stButton"] button[kind="secondary"]:hover {{
        border-color: var(--accent1) !important;
        color: var(--accent1) !important;
    }}

    /* 7. Sliders & Toggles */
    div[data-baseweb="slider"] div[role="slider"] {{
        background-color: var(--accent1) !important;
    }}
    div[data-baseweb="slider"] div[data-testid="stTickBar"] > div {{
        background-color: var(--accent1) !important;
    }}

    /* Make color pickers look like swatches */
    div[data-testid="stColorPicker"] {{
        background-color: transparent !important;
        justify-content: center;
    }}
    div[data-testid="stColorPicker"] > div > div {{
        border-radius: 8px !important;
        border: 1px solid var(--border-color) !important;
        overflow: hidden;
    }}

    /* Iframe Map Container styling */
    iframe {{
        border: none !important;
        display: block;
    }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ========== CONFIGURATION DATA ==========
THEMES = {
    "Midnight": {"bg": "#0f172a", "road": "#334155", "water": "#0284c7", "park": "#064e3b", "building": "#1e293b", "text": "#f8fafc"},
    "Monochrome": {"bg": "#ffffff", "road": "#000000", "water": "#cccccc", "park": "#eeeeee", "building": "#999999", "text": "#000000"},
    "Blueprint": {"bg": "#1e3a8a", "road": "#ffffff", "water": "#1d4ed8", "park": "#3b82f6", "building": "#60a5fa", "text": "#ffffff"},
    "Vintage": {"bg": "#fef3c7", "road": "#78350f", "water": "#93c5fd", "park": "#d9f99d", "building": "#fde68a", "text": "#451a03"},
    "Forest": {"bg": "#022c22", "road": "#166534", "water": "#0369a1", "park": "#047857", "building": "#064e3b", "text": "#ecfccb"},
    "Coral": {"bg": "#fff1f2", "road": "#be123c", "water": "#fda4af", "park": "#fecdd3", "building": "#ffe4e6", "text": "#881337"},
    "Cyberpunk": {"bg": "#000000", "road": "#ec4899", "water": "#06b6d4", "park": "#3b0764", "building": "#172554", "text": "#fde047"},
    "Sandstone": {"bg": "#f5f5f4", "road": "#a8a29e", "water": "#bae6fd", "park": "#d1fae5", "building": "#e7e5e4", "text": "#44403c"},
    "Lavender": {"bg": "#faf5ff", "road": "#9333ea", "water": "#c084fc", "park": "#e9d5ff", "building": "#f3e8ff", "text": "#581c87"},
    "Gold": {"bg": "#111827", "road": "#fbbf24", "water": "#1f2937", "park": "#374151", "building": "#4b5563", "text": "#fcd34d"},
    "Custom": {"bg": "#ffffff", "road": "#000000", "water": "#aadaff", "park": "#c8facc", "building": "#e0e0e0", "text": "#000000"},
}

FONTS = ["Roboto", "Inter", "Playfair Display", "Montserrat", "Lora", "Raleway", "Merriweather", "Oswald", "Nunito", "Cormorant Garamond"]

# ========== BACKEND LOGIC (UNCHANGED FUNCTIONALITY) ==========
@st.cache_data(show_spinner=False)
def geocode_location(query: str):
    geolocator = Nominatim(user_agent="terraink_studio_app")
    try:
        location = geolocator.geocode(query)
        if location:
            display_name = query.split(",")[0].strip().upper()
            return location.latitude, location.longitude, location.address, display_name
    except Exception:
        return None
    return None

@st.cache_data(show_spinner=False)
def fetch_vector_data(lat, lon, radius=2000):
    point = (lat, lon)
    gdfs = {}
    tags_dict = {
        'water': {'natural': ['water', 'bay', 'coastline'], 'waterway': ['river', 'canal']},
        'parks': {'leisure': ['park', 'nature_reserve'], 'landuse': ['grass', 'recreation_ground']},
        'buildings': {'building': True},
        'roads': {'highway': True}
    }
    for layer, tags in tags_dict.items():
        try:
            fetch_dist = radius // 2 if layer == 'buildings' else radius
            gdf = ox.features_from_point(point, tags=tags, dist=fetch_dist)
            gdf = gdf[gdf.geometry.type.isin(['Polygon', 'MultiPolygon', 'LineString', 'MultiLineString'])]
            if not gdf.empty:
                gdfs[layer] = gdf
        except Exception:
            pass 
    return gdfs

def generate_map(lat, lon, gdfs, theme_colors, layers, font_family, font_size, label_text, show_label):
    m = folium.Map(location=[lat, lon], zoom_start=14, tiles=None, zoom_control=False)

    bg_html = f"<style>.leaflet-container {{ background-color: {theme_colors['bg']} !important; }}</style>"
    m.get_root().html.add_child(folium.Element(bg_html))

    if layers['water'] and 'water' in gdfs:
        folium.GeoJson(gdfs['water'], style_function=lambda x: {'fillColor': theme_colors['water'], 'color': theme_colors['water'], 'weight': 1, 'fillOpacity': 1}).add_to(m)
    if layers['parks'] and 'parks' in gdfs:
        folium.GeoJson(gdfs['parks'], style_function=lambda x: {'fillColor': theme_colors['park'], 'color': theme_colors['park'], 'weight': 1, 'fillOpacity': 1}).add_to(m)
    if layers['buildings'] and 'buildings' in gdfs:
        folium.GeoJson(gdfs['buildings'], style_function=lambda x: {'fillColor': theme_colors['building'], 'color': theme_colors['building'], 'weight': 0.5, 'fillOpacity': 0.8}).add_to(m)
    if layers['roads'] and 'roads' in gdfs:
        folium.GeoJson(gdfs['roads'], style_function=lambda x: {'color': theme_colors['road'], 'weight': 1.2, 'opacity': 0.9}).add_to(m)

    if show_label:
        font_url = font_family.replace(" ", "+")
        font_import = f'<link href="https://fonts.googleapis.com/css2?family={font_url}:wght@400;600;700&display=swap" rel="stylesheet">'
        m.get_root().header.add_child(folium.Element(font_import))
        
        # UI REDESIGN: Added glass-morphism, backdrop-filter, and elegant typography to the poster title
        title_html = f'''
        <div style="position: absolute; bottom: 50px; left: 50%; transform: translateX(-50%); z-index: 9999; pointer-events: none;
                    background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
                    padding: 24px 48px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.1);
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2); text-align: center;">
            <h1 style="font-family: '{font_family}', serif; font-size: {font_size}px; color: {theme_colors['text']}; margin: 0; 
                       text-transform: uppercase; letter-spacing: 0.15em; text-shadow: 0px 4px 12px rgba(0,0,0,0.4); font-weight: 700;">
                {label_text}
            </h1>
            <p style="font-family: 'Inter', sans-serif; font-size: {max(12, int(font_size*0.25))}px; color: {theme_colors['text']}; 
                      margin-top: 8px; margin-bottom: 0; opacity: 0.85; letter-spacing: 0.25em; text-shadow: 0px 2px 4px rgba(0,0,0,0.5);">
                {lat:.4f}° N / {lon:.4f}° E
            </p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))

    return m

def export_poster(map_object, width, height):
    map_file = "temp_poster_map.html"
    map_object.save(map_file)
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--hide-scrollbars")
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_window_size(width, height)
        driver.get(f"file://{os.path.abspath(map_file)}")
        time.sleep(4)
        png_data = driver.get_screenshot_as_png()
        driver.quit()
        os.remove(map_file)
        return png_data
    except Exception as e:
        return None

# ========== STUDIO UI LAYOUT ==========
with st.sidebar:
    # Studio Brand Header & Theme Toggle
    col_brand, col_theme = st.columns([3, 1])
    with col_brand:
        st.markdown("<h2 style='margin:0; font-weight:700; font-family:\"Inter\", sans-serif;'>Poster Studio</h2>", unsafe_allow_html=True)
        st.markdown("<p style='margin:0; font-size:0.8rem; color:var(--text-muted);'>Map Forge Engine</p>", unsafe_allow_html=True)
    with col_theme:
        # Native toggle handles dark mode switching instantly via session state binding
        st.toggle("☾", key="dark_mode", help="Toggle Light/Dark Mode")
    
    st.markdown("<br>", unsafe_allow_html=True)

    # 1. Location Settings
    st.markdown("### 📍 Location")
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        location_query = st.text_input("Search Location", value="Paris, France", label_visibility="collapsed", placeholder="Enter city name...")
    with col_btn:
        search_clicked = st.button("🌍", use_container_width=True)
    
    if search_clicked:
        with st.spinner("Locating..."):
            result = geocode_location(location_query)
            if result:
                st.session_state.lat, st.session_state.lon, st.session_state.location_name, st.session_state.display_name = result
                st.session_state.ready_png = None # Reset export when location changes
                st.rerun()
            else:
                st.error("Location not found.")
    
    # Coordinates Helper Text
    st.markdown(f"<div style='font-family: monospace; font-size: 0.75rem; color: var(--text-muted); margin-top:-10px; padding-bottom: 10px;'>Current: {st.session_state.lat:.4f}, {st.session_state.lon:.4f}</div>", unsafe_allow_html=True)

    # 2. Theme & Colors Settings
    st.markdown("### 🎨 Theme & Colors")
    selected_theme = st.selectbox("Palette Preset", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state.theme))
    st.session_state.theme = selected_theme
    
    theme_colors = THEMES[selected_theme].copy()
    if selected_theme == "Custom":
        st.markdown("<div style='font-size: 0.85rem; color: var(--text-muted); margin-bottom: 10px;'>Define Custom Colors</div>", unsafe_allow_html=True)
        col_c1, col_c2, col_c3 = st.columns(3)
        theme_colors['bg'] = col_c1.color_picker("Back", theme_colors['bg'])
        theme_colors['road'] = col_c2.color_picker("Roads", theme_colors['road'])
        theme_colors['water'] = col_c3.color_picker("Water", theme_colors['water'])
        
        col_c4, col_c5, col_c6 = st.columns(3)
        theme_colors['park'] = col_c4.color_picker("Parks", theme_colors['park'])
        theme_colors['building'] = col_c5.color_picker("Buildings", theme_colors['building'])
        theme_colors['text'] = col_c6.color_picker("Text", theme_colors['text'])

    # 3. Map Layers (Using native st.toggle for iOS-style pill switches)
    st.markdown("### 🗺️ Map Layers")
    l_col1, l_col2 = st.columns(2)
    with l_col1:
        show_roads = st.toggle("Roads", value=True)
        show_water = st.toggle("Water", value=True)
    with l_col2:
        show_parks = st.toggle("Parks", value=True)
        show_buildings = st.toggle("Buildings", value=False)
    layers_dict = {"roads": show_roads, "water": show_water, "parks": show_parks, "buildings": show_buildings}

    # 4. Typography Settings
    st.markdown("### ✍️ Typography")
    show_label = st.toggle("Show Poster Title", value=True)
    if show_label:
        poster_title = st.text_input("Label Text", value=st.session_state.display_name, label_visibility="collapsed")
        font_family = st.selectbox("Font Style", FONTS, index=2)
        font_size = st.slider("Font Size", 24, 120, 72)
    else:
        poster_title, font_family, font_size = "", FONTS[0], 24

    # 5. Export Settings
    st.markdown("### 📸 Export")
    export_preset = st.selectbox("Print Dimensions", ["Vertical (1200x1600)", "Square (1600x1600)", "Horizontal (1600x1200)"])
    if export_preset == "Vertical (1200x1600)":
        export_width, export_height = 1200, 1600
    elif export_preset == "Square (1600x1600)":
        export_width, export_height = 1600, 1600
    else:
        export_width, export_height = 1600, 1200

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Export Generation Flow
    if st.button("✨ Generate High-Res Poster", type="primary", use_container_width=True):
        with st.spinner("Rendering canvas... (5-10s)"):
            export_map_obj = generate_map(
                st.session_state.lat, st.session_state.lon, 
                fetch_vector_data(st.session_state.lat, st.session_state.lon), 
                theme_colors, layers_dict, font_family, font_size, poster_title, show_label
            )
            png_bytes = export_poster(export_map_obj, export_width, export_height)
            if png_bytes:
                st.session_state.ready_png = png_bytes
                st.toast("Poster generated successfully!", icon="🎉")
            else:
                st.error("Export failed. Please check environment dependencies.")

    # Show Download Button only when PNG is ready in memory
    if st.session_state.ready_png is not None:
        filename = f"{st.session_state.display_name.lower().replace(' ', '_')}_poster.png"
        st.download_button(
            label="⬇️ Download PNG File",
            data=st.session_state.ready_png,
            file_name=filename,
            mime="image/png",
            type="primary",
            use_container_width=True
        )

# ========== MAIN CANVAS AREA ==========
# Fetch vector data for the preview
with st.spinner("Loading vector geometry from OpenStreetMap..."):
    gdfs = fetch_vector_data(st.session_state.lat, st.session_state.lon)

# Generate Live Preview Map
map_obj = generate_map(
    st.session_state.lat, 
    st.session_state.lon, 
    gdfs, 
    theme_colors, 
    layers_dict, 
    font_family, 
    font_size,
    poster_title,
    show_label
)

# Render Full-Screen Canvas (Height is set dynamically large to cover standard screens)
st_folium(map_obj, use_container_width=True, height=1200, returned_objects=[])
