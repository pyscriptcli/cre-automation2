import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw, MousePosition
import json
from datetime import datetime
import re

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Project APEX - GIS Analysis",
    page_icon=":globe_with_meridians:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS - Hide toolbar, full map, floating panels
# ============================================================================
st.markdown("""
    <style>
    /* Hide Streamlit toolbar */
    .stAppToolbar, .stMainMenu, #MainMenu, footer {
        display: none !important;
    }
    /* Remove default padding */
    .main > div {
        padding: 0 !important;
        margin: 0 !important;
    }
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }
    /* Sidebar overlay */
    section[data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.92);
        backdrop-filter: blur(6px);
        border-right: 1px solid rgba(0,0,0,0.08);
        padding-top: 1rem;
        z-index: 1000;
        width: 320px !important;
        box-shadow: 2px 0 12px rgba(0,0,0,0.08);
    }
    .sidebar-section {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #6c757d;
        margin-top: 0.75rem;
        margin-bottom: 0.25rem;
        padding-bottom: 0.25rem;
        border-bottom: 1px solid #e9ecef;
    }
    .app-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1a1a2e;
        padding: 0.5rem 0 0.2rem 0;
        border-bottom: 2px solid #4a90d9;
        display: inline-block;
    }
    /* Full‑screen map */
    .map-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: 0;
    }
    /* Floating details panel */
    .floating-panel {
        position: fixed;
        top: 20px;
        right: 20px;
        width: 360px;
        max-height: calc(100vh - 40px);
        overflow-y: auto;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(8px);
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.15);
        padding: 1.2rem 1.5rem;
        z-index: 999;
        border: 1px solid rgba(255,255,255,0.2);
    }
    .floating-panel h4 {
        margin-top: 0;
        margin-bottom: 0.5rem;
        font-weight: 600;
        color: #1a1a2e;
        border-bottom: 2px solid #4a90d9;
        padding-bottom: 0.4rem;
    }
    .floating-panel .detail-label {
        font-size: 0.7rem;
        font-weight: 600;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    .floating-panel .detail-value {
        font-size: 0.9rem;
        color: #1a1a2e;
        margin-bottom: 0.3rem;
    }
    .floating-panel .divider {
        border: none;
        border-top: 1px solid #f1f3f5;
        margin: 0.6rem 0;
    }
    .floating-panel .close-btn {
        float: right;
        background: none;
        border: none;
        font-size: 1.2rem;
        color: #adb5bd;
        cursor: pointer;
    }
    .floating-panel .close-btn:hover {
        color: #495057;
    }
    .floating-panel::-webkit-scrollbar {
        width: 4px;
    }
    .floating-panel::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    .floating-panel::-webkit-scrollbar-thumb {
        background: #c1c7cd;
        border-radius: 4px;
    }
    .footer {
        font-size: 0.65rem;
        color: #adb5bd;
        text-align: center;
        padding: 0.5rem 0;
        border-top: 1px solid #e9ecef;
        margin-top: 0.5rem;
    }
    @media (max-width: 768px) {
        .floating-panel {
            width: 300px;
            right: 10px;
            top: 10px;
            max-height: calc(100vh - 20px);
            padding: 1rem;
        }
        section[data-testid="stSidebar"] {
            width: 280px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE
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

# Sub‑layer visibility: all sub‑layers toggled individually
if "sub_layers" not in st.session_state:
    st.session_state.sub_layers = {
        "earthquake": True,
        "floods": True,
        "landslide": False,
        "tsunami": False,
        "volcanic": False,
        "roads": True,
        "boundaries": True,
        "zoning": False,
        "valuation": False,
        "rental_rate": False,
        "prime_core": False,
        "lamudi": False,
        "other_platforms": False
    }

if "basemap" not in st.session_state:
    st.session_state.basemap = "CartoDB Positron"
if "panel_visible" not in st.session_state:
    st.session_state.panel_visible = True

# ============================================================================
# SAMPLE DATA
# ============================================================================
sample_locations = [
    {"id": 1, "name": "Plaridel", "lat": 14.8875, "lng": 120.8567, "type": "Municipality",
     "description": "Municipal hall and town center", "population": "41,000", "area_km2": "32.44",
     "hazard_risk": "Moderate", "infrastructure": "Good road network"},
    {"id": 2, "name": "Tabang Spur Road", "lat": 14.8950, "lng": 120.8700, "type": "Road Junction",
     "description": "Major intersection connecting to MacArthur Highway", "population": "N/A",
     "area_km2": "N/A", "hazard_risk": "Low", "infrastructure": "Highway junction"},
    {"id": 3, "name": "MacArthur Highway", "lat": 14.8980, "lng": 120.8780, "type": "Highway",
     "description": "Primary north-south thoroughfare", "population": "N/A", "area_km2": "N/A",
     "hazard_risk": "Low", "infrastructure": "Major highway"},
    {"id": 4, "name": "Santa Maria", "lat": 14.8183, "lng": 120.9567, "type": "Municipality",
     "description": "Town center with commercial district", "population": "289,000", "area_km2": "90.92",
     "hazard_risk": "Moderate", "infrastructure": "Developing urban center"},
    {"id": 5, "name": "San Jose del Monte", "lat": 14.8139, "lng": 121.0450, "type": "City",
     "description": "Component city, major residential area", "population": "651,000", "area_km2": "105.53",
     "hazard_risk": "High (flooding)", "infrastructure": "Expanding infrastructure"},
    {"id": 6, "name": "Meycauayan", "lat": 14.7333, "lng": 120.9500, "type": "City",
     "description": "Industrial and commercial hub", "population": "225,000", "area_km2": "32.10",
     "hazard_risk": "Moderate", "infrastructure": "Well-developed"},
    {"id": 7, "name": "Montalban (Rodriguez)", "lat": 14.7000, "lng": 121.1167, "type": "Municipality",
     "description": "Growing suburban area", "population": "370,000", "area_km2": "172.53",
     "hazard_risk": "Moderate", "infrastructure": "Developing"}
]

sample_polygons = [
    {"id": 101, "name": "Flood Zone A - Santa Maria", "type": "Hazard Zone",
     "description": "High risk flood area along river basin",
     "coordinates": [[14.8350, 120.9400], [14.8300, 120.9600], [14.8100, 120.9650],
                     [14.8000, 120.9450], [14.8150, 120.9300]],
     "risk_level": "High", "area_km2": "8.5"},
    {"id": 102, "name": "Commercial Zone - Meycauayan", "type": "Zoning",
     "description": "Designated commercial and industrial zone",
     "coordinates": [[14.7450, 120.9450], [14.7400, 120.9600], [14.7250, 120.9550],
                     [14.7280, 120.9400]],
     "risk_level": "Low", "area_km2": "3.2"}
]

# ============================================================================
# FUNCTIONS
# ============================================================================
def parse_location_input(text):
    text = text.strip()
    coord_pattern = re.compile(r'^\s*([-+]?\d*\.?\d+)\s*[,;]\s*([-+]?\d*\.?\d+)\s*$')
    match = coord_pattern.match(text)
    if match:
        return {"lat": float(match.group(1)), "lng": float(match.group(2)), "type": "coordinates"}
    for loc in sample_locations:
        if text.lower() in loc["name"].lower():
            return {"lat": loc["lat"], "lng": loc["lng"], "type": "location", "name": loc["name"]}
    return None

# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    st.markdown('<div class="app-title">Project APEX</div>', unsafe_allow_html=True)

    # Location input
    st.markdown('<div class="sidebar-section">Location</div>', unsafe_allow_html=True)
    loc_input = st.text_input("Enter coordinates (lat, lng) or place name", key="loc_input",
                              placeholder="e.g. 14.8875, 120.8567 or Plaridel")
    if st.button("Search Location", use_container_width=True):
        result = parse_location_input(loc_input)
        if result:
            st.session_state.map_center = [result["lat"], result["lng"]]
            st.session_state.map_zoom = 13
            st.rerun()
        else:
            st.warning("Location not found. Try coordinates like '14.8875, 120.8567'")

    # Data Layers - collapsible expander with checkboxes for sub‑layers
    with st.expander("Data Layers", expanded=True):
        # Hazards sub‑layers
        st.markdown("**Hazards**")
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.sub_layers["earthquake"] = st.checkbox("Earthquake", value=st.session_state.sub_layers["earthquake"])
            st.session_state.sub_layers["floods"] = st.checkbox("Floods", value=st.session_state.sub_layers["floods"])
            st.session_state.sub_layers["landslide"] = st.checkbox("Landslide", value=st.session_state.sub_layers["landslide"])
        with col2:
            st.session_state.sub_layers["tsunami"] = st.checkbox("Tsunami", value=st.session_state.sub_layers["tsunami"])
            st.session_state.sub_layers["volcanic"] = st.checkbox("Volcanic", value=st.session_state.sub_layers["volcanic"])

        st.markdown("**Infrastructure**")
        st.session_state.sub_layers["roads"] = st.checkbox("Roads", value=st.session_state.sub_layers["roads"])
        st.session_state.sub_layers["boundaries"] = st.checkbox("Boundaries (Cities, Province, Region)", value=st.session_state.sub_layers["boundaries"])
        st.session_state.sub_layers["zoning"] = st.checkbox("Zoning (LGU Restrictions, CLUP)", value=st.session_state.sub_layers["zoning"])

        st.markdown("**Valuation**")
        st.session_state.sub_layers["valuation"] = st.checkbox("Valuation (general)", value=st.session_state.sub_layers["valuation"])
        # Sub‑options for valuation (optional)
        if st.session_state.sub_layers["valuation"]:
            st.session_state.sub_layers["rental_rate"] = st.checkbox("Rental Rate", value=st.session_state.sub_layers["rental_rate"])
            st.session_state.sub_layers["prime_core"] = st.checkbox("PRIME Core", value=st.session_state.sub_layers["prime_core"])
            st.session_state.sub_layers["lamudi"] = st.checkbox("Lamudi", value=st.session_state.sub_layers["lamudi"])
            st.session_state.sub_layers["other_platforms"] = st.checkbox("Other Platforms", value=st.session_state.sub_layers["other_platforms"])

    # Manage layer button (keep for compatibility, but can be removed)
    st.button("Manage layer", use_container_width=True, key="manage_layer")

    # Basemap selector (still in sidebar for convenience)
    basemap_options = {
        "CartoDB Positron": "CartoDB Positron",
        "CartoDB Dark_Matter": "CartoDB Dark_Matter",
        "OpenStreetMap": "OpenStreetMap",
        "Stamen Terrain": "Stamen Terrain",
        "Stamen Toner": "Stamen Toner"
    }
    selected_basemap = st.selectbox("Base Map", list(basemap_options.keys()), index=0)
    if selected_basemap != st.session_state.basemap:
        st.session_state.basemap = basemap_options[selected_basemap]
        st.rerun()

    st.markdown('<div class="footer">Map tiles by CartoDB under CC BY-SA 3.0<br>Data © OpenStreetMap contributors</div>', unsafe_allow_html=True)

# ============================================================================
# MAIN MAP (full screen)
# ============================================================================
map_container = st.container()
with map_container:
    st.markdown('<div class="map-container" id="map-container">', unsafe_allow_html=True)

    # Create map with selected basemap
    m = folium.Map(
        location=st.session_state.map_center,
        zoom_start=st.session_state.map_zoom,
        tiles=st.session_state.basemap,
        attr='Map tiles by CartoDB under CC BY-SA 3.0. Data © OpenStreetMap contributors'
    )

    MousePosition().add_to(m)

    # ========================================================================
    # ADD BASEMAP SWITCHER (LayerControl) - appears in top-right corner
    # ========================================================================
    # Define additional tile layers for switching
    folium.TileLayer('CartoDB Dark_Matter', name='Dark').add_to(m)
    folium.TileLayer('OpenStreetMap', name='OSM').add_to(m)
    folium.TileLayer('Stamen Terrain', name='Terrain').add_to(m)
    folium.TileLayer('Stamen Toner', name='Toner').add_to(m)
    # Add LayerControl after tiles
    folium.LayerControl(collapsed=False).add_to(m)

    # ========================================================================
    # ADD SAMPLE MARKERS WITH SUB‑LAYER FILTERING
    # ========================================================================
    # We'll show markers based on sub‑layer toggles:
    # - If "roads" is on, show road/highway markers
    # - If "boundaries" is on, show municipality/city markers
    # - "hazards" are shown via polygons; we also show hazard markers if any

    # Filter markers based on sub‑layer visibility
    show_roads = st.session_state.sub_layers.get("roads", True)
    show_boundaries = st.session_state.sub_layers.get("boundaries", True)
    show_hazards = st.session_state.sub_layers.get("floods", True) or st.session_state.sub_layers.get("earthquake", True)  # etc.

    for loc in sample_locations:
        # Determine if this marker should be shown
        is_road = "Road" in loc["type"] or "Highway" in loc["type"]
        is_boundary = "Municipality" in loc["type"] or "City" in loc["type"]
        if is_road and not show_roads:
            continue
        if is_boundary and not show_boundaries:
            continue
        # For hazards, we might have specific markers, but we'll show all if any hazard sub‑layer is on
        # Actually we don't have hazard-specific markers, so we'll show all if hazards are on
        # But we already filtered by roads/boundaries, so we show everything else
        # if not show_hazards and not is_road and not is_boundary: continue  # but we have no others

        color = "#dc3545" if "City" in loc["type"] else "#4a90d9" if "Municipality" in loc["type"] else "#28a745"
        popup_html = f"""
        <div style="min-width:200px;">
            <h4 style="margin:0 0 4px 0;">{loc['name']}</h4>
            <div style="font-size:0.8rem; color:#6c757d;">{loc['type']}</div>
            <hr style="margin:4px 0;">
            <div style="font-size:0.85rem;">
                <strong>Population:</strong> {loc['population']}<br>
                <strong>Area:</strong> {loc['area_km2']} km²<br>
                <strong>Hazard Risk:</strong> {loc['hazard_risk']}<br>
                <strong>Infrastructure:</strong> {loc['infrastructure']}
            </div>
            <div style="margin-top:6px; font-size:0.75rem; color:#adb5bd;">Click for full details</div>
        </div>
        """
        folium.Marker(
            location=[loc["lat"], loc["lng"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{loc['name']} ({loc['type']})",
            icon=folium.Icon(color="red" if "City" in loc["type"] else "blue" if "Municipality" in loc["type"] else "green",
                             icon="info-sign" if "Municipality" in loc["type"] else "star" if "City" in loc["type"] else "road",
                             prefix="fa")
        ).add_to(m)
        folium.CircleMarker(
            location=[loc["lat"], loc["lng"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.3,
            tooltip=loc["name"]
        ).add_to(m)

    # ========================================================================
    # ADD POLYGONS - filtered by hazard sub‑layers
    # ========================================================================
    show_floods = st.session_state.sub_layers.get("floods", True)
    show_zoning = st.session_state.sub_layers.get("zoning", True)

    for poly in sample_polygons:
        if "Flood" in poly["name"] and not show_floods:
            continue
        if "Commercial" in poly["name"] and not show_zoning:
            continue
        color = "#dc3545" if "Flood" in poly["name"] else "#4a90d9"
        fill_color = color
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
    # DRAW PLUGIN (still active for defining assessment areas)
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

    map_data = st_folium(
        m,
        width="100%",
        height=800,
        returned_objects=["last_clicked", "last_object_clicked", "all_drawings", "bounds"],
        key="gis_map"
    )

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# FLOATING DETAILS PANEL (right side)
# ============================================================================
selected_info = None

if map_data and map_data.get("last_object_clicked"):
    clicked = map_data["last_object_clicked"]
    if clicked and "lat" in clicked and "lng" in clicked:
        lat = clicked["lat"]
        lng = clicked["lng"]
        for loc in sample_locations:
            dist = ((loc["lat"] - lat) ** 2 + (loc["lng"] - lng) ** 2) ** 0.5
            if dist < 0.005:
                selected_info = {"type": "Location", "data": loc, "name": loc["name"]}
                break

if not selected_info and map_data and map_data.get("all_drawings"):
    drawings = map_data["all_drawings"]
    if drawings and len(drawings) > 0:
        last_drawing = drawings[-1]
        geom_type = last_drawing.get("geometry", {}).get("type", "Unknown")
        coords = last_drawing.get("geometry", {}).get("coordinates", [])
        if geom_type == "Point":
            selected_info = {"type": "Point", "name": "Drawn Point",
                             "data": {"name": "Drawn Point", "coordinates": coords,
                                      "description": "Point drawn on map",
                                      "created": datetime.now().strftime("%Y-%m-%d %H:%M")}}
        elif geom_type == "Polygon":
            selected_info = {"type": "Polygon", "name": "Drawn Polygon",
                             "data": {"name": "Drawn Polygon", "coordinates": coords,
                                      "description": "Polygon drawn on map", "area": "Calculated on server",
                                      "created": datetime.now().strftime("%Y-%m-%d %H:%M")}}
        elif geom_type == "LineString":
            selected_info = {"type": "Street", "name": "Drawn Street",
                             "data": {"name": "Drawn Street", "coordinates": coords,
                                      "description": "Street segment drawn on map", "length": "Calculated on server",
                                      "created": datetime.now().strftime("%Y-%m-%d %H:%M")}}
        elif geom_type == "Circle":
            selected_info = {"type": "Radius", "name": "Drawn Radius",
                             "data": {"name": "Drawn Radius", "coordinates": coords,
                                      "description": "Radius drawn on map", "radius": "Calculated on server",
                                      "created": datetime.now().strftime("%Y-%m-%d %H:%M")}}

if not selected_info and map_data and map_data.get("last_clicked"):
    click_loc = map_data["last_clicked"]
    if click_loc and "lat" in click_loc and "lng" in click_loc:
        selected_info = {"type": "Map Click", "name": f"{click_loc['lat']:.5f}, {click_loc['lng']:.5f}",
                         "data": {"name": "Selected Location",
                                  "coordinates": [click_loc["lat"], click_loc["lng"]],
                                  "description": "Point clicked on map",
                                  "created": datetime.now().strftime("%Y-%m-%d %H:%M")}}

panel_html = '<div class="floating-panel" id="floating-panel">'

if selected_info:
    info_type = selected_info.get("type", "Unknown")
    data = selected_info.get("data", {})
    name = selected_info.get("name", "Unnamed")

    panel_html += f"""
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <h4 style="margin:0;">{name}</h4>
        <button class="close-btn" onclick="document.getElementById('floating-panel').style.display='none';">&times;</button>
    </div>
    <div style="font-size:0.8rem; color:#6c757d; margin-bottom:0.5rem;">Type: {info_type}</div>
    <hr class="divider">
    """

    if info_type == "Location" and data:
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
            panel_html += f'<div class="detail-label">{label}</div><div class="detail-value">{value}</div>'

    elif info_type in ["Point", "Map Click"] and data:
        coords = data.get("coordinates", [])
        if coords:
            if isinstance(coords[0], list):
                lat_str = f"{coords[0][0]:.5f}" if len(coords[0]) > 0 else "N/A"
                lng_str = f"{coords[0][1]:.5f}" if len(coords[0]) > 1 else "N/A"
                panel_html += f'<div class="detail-label">Coordinates</div><div class="detail-value">{lat_str}, {lng_str}</div>'
            else:
                panel_html += f'<div class="detail-label">Coordinates</div><div class="detail-value">{coords[0]:.5f}, {coords[1]:.5f}</div>'
        panel_html += f'<div class="detail-label">Description</div><div class="detail-value">{data.get("description", "No description")}</div>'
        panel_html += f'<div class="detail-label">Created</div><div class="detail-value">{data.get("created", "N/A")}</div>'

    elif info_type == "Polygon" and data:
        coords = data.get("coordinates", [])
        if coords and isinstance(coords[0], list):
            panel_html += f'<div class="detail-label">Number of vertices</div><div class="detail-value">{len(coords[0])}</div>'
            panel_html += f'<div class="detail-label">Area</div><div class="detail-value">{data.get("area", "Calculating...")}</div>'
        panel_html += f'<div class="detail-label">Description</div><div class="detail-value">{data.get("description", "No description")}</div>'
        panel_html += f'<div class="detail-label">Created</div><div class="detail-value">{data.get("created", "N/A")}</div>'

    elif info_type == "Street" and data:
        coords = data.get("coordinates", [])
        if coords and isinstance(coords[0], list):
            panel_html += f'<div class="detail-label">Number of points</div><div class="detail-value">{len(coords[0])}</div>'
            panel_html += f'<div class="detail-label">Length</div><div class="detail-value">{data.get("length", "Calculating...")}</div>'
        panel_html += f'<div class="detail-label">Description</div><div class="detail-value">{data.get("description", "No description")}</div>'
        panel_html += f'<div class="detail-label">Created</div><div class="detail-value">{data.get("created", "N/A")}</div>'

    elif info_type == "Radius" and data:
        coords = data.get("coordinates", [])
        if coords and isinstance(coords[0], list):
            panel_html += f'<div class="detail-label">Center</div><div class="detail-value">{coords[0][0]:.5f}, {coords[0][1]:.5f}</div>'
            panel_html += f'<div class="detail-label">Radius</div><div class="detail-value">{data.get("radius", "Calculating...")}</div>'
        panel_html += f'<div class="detail-label">Description</div><div class="detail-value">{data.get("description", "No description")}</div>'
        panel_html += f'<div class="detail-label">Created</div><div class="detail-value">{data.get("created", "N/A")}</div>'

    else:
        panel_html += "<div>No details available for this selection.</div>"

    # Advanced Analytics section
    panel_html += """
    <hr class="divider">
    <h4 style="font-size:1rem; margin-top:0.8rem;">Advanced Analytics</h4>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; font-size:0.85rem;">
        <div><span class="detail-label">Avg Rental Rate</span><br><span class="detail-value" style="font-weight:600;">₱ 850/m²</span> <span style="color:#28a745;">↑3.2%</span></div>
        <div><span class="detail-label">PRIME Core Index</span><br><span class="detail-value" style="font-weight:600;">87.5</span> <span style="color:#28a745;">↑1.8%</span></div>
        <div><span class="detail-label">Road Density</span><br><span class="detail-value" style="font-weight:600;">2.4 km/km²</span> <span style="color:#28a745;">↑0.3</span></div>
        <div><span class="detail-label">Zoning Compliance</span><br><span class="detail-value" style="font-weight:600;">94%</span> <span style="color:#28a745;">↑2%</span></div>
        <div><span class="detail-label">Flood Risk Index</span><br><span class="detail-value" style="font-weight:600;">Medium (4.2)</span> <span style="color:#dc3545;">↓0.5</span></div>
        <div><span class="detail-label">Earthquake Suscept.</span><br><span class="detail-value" style="font-weight:600;">Low (2.1)</span> <span style="color:#6c757d;">→0.0</span></div>
    </div>
    <div style="font-size:0.7rem; color:#6c757d; margin-top:0.5rem; border-top:1px solid #e9ecef; padding-top:0.5rem;">
        Smart Comparable Analysis: Advanced scoring algorithms for property valuation
    </div>
    """

else:
    panel_html += """
    <h4 style="margin-top:0;">Details</h4>
    <div style="color:#6c757d; font-size:0.9rem;">Click on a marker, polygon, or draw on the map to see details here.</div>
    <hr class="divider">
    <div style="font-size:0.8rem; color:#6c757d;">
        <div><span class="detail-label">Last click</span><br><span class="detail-value">-</span></div>
        <div><span class="detail-label">Active drawings</span><br><span class="detail-value">0</span></div>
    </div>
    <hr class="divider">
    <h4 style="font-size:1rem; margin-top:0.8rem;">Advanced Analytics</h4>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; font-size:0.85rem;">
        <div><span class="detail-label">Avg Rental Rate</span><br><span class="detail-value" style="font-weight:600;">₱ 850/m²</span> <span style="color:#28a745;">↑3.2%</span></div>
        <div><span class="detail-label">PRIME Core Index</span><br><span class="detail-value" style="font-weight:600;">87.5</span> <span style="color:#28a745;">↑1.8%</span></div>
        <div><span class="detail-label">Road Density</span><br><span class="detail-value" style="font-weight:600;">2.4 km/km²</span> <span style="color:#28a745;">↑0.3</span></div>
        <div><span class="detail-label">Zoning Compliance</span><br><span class="detail-value" style="font-weight:600;">94%</span> <span style="color:#28a745;">↑2%</span></div>
        <div><span class="detail-label">Flood Risk Index</span><br><span class="detail-value" style="font-weight:600;">Medium (4.2)</span> <span style="color:#dc3545;">↓0.5</span></div>
        <div><span class="detail-label">Earthquake Suscept.</span><br><span class="detail-value" style="font-weight:600;">Low (2.1)</span> <span style="color:#6c757d;">→0.0</span></div>
    </div>
    <div style="font-size:0.7rem; color:#6c757d; margin-top:0.5rem; border-top:1px solid #e9ecef; padding-top:0.5rem;">
        Smart Comparable Analysis: Advanced scoring algorithms for property valuation
    </div>
    """

panel_html += "</div>"
st.markdown(panel_html, unsafe_allow_html=True)
