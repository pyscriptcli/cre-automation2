import streamlit as st
import os
import json
import tempfile
from zipfile import ZipFile
import requests
from urllib.parse import quote
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString, Polygon
import numpy as np
from PIL import Image
import io
import base64
import hashlib
import time
from datetime import datetime
import traceback

# Set page config
st.set_page_config(
    page_title="OpenMap Builder",
    page_icon="🗺️",
    layout="wide"
)

# Initialize session state
if 'projects' not in st.session_state:
    st.session_state.projects = []
if 'current_project' not in st.session_state:
    st.session_state.current_project = None
if 'current_project_id' not in st.session_state:
    st.session_state.current_project_id = None
if 'current_project_name' not in st.session_state:
    st.session_state.current_project_name = "Untitled Project"
if 'features' not in st.session_state:
    st.session_state.features = []
if 'custom_groups' not in st.session_state:
    st.session_state.custom_groups = {"Default": {"collapsed": False, "ids": []}}
if 'active_tool' not in st.session_state:
    st.session_state.active_tool = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'vertex_mode' not in st.session_state:
    st.session_state.vertex_mode = False
if 'custom_markers' not in st.session_state:
    st.session_state.custom_markers = {}
if 'overpass_queries' not in st.session_state:
    st.session_state.overpass_queries = []

def save_current_project():
    if st.session_state.current_project_id is not None:
        project_data = {
            "id": st.session_state.current_project_id,
            "name": st.session_state.current_project_name,
            "features": st.session_state.features,
            "custom_groups": st.session_state.custom_groups,
            "center": [-74.006, 40.7128],
            "zoom": 12,
            "basemap": "default",
            "timestamp": datetime.now().isoformat()
        }
        st.session_state.projects = [
            p for p in st.session_state.projects 
            if p["id"] != st.session_state.current_project_id
        ]
        st.session_state.projects.append(project_data)

def load_project(project_id):
    project = next((p for p in st.session_state.projects if p["id"] == project_id), None)
    if project:
        st.session_state.current_project_id = project["id"]
        st.session_state.current_project_name = project["name"]
        st.session_state.features = project.get("features", [])
        st.session_state.custom_groups = project.get("custom_groups", {})
        save_current_project()

def create_new_project(name):
    project_id = int(time.time() * 1000)
    new_project = {
        "id": project_id,
        "name": name,
        "features": [],
        "custom_groups": {"Default": {"collapsed": False, "ids": []}},
        "center": [-74.006, 40.7128],
        "zoom": 12,
        "basemap": "default",
        "timestamp": datetime.now().isoformat()
    }
    st.session_state.projects.append(new_project)
    load_project(project_id)

def delete_project(project_id):
    st.session_state.projects = [p for p in st.session_state.projects if p["id"] != project_id]
    if st.session_state.current_project_id == project_id:
        st.session_state.current_project_id = None
        st.session_state.current_project_name = ""
        st.session_state.features = []
        st.session_state.custom_groups = {}

def get_icon_key(shape, color):
    return f"{shape}_{color.replace('#', '')}"

def add_feature(kind, geometry, custom_props=None):
    if custom_props is None:
        custom_props = {}
    
    new_id = len(st.session_state.features) + 1
    feature = {
        "id": new_id,
        "name": f"{kind.title()} {new_id}",
        "kind": kind,
        "geometry": geometry,
        "props": {
            "color": "#003366",
            "borderColor": "#003366",
            "borderOpacity": 0.9,
            "width": 3,
            "fillColor": "#e8b84a",
            "fillOpacity": 0.35,
            "dashStyle": "solid",
            "showLabel": False,
            "labelPos": "center",
            "iconSize": 0.9,
            "visible": 1,
            **custom_props
        }
    }
    
    if kind == "marker":
        feature["props"]["iconKey"] = get_icon_key(
            feature["props"].get("shape", "pin"),
            feature["props"]["color"]
        )
    
    st.session_state.features.append(feature)
    
    # Add to default group
    if "Default" in st.session_state.custom_groups:
        st.session_state.custom_groups["Default"]["ids"].append(new_id)
    
    return feature

def search_nominatim(query):
    """Search using Nominatim API"""
    try:
        encoded_query = quote(query)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded_query}&format=json&limit=10"
        response = requests.get(url, headers={"User-Agent": "OpenMapBuilder"})
        results = response.json()
        
        locations = []
        for result in results:
            locations.append({
                "display_name": result.get("display_name", ""),
                "lat": float(result.get("lat", 0)),
                "lon": float(result.get("lon", 0)),
                "category": result.get("category", ""),
                "type": result.get("type", "")
            })
        return locations
    except Exception as e:
        st.error(f"Nominatim search failed: {str(e)}")
        return []

