import os
import io
import subprocess
import tempfile
import re
import json
import math
import streamlit as st
from pptx import Presentation
from pptx.util import Pt
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt as DocxPt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import base64
import traceback
import streamlit.components.v1 as components
import webbrowser
import threading

# --- MAP SPECIFIC DEPENDENCIES ---
import folium
from folium.plugins import Draw
import requests

# --- PROGRAMMATIC LIGHT MODE LOCK ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\n")

# --- MINIMAL UI CSS ---
MINIMAL_CRE_SYSTEM = """
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { margin-top: -50px; }
    .stDeployButton {display: none;}
    .stStatusWidget {display: none;}
    
    .stApp { background-color: #FFFFFF !important; color: #1A1A1A !important; font-family: 'Segoe UI', Arial, sans-serif !important; }
    div[data-testid="stHeader"] { background-color: #FFFFFF !important; display: none !important; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; max-width: 1200px !important; }
    
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[role="textbox"], div[data-baseweb="select"], textarea {
        background-color: #FFFFFF !important; border: 1px solid #CCCCCC !important; border-radius: 4px !important;
        color: #1A1A1A !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within, textarea:focus { border-color: #003366 !important; box-shadow: none !important; }
    input[type="text"], .stTextInput input, div[data-baseweb="select"] div, textarea { color: #1A1A1A !important; font-size: 14px !important; }
    
    div[data-baseweb="select"] { min-height: 32px !important; }
    div[data-baseweb="select"] > div { min-height: 32px !important; padding: 0 8px !important; }
    div[data-baseweb="select"] select { font-size: 13px !important; padding: 2px 8px !important; }
    
    section[data-testid="stFileUploader"] { background-color: #F8F8F8 !important; border: 1px solid #CCCCCC !important; border-radius: 4px !important; padding: 4px 12px !important; }
    .workspace-card { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 4px; padding: 16px; margin-bottom: 12px; }
    
    div.stButton > button { 
        background-color: #003366 !important; color: #FFFFFF !important; font-weight: 600 !important; font-size: 11px !important; 
        border: none !important; border-radius: 3px !important; padding: 5px 12px !important; width: 100% !important; min-height: 28px !important;
    }
    div.stButton > button:hover { background-color: #002244 !important; transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0, 51, 102, 0.3); }
    
    div[data-testid="stDownloadButton"] > button { 
        background-color: #003366 !important; color: #FFFFFF !important; border-radius: 3px !important; 
        font-weight: 600 !important; padding: 5px 12px !important; width: 100% !important; font-size: 11px !important; min-height: 28px !important;
    }
    
    .field-label { font-size: 13px !important; font-weight: 600 !important; color: #1A1A1A !important; padding-top: 6px; }
    .section-header { font-size: 15px !important; font-weight: 700 !important; color: #1A1A1A !important; margin-bottom: 10px; }
    .saved-indicator { background-color: #E8F5E9; padding: 6px 12px; border-radius: 4px; font-size: 13px; color: #2E7D32; border-left: 3px solid #2E7D32; margin-top: 6px; }
    hr { margin: 12px 0 !important; border-color: #E0E0E0 !important; }
    
    /* Maximize Dialog Viewport Space */
    div[role="dialog"] { max-width: 96vw !important; width: 96vw !important; padding: 0.8rem !important; }
    
    /* Full page map container */
    .map-container { width: 100%; height: 600px; }
</style>
"""

# --- FILE MANAGEMENT FUNCTIONS ---
def get_storage_dir():
    storage_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stored_templates")
    os.makedirs(storage_dir, exist_ok=True)
    return storage_dir

def save_template_to_file(template_bytes, template_name):
    storage_dir = get_storage_dir()
    safe_name = re.sub(r'[^\w\-_. ]', '_', template_name)
    if not safe_name.endswith('.pptx') and not safe_name.endswith('.docx'):
        safe_name += '.docx'
    filepath = os.path.join(storage_dir, safe_name)
    with open(filepath, 'wb') as f:
        f.write(template_bytes)
    return filepath

def load_template_from_file(template_name):
    storage_dir = get_storage_dir()
    filepath = os.path.join(storage_dir, template_name)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            return f.read()
    return None

def get_saved_templates():
    storage_dir = get_storage_dir()
    templates = []
    if os.path.exists(storage_dir):
        for file in os.listdir(storage_dir):
            if file.endswith('.pptx') or file.endswith('.docx'):
                filepath = os.path.join(storage_dir, file)
                stat = os.stat(filepath)
                templates.append({
                    'name': file, 'path': filepath, 'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'PPTX' if file.endswith('.pptx') else 'DOCX'
                })
    return templates

