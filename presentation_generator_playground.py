import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
import geopandas as gpd
from shapely.geometry import Polygon, Point, LineString
import tempfile
import os
import json

st.set_page_config(
    page_title="Felt",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for exact Felt UI clone
st.markdown("""
<style>
    /* Reset and base */
    .main {
        padding: 0px !important;
        margin: 0px !important;
    }
    .block-container {
        padding: 0px !important;
        margin: 0px !important;
        max-width: 100% !important;
    }
    
    /* Top bar */
    .felt-topbar {
        background-color: white;
        border-bottom: 1px solid #e8e8e8;
        padding: 8px 20px;
        display: flex;
        align-items: center;
        gap: 20px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .felt-logo {
        font-weight: 600;
        font-size: 18px;
        color: #1a1a1a;
    }
    .felt-logo span {
        color: #4285f4;
    }
    .felt-draft {
        color: #666;
        font-size: 14px;
        background: #f5f5f5;
        padding: 4px 12px;
        border-radius: 4px;
    }
    
    /* Sidebar */
    .felt-sidebar {
        background-color: #f8f9fa;
        border-right: 1px solid #e8e8e8;
        padding: 16px 12px;
        height: calc(100vh - 60px);
        overflow-y: auto;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .felt-sidebar::-webkit-scrollbar {
        width: 6px;
    }
    .felt-sidebar::-webkit-scrollbar-thumb {
        background: #d0d0d0;
        border-radius: 3px;
    }
    
    /* Section headers */
    .felt-section-title {
        font-size: 11px;
        font-weight: 600;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin: 16px 0 8px 0;
        padding: 0 4px;
    }
    
    /* Layer items */
    .felt-layer {
        display: flex;
        align-items: center;
        padding: 8px 10px;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.15s;
        font-size: 13px;
        color: #1a1a1a;
        margin-bottom: 2px;
        background: white;
        border: 1px solid transparent;
    }
    .felt-layer:hover {
        background: #f0f4ff;
        border-color: #d0d9ff;
    }
    .felt-layer.active {
        background: #e8edff;
        border-color: #4285f4;
    }
    .felt-layer-icon {
        margin-right: 10px;
        font-size: 14px;
    }
    .felt-layer-name {
        flex: 1;
    }
    .felt-layer-delete {
        color: #999;
        cursor: pointer;
        font-size: 14px;
        padding: 0 4px;
    }
    .felt-layer-delete:hover {
        color: #e74c3c;
    }
    
    /* Create layer input */
    .felt-create-layer {
        display: flex;
        gap: 6px;
        margin-top: 4px;
    }
    .felt-create-layer input {
        flex: 1;
        padding: 6px 10px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 13px;
        outline: none;
    }
    .felt-create-layer input:focus {
        border-color: #4285f4;
    }
    .felt-create-layer button {
        padding: 6px 12px;
        background: #4285f4;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 13px;
    }
    .felt-create-layer button:hover {
        background: #3367d6;
    }
    
    /* Tool buttons */
    .felt-tool-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 4px;
        margin: 4px 0;
    }
    .felt-tool-btn {
        padding: 8px 4px;
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        cursor: pointer;
        text-align: center;
        font-size: 12px;
        color: #333;
        transition: all 0.15s;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .felt-tool-btn:hover {
        background: #f0f4ff;
        border-color: #4285f4;
    }
    .felt-tool-btn.active {
        background: #e8edff;
        border-color: #4285f4;
        box-shadow: 0 0 0 2px rgba(66, 133, 244, 0.2);
    }
    .felt-tool-icon {
        font-size: 18px;
        display: block;
        margin-bottom: 2px;
    }
    
    /* Action buttons */
    .felt-action-btn {
        padding: 8px 12px;
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        cursor: pointer;
        text-align: left;
        font-size: 13px;
        color: #333;
        transition: all 0.15s;
        width: 100%;
        margin: 2px 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .felt-action-btn:hover {
        background: #f5f5f5;
        border-color: #ccc;
    }
    
    /* Style controls */
    .felt-style-group {
        background: white;
        padding: 10px 12px;
        border-radius: 6px;
        border: 1px solid #e0e0e0;
        margin: 4px 0;
    }
    .felt-style-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 4px 0;
        font-size: 13px;
        color: #333;
    }
    .felt-style-label {
        color: #666;
        font-size: 12px;
    }
    .felt-opacity-display {
        background: #f0f0f0;
        padding: 0 8px;
        border-radius: 3px;
        font-size: 12px;
        color: #666;
    }
    
    /* On click selector */
    .felt-select {
        width: 100%;
        padding: 4px 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 12px;
        background: white;
        color: #333;
        outline: none;
        margin-top: 4px;
    }
    .felt-select:focus {
        border-color: #4285f4;
    }
    
    /* Map container */
    .felt-map {
        height: calc(100vh - 60px);
        width: 100%;
    }
    
    /* Annotation list */
    .felt-annotation-item {
        background: white;
        padding: 8px 12px;
        border-radius: 4px;
        border-left: 3px solid #4285f4;
        margin: 4px 0;
        font-size: 13px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .felt-annotation-name {
        font-weight: 500;
        color: #1a1a1a;
    }
    .felt-annotation-type {
        font-size: 11px;
        color: #888;
        text-transform: uppercase;
    }
    .felt-annotation-delete {
        color: #ccc;
        cursor: pointer;
        padding: 0 4px;
    }
    .felt-annotation-delete:hover {
        color: #e74c3c;
    }
    
    /* Divider */
    .felt-divider {
        border-top: 1px solid #e8e8e8;
        margin: 12px 0;
    }
    
    /* Name input */
    .felt-input {
        width: 100%;
        padding: 6px 10px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 13px;
        outline: none;
        margin: 4px 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .felt-input:focus {
        border-color: #4285f4;
    }
    .felt-textarea {
        width: 100%;
        padding: 6px 10px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 13px;
        outline: none;
        margin: 4px 0;
        resize: vertical;
        min-height: 50px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .felt-textarea:focus {
        border-color: #4285f4;
    }
    
    /* Save button */
    .felt-save-btn {
        width: 100%;
        padding: 8px;
        background: #4285f4;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        margin: 4px 0;
        transition: background 0.15s;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .felt-save-btn:hover {
        background: #3367d6;
    }
    
    /* Street label on map - we'll use folium for this */
    .custom-html-label {
        font-size: 11px;
        font-weight: 500;
        color: #333;
        text-shadow: 0 0 4px white, 0 0 4px white;
    }
    
    /* Map attribution */
    .felt-attribution {
        position: fixed;
        bottom: 8px;
        right: 12px;
        font-size: 10px;
        color: #888;
        background: rgba(255,255,255,0.9);
        padding: 2px 8px;
        border-radius: 3px;
        z-index: 1000;
        pointer-events: none;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'polygons' not in st.session_state:
    st.session_state.polygons = []
if 'lines' not in st.session_state:
    st.session_state.lines = []
if 'points' not in st.session_state:
    st.session_state.points = []
if 'routes' not in st.session_state:
    st.session_state.routes = []
if 'layers' not in st.session_state:
    st.session_state.layers = {'Default': {'annotations': []}}
if 'current_layer' not in st.session_state:
    st.session_state.current_layer = 'Default'
if 'draw_mode' not in st.session_state:
    st.session_state.draw_mode = None
if 'annotations' not in st.session_state:
    st.session_state.annotations = []
if 'show_save_form' not in st.session_state:
    st.session_state.show_save_form = False
if 'pending_annotation' not in st.session_state:
    st.session_state.pending_annotation = None

# Top bar
st.markdown("""
<div class="felt-topbar">
    <div class="felt-logo">🗺️ <span>Felt</span></div>
    <div class="felt-draft">Drafts &gt; 2nd Batch TA</div>
</div>
""", unsafe_allow_html=True)

# Main layout
col_sidebar, col_map = st.columns([280, 1])

with col_sidebar:
    st.markdown('<div class="felt-sidebar">', unsafe_allow_html=True)
    
    # LAYERS section
    st.markdown('<div class="felt-section-title">LAYERS</div>', unsafe_allow_html=True)
    
    # Display layers
    for layer_name in st.session_state.layers.keys():
        is_active = layer_name == st.session_state.current_layer
        active_class = "active" if is_active else ""
        st.markdown(f"""
        <div class="felt-layer {active_class}" onclick="this.click()">
            <span class="felt-layer-icon">📁</span>
            <span class="felt-layer-name">{layer_name}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # We need actual buttons for interaction
        col1, col2 = st.columns([5, 1])
        with col1:
            if st.button(f"📁 {layer_name}", key=f"layer_{layer_name}", help="Select layer"):
                st.session_state.current_layer = layer_name
                st.rerun()
        with col2:
            if layer_name != 'Default':
                if st.button("✕", key=f"del_layer_{layer_name}", help="Delete layer"):
                    if layer_name in st.session_state.layers:
                        del st.session_state.layers[layer_name]
                        if st.session_state.current_layer == layer_name:
                            st.session_state.current_layer = 'Default'
                        st.rerun()
    
    # Create layer
    st.markdown('<div class="felt-create-layer">', unsafe_allow_html=True)
    new_layer = st.text_input("", placeholder="+ Create layer...", key="new_layer_input", label_visibility="collapsed")
    if new_layer and st.button("Add", key="add_layer_btn"):
        if new_layer not in st.session_state.layers:
            st.session_state.layers[new_layer] = {'annotations': []}
            st.session_state.current_layer = new_layer
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="felt-divider"></div>', unsafe_allow_html=True)
    
    # ANNOTATIONS section
    st.markdown('<div class="felt-section-title">ANNOTATIONS</div>', unsafe_allow_html=True)
    
    # Tool grid
    tools = [
        ("📍", "Pin", "point"),
        ("📏", "Line", "line"),
        ("🛤️", "Route", "route"),
        ("⬡", "Polygon", "polygon"),
        ("▭", "Rectangle", "rectangle"),
        ("⭕", "Circle", "circle"),
    ]
    
    # Create grid with actual buttons
    cols = st.columns(3)
    for idx, (icon, name, mode) in enumerate(tools):
        with cols[idx % 3]:
            is_active = st.session_state.draw_mode == mode
            active_class = "active" if is_active else ""
            if st.button(f"{icon}\n{name}", key=f"tool_{mode}", help=f"Draw {name}"):
                if st.session_state.draw_mode == mode:
                    st.session_state.draw_mode = None
                else:
                    st.session_state.draw_mode = mode
                st.rerun()
    
    st.markdown('<div class="felt-divider"></div>', unsafe_allow_html=True)
    
    # More and Extract
    if st.button("⚙️ More", key="more_btn", help="More options"):
        st.info("More options")
    if st.button("📤 Extract", key="extract_btn", help="Extract data"):
        st.info("Extract data")
    
    st.markdown('<div class="felt-divider"></div>', unsafe_allow_html=True)
    
    # Style section
    st.markdown('<div class="felt-section-title">Style</div>', unsafe_allow_html=True)
    st.markdown('<div class="felt-style-group">', unsafe_allow_html=True)
    
    # Attributes button
    if st.button("Attributes", key="attributes_btn"):
        st.info("Attributes")
    
    # Opacity
    opacity_val = st.slider("Opacity", 0.0, 1.0, 0.82, 0.01, key="opacity_slider", label_visibility="collapsed")
    st.markdown(f'<div style="text-align: right; font-size: 12px; color: #666; margin-top: -10px;">{int(opacity_val * 100)}%</div>', unsafe_allow_html=True)
    
    # On click
    st.selectbox("On click", ["Show larger", "Show popup", "Zoom to", "None"], key="on_click_select")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="felt-divider"></div>', unsafe_allow_html=True)
    
    # Add name and description when annotation is pending
    if st.session_state.pending_annotation:
        st.markdown("### Save Annotation")
        anno_name = st.text_input("Add a name", placeholder="Enter name", key="anno_name_input")
        anno_desc = st.text_area("Add a description", placeholder="Enter description", key="anno_desc_input", height=60)
        
        if st.button("💾 Save", key="save_anno_btn"):
            if st.session_state.pending_annotation:
                anno_data = st.session_state.pending_annotation
                anno_data['name'] = anno_name or "Untitled"
                anno_data['description'] = anno_desc
                st.session_state.annotations.append(anno_data)
                st.session_state.pending_annotation = None
                st.session_state.draw_mode = None
                st.success("Annotation saved!")
                st.rerun()
        
        if st.button("Cancel", key="cancel_anno_btn"):
            st.session_state.pending_annotation = None
            st.session_state.draw_mode = None
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

with col_map:
    # Google Maps basemap with exact style
    google_tiles = 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}&apistyle=s.t%3A2%7Cp.v%3Aoff'
    
    m = folium.Map(
        location=[14.5995, 120.9842],
        zoom_start=17,
        tiles=google_tiles,
        attr='Google Maps'
    )
    
    # Add drawing controls
    draw = plugins.Draw(
        export=False,
        position='topleft',
        draw_options={
            'polygon': {
                'allowIntersection': False,
                'showArea': True,
                'shapeOptions': {
                    'color': '#4285f4',
                    'weight': 3,
                    'fillColor': '#4285f4',
                    'fillOpacity': opacity_val
                }
            },
            'rectangle': {
                'shapeOptions': {
                    'color': '#4285f4',
                    'weight': 3,
                    'fillColor': '#4285f4',
                    'fillOpacity': opacity_val
                }
            },
            'circle': {
                'shapeOptions': {
                    'color': '#4285f4',
                    'weight': 3,
                    'fillColor': '#4285f4',
                    'fillOpacity': opacity_val
                }
            },
            'polyline': {
                'shapeOptions': {
                    'color': '#4285f4',
                    'weight': 3
                }
            },
            'marker': True,
            'circlemarker': False
        }
    )
    draw.add_to(m)
    
    # Add streets from image
    streets = [
        ("Lakandula St", [14.6005, 120.9835], [14.6015, 120.9845]),
        ("Maria Payo St", [14.5998, 120.9848], [14.6010, 120.9858]),
        ("Balagtas St", [14.5985, 120.9838], [14.5995, 120.9848]),
        ("Lunduya St", [14.6012, 120.9828], [14.6022, 120.9838]),
        ("Lahadra St", [14.6005, 120.9825], [14.6015, 120.9835]),
        ("P. Herrera 1st St", [14.5990, 120.9855], [14.6000, 120.9865]),
        ("Santa Aguirre St", [14.5980, 120.9845], [14.5990, 120.9855]),
        ("Padre K", [14.5975, 120.9850], [14.5985, 120.9860]),
        ("Faura", [14.5985, 120.9865], [14.5995, 120.9875]),
        ("Cristo St", [14.5980, 120.9830], [14.5990, 120.9840]),
        ("Dela Reina St", [14.5975, 120.9825], [14.5985, 120.9835]),
        ("Veronica St", [14.5970, 120.9830], [14.5980, 120.9840]),
        ("Oportunidad St", [14.5965, 120.9840], [14.5975, 120.9850]),
        ("Chinatown Walk", [14.5990, 120.9860], [14.6000, 120.9870])
    ]
    
    for name, start, end in streets:
        folium.PolyLine(
            locations=[start, end],
            color='#666666',
            weight=2,
            opacity=0.7
        ).add_to(m)
        # Add label at midpoint
        mid = [(start[0] + end[0])/2, (start[1] + end[1])/2]
        folium.Marker(
            location=mid,
            icon=folium.DivIcon(
                html=f'<div style="font-size:10px;font-weight:500;color:#333;text-shadow:0 0 4px white,0 0 4px white;white-space:nowrap;">{name}</div>'
            )
        ).add_to(m)
    
    # C-1 markers
    c1_locations = [
        (14.6010, 120.9840),
        (14.5990, 120.9850),
        (14.5980, 120.9860),
        (14.5975, 120.9855),
        (14.5970, 120.9845)
    ]
    for lat, lng in c1_locations:
        folium.Marker(
            location=[lat, lng],
            icon=folium.DivIcon(
                html='<div style="background:#4285f4;color:white;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:bold;border:2px solid white;box-shadow:0 2px 4px rgba(0,0,0,0.2);">C-1</div>'
            )
        ).add_to(m)
    
    # Display existing annotations
    for anno in st.session_state.annotations:
        if anno['type'] == 'polygon':
            folium.Polygon(
                locations=anno['coords'],
                color=anno.get('color', '#4285f4'),
                weight=anno.get('weight', 3),
                fill_color=anno.get('fill_color', '#4285f4'),
                fill_opacity=anno.get('opacity', 0.82),
                popup=anno.get('name', 'Polygon')
            ).add_to(m)
        elif anno['type'] == 'line':
            folium.PolyLine(
                locations=anno['coords'],
                color=anno.get('color', '#4285f4'),
                weight=anno.get('weight', 3),
                popup=anno.get('name', 'Line')
            ).add_to(m)
        elif anno['type'] == 'point':
            folium.Marker(
                location=anno['coords'],
                popup=anno.get('name', 'Point'),
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
    
    # Display map
    st_data = st_folium(m, width=None, height=700)
    
    # Capture drawing
    if st_data and 'last_active_drawing' in st_data:
        drawing = st_data['last_active_drawing']
        if drawing and 'geometry' in drawing and not st.session_state.pending_annotation:
            geom = drawing['geometry']
            
            if geom['type'] == 'Polygon':
                coords = geom['coordinates'][0]
                lat_lng = [[lat, lng] for lng, lat in coords]
                st.session_state.pending_annotation = {
                    'type': 'polygon',
                    'coords': lat_lng,
                    'color': '#4285f4',
                    'fill_color': '#4285f4',
                    'opacity': opacity_val,
                    'weight': 3
                }
            elif geom['type'] == 'LineString':
                coords = geom['coordinates']
                lat_lng = [[lat, lng] for lng, lat in coords]
                st.session_state.pending_annotation = {
                    'type': 'line',
                    'coords': lat_lng,
                    'color': '#4285f4',
                    'weight': 3
                }
            elif geom['type'] == 'Point':
                lng, lat = geom['coordinates']
                st.session_state.pending_annotation = {
                    'type': 'point',
                    'coords': [lat, lng]
                }
            st.rerun()
    
    # Attribution
    st.markdown('<div class="felt-attribution">Made with Felt. © mt1.google.com</div>', unsafe_allow_html=True)

# Display annotations in sidebar
with col_sidebar:
    st.markdown('<div class="felt-divider"></div>', unsafe_allow_html=True)
    if st.session_state.annotations:
        st.markdown('<div class="felt-section-title">Annotations</div>', unsafe_allow_html=True)
        for i, anno in enumerate(st.session_state.annotations):
            st.markdown(f"""
            <div class="felt-annotation-item">
                <div>
                    <span class="felt-annotation-name">{anno.get('name', 'Untitled')}</span>
                    <span style="font-size:11px;color:#888;margin-left:8px;">{anno['type'].upper()}</span>
                </div>
                <span class="felt-annotation-delete" onclick="this.click()">✕</span>
            </div>
            """, unsafe_allow_html=True)
            col1, col2 = st.columns([4, 1])
            with col1:
                st.caption(anno.get('description', ''))
            with col2:
                if st.button("✕", key=f"del_anno_{i}", help="Delete annotation"):
                    st.session_state.annotations.pop(i)
                    st.rerun()

# Export functionality
with col_sidebar:
    st.markdown('<div class="felt-divider"></div>', unsafe_allow_html=True)
    if st.button("📥 Export to KML", key="export_kml"):
        if st.session_state.annotations:
            features = []
            for anno in st.session_state.annotations:
                if anno['type'] == 'polygon':
                    coords = [(lng, lat) for lat, lng in anno['coords']]
                    geom = Polygon(coords)
                elif anno['type'] == 'line':
                    coords = [(lng, lat) for lat, lng in anno['coords']]
                    geom = LineString(coords)
                elif anno['type'] == 'point':
                    lat, lng = anno['coords']
                    geom = Point(lng, lat)
                
                features.append({
                    'geometry': geom,
                    'name': anno.get('name', ''),
                    'description': anno.get('description', ''),
                    'type': anno['type']
                })
            
            gdf = gpd.GeoDataFrame(features, crs='EPSG:4326')
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.kml') as tmp:
                gdf.to_file(tmp.name, driver='KML')
                tmp_path = tmp.name
            
            with open(tmp_path, 'rb') as f:
                kml_data = f.read()
            
            st.download_button(
                label="Download KML",
                data=kml_data,
                file_name="felt_annotations.kml",
                mime="application/vnd.google-earth.kml+xml"
            )
            
            os.unlink(tmp_path)
        else:
            st.warning("No annotations to export")
