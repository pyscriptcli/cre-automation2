import streamlit as st
import folium
from streamlit_folium import st_folium

# ------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & FELT.COM-STYLE CSS
# ------------------------------------------------------------------------
st.set_page_config(
    page_title="Felt-Style Map Viewer",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to force full-screen map, hide Streamlit chrome, and style the sidebar
st.markdown("""
    <style>
    /* Remove standard Streamlit padding and margins */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
    }
    
    /* Hide Header and Main Menu for a clean app-like feel */
    header { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    
    /* Dark theme for sidebar */
    [data-testid="stSidebar"] {
        background-color: #111418;
        border-right: 1px solid #2d333b;
    }
    [data-testid="stSidebar"] * {
        color: #e6edf3;
    }
    
    /* Style radio buttons to look a bit cleaner */
    div.row-widget.stRadio > div {
        background: #1d2127;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #30363d;
    }
    </style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------------
# 2. SIDEBAR UI (TOOLBAR)
# ------------------------------------------------------------------------
st.sidebar.title("🗺️ Map Workspace")
st.sidebar.markdown("---")

st.sidebar.subheader("Basemap Configuration")

# Standard Basemaps
standard_basemaps = [
    "Carto DB Light",
    "Carto DB Dark",
    "Satellite",
    "OSM"
]

# Color Themes
color_themes = [
    "Theme: Carrara",
    "Theme: Sandstone",
    "Theme: Midnight Blue",
    "Theme: Contrast"
]

selected_layer = st.sidebar.radio(
    "Select Layer or Theme",
    options=standard_basemaps + color_themes,
    index=6 # Defaults to Midnight Blue based on your screenshot
)

st.sidebar.markdown("---")
st.sidebar.caption("Selecting a 'Theme' injects CSS filters onto a Carto DB Light base layer to simulate the custom styles shown in the screenshots.")

# ------------------------------------------------------------------------
# 3. MAP GENERATION & COLOR INJECTION LOGIC
# ------------------------------------------------------------------------

# Coordinates for Mandaluyong City, Metro Manila
MANDALUYONG_COORDS = [14.5794, 121.0359]

# Initialize base map without standard tiles
m = folium.Map(
    location=MANDALUYONG_COORDS, 
    zoom_start=13, 
    tiles=None,
    control_scale=True,
    zoom_control=False # Hiding default controls for a cleaner Felt look
)

# Determine which tile set and filters to apply
if selected_layer == "Carto DB Light":
    folium.TileLayer('CartoDB positron', name="Carto DB Light").add_to(m)

elif selected_layer == "Carto DB Dark":
    folium.TileLayer('CartoDB dark_matter', name="Carto DB Dark").add_to(m)

elif selected_layer == "OSM":
    folium.TileLayer('OpenStreetMap', name="OSM").add_to(m)

elif selected_layer == "Satellite":
    # Using Esri World Imagery for a clean, high-res satellite view
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery',
        name='Satellite'
    ).add_to(m)

else:
    # --- COLOR THEME INJECTION ---
    # Add the base layer first
    folium.TileLayer('CartoDB positron', name=selected_layer).add_to(m)
    
    css_filter = ""
    bg_color = "#f8f9fa" # Default light background
    
    if selected_layer == "Theme: Carrara":
        # Subtle warm greyscale with light contrast
        css_filter = "sepia(15%) grayscale(40%) contrast(105%) brightness(98%)"
        
    elif selected_layer == "Theme: Sandstone":
        # Warm brownish/sepia tones, increased saturation
        css_filter = "sepia(70%) hue-rotate(-15deg) saturate(140%) contrast(110%) brightness(95%)"
        
    elif selected_layer == "Theme: Midnight Blue":
        # Invert the light map to make it dark, then hue-shift to blues and gold
        css_filter = "invert(100%) hue-rotate(185deg) saturate(150%) contrast(115%) brightness(90%)"
        bg_color = "#111418" # Dark background to prevent white flashes
        
    elif selected_layer == "Theme: Contrast":
        # High contrast, pure black/white/grey
        css_filter = "grayscale(100%) contrast(200%) brightness(85%)"
        bg_color = "#111418" 

    # THE FIX: Inject the generated CSS filter into the header using !important
    custom_css = f"""
    <style>
    .leaflet-tile-pane {{
        filter: {css_filter} !important;
        -webkit-filter: {css_filter} !important;
        transition: filter 0.5s ease-in-out;
    }}
    .leaflet-container {{
        background: {bg_color} !important;
    }}
    </style>
    """
    m.get_root().header.add_child(folium.Element(custom_css))

# ------------------------------------------------------------------------
# 4. RENDER MAP 
# ------------------------------------------------------------------------
st_folium(
    m, 
    use_container_width=True, 
    height=1000, 
    returned_objects=[] # Prevents Streamlit re-renders on map pan/zoom
)
