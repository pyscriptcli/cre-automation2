# ========== IMPORTS ==========
import streamlit as st
import folium
from streamlit_folium import folium_static
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import requests
import json
import time
import os
import tempfile
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException
import streamlit.components.v1 as components

# ========== CONFIGURATION ==========

# 12 curated themes: each defines CSS filter values for base tiles
# and colors for overlays (water, park, building, road, background, text)
THEMES = {
    "Carrara": {
        "filter": "brightness(1.05) contrast(1.0) saturate(0.9) hue-rotate(0deg) sepia(0.1)",
        "colors": {"water": "#4a90d9", "park": "#6b8e23", "building": "#d3c5b0", "road": "#b0a090", "bg": "#f5f0eb", "text": "#3a2e25"}
    },
    "Blush": {
        "filter": "brightness(1.1) contrast(0.95) saturate(1.1) hue-rotate(-10deg) sepia(0.15)",
        "colors": {"water": "#9fc7d9", "park": "#d9b8a8", "building": "#e8d5c4", "road": "#c4b0a0", "bg": "#f9ede8", "text": "#5a3e3a"}
    },
    "Sandstone": {
        "filter": "brightness(0.95) contrast(1.1) saturate(0.8) hue-rotate(0deg) sepia(0.3)",
        "colors": {"water": "#8a9ba8", "park": "#a89878", "building": "#d4c4a8", "road": "#b8a890", "bg": "#f0e8d8", "text": "#4a3e2a"}
    },
    "Midnight": {
        "filter": "brightness(0.6) contrast(1.2) saturate(0.7) hue-rotate(180deg) sepia(0.0)",
        "colors": {"water": "#1a2a4a", "park": "#2a3a2a", "building": "#3a3a4a", "road": "#4a4a5a", "bg": "#1a1a2a", "text": "#e0e0f0"}
    },
    "Forest": {
        "filter": "brightness(0.9) contrast(1.0) saturate(1.2) hue-rotate(90deg) sepia(0.1)",
        "colors": {"water": "#2a6a6a", "park": "#3a8a3a", "building": "#6a7a5a", "road": "#7a8a6a", "bg": "#e8f0e0", "text": "#2a3a1a"}
    },
    "Ocean": {
        "filter": "brightness(0.95) contrast(1.0) saturate(1.3) hue-rotate(200deg) sepia(0.0)",
        "colors": {"water": "#1a5a8a", "park": "#3a7a6a", "building": "#8aa0b0", "road": "#6a8a9a", "bg": "#e8f0f8", "text": "#0a2a3a"}
    },
    "Monochrome": {
        "filter": "brightness(1.0) contrast(1.1) saturate(0.0) hue-rotate(0deg) sepia(0.0)",
        "colors": {"water": "#888888", "park": "#aaaaaa", "building": "#cccccc", "road": "#999999", "bg": "#f0f0f0", "text": "#222222"}
    },
    "Vintage": {
        "filter": "brightness(0.9) contrast(0.9) saturate(0.8) hue-rotate(0deg) sepia(0.6)",
        "colors": {"water": "#8a7a5a", "park": "#9a8a5a", "building": "#c4b08a", "road": "#a89878", "bg": "#f0e8d0", "text": "#4a3a2a"}
    },
    "Warm": {
        "filter": "brightness(1.0) contrast(1.0) saturate(1.1) hue-rotate(20deg) sepia(0.1)",
        "colors": {"water": "#c47a4a", "park": "#d4a04a", "building": "#e8c8a0", "road": "#d4b090", "bg": "#faf0e0", "text": "#4a2a1a"}
    },
    "Cool": {
        "filter": "brightness(1.0) contrast(1.0) saturate(1.1) hue-rotate(-30deg) sepia(0.0)",
        "colors": {"water": "#5a7a9a", "park": "#6a9a8a", "building": "#a0b8c8", "road": "#8aa0b0", "bg": "#e8f0f8", "text": "#1a2a3a"}
    },
    "Moss": {
        "filter": "brightness(0.9) contrast(1.05) saturate(1.0) hue-rotate(60deg) sepia(0.2)",
        "colors": {"water": "#4a7a5a", "park": "#5a8a3a", "building": "#8a9a6a", "road": "#7a8a5a", "bg": "#eaf0e0", "text": "#2a3a1a"}
    },
    "Terracotta": {
        "filter": "brightness(1.0) contrast(1.0) saturate(1.2) hue-rotate(-10deg) sepia(0.25)",
        "colors": {"water": "#8a6a5a", "park": "#b08a5a", "building": "#d4b090", "road": "#c4a080", "bg": "#f5ede0", "text": "#4a2a1a"}
    }
}

