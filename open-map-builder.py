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

# ========== CONFIGURATION ==========
st.set_page_config(page_title="Terraink Clone", layout="wide", page_icon="🌍")

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

FONTS = ["Roboto", "Open Sans", "Playfair Display", "Montserrat", "Lora", "Raleway", "Merriweather", "Oswald", "Nunito", "Quicksand"]

# ========== SESSION STATE INIT ==========
if "lat" not in st.session_state:
    st.session_state.lat = 48.8566
    st.session_state.lon = 2.3522
    st.session_state.location_name = "Paris, France"
if "display_name" not in st.session_state:
    st.session_state.display_name = "PARIS"
if "theme" not in st.session_state:
    st.session_state.theme = "Midnight"

# ========== HELPER FUNCTIONS ==========
@st.cache_data(show_spinner=False)
def geocode_location(query: str):
    """Convert a city/place name to coordinates."""
    geolocator = Nominatim(user_agent="terraink_clone_app")
    try:
        location = geolocator.geocode(query)
        if location:
            # Clean up the name for the poster (e.g., take the first part)
            display_name = query.split(",")[0].strip().upper()
            return location.latitude, location.longitude, location.address, display_name
    except Exception as e:
        return None
    return None

@st.cache_data(show_spinner=False)
def fetch_vector_data(lat, lon, radius=2000):
    """Fetch vector geometries from OpenStreetMap using OSMnx."""
    point = (lat, lon)
    gdfs = {}
    
    # Define tags for different layers
    tags_dict = {
        'water': {'natural': ['water', 'bay', 'coastline'], 'waterway': ['river', 'canal']},
        'parks': {'leisure': ['park', 'nature_reserve'], 'landuse': ['grass', 'recreation_ground']},
        'buildings': {'building': True},
        'roads': {'highway': True}
    }
    
    for layer, tags in tags_dict.items():
        try:
            # Only fetch buildings for a smaller radius to prevent browser freezing
            fetch_dist = radius // 2 if layer == 'buildings' else radius
            gdf = ox.features_from_point(point, tags=tags, dist=fetch_dist)
            # Filter for renderable geometries
            gdf = gdf[gdf.geometry.type.isin(['Polygon', 'MultiPolygon', 'LineString', 'MultiLineString'])]
            if not gdf.empty:
                gdfs[layer] = gdf
        except Exception:
            pass # Fail silently if no features found for a specific tag
            
    return gdfs

