import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
import geopandas as gpd
from shapely.geometry import Polygon, Point, LineString
import tempfile
import os
import json
import pandas as pd

st.set_page_config(page_title="Felt-Style Map Tool", layout="wide")

# Custom CSS for Felt-like styling
st.markdown("""
<style>
    .main {
        padding: 0px !important;
        margin: 0px !important;
    }
    .stButton > button {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        color: #333333;
        font-weight: 500;
        padding: 0.5rem 1rem;
        width: 100%;
        text-align: left;
    }
    .stButton > button:hover {
        background-color: #f5f5f5;
        border-color: #cccccc;
    }
    .css-1d391kg {
        padding: 1rem 1rem 1rem 1rem;
    }
    .stSelectbox > div > div {
        background-color: #f8f9fa;
    }
    .css-1aumxhk {
        background-color: #f8f9fa;
    }
    .layer-card {
        background-color: white;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 5px;
        border-left: 4px solid #4285f4;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .annotation-tool {
        background-color: white;
        padding: 8px;
        border-radius: 6px;
        border: 1px solid #e0e0e0;
        margin: 3px 0;
        cursor: pointer;
        transition: all 0.2s;
    }
    .annotation-tool:hover {
        background-color: #f0f4ff;
        border-color: #4285f4;
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
    st.session_state.layers = {'Default': {'polygons': [], 'lines': [], 'points': [], 'routes': []}}
if 'current_layer' not in st.session_state:
    st.session_state.current_layer = 'Default'
if 'draw_mode' not in st.session_state:
    st.session_state.draw_mode = None
if 'annotations' not in st.session_state:
    st.session_state.annotations = []

# Layout: Sidebar + Main
col_left, col_right = st.columns([1, 4])

with col_left:
    st.markdown("## 🗺️ Map Tools")
    
    # Layer Management
    st.markdown("### LAYERS")
    
    # Create new layer
    new_layer = st.text_input("+ Create layer...", placeholder="Layer name", key="new_layer")
    if new_layer and st.button("Add Layer"):
        if new_layer not in st.session_state.layers:
            st.session_state.layers[new_layer] = {'polygons': [], 'lines': [], 'points': [], 'routes': []}
            st.rerun()
    
    # Display existing layers
    for layer_name in st.session_state.layers.keys():
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(f"📁 {layer_name}", key=f"layer_{layer_name}"):
                st.session_state.current_layer = layer_name
                st.rerun()
        with col2:
            if layer_name != 'Default':
                if st.button("✕", key=f"del_layer_{layer_name}"):
                    del st.session_state.layers[layer_name]
                    if st.session_state.current_layer == layer_name:
                        st.session_state.current_layer = 'Default'
                    st.rerun()
    
    st.markdown("---")
    
    # Drawing Tools
    st.markdown("### ANNOTATIONS")
    
    tools = [
        ("📍", "Pin", "point"),
        ("📏", "Line", "line"),
        ("🛤️", "Route", "route"),
        ("⬡", "Polygon", "polygon"),
        ("▭", "Rectangle", "rectangle"),
        ("⭕", "Circle", "circle"),
    ]
    
    cols = st.columns(3)
    for idx, (icon, name, mode) in enumerate(tools):
        with cols[idx % 3]:
            if st.button(f"{icon} {name}", key=f"tool_{mode}"):
                st.session_state.draw_mode = mode
                st.rerun()
    
    st.markdown("---")
    
    # More options
    if st.button("⚙️ More"):
        st.info("More options coming soon")
    
    if st.button("📤 Extract"):
        st.info("Extract data")
    
    st.markdown("---")
    
    # Style controls
    st.markdown("### Style")
    
    fill_color = st.color_picker("Fill Color", "#4285f4")
    fill_opacity = st.slider("Opacity", 0.0, 1.0, 0.82, 0.01)
    outline_color = st.color_picker("Outline Color", "#ff0000")
    outline_weight = st.slider("Weight", 1, 10, 3)
    
    # On click behavior
    st.selectbox("On click", ["Show larger", "Show popup", "Zoom to", "None"])

with col_right:
    # Create map with Google basemap
    google_tiles = 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}&apistyle=s.t%3A2%7Cp.v%3Aoff'
    
    m = folium.Map(
        location=[14.5995, 120.9842],  # Manila coordinates
        zoom_start=16,
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
                    'color': outline_color,
                    'weight': outline_weight,
                    'fillColor': fill_color,
                    'fillOpacity': fill_opacity
                }
            },
            'rectangle': {
                'shapeOptions': {
                    'color': outline_color,
                    'weight': outline_weight,
                    'fillColor': fill_color,
                    'fillOpacity': fill_opacity
                }
            },
            'circle': {
                'shapeOptions': {
                    'color': outline_color,
                    'weight': outline_weight,
                    'fillColor': fill_color,
                    'fillOpacity': fill_opacity
                }
            },
            'polyline': {
                'shapeOptions': {
                    'color': outline_color,
                    'weight': outline_weight
                }
            },
            'marker': True,
            'circlemarker': False
        }
    )
    draw.add_to(m)
    
    # Add sample streets (based on the image)
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
            opacity=0.8,
            popup=name
        ).add_to(m)
    
    # Add sample markers (C-1 labels from the image)
    marker_locations = [
        (14.6010, 120.9840, "C-1"),
        (14.5990, 120.9850, "C-1"),
        (14.5980, 120.9860, "C-1"),
        (14.5975, 120.9855, "C-1"),
        (14.5970, 120.9845, "C-1")
    ]
    
    for lat, lng, label in marker_locations:
        folium.Marker(
            location=[lat, lng],
            popup=label,
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
    
    # Add existing annotations from session state
    for annotation in st.session_state.annotations:
        if annotation['type'] == 'polygon':
            folium.Polygon(
                locations=annotation['coords'],
                color=annotation.get('outline_color', '#ff0000'),
                weight=annotation.get('weight', 3),
                fill_color=annotation.get('fill_color', '#4285f4'),
                fill_opacity=annotation.get('opacity', 0.82),
                popup=annotation.get('name', 'Polygon')
            ).add_to(m)
        elif annotation['type'] == 'line':
            folium.PolyLine(
                locations=annotation['coords'],
                color=annotation.get('color', '#ff0000'),
                weight=annotation.get('weight', 3),
                popup=annotation.get('name', 'Line')
            ).add_to(m)
        elif annotation['type'] == 'point':
            folium.Marker(
                location=annotation['coords'],
                popup=annotation.get('name', 'Point'),
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
    
    # Display map
    st_data = st_folium(m, width=1000, height=700)
    
    # Capture drawn features
    if st_data and 'last_active_drawing' in st_data:
        drawing = st_data['last_active_drawing']
        if drawing and 'geometry' in drawing:
            geom = drawing['geometry']
            
            # Get name for annotation
            name = st.text_input("Add a name:", placeholder="Enter annotation name", key="anno_name")
            description = st.text_area("Add a description:", placeholder="Enter description", key="anno_desc")
            
            if st.button("Save Annotation", key="save_anno"):
                if geom['type'] == 'Polygon':
                    coords = geom['coordinates'][0]
                    lat_lng = [[lat, lng] for lng, lat in coords]
                    st.session_state.annotations.append({
                        'type': 'polygon',
                        'coords': lat_lng,
                        'name': name or 'Polygon',
                        'description': description,
                        'fill_color': fill_color,
                        'outline_color': outline_color,
                        'opacity': fill_opacity,
                        'weight': outline_weight
                    })
                elif geom['type'] == 'LineString':
                    coords = geom['coordinates']
                    lat_lng = [[lat, lng] for lng, lat in coords]
                    st.session_state.annotations.append({
                        'type': 'line',
                        'coords': lat_lng,
                        'name': name or 'Line',
                        'description': description,
                        'color': outline_color,
                        'weight': outline_weight
                    })
                elif geom['type'] == 'Point':
                    lng, lat = geom['coordinates']
                    st.session_state.annotations.append({
                        'type': 'point',
                        'coords': [lat, lng],
                        'name': name or 'Point',
                        'description': description
                    })
                
                st.success("Annotation saved!")
                st.rerun()
    
    # Display annotations list
    if st.session_state.annotations:
        st.markdown("### 📋 Annotations")
        for i, anno in enumerate(st.session_state.annotations):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{anno.get('name', 'Untitled')}**")
                if anno.get('description'):
                    st.caption(anno['description'])
            with col2:
                st.caption(anno['type'].upper())
            with col3:
                if st.button("🗑️", key=f"del_anno_{i}"):
                    st.session_state.annotations.pop(i)
                    st.rerun()

# Export functionality
st.sidebar.markdown("---")
if st.sidebar.button("📥 Export All Annotations"):
    if st.session_state.annotations:
        # Create GeoDataFrame
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
        
        st.sidebar.download_button(
            label="Download KML",
            data=kml_data,
            file_name="annotations.kml",
            mime="application/vnd.google-earth.kml+xml"
        )
        
        os.unlink(tmp_path)
    else:
        st.sidebar.warning("No annotations to export")

# Instructions
st.sidebar.markdown("---")
st.sidebar.markdown("""
### ℹ️ Instructions
1. **Select a layer** or create a new one
2. **Choose an annotation tool** (Pin, Line, Route, Polygon, Rectangle, Circle)
3. **Draw on the map** using the drawing tools
4. **Add a name and description** to your annotation
5. **Save** the annotation
6. **Export** all annotations to KML

💡 **Tip**: The Google Maps basemap matches the style from the image
""")