# Google Fonts (10+)
FONTS = [
    "Roboto", "Open Sans", "Playfair Display", "Montserrat", "Lora",
    "Raleway", "Merriweather", "Oswald", "Nunito", "Quicksand",
    "Poppins", "Lato", "PT Sans", "Source Sans Pro"
]

# Map layers toggles
LAYERS = ["Water", "Parks", "Buildings", "Roads"]

# ========== SESSION STATE INIT ==========
def init_session_state():
    defaults = {
        "lat": 48.8566,
        "lon": 2.3522,
        "location_name": "Paris, France",
        "theme": "Midnight",
        "show_water": True,
        "show_parks": True,
        "show_buildings": False,
        "show_roads": False,
        "show_label": True,
        "font": "Playfair Display",
        "font_size": 36,
        "zoom": 12,
        "osm_data": None,  # cached GeoJSON features
        "map_html": None,  # cached HTML for export
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session_state()

# ========== HELPER FUNCTIONS ==========

@st.cache_data(ttl=86400, show_spinner=False)
def geocode_location(query: str) -> tuple:
    """Return (lat, lon, display_name) using Nominatim, with manual coordinate fallback."""
    # Try manual coordinate parse
    coord_pattern = r"^\s*([-+]?\d*\.?\d+)\s*[,;]\s*([-+]?\d*\.?\d+)\s*$"
    match = re.match(coord_pattern, query.strip())
    if match:
        lat = float(match.group(1))
        lon = float(match.group(2))
        return lat, lon, f"{lat:.4f}, {lon:.4f} (manual)"

    # Use Nominatim
    geolocator = Nominatim(user_agent="terraink_clone")
    try:
        location = geolocator.geocode(query, timeout=10)
        if location:
            return location.latitude, location.longitude, location.address
        else:
            st.error(f"Location '{query}' not found. Please try a different name or enter coordinates.")
            return None, None, None
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        st.error(f"Geocoding service unavailable: {e}. Please enter coordinates manually.")
        return None, None, None

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_osm_features(lat, lon, radius=5000):
    """Query Overpass API for water, parks, buildings, roads within a bounding box."""
    # Build bounding box (approx 0.05° per 5 km)
    delta = 0.05 * (radius / 5000.0)
    bbox = (lon - delta, lat - delta, lon + delta, lat + delta)
    bbox_str = f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}"

    # Define queries for each feature type
    queries = {
        "water": f"""
            [out:json][timeout:25];
            (way["natural"="water"]({bbox_str});
             way["waterway"]({bbox_str});
             relation["natural"="water"]({bbox_str}););
            out body;>;
        """,
        "parks": f"""
            [out:json][timeout:25];
            (way["leisure"="park"]({bbox_str});
             way["landuse"="recreation_ground"]({bbox_str});
             way["leisure"="garden"]({bbox_str}););
            out body;>;
        """,
        "buildings": f"""
            [out:json][timeout:25];
            (way["building"]({bbox_str});
             way["building:part"]({bbox_str}););
            out body;>;
        """,
        "roads": f"""
            [out:json][timeout:25];
            (way["highway"]({bbox_str}););
            out body;>;
        """
    }

    results = {}
    for key, query in queries.items():
        try:
            response = requests.post(
                "https://overpass-api.de/api/interpreter",
                data={"data": query},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                # Convert to GeoJSON-like features
                features = []
                for element in data.get("elements", []):
                    if element["type"] == "way" and "geometry" in element:
                        # Simple conversion: list of lat,lon pairs -> GeoJSON LineString or Polygon
                        coords = [[p["lon"], p["lat"]] for p in element["geometry"]]
                        if element.get("tags", {}).get("area") == "yes" or key in ["water", "parks", "buildings"]:
                            # Treat as polygon (closed)
                            if len(coords) > 2 and coords[0] != coords[-1]:
                                coords.append(coords[0])
                            geom_type = "Polygon"
                            geometry = [coords]
                        else:
                            geom_type = "LineString"
                            geometry = coords
                        features.append({
                            "type": "Feature",
                            "geometry": {
                                "type": geom_type,
                                "coordinates": geometry
                            },
                            "properties": element.get("tags", {})
                        })
                results[key] = features
            else:
                results[key] = []
        except Exception as e:
            st.warning(f"Could not fetch {key} data: {e}")
            results[key] = []
    return results

def generate_map(lat, lon, zoom, theme_name, show_water, show_parks, show_buildings, show_roads):
    """Generate a Folium map with tile filter and overlay features."""
    theme = THEMES[theme_name]
    colors = theme["colors"]
    filter_val = theme["filter"]

    # Create base map
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles=None)

    # Add OpenStreetMap tile layer with custom CSS filter
    tile = folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        name="OSM",
        overlay=False,
        control=False
    )
    tile.add_to(m)

    # Inject CSS filter via custom JavaScript
    filter_js = f"""
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var tileContainer = document.querySelector('.leaflet-tile-pane');
            if (tileContainer) {{
                tileContainer.style.filter = "{filter_val}";
            }}
        }});
        </script>
    """
    m.get_root().html.add_child(folium.Element(filter_js))

    # Fetch OSM features if not cached
    if st.session_state.osm_data is None:
        with st.spinner("Fetching map features..."):
            st.session_state.osm_data = fetch_osm_features(lat, lon)
    osm_data = st.session_state.osm_data

    # Add feature overlays
    feature_groups = {}

    # Water
    if show_water and osm_data.get("water"):
        fg_water = folium.FeatureGroup(name="Water", show=True)
        for feat in osm_data["water"]:
            geom = feat["geometry"]
            if geom["type"] == "Polygon":
                folium.GeoJson(
                    feat,
                    style_function=lambda x, color=colors["water"]: {
                        "fillColor": color,
                        "color": color,
                        "weight": 1,
                        "fillOpacity": 0.6
                    }
                ).add_to(fg_water)
        fg_water.add_to(m)
        feature_groups["water"] = fg_water

    # Parks
    if show_parks and osm_data.get("parks"):
        fg_parks = folium.FeatureGroup(name="Parks", show=True)
        for feat in osm_data["parks"]:
            geom = feat["geometry"]
            if geom["type"] == "Polygon":
                folium.GeoJson(
                    feat,
                    style_function=lambda x, color=colors["park"]: {
                        "fillColor": color,
                        "color": color,
                        "weight": 1,
                        "fillOpacity": 0.5
                    }
                ).add_to(fg_parks)
        fg_parks.add_to(m)
        feature_groups["parks"] = fg_parks

    # Buildings
    if show_buildings and osm_data.get("buildings"):
        fg_buildings = folium.FeatureGroup(name="Buildings", show=True)
        for feat in osm_data["buildings"]:
            geom = feat["geometry"]
            if geom["type"] == "Polygon":
                folium.GeoJson(
                    feat,
                    style_function=lambda x, color=colors["building"]: {
                        "fillColor": color,
                        "color": color,
                        "weight": 1,
                        "fillOpacity": 0.7
                    }
                ).add_to(fg_buildings)
        fg_buildings.add_to(m)
        feature_groups["buildings"] = fg_buildings

    # Roads (as lines)
    if show_roads and osm_data.get("roads"):
        fg_roads = folium.FeatureGroup(name="Roads", show=True)
        for feat in osm_data["roads"]:
            geom = feat["geometry"]
            if geom["type"] == "LineString":
                folium.GeoJson(
                    feat,
                    style_function=lambda x, color=colors["road"]: {
                        "color": color,
                        "weight": 2,
                        "opacity": 0.6
                    }
                ).add_to(fg_roads)
        fg_roads.add_to(m)
        feature_groups["roads"] = fg_roads

    # Add layer control
    folium.LayerControl(collapsed=False).add_to(m)

    return m