def delete_template_file(template_name):
    storage_dir = get_storage_dir()
    filepath = os.path.join(storage_dir, template_name)
    if os.path.exists(filepath):
        os.remove(filepath)
        config_name = template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
        config_path = os.path.join(storage_dir, config_name)
        if os.path.exists(config_path):
            os.remove(config_path)
        return True
    return False

def save_config_to_file(config_data, config_name="template_config.json"):
    storage_dir = get_storage_dir()
    filepath = os.path.join(storage_dir, config_name)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4)
    return filepath

def load_config_from_file(config_name="template_config.json"):
    storage_dir = get_storage_dir()
    filepath = os.path.join(storage_dir, config_name)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def auto_save_config():
    if st.session_state.saved_template_name and st.session_state.custom_mapping:
        config_name = st.session_state.saved_template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
        save_config_to_file(st.session_state.custom_mapping, config_name)

# --- DYNAMIC HIGH-RESOLUTION BOUNDING BOX GENERATOR ---
def generate_static_map_bounds(n, s, e, w, pin_lat, pin_lon, style="Hybrid", pin_color="#DC3545", pin_size=32):
    """Dynamically scales zoom to construct a massive high-res stitch and drops styled vector pins"""
    target_tiles_span = 8
    lon_span = e - w
    if lon_span <= 0: lon_span = 0.001
    
    zoom = int(math.log2(360.0 / lon_span * target_tiles_span))
    zoom = max(10, min(18, zoom))
    
    def deg2num(lat_deg, lon_deg, z):
        lat_rad = math.radians(lat_deg)
        n_tiles = 2.0 ** z
        xtile = int((lon_deg + 180.0) / 360.0 * n_tiles)
        ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n_tiles)
        return (xtile, ytile)
        
    x_min, y_min = deg2num(n, w, zoom)
    x_max, y_max = deg2num(s, e, zoom)
    
    tile_count = (x_max - x_min + 1) * (y_max - y_min + 1)
    if tile_count > 100:
        zoom -= 1
        x_min, y_min = deg2num(n, w, zoom)
        x_max, y_max = deg2num(s, e, zoom)
        
    width_tiles = x_max - x_min + 1
    height_tiles = y_max - y_min + 1
    tile_size = 256
    
    stitched = Image.new('RGB', (width_tiles * tile_size, height_tiles * tile_size))
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    styles = {
        "OSM": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        "Carto Light": "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        "Satellite": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        "Hybrid": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}&apistyle=s.t%3A2%7Cp.v%3Aoff"
    }
    url_template = styles.get(style, styles["Hybrid"])
    
    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            url = url_template.format(z=zoom, x=x, y=y)
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    img = Image.open(io.BytesIO(resp.content))
                    stitched.paste(img, ((x - x_min) * tile_size, (y - y_min) * tile_size))
            except Exception:
                pass
                
    def num2px(lat_deg, lon_deg, z):
        lat_rad = math.radians(lat_deg)
        n_tiles = 2.0 ** z
        px_x = (lon_deg + 180.0) / 360.0 * n_tiles * tile_size
        px_y = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n_tiles * tile_size
        return px_x, px_y
        
    px_w, py_n = num2px(n, w, zoom)
    px_e, py_s = num2px(s, e, zoom)
    
    base_x = x_min * tile_size
    base_y = y_min * tile_size
    
    left = int(px_w - base_x)
    top = int(py_n - base_y)
    right = int(px_e - base_x)
    bottom = int(py_s - base_y)
    
    left = max(0, min(left, stitched.width - 1))
    top = max(0, min(top, stitched.height - 1))
    right = max(left + 1, min(right, stitched.width))
    bottom = max(top + 1, min(bottom, stitched.height))
    
    cropped = stitched.crop((left, top, right, bottom)).convert("RGBA")
    
    draw = ImageDraw.Draw(cropped)
    pin_px_x, pin_px_y = num2px(pin_lat, pin_lon, zoom)
    pin_local_x = int(pin_px_x - base_x) - left
    pin_local_y = int(pin_px_y - base_y) - top
    
    pin_local_x = max(0, min(pin_local_x, cropped.width - 1))
    pin_local_y = max(0, min(pin_local_y, cropped.height - 1))
    
    scale = pin_size / 32.0
    w_px = 16 * scale
    h_px = 32 * scale
    
    draw.ellipse([
        pin_local_x - w_px - 2, pin_local_y - h_px - w_px + 2, 
        pin_local_x + w_px + 2, pin_local_y - h_px + w_px + 2
    ], fill="rgba(0,0,0,0.3)")
    
    draw.polygon([
        (pin_local_x, pin_local_y), 
        (pin_local_x - w_px, pin_local_y - h_px), 
        (pin_local_x + w_px, pin_local_y - h_px)
    ], fill="#ffffff")
    draw.ellipse([
        pin_local_x - w_px, pin_local_y - h_px - w_px, 
        pin_local_x + w_px, pin_local_y - h_px + w_px
    ], fill="#ffffff")
    
    draw.polygon([
        (pin_local_x, pin_local_y - (4 * scale)), 
        (pin_local_x - (w_px * 0.75), pin_local_y - h_px), 
        (pin_local_x + (w_px * 0.75), pin_local_y - h_px)
    ], fill=pin_color)
    draw.ellipse([
        pin_local_x - (w_px * 0.75), pin_local_y - h_px - (w_px * 0.75), 
        pin_local_x + (w_px * 0.75), pin_local_y - h_px + (w_px * 0.75)
    ], fill=pin_color)
    
    inner_radius = w_px * 0.33
    draw.ellipse([
        pin_local_x - inner_radius, pin_local_y - h_px - inner_radius, 
        pin_local_x + inner_radius, pin_local_y - h_px + inner_radius
    ], fill="#ffffff")
    
    final_img = cropped.convert("RGB")
    
    if cropped.width < 1000 or cropped.height < 1000:
        scale_factor = 2
        new_width = cropped.width * scale_factor
        new_height = cropped.height * scale_factor
        final_img = final_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    img_byte_arr = io.BytesIO()
    final_img.save(img_byte_arr, format='PNG', quality=95, optimize=True)
    img_byte_arr.seek(0)
    return img_byte_arr

