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
    "Roboto", "Open Sans", "Playfair Display", "Montserrat", "Lora", 
    "Raleway", "Merriweather", "Oswald", "Nunito", "Quicksand"
]

# ========== SESSION STATE INIT ==========
if "lat" not in st.session_state:
    st.session_state.lat = 48.8566
    st.session_state.lon = 2.3522
    st.session_state.zoom = 13
    st.session_state.location_name = "Paris, France"

# ========== HELPER FUNCTIONS ==========
@st.cache_data(ttl=3600)
def geocode_location(query: str):
    """Return (lat, lon, display_name) from Nominatim."""
    geolocator = Nominatim(user_agent="terraink_clone_app_v1")
    try:
        location = geolocator.geocode(query)
        if location:
            return location.latitude, location.longitude, location.address
    except Exception as e:
        st.error(f"Geocoding error: {e}")
    return None, None, None

def generate_map(lat, lon, zoom, theme_name, layers, show_label, font, font_size, location_name):
    """Generate a Folium map with the given parameters."""
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles=None)
    
    # Base Theme
    folium.TileLayer(THEMES[theme_name], name="Base Map").add_to(m)
    
    # Overlay Layers (Workaround for raster tiles)
    if layers.get("water"):
        folium.TileLayer('OpenSeaMap', name='Water (Sea Overlay)').add_to(m)
    
    # Layer Control
    folium.LayerControl(collapsed=False).add_to(m)
    
    # Typography Overlay (Injected into map DOM for export capture)
    if show_label:
        font_css = f"<link href='https://fonts.googleapis.com/css2?family={font.replace(' ', '+')}&display=swap' rel='stylesheet'>"
        html = f"""
        {font_css}
        <div style="position: absolute; 
                    bottom: 5%; left: 5%; 
                    background-color: rgba(255,255,255,0.85); 
                    padding: 15px 25px;
                    border-radius: 8px;
                    color: #222; 
                    font-family: '{font}', sans-serif; 
                    font-size: {font_size}px; 
                    font-weight: 700;
                    z-index: 1000;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    letter-spacing: 1px;">
            {location_name}
        </div>
        """
        m.get_root().html.add_child(Element(html))
        
    return m

def export_poster(html_content, width, height):
    """Capture the map + overlay text as a PNG image using Selenium."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except ImportError:
        st.error("Selenium not installed. Run: pip install selenium")
        return None

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument(f'--window-size={width},{height}')
    
    # Streamlit Cloud specific binary path
    if os.path.exists("/usr/bin/chromium"):
        options.binary_location = "/usr/bin/chromium"
    
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(html_content)
        temp_path = f.name
        
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(f"file://{temp_path}")
        time.sleep(4) # Wait for tiles and fonts to render
        png = driver.get_screenshot_as_png()
        driver.quit()
        return png
    except Exception as e:
        st.error(f"Export failed: {e}. Ensure Chrome/Chromium and ChromeDriver are installed in your environment.")
        return None
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

# ========== UI LAYOUT ==========
st.set_page_config(layout="wide", page_title="Terraink Clone")

with st.sidebar:
    st.title("🗺️ Terraink Clone")
    
    st.header("📍 Location")
    query = st.text_input("Search place", value="Paris, France")
    if st.button("Search"):
        with st.spinner("Geocoding..."):
            lat, lon, name = geocode_location(query)
            if lat:
                st.session_state.lat = lat
                st.session_state.lon = lon
                st.session_state.location_name = name
                st.session_state.zoom = 13
                st.rerun()
            else:
                st.error("Location not found.")
                
    st.header("🎨 Theme")
    theme = st.selectbox("Color Theme", list(THEMES.keys()), index=0)
    
    st.header("🗂️ Layers")
    # Note: Standard raster tiles bake layers. We use overlay providers where possible.
    roads = st.checkbox("Roads", value=True, help="Baked into base theme for standard OSM")
    water = st.checkbox("Water", value=True)
    parks = st.checkbox("Parks", value=True, help="Baked into base theme for standard OSM")
    buildings = st.checkbox("Buildings", value=False, help="Baked into base theme for standard OSM")
    
    st.header("🔤 Typography")
    show_label = st.checkbox("Show Label", value=True)
    font = st.selectbox("Font", FONTS, index=0)
    font_size = st.slider("Font Size", 16, 72, 36)
    
    st.header("📥 Export")
    width = st.number_input("Width (px)", value=1200, step=100)
    height = st.number_input("Height (px)", value=1600, step=100)
    export_clicked = st.button("Download Poster", type="primary")

col1, col2 = st.columns([2, 1])

with col1:
    m = generate_map(
        st.session_state.lat, st.session_state.lon, st.session_state.zoom,
        theme, {"roads": roads, "water": water, "parks": parks, "buildings": buildings},
        show_label, font, font_size, st.session_state.location_name
    )
    
    map_data = st_folium(m, width=None, height=600, returned_objects=["center", "zoom"])
    
    if map_data and map_data.get("center"):
        if map_data["center"]["lat"] != st.session_state.lat or map_data["center"]["lng"] != st.session_state.lon:
            st.session_state.lat = map_data["center"]["lat"]
            st.session_state.lon = map_data["center"]["lng"]
            st.session_state.zoom = map_data["zoom"]
            
    if export_clicked:
        with st.spinner("Generating high-res poster..."):
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
                st.download_button(
                    label="Download PNG",
                    data=png_data,
                    file_name=f"terraink_{st.session_state.location_name.replace(' ', '_')}_{width}x{height}.png",
                    mime="image/png"
                )

with col2:
    st.write(f"**Location:** {st.session_state.location_name}")
    st.write(f"**Coordinates:** {st.session_state.lat:.4f}, {st.session_state.lon:.4f}")
    st.write(f"**Zoom:** {st.session_state.zoom}")
    st.markdown("---")
    st.markdown("### ℹ️ Architecture Notes")
    st.markdown("""
    - **Layers:** Standard OSM tiles are raster. True vector layer toggling requires Mapbox/MapLibre. Overlays are used where possible.
    - **Export:** Uses headless Selenium to capture the exact map viewport at your specified resolution.
    """)