def export_poster(lat, lon, zoom, theme_name, show_water, show_parks, show_buildings, show_roads,
                  show_label, font_family, font_size, location_name, width, height):
    """Generate a PNG of the map with text overlay using Selenium."""
    # Generate map HTML
    m = generate_map(lat, lon, zoom, theme_name, show_water, show_parks, show_buildings, show_roads)
    map_html = m.get_root().render()

    # Build full HTML page with text overlay
    label_html = ""
    if show_label:
        label_html = f"""
        <div style="position: absolute; bottom: 30px; left: 0; right: 0; text-align: center; pointer-events: none; z-index: 1000;">
            <h1 style="font-family: '{font_family}'; font-size: {font_size}px; color: {THEMES[theme_name]['colors']['text']}; text-shadow: 0 2px 10px rgba(0,0,0,0.3); margin: 0; padding: 0 20px;">
                {location_name}
            </h1>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family={font_family.replace(' ', '+')}:wght@700&display=swap" rel="stylesheet">
        <style>
            body {{ margin: 0; padding: 0; background-color: {THEMES[theme_name]['colors']['bg']}; }}
            #map {{ width: 100%; height: 100%; position: relative; }}
            .leaflet-container {{ background: {THEMES[theme_name]['colors']['bg']} !important; }}
        </style>
    </head>
    <body>
        <div id="map">
            {map_html}
            {label_html}
        </div>
    </body>
    </html>
    """

    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(html_content)
        html_path = f.name

    # Setup Selenium headless Chrome
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--window-size={width},{height}")

    try:
        # Use webdriver-manager to get ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(f"file://{html_path}")
        time.sleep(2)  # Allow map to render

        # Take screenshot
        png = driver.get_screenshot_as_png()
        driver.quit()
        os.unlink(html_path)
        return png
    except (WebDriverException, TimeoutException) as e:
        st.error(f"Export failed: {e}. Please ensure Chrome browser is installed.")
        # Fallback: generate a simple image with text only
        img = Image.new("RGB", (width, height), THEMES[theme_name]['colors']['bg'])
        draw = ImageDraw.Draw(img)
        if show_label:
            try:
                # Attempt to use the font (may not be installed locally)
                font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", font_size)
            except:
                font = ImageFont.load_default()
            # Simple text placement
            bbox = draw.textbbox((0,0), location_name, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            x = (width - text_w) // 2
            y = height - text_h - 30
            draw.text((x, y), location_name, fill=THEMES[theme_name]['colors']['text'], font=font)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        return img_bytes.getvalue()

# ========== UI LAYOUT ==========

st.set_page_config(page_title="Terraink Clone - Map Poster Generator", layout="wide")

# Sidebar
with st.sidebar:
    st.header("📍 Location")
    location_query = st.text_input("Search for a place", value=st.session_state.location_name)
    col1, col2 = st.columns([2,1])
    with col1:
        if st.button("Search", use_container_width=True):
            with st.spinner("Geocoding..."):
                lat, lon, name = geocode_location(location_query)
                if lat is not None:
                    st.session_state.lat = lat
                    st.session_state.lon = lon
                    st.session_state.location_name = name
                    st.session_state.osm_data = None  # invalidate cache
                    st.rerun()
    with col2:
        if st.button("Reset", use_container_width=True):
            st.session_state.lat = 48.8566
            st.session_state.lon = 2.3522
            st.session_state.location_name = "Paris, France"
            st.session_state.osm_data = None
            st.rerun()

    st.divider()
    st.header("🎨 Theme")
    theme_names = list(THEMES.keys())
    selected_theme = st.selectbox("Theme", theme_names, index=theme_names.index(st.session_state.theme))
    st.session_state.theme = selected_theme

    st.divider()
    st.header("🗺️ Map Layers")
    show_water = st.checkbox("Water", value=st.session_state.show_water)
    show_parks = st.checkbox("Parks", value=st.session_state.show_parks)
    show_buildings = st.checkbox("Buildings", value=st.session_state.show_buildings)
    show_roads = st.checkbox("Roads", value=st.session_state.show_roads)
    st.session_state.show_water = show_water
    st.session_state.show_parks = show_parks
    st.session_state.show_buildings = show_buildings
    st.session_state.show_roads = show_roads

    st.divider()
    st.header("✍️ Typography")
    show_label = st.checkbox("Show city label", value=st.session_state.show_label)
    st.session_state.show_label = show_label
    font_family = st.selectbox("Font", FONTS, index=FONTS.index(st.session_state.font) if st.session_state.font in FONTS else 0)
    st.session_state.font = font_family
    font_size = st.slider("Font size", 16, 72, st.session_state.font_size)
    st.session_state.font_size = font_size

    st.divider()
    st.header("📤 Export")
    export_width = st.number_input("Width (px)", min_value=400, max_value=4000, value=1200, step=100)
    export_height = st.number_input("Height (px)", min_value=400, max_value=4000, value=1600, step=100)
    if st.button("Download Poster", type="primary", use_container_width=True):
        with st.spinner("Generating high-resolution poster..."):
            png_data = export_poster(
                st.session_state.lat,
                st.session_state.lon,
                st.session_state.get("zoom", 12),
                st.session_state.theme,
                st.session_state.show_water,
                st.session_state.show_parks,
                st.session_state.show_buildings,
                st.session_state.show_roads,
                st.session_state.show_label,
                st.session_state.font,
                st.session_state.font_size,
                st.session_state.location_name,
                export_width,
                export_height
            )
            if png_data:
                b64 = base64.b64encode(png_data).decode()
                href = f'<a href="data:image/png;base64,{b64}" download="poster.png">Click here to download</a>'
                st.markdown(href, unsafe_allow_html=True)
            else:
                st.error("Export failed. Please check that Chrome is installed.")

# Main area: Map
st.title("🗺️ Terraink Clone - Map Poster Generator")
st.caption("Interactive map with customizable themes and layers. Adjust controls on the left.")

# Display current location info
col_info1, col_info2 = st.columns(2)
with col_info1:
    st.metric("Location", st.session_state.location_name)
with col_info2:
    st.metric("Coordinates", f"{st.session_state.lat:.4f}, {st.session_state.lon:.4f}")

# Generate and show map
map_obj = generate_map(
    st.session_state.lat,
    st.session_state.lon,
    st.session_state.get("zoom", 12),
    st.session_state.theme,
    st.session_state.show_water,
    st.session_state.show_parks,
    st.session_state.show_buildings,
    st.session_state.show_roads
)

# Use folium_static with a larger height
folium_static(map_obj, width=900, height=600)

# If label is shown, we also display a text overlay (simulated using st.markdown)
# Note: The actual map HTML already includes the label via export, but for preview we can show it.
# However, folium_static renders the map in an iframe, so we can't overlay text directly.
# We'll just show a preview text below the map for reference.
if st.session_state.show_label:
    st.markdown(
        f"<h2 style='font-family: {st.session_state.font}; font-size: {st.session_state.font_size}px; text-align: center; color: {THEMES[st.session_state.theme]['colors']['text']};'>"
        f"{st.session_state.location_name}</h2>",
        unsafe_allow_html=True
    )

# Store zoom level from map interaction? Not possible with folium_static; we can add a zoom slider.
# For simplicity, we can add a zoom control in sidebar.
st.sidebar.divider()
st.sidebar.header("Zoom")
zoom_level = st.sidebar.slider("Zoom", 5, 18, st.session_state.get("zoom", 12))
st.session_state.zoom = zoom_level
# Rerun on zoom change
if zoom_level != st.session_state.get("last_zoom", None):
    st.session_state.last_zoom = zoom_level
    st.rerun()

# ========== FOOTER ==========
st.sidebar.markdown("---")
st.sidebar.caption("Built with Streamlit, Folium, and Selenium")
