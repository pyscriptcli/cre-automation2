import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
import geopandas as gpd
from shapely.geometry import Polygon
import tempfile
import os
import base64
from io import BytesIO
from PIL import Image
import branca.colormap as cm

st.set_page_config(page_title="Site Overlay & Polygon Tool", layout="wide")
st.title("🗺️ Map Overlay & Polygon Tool")

# Sidebar controls
st.sidebar.header("Controls")

# Upload image
uploaded_file = st.sidebar.file_uploader("Upload site plot (PNG/JPG)", type=["png", "jpg", "jpeg"])

# Opacity slider
opacity = st.sidebar.slider("Overlay opacity", 0.0, 1.0, 0.6)

# Basemap selection
basemap = st.sidebar.radio("Basemap", ["OpenStreetMap", "Clean Satellite"])

# Polygon style
st.sidebar.subheader("Polygon Style")
fill_color = st.sidebar.color_picker("Fill color", "#ff0000")
fill_opacity = st.sidebar.slider("Fill opacity", 0.0, 1.0, 0.3)
outline_color = st.sidebar.color_picker("Outline color", "#0000ff")
outline_weight = st.sidebar.slider("Outline weight", 1, 10, 3)

# Initialize session state for polygons
if 'polygons' not in st.session_state:
    st.session_state.polygons = []
if 'polygon_counter' not in st.session_state:
    st.session_state.polygon_counter = 0

# Create map
def get_basemap():
    if basemap == "Clean Satellite":
        return folium.Map(location=[0, 0], zoom_start=2, tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri')
    else:
        return folium.Map(location=[0, 0], zoom_start=2)

m = get_basemap()

# Add overlay if image uploaded
if uploaded_file:
    # Read image
    image = Image.open(uploaded_file)
    # Convert to base64
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    # Create overlay
    overlay = folium.raster_layers.ImageOverlay(
        image=image,
        bounds=[[-60, -120], [60, 120]],  # Default bounds, user can adjust
        opacity=opacity,
        interactive=True,
        cross_origin=False,
        zindex=1
    )
    overlay.add_to(m)

# Display existing polygons
for poly_data in st.session_state.polygons:
    folium.Polygon(
        locations=poly_data['coords'],
        color=outline_color,
        weight=outline_weight,
        fill_color=fill_color,
        fill_opacity=fill_opacity,
        popup=poly_data['label']
    ).add_to(m)

# Draw tool (rectangle/polygon)
draw = plugins.Draw(
    export=False,
    position='topleft',
    draw_options={
        'polyline': False,
        'circle': False,
        'circlemarker': False,
        'marker': False,
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
        }
    }
)
draw.add_to(m)

# Add layer control
folium.LayerControl().add_to(m)

# Display map
st_data = st_folium(m, width=1000, height=600)

# Capture drawn polygon
if st_data and 'last_active_drawing' in st_data:
    drawing = st_data['last_active_drawing']
    if drawing and 'geometry' in drawing:
        geom = drawing['geometry']
        if geom['type'] == 'Polygon':
            coords = geom['coordinates'][0]
            # Convert to lat/lng format
            lat_lng = [[lat, lng] for lng, lat in coords]
            
            # Add to session state
            st.session_state.polygon_counter += 1
            label = st.text_input(f"Label for polygon {st.session_state.polygon_counter}", 
                                 f"Polygon {st.session_state.polygon_counter}")
            
            if st.button("Save Polygon"):
                st.session_state.polygons.append({
                    'coords': lat_lng,
                    'label': label or f"Polygon {st.session_state.polygon_counter}",
                    'fill_color': fill_color,
                    'outline_color': outline_color
                })
                st.success("Polygon saved!")
                st.rerun()

# Display polygon list
if st.session_state.polygons:
    st.subheader("Saved Polygons")
    for i, poly in enumerate(st.session_state.polygons):
        col1, col2, col3 = st.columns([3, 1, 1])
        col1.write(f"**{poly['label']}** - {len(poly['coords'])} points")
        if col2.button("Delete", key=f"del_{i}"):
            st.session_state.polygons.pop(i)
            st.rerun()
    
    # Export to KML
    if st.button("Export to KML"):
        # Create GeoDataFrame
        polygons = []
        for poly in st.session_state.polygons:
            # Convert to shapely Polygon
            coords = [(lng, lat) for lat, lng in poly['coords']]
            polygons.append({
                'geometry': Polygon(coords),
                'label': poly['label'],
                'fill_color': poly.get('fill_color', '#ff0000'),
                'outline_color': poly.get('outline_color', '#0000ff')
            })
        
        gdf = gpd.GeoDataFrame(polygons, crs='EPSG:4326')
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.kml') as tmp:
            gdf.to_file(tmp.name, driver='KML')
            tmp_path = tmp.name
        
        # Read and offer download
        with open(tmp_path, 'rb') as f:
            kml_data = f.read()
        
        st.download_button(
            label="Download KML",
            data=kml_data,
            file_name="site_polygons.kml",
            mime="application/vnd.google-earth.kml+xml"
        )
        
        os.unlink(tmp_path)

# Instructions
st.sidebar.markdown("---")
st.sidebar.markdown("""
### Instructions
1. Upload your site plot image
2. Adjust opacity with slider
3. Use the draw tool (top-left) to draw polygons/rectangles
4. Add labels to your polygons
5. View and manage polygons in the list
6. Export all polygons to KML
""")

# Clear all polygons
if st.sidebar.button("Clear All Polygons"):
    st.session_state.polygons = []
    st.session_state.polygon_counter = 0
    st.rerun()