def generate_map(lat, lon, gdfs, theme_colors, layers, font_family, font_size, label_text, show_label):
    """Generate a Folium map utilizing custom GeoJSON styling."""
    m = folium.Map(location=[lat, lon], zoom_start=14, tiles=None, zoom_control=False)

    # 1. Custom Background Color via CSS
    bg_html = f"<style>.leaflet-container {{ background-color: {theme_colors['bg']} !important; }}</style>"
    m.get_root().html.add_child(folium.Element(bg_html))

    # 2. Add Vector Layers
    if layers['water'] and 'water' in gdfs:
        folium.GeoJson(
            gdfs['water'],
            style_function=lambda x: {'fillColor': theme_colors['water'], 'color': theme_colors['water'], 'weight': 1, 'fillOpacity': 1}
        ).add_to(m)

    if layers['parks'] and 'parks' in gdfs:
        folium.GeoJson(
            gdfs['parks'],
            style_function=lambda x: {'fillColor': theme_colors['park'], 'color': theme_colors['park'], 'weight': 1, 'fillOpacity': 1}
        ).add_to(m)

    if layers['buildings'] and 'buildings' in gdfs:
        folium.GeoJson(
            gdfs['buildings'],
            style_function=lambda x: {'fillColor': theme_colors['building'], 'color': theme_colors['building'], 'weight': 0.5, 'fillOpacity': 0.8}
        ).add_to(m)

    if layers['roads'] and 'roads' in gdfs:
        folium.GeoJson(
            gdfs['roads'],
            style_function=lambda x: {'color': theme_colors['road'], 'weight': 1.2, 'opacity': 0.9}
        ).add_to(m)

    # 3. Add Typography Overlay inside the map HTML
    if show_label:
        font_url = font_family.replace(" ", "+")
        font_import = f'<link href="https://fonts.googleapis.com/css2?family={font_url}:wght@700&display=swap" rel="stylesheet">'
        m.get_root().header.add_child(folium.Element(font_import))
        
        title_html = f'''
        <div style="position: absolute; bottom: 8%; width: 100%; text-align: center; z-index: 9999; pointer-events: none;">
            <h1 style="font-family: '{font_family}', sans-serif; font-size: {font_size}px; color: {theme_colors['text']}; margin: 0; text-transform: uppercase; letter-spacing: 0.15em; text-shadow: 0px 4px 15px rgba(0,0,0,0.3);">
                {label_text}
            </h1>
            <p style="font-family: '{font_family}', sans-serif; font-size: {max(12, int(font_size*0.3))}px; color: {theme_colors['text']}; margin-top: 5px; opacity: 0.7; letter-spacing: 0.1em;">
                {lat:.4f}° N / {lon:.4f}° E
            </p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))

    return m

def export_poster(map_object, width, height):
    """Use Selenium headless Chrome to capture the HTML map as a high-res PNG."""
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
        file_url = f"file://{os.path.abspath(map_file)}"
        driver.get(file_url)
        
        # Wait a few seconds for map tiles/GeoJSON to render fully
        time.sleep(4)
        
        png_data = driver.get_screenshot_as_png()
        driver.quit()
        os.remove(map_file)
        return png_data
    except Exception as e:
        st.error(f"Failed to generate PNG. Make sure Chrome/Chromium is installed. Error: {e}")
        return None

# ========== UI LAYOUT ==========
st.title("🗺️ Terraink Clone - Map Poster Generator")
st.markdown("Search for a city, customize the aesthetic, and download a beautiful, high-resolution cartographic poster.")

# Controls
with st.sidebar:
    st.header("1. Location")
    location_query = st.text_input("City or Region", value="Paris, France")
    
    if st.button("Search Location", use_container_width=True):
        with st.spinner("Geocoding..."):
            result = geocode_location(location_query)
            if result:
                st.session_state.lat, st.session_state.lon, st.session_state.location_name, st.session_state.display_name = result
                st.rerun()
            else:
                st.error("Location not found. Try entering coordinates directly.")
    
    # Fallback coordinate entry
    with st.expander("Manual Coordinates"):
        new_lat = st.number_input("Latitude", value=st.session_state.lat, format="%.4f")
        new_lon = st.number_input("Longitude", value=st.session_state.lon, format="%.4f")
        if st.button("Update Coordinates"):
            st.session_state.lat = new_lat
            st.session_state.lon = new_lon
            st.session_state.display_name = "CUSTOM"
            st.rerun()

    st.divider()

    st.header("2. Theme & Colors")
    selected_theme = st.selectbox("Select Preset", list(THEMES.keys()), index=0)
    
    # Custom Palette UI
    theme_colors = THEMES[selected_theme].copy()
    if selected_theme == "Custom":
        with st.expander("Customize Palette", expanded=True):
            theme_colors['bg'] = st.color_picker("Background Color", theme_colors['bg'])
            theme_colors['road'] = st.color_picker("Road Color", theme_colors['road'])
            theme_colors['water'] = st.color_picker("Water Color", theme_colors['water'])
            theme_colors['park'] = st.color_picker("Park Color", theme_colors['park'])
            theme_colors['building'] = st.color_picker("Building Color", theme_colors['building'])
            theme_colors['text'] = st.color_picker("Text Color", theme_colors['text'])

    st.divider()

    st.header("3. Map Layers")
    st.caption("Toggle vector features (may take a moment to refresh)")
    show_roads = st.checkbox("Roads", value=True)
    show_water = st.checkbox("Water bodies", value=True)
    show_parks = st.checkbox("Parks & Greens", value=True)
    show_buildings = st.checkbox("Buildings (Heavy)", value=False)
    layers_dict = {"roads": show_roads, "water": show_water, "parks": show_parks, "buildings": show_buildings}

    st.divider()

    st.header("4. Typography")
    show_label = st.checkbox("Show City Label", value=True)
    poster_title = st.text_input("Label Text", value=st.session_state.display_name)
    font_family = st.selectbox("Font Family", FONTS, index=3)
    font_size = st.slider("Font Size", 24, 120, 64)

    st.divider()

    st.header("5. Export Poster")
    export_preset = st.selectbox("Dimensions", ["Vertical (1200x1600)", "Square (1600x1600)", "Horizontal (1600x1200)"])
    if export_preset == "Vertical (1200x1600)":
        export_width, export_height = 1200, 1600
    elif export_preset == "Square (1600x1600)":
        export_width, export_height = 1600, 1600
    else:
        export_width, export_height = 1600, 1200

# Main area
col1, col2 = st.columns([1, 4])
with col2:
    st.subheader(f"Previewing: {st.session_state.location_name}")
    
    with st.spinner("Downloading vector geometries from OpenStreetMap... (This runs once per location)"):
        # Fetch data. Cached heavily based on lat/lon.
        gdfs = fetch_vector_data(st.session_state.lat, st.session_state.lon)
    
    # Generate Map
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
    
    # Display Map
    st_folium(map_obj, width=800, height=600, returned_objects=[])

with col1:
    st.info("Adjust the settings in the sidebar to customize your poster in real-time.")
    
    if st.button("📸 Generate PNG Poster", use_container_width=True, type="primary"):
        with st.spinner("Rendering high-resolution map..."):
            # Create a fresh map object specifically for export (without interactive controls)
            export_map_obj = generate_map(
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
            
            png_bytes = export_poster(export_map_obj, export_width, export_height)
            
            if png_bytes:
                st.success("Poster generated!")
                st.download_button(
                    label="⬇️ Download PNG",
                    data=png_bytes,
                    file_name=f"{poster_title.lower().replace(' ', '_')}_poster.png",
                    mime="image/png",
                    use_container_width=True
                )
