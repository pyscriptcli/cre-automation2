import streamlit as st
import folium
from streamlit_folium import st_folium

# 1. Page Configuration for Full Screen Layout
st.set_page_config(
    page_title="Basemap Color Picker",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Define Tile Configurations matching the uploaded images
# These URLs are open-source or use standard provider URLs.
TILE_CONFIG = {
    "Carrara": {
        # Dark grey / white clean theme (CartoDB Dark Matter)
        "url": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        "attr": "CartoDB"
    },
    "Contrast": {
        # Stark black and white high contrast theme (Stamen Toner)
        "url": "https://stamen-tiles-{s}.a.ssl.fastly.net/toner/{z}/{x}/{y}{r}.png",
        "attr": "Stamen Toner"
    },
    "Sandstone": {
        # Earthy, sandy, brownish theme (CartoDB Voyager)
        "url": "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        "attr": "CartoDB"
    },
    "Midnight Blue": {
        # Deep dark blue theme (Mapbox Midnight) - requires an API token
        "url": "https://api.mapbox.com/styles/v1/mapbox/midnight-v1/tiles/{z}/{x}/{y}{r}.png?access_token={token}",
        "attr": "Mapbox"
    }
}

# 3. Sidebar UI (Toolbar)
with st.sidebar:
    st.header("🗺️ Map Controls")
    st.markdown("---")
    
    # Dropdown to select the Theme
    selected_theme = st.selectbox(
        "Select Basemap & Colors",
        list(TILE_CONFIG.keys())
    )
    
    # Input for Mapbox Token (Required only for Midnight Blue)
    mapbox_token = st.text_input(
        "Mapbox Access Token (Required for Midnight Blue)",
        type="password",
        placeholder="pk.eyJ1..."
    )
    
    st.markdown("---")
    st.caption("**Note:** Midnight Blue requires a valid Mapbox token. If none is provided, it will fallback to Carrara.")
    st.caption("Map can be dragged and zoomed.")

# 4. Logic to validate settings
# Determine which map URL and attribution to use
if selected_theme == "Midnight Blue":
    if not mapbox_token:
        st.sidebar.warning("⚠️ Mapbox Token missing! Falling back to Carrara theme.")
        active_theme_name = "Carrara"
        url = TILE_CONFIG[active_theme_name]["url"]
        attr = TILE_CONFIG[active_theme_name]["attr"]
    else:
        url = TILE_CONFIG["Midnight Blue"]["url"].format(token=mapbox_token)
        attr = TILE_CONFIG["Midnight Blue"]["attr"]
else:
    url = TILE_CONFIG[selected_theme]["url"]
    attr = TILE_CONFIG[selected_theme]["attr"]

# 5. Create the Map
# Center over the USA as a default, Zoom Level 4
m = folium.Map(
    location=[39.8283, -98.5795], 
    zoom_start=4,
    tiles=url,
    attr=attr,
    width="100%",
    height="100%"
)

# Add a fullscreen plugin (optional extras, works natively with streamlit-folium)
folium.plugins.Fullscreen().add_to(m)

# 6. Render the full-screen map using streamlit-folium
# Returning the map component will automatically take the width of the container.
map_data = st_folium(m, width="100%", height=850)

# 7. Display interactions (Optional, displays bounds and coordinates)
if map_data and 'last_clicked' in map_data and map_data['last_clicked']:
    st.write(f"📍 Last clicked coordinates: {map_data['last_clicked']}")
