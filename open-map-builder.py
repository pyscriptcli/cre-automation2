import streamlit as st
import folium
from streamlit_folium import st_folium

# ------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & FELT.COM-STYLE UI
# ------------------------------------------------------------------------
st.set_page_config(
    page_title="Felt Map Studio",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Streamlit full-bleed layout and dark Felt-like sidebar
st.markdown("""
    <style>
    /* Full-screen bleed layout */
    .block-container {
        padding: 0rem !important;
        max-width: 100% !important;
    }
    
    /* Clean app mode: hide standard Streamlit headers */
    header { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    
    /* Felt Dark Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #21262d;
    }
    [data-testid="stSidebar"] * {
        color: #f0f6fc;
    }
    
    /* Radio Option Cards */
    div.row-widget.stRadio > div {
        background: #161b22;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #30363d;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------
# 2. SIDEBAR TOOLBAR
# ------------------------------------------------------------------------
st.sidebar.markdown("### 🗺️ **Basemap Layer**")

basemap_options = [
    "Midnight Blue",
    "Carto DB Light",
    "Carto DB Dark",
    "Satellite",
    "OSM"
]

selected_basemap = st.sidebar.radio(
    "Select Layer",
    options=basemap_options,
    index=0
)

st.sidebar.markdown("---")

if selected_basemap == "Midnight Blue":
    st.sidebar.markdown(
        """
        <div style="background-color: #0a1628; padding: 12px; border-radius: 6px; border-left: 4px solid #c99c37;">
            <strong style="color: #c99c37;">Midnight Blue Active</strong><br>
            <span style="font-size: 12px; color: #8b949e;">Deep Navy Base (#0a1628) with Gold/Amber Features (#c99c37).</span>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.sidebar.caption(f"Active basemap: **{selected_basemap}**")

# ------------------------------------------------------------------------
# 3. MAP BUILDER & ZERO-API COLOR MATRIX TRANSFORMATION
# ------------------------------------------------------------------------

# Coordinates for Mandaluyong / Metro Manila
CENTER_COORDS = [14.5794, 121.0359]

m = folium.Map(
    location=CENTER_COORDS,
    zoom_start=14,
    tiles=None,
    control_scale=True,
    zoom_control=False
)

# Common CSS fix for subpixel tile seams/grid line artifacts across all modes
# We use a box-shadow trick to bleed the exact background color into the grid seams
tile_seam_fix = """
    .leaflet-tile {
        margin: -1px !important;
        padding: 1px !important;
        outline: none !important;
        border: none !important;
        -webkit-backface-visibility: hidden !important;
        backface-visibility: hidden !important;
    }
"""

if selected_basemap == "Midnight Blue":
    # Base: CartoDB Dark Matter
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        attr='&copy; OpenStreetMap contributors &copy; CARTO',
        name='Midnight Blue Base',
        max_zoom=20,
        subdomains='abcd'
    ).add_to(m)

    # SVG feColorMatrix Transformation (Mathematically tuned for #0a1628 and #c99c37)
    # The box-shadow in the leaflet-tile CSS completely eliminates the gridlines
    midnight_svg_matrix = f"""
    <svg xmlns="http://www.w3.org/2000/svg" style="display:none;">
        <filter id="navy-gold-matrix" color-interpolation-filters="sRGB">
            <feColorMatrix type="matrix" values="
                3.00 0 0 0 -0.26
                2.10 0 0 0 -0.12
                0.24 0 0 0  0.13
                0    0 0 1  0" />
        </filter>
    </svg>
    <style>
    {tile_seam_fix}
    .leaflet-tile {{
        box-shadow: 0 0 1px #0a1628 !important; 
    }}
    .leaflet-tile-pane {{
        filter: url(#navy-gold-matrix) !important;
        -webkit-filter: url(#navy-gold-matrix) !important;
    }}
    .leaflet-container {{
        background: #0a1628 !important;
    }}
    </style>
    """
    m.get_root().header.add_child(folium.Element(midnight_svg_matrix))

elif selected_basemap == "Carto DB Light":
    folium.TileLayer('CartoDB positron', name="Carto DB Light").add_to(m)
    m.get_root().header.add_child(folium.Element(f"<style>{tile_seam_fix} .leaflet-container {{ background: #f8f9fa !important; }}</style>"))

elif selected_basemap == "Carto DB Dark":
    folium.TileLayer('CartoDB dark_matter', name="Carto DB Dark").add_to(m)
    m.get_root().header.add_child(folium.Element(f"<style>{tile_seam_fix} .leaflet-tile {{ box-shadow: 0 0 1px #000 !important; }} .leaflet-container {{ background: #000 !important; }}</style>"))

elif selected_basemap == "OSM":
    folium.TileLayer('OpenStreetMap', name="OSM").add_to(m)
    m.get_root().header.add_child(folium.Element(f"<style>{tile_seam_fix}</style>"))

elif selected_basemap == "Satellite":
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery',
        name='Satellite',
        max_zoom=19
    ).add_to(m)
    m.get_root().header.add_child(folium.Element(f"<style>{tile_seam_fix} .leaflet-tile {{ box-shadow: 0 0 1px #000 !important; }} .leaflet-container {{ background: #000 !important; }}</style>"))

# ------------------------------------------------------------------------
# 4. RENDER FULL-SCREEN MAP
# ------------------------------------------------------------------------
st_folium(
    m,
    use_container_width=True,
    height=950,
    returned_objects=[]
)