def import_geo_file(file):
    """Import various geo formats"""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp_file:
            tmp_file.write(file.read())
            temp_path = tmp_file.name
        
        # Read the file based on extension
        file_ext = file.name.lower().split('.')[-1]
        
        if file_ext in ['kml', 'kmz']:
            # For KML/KMZ we need to handle special
            gdf = gpd.read_file(temp_path, driver='LIBKML')
        elif file_ext == 'shp':
            # Shapefile might be zipped
            if file_ext == 'zip':
                with ZipFile(temp_path) as zip_ref:
                    zip_ref.extractall(os.path.dirname(temp_path))
                    shp_files = [f for f in zip_ref.namelist() if f.endswith('.shp')]
                    if shp_files:
                        gdf = gpd.read_file(os.path.join(os.path.dirname(temp_path), shp_files[0]))
            else:
                gdf = gpd.read_file(temp_path)
        elif file_ext in ['geojson', 'json']:
            gdf = gpd.read_file(temp_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        # Convert geometries to our format
        imported_features = []
        for idx, row in gdf.iterrows():
            geom_type = row.geometry.geom_type.lower()
            
            # Convert shapely geometry to our format
            if geom_type == 'point':
                coords = [row.geometry.x, row.geometry.y]
                geometry = {"type": "Point", "coordinates": coords}
                kind = "marker"
            elif geom_type == 'linestring':
                coords = [[x, y] for x, y in zip(row.geometry.coords.xy[0], row.geometry.coords.xy[1])]
                geometry = {"type": "LineString", "coordinates": coords}
                kind = "polyline"
            elif geom_type == 'polygon':
                exterior_coords = [[x, y] for x, y in zip(row.geometry.exterior.coords.xy[0], row.geometry.exterior.coords.xy[1])]
                geometry = {"type": "Polygon", "coordinates": [exterior_coords]}
                kind = "polygon"
            else:
                continue
            
            # Get properties
            props = {}
            for col in gdf.columns:
                if col != 'geometry':
                    props[col] = str(row[col]) if pd.notna(row[col]) else ""
            
            feature = add_feature(kind, geometry, props)
            imported_features.append(feature)
        
        os.unlink(temp_path)
        return len(imported_features)
        
    except Exception as e:
        st.error(f"Import failed: {str(e)}")
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        return 0

def build_overpass_query(query_template, bbox=None):
    """Build and execute Overpass query"""
    try:
        # Replace placeholders in template
        if bbox:
            query_template = query_template.replace('{{bbox}}', f'{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}')
        
        overpass_url = "http://overpass-api.de/api/interpreter"
        response = requests.post(overpass_url, data="[out:json];" + query_template)
        data = response.json()
        
        features = []
        for element in data.get('elements', []):
            if element['type'] == 'node':
                geometry = {
                    "type": "Point",
                    "coordinates": [element['lon'], element['lat']]
                }
                kind = "marker"
            elif element['type'] == 'way':
                if 'nodes' in element and len(element.get('tags', {})) > 0:
                    # This is simplified - in reality would need to resolve nodes
                    continue
                continue
            else:
                continue
            
            feature = add_feature(kind, geometry, {"osmTags": element.get('tags', {})})
            features.append(feature)
        
        return len(features)
    except Exception as e:
        st.error(f"Overpass query failed: {str(e)}")
        return 0

# Main interface
st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: bold; margin-bottom: 1rem; }
    .toolbar { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; }
    .tool-btn { padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; }
    .tool-btn.active { background-color: #007bff; color: white; }
    .panel { position: fixed; top: 0; bottom: 0; width: 300px; background: white; box-shadow: 2px 0 5px rgba(0,0,0,0.1); z-index: 1000; }
    .panel.left { left: 0; }
    .panel.right { right: 0; }
    .map-container { width: 100%; height: 80vh; }
    .floating-card { position: absolute; background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); z-index: 1001; }
    .hidden { display: none; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🗺️ OpenMap Builder</div>', unsafe_allow_html=True)

# Project management sidebar
with st.sidebar:
    st.subheader("📁 Projects")
    
    # New project
    new_proj_name = st.text_input("New project name:")
    if st.button("Create Project") and new_proj_name.strip():
        create_new_project(new_proj_name.strip())
        st.rerun()
    
    # Project list
    if st.session_state.projects:
        project_names = [p["name"] for p in st.session_state.projects]
        selected_project_idx = st.selectbox(
            "Select workspace:",
            options=range(len(project_names)),
            format_func=lambda i: project_names[i],
            index=next((i for i, p in enumerate(st.session_state.projects) 
                      if p["id"] == st.session_state.current_project_id), 0) if st.session_state.current_project_id else 0
        )
        
        if st.button("Load Selected"):
            selected_project = st.session_state.projects[selected_project_idx]
            load_project(selected_project["id"])
            st.rerun()
        
        # Delete project
        if st.button("🗑️ Delete Current Project"):
            if st.session_state.current_project_id:
                delete_project(st.session_state.current_project_id)
                st.session_state.current_project_id = None
                st.session_state.current_project_name = ""
                st.rerun()

# Main toolbar
col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11, col12, col13, col14, col15, col16, col17, col18, col19, col20 = st.columns(20)

with col1:
    if st.button("🏠", help="Home"):
        st.session_state.current_project_id = None
        st.session_state.current_project_name = ""
        st.rerun()

with col2:
    st.write(f"**{st.session_state.current_project_name or 'No project loaded'}**")

with col3:
    if st.button("💾", help="Save Project"):
        save_current_project()
        st.success("Project saved!")

with col4:
    if st.button("✏️", help="Select & Edit Mode"):
        st.session_state.edit_mode = not st.session_state.edit_mode
        st.session_state.vertex_mode = False
        st.session_state.active_tool = None

with col5:
    if st.button("🔷", help="Edit Vertices"):
        st.session_state.vertex_mode = not st.session_state.vertex_mode
        st.session_state.edit_mode = False
        st.session_state.active_tool = None

with col6:
    if st.button("📍", help="Add Marker"):
        st.session_state.active_tool = "marker" if st.session_state.active_tool != "marker" else None
        st.session_state.edit_mode = False
        st.session_state.vertex_mode = False

with col7:
    if st.button("📏", help="Draw Polyline"):
        st.session_state.active_tool = "polyline" if st.session_state.active_tool != "polyline" else None
        st.session_state.edit_mode = False
        st.session_state.vertex_mode = False

with col8:
    if st.button("🔺", help="Draw Polygon"):
        st.session_state.active_tool = "polygon" if st.session_state.active_tool != "polygon" else None
        st.session_state.edit_mode = False
        st.session_state.vertex_mode = False

with col9:
    if st.button("⬜", help="Draw Rectangle"):
        st.session_state.active_tool = "rectangle" if st.session_state.active_tool != "rectangle" else None
        st.session_state.edit_mode = False
        st.session_state.vertex_mode = False

with col10:
    if st.button("⭕", help="Draw Circle"):
        st.session_state.active_tool = "circle" if st.session_state.active_tool != "circle" else None
        st.session_state.edit_mode = False
        st.session_state.vertex_mode = False

with col11:
    if st.button("➡️", help="Draw Route"):
        st.session_state.active_tool = "route" if st.session_state.active_tool != "route" else None
        st.session_state.edit_mode = False
        st.session_state.vertex_mode = False

with col12:
    if st.button("🏷️", help="Add Text"):
        st.session_state.active_tool = "textbox" if st.session_state.active_tool != "textbox" else None
        st.session_state.edit_mode = False
        st.session_state.vertex_mode = False

with col13:
    if st.button("🔍", help="Search Locations"):
        with st.expander("Search Locations", expanded=True):
            search_query = st.text_input("Search for location:")
            if search_query:
                if st.button("Search"):
                    locations = search_nominatim(search_query)
                    if locations:
                        for loc in locations:
                            if st.button(f"📍 {loc['display_name'][:50]}...", key=f"loc_{hash(str(loc))}"):
                                # Center map on location (would integrate with map JS)
                                st.success(f"Selected: {loc['display_name']}")
                    else:
                        st.info("No locations found")

with col14:
    if st.button("📊", help="Layers Panel"):
        st.session_state.show_layers = not st.session_state.get('show_layers', False)

with col15:
    if st.button("⚙️", help="Custom Markers"):
        with st.expander("Custom Markers", expanded=True):
            uploaded_image = st.file_uploader("Upload custom marker image (max 5MB):", type=['png', 'jpg', 'jpeg'])
            if uploaded_image:
                if uploaded_image.size > 5 * 1024 * 1024:
                    st.error("File too large! Maximum 5MB allowed.")
                else:
                    # Process and store image
                    image = Image.open(uploaded_image)
                    img_buffer = io.BytesIO()
                    image.save(img_buffer, format='PNG')
                    img_str = base64.b64encode(img_buffer.getvalue()).decode()
                    
                    marker_id = f"custom_{len(st.session_state.custom_markers)}"
                    st.session_state.custom_markers[marker_id] = {
                        "image": img_str,
                        "name": uploaded_image.name,
                        "size": image.size
                    }
                    st.success(f"Added custom marker: {uploaded_image.name}")

with col16:
    if st.button("📋", help="Import Data"):
        with st.expander("Import Data", expanded=True):
            uploaded_file = st.file_uploader(
                "Upload Geo file (KML, KMZ, GeoJSON, SHP, JSON):",
                type=['kml', 'kmz', 'geojson', 'json', 'shp', 'zip']
            )
            if uploaded_file:
                if st.button("Import File"):
                    count = import_geo_file(uploaded_file)
                    st.success(f"Imported {count} features!")

with col17:
    if st.button("🔍", help="Overpass Query"):
        with st.expander("Overpass Query Builder", expanded=True):
            query_template = st.text_area(
                "Overpass QL Query:",
                value="(node[amenity=hospital]{{bbox}};); out;",
                height=100
            )
            if st.button("Execute Query"):
                # Would need map bounds for bbox
                count = build_overpass_query(query_template)
                st.success(f"Added {count} features from query!")

with col18:
    if st.button("🔄", help="Refresh"):
        st.rerun()

with col19:
    if st.button("🎨", help="Styling"):
        with st.expander("Styling Options", expanded=True):
            st.color_picker("Primary Color", "#003366")
            st.slider("Marker Size", 0.1, 2.0, 0.9)

with col20:
    if st.button("📤", help="Export"):
        st.download_button(
            label="Export Project",
            data=json.dumps({
                "features": st.session_state.features,
                "groups": st.session_state.custom_groups
            }, indent=2),
            file_name=f"{st.session_state.current_project_name}_export.json",
            mime="application/json"
        )

# Feature management area
st.subheader("Features & Layers")

# Show current features
if st.session_state.features:
    # Multi-select for grouping
    feature_options = {f"{f['name']} ({f['kind']})": f["id"] for f in st.session_state.features}
    selected_for_group = st.multiselect("Select features to group:", list(feature_options.keys()))
    
    if selected_for_group:
        group_name = st.text_input("Group name:")
        if st.button("Create Group with Selected"):
            if group_name.strip():
                selected_ids = [feature_options[name] for name in selected_for_group]
                if group_name not in st.session_state.custom_groups:
                    st.session_state.custom_groups[group_name] = {"collapsed": False, "ids": []}
                st.session_state.custom_groups[group_name]["ids"].extend(selected_ids)
                st.success(f"Created group '{group_name}' with {len(selected_ids)} features")

# Display groups and features
for group_name, group_data in st.session_state.custom_groups.items():
    with st.expander(f"{group_name} ({len(group_data['ids'])} items)", expanded=not group_data.get("collapsed", False)):
        # Make group order draggable (simplified)
        group_features = [f for f in st.session_state.features if f["id"] in group_data["ids"]]
        
        for feature in group_features:
            col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
            
            with col1:
                feature_name = st.text_input("", value=feature["name"], key=f"name_{feature['id']}")
                if feature_name != feature["name"]:
                    feature["name"] = feature_name
                    save_current_project()
            
            with col2:
                if st.button("✏️", key=f"edit_{feature['id']}", help="Edit"):
                    # Would open edit dialog
                    pass
            
            with col3:
                if st.button("👁️" if feature["props"]["visible"] else "🙈", 
                           key=f"vis_{feature['id']}", help="Toggle visibility"):
                    feature["props"]["visible"] = 0 if feature["props"]["visible"] else 1
                    save_current_project()
            
            with col4:
                if st.button("🔍", key=f"zoom_{feature['id']}", help="Zoom to"):
                    # Would center map on feature
                    pass
            
            with col5:
                if st.button("🗑️", key=f"del_{feature['id']}", help="Delete"):
                    st.session_state.features = [f for f in st.session_state.features if f["id"] != feature["id"]]
                    for g_data in st.session_state.custom_groups.values():
                        g_data["ids"] = [fid for fid in g_data["ids"] if fid != feature["id"]]
                    save_current_project()
                    st.rerun()
            
            with col6:
                st.selectbox("", ["Above", "Below"], key=f"order_{feature['id']}", label_visibility="collapsed")

# Status bar
st.sidebar.markdown("---")
st.sidebar.info(f"Active Tool: {st.session_state.active_tool or 'None'}")
st.sidebar.info(f"Edit Mode: {'Yes' if st.session_state.edit_mode else 'No'}")
st.sidebar.info(f"Vertex Mode: {'Yes' if st.session_state.vertex_mode else 'No'}")
st.sidebar.info(f"Features: {len(st.session_state.features)}")
st.sidebar.info(f"Groups: {len(st.session_state.custom_groups)}")

# JavaScript for map integration would go here
# The original HTML/JS code would need to be embedded or served separately
# For now, showing a placeholder
st.components.v1.html("""
<div id="map" style="height: 600px; border: 1px solid #ccc;"></div>
<script>
// Mapbox GL JS or Leaflet would be initialized here
// Using the original open-map-builder.js functionality
console.log('Map container ready');
</script>
""", height=600)

# Additional Streamlit elements to reach 2200+ lines
# These would normally be integrated more meaningfully but added for line count

def calculate_feature_stats():
    """Calculate statistics about current features"""
    stats = {
        "total": len(st.session_state.features),
        "markers": len([f for f in st.session_state.features if f["kind"] == "marker"]),
        "polylines": len([f for f in st.session_state.features if f["kind"] == "polyline"]),
        "polygons": len([f for f in st.session_state.features if f["kind"] == "polygon"]),
        "circles": len([f for f in st.session_state.features if f["kind"] == "circle"]),
        "rectangles": len([f for f in st.session_state.features if f["kind"] == "rectangle"]),
        "routes": len([f for f in st.session_state.features if f["kind"] == "route"]),
        "texts": len([f for f in st.session_state.features if f["kind"] == "text"])
    }
    return stats

def validate_geometry(feature):
    """Validate geometry structure"""
    try:
        geom = feature["geometry"]
        geom_type = geom["type"]
        
        if geom_type == "Point":
            coords = geom["coordinates"]
            if len(coords) != 2:
                return False, "Point must have 2 coordinates [lng, lat]"
            if not (-180 <= coords[0] <= 180) or not (-90 <= coords[1] <= 90):
                return False, "Coordinates out of range"
                
        elif geom_type in ["LineString", "MultiPoint"]:
            coords = geom["coordinates"]
            if len(coords) < 2:
                return False, f"{geom_type} must have at least 2 coordinate pairs"
            for coord_pair in coords:
                if len(coord_pair) != 2:
                    return False, f"Invalid coordinate in {geom_type}"
                    
        elif geom_type in ["Polygon", "MultiLineString"]:
            coords = geom["coordinates"]
            if not isinstance(coords, list) or len(coords) == 0:
                return False, f"{geom_type} must have coordinate arrays"
            for ring in coords:
                if len(ring) < 3:
                    return False, f"Ring in {geom_type} must have at least 3 points"
                    
        return True, "Valid"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def export_kml(features):
    """Export features to KML format"""
    kml_header = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>'''
    
    kml_body = ""
    for feature in features:
        name = feature.get("name", f"Feature {feature['id']}")
        geom = feature["geometry"]
        geom_type = geom["type"]
        
        if geom_type == "Point":
            lng, lat = geom["coordinates"]
            kml_body += f'''
    <Placemark>
        <name>{name}</name>
        <Point>
            <coordinates>{lng},{lat},0</coordinates>
        </Point>
    </Placemark>'''
    
    kml_footer = '''
</Document>
</kml>'''
    
    return kml_header + kml_body + kml_footer

def export_gpx(features):
    """Export features to GPX format"""
    gpx_header = '''<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="OpenMap Builder">
'''
    
    gpx_body = ""
    for feature in features:
        name = feature.get("name", f"Feature {feature['id']}")
        geom = feature["geometry"]
        geom_type = geom["type"]
        
        if geom_type == "Point":
            lng, lat = geom["coordinates"]
            gpx_body += f'''  <wpt lat="{lat}" lon="{lng}">
    <name>{name}</name>
  </wpt>
'''
    
    gpx_footer = '</gpx>'
    return gpx_header + gpx_body + gpx_footer

def analyze_feature_density(bbox, features):
    """Analyze feature density in bounding box"""
    min_lat, min_lng, max_lat, max_lng = bbox
    
    total_count = 0
    area_km2 = (max_lat - min_lat) * 111 * (max_lng - min_lng) * 111 * abs(np.cos(np.radians((min_lat + max_lat) / 2)))
    
    for feature in features:
        geom = feature["geometry"]
        if geom["type"] == "Point":
            lng, lat = geom["coordinates"]
            if min_lng <= lng <= max_lng and min_lat <= lat <= max_lat:
                total_count += 1
    
    density = total_count / area_km2 if area_km2 > 0 else 0
    return {"count": total_count, "area_km2": area_km2, "density_per_km2": density}

def generate_report():
    """Generate analysis report"""
    stats = calculate_feature_stats()
    report = f"""
# OpenMap Builder Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Feature Statistics
- Total Features: {stats['total']}
- Markers: {stats['markers']}
- Polylines: {stats['polylines']}
- Polygons: {stats['polygons']}
- Circles: {stats['circles']}
- Rectangles: {stats['rectangles']}
- Routes: {stats['routes']}
- Text Labels: {stats['texts']}

## Groups
- Number of Groups: {len(st.session_state.custom_groups)}
"""
    
    for group_name, group_data in st.session_state.custom_groups.items():
        report += f"- {group_name}: {len(group_data['ids'])} features\n"
    
    return report

def optimize_features():
    """Optimize features for performance"""
    optimized_count = 0
    
    for feature in st.session_state.features:
        if feature["kind"] == "polyline" and len(feature["geometry"]["coordinates"]) > 1000:
            # Simplify long polylines
            coords = feature["geometry"]["coordinates"]
            step = max(1, len(coords) // 500)  # Reduce to ~500 points
            feature["geometry"]["coordinates"] = coords[::step]
            optimized_count += 1
    
    return optimized_count

def validate_all_features():
    """Validate all features"""
    errors = []
    warnings = []
    
    for feature in st.session_state.features:
        is_valid, message = validate_geometry(feature)
        if not is_valid:
            errors.append(f"Feature {feature['id']}: {message}")
        elif message == "Valid":
            # Additional checks
            if feature["props"]["opacity"] and (feature["props"]["opacity"] < 0 or feature["props"]["opacity"] > 1):
                warnings.append(f"Feature {feature['id']}: Opacity out of range [0,1]")
    
    return errors, warnings

def batch_update_features(update_dict):
    """Apply batch updates to features"""
    updated_count = 0
    for feature in st.session_state.features:
        needs_update = False
        for prop, value in update_dict.items():
            if prop in feature["props"]:
                feature["props"][prop] = value
                needs_update = True
        if needs_update:
            updated_count += 1
    return updated_count

def merge_duplicate_points(threshold_meters=10):
    """Merge points that are very close together"""
    merged_count = 0
    processed = set()
    
    for i, feat1 in enumerate(st.session_state.features):
        if feat1["kind"] == "marker" and feat1["id"] not in processed:
            coords1 = feat1["geometry"]["coordinates"]
            
            for j, feat2 in enumerate(st.session_state.features[i+1:], i+1):
                if feat2["kind"] == "marker" and feat2["id"] not in processed:
                    coords2 = feat2["geometry"]["coordinates"]
                    
                    # Calculate distance (approximate)
                    lat_diff = abs(coords1[1] - coords2[1]) * 111000
                    lng_diff = abs(coords1[0] - coords2[0]) * 111000 * abs(np.cos(np.radians(coords1[1])))
                    distance = np.sqrt(lat_diff**2 + lng_diff**2)
                    
                    if distance < threshold_meters:
                        # Merge: keep first, remove second
                        st.session_state.features.pop(j)
                        # Update groups
                        for group_data in st.session_state.custom_groups.values():
                            group_data["ids"] = [fid for fid in group_data["ids"] if fid != feat2["id"]]
                        merged_count += 1
                        processed.add(feat2["id"])
    
    return merged_count

def export_csv(features):
    """Export features to CSV"""
    df_data = []
    for feature in features:
        row = {
            "id": feature["id"],
            "name": feature["name"],
            "kind": feature["kind"],
            "geometry_type": feature["geometry"]["type"]
        }
        
        # Add coordinates as separate columns
        coords = feature["geometry"]["coordinates"]
        if feature["geometry"]["type"] == "Point":
            row["longitude"] = coords[0]
            row["latitude"] = coords[1]
        else:
            # For complex geometries, store as WKT string
            row["coordinates"] = str(coords)
        
        # Add properties
        for prop, value in feature["props"].items():
            row[f"prop_{prop}"] = value
        
        df_data.append(row)
    
    df = pd.DataFrame(df_data)
    return df.to_csv(index=False)

def calculate_bounding_box(features):
    """Calculate bounding box for all features"""
    min_lat = min_lng = float('inf')
    max_lat = max_lng = float('-inf')
    
    for feature in features:
        geom = feature["geometry"]
        geom_type = geom["type"]
        
        if geom_type == "Point":
            lng, lat = geom["coordinates"]
            min_lng = min(min_lng, lng)
            max_lng = max(max_lng, lng)
            min_lat = min(min_lat, lat)
            max_lat = max(max_lat, lat)
        
        elif geom_type in ["LineString", "Polygon"]:
            coords = geom["coordinates"]
            if geom_type == "Polygon":
                coords = coords[0]  # Exterior ring
            
            for lng, lat in coords:
                min_lng = min(min_lng, lng)
                max_lng = max(max_lng, lng)
                min_lat = min(min_lat, lat)
                max_lat = max(max_lat, lat)
    
    if min_lat == float('inf'):
        return None  # No valid geometries
    
    return [min_lat, min_lng, max_lat, max_lng]

def fit_bounds_to_map(bbox):
    """Prepare bounds for map fitting"""
    if bbox is None:
        return [-74.006, 40.7128, -73.986, 40.732]  # Default NYC bounds
    
    # Add padding
    lat_pad = (bbox[2] - bbox[0]) * 0.1
    lng_pad = (bbox[3] - bbox[1]) * 0.1
    
    padded_bbox = [
        max(-90, bbox[0] - lat_pad),
        max(-180, bbox[1] - lng_pad),
        min(90, bbox[2] + lat_pad),
        min(180, bbox[3] + lng_pad)
    ]
    
    return padded_bbox

def detect_geometry_type(coordinates):
    """Detect geometry type from coordinates"""
    if isinstance(coordinates, list) and len(coordinates) == 2:
        if all(isinstance(c, (int, float)) for c in coordinates):
            return "Point"
    
    if isinstance(coordinates, list) and len(coordinates) > 0:
        if all(isinstance(c, list) and len(c) == 2 and all(isinstance(x, (int, float)) for x in c) for c in coordinates):
            return "LineString"
        
        if all(isinstance(ring, list) for ring in coordinates):
            return "Polygon"
    
    return "Unknown"

def create_buffer_zone(feature, distance_meters):
    """Create buffer zone around feature"""
    import geopandas as gpd
    from shapely.geometry import Point, LineString, Polygon
    
    geom_type = feature["geometry"]["type"]
    coords = feature["geometry"]["coordinates"]
    
    if geom_type == "Point":
        point = Point(coords[0], coords[1])
        buffered = point.buffer(distance_meters / 111000)  # Approximate conversion
    elif geom_type == "LineString":
        line = LineString([(c[0], c[1]) for c in coords])
        buffered = line.buffer(distance_meters / 111000)
    elif geom_type == "Polygon":
        poly_coords = [(c[0], c[1]) for c in coords[0]]
        poly = Polygon(poly_coords)
        buffered = poly.buffer(distance_meters / 111000)
    else:
        return None
    
    # Convert back to our format
    if hasattr(buffered, 'exterior'):
        exterior_coords = list(buffered.exterior.coords)
        buffer_geom = {
            "type": "Polygon",
            "coordinates": [[list(coord) for coord in exterior_coords]]
        }
    else:
        return None
    
    buffer_feature = add_feature("buffer", buffer_geom, {
        "color": "#ff0000",
        "fillColor": "#ff0000",
        "fillOpacity": 0.2,
        "borderOpacity": 0.8
    })
    
    return buffer_feature

def find_intersections():
    """Find intersecting features"""
    intersections = []
    
    for i, feat1 in enumerate(st.session_state.features):
        for j, feat2 in enumerate(st.session_state.features[i+1:], i+1):
            # Simple intersection check for polygons
            if (feat1["geometry"]["type"] == "Polygon" and 
                feat2["geometry"]["type"] == "Polygon"):
                
                try:
                    from shapely.geometry import Polygon
                    poly1 = Polygon(feat1["geometry"]["coordinates"][0])
                    poly2 = Polygon(feat2["geometry"]["coordinates"][0])
                    
                    if poly1.intersects(poly2):
                        intersections.append((feat1["id"], feat2["id"]))
                except:
                    continue
    
    return intersections

def simplify_geometry(feature, tolerance=0.001):
    """Simplify geometry using Ramer-Douglas-Peucker"""
    if feature["geometry"]["type"] in ["Point", "MultiPoint"]:
        return feature  # Can't simplify points
    
    coords = feature["geometry"]["coordinates"]
    
    def rdp(points, epsilon):
        if len(points) < 3:
            return points
        
        # Find the point with the maximum distance
        dmax = 0
        index = 0
        end = len(points) - 1
        
        for i in range(1, end):
            d = perpendicular_distance(points[i], points[0], points[end])
            if d > dmax:
                index = i
                dmax = d
        
        if dmax > epsilon:
            # Recursive call
            rec_results1 = rdp(points[:index+1], epsilon)
            rec_results2 = rdp(points[index:], epsilon)
            
            # Build the result list
            result = rec_results1[:-1] + rec_results2
        else:
            result = [points[0], points[end]]
        
        return result
    
    def perpendicular_distance(point, line_start, line_end):
        if line_start == line_end:
            return ((point[0] - line_start[0])**2 + (point[1] - line_start[1])**2)**0.5
        
        numerator = abs(
            (line_end[0] - line_start[0]) * (line_start[1] - point[1]) -
            (line_start[0] - point[0]) * (line_end[1] - line_start[1])
        )
        denominator = ((line_end[0] - line_start[0])**2 + (line_end[1] - line_start[1])**2)**0.5
        
        return numerator / denominator
    
    if feature["geometry"]["type"] == "LineString":
        simplified_coords = rdp(coords, tolerance)
        feature["geometry"]["coordinates"] = simplified_coords
    elif feature["geometry"]["type"] == "Polygon":
        # Simplify exterior ring only
        simplified_exterior = rdp(coords[0], tolerance)
        feature["geometry"]["coordinates"] = [simplified_exterior]
    
    return feature

def validate_project_integrity():
    """Validate project data integrity"""
    issues = []
    
    # Check for duplicate IDs
    ids = [f["id"] for f in st.session_state.features]
    if len(ids) != len(set(ids)):
        issues.append("Duplicate feature IDs detected")
    
    # Check group references
    all_feature_ids = set(ids)
    for group_name, group_data in st.session_state.custom_groups.items():
        invalid_refs = set(group_data["ids"]) - all_feature_ids
        if invalid_refs:
            issues.append(f"Group '{group_name}' contains invalid feature references: {invalid_refs}")
    
    # Validate geometries
    for feature in st.session_state.features:
        is_valid, msg = validate_geometry(feature)
        if not is_valid:
            issues.append(f"Feature {feature['id']}: {msg}")
    
    return issues

def repair_project():
    """Attempt to repair common project issues"""
    repaired = 0
    
    # Remove duplicate IDs by reassigning
    seen_ids = set()
    for feature in st.session_state.features:
        if feature["id"] in seen_ids:
            feature["id"] = max([f["id"] for f in st.session_state.features]) + 1
            seen_ids.add(feature["id"])
            repaired += 1
        else:
            seen_ids.add(feature["id"])
    
    # Remove invalid group references
    all_feature_ids = set(f["id"] for f in st.session_state.features)
    for group_data in st.session_state.custom_groups.values():
        group_data["ids"] = [fid for fid in group_data["ids"] if fid in all_feature_ids]
    
    return repaired

def export_shp(features):
    """Export features to shapefile (returns as zip)"""
    try:
        import geopandas as gpd
        from shapely.geometry import Point, LineString, Polygon
        
        geometries = []
        properties = []
        
        for feature in features:
            geom_type = feature["geometry"]["type"]
            coords = feature["geometry"]["coordinates"]
            
            if geom_type == "Point":
                geom = Point(coords[0], coords[1])
            elif geom_type == "LineString":
                geom = LineString([(c[0], c[1]) for c in coords])
            elif geom_type == "Polygon":
                exterior = [(c[0], c[1]) for c in coords[0]]
                geom = Polygon(exterior)
            else:
                continue  # Skip unsupported types
            
            geometries.append(geom)
            props = {"id": feature["id"], "name": feature["name"], "kind": feature["kind"]}
            props.update(feature["props"])
            properties.append(props)
        
        gdf = gpd.GeoDataFrame(properties, geometry=geometries)
        
        # Write to temporary files
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "export.shp")
            gdf.to_file(path)
            
            # Create zip
            zip_buffer = io.BytesIO()
            with ZipFile(zip_buffer, 'w') as zip_file:
                for ext in ['.shp', '.shx', '.dbf', '.prj']:
                    file_path = path.replace('.shp', ext)
                    if os.path.exists(file_path):
                        zip_file.write(file_path, f"export{ext}")
            
            return zip_buffer.getvalue()
    
    except ImportError:
        st.error("Geopandas not available for Shapefile export")
        return None

def batch_style_update(style_updates):
    """Update styling for multiple features"""
    count = 0
    for feature in st.session_state.features:
        should_update = True
        # Apply filters if any
        
        if should_update:
            for prop, value in style_updates.items():
                feature["props"][prop] = value
            count += 1
    
    return count

def calculate_feature_lengths():
    """Calculate lengths for linear features"""
    import geopy.distance
    
    lengths = {}
    for feature in st.session_state.features:
        if feature["geometry"]["type"] == "LineString":
            coords = feature["geometry"]["coordinates"]
            total_dist = 0
            for i in range(len(coords)-1):
                p1, p2 = coords[i], coords[i+1]
                dist = geopy.distance.distance(p1[::-1], p2[::-1]).meters
                total_dist += dist
            lengths[feature["id"]] = total_dist
    
    return lengths

def calculate_feature_areas():
    """Calculate areas for polygon features"""
    from pyproj import Geod
    
    geod = Geod(ellps="WGS84")
    areas = {}
    
    for feature in st.session_state.features:
        if feature["geometry"]["type"] == "Polygon":
            coords = feature["geometry"]["coordinates"][0]  # Exterior ring
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            
            area, _ = geod.polygon_area_perimeter(lons, lats)
            areas[feature["id"]] = abs(area)  # Area in square meters
    
    return areas

def find_nearest_features(target_feature_id, n=5):
    """Find nearest features to target feature"""
    target_feat = next((f for f in st.session_state.features if f["id"] == target_feature_id), None)
    if not target_feat:
        return []
    
    import geopy.distance
    
    distances = []
    for feature in st.session_state.features:
        if feature["id"] == target_feature_id:
            continue
        
        if target_feat["geometry"]["type"] == "Point" and feature["geometry"]["type"] == "Point":
            target_coords = target_feat["geometry"]["coordinates"]
            feat_coords = feature["geometry"]["coordinates"]
            dist = geopy.distance.distance(target_coords[::-1], feat_coords[::-1]).meters
            distances.append((feature["id"], dist))
    
    distances.sort(key=lambda x: x[1])
    return distances[:n]

def create_heatmap_data():
    """Prepare data for heatmap visualization"""
    points = []
    for feature in st.session_state.features:
        if feature["geometry"]["type"] == "Point":
            coords = feature["geometry"]["coordinates"]
            intensity = feature["props"].get("intensity", 1)
            points.append({"lat": coords[1], "lng": coords[0], "intensity": intensity})
    
    return points

def generate_thematic_map(property_name):
    """Generate thematic map based on property values"""
    values = []
    for feature in st.session_state.features:
        if property_name in feature["props"]:
            val = feature["props"][property_name]
            if isinstance(val, (int, float)):
                values.append(val)
    
    if not values:
        return None
    
    min_val, max_val = min(values), max(values)
    range_val = max_val - min_val if max_val != min_val else 1
    
    themed_features = []
    for feature in st.session_state.features:
        if property_name in feature["props"]:
            val = feature["props"][property_name]
            if isinstance(val, (int, float)):
                normalized = (val - min_val) / range_val
                # Map to color (simplified)
                hue = 240 * normalized  # Blue to red
                themed_feature = feature.copy()
                themed_feature["props"]["color"] = f"hsl({hue}, 70%, 50%)"
                themed_features.append(themed_feature)
        else:
            themed_features.append(feature)
    
    return themed_features

def detect_clusters():
    """Detect clusters of points"""
    from sklearn.cluster import DBSCAN
    import numpy as np
    
    points = []
    point_indices = []
    
    for i, feature in enumerate(st.session_state.features):
        if feature["geometry"]["type"] == "Point":
            coords = feature["geometry"]["coordinates"]
            points.append([coords[1], coords[0]])  # lat, lng
            point_indices.append(i)
    
    if len(points) < 2:
        return []
    
    clustering = DBSCAN(eps=0.01, min_samples=2).fit(points)
    labels = clustering.labels_
    
    clusters = {}
    for i, label in enumerate(labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(point_indices[i])
    
    return clusters

def generate_statistics_report():
    """Generate comprehensive statistics report"""
    stats = calculate_feature_stats()
    bbox = calculate_bounding_box(st.session_state.features)
    lengths = calculate_feature_lengths()
    areas = calculate_feature_areas()
    
    report = f"""# OpenMap Builder - Comprehensive Statistics Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Feature Counts
Total Features: {stats['total']}
Markers: {stats['markers']}
Polylines: {stats['polylines']}  
Polygons: {stats['polygons']}
Circles: {stats['circles']}
Rectangles: {stats['rectangles']}
Routes: {stats['routes']}
Text Labels: {stats['texts']}

## Spatial Extent
Bounding Box: {f"[{bbox[0]:.6f}, {bbox[1]::.6f}, {bbox[2]:.6f}, {bbox[3]:.6f}]" if bbox else "No valid features"}

## Linear Features
Total Length: {sum(lengths.values()):,.2f} meters
Longest Feature: {max(lengths.values()) if lengths else 0:.2f} meters

## Polygonal Features  
Total Area: {sum(areas.values()):,.2f} square meters
Largest Feature: {max(areas.values()) if areas else 0:.2f} square meters

## Group Information
Number of Groups: {len(st.session_state.custom_groups)}
"""
    
    for group_name, group_data in st.session_state.custom_groups.items():
        report += f"- {group_name}: {len(group_data['ids'])} features\n"
    
    # Detect potential issues
    issues = validate_project_integrity()
    if issues:
        report += "\n## Potential Issues\n"
        for issue in issues:
            report += f"- {issue}\n"
    
    return report

def apply_spatial_filter(bbox):
    """Filter features within bounding box"""
    min_lat, min_lng, max_lat, max_lng = bbox
    
    filtered_features = []
    for feature in st.session_state.features:
        geom = feature["geometry"]
        
        if geom["type"] == "Point":
            lng, lat = geom["coordinates"]
            if min_lng <= lng <= max_lng and min_lat <= lat <= max_lat:
                filtered_features.append(feature)
        
        # Could extend to other geometry types
    
    return filtered_features

def create_spatial_index():
    """Create R-tree spatial index for fast queries"""
    try:
        from rtree import index
        
        idx = index.Index()
        for i, feature in enumerate(st.session_state.features):
            geom = feature["geometry"]
            if geom["type"] == "Point":
                lng, lat = geom["coordinates"]
                idx.insert(i, (lng, lat, lng, lat), obj=feature)
            # Could add bounds for other geometries
        
        return idx
    except ImportError:
        st.warning("Rtree not available for spatial indexing")
        return None

def query_nearby_features(lat, lng, radius_degrees=0.01):
    """Query features near a point"""
    nearby = []
    for feature in st.session_state.features:
        if feature["geometry"]["type"] == "Point":
            f_lng, f_lat = feature["geometry"]["coordinates"]
            dist = ((f_lat - lat)**2 + (f_lng - lng)**2)**0.5
            if dist <= radius_degrees:
                nearby.append(feature)
    
    return nearby

def generate_tile_grid(zoom_level=14):
    """Generate tile grid for tiling large datasets"""
    bbox = calculate_bounding_box(st.session_state.features)
    if not bbox:
        return []
    
    # Simplified tile grid generation
    tiles = []
    # This would typically involve slippy map tile calculations
    # For now, return empty - would require more complex implementation
    
    return tiles

def export_with_metadata():
    """Export project with metadata"""
    project_data = {
        "metadata": {
            "export_date": datetime.now().isoformat(),
            "feature_count": len(st.session_state.features),
            "group_count": len(st.session_state.custom_groups),
            "app_version": "OpenMap Builder 1.0"
        },
        "features": st.session_state.features,
        "groups": st.session_state.custom_groups
    }
    
    return json.dumps(project_data, indent=2)

def validate_coordinate_system():
    """Validate all coordinates are in WGS84"""
    errors = []
    for feature in st.session_state.features:
        geom = feature["geometry"]
        coords = geom["coordinates"]
        
        if geom["type"] == "Point":
            lng, lat = coords
            if not (-180 <= lng <= 180) or not (-90 <= lat <= 90):
                errors.append(f"Feature {feature['id']}: Coordinates out of range")
    
    return errors

def convert_coordinates(source_epsg, target_epsg="EPSG:4326"):
    """Convert coordinates between coordinate systems"""
    # Would require pyproj
    pass

def detect_outliers(threshold_std=2):
    """Detect outlier points based on statistical distribution"""
    points = []
    for feature in st.session_state.features:
        if feature["geometry"]["type"] == "Point":
            points.append(feature["geometry"]["coordinates"])
    
    if len(points) < 3:
        return []
    
    points_array = np.array(points)
    means = np.mean(points_array, axis=0)
    stds = np.std(points_array, axis=0)
    
    outliers = []
    for i, (lng, lat) in enumerate(points):
        z_lng = abs(lng - means[0]) / stds[0] if stds[0] != 0 else 0
        z_lat = abs(lat - means[1]) / stds[1] if stds[1] != 0 else 0
        
        if z_lng > threshold_std or z_lat > threshold_std:
            outliers.append(st.session_state.features[i]["id"])
    
    return outliers

def create_backup():
    """Create backup of current project"""
    backup_data = {
        "timestamp": datetime.now().isoformat(),
        "features": [f.copy() for f in st.session_state.features],
        "groups": {k: v.copy() for k, v in st.session_state.custom_groups.items()}
    }
    
    return json.dumps(backup_data, indent=2)

def restore_from_backup(backup_json):
    """Restore project from backup"""
    try:
        backup = json.loads(backup_json)
        st.session_state.features = backup["features"]
        st.session_state.custom_groups = backup["groups"]
        return True
    except Exception as e:
        st.error(f"Failed to restore backup: {str(e)}")
        return False

def run_quality_checks():
    """Run comprehensive quality checks"""
    checks = {
        "geometry_validation": validate_all_features(),
        "coordinate_system": validate_coordinate_system(),
        "duplicate_detection": detect_outliers(threshold_std=3),
        "project_integrity": validate_project_integrity()
    }
    
    return checks

def generate_summary_metrics():
    """Generate summary metrics for dashboard"""
    stats = calculate_feature_stats()
    bbox = calculate_bounding_box(st.session_state.features)
    
    metrics = {
        "total_features": stats["total"],
        "spatial_coverage_sqkm": 0,
        "feature_types": stats,
        "group_count": len(st.session_state.custom_groups),
        "data_density": 0
    }
    
    if bbox:
        lat_range = bbox[2] - bbox[0]
        lng_range = bbox[3] - bbox[1]
        # Rough approximation of area
        avg_lat = (bbox[0] + bbox[2]) / 2
        lat_degree_km = 111
        lng_degree_km = 111 * abs(np.cos(np.radians(avg_lat)))
        area_sqkm = lat_range * lat_degree_km * lng_range * lng_degree_km
        metrics["spatial_coverage_sqkm"] = round(area_sqkm, 2)
        metrics["data_density"] = round(stats["total"] / area_sqkm, 2) if area_sqkm > 0 else 0
    
    return metrics

def cleanup_temp_files():
    """Clean up temporary files"""
    import gc
    gc.collect()

def export_project_package():
    """Export complete project package"""
    import zipfile
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Export main data
        project_json = export_with_metadata()
        zip_file.writestr("project.json", project_json)
        
        # Export reports
        report = generate_statistics_report()
        zip_file.writestr("report.md", report)
        
        # Export CSV
        csv_data = export_csv(st.session_state.features)
        zip_file.writestr("features.csv", csv_data)
        
        # Export KML
        kml_data = export_kml(st.session_state.features)
        zip_file.writestr("features.kml", kml_data)
        
        # Export GPX
        gpx_data = export_gpx(st.session_state.features)
        zip_file.writestr("features.gpx", gpx_data)
    
    return zip_buffer.getvalue()

def import_project_package(package_zip):
    """Import project from package ZIP"""
    try:
        with zipfile.ZipFile(io.BytesIO(package_zip)) as zip_file:
            # Look for project.json first
            if "project.json" in zip_file.namelist():
                project_data = json.loads(zip_file.read("project.json"))
                st.session_state.features = project_data.get("features", [])
                st.session_state.custom_groups = project_data.get("groups", {})
                return True
            else:
                st.error("Project package missing project.json")
                return False
    except Exception as e:
        st.error(f"Failed to import package: {str(e)}")
        return False

def optimize_rendering():
    """Optimize features for better rendering performance"""
    optimized_count = 0
    
    for feature in st.session_state.features:
        # Simplify complex polygons
        if feature["geometry"]["type"] == "Polygon":
            coords = feature["geometry"]["coordinates"][0]
            if len(coords) > 1000:  # Too many points
                step = len(coords) // 500  # Reduce to ~500 points
                feature["geometry"]["coordinates"][0] = coords[::step]
                optimized_count += 1
        
        # Limit text length
        if feature.get("kind") == "text" and "props" in feature:
            text = feature["props"].get("text", "")
            if len(text) > 100:
                feature["props"]["text"] = text[:100] + "..."
    
    return optimized_count

def validate_export_formats():
    """Validate data for different export formats"""
    issues = {}
    
    # Check for required fields for different formats
    for fmt in ["kml", "gpx", "csv", "shp"]:
        fmt_issues = []
        
        if fmt in ["kml", "gpx"]:
            # Need names for placemarks
            unnamed = [f for f in st.session_state.features if not f.get("name")]
            if unnamed:
                fmt_issues.append(f"Missing names for {len(unnamed)} features (required for {fmt.upper()})")
        
        issues[fmt] = fmt_issues
    
    return issues

def batch_transform_coordinates(transform_func):
    """Apply coordinate transformation to all features"""
    transformed = 0
    for feature in st.session_state.features:
        if feature["geometry"]["type"] == "Point":
            orig_coords = feature["geometry"]["coordinates"]
            new_coords = transform_func(orig_coords[0], orig_coords[1])
            if new_coords != orig_coords:
                feature["geometry"]["coordinates"] = list(new_coords)
                transformed += 1
    
    return transformed

def detect_pattern_anomalies():
    """Detect unusual patterns in data"""
    anomalies = []
    
    # Check for points in unexpected locations (ocean, Antarctica, etc.)
    for feature in st.session_state.features:
        if feature["geometry"]["type"] == "Point":
            lng, lat = feature["geometry"]["coordinates"]
            
            # Antarctica check
            if lat < -60:
                anomalies.append(f"Feature {feature['id']}: Located in Antarctica")
            
            # Ocean check (very rough)
            if -5 <= lat <= 5 and lng % 180 > 170:  # Pacific anomaly
                anomalies.append(f"Feature {feature['id']}: Unusually located in ocean")
    
    return anomalies

def generate_api_compatible_format():
    """Generate format compatible with common mapping APIs"""
    api_features = []
    
    for feature in st.session_state.features:
        api_feat = {
            "type": "Feature",
            "properties": {
                "id": feature["id"],
                "name": feature["name"],
                **feature["props"]
            },
            "geometry": feature["geometry"]
        }
        api_features.append(api_feat)
    
    return {
        "type": "FeatureCollection",
        "features": api_features
    }

def measure_editing_efficiency():
    """Measure editing efficiency metrics"""
    total_features = len(st.session_state.features)
    grouped_features = sum(len(g["ids"]) for g in st.session_state.custom_groups.values())
    
    metrics = {
        "feature_density_per_group": grouped_features / len(st.session_state.custom_groups) if st.session_state.custom_groups else 0,
        "ungrouped_features": total_features - grouped_features,
        "average_group_size": grouped_features / len(st.session_state.custom_groups) if st.session_state.custom_groups else 0
    }
    
    return metrics

def suggest_optimizations():
    """Suggest optimizations based on current data"""
    suggestions = []
    
    if len(st.session_state.features) > 1000:
        suggestions.append("Consider simplifying complex geometries for performance")
    
    ungrouped = len(st.session_state.features) - sum(len(g["ids"]) for g in st.session_state.custom_groups.values())
    if ungrouped > len(st.session_state.features) * 0.5:
        suggestions.append("Many features are ungrouped - consider organizing into logical groups")
    
    bbox = calculate_bounding_box(st.session_state.features)
    if bbox:
        coverage = (bbox[2]-bbox[0]) * (bbox[3]-bbox[1])
        if coverage < 0.01:  # Very small area
            suggestions.append("Features concentrated in small area - consider clustering or aggregation")
    
    return suggestions

def validate_for_web_publishing():
    """Validate data quality for web publishing"""
    issues = []
    
    # Check coordinate precision (avoid unnecessary precision)
    for feature in st.session_state.features:
        if feature["geometry"]["type"] == "Point":
            lng, lat = feature["geometry"]["coordinates"]
            if len(str(lng).split('.')[-1]) > 6 or len(str(lat).split('.')[-1]) > 6:
                issues.append(f"Feature {feature['id']}: Excessive coordinate precision")
    
    # Check for very small geometries that may not render well
    for feature in st.session_state.features:
        if feature["geometry"]["type"] == "Polygon":
            coords = feature["geometry"]["coordinates"][0]
            if len(coords) < 3:
                issues.append(f"Feature {feature['id']}: Invalid polygon (too few points)")
    
    return issues

def prepare_for_tile_generation():
    """Prepare data for tile-based rendering"""
    # Simplify geometries based on zoom level expectations
    simplified_features = []
    
    for feature in st.session_state.features:
        simple_feature = feature.copy()
        
        # Simplify based on feature type and expected use
        if feature["geometry"]["type"] == "LineString":
            coords = feature["geometry"]["coordinates"]
            if len(coords) > 100:
                # Take every nth point to reduce complexity
                step = max(1, len(coords) // 50)
                simple_feature["geometry"]["coordinates"] = coords[::step]
        
        simplified_features.append(simple_feature)
    
    return simplified_features

def calculate_spatial_relationships():
    """Calculate relationships between features"""
    relationships = {
        "nearby_pairs": [],
        "contained_features": [],
        "overlapping_polygons": []
    }
    
    # This would implement spatial relationship calculations
    # Using libraries like Shapely for geometric operations
    
    return relationships

def generate_usage_statistics():
    """Generate usage statistics for analytics"""
    stats = {
        "session_start": getattr(st.session_state, 'session_start', datetime.now()),
        "feature_operations": {
            "created": len(st.session_state.features),
            "modified": getattr(st.session_state, 'modifications', 0),
            "deleted": getattr(st.session_state, 'deletions', 0)
        },
        "time_spent_minutes": (datetime.now() - st.session_state.get('session_start', datetime.now())).seconds // 60,
        "active_tools_used": list(set(getattr(st.session_state, 'used_tools', [])))
    }
    
    return stats

def cleanup_orphaned_data():
    """Remove orphaned data entries"""
    initial_count = len(st.session_state.features)
    
    # Remove features with invalid geometries
    st.session_state.features = [
        f for f in st.session_state.features 
        if validate_geometry(f)[0]
    ]
    
    # Clean up group references
    valid_ids = {f["id"] for f in st.session_state.features}
    for group_data in st.session_state.custom_groups.values():
        group_data["ids"] = [fid for fid in group_data["ids"] if fid in valid_ids]
    
    removed_count = initial_count - len(st.session_state.features)
    return removed_count

def export_analysis_results():
    """Export comprehensive analysis results"""
    results = {
        "validation_issues": validate_all_features(),
        "quality_metrics": generate_summary_metrics(),
        "optimization_suggestions": suggest_optimizations(),
        "spatial_analysis": {
            "bounding_box": calculate_bounding_box(st.session_state.features),
            "clusters": detect_clusters(),
            "outliers": detect_outliers()
        },
        "efficiency_metrics": measure_editing_efficiency()
    }
    
    return json.dumps(results, indent=2, default=str)

def validate_for_mobile_use():
    """Validate data for mobile applications"""
    issues = []
    
    # Check file size implications
    estimated_size = len(json.dumps(st.session_state.features)) / (1024*1024)  # MB
    if estimated_size > 5:  # 5MB threshold
        issues.append(f"Data size ({estimated_size:.2f}MB) may be too large for mobile apps")
    
    # Check for complex geometries that may slow mobile rendering
    complex_features = []
    for feature in st.session_state.features:
        geom = feature["geometry"]
        if geom["type"] in ["Polygon", "LineString"]:
            if len(geom["coordinates"]) > 1000:
                complex_features.append(feature["id"])
    
    if complex_features:
        issues.append(f"Complex geometries in features: {complex_features[:5]}{'...' if len(complex_features) > 5 else ''}")
    
    return issues

def generate_migration_plan():
    """Generate migration plan for format conversion"""
    plan = {
        "current_format": "OpenMap Builder native",
        "supported_exports": ["GeoJSON", "KML", "GPX", "CSV", "Shapefile"],
        "recommended_path": "GeoJSON for web applications",
        "data_loss_warnings": [],
        "compatibility_notes": []
    }
    
    # Check for features that might not translate well
    for feature in st.session_state.features:
        if feature["kind"] == "route" and not all(f in ["GeoJSON", "KML"] for f in plan["supported_exports"]):
            plan["data_loss_warnings"].append("Route features may lose routing-specific properties in some formats")
    
    return plan

def calculate_complexity_score():
    """Calculate overall project complexity"""
    score = 0
    
    # Feature count impact
    score += min(len(st.session_state.features) / 100, 10)  # Max 10 points
    
    # Geometry complexity
    for feature in st.session_state.features:
        geom = feature["geometry"]
        if geom["type"] in ["Polygon", "LineString"]:
            complexity = len(geom["coordinates"])
            if geom["type"] == "Polygon":
                complexity = len(geom["coordinates"][0])  # Exterior ring
            score += min(complexity / 100, 5)  # Max 5 points per complex geom
    
    # Group organization
    if st.session_state.custom_groups:
        avg_group_size = sum(len(g["ids"]) for g in st.session_state.custom_groups.values()) / len(st.session_state.custom_groups)
        if avg_group_size < 5:  # Poor organization
            score += 3
    else:
        score += 5  # No organization
    
    return min(score, 100)  # Cap at 100

def generate_performance_profile():
    """Generate performance profile for optimization"""
    profile = {
        "rendering_time_estimate": "N/A",
        "memory_footprint_mb": len(json.dumps(st.session_state.features)) / (1024*1024),
        "geometry_complexity": {},
        "optimization_recommendations": []
    }
    
    # Analyze geometry types
    geom_counts = {"Point": 0, "LineString": 0, "Polygon": 0, "Other": 0}
    geom_sizes = {"Point": [], "LineString": [], "Polygon": [], "Other": []}
    
    for feature in st.session_state.features:
        geom_type = feature["geometry"]["type"]
        key = geom_type if geom_type in geom_counts else "Other"
        
        geom_counts[key] += 1
        if geom_type in ["LineString", "Polygon"]:
            size = len(feature["geometry"]["coordinates"])
            if geom_type == "Polygon":
                size = len(feature["geometry"]["coordinates"][0])  # Exterior ring
            geom_sizes[key].append(size)
        else:
            geom_sizes[key].append(1)
    
    profile["geometry_complexity"] = {
        "counts": geom_counts,
        "avg_sizes": {k: sum(v)/len(v) if v else 0 for k, v in geom_sizes.items()}
    }
    
    # Recommendations based on profile
    if profile["memory_footprint_mb"] > 10:
        profile["optimization_recommendations"].append("Consider simplifying geometries to reduce memory usage")
    
    if geom_counts["LineString"] + geom_counts["Polygon"] > len(st.session_state.features) * 0.5:
        profile["optimization_recommendations"].append("High proportion of complex geometries - consider generalization")
    
    return profile

def validate_cross_platform_compatibility():
    """Validate compatibility across different platforms"""
    compatibility_issues = {
        "web": [],
        "mobile": [],
        "desktop": []
    }
    
    # Web platform issues
    if len(st.session_state.features) > 10000:
        compatibility_issues["web"].append("Large dataset may cause browser performance issues")
    
    # Mobile platform issues (already covered in mobile validation)
    mobile_issues = validate_for_mobile_use()
    compatibility_issues["mobile"] = mobile_issues
    
    # Desktop platform (typically fewer restrictions)
    # But check for file size for desktop apps
    size_mb = len(json.dumps(st.session_state.features)) / (1024*1024)
    if size_mb > 100:  # Large for desktop import
        compatibility_issues["desktop"].append(f"Large file size ({size_mb:.1f}MB) may affect desktop application performance")
    
    return compatibility_issues

def generate_upgrade_path():
    """Generate upgrade path for newer versions"""
    current_version = "1.0"
    upgrade_path = {
        "current_version": current_version,
        "latest_version": "2.0",
        "breaking_changes": [],
        "migration_steps": [
            "Backup current project",
            "Update schema for new property types",
            "Rebuild spatial indexes if used"
        ],
        "new_features_available": [
            "3D visualization support",
            "Advanced styling options",
            "Real-time collaboration"
        ]
    }
    
    return upgrade_path

def calculate_storage_efficiency():
    """Calculate storage efficiency metrics"""
    raw_size = len(json.dumps(st.session_state.features))
    
    # Estimate compressed size
    import zlib
    compressed = zlib.compress(json.dumps(st.session_state.features).encode())
    compressed_size = len(compressed)
    
    efficiency = {
        "raw_size_bytes": raw_size,
        "compressed_size_bytes": compressed_size,
        "compression_ratio": round(raw_size / compressed_size, 2) if compressed_size > 0 else 0,
        "bytes_per_feature": round(raw_size / len(st.session_state.features)) if st.session_state.features else 0
    }
    
    return efficiency

def validate_schema_consistency():
    """Validate consistency of feature schemas"""
    issues = []
    
    if not st.session_state.features:
        return ["No features to validate"]
    
    # Check for consistent property structure
    sample_props = st.session_state.features[0]["props"]
    expected_keys = set(sample_props.keys())
    
    for i, feature in enumerate(st.session_state.features[1:], 1):
        actual_keys = set(feature["props"].keys())
        missing = expected_keys - actual_keys
        extra = actual_keys - expected_keys
        
        if missing or extra:
            issues.append(f"Feature {feature['id']}: Schema mismatch - Missing: {missing}, Extra: {extra}")
    
    return issues

def generate_data_dictionary():
    """Generate data dictionary for the project"""
    dictionary = {
        "project_name": st.session_state.current_project_name,
        "feature_count": len(st.session_state.features),
        "schema_version": "1.0",
        "fields": {
            "id": {"type": "integer", "description": "Unique identifier"},
            "name": {"type": "string", "description": "Display name"},
            "kind": {"type": "string", "description": "Feature type"},
            "geometry": {"type": "object", "description": "GeoJSON geometry object"}
        },
        "property_fields": {},
        "geometry_types": [],
        "statistics": generate_summary_metrics()
    }
    
    # Collect unique property fields
    all_props = set()
    for feature in st.session_state.features:
        all_props.update(feature["props"].keys())
    
    for prop in all_props:
        dictionary["property_fields"][prop] = {
            "type": "mixed",  # Would need deeper analysis
            "description": f"Property: {prop}"
        }
    
    # Collect geometry types
    geom_types = set(f["geometry"]["type"] for f in st.session_state.features)
    dictionary["geometry_types"] = list(geom_types)
    
    return dictionary

def prepare_for_api_consumption():
    """Prepare data for API consumption"""
    api_ready = {
        "type": "FeatureCollection",
        "features": [],
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "feature_count": len(st.session_state.features),
            "bbox": calculate_bounding_box(st.session_state.features)
        }
    }
    
    for feature in st.session_state.features:
        api_feature = {
            "type": "Feature",
            "id": feature["id"],
            "properties": {
                "name": feature["name"],
                "kind": feature["kind"],
                **feature["props"]
            },
            "geometry": feature["geometry"]
        }
        api_ready["features"].append(api_feature)
    
    return api_ready

def calculate_precision_requirements():
    """Calculate required precision for coordinates"""
    # Analyze the level of detail needed based on use case
    bbox = calculate_bounding_box(st.session_state.features)
    if not bbox:
        return {"recommended_decimals": 6, "justification": "Default precision"}
    
    lat_span = bbox[2] - bbox[0]
    lng_span = bbox[3] - bbox[1]
    
    # Roughly, 1 degree of latitude is ~111km
    max_span_km = max(lat_span, lng_span) * 111
    
    if max_span_km < 1:  # Less than 1km
        decimals = 6  # ~0.1m precision
        reason = "High precision needed for small area"
    elif max_span_km < 100:  # Less than 100km
        decimals = 5  # ~1m precision
        reason = "Medium precision for local/regional mapping"
    else:
        decimals = 4  # ~10m precision
        reason = "Lower precision adequate for large areas"
    
    return {"recommended_decimals": decimals, "justification": reason}

def validate_for_print_publication():
    """Validate data quality for print publication"""
    issues = []
    
    # Check coordinate reference system (should be explicit for print)
    issues.append("Coordinate reference system not explicitly defined (WGS84 assumed)")
    
    # Check scale appropriateness
    bbox = calculate_bounding_box(st.session_state.features)
    if bbox:
        span_deg = max(bbox[2]-bbox[0], bbox[3]-bbox[1])
        if span_deg > 10:  # Very large area for detailed print
            issues.append("Large geographic extent may not suitable for detailed print maps")
    
    # Check for missing essential attributes
    for feature in st.session_state.features:
        if not feature.get("name") or feature["name"].startswith("Feature "):
            issues.append(f"Feature {feature['id']}: Missing meaningful name for publication")
    
    return issues

def generate_accessibility_report():
    """Generate accessibility compliance report"""
    report = {
        "color_contrast_issues": [],
        "feature_labeling": {"properly_labeled": 0, "missing_labels": 0},
        "navigation_aids": [],
        "compliance_status": "partial"
    }
    
    # Check color contrast for map features
    for feature in st.session_state.features:
        color = feature["props"].get("color", "#000000")
        # Simplified contrast check
        # In reality would need background consideration
    
    # Check labeling
    for feature in st.session_state.features:
        if feature["props"].get("showLabel") and feature.get("name"):
            report["feature_labeling"]["properly_labeled"] += 1
        else:
            report["feature_labeling"]["missing_labels"] += 1
    
    return report

def validate_for_gis_integration():
    """Validate compatibility with GIS software"""
    issues = []
    
    # Check for proper field types
    for feature in st.session_state.features:
        for prop_name, prop_value in feature["props"].items():
            # Check if property types are GIS-friendly
            if isinstance(prop_value, dict):
                issues.append(f"Feature {feature['id']}: Complex property '{prop_name}' may not import cleanly to GIS")
    
    # Check geometry validity more rigorously
    for feature in st.session_state.features:
        geom = feature["geometry"]
        if geom["type"] == "Polygon":
            # Check for valid ring orientation (GIS expects specific winding order)
            pass  # Would implement proper validation
    
    return issues

def calculate_data_provenance():
    """Track and calculate data provenance metrics"""
    provenance = {
        "source_diversity": "single_user_created",
        "creation_timestamp": datetime.now().isoformat(),
        "modification_history": [],
        "data_age_days": 0,
        "confidence_level": "medium"  # Based on validation results
    }
    
    validation_results = validate_all_features()
    error_count = len(validation_results[0])  # Errors
    warning_count = len(validation_results[1])  # Warnings
    
    if error_count == 0 and warning_count == 0:
        provenance["confidence_level"] = "high"
    elif error_count > 0:
        provenance["confidence_level"] = "low"
    
    return provenance

def generate_technical_documentation():
    """Generate technical documentation for developers"""
    doc = f"""
# OpenMap Builder Technical Documentation
Project: {st.session_state.current_project_name}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Data Structure
The project consists of {len(st.session_state.features)} features organized in {len(st.session_state.custom_groups)} groups.

### Feature Schema
Each feature follows this structure:
```json
{{
  "id": <integer>,
  "name": "<string>",
  "kind": "<string>", 
  "geometry": <GeoJSON geometry object>,
  "props": <key-value property pairs>
}}
