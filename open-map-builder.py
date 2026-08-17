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

# Initialize Session State for Color Customization
DEFAULT_PALETTE = {
    "Overlay": "#0d1c2f",
    "Text": "#e0a838",
    "Land": "#0a1628",
    "Landcover": "#0d1c2f",
    "Water": "#050c18",
    "Waterways": "#061020",
    "Parks": "#0d1e34",
    "Buildings": "#5c4d3c",
    "Aeroway": "#132238",
    "Rail": "#e0a838",
    "Roads Major": "#c99c37",
    "Roads Minor High": "#9e7322",
    "Roads Minor Mid": "#3c3c38",
    "Roads Minor Low": "#282b2e",
    "Roads Path": "#3f3e35",
    "Road Outline": "#474536"
}

if "palette" not in st.session_state:
    st.session_state.palette = DEFAULT_PALETTE.copy()

if "active_layer_edit" not in st.session_state:
    st.session_state.active_layer_edit = "Land"

if "editor_mode" not in st.session_state:
    st.session_state.editor_mode = False

# Custom CSS for Felt-Style Sidebar, Swatch Grid, and Full-Bleed Map
st.markdown("""
    <style>
    /* Full-bleed map layout */
    .block-container {
        padding: 0rem !important;
        margin: 0rem !important;
        max-width: 100% !important;
    }
    
    header { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    
    /* Felt Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0b0f17 !important;
        border-right: 1px solid #1a2233 !important;
        padding-top: 1rem !important;
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Swatch Button Cards */
    div.stButton > button {
        background-color: #111827;
        color: #cbd5e1;
        border: 1px solid #1f293d;
        border-radius: 8px;
        font-size: 11px;
        padding: 4px 6px;
        width: 100%;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        border-color: #38bdf8;
        color: #ffffff;
    }
    
    /* Active Selected Swatch highlight */
    .swatch-box {
        height: 28px;
        border-radius: 6px;
        margin-bottom: 4px;
        border: 1px solid rgba(255,255,255,0.15);
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------
# 2. SIDEBAR TOOLBAR & FELT COLOR EDITOR
# ------------------------------------------------------------------------

# Helper functions for color conversions
def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4))

if not st.session_state.editor_mode:
    # --- STANDARD VIEW ---
    st.sidebar.markdown("### 🗺️ **Basemap Layer**")
    
    basemap_options = ["Custom Midnight Theme", "Carto DB Light", "Carto DB Dark", "Satellite", "OSM"]
    selected_basemap = st.sidebar.radio("Select Layer", options=basemap_options, index=0)
    
    st.sidebar.markdown("---")
    
    if selected_basemap == "Custom Midnight Theme":
        st.sidebar.markdown(
            f"""
            <div style="background-color: {st.session_state.palette['Land']}; padding: 12px; border-radius: 8px; border: 1px solid #1a2c4e; border-left: 4px solid {st.session_state.palette['Roads Major']};">
                <strong style="color: {st.session_state.palette['Roads Major']}; font-size: 13px;">Midnight Theme Active</strong><br>
                <div style="display: flex; gap: 8px; margin-top: 8px; align-items: center;">
                    <span style="display:inline-block; width:14px; height:14px; background:{st.session_state.palette['Land']}; border:1px solid #334e7a; border-radius:3px;"></span>
                    <span style="font-size: 11px; color: #94a3b8;">Base: <code>{st.session_state.palette['Land']}</code></span>
                </div>
                <div style="display: flex; gap: 8px; margin-top: 4px; align-items: center;">
                    <span style="display:inline-block; width:14px; height:14px; background:{st.session_state.palette['Roads Major']}; border-radius:3px;"></span>
                    <span style="font-size: 11px; color: #94a3b8;">Roads: <code>{st.session_state.palette['Roads Major']}</code></span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.sidebar.write("")
        if st.sidebar.button("🎨 Open Color Editor", use_container_width=True):
            st.session_state.editor_mode = True
            st.rerun()
    else:
        st.sidebar.caption(f"Active layer: **{selected_basemap}**")

else:
    # --- COLOR EDITOR VIEW (FELT.COM STYLE) ---
    selected_basemap = "Custom Midnight Theme"
    
    # Header & Action buttons
    st.sidebar.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 11px; font-weight: 700; color: #7dd3fc; letter-spacing: 1px;">COLOR EDITOR</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col_hdr1, col_hdr2 = st.sidebar.columns([1, 1])
    with col_hdr1:
        if st.button("Reset All Colors", use_container_width=True):
            st.session_state.palette = DEFAULT_PALETTE.copy()
            st.rerun()
    with col_hdr2:
        if st.button("✓ Done", use_container_width=True):
            st.session_state.editor_mode = False
            st.rerun()
            
    st.sidebar.markdown(f"<p style='font-size:13px; font-weight:600; margin: 4px 0;'>Editing: <span style='color:#38bdf8;'>{st.session_state.active_layer_edit}</span></p>", unsafe_allow_html=True)
    
    # 4x4 Interactive Swatch Grid (Matching image_306746.png)
    layer_names = list(st.session_state.palette.keys())
    for row in range(4):
        cols = st.sidebar.columns(4)
        for col_idx in range(4):
            item_idx = row * 4 + col_idx
            layer = layer_names[item_idx]
            color = st.session_state.palette[layer]
            is_active = (layer == st.session_state.active_layer_edit)
            
            with cols[col_idx]:
                border_style = "2px solid #ffffff" if is_active else "1px solid rgba(255,255,255,0.15)"
                st.markdown(
                    f"""
                    <div style="background-color: {color}; height: 26px; border-radius: 6px; border: {border_style}; margin-bottom: 2px;"></div>
                    """,
                    unsafe_allow_html=True
                )
                if st.button(layer[:7], key=f"btn_{layer}", help=layer):
                    st.session_state.active_layer_edit = layer
                    st.rerun()

    st.sidebar.markdown("---")
    
    # Detail Color Picker Panel (Matching image_30672a.png)
    st.sidebar.markdown(f"**Fine-tune `{st.session_state.active_layer_edit}`**")
    
    # Preset Quick-Select Row
    preset_colors = ["#0a1628", "#0d1c2f", "#1e293b", "#050c18", "#c99c37", "#e0a838", "#5c4d3c", "#ffffff"]
    preset_cols = st.sidebar.columns(len(preset_colors))
    for idx, pcolor in enumerate(preset_colors):
        with preset_cols[idx]:
            if st.button(" ", key=f"preset_{idx}"):
                st.session_state.palette[st.session_state.active_layer_edit] = pcolor
                st.rerun()
            st.markdown(f"<div style='background-color: {pcolor}; height: 8px; border-radius: 2px; margin-top:-10px;'></div>", unsafe_allow_html=True)
            
    # Native Precision Color Picker
    new_color = st.sidebar.color_picker(
        "Hex Color",
        value=st.session_state.palette[st.session_state.active_layer_edit],
        key=f"picker_{st.session_state.active_layer_edit}"
    )
    if new_color != st.session_state.palette[st.session_state.active_layer_edit]:
        st.session_state.palette[st.session_state.active_layer_edit] = new_color
        st.rerun()

    if st.sidebar.button("Reset This Color", use_container_width=True):
        st.session_state.palette[st.session_state.active_layer_edit] = DEFAULT_PALETTE[st.session_state.active_layer_edit]
        st.rerun()

# ------------------------------------------------------------------------
# 3. MAP BUILDER & DYNAMIC COLOR MATRIX
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

# Zero gridline CSS
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

if selected_basemap == "Custom Midnight Theme":
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/rastertiles/dark_nolabels/{z}/{x}/{y}@2x.png',
        attr='&copy; OpenStreetMap contributors &copy; CARTO',
        name='Custom Theme',
        max_zoom=20,
        subdomains='abcd',
        detect_retina=True
    ).add_to(m)

    # Calculate dynamic RGB transformation matrix from user palette
    base_rgb = hex_to_rgb(st.session_state.palette["Land"])
    road_rgb = hex_to_rgb(st.session_state.palette["Roads Major"])
    
    delta_l = 0.32
    m_r = (road_rgb[0] - base_rgb[0]) / delta_l
    c_r = base_rgb[0] - m_r * 0.14

    m_g = (road_rgb[1] - base_rgb[1]) / delta_l
    c_g = base_rgb[1] - m_g * 0.14

    m_b = (road_rgb[2] - base_rgb[2]) / delta_l
    c_b = base_rgb[2] - m_b * 0.14

    dynamic_svg_filter = f"""
    <svg xmlns="http://www.w3.org/2000/svg" style="position: absolute; width: 0; height: 0; pointer-events: none;">
        <filter id="custom-color-matrix" color-interpolation-filters="sRGB">
            <feColorMatrix type="matrix" values="
                {m_r:.3f} 0 0 0 {c_r:.3f}
                {m_g:.3f} 0 0 0 {c_g:.3f}
                {m_b:.3f} 0 0 0 {c_b:.3f}
                0         0 0 1  0" />
        </filter>
    </svg>
    <style>
    {transparent_grid_css}
    .leaflet-tile-pane {{
        filter: url(#custom-color-matrix) !important;
        -webkit-filter: url(#custom-color-matrix) !important;
    }}
    .leaflet-container {{
        background: {st.session_state.palette['Land']} !important;
    }}
    </style>
    """
    m.get_root().header.add_child(folium.Element(dynamic_svg_filter))

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
