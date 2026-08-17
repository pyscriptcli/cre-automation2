import streamlit as st
import folium
from streamlit_folium import st_folium

# ------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & FELT.COM THEME
# ------------------------------------------------------------------------
st.set_page_config(
    page_title="Felt Map Studio",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Felt-style UI styling
st.markdown("""
    <style>
    /* Full-bleed map canvas */
    .block-container {
        padding: 0rem !important;
        margin: 0rem !important;
        max-width: 100% !important;
    }
    
    /* Remove default Streamlit headers */
    header { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    
    /* Felt-style dark workspace toolbar */
    [data-testid="stSidebar"] {
        background-color: #0b0f17 !important;
        border-right: 1px solid #1a2233 !important;
        padding-top: 1.5rem;
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Radio options styled as clean select cards */
    div.row-widget.stRadio > div {
        background: #111827;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #1f293d;
        gap: 6px;
    }
    div.row-widget.stRadio label {
        padding: 6px 10px;
        border-radius: 6px;
        transition: background 0.15s ease;
    }
    div.row-widget.stRadio label:hover {
        background: #1a2336;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------
# 2. SIDEBAR (FELT TOOLBAR)
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
        <div style="background-color: #0a1628; padding: 12px; border-radius: 8px; border: 1px solid #1a2c4e; border-left: 4px solid #c99c37;">
            <strong style="color: #c99c37; font-size: 13px;">Midnight Blue Active</strong><br>
            <div style="display: flex; gap: 8px; margin-top: 8px; align-items: center;">
                <span style="display:inline-block; width:14px; height:14px; background:#0a1628; border:1px solid #334e7a; border-radius:3px;"></span>
                <span style="font-size: 11px; color: #94a3b8;">Base: <code>#0a1628</code></span>
            </div>
            <div style="display: flex; gap: 8px; margin-top: 4px; align-items: center;">
                <span style="display:inline-block; width:14px; height:14px; background:#c99c37; border-radius:3px;"></span>
                <span style="font-size: 11px; color: #94a3b8;">Roads: <code>#c99c37</code></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.sidebar.caption(f"Active layer: **{selected_basemap}**")

# ------------------------------------------------------------------------
# 3. MAP BUILDER & ZERO-GRIDLINE CONFIGURATION
# ------------------------------------------------------------------------

CENTER_COORDS = [14.5794, 121.0359]

m = folium.Map(
    location=CENTER_COORDS,
    zoom_start=14,
    tiles=None,
    control_scale=True,
    zoom_control=False,
    zoom_snap=1,
    zoom_delta=1
)

# Strips all borders, outlines, shadows, and margins to eliminate gridlines completely
transparent_grid_css = """
    .leaflet-tile,
    .leaflet-tile-container,
    .leaflet-tile-pane,
    .leaflet-layer {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        margin: 0 !important;
        padding: 0 !important;
        -webkit-backface-visibility: hidden !important;
        backface-visibility: hidden !important;
        transform: translate3d(0, 0, 0);
    }
    .leaflet-tile {
        background: transparent !important;
    }
"""

if selected_basemap == "Midnight Blue":
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/rastertiles/dark_nolabels/{z}/{x}/{y}@2x.png',
        attr='&copy; OpenStreetMap contributors &copy; CARTO',
        name='Midnight Blue',
        max_zoom=20,
        subdomains='abcd',
        detect_retina=True
    ).add_to(m)

    midnight_svg_filter = f"""
    <svg xmlns="http://www.w3.org/2000/svg" style="position: absolute; width: 0; height: 0; pointer-events: none;">
        <filter id="midnight-gold-matrix" color-interpolation-filters="sRGB">
            <feColorMatrix type="matrix" values="
                2.18 0 0 0 -0.285
                1.52 0 0 0 -0.140
                0.16 0 0 0  0.132
                0    0 0 1  0" />
        </filter>
    </svg>
    <style>
    {transparent_grid_css}
    .leaflet-tile-pane {{
        filter: url(#midnight-gold-matrix) !important;
        -webkit-filter: url(#midnight-gold-matrix) !important;
    }}
    .leaflet-container {{
        background: #0a1628 !important;
    }}
    </style>
    """
    m.get_root().header.add_child(folium.Element(midnight_svg_filter))

elif selected_basemap == "Carto DB Light":
    folium.TileLayer('CartoDB positron', name="Carto DB Light").add_to(m)
    m.get_root().header.add_child(folium.Element(f"<style>{transparent_grid_css} .leaflet-container {{ background: #f8f9fa !important; }}</style>"))

elif selected_basemap == "Carto DB Dark":
    folium.TileLayer('CartoDB dark_matter', name="Carto DB Dark").add_to(m)
    m.get_root().header.add_child(folium.Element(f"<style>{transparent_grid_css} .leaflet-container {{ background: #000000 !important; }}</style>"))

elif selected_basemap == "OSM":
    folium.TileLayer('OpenStreetMap', name="OSM").add_to(m)
    m.get_root().header.add_child(folium.Element(f"<style>{transparent_grid_css}</style>"))

elif selected_basemap == "Satellite":
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery',
        name='Satellite',
        max_zoom=19
    ).add_to(m)
    m.get_root().header.add_child(folium.Element(f"<style>{transparent_grid_css} .leaflet-container {{ background: #000000 !important; }}</style>"))

# ------------------------------------------------------------------------
# 4. RENDER FULL-SCREEN MAP
# ------------------------------------------------------------------------
st_folium(
    m,
    use_container_width=True,
    height=950,
    returned_objects=[]
)
