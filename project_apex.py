import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw, MousePosition
import pandas as pd
import json
from datetime import datetime

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="GIS Analysis Tool",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================
st.markdown("""
    <style>
    /* Main container */
    .main {
        padding: 0rem 0rem;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
        padding-top: 0.5rem;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #1a1a2e;
        font-weight: 600;
    }

    /* Sidebar section headers */
    .sidebar-section {
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #6c757d;
        margin-top: 0.75rem;
        margin-bottom: 0.25rem;
        padding-bottom: 0.25rem;
        border-bottom: 1px solid #e9ecef;
    }

    /* Location input cards */
    .loc-card {
        background: white;
        padding: 0.5rem 0.75rem;
        border-radius: 6px;
        border: 1px solid #e9ecef;
        margin-bottom: 0.3rem;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    .loc-card:hover {
        border-color: #4a90d9;
        background: #f0f7ff;
    }
    .loc-card.active {
        border-color: #4a90d9;
        background: #e8f0fe;
        font-weight: 500;
    }

    /* Map container */
    .map-container {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e9ecef;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }

    /* Details panel */
    .details-panel {
        background: white;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        padding: 0.75rem 1rem;
        margin-top: 0.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        max-height: 320px;
        overflow-y: auto;
    }
    .details-panel .detail-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    .details-panel .detail-value {
        font-size: 0.95rem;
        color: #1a1a2e;
        margin-bottom: 0.5rem;
    }
    .details-panel .detail-divider {
        border: none;
        border-top: 1px solid #f1f3f5;
        margin: 0.5rem 0;
    }

    /* Dropdown styling */
    .stSelectbox label {
        font-size: 0.85rem;
        font-weight: 500;
        color: #495057;
    }

    /* Checkbox styling */
    .stCheckbox label {
        font-size: 0.85rem;
        color: #495057;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #1a1a2e;
        background: #f8f9fa;
        border-radius: 6px;
    }

    /* Title */
    .app-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1a1a2e;
        padding: 0.5rem 0 0.25rem 0;
        border-bottom: 2px solid #4a90d9;
        display: inline-block;
    }
    .app-subtitle {
        font-size: 0.8rem;
        color: #6c757d;
        margin-bottom: 0.5rem;
    }

    /* Badge */
    .badge {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        font-size: 0.7rem;
        font-weight: 600;
        border-radius: 12px;
        background: #e9ecef;
        color: #495057;
    }
    .badge-primary {
        background: #4a90d9;
        color: white;
    }
    .badge-success {
        background: #28a745;
        color: white;
    }
    .badge-warning {
        background: #ffc107;
        color: #1a1a2e;
    }

    /* Layer toggle */
    .layer-item {
        display: flex;
        align-items: center;
        padding: 0.2rem 0;
        font-size: 0.85rem;
    }
    .layer-item .color-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 0.5rem;
        display: inline-block;
        border: 1px solid #dee2e6;
    }

    /* Footer */
    .footer {
        font-size: 0.7rem;
        color: #adb5bd;
        text-align: center;
        padding: 0.5rem 0;
        border-top: 1px solid #e9ecef;
        margin-top: 0.5rem;
    }

    /* Scrollbar */
    .details-panel::-webkit-scrollbar {
        width: 4px;
    }
    .details-panel::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    .details-panel::-webkit-scrollbar-thumb {
        background: #c1c7cd;
        border-radius: 4px;
    }
    .details-panel::-webkit-scrollbar-thumb:hover {
        background: #a0a7ae;
    }

    /* Resize handle hint */
    .resize-hint {
        font-size: 0.7rem;
        color: #adb5bd;
        text-align: right;
        cursor: ns-resize;
        user-select: none;
    }

    /* Map attribution small */
    .map-attribution {
        font-size: 0.65rem;
        color: #868e96;
        padding: 0.25rem 0.5rem;
        background: rgba(255,255,255,0.8);
        border-radius: 4px;
        margin-top: -2rem;
        position: relative;
        z-index: 1000;
        display: inline-block;
    }

    /* Tooltip style */
    .info-tip {
        font-size: 0.75rem;
        color: #6c757d;
        font-style: italic;
    }

    /* Make sidebar scrollable */
    section[data-testid="stSidebar"] > div:first-child {
        max-height: 100vh;
        overflow-y: auto;
    }

    /* Custom radio buttons for location input */
    div[role="radiogroup"] label {
        font-size: 0.85rem;
        padding: 0.3rem 0.6rem;
        border-radius: 4px;
        border: 1px solid #e9ecef;
        margin: 0.1rem 0.2rem;
        background: white;
    }
    div[role="radiogroup"] label[data-checked="true"] {
        background: #e8f0fe;
        border-color: #4a90d9;
    }

    /* Reduce padding in sidebar columns */
    .stColumn {
        padding: 0 !important;
    }

    /* Detail panel header */
    .detail-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.25rem 0;
    }
    .detail-header h4 {
        margin: 0;
        font-weight: 600;
        color: #1a1a2e;
    }
    .detail-header .close-btn {
        background: none;
        border: none;
        font-size: 1.2rem;
        color: #adb5bd;
        cursor: pointer;
    }
    .detail-header .close-btn:hover {
        color: #495057;
    }

    /* Responsive tweaks */
    @media (max-width: 768px) {
        .details-panel {
            max-height: 200px;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INIT
# ============================================================================
if "selected_feature" not in st.session_state:
    st.session_state.selected_feature = None

if "selected_feature_type" not in st.session_state:
    st.session_state.selected_feature_type = None

if "drawings" not in st.session_state:
    st.session_state.drawings = []

if "map_center" not in st.session_state:
    st.session_state.map_center = [14.8500, 120.9500]

if "map_zoom" not in st.session_state:
    st.session_state.map_zoom = 11

if "details_expanded" not in st.session_state:
    st.session_state.details_expanded = True

if "location_input_mode" not in st.session_state:
    st.session_state.location_input_mode = "Polygon"

if "layers_visible" not in st.session_state:
    st.session_state.layers_visible = {
        "hazards": True,
        "roads": True,
        "boundaries": True,
        "zoning": False,
        "valuation": False
    }

# ============================================================================
# SAMPLE DATA
# ============================================================================
# Sample locations in Bulacan, Philippines
sample_locations = [
    {
        "id": 1,
        "name": "Plaridel",
        "lat": 14.8875,
        "lng": 120.8567,
        "type": "Municipality",
        "description": "Municipal hall and town center",
        "population": "41,000",
        "area_km2": "32.44",
        "hazard_risk": "Moderate",
        "infrastructure": "Good road network"
    },
    {
        "id": 2,
        "name": "Tabang Spur Road",
        "lat": 14.8950,
        "lng": 120.8700,
        "type": "Road Junction",
        "description": "Major intersection connecting to MacArthur Highway",
        "population": "N/A",
        "area_km2": "N/A",
        "hazard_risk": "Low",
        "infrastructure": "Highway junction"
    },
    {
        "id": 3,
        "name": "MacArthur Highway",
        "lat": 14.8980,
        "lng": 120.8780,
        "type": "Highway",
        "description": "Primary north-south thoroughfare",
        "population": "N/A",
        "area_km2": "N/A",
        "hazard_risk": "Low",
        "infrastructure": "Major highway"
    },
    {
        "id": 4,
        "name": "Santa Maria",
        "lat": 14.8183,
        "lng": 120.9567,
        "type": "Municipality",
        "description": "Town center with commercial district",
        "population": "289,000",
        "area_km2": "90.92",
        "hazard_risk": "Moderate",
        "infrastructure": "Developing urban center"
    },
    {
        "id": 5,
        "name": "San Jose del Monte",
        "lat": 14.8139,
        "lng": 121.0450,
        "type": "City",
        "description": "Component city, major residential area",
        "population": "651,000",
        "area_km2": "105.53",
        "hazard_risk": "High (flooding)",
        "infrastructure": "Expanding infrastructure"
    },
    {
        "id": 6,
        "name": "Meycauayan",
        "lat": 14.7333,
        "lng": 120.9500,
        "type": "City",
        "description": "Industrial and commercial hub",
        "population": "225,000",
        "area_km2": "32.10",
        "hazard_risk": "Moderate",
        "infrastructure": "Well-developed"
    },
    {
        "id": 7,
        "name": "Montalban (Rodriguez)",
        "lat": 14.7000,
        "lng": 121.1167,
        "type": "Municipality",
        "description": "Growing suburban area",
        "population": "370,000",
        "area_km2": "172.53",
        "hazard_risk": "Moderate",
        "infrastructure": "Developing"
    }
]

# Sample polygons (simplified)
sample_polygons = [
    {
        "id": 101,
        "name": "Flood Zone A - Santa Maria",
        "type": "Hazard Zone",
        "description": "High risk flood area along river basin",
        "coordinates": [
            [14.8350, 120.9400],
            [14.8300, 120.9600],
            [14.8100, 120.9650],
            [14.8000, 120.9450],
            [14.8150, 120.9300]
        ],
        "risk_level": "High",
        "area_km2": "8.5"
    },
    {
        "id": 102,
        "name": "Commercial Zone - Meycauayan",
        "type": "Zoning",
        "description": "Designated commercial and industrial zone",
        "coordinates": [
            [14.7450, 120.9450],
            [14.7400, 120.9600],
            [14.7250, 120.9550],
            [14.7280, 120.9400]
        ],
        "risk_level": "Low",
        "area_km2": "3.2"
    }
]

# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    # Title
    st.markdown('<div class="app-title">🌍 GIS Analysis Tool</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Location Intelligence & Mapping Platform</div>', unsafe_allow_html=True)

    # ========================================================================
    # LOCATION INPUT OPTIONS
    # ========================================================================
    st.markdown('<div class="sidebar-section">📍 Location Input</div>', unsafe_allow_html=True)

    loc_mode = st.radio(
        "Coordinates for Pin Location",
        ["Radius", "Polygon", "Street (Point A → Point B)"],
        index=1,
        key="loc_mode",
        label_visibility="collapsed"
    )
    st.session_state.location_input_mode = loc_mode

    # Quick helper text
    if loc_mode == "Radius":
        st.caption("Draw a circle on the map to define a radius.")
        radius_val = st.slider("Radius", min_value=100, max_value=5000, value=1000, step=100, key="radius_val")
        st.caption(f"📍 {radius_val}m radius")
    elif loc_mode == "Polygon":
        st.caption("Draw a polygon on the map to define an area.")
        st.caption("🖱️ Click the polygon tool in the map toolbar")
    else:  # Street
        st.caption("Click two points on the map to define a street segment.")
        st.caption("🖱️ Use the polyline tool to draw a street")

    # ========================================================================
    # LAYERS
    # ========================================================================
    st.markdown('<div class="sidebar-section">🗺️ Layers</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        layers_hazards = st.checkbox("Hazards", value=True, key="layer_hazards")
        layers_roads = st.checkbox("Roads", value=True, key="layer_roads")
        layers_boundaries = st.checkbox("Boundaries", value=True, key="layer_boundaries")
    with col2:
        layers_zoning = st.checkbox("Zoning", value=False, key="layer_zoning")
        layers_valuation = st.checkbox("Valuation", value=False, key="layer_valuation")

    st.session_state.layers_visible["hazards"] = layers_hazards
    st.session_state.layers_visible["roads"] = layers_roads
    st.session_state.layers_visible["boundaries"] = layers_boundaries
    st.session_state.layers_visible["zoning"] = layers_zoning
    st.session_state.layers_visible["valuation"] = layers_valuation

    # Manage layer button
    st.button("⚙️ Manage layer", use_container_width=True, key="manage_layer")

    # ========================================================================
    # DROPDOWNS
    # ========================================================================
    st.markdown('<div class="sidebar-section">📊 Data Layers</div>', unsafe_allow_html=True)

    # Hazards
    with st.expander("⚠️ Hazards", expanded=False):
        hazard_sel = st.multiselect(
            "Select hazard types",
            ["Earthquake", "Floods", "Landslide", "Tsunami", "Volcanic"],
            default=["Earthquake", "Floods"],
            key="hazard_sel"
        )
        if hazard_sel:
            st.caption(f"Showing: {', '.join(hazard_sel)}")
        else:
            st.caption("No hazards selected")

    # Infrastructure
    with st.expander("🏗️ Infrastructure", expanded=False):
        infra_sel = st.multiselect(
            "Select infrastructure layers",
            ["Roads", "Boundaries (Cities)", "Boundaries (Province)", "Boundaries (Region)", "Zoning (LGU Restrictions)", "CLUP"],
            default=["Roads", "Boundaries (Cities)"],
            key="infra_sel"
        )
        if infra_sel:
            st.caption(f"Showing: {', '.join(infra_sel)}")

    # Valuation
    with st.expander("💰 Valuation", expanded=False):
        val_sel = st.multiselect(
            "Select valuation sources",
            ["Rental Rate", "PRIME Core", "Lamudi", "Other Platforms"],
            default=["Rental Rate", "PRIME Core"],
            key="val_sel"
        )
        st.caption("📊 Smart Comparable Analysis: Finds and analyzes comparable properties with advanced scoring algorithms")
        st.caption("📈 Tiering: Primary / Secondary sources")

    # ========================================================================
    # SUGGESTION NOTES
    # ========================================================================
    st.markdown('<div class="sidebar-section">💡 Suggestions</div>', unsafe_allow_html=True)
    st.info("""
    - **Power BI** for dashboard-like data interpretation
    - **Use less AI** in GIS format — focus on spatial analysis
    """)

    # ========================================================================
    # FOOTER
    # ========================================================================
    st.markdown('<div class="footer">Map tiles by CartoDB under CC BY-SA 3.0<br>Data © OpenStreetMap contributors</div>', unsafe_allow_html=True)

# ============================================================================
# MAIN CONTENT
# ============================================================================
# Create two columns: map (left, larger) and details panel (right, smaller)
# But we want details below map, so let's use a different layout

# Map takes full width, details below in an expander
col_map, col_side = st.columns([4, 1.2])

with col_map:
    st.markdown('<div class="map-container">', unsafe_allow_html=True)

    # ========================================================================
    # CREATE MAP
    # ========================================================================
    m = folium.Map(
        location=st.session_state.map_center,
        zoom_start=st.session_state.map_zoom,
        tiles="CartoDB Positron",
        attr='Map tiles by CartoDB under CC BY-SA 3.0. Data © OpenStreetMap contributors'
    )

    # Add Mouse Position
    MousePosition().add_to(m)

    # ========================================================================
    # ADD SAMPLE MARKERS
    # ========================================================================
    if st.session_state.layers_visible.get("hazards", True) or st.session_state.layers_visible.get("boundaries", True):
        for loc in sample_locations:
            # Determine color based on type
            if "City" in loc["type"]:
                color = "#dc3545"  # red
                icon_type = "star"
            elif "Municipality" in loc["type"]:
                color = "#4a90d9"  # blue
                icon_type = "circle"
            elif "Road" in loc["type"] or "Highway" in loc["type"]:
                color = "#28a745"  # green
                icon_type = "road"
            else:
                color = "#ffc107"  # yellow
                icon_type = "info-sign"

            # Only show if layer is visible
            if "Highway" in loc["type"] or "Road" in loc["type"]:
                if not st.session_state.layers_visible.get("roads", True):
                    continue
            else:
                if not st.session_state.layers_visible.get("boundaries", True):
                    continue

            # Create popup with details
            popup_html = f"""
            <div style="min-width:200px; font-family:sans-serif;">
                <h4 style="margin:0 0 4px 0; color:#1a1a2e;">{loc['name']}</h4>
                <div style="font-size:0.8rem; color:#6c757d; margin-bottom:6px;">{loc['type']}</div>
                <hr style="margin:4px 0; border-top:1px solid #e9ecef;">
                <div style="font-size:0.85rem;">
                    <strong>Population:</strong> {loc['population']}<br>
                    <strong>Area:</strong> {loc['area_km2']} km²<br>
                    <strong>Hazard Risk:</strong> {loc['hazard_risk']}<br>
                    <strong>Infrastructure:</strong> {loc['infrastructure']}
                </div>
                <div style="margin-top:6px; font-size:0.75rem; color:#adb5bd;">
                    Click for full details
                </div>
            </div>
            """

            # Use a custom marker
            folium.Marker(
                location=[loc["lat"], loc["lng"]],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{loc['name']} ({loc['type']})",
                icon=folium.Icon(color="red" if "City" in loc["type"] else "blue" if "Municipality" in loc["type"] else "green", icon="info-sign" if "Municipality" in loc["type"] else "star" if "City" in loc["type"] else "road", prefix="fa"),
                # Use a custom marker with id for click detection
                # Store the id in the popup or use a custom attribute
            ).add_to(m)

            # Also add a circle marker for better visibility
            folium.CircleMarker(
                location=[loc["lat"], loc["lng"]],
                radius=8,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.3,
                popup=loc["name"],
                tooltip=loc["name"]
            ).add_to(m)

    # ========================================================================
    # ADD SAMPLE POLYGONS
    # ========================================================================
    if st.session_state.layers_visible.get("hazards", True):
        for poly in sample_polygons:
            color = "#dc3545" if "Flood" in poly["name"] else "#4a90d9"
            fill_color = "#dc3545" if "Flood" in poly["name"] else "#4a90d9"
            folium.Polygon(
                locations=poly["coordinates"],
                color=color,
                weight=2,
                fill=True,
                fill_color=fill_color,
                fill_opacity=0.2,
                popup=f"<b>{poly['name']}</b><br>{poly['description']}<br>Risk: {poly['risk_level']}<br>Area: {poly['area_km2']} km²",
                tooltip=poly["name"]
            ).add_to(m)

    # ========================================================================
    # ADD DRAW PLUGIN
    # ========================================================================
    draw = Draw(
        export=False,
        position='topleft',
        draw_options={
            'polygon': {'allowIntersection': False, 'showArea': True, 'shapeOptions': {'color': '#4a90d9', 'weight': 2}},
            'polyline': {'shapeOptions': {'color': '#28a745', 'weight': 3}},
            'circle': {'shapeOptions': {'color': '#ffc107', 'weight': 2}},
            'rectangle': {'shapeOptions': {'color': '#dc3545', 'weight': 2}},
            'marker': True,
            'circlemarker': False
        },
        edit_options={'poly': {'allowIntersection': False}}
    )
    draw.add_to(m)

    # ========================================================================
    # RENDER MAP
    # ========================================================================
    map_data = st_folium(
        m,
        width="100%",
        height=600,
        returned_objects=[
            "last_clicked",
            "last_object_clicked",
            "all_drawings",
            "bounds"
        ],
        key="gis_map"
    )

    st.markdown('</div>', unsafe_allow_html=True)

    # Map attribution
    st.markdown(
        '<div style="font-size:0.65rem; color:#868e96; padding:0.25rem 0; text-align:right;">'
        'Map tiles by CartoDB under CC BY-SA 3.0. Data © OpenStreetMap contributors'
        '</div>',
        unsafe_allow_html=True
    )

# ========================================================================
# DETAILS PANEL (Right column)
# ========================================================================
with col_side:
    st.markdown("### 📋 Full Details")

    # Check if we have data from map interaction
    selected_info = None

    # Check for last clicked object
    if map_data and map_data.get("last_object_clicked"):
        clicked = map_data["last_object_clicked"]
        # Try to find matching location
        if clicked and "lat" in clicked and "lng" in clicked:
            lat = clicked["lat"]
            lng = clicked["lng"]
            # Find closest sample location
            for loc in sample_locations:
                dist = ((loc["lat"] - lat) ** 2 + (loc["lng"] - lng) ** 2) ** 0.5
                if dist < 0.005:  # Approximate match
                    selected_info = {
                        "type": "Location",
                        "data": loc,
                        "name": loc["name"]
                    }
                    break

    # Check for drawings
    if map_data and map_data.get("all_drawings"):
        drawings = map_data["all_drawings"]
        if drawings and len(drawings) > 0:
            # Get the most recent drawing
            last_drawing = drawings[-1]
            geom_type = last_drawing.get("geometry", {}).get("type", "Unknown")
            coords = last_drawing.get("geometry", {}).get("coordinates", [])

            if geom_type == "Point":
                selected_info = {
                    "type": "Point",
                    "data": {
                        "name": "Drawn Point",
                        "coordinates": coords,
                        "description": "Point drawn on map",
                        "created": datetime.now().strftime("%Y-%m-%d %H:%M")
                    },
                    "name": "Drawn Point"
                }
            elif geom_type == "Polygon":
                selected_info = {
                    "type": "Polygon",
                    "data": {
                        "name": "Drawn Polygon",
                        "coordinates": coords,
                        "description": "Polygon drawn on map",
                        "area": "Calculated on server",
                        "created": datetime.now().strftime("%Y-%m-%d %H:%M")
                    },
                    "name": "Drawn Polygon"
                }
            elif geom_type == "LineString":
                selected_info = {
                    "type": "Street",
                    "data": {
                        "name": "Drawn Street",
                        "coordinates": coords,
                        "description": "Street segment drawn on map",
                        "length": "Calculated on server",
                        "created": datetime.now().strftime("%Y-%m-%d %H:%M")
                    },
                    "name": "Drawn Street"
                }
            elif geom_type == "Circle":
                selected_info = {
                    "type": "Radius",
                    "data": {
                        "name": "Drawn Radius",
                        "coordinates": coords,
                        "description": "Radius drawn on map",
                        "radius": "Calculated on server",
                        "created": datetime.now().strftime("%Y-%m-%d %H:%M")
                    },
                    "name": "Drawn Radius"
                }

    # If nothing selected, show default info
    if not selected_info:
        # Try to get last clicked location
        if map_data and map_data.get("last_clicked"):
            click_loc = map_data["last_clicked"]
            if click_loc and "lat" in click_loc and "lng" in click_loc:
                selected_info = {
                    "type": "Map Click",
                    "data": {
                        "name": "Selected Location",
                        "coordinates": [click_loc["lat"], click_loc["lng"]],
                        "description": "Point clicked on map",
                        "created": datetime.now().strftime("%Y-%m-%d %H:%M")
                    },
                    "name": f"📍 {click_loc['lat']:.5f}, {click_loc['lng']:.5f}"
                }

    # ========================================================================
    # DISPLAY DETAILS
    # ========================================================================
    with st.container():
        if selected_info:
            info_type = selected_info.get("type", "Unknown")
            data = selected_info.get("data", {})
            name = selected_info.get("name", "Unnamed")

            # Header with close button
            col_h1, col_h2 = st.columns([5, 1])
            with col_h1:
                st.markdown(f"**{name}**")
                st.caption(f"Type: {info_type}")
            with col_h2:
                if st.button("✕", key="close_details", help="Close details"):
                    st.session_state.selected_feature = None
                    st.session_state.selected_feature_type = None
                    st.rerun()

            st.divider()

            # Show details based on type
            if info_type == "Location" and data:
                # This is a sample location
                fields = [
                    ("Name", data.get("name", "N/A")),
                    ("Type", data.get("type", "N/A")),
                    ("Population", data.get("population", "N/A")),
                    ("Area", f"{data.get('area_km2', 'N/A')} km²"),
                    ("Hazard Risk", data.get("hazard_risk", "N/A")),
                    ("Infrastructure", data.get("infrastructure", "N/A")),
                    ("Coordinates", f"{data.get('lat', 'N/A')}, {data.get('lng', 'N/A')}")
                ]
                for label, value in fields:
                    st.markdown(f"**{label}:** {value}")

            elif info_type in ["Point", "Map Click"] and data:
                coords = data.get("coordinates", [])
                if coords:
                    if isinstance(coords[0], list):
                        # Nested coords
                        lat_str = f"{coords[0][0]:.5f}" if len(coords[0]) > 0 else "N/A"
                        lng_str = f"{coords[0][1]:.5f}" if len(coords[0]) > 1 else "N/A"
                        st.markdown(f"**Coordinates:** {lat_str}, {lng_str}")
                    else:
                        st.markdown(f"**Coordinates:** {coords[0]:.5f}, {coords[1]:.5f}")
                st.markdown(f"**Description:** {data.get('description', 'No description')}")
                st.markdown(f"**Created:** {data.get('created', 'N/A')}")

            elif info_type == "Polygon" and data:
                coords = data.get("coordinates", [])
                if coords and isinstance(coords[0], list):
                    st.markdown(f"**Number of vertices:** {len(coords[0])}")
                    st.markdown(f"**Area:** {data.get('area', 'Calculating...')}")
                st.markdown(f"**Description:** {data.get('description', 'No description')}")
                st.markdown(f"**Created:** {data.get('created', 'N/A')}")

            elif info_type == "Street" and data:
                coords = data.get("coordinates", [])
                if coords and isinstance(coords[0], list):
                    st.markdown(f"**Number of points:** {len(coords[0])}")
                    st.markdown(f"**Length:** {data.get('length', 'Calculating...')}")
                st.markdown(f"**Description:** {data.get('description', 'No description')}")
                st.markdown(f"**Created:** {data.get('created', 'N/A')}")

            elif info_type == "Radius" and data:
                coords = data.get("coordinates", [])
                if coords and isinstance(coords[0], list):
                    st.markdown(f"**Center:** {coords[0][0]:.5f}, {coords[0][1]:.5f}")
                    st.markdown(f"**Radius:** {data.get('radius', 'Calculating...')}")
                st.markdown(f"**Description:** {data.get('description', 'No description')}")
                st.markdown(f"**Created:** {data.get('created', 'N/A')}")

            else:
                st.info("Select a feature on the map to see details here.")
        else:
            # No selection - show instruction and recent activities
            st.info("👆 Click on a marker, polygon, or draw on the map to see details here.")

            # Show recent activity
            if map_data and map_data.get("last_clicked"):
                click_loc = map_data["last_clicked"]
                st.caption(f"🖱️ Last click: {click_loc['lat']:.5f}, {click_loc['lng']:.5f}")

            # Show active drawing count
            if map_data and map_data.get("all_drawings"):
                draw_count = len(map_data["all_drawings"])
                st.caption(f"✏️ Active drawings: {draw_count}")

            # Layer status
            st.divider()
            st.caption("🗺️ Active layers:")
            active_layers = [k for k, v in st.session_state.layers_visible.items() if v]
            if active_layers:
                st.caption(", ".join(active_layers).title())
            else:
                st.caption("No layers active")

            # Location mode
            st.caption(f"📍 Input mode: {st.session_state.location_input_mode}")

    # ========================================================================
    # RESIZE HANDLE (visual only)
    # ========================================================================
    st.markdown(
        '<div class="resize-hint">↕︎ Drag to resize</div>',
        unsafe_allow_html=True
    )

# ============================================================================
# BOTTOM SECTION - Additional details / expandable
# ============================================================================
with st.expander("📊 Advanced Analytics & Data Interpretation", expanded=False):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 📈 Valuation Metrics")
        st.metric("Average Rental Rate", "₱ 850/m²", "↑ 3.2%")
        st.metric("PRIME Core Index", "87.5", "↑ 1.8%")
        st.caption("Data from Lamudi & other property platforms")

    with col2:
        st.markdown("#### 🏗️ Infrastructure Score")
        st.metric("Road Network Density", "2.4 km/km²", "↑ 0.3")
        st.metric("Zoning Compliance", "94%", "↑ 2%")
        st.caption("LGU Restrictions & CLUP analysis")

    with col3:
        st.markdown("#### ⚠️ Hazard Assessment")
        st.metric("Flood Risk Index", "Medium (4.2)", "↓ 0.5")
        st.metric("Earthquake Susceptibility", "Low (2.1)", "→ 0.0")
        st.caption("Multi-hazard risk assessment")

    st.divider()
    st.caption("📊 Power BI dashboard integration available for advanced data interpretation")
    st.caption("💡 Smart Comparable Analysis: Advanced scoring algorithms for property valuation")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("""
    <div style="font-size:0.7rem; color:#adb5bd; text-align:center; padding:0.5rem 0; border-top:1px solid #e9ecef; margin-top:0.5rem;">
        GIS Analysis Tool Prototype • Powered by Streamlit & Leaflet • Data © OpenStreetMap contributors
    </div>
""", unsafe_allow_html=True)
