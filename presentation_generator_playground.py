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
    
    .field-label { font-size: 13px !important; font-weight: 600 !important; color: #1A1A1A !important; padding-top: 2px; margin-bottom: 2px; }
    .section-header { font-size: 15px !important; font-weight: 700 !important; color: #1A1A1A !important; margin-bottom: 10px; }
    .saved-indicator { background-color: #E8F5E9; padding: 6px 12px; border-radius: 4px; font-size: 13px; color: #2E7D32; border-left: 3px solid #2E7D32; margin-top: 6px; }
    hr { margin: 12px 0 !important; border-color: #E0E0E0 !important; }
    
    div[data-testid="stForm"] { border: 1px solid #E0E0E0 !important; border-radius: 6px !important; padding: 1rem !important; background-color: #FFFFFF; }
    
    /* Strict CSS layout override matching dropdown sizes side-by-side on mobile screen dimensions */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: flex-end !important;
        gap: 8px !important;
    }
    div[data-testid="stHorizontalBlock"] > div {
        min-width: 0 !important;
    }
    /* Set column percentage widths forcefully */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) {
        flex: 3 1 0% !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
        flex: 1 1 0% !important;
        min-width: 95px !important;
        max-width: 120px !important;
    }
</style>
"""

# --- FILE MANAGEMENT FUNCTIONS ---
def get_storage_dir():
    storage_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stored_templates")
    os.makedirs(storage_dir, exist_ok=True)
    return storage_dir

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
    root_filepath = os.path.join(root_dir, template_name)
    if os.path.exists(root_filepath):
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


# --- FIXED HIGH-RESOLUTION CLOSE-ZOOM BOUNDING BOX GENERATOR ---
def generate_static_map_bounds(n, s, e, w, pin_lat, pin_lon, style="Hybrid", pin_color="#DC3545", pin_size=32):
    """Generates high-res structured map map snapshot locked tight to structural target coords"""
    # Overriding standard map span dimensions to guarantee a macro, high-detail view of property asset site
    zoom = 18  # Hard fixed closer detail factor to prevent far zoomed out looks
    
    def deg2num(lat_deg, lon_deg, z):
        lat_rad = math.radians(lat_deg)
        n_tiles = 2.0 ** z
        xtile = int((lon_deg + 180.0) / 360.0 * n_tiles)
        ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n_tiles)
        return (xtile, ytile)
        
    # Capture bounding coordinate arrays around the specific explicit marker target pin position instead of map canvas edges
    center_x, center_y = deg2num(pin_lat, pin_lon, zoom)
    
    # Grab structural 5x5 tile configuration framework grid directly around central location node
    radius_tiles = 2 
    x_min, x_max = center_x - radius_tiles, center_x + radius_tiles
    y_min, y_max = center_y - radius_tiles, center_y + radius_tiles
        
    width_tiles = x_max - x_min + 1
    height_tiles = y_max - y_min + 1
    tile_size = 256
    scale_factor = 2  # Double grid resolution compilation structure logic
    
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
        
    base_x = x_min * tile_size * scale_factor
    base_y = y_min * tile_size * scale_factor
    
    pin_px_x, pin_px_y = num2px(pin_lat, pin_lon, zoom)
    pin_local_x = int(pin_px_x - base_x)
    pin_local_y = int(pin_px_y - base_y)
    
    # Executing tighter square dynamic cropping boundaries around center pin vector map layer
    crop_w, crop_h = 750 * scale_factor, 500 * scale_factor
    left = max(0, pin_local_x - (crop_w // 2))
    top = max(0, pin_local_y - (crop_h // 2))
    right = min(stitched.width, left + crop_w)
    bottom = min(stitched.height, top + crop_h)
    
    cropped = stitched.crop((left, top, right, bottom)).convert("RGBA")
    draw = ImageDraw.Draw(cropped)
    
    # Re-calculate tracking coordinate metrics within newly transformed cropped context space bounds
    pin_dest_x = pin_local_x - left
    pin_dest_y = pin_local_y - top
    
    scale = max(1.5, (pin_size / 32.0) * scale_factor * 1.5)
    radius = int(16 * scale)
    
    # Shadow layer elements
    shadow_offset = int(2 * scale)
    draw.ellipse([pin_dest_x - radius - shadow_offset, pin_dest_y - radius - shadow_offset,
                  pin_dest_x + radius + shadow_offset, pin_dest_y + radius + shadow_offset], fill=(0, 0, 0, 60))
    
    # Core pinpoint structural badge graphics
    draw.ellipse([pin_dest_x - radius, pin_dest_y - radius, pin_dest_x + radius, pin_dest_y + radius], 
                 fill=pin_color, outline=(255, 255, 255), width=int(2.5 * scale))
    
    star_size = int(radius * 0.55)
    star_points = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        r = star_size if i % 2 == 0 else star_size * 0.4
        star_points.append((pin_dest_x + r * math.cos(angle), pin_dest_y + r * math.sin(angle)))
    
    draw.polygon(star_points, fill=(255, 255, 255))
    
    final_img = cropped.convert("RGB")
    img_byte_arr = io.BytesIO()
    final_img.save(img_byte_arr, format='PNG', quality=100)
    img_byte_arr.seek(0)
    return img_byte_arr

# --- ISOLATED FULL-SCREEN MAP EDITOR PAGE ---
def render_isolated_map_editor():
    token_key = st.session_state.active_map_editor_token
    
    st.markdown('<div class="editor-card">', unsafe_allow_html=True)
    col_back, col_title = st.columns([1, 4])
    with col_back:
        if st.button("← Back to Document", key="back_from_map"):
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
    bounds_key = f"map_bounds_{token_key}"
    
    if style_key not in st.session_state: st.session_state[style_key] = "Hybrid"
    if coord_key not in st.session_state: st.session_state[coord_key] = "14.5995, 120.9842"
    if color_key not in st.session_state: st.session_state[color_key] = "#003366"
    if size_key not in st.session_state: st.session_state[size_key] = 32
    
    if dragged_key in st.session_state:
        st.session_state[coord_key] = st.session_state[dragged_key]
        del st.session_state[dragged_key]

    c1, c2, c3, c4 = st.columns([1.5, 2, 1, 2])
    basemap_style = c1.selectbox("Map Layer", ["Hybrid", "Satellite", "Carto Light", "OSM"], key=style_key)
    coord_input = c2.text_input("Coordinates (Lat, Lon)", key=coord_key)
    pin_color = c3.color_picker("Pin Color", key=color_key)
    pin_size = c4.slider("Pin Size", 16, 64, key=size_key)

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
    attr_dict = {
        "OSM": "OpenStreetMap", "Carto Light": "CartoDB", "Satellite": "Google Maps", "Hybrid": "Google Maps"
    }
    
    m = folium.Map(location=[plat, plon], zoom_start=17, tiles=tiles_dict[basemap_style], attr=attr_dict[basemap_style])

    icon_html = f"""
    <div style="position: relative; width: {pin_size}px; height: {pin_size}px;">
        <svg width="{pin_size}" height="{pin_size}" viewBox="0 0 40 40">
            <circle cx="20" cy="20" r="18" fill="{pin_color}" stroke="white" stroke-width="2"/>
            <polygon points="20,6 23.5,14.5 32,15 25.5,21 27.5,30 20,25 12.5,30 14.5,21 8,15 16.5,14.5" fill="white"/>
        </svg>
    </div>
    """
    
    folium.Marker([plat, plon], draggable=True, icon=folium.DivIcon(html=icon_html)).add_to(m)
    Draw(export=False, position='topleft', draw_options={'polyline':False, 'polygon':False, 'circle':False, 'marker':False, 'circlemarker':False, 'rectangle':True}).add_to(m)
    
    map_data = st_folium(m, height=500, width=1300, use_container_width=True, key=f"int_map_{token_key}", returned_objects=["bounds", "last_marker_moved"])

    if isinstance(map_data, dict) and map_data.get("bounds"):
        st.session_state[bounds_key] = map_data["bounds"]

    if st.button("Confirm and Export High-Res Image to Document", type="primary", use_container_width=True):
        export_lat, export_lon = plat, plon
        if isinstance(map_data, dict) and map_data.get("last_marker_moved"):
            moved = map_data["last_marker_moved"]
            if moved:
                export_lat, export_lon = moved["lat"], moved["lng"]

        n, s, e, w = export_lat + 0.002, export_lat - 0.002, export_lon + 0.002, export_lon - 0.002
        
        map_img_bytes = generate_static_map_bounds(n, s, e, w, export_lat, export_lon, style=basemap_style, pin_color=pin_color, pin_size=pin_size)
        
        st.session_state[image_key] = map_img_bytes
        # Map output content into standard form fields directly to shield against UI refreshes
        st.session_state[f"form_val_{token_key}"] = map_img_bytes
        st.session_state[coord_key] = f"{export_lat}, {export_lon}"
        st.session_state.active_map_editor_token = None
        st.success("High-res closed-zoom map view pinned successfully!")
        time.sleep(0.4)
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
                        tokens.append(token); seen.add(token)
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        found = re.findall(r'\{\{.*?\}\}', cell.text)
                        for token in found:
                            if token not in seen:
                                tokens.append(token); seen.add(token)
    return tokens

def extract_placeholders_from_docx(docx_bytes):
    doc = Document(io.BytesIO(docx_bytes))
    tokens = []
    seen = set()
    for paragraph in doc.paragraphs:
        found = re.findall(r'\{\{.*?\}\}', paragraph.text)
        for token in found:
            if token not in seen: tokens.append(token); seen.add(token)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                found = re.findall(r'\{\{.*?\}\}', cell.text)
                for token in found:
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
                run.text = run.text.replace(token, str(value) if value else '')
    if hasattr(paragraph, 'text') and paragraph.text:
        for token, value in text_inputs.items():
            if token in paragraph.text:
                if not paragraph.runs: paragraph.add_run()
                for run in paragraph.runs:
                    if token in run.text:
                        run.text = run.text.replace(token, str(value) if value else '')

def generate_pptx_bytes(template_bytes, text_inputs, image_inputs):
    prs = Presentation(io.BytesIO(template_bytes))
    for slide in prs.slides:
        shapes_to_delete = []; images_to_add = []
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
                    for paragraph in shape.text_frame.paragraphs: replace_text_in_paragraph(paragraph, text_inputs)
                if hasattr(shape, 'table') and shape.table:
                    for row in shape.table.rows:
                        for cell in row.cells:
                            if cell.text_frame:
                                for paragraph in cell.text_frame.paragraphs: replace_text_in_paragraph(paragraph, text_inputs)
        for img_file, left, top, width, height in images_to_add:
            try:
                processed_img = smart_crop_to_fit(img_file, width, height)
                slide.shapes.add_picture(processed_img, left, top, width=width, height=height)
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
        has_image = any(img_token in paragraph.text for img_token in image_inputs.keys())
        if not has_image: replace_text_in_paragraph(paragraph, text_inputs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs: replace_text_in_paragraph(paragraph, text_inputs)
    doc_stream = io.BytesIO()
    doc.save(doc_stream)
    return doc_stream.getvalue()

def get_download_filename(template_name, file_type):
    base_name = re.sub(r'\.(pptx|docx)$', '', template_name or "Generated_Document")
    base_name = re.sub(r'[^\w\-_. ]', '_', base_name)
    return f"{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_type}"

# --- INIT APP ---
st.set_page_config(page_title="OpenFlux", layout="wide", initial_sidebar_state="collapsed")
st.markdown(MINIMAL_CRE_SYSTEM, unsafe_allow_html=True)

# System-level routing properties definitions
states = ["active_map_editor_token", "custom_mapping", "tokens", "template_bytes", "saved_template_name", 
          "template_loaded", "template_type", "show_delete_confirm", "save_success", "clear_uploader"]
for state in states:
    if state not in st.session_state:
        st.session_state[state] = {} if "mapping" in state else ([] if "tokens" in state else None if "bytes" in state or "name" in state or "token" in state else False)

# --- APP ROUTER ---
if st.session_state.active_map_editor_token:
    render_isolated_map_editor()
else:
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
            template_options.append("--- Templates ---")
            for t in github_templates: template_options.append(f"{t['display_name']} ({t['type']})")
        if stored_templates:
            template_options.append("--- User Uploaded Templates ---")
            for t in stored_templates: template_options.append(f"{t['display_name']} ({t['type']})")
        
        dropdown_col, delete_col = st.columns([4, 1])
        with dropdown_col:
            selected_template = st.selectbox("Load Template", template_options, key="saved_template_select", label_visibility="collapsed")
        with delete_col:
            if selected_template and selected_template != "Select saved template" and not selected_template.startswith("---"):
                template_display = selected_template.split(' (')[0].strip()
                for t in saved_templates:
                    if t['display_name'] == template_display and t['source'] == 'stored':
                        if st.button("🗑️", key="delete_template"):
                            st.session_state.show_delete_confirm = True
                            st.session_state.template_to_delete = t['name']
                            st.rerun()
        
        if st.session_state.show_delete_confirm:
            st.warning(f"Are you sure you want to delete '{st.session_state.template_to_delete}'?")
            c_con1, c_con2 = st.columns(2)
            if c_con1.button("Yes, Delete"):
                if delete_template_file(st.session_state.template_to_delete):
                    st.session_state.template_bytes = None
                    st.session_state.tokens = []
                    st.session_state.show_delete_confirm = False
                    st.rerun()
            if c_con2.button("Cancel"):
                st.session_state.show_delete_confirm = False
                st.rerun()
                
        if selected_template and selected_template != "Select saved template" and not selected_template.startswith("---"):
            template_display = selected_template.split(' (')[0].strip()
            for t in saved_templates:
                if t['display_name'] == template_display:
                    template_bytes = load_template_from_file(t['name'])
                    if template_bytes and st.session_state.template_bytes != template_bytes:
                        st.session_state.template_bytes = template_bytes
                        st.session_state.saved_template_name = t['name']
                        st.session_state.template_type = 'pptx' if t['name'].endswith('.pptx') else 'docx'
                        st.session_state.tokens = extract_placeholders(template_bytes, st.session_state.template_type)
                        config_data = load_config_from_file(t['name'].replace('.pptx', '').replace('.docx', '') + '_config.json')
                        if config_data: st.session_state.custom_mapping = config_data
                    break

    with col_template2:
        uploader_key = "new_template_upload_clear" if st.session_state.clear_uploader else "new_template_upload"
        uploaded_template = st.file_uploader("Upload New Template", type=["pptx", "docx"], label_visibility="collapsed", key=uploader_key)
        
        if uploaded_template:
            template_bytes = uploaded_template.getvalue()
            st.session_state.template_bytes = template_bytes
            st.session_state.saved_template_name = None
            st.session_state.template_type = 'pptx' if uploaded_template.name.endswith('.pptx') else 'docx'
            st.session_state.tokens = extract_placeholders(template_bytes, st.session_state.template_type)
            
            if st.button("Save Template", use_container_width=True):
                save_template_to_file(template_bytes, uploaded_template.name)
                st.session_state.saved_template_name = uploaded_template.name
                if st.session_state.custom_mapping:
                    save_config_to_file(st.session_state.custom_mapping, uploaded_template.name.replace('.pptx', '').replace('.docx', '') + '_config.json')
                st.session_state.save_success = True
                st.session_state.clear_uploader = True
                st.rerun()

    if st.session_state.save_success:
        st.success("Template stored successfully!")
        st.session_state.save_success = False

    if st.session_state.template_bytes is not None:
        t_name = st.session_state.saved_template_name or "Unsaved Template"
        st.markdown(f'<div class="saved-indicator">Active: {t_name} ({st.session_state.template_type.upper()})</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    text_data = {}; image_data = {}

    if st.session_state.template_bytes is not None and st.session_state.tokens:
        st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Placeholder Values</div>', unsafe_allow_html=True)
        
        # Iterating placeholders matching flat-line structural row designs
        for token in st.session_state.tokens:
            clean_label = token.replace("{", "").replace("}", "")
            current_type = st.session_state.custom_mapping.get(token, "Text")
            
            # Form field layout row implementation blocks
            col_a, col_b = st.columns([3, 1])
            
            with col_a:
                st.markdown(f'<div class="field-label">{clean_label}</div>', unsafe_allow_html=True)
                form_key = f"form_val_{token}"
                
                if current_type == "Image" and st.session_state.template_type == 'pptx':
                    image_data[token] = st.file_uploader(clean_label, type=["png", "jpg", "jpeg"], key=form_key, label_visibility="collapsed")
                elif current_type == "Map" and st.session_state.template_type == 'pptx':
                    saved_map_img = st.session_state.get(f"map_bytes_holder_{token}")
                    if saved_map_img:
                        image_data[token] = saved_map_img
                        st.caption("✨ Dynamic high-density close-zoom map attached.")
                    
                    if st.button(f"Open Map Editor", key=f"btn_map_{token}", use_container_width=True):
                        st.session_state.active_map_editor_token = token
                        st.rerun()
                else:
                    # Text data handling utilizing standard persistent layout keys
                    if form_key not in st.session_state:
                        st.session_state[form_key] = ""
                    text_data[token] = st.text_input(clean_label, key=form_key, label_visibility="collapsed")
            
            with col_b:
                st.markdown('<div style="padding-top: 20px;"></div>', unsafe_allow_html=True)
                data_type = st.selectbox("Type", ["Text", "Image", "Map"], index=["Text", "Image", "Map"].index(current_type) if current_type in ["Text", "Image", "Map"] else 0, key=f"type_{token}", label_visibility="collapsed")
                if data_type != current_type:
                    st.session_state.custom_mapping[token] = data_type
                    auto_save_config()
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- DOWNLOAD SECTION ---
    if st.session_state.template_bytes is not None:
        st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Download Document</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.template_type != 'pptx':
                st.button("Download PPTX", disabled=True, use_container_width=True)
            else:
                try:
                    pptx_data = generate_pptx_bytes(st.session_state.template_bytes, text_data, image_data)
                    st.download_button(label="Download PPTX", data=pptx_data, file_name=get_download_filename(st.session_state.saved_template_name, "pptx"), mime="application/vnd.openxmlformats-officedocument.presentationml.presentation", use_container_width=True)
                except Exception as e: st.error(f"Error: {str(e)}")
                    
        with col2:
            if st.session_state.template_type != 'docx':
                st.button("Download DOCX", disabled=True, use_container_width=True)
            else:
                try:
                    docx_data = generate_docx_bytes(st.session_state.template_bytes, text_data, image_data)
                    st.download_button(label="Download DOCX", data=docx_data, file_name=get_download_filename(st.session_state.saved_template_name, "docx"), mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
                except Exception as e: st.error(f"Error: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Please upload or select a template to begin")
