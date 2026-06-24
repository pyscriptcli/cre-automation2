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
from PIL import Image, ImageDraw
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt as DocxPt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import base64
import traceback
import time

# --- MAP SPECIFIC DEPENDENCIES ---
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
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
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; max-width: 1300px !important; }
    
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
    .editor-card { background-color: #F8F9FA; border: 2px solid #003366; border-radius: 6px; padding: 20px; }
    
    div.stButton > button { 
        background-color: #003366 !important; color: #FFFFFF !important; font-weight: 600 !important; font-size: 12px !important; 
        border: none !important; border-radius: 4px !important; padding: 6px 14px !important; width: 100% !important; min-height: 32px !important;
    }
    div.stButton > button:hover { background-color: #002244 !important; transform: translateY(-1px); box-shadow: 0 4px 8px rgba(0, 51, 102, 0.2); }
    div.stButton > button:disabled { background-color: #666666 !important; opacity: 0.6; cursor: not-allowed; }
    
    .field-label { font-size: 13px !important; font-weight: 600 !important; color: #1A1A1A !important; padding-top: 6px; }
    .section-header { font-size: 15px !important; font-weight: 700 !important; color: #1A1A1A !important; margin-bottom: 10px; }
    .saved-indicator { background-color: #E8F5E9; padding: 6px 12px; border-radius: 4px; font-size: 13px; color: #2E7D32; border-left: 3px solid #2E7D32; margin-top: 6px; }
    hr { margin: 12px 0 !important; border-color: #E0E0E0 !important; }
    
    div[data-testid="stForm"] { border: 1px solid #E0E0E0 !important; border-radius: 6px !important; padding: 1rem !important; background-color: #FFFFFF; }
    
    .placeholder-label {
        font-weight: 600 !important;
        font-size: 13px !important;
        color: #1A1A1A !important;
        margin-bottom: 4px;
    }
    
    /* Type mapping section */
    .type-mapping-section {
        background-color: #F8F9FA !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 6px !important;
        padding: 12px !important;
        margin: 8px 0 12px 0 !important;
    }
    .type-mapping-grid {
        display: grid !important;
        grid-template-columns: 1fr 1fr 1fr !important;
        gap: 6px 16px !important;
        margin-top: 8px !important;
    }
    
    /* Map editor controls */
    .map-controls-row {
        display: flex !important;
        gap: 12px !important;
        align-items: center !important;
        flex-wrap: wrap !important;
        margin-bottom: 12px !important;
    }
    .map-control-item {
        display: flex !important;
        align-items: center !important;
        gap: 6px !important;
    }
    .map-control-item label {
        font-size: 12px !important;
        font-weight: 500 !important;
        color: #333 !important;
        white-space: nowrap !important;
    }
    .size-control {
        display: flex !important;
        align-items: center !important;
        gap: 4px !important;
    }
    .size-control button {
        min-width: 28px !important;
        height: 28px !important;
        padding: 0 8px !important;
        font-size: 14px !important;
        background: #f0f0f0 !important;
        border: 1px solid #ccc !important;
        border-radius: 4px !important;
        cursor: pointer !important;
    }
    .size-control button:hover {
        background: #e0e0e0 !important;
    }
    .size-control span {
        min-width: 30px !important;
        text-align: center !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    @media (max-width: 768px) {
        .type-mapping-grid {
            grid-template-columns: 1fr !important;
        }
        .map-controls-row {
            flex-direction: column !important;
            align-items: stretch !important;
        }
    }
</style>
"""

# --- FILE MANAGEMENT FUNCTIONS ---
def get_storage_dir():
    storage_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stored_templates")
    os.makedirs(storage_dir, exist_ok=True)
    return storage_dir

def get_temp_config_path(template_name):
    storage_dir = get_storage_dir()
    safe_name = re.sub(r'[^\w\-_. ]', '_', template_name or "unsaved_template")
    return os.path.join(storage_dir, f"{safe_name}_temp_form_data.json")

def get_github_templates():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    templates = []
    if os.path.exists(root_dir):
        for file in os.listdir(root_dir):
            if file.startswith('template_') and (file.endswith('.pptx') or file.endswith('.docx')):
                filepath = os.path.join(root_dir, file)
                stat = os.stat(filepath)
                display_name = file.replace('template_', '').replace('.pptx', '').replace('.docx', '')
                templates.append({
                    'name': file,
                    'display_name': display_name,
                    'path': filepath,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'PPTX' if file.endswith('.pptx') else 'DOCX',
                    'source': 'github'
                })
    return templates

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
    root_dir = os.path.dirname(os.path.abspath(__file__))
    root_filepath = os.path.join(root_dir, template_name)
    if os.path.exists(root_filepath):
        with open(root_filepath, 'rb') as f:
            return f.read()
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
                    'name': file,
                    'display_name': file.replace('.pptx', '').replace('.docx', ''),
                    'path': filepath,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'PPTX' if file.endswith('.pptx') else 'DOCX',
                    'source': 'stored'
                })
    templates.extend(get_github_templates())
    return templates

def delete_template_file(template_name):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(root_dir, template_name)):
        st.warning("Cannot delete GitHub repository templates")
        return False
    storage_dir = get_storage_dir()
    filepath = os.path.join(storage_dir, template_name)
    if os.path.exists(filepath):
        os.remove(filepath)
        config_name = template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
        config_path = os.path.join(storage_dir, config_name)
        if os.path.exists(config_path):
            os.remove(config_path)
        temp_config = get_temp_config_path(template_name)
        if os.path.exists(temp_config):
            os.remove(temp_config)
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

# --- DYNAMIC ULTRA HIGH-RESOLUTION BOUNDING BOX GENERATOR ---
def generate_static_map_bounds(n, s, e, w, pin_lat, pin_lon, style="Hybrid", pin_color="#DC3545", pin_size=32):
    lon_span = e - w
    lat_span = n - s
    target_width_tiles = 8
    if lon_span <= 0: lon_span = 0.001
    zoom = int(math.log2((360.0 / lon_span) * target_width_tiles))
    zoom = max(13, min(20, zoom))
    if lon_span < 0.01 and lat_span < 0.01:
        zoom = min(20, zoom + 2)
    def deg2num(lat_deg, lon_deg, z):
        lat_rad = math.radians(lat_deg)
        n_tiles = 2.0 ** z
        xtile = int((lon_deg + 180.0) / 360.0 * n_tiles)
        ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n_tiles)
        return (xtile, ytile)
    x_min, y_min = deg2num(n, w, zoom)
    x_max, y_max = deg2num(s, e, zoom)
    if x_max == x_min: x_max += 1
    if y_max == y_min: y_max += 1
    if (x_max - x_min + 1) * (y_max - y_min + 1) > 100:
        zoom -= 1
        x_min, y_min = deg2num(n, w, zoom)
        x_max, y_max = deg2num(s, e, zoom)
    width_tiles = x_max - x_min + 1
    height_tiles = y_max - y_min + 1
    tile_size = 256
    scale_factor = 2
    stitched = Image.new('RGB', (width_tiles * tile_size * scale_factor, height_tiles * tile_size * scale_factor))
    headers = {"User-Agent": "Mozilla/5.0"}
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
                resp = requests.get(url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    img = Image.open(io.BytesIO(resp.content))
                    img = img.resize((tile_size * scale_factor, tile_size * scale_factor), Image.Resampling.LANCZOS)
                    stitched.paste(img, ((x - x_min) * tile_size * scale_factor, (y - y_min) * tile_size * scale_factor))
            except Exception:
                pass
    def num2px(lat_deg, lon_deg, z):
        lat_rad = math.radians(lat_deg)
        n_tiles = 2.0 ** z
        px_x = (lon_deg + 180.0) / 360.0 * n_tiles * tile_size * scale_factor
        px_y = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n_tiles * tile_size * scale_factor
        return px_x, px_y
    px_w, py_n = num2px(n, w, zoom)
    px_e, py_s = num2px(s, e, zoom)
    base_x = x_min * tile_size * scale_factor
    base_y = y_min * tile_size * scale_factor
    left = int(px_w - base_x)
    top = int(py_n - base_y)
    right = int(px_e - base_x)
    bottom = int(py_s - base_y)
    if right <= left: right = left + 100
    if bottom <= top: bottom = top + 100
    cropped = stitched.crop((left, top, right, bottom)).convert("RGBA")
    draw = ImageDraw.Draw(cropped)
    pin_px_x, pin_px_y = num2px(pin_lat, pin_lon, zoom)
    pin_local_x = int(pin_px_x - base_x) - left
    pin_local_y = int(pin_px_y - base_y) - top
    pin_local_x = max(0, min(pin_local_x, cropped.width - 1))
    pin_local_y = max(0, min(pin_local_y, cropped.height - 1))
    img_width = cropped.width
    img_height = cropped.height
    base_scale = min(img_width, img_height) / 600.0
    scale = max(1.5, (pin_size / 32.0) * base_scale * 2.0)
    radius = int(20 * scale)
    shadow_offset = int(3 * scale)
    draw.ellipse([pin_local_x - radius - shadow_offset, pin_local_y - radius - shadow_offset, pin_local_x + radius + shadow_offset, pin_local_y + radius + shadow_offset], fill=(0, 0, 0, 60))
    draw.ellipse([pin_local_x - radius, pin_local_y - radius, pin_local_x + radius, pin_local_y + radius], fill=pin_color, outline=(255, 255, 255), width=int(3 * scale))
    star_size = int(radius * 0.6)
    star_points = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        r = star_size if i % 2 == 0 else star_size * 0.4
        star_points.append((pin_local_x + r * math.cos(angle), pin_local_y + r * math.sin(angle)))
    draw.polygon(star_points, fill=(255, 255, 255))
    final_img = cropped.convert("RGB")
    img_byte_arr = io.BytesIO()
    final_img.save(img_byte_arr, format='PNG', quality=100, optimize=True)
    img_byte_arr.seek(0)
    return img_byte_arr

# --- ISOLATED FULL-SCREEN MAP EDITOR PAGE ---
def render_isolated_map_editor():
    token_key = st.session_state.active_map_editor_token
    
    # Custom CSS adjustments to normalize structural alignment with visible labels
    st.markdown("""
        <style>
            /* Ensures that elements with varying native heights snap predictably */
            div[data-testid="stHorizontalBlock"] {
                align-items: flex-end !important;
                gap: 12px !important;
            }
            /* Match element inner wrapper boundaries cleanly */
            div[data-baseweb="input"], div[data-baseweb="select"], .stColorPicker div {
                height: 38px !important;
            }
            /* Clean formatting alignment for the manual color picker label */
            .manual-picker-label {
                font-family: 'Segoe UI', Arial, sans-serif !important;
                font-size: 14px !important;
                color: #1A1A1A !important;
                margin-bottom: 8px !important;
                line-height: 1.2;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="editor-card">', unsafe_allow_html=True)
    col_back, col_title = st.columns([1, 4])
    with col_back:
        if st.button("Back to Document", key="back_from_map"):
            st.session_state.restore_form_data = True
            st.session_state.active_map_editor_token = None
            st.rerun()
    with col_title:
        st.markdown(f"### Map Editor: {token_key}")
    st.markdown("</div><br>", unsafe_allow_html=True)

    style_key = f"map_style_{token_key}"
    coord_key = f"map_coord_{token_key}"
    color_key = f"map_color_{token_key}"
    size_key = f"map_size_{token_key}"
    dragged_key = f"map_dragged_{token_key}"
    image_key = f"map_bytes_holder_{token_key}"
    marker_key = f"map_marker_{token_key}"
    bounds_key = f"map_bounds_{token_key}"
    
    if style_key not in st.session_state: st.session_state[style_key] = "Hybrid"
    if coord_key not in st.session_state: st.session_state[coord_key] = "14.5995, 120.9842"
    if color_key not in st.session_state: st.session_state[color_key] = "#003366"
    # FIXED: Initial baseline size updated to 16
    if size_key not in st.session_state: st.session_state[size_key] = 16
    if image_key not in st.session_state: st.session_state[image_key] = None
    if marker_key not in st.session_state: st.session_state[marker_key] = None
    if bounds_key not in st.session_state: st.session_state[bounds_key] = None
    
    if dragged_key in st.session_state:
        st.session_state[coord_key] = st.session_state[dragged_key]
        del st.session_state[dragged_key]

    # --- FLAT SLICK HORIZONTAL CONTROLS MATRIX WITH TOP LABELS ---
    c_btn, c_style, c_color, c_size, c_coord = st.columns([1.6, 2.0, 0.8, 1.2, 3.4])
    
    with c_btn:
        export_clicked = st.button("Confirm and Export", type="primary", key=f"export_map_{token_key}", use_container_width=True)
        
    with c_style:
        basemap_style = st.selectbox(label="Basemap Layer", options=["Hybrid", "Satellite", "Carto Light", "OSM"], key=style_key)
        
    with c_color:
        # FIXED: Injected explicit label with standard margin overrides to align perfectly with its neighbors
        st.markdown('<div class="manual-picker-label">Pin Color</div>', unsafe_allow_html=True)
        pin_color = st.color_picker(label="Pin Color", key=color_key, label_visibility="collapsed")
        
    with c_size:
        pin_size = st.number_input(
            label="Pin Size", 
            min_value=16, 
            max_value=64, 
            step=2, 
            key=size_key
        )
        
    with c_coord:
        coord_input = st.text_input(label="Enter Coordinates", key=coord_key, placeholder="Lat, Lon")
    
    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)
    
    try:
        plat, plon = map(float, coord_input.split(","))
    except ValueError:
        plat, plon = 14.5995, 120.9842

    tiles_dict = {
        "OSM": "OpenStreetMap",
        "Carto Light": "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        "Satellite": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        "Hybrid": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}&apistyle=s.t%3A2%7Cp.v%3Aoff"
    }
    attr_dict = {"OSM": "OpenStreetMap", "Carto Light": "CartoDB", "Satellite": "Google Maps", "Hybrid": "Google Maps"}
    
    m = folium.Map(location=[plat, plon], zoom_start=15, tiles=tiles_dict[basemap_style], attr=attr_dict[basemap_style], zoom_control=True)
    
    icon_html = f"""
    <div style="position: relative; width: {pin_size}px; height: {pin_size}px;">
        <svg width="{pin_size}" height="{pin_size}" viewBox="0 0 40 40">
            <defs>
                <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                    <feDropShadow dx="0" dy="2" stdDeviation="2" flood-opacity="0.3"/>
                </filter>
            </defs>
            <g filter="url(#shadow)">
                <circle cx="20" cy="20" r="18" fill="{pin_color}" stroke="white" stroke-width="2"/>
                <polygon points="20,6 23.5,14.5 32,15 25.5,21 27.5,30 20,25 12.5,30 14.5,21 8,15 16.5,14.5" fill="white"/>
            </g>
        </svg>
    </div>
    """
    folium.Marker([plat, plon], draggable=True, icon=folium.DivIcon(html=icon_html)).add_to(m)
    Draw(export=False, position='topleft', draw_options={'polyline':False, 'polygon':False, 'circle':False, 'marker':False, 'circlemarker':False, 'rectangle':True}, edit_options={'edit':True}).add_to(m)
    
    st.info("Use the Rectangle tool to frame your export area. Drag the pin to move it.")
    map_data = st_folium(m, height=600, width=1300, use_container_width=True, key=f"int_map_{token_key}", returned_objects=["last_active_drawing", "bounds", "last_marker_moved"])

    if isinstance(map_data, dict) and map_data.get("bounds"):
        st.session_state[bounds_key] = map_data["bounds"]

    if export_clicked:
        with st.spinner("Compiling map asset..."):
            n, s, e, w = None, None, None, None
            if st.session_state.get(bounds_key):
                b = st.session_state[bounds_key]
                if b and "_northEast" in b and "_southWest" in b:
                    n, s = b["_northEast"]["lat"], b["_southWest"]["lat"]
                    e, w = b["_northEast"]["lng"], b["_southWest"]["lng"]
            if n is None:
                n, s = plat + 0.005, plat - 0.005
                e, w = plon + 0.005, plon - 0.005
            
            map_img_bytes = generate_static_map_bounds(n, s, e, w, plat, plon, style=basemap_style, pin_color=pin_color, pin_size=pin_size)
            st.session_state[image_key] = map_img_bytes
            st.session_state[f"coord_{token_key}"] = f"{plat}, {plon}"
            
            if st.session_state.temp_form_data:
                st.session_state.temp_form_data[token_key] = f"{plat}, {plon}"
                temp_path = get_temp_config_path(st.session_state.saved_template_name)
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state.temp_form_data, f, indent=4)
                    
            st.session_state.restore_form_data = True
            st.session_state.active_map_editor_token = None
            st.success("Map attached successfully!")
            time.sleep(0.3)
            st.rerun()

    if isinstance(map_data, dict) and map_data.get("last_marker_moved"):
        moved = map_data["last_marker_moved"]
        if moved:
            new_coord = f"{round(moved['lat'], 5)}, {round(moved['lng'], 5)}"
            if new_coord != st.session_state.get(coord_key, ""):
                st.session_state[dragged_key] = new_coord
                st.rerun()
                
# --- CORE UTILITIES ---
def smart_crop_to_fit(img_file, target_w_emu, target_h_emu):
    try:
        img = Image.open(img_file)
        img_w, img_h = img.size
        target_ratio = target_w_emu / target_h_emu
        if img_w / img_h > target_ratio:
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
    tokens, seen = [], set()
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for token in re.findall(r'\{\{.*?\}\}', shape.text):
                    if token not in seen: tokens.append(token); seen.add(token)
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        for token in re.findall(r'\{\{.*?\}\}', cell.text):
                            if token not in seen: tokens.append(token); seen.add(token)
    return tokens

def extract_placeholders_from_docx(docx_bytes):
    doc = Document(io.BytesIO(docx_bytes))
    tokens, seen = [], set()
    for paragraph in doc.paragraphs:
        for token in re.findall(r'\{\{.*?\}\}', paragraph.text):
            if token not in seen: tokens.append(token); seen.add(token)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for token in re.findall(r'\{\{.*?\}\}', cell.text):
                    if token not in seen: tokens.append(token); seen.add(token)
    return tokens

def extract_placeholders(template_bytes, template_type):
    if template_type == 'pptx': return extract_placeholders_from_pptx(template_bytes)
    if template_type == 'docx': return extract_placeholders_from_docx(template_bytes)
    return []

def replace_text_in_paragraph(paragraph, text_inputs):
    for run in paragraph.runs:
        for token, value in text_inputs.items():
            if token in run.text:
                run.text = run.text.replace(token, str(value) if value is not None else '')
    if hasattr(paragraph, 'text') and paragraph.text:
        for token, value in text_inputs.items():
            if token in paragraph.text:
                if not paragraph.runs: paragraph.add_run()
                for run in paragraph.runs:
                    if token in run.text:
                        run.text = run.text.replace(token, str(value) if value is not None else '')

def generate_pptx_bytes(template_bytes, text_inputs, image_inputs):
    prs = Presentation(io.BytesIO(template_bytes))
    for slide in prs.slides:
        shapes_to_delete, images_to_add = [], []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for img_token, img_file in image_inputs.items():
                    if img_token in shape.text and img_file is not None:
                        images_to_add.append((img_file, shape.left, shape.top, shape.width, shape.height))
                        shapes_to_delete.append(shape)
                        break
        for shape in slide.shapes:
            if shape not in shapes_to_delete:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs: replace_text_in_paragraph(paragraph, text_inputs)
                if hasattr(shape, 'table') and shape.table:
                    for row in shape.table.rows:
                        for cell in row.cells:
                            if cell.text_frame:
                                for paragraph in cell.text_frame.paragraphs: replace_text_in_paragraph(paragraph, text_inputs)
        for img_file, left, top, width, height in images_to_add:
            try:
                slide.shapes.add_picture(smart_crop_to_fit(img_file, width, height), left, top, width=width, height=height)
            except Exception: pass
        for old_shape in shapes_to_delete:
            try:
                sp = old_shape._element
                sp.getparent().remove(sp)
            except Exception: pass
    pptx_stream = io.BytesIO()
    prs.save(pptx_stream)
    return pptx_stream.getvalue()

def generate_docx_bytes(template_bytes, text_inputs, image_inputs):
    doc = Document(io.BytesIO(template_bytes))
    for paragraph in doc.paragraphs:
        if not any(img_token in paragraph.text for img_token in image_inputs.keys()):
            replace_text_in_paragraph(paragraph, text_inputs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs: replace_text_in_paragraph(paragraph, text_inputs)
    doc_stream = io.BytesIO()
    doc.save(doc_stream)
    return doc_stream.getvalue()

def get_download_filename(template_name, file_type):
    base_name = re.sub(r'\.(pptx|docx)$', '', template_name or "Document")
    base_name = re.sub(r'[^\w\-_. ]', '_', base_name)
    return f"{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_type}"

# --- FORM DATA LIVE PERSISTENCE ---
def save_form_data_to_session():
    if st.session_state.saved_template_name and st.session_state.tokens:
        form_data = {}
        for token in st.session_state.tokens:
            key = f"val_{token}"
            current_type = st.session_state.custom_mapping.get(token, "Text")
            
            # File uploaders shouldn't have raw bytes serialized to the config file
            if current_type == "Image":
                continue
                
            if key in st.session_state:
                form_data[token] = st.session_state[key]
                
        st.session_state.temp_form_data = form_data
        
        # Flush directly to localized temp file configuration automatically on input changes
        temp_path = get_temp_config_path(st.session_state.saved_template_name)
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(form_data, f, indent=4)

def restore_form_data_from_session():
    # Attempt to read cached entries from disk if memory baseline is currently uninitialized
    if not st.session_state.temp_form_data and st.session_state.saved_template_name:
        temp_path = get_temp_config_path(st.session_state.saved_template_name)
        if os.path.exists(temp_path):
            try:
                with open(temp_path, 'r', encoding='utf-8') as f:
                    st.session_state.temp_form_data = json.load(f)
            except Exception: pass

    if st.session_state.temp_form_data:
        for token, value in st.session_state.temp_form_data.items():
            current_type = st.session_state.custom_mapping.get(token, "Text")
            
            # CRITICAL FIX: Skip injecting values into st.session_state for widgets where it's not allowed
            if current_type == "Image":
                continue
                
            st.session_state[f"val_{token}"] = value
        return True
    return False

def purge_all_temporary_data():
    """Triggered post-download loop completion to cleanly wipe runtime configuration files."""
    if st.session_state.saved_template_name:
        temp_path = get_temp_config_path(st.session_state.saved_template_name)
        if os.path.exists(temp_path):
            try: os.remove(temp_path)
            except Exception: pass
            
    # Wipe references out of live session runtime memory blocks
    if st.session_state.tokens:
        for token in st.session_state.tokens:
            if f"val_{token}" in st.session_state: del st.session_state[f"val_{token}"]
            if f"map_bytes_holder_{token}" in st.session_state: del st.session_state[f"map_bytes_holder_{token}"]
            
    st.session_state.temp_form_data = {}

# --- INIT APP ---
st.set_page_config(page_title="OpenFlux", layout="wide", initial_sidebar_state="collapsed")
st.markdown(MINIMAL_CRE_SYSTEM, unsafe_allow_html=True)

if "active_map_editor_token" not in st.session_state: st.session_state.active_map_editor_token = None
if "custom_mapping" not in st.session_state: st.session_state.custom_mapping = {}
if "tokens" not in st.session_state: st.session_state.tokens = []
if "template_bytes" not in st.session_state: st.session_state.template_bytes = None
if "saved_template_name" not in st.session_state: st.session_state.saved_template_name = None
if "template_loaded" not in st.session_state: st.session_state.template_loaded = False
if "template_type" not in st.session_state: st.session_state.template_type = None
if "show_delete_confirm" not in st.session_state: st.session_state.show_delete_confirm = False
if "template_to_delete" not in st.session_state: st.session_state.template_to_delete = None
if "save_success" not in st.session_state: st.session_state.save_success = False
if "saved_file_name" not in st.session_state: st.session_state.saved_file_name = None
if "clear_uploader" not in st.session_state: st.session_state.clear_uploader = False
if "restore_form_data" not in st.session_state: st.session_state.restore_form_data = False
if "show_type_mapping" not in st.session_state: st.session_state.show_type_mapping = False
if "temp_form_data" not in st.session_state: st.session_state.temp_form_data = {}

# --- APP ROUTER ---
if st.session_state.active_map_editor_token:
    render_isolated_map_editor()
else:
    if st.session_state.restore_form_data:
        restore_form_data_from_session()
        st.session_state.restore_form_data = False
        
    st.markdown("<hr style='margin: 4px 0 12px 0;'>", unsafe_allow_html=True)
    st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Template Setup</div>', unsafe_allow_html=True)

    col_template1, col_template2 = st.columns(2)
    with col_template1:
        saved_templates = get_saved_templates()
        template_options = ["Select saved template"]
        github_templates = [t for t in saved_templates if t['source'] == 'github']
        stored_templates = [t for t in saved_templates if t['source'] == 'stored']
        
        if github_templates:
            template_options.append("--- GitHub Templates ---")
            for t in github_templates: template_options.append(f"{t['display_name']} ({t['type']})")
        if stored_templates:
            template_options.append("--- Stored Templates ---")
            for t in stored_templates: template_options.append(f"{t['display_name']} ({t['type']})")
        
        dropdown_col, delete_col = st.columns([4, 1])
        with dropdown_col:
            selected_template = st.selectbox("Load Template", template_options, key="saved_template_select", label_visibility="collapsed")
        with delete_col:
            if selected_template and selected_template != "Select saved template" and not selected_template.startswith("---"):
                template_display = selected_template.split(' (')[0].strip()
                for t in saved_templates:
                    if t['display_name'] == template_display:
                        if t['source'] == 'stored' and st.button("Delete", key="delete_template"):
                            st.session_state.show_delete_confirm = True
                            st.session_state.template_to_delete = t['name']
                            st.rerun()
                        break
                        
        if st.session_state.show_delete_confirm:
            st.warning(f"Are you sure you want to delete '{st.session_state.template_to_delete}'?")
            col_confirm1, col_confirm2 = st.columns(2)
            with col_confirm1:
                if st.button("Yes, Delete", key="confirm_delete"):
                    if delete_template_file(st.session_state.template_to_delete):
                        st.session_state.template_bytes = None
                        st.session_state.saved_template_name = None
                        st.session_state.template_loaded = False
                        st.session_state.tokens = []
                        st.session_state.temp_form_data = {}
                        st.session_state.show_delete_confirm = False
                        st.session_state.template_to_delete = None
                        st.rerun()
            with col_confirm2:
                if st.button("Cancel", key="cancel_delete"):
                    st.session_state.show_delete_confirm = False
                    st.session_state.template_to_delete = None
                    st.rerun()
                    
        if selected_template and selected_template != "Select saved template" and not selected_template.startswith("---"):
            template_display = selected_template.split(' (')[0].strip()
            for t in saved_templates:
                if t['display_name'] == template_display:
                    template_name = t['name']
                    template_bytes = load_template_from_file(template_name)
                    if template_bytes:
                        if st.session_state.saved_template_name != template_name:
                            st.session_state.temp_form_data = {}
                        st.session_state.template_bytes = template_bytes
                        st.session_state.saved_template_name = template_name
                        st.session_state.template_loaded = True
                        st.session_state.template_type = 'pptx' if template_name.endswith('.pptx') else 'docx'
                        config_data = load_config_from_file(template_name.replace('.pptx', '').replace('.docx', '') + '_config.json')
                        if config_data: st.session_state.custom_mapping = config_data
                        st.session_state.tokens = extract_placeholders(template_bytes, st.session_state.template_type)
                        restore_form_data_from_session()
                    break

    with col_template2:
        uploader_key = "new_template_upload_clear" if st.session_state.clear_uploader else "new_template_upload"
        uploaded_template = st.file_uploader("Upload New Template", type=["pptx", "docx"], label_visibility="collapsed", key=uploader_key)
        if st.session_state.clear_uploader: st.session_state.clear_uploader = False
        
        if uploaded_template:
            template_bytes = uploaded_template.getvalue()
            st.session_state.template_bytes = template_bytes
            st.session_state.saved_template_name = uploaded_template.name
            st.session_state.template_loaded = True
            st.session_state.template_type = 'pptx' if uploaded_template.name.endswith('.pptx') else 'docx'
            st.session_state.tokens = extract_placeholders(template_bytes, st.session_state.template_type)
            st.session_state.temp_form_data = {}
            
            if st.button("Save Template", key="save_template_btn", use_container_width=True):
                save_template_to_file(template_bytes, uploaded_template.name)
                if st.session_state.custom_mapping:
                    save_config_to_file(st.session_state.custom_mapping, uploaded_template.name.replace('.pptx', '').replace('.docx', '') + '_config.json')
                st.session_state.save_success = True
                st.session_state.saved_file_name = uploaded_template.name
                st.session_state.clear_uploader = True
                st.rerun()

    if st.session_state.save_success:
        st.success(f"Template '{st.session_state.saved_file_name}' saved successfully!")
        st.session_state.save_success = False

    if st.session_state.template_bytes is not None:
        template_name = st.session_state.saved_template_name or "Unsaved Template"
        is_github = os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), template_name))
        st.markdown(f'<div class="saved-indicator">Active: {template_name}{" (GitHub)" if is_github else " (Stored)"} ({st.session_state.template_type.upper()})</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    text_data, image_data, field_types = {}, {}, {}

    if st.session_state.template_bytes is not None and st.session_state.tokens:
        tokens = st.session_state.tokens
        st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
        
        with st.expander("Data Type Mapping", expanded=st.session_state.show_type_mapping):
            st.markdown("Configure the data type for each placeholder field.")
            cols = st.columns(3)
            for idx, token in enumerate(tokens):
                with cols[idx % 3]:
                    clean_label = token.replace("{", "").replace("}", "")
                    current_type = st.session_state.custom_mapping.get(token, "Text")
                    c_lbl, c_sel = st.columns([1, 1.5])
                    with c_lbl: st.markdown(f'<span style="font-size:12px; font-weight:500;">{clean_label}</span>', unsafe_allow_html=True)
                    with c_sel:
                        data_type = st.selectbox("", ["Text", "Image", "Map"], index=["Text", "Image", "Map"].index(current_type) if current_type in ["Text", "Image", "Map"] else 0, key=f"type_mapping_{token}", label_visibility="collapsed")
                        if data_type != current_type:
                            st.session_state.custom_mapping[token] = data_type
                            auto_save_config()
                            st.rerun()
        
        st.markdown('<div class="section-header">Placeholder Values</div>', unsafe_allow_html=True)
        
        # --- ROBUST 2-COLUMN INPUT FIELDS LAYOUT ---
        for idx, token in enumerate(tokens):
            # Alternate fields between two dynamic UI columns to ensure layout stability without squishing
            col_target = idx % 2
            if col_target == 0:
                ui_col_1, ui_col_2 = st.columns(2)
                current_block_column = ui_col_1
            else:
                current_block_column = ui_col_2
                
            with current_block_column:
                clean_label = token.replace("{", "").replace("}", "")
                current_type = st.session_state.custom_mapping.get(token, "Text")
                
                st.markdown(f'<div class="placeholder-label">{clean_label}</div>', unsafe_allow_html=True)
                
                if current_type == "Image" and st.session_state.template_type == 'pptx':
                    image_data[token] = st.file_uploader(clean_label, type=["png", "jpg", "jpeg"], key=f"val_{token}", label_visibility="collapsed")
                    field_types[token] = "Image"
                elif current_type == "Map" and st.session_state.template_type == 'pptx':
                    saved_map_img = st.session_state.get(f"map_bytes_holder_{token}")
                    if saved_map_img:
                        image_data[token] = saved_map_img
                        st.caption("Map attached.")
                    if st.button("Open Map Editor", key=f"btn_map_{token}", use_container_width=True):
                        save_form_data_to_session()
                        st.session_state.active_map_editor_token = token
                        st.rerun()
                    field_types[token] = "Image"
                else:
                    if current_type in ["Image", "Map"] and st.session_state.template_type != 'pptx':
                        st.warning("Images/Maps are only supported in PPTX files.")
                    
                    # Capture user typing interactions seamlessly using standard callback hooks
                    text_data[token] = st.text_input("", key=f"val_{token}", label_visibility="collapsed", placeholder="Enter value...", on_change=save_form_data_to_session)
                    field_types[token] = "Text"
                st.markdown('<div style="margin-bottom:14px;"></div>', unsafe_allow_html=True)
                
        st.markdown('</div>', unsafe_allow_html=True)

    # --- DOWNLOAD & CLEANUP SECTION ---
    if st.session_state.template_bytes is not None:
        st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Download Document</div>', unsafe_allow_html=True)
        
        base_template_name = re.sub(r'\.(pptx|docx)$', '', st.session_state.saved_template_name or "Generated_Document")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.template_type != 'pptx':
                st.button("Download PPTX", disabled=True, use_container_width=True)
            else:
                try:
                    pptx_data = generate_pptx_bytes(st.session_state.template_bytes, text_data, image_data)
                    st.download_button(
                        label="Download PPTX", data=pptx_data,
                        file_name=get_download_filename(base_template_name, "pptx"),
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True, key="download_pptx",
                        on_click=purge_all_temporary_data
                    )
                except Exception as e:
                    st.error(f"Error generating PPTX: {str(e)}")
                    
        with col2:
            if st.session_state.template_type != 'docx':
                st.button("Download DOCX", disabled=True, use_container_width=True)
            else:
                try:
                    docx_data = generate_docx_bytes(st.session_state.template_bytes, text_data, image_data)
                    st.download_button(
                        label="Download DOCX", data=docx_data,
                        file_name=get_download_filename(base_template_name, "docx"),
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True, key="download_docx",
                        on_click=purge_all_temporary_data
                    )
                except Exception as e:
                    st.error(f"Error generating document: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Please upload or select a template to begin")