# --- STANDALONE MAP EDITOR USING HTML COMPONENT ---
def build_map_html(lat, lon, zoom, style, color, size, token_key):
    """Build HTML for standalone map with Leaflet.js using string concatenation to avoid formatting issues"""
    
    # Map tile URLs
    tile_urls = {
        "Hybrid": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}&apistyle=s.t%3A2%7Cp.v%3Aoff",
        "Satellite": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        "Carto Light": "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        "OSM": "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    }
    
    tile_attribution = {
        "Hybrid": "Google Maps Hybrid",
        "Satellite": "Google Maps",
        "Carto Light": "CartoDB",
        "OSM": "OpenStreetMap"
    }
    
    tile_url = tile_urls.get(style, tile_urls["Hybrid"])
    attribution = tile_attribution.get(style, "Map data")
    
    # Build HTML using string concatenation to avoid format string conflicts
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Map Editor</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script src="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js"></script>
        <style>
            body { margin: 0; padding: 0; }
            #map { width: 100%; height: 100vh; }
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            // Initialize map
            var map = L.map('map').setView([''' + str(lat) + ''', ''' + str(lon) + '''] , ''' + str(zoom) + ''');
            
            // Add tile layer
            L.tileLayer(''' + repr(tile_url) + ''', {
                attribution: ''' + repr(attribution) + ''',
                maxZoom: 20
            }).addTo(map);
            
            // Create custom pin icon
            var pinSize = ''' + str(size) + ''';
            var pinColor = ''' + repr(color) + ''';
            
            // Create pin with SVG
            var pinIcon = L.divIcon({
                className: 'custom-pin',
                html: '<div style="position: relative; width: ' + pinSize + 'px; height: ' + pinSize + 'px;"><svg width="' + pinSize + '" height="' + pinSize + '" viewBox="0 0 32 32"><defs><filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="2" stdDeviation="2" flood-opacity="0.3"/></filter></defs><g filter="url(#shadow)"><path d="M16 32 L4 16 C4 8 9 0 16 0 C23 0 28 8 28 16 Z" fill="white" stroke="white" stroke-width="1"/><path d="M16 30 L6 16 C6 10 10 4 16 4 C22 4 26 10 26 16 Z" fill="' + pinColor + '" stroke="' + pinColor + '" stroke-width="0.5"/><circle cx="16" cy="14" r="5" fill="white" opacity="0.8"/><circle cx="16" cy="14" r="2" fill="' + pinColor + '"/></g></svg></div>',
                iconSize: [pinSize, pinSize],
                iconAnchor: [pinSize/2, pinSize],
                popupAnchor: [0, -pinSize/2]
            });
            
            // Add marker
            var marker = L.marker([''' + str(lat) + ''', ''' + str(lon) + '''], {
                icon: pinIcon,
                draggable: true
            }).addTo(map);
            
            // Store marker position
            var markerLat = ''' + str(lat) + ''';
            var markerLon = ''' + str(lon) + ''';
            
            // Update marker position on drag
            marker.on('dragend', function(e) {
                var pos = marker.getLatLng();
                markerLat = pos.lat;
                markerLon = pos.lng;
                // Send update back to parent
                if (window.opener) {
                    window.opener.postMessage({
                        type: 'map_update',
                        lat: pos.lat,
                        lng: pos.lng,
                        action: 'marker_moved'
                    }, '*');
                }
            });
            
            // Add draw control for rectangle
            var drawnItems = new L.FeatureGroup();
            map.addLayer(drawnItems);
            
            var drawControl = new L.Control.Draw({
                draw: {
                    polyline: false,
                    polygon: false,
                    circle: false,
                    marker: false,
                    circlemarker: false,
                    rectangle: {
                        shapeOptions: {
                            color: '#003366',
                            weight: 2,
                            opacity: 0.8
                        }
                    }
                },
                edit: {
                    featureGroup: drawnItems
                }
            });
            map.addControl(drawControl);
            
            // Store rectangle bounds
            var rectBounds = null;
            
            // Handle draw events
            map.on('draw:created', function(e) {
                drawnItems.clearLayers();
                var layer = e.layer;
                drawnItems.addLayer(layer);
                
                if (layer instanceof L.Rectangle) {
                    rectBounds = layer.getBounds();
                    // Send bounds back
                    if (window.opener) {
                        window.opener.postMessage({
                            type: 'map_update',
                            bounds: {
                                north: rectBounds.getNorth(),
                                south: rectBounds.getSouth(),
                                east: rectBounds.getEast(),
                                west: rectBounds.getWest()
                            },
                            action: 'rectangle_drawn'
                        }, '*');
                    }
                }
            });
            
            map.on('draw:deleted', function(e) {
                rectBounds = null;
                if (window.opener) {
                    window.opener.postMessage({
                        type: 'map_update',
                        bounds: null,
                        action: 'rectangle_deleted'
                    }, '*');
                }
            });
            
            // Handle zoom events
            map.on('zoomend', function() {
                if (window.opener) {
                    window.opener.postMessage({
                        type: 'map_update',
                        zoom: map.getZoom(),
                        action: 'zoom_changed'
                    }, '*');
                }
            });
            
            // Log instructions
            console.log('Map editor opened. Configure your map and then click "Import" in the main app.');
        </script>
    </body>
    </html>
    '''
    
    return html

# --- OPEN MAP IN NEW WINDOW ---
def open_map_in_new_window(token_key):
    """Open the map editor in a new browser window"""
    
    # Initialize map state for this token
    map_state_key = f"standalone_map_{token_key}"
    if map_state_key not in st.session_state:
        st.session_state[map_state_key] = {
            "lat": 14.3294,
            "lon": 120.9368,
            "zoom": 15,
            "style": "Hybrid",
            "color": "#DC3545",
            "size": 32,
            "bounds": None,
            "has_image": False,
            "image_bytes": None
        }
    
    map_state = st.session_state[map_state_key]
    
    # Show current status
    if map_state["has_image"]:
        st.success("✅ Map snapshot ready")
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔄 Regenerate", key=f"regen_{token_key}"):
                map_state["has_image"] = False
                map_state["image_bytes"] = None
                st.rerun()
        with col2:
            if map_state["image_bytes"]:
                try:
                    img = Image.open(map_state["image_bytes"])
                    st.image(img, use_container_width=True)
                except:
                    pass
        return
    
    # Map configuration
    st.markdown("### Map Editor")
    st.info("Configure your map below, then click 'Open Map in New Window' to interact with it.")
    
    # Map settings
    with st.expander("⚙️ Map Settings", expanded=True):
        c1, c2, c3, c4 = st.columns([1.2, 1.6, 0.6, 1.2])
        with c1:
            style = st.selectbox(
                "Style",
                ["Hybrid", "Satellite", "Carto Light", "OSM"],
                index=["Hybrid", "Satellite", "Carto Light", "OSM"].index(map_state["style"]),
                key=f"style_{token_key}"
            )
            map_state["style"] = style
        with c2:
            lat = st.number_input("Latitude", value=map_state["lat"], format="%.6f", step=0.0001, key=f"lat_{token_key}")
            lon = st.number_input("Longitude", value=map_state["lon"], format="%.6f", step=0.0001, key=f"lon_{token_key}")
            map_state["lat"] = lat
            map_state["lon"] = lon
        with c3:
            color = st.color_picker("Pin Color", value=map_state["color"], key=f"color_{token_key}")
            map_state["color"] = color
        with c4:
            size = st.slider("Pin Size", 16, 64, value=map_state["size"], key=f"size_{token_key}")
            map_state["size"] = size
    
    # Generate the map HTML
    map_html = build_map_html(
        map_state["lat"], 
        map_state["lon"], 
        map_state["zoom"], 
        map_state["style"], 
        map_state["color"], 
        map_state["size"], 
        token_key
    )
    
    # Create a temporary HTML file and encode it
    html_bytes = map_html.encode('utf-8')
    b64_html = base64.b64encode(html_bytes).decode('utf-8')
    
    # Create a data URI
    data_uri = f"data:text/html;base64,{b64_html}"
    
    # JavaScript to open in new window with specific features
    js_code = f"""
    <script>
    function openMapWindow() {{
        var width = 1200;
        var height = 800;
        var left = (screen.width - width) / 2;
        var top = (screen.height - height) / 2;
        var features = 'width=' + width + ',height=' + height + ',left=' + left + ',top=' + top + ',menubar=no,toolbar=no,location=no,status=no,scrollbars=yes,resizable=yes';
        var win = window.open('{data_uri}', 'MapEditor', features);
        if (win) {{
            win.focus();
        }} else {{
            alert('Please allow popups for this site to open the map editor.');
        }}
    }}
    </script>
    <button onclick="openMapWindow()" style="
        background-color: #003366;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 4px;
        font-size: 16px;
        cursor: pointer;
        width: 100%;
        font-weight: 600;
    ">
        🗺️ Open Map in New Window
    </button>
    """
    
    # Display the button
    st.components.v1.html(js_code, height=60)
    
    st.caption("💡 Configure the map in the new window, then come back here and click 'Generate & Import Map Snapshot' below.")
    
    # Import button
    if st.button("📥 Generate & Import Map Snapshot", key=f"import_map_{token_key}", use_container_width=True):
        with st.spinner("Generating high-resolution map image..."):
            # Use the current settings
            lat = map_state["lat"]
            lon = map_state["lon"]
            n, s, e, w = lat + 0.02, lat - 0.02, lon + 0.02, lon - 0.02
            
            # Generate the image
            img_bytes = generate_static_map_bounds(
                n, s, e, w,
                lat, lon,
                style=map_state["style"],
                pin_color=map_state["color"],
                pin_size=map_state["size"]
            )
            
            map_state["image_bytes"] = img_bytes
            map_state["has_image"] = True
            st.success("✅ Map snapshot generated and imported!")
            st.rerun()

# --- CORE UTILITIES ---
def smart_crop_to_fit(img_file, target_w_emu, target_h_emu):
    try:
        img = Image.open(img_file)
        img_w, img_h = img.size
        target_ratio = target_w_emu / target_h_emu
        img_ratio = img_w / img_h
        
        if img_ratio > target_ratio:
            new_w = int(img_h * target_ratio)
            left = (img_w - new_w) // 2
            img = img.crop((left, 0, left + new_w, img_h))
        else:
            new_h = int(img_w / target_ratio)
            top = (img_h - new_h) // 2
            img = img.crop((0, top, img_w, top + new_h))
            
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG', quality=95)
        img_byte_arr.seek(0)
        return img_byte_arr
    except Exception:
        return img_file

def extract_placeholders_from_pptx(pptx_bytes):
    prs = Presentation(io.BytesIO(pptx_bytes))
    tokens = []
    seen = set()
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                found = re.findall(r'\{\{.*?\}\}', shape.text)
                for token in found:
                    if token not in seen:
                        tokens.append(token)
                        seen.add(token)
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        found = re.findall(r'\{\{.*?\}\}', cell.text)
                        for token in found:
                            if token not in seen:
                                tokens.append(token)
                                seen.add(token)
    return tokens

def extract_placeholders_from_docx(docx_bytes):
    doc = Document(io.BytesIO(docx_bytes))
    tokens = []
    seen = set()
    for paragraph in doc.paragraphs:
        found = re.findall(r'\{\{.*?\}\}', paragraph.text)
        for token in found:
            if token not in seen:
                tokens.append(token)
                seen.add(token)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                found = re.findall(r'\{\{.*?\}\}', cell.text)
                for token in found:
                    if token not in seen:
                        tokens.append(token)
                        seen.add(token)
    return tokens

def extract_placeholders(template_bytes, template_type):
    if template_type == 'pptx':
        return extract_placeholders_from_pptx(template_bytes)
    elif template_type == 'docx':
        return extract_placeholders_from_docx(template_bytes)
    return []

def replace_text_in_paragraph(paragraph, text_inputs):
    for run in paragraph.runs:
        for token, value in text_inputs.items():
            if token in run.text:
                replacement = str(value) if value else ''
                run.text = run.text.replace(token, replacement)
    if hasattr(paragraph, 'text') and paragraph.text:
        for token, value in text_inputs.items():
            if token in paragraph.text:
                if not paragraph.runs:
                    paragraph.add_run()
                for run in paragraph.runs:
                    if token in run.text:
                        replacement = str(value) if value else ''
                        run.text = run.text.replace(token, replacement)

def generate_pptx_bytes(template_bytes, text_inputs, image_inputs):
    prs = Presentation(io.BytesIO(template_bytes))
    for slide in prs.slides:
        shapes_to_delete = []
        images_to_add = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                text_content = shape.text
                for img_token, img_file in image_inputs.items():
                    if img_token in text_content and img_file is not None:
                        images_to_add.append((img_file, shape.left, shape.top, shape.width, shape.height))
                        shapes_to_delete.append(shape)
                        break
        for shape in slide.shapes:
            if shape not in shapes_to_delete:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        replace_text_in_paragraph(paragraph, text_inputs)
                if hasattr(shape, 'table') and shape.table:
                    for row in shape.table.rows:
                        for cell in row.cells:
                            if cell.text_frame:
                                for paragraph in cell.text_frame.paragraphs:
                                    replace_text_in_paragraph(paragraph, text_inputs)
        for img_file, left, top, width, height in images_to_add:
            try:
                processed_img = smart_crop_to_fit(img_file, width, height)
                slide.shapes.add_picture(processed_img, left, top, width=width, height=height)
            except Exception:
                pass
        for old_shape in shapes_to_delete:
            try:
                sp = old_shape._element
                sp.getparent().remove(sp)
            except Exception:
                pass
    pptx_stream = io.BytesIO()
    prs.save(pptx_stream)
    return pptx_stream.getvalue()

def generate_docx_bytes(template_bytes, text_inputs, image_inputs):
    doc = Document(io.BytesIO(template_bytes))
    for paragraph in doc.paragraphs:
        has_image = False
        for img_token in image_inputs.keys():
            if img_token in paragraph.text:
                has_image = True
                break
        if not has_image:
            replace_text_in_paragraph(paragraph, text_inputs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    replace_text_in_paragraph(paragraph, text_inputs)
    doc_stream = io.BytesIO()
    doc.save(doc_stream)
    doc_stream.seek(0)
    return doc_stream.getvalue()

def get_download_filename(template_name, file_type):
    if template_name:
        base_name = re.sub(r'\.(pptx|docx)$', '', template_name)
        base_name = re.sub(r'[^\w\-_. ]', '_', base_name)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{base_name}_{timestamp}.{file_type}"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"Generated_Document_{timestamp}.{file_type}"

def simple_uploader_row(label_text, allowed_types, key):
    st.markdown(f'<div class="field-label">{label_text}</div>', unsafe_allow_html=True)
    return st.file_uploader(label_text, type=allowed_types, key=f"val_{key}", label_visibility="collapsed")


# --- INIT APP ---
st.set_page_config(page_title="OpenFlux", layout="wide", initial_sidebar_state="collapsed")
st.markdown(MINIMAL_CRE_SYSTEM, unsafe_allow_html=True)

if "custom_mapping" not in st.session_state: st.session_state.custom_mapping = {}
if "tokens" not in st.session_state: st.session_state.tokens = []
if "template_bytes" not in st.session_state: st.session_state.template_bytes = None
if "saved_template_name" not in st.session_state: st.session_state.saved_template_name = None
if "template_loaded" not in st.session_state: st.session_state.template_loaded = False
if "template_type" not in st.session_state: st.session_state.template_type = None
if "delete_trigger" not in st.session_state: st.session_state.delete_trigger = False
if "show_delete_confirm" not in st.session_state: st.session_state.show_delete_confirm = False
if "template_to_delete" not in st.session_state: st.session_state.template_to_delete = None
if "save_success" not in st.session_state: st.session_state.save_success = False
if "saved_file_name" not in st.session_state: st.session_state.saved_file_name = None
if "clear_uploader" not in st.session_state: st.session_state.clear_uploader = False

st.markdown("<hr style='margin: 4px 0 12px 0;'>", unsafe_allow_html=True)

# --- TEMPLATE MANAGEMENT SECTION ---
st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
st.markdown('<div class="section-header">Template</div>', unsafe_allow_html=True)

col_template1, col_template2 = st.columns(2)

with col_template1:
    saved_templates = get_saved_templates()
    template_options = ["Select saved template"]
    if saved_templates:
        for t in saved_templates:
            template_options.append(f"{t['name']} ({t['type']})")
    dropdown_col, delete_col = st.columns([4, 1])
    with dropdown_col:
        selected_template = st.selectbox("Load Template", template_options, key="saved_template_select", label_visibility="collapsed")
    with delete_col:
        if selected_template and selected_template != "Select saved template":
            template_name = selected_template.split(' (')[0]
            if st.button("Delete", key="delete_template", help="Delete this template"):
                st.session_state.show_delete_confirm = True
                st.session_state.template_to_delete = template_name
                st.rerun()
                
    if st.session_state.show_delete_confirm:
        st.warning(f"Are you sure you want to delete '{st.session_state.template_to_delete}'?")
        col_confirm1, col_confirm2 = st.columns([1, 1])
        with col_confirm1:
            if st.button("Yes, Delete", key="confirm_delete"):
                if delete_template_file(st.session_state.template_to_delete):
                    st.session_state.delete_trigger = True
                    st.session_state.template_bytes = None
                    st.session_state.saved_template_name = None
                    st.session_state.template_loaded = False
                    st.session_state.tokens = []
                    st.session_state.show_delete_confirm = False
                    st.session_state.template_to_delete = None
                    st.rerun()
        with col_confirm2:
            if st.button("Cancel", key="cancel_delete"):
                st.session_state.show_delete_confirm = False
                st.session_state.template_to_delete = None
                st.rerun()
                
    if selected_template and selected_template != "Select saved template" and not st.session_state.delete_trigger:
        template_name = selected_template.split(' (')[0]
        template_bytes = load_template_from_file(template_name)
        if template_bytes:
            st.session_state.template_bytes = template_bytes
            st.session_state.saved_template_name = template_name
            st.session_state.template_loaded = True
            st.session_state.template_type = 'pptx' if template_name.endswith('.pptx') else 'docx'
            config_name = template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
            config_data = load_config_from_file(config_name)
            if config_data:
                st.session_state.custom_mapping = config_data
            tokens = extract_placeholders(template_bytes, st.session_state.template_type)
            st.session_state.tokens = tokens

with col_template2:
    uploader_key = "new_template_upload_clear" if st.session_state.clear_uploader else "new_template_upload"
    uploaded_template = st.file_uploader("Upload New Template", type=["pptx", "docx"], label_visibility="collapsed", key=uploader_key)
    if st.session_state.clear_uploader: st.session_state.clear_uploader = False
    
    if uploaded_template:
        template_bytes = uploaded_template.getvalue()
        st.session_state.template_bytes = template_bytes
        st.session_state.saved_template_name = None
        st.session_state.template_loaded = True
        st.session_state.template_type = 'pptx' if uploaded_template.name.endswith('.pptx') else 'docx'
        tokens = extract_placeholders(template_bytes, st.session_state.template_type)
        st.session_state.tokens = tokens
        
        if st.button("Save Template", key="save_template_btn", use_container_width=True):
            saved_path = save_template_to_file(template_bytes, uploaded_template.name)
            st.session_state.saved_template_name = uploaded_template.name
            if st.session_state.custom_mapping:
                config_name = uploaded_template.name.replace('.pptx', '').replace('.docx', '') + '_config.json'
                save_config_to_file(st.session_state.custom_mapping, config_name)
            st.session_state.save_success = True
            st.session_state.saved_file_name = uploaded_template.name
            st.session_state.clear_uploader = True
            st.rerun()

if st.session_state.save_success:
    st.success(f"Template '{st.session_state.saved_file_name}' saved successfully!")
    st.session_state.save_success = False
    st.session_state.saved_file_name = None

if st.session_state.template_bytes is not None:
    template_name = st.session_state.saved_template_name or "Unsaved Template"
    template_type = st.session_state.template_type or "Unknown"
    st.markdown(f'<div class="saved-indicator">Active: {template_name} ({template_type.upper()})</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

template_bytes = st.session_state.template_bytes
template_type = st.session_state.template_type
u_template = None
if template_bytes is not None:
    u_template = type('obj', (object,), {'getvalue': lambda: template_bytes})()

text_data = {}
image_data = {}
field_types = {}

if u_template is not None and st.session_state.tokens:
    tokens = st.session_state.tokens
    if not tokens:
        st.info("No placeholders found in the template.")
    else:
        st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Placeholder Values</div>', unsafe_allow_html=True)
        
        mid_point = len(tokens) // 2
        col1, col2 = st.columns(2)
        
        def render_token_fields(token_list, col_target):
            with col_target:
                for token in token_list:
                    clean_label = token.replace("{", "").replace("}", "")
                    current_type = st.session_state.custom_mapping.get(token, "Text")
                    
                    col_a, col_b = st.columns([3, 1])
                    with col_b:
                        st.markdown('<div style="padding-top: 6px;"></div>', unsafe_allow_html=True)
                        data_type = st.selectbox(
                            "Type", ["Text", "Image", "Map"], 
                            index=["Text", "Image", "Map"].index(current_type) if current_type in ["Text", "Image", "Map"] else 0,
                            key=f"type_{token}", label_visibility="collapsed"
                        )
                        if data_type != current_type:
                            st.session_state.custom_mapping[token] = data_type
                            auto_save_config()
                            st.rerun()
                            
                    with col_a:
                        if data_type == "Image" and template_type == 'pptx':
                            image_data[token] = simple_uploader_row(clean_label, ["png", "jpg", "jpeg"], token)
                            field_types[token] = "Image"
                        elif data_type == "Map" and template_type == 'pptx':
                            st.markdown(f'<div class="field-label">{clean_label} (Map Mode)</div>', unsafe_allow_html=True)
                            
                            # Use the new window map editor
                            open_map_in_new_window(token)
                            
                            # Get the map image if it was generated
                            map_state_key = f"standalone_map_{token}"
                            if map_state_key in st.session_state:
                                map_state = st.session_state[map_state_key]
                                if map_state["has_image"] and map_state["image_bytes"]:
                                    image_data[token] = map_state["image_bytes"]
                                    st.caption("✅ Map snapshot attached")
                            
                            field_types[token] = "Image"
                        else:
                            if data_type in ["Image", "Map"] and template_type != 'pptx':
                                st.warning("Media & Map uploads are only supported in PPTX files.")
                            st.markdown(f'<div class="field-label">{clean_label}</div>', unsafe_allow_html=True)
                            text_data[token] = st.text_input(clean_label, key=f"val_{token}", label_visibility="collapsed")
                            field_types[token] = "Text"

        render_token_fields(tokens[:mid_point], col1)
        render_token_fields(tokens[mid_point:], col2)
        st.markdown('</div>', unsafe_allow_html=True)

# --- DOWNLOAD SECTION ---
if u_template is not None:
    st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Download Document</div>', unsafe_allow_html=True)
    
    template_name = st.session_state.saved_template_name or "Generated_Document"
    base_template_name = re.sub(r'\.(pptx|docx)$', '', template_name)
    col1, col2 = st.columns(2)
    
    with col1:
        if template_type != 'pptx':
            st.button("Download PPTX", disabled=True, use_container_width=True)
        else:
            try:
                pptx_data = generate_pptx_bytes(template_bytes, text_data, image_data)
                st.download_button(
                    label="Download PPTX", data=pptx_data,
                    file_name=get_download_filename(base_template_name, "pptx"),
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True, key="download_pptx"
                )
            except Exception as e:
                st.error(f"Error generating PPTX: {str(e)}")
                
    with col2:
        if template_type != 'docx':
            st.button("Download DOCX", disabled=True, use_container_width=True)
        else:
            try:
                docx_data = generate_docx_bytes(template_bytes, text_data, image_data)
                if docx_data:
                    st.download_button(
                        label="Download DOCX", data=docx_data,
                        file_name=get_download_filename(base_template_name, "docx"),
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True, key="download_docx"
                    )
            except Exception as e:
                st.error(f"Error generating document: {str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Please upload or select a template to begin")
