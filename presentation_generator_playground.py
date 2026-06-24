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
    
    .field-label { font-size: 13px !important; font-weight: 600 !important; color: #1A1A1A !important; padding-top: 6px; }
    .section-header { font-size: 15px !important; font-weight: 700 !important; color: #1A1A1A !important; margin-bottom: 10px; }
    .saved-indicator { background-color: #E8F5E9; padding: 6px 12px; border-radius: 4px; font-size: 13px; color: #2E7D32; border-left: 3px solid #2E7D32; margin-top: 6px; }
    hr { margin: 12px 0 !important; border-color: #E0E0E0 !important; }
    
    /* Clean up form container borders */
    div[data-testid="stForm"] { border: 1px solid #E0E0E0 !important; border-radius: 6px !important; padding: 1rem !important; background-color: #FFFFFF; }
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


# --- DYNAMIC ULTRA HIGH-RESOLUTION BOUNDING BOX GENERATOR ---
def generate_static_map_bounds(n, s, e, w, pin_lat, pin_lon, style="Hybrid", pin_color="#DC3545", pin_size=32):
    """Calculates deep zoom levels to generate crisp print-quality document assets and stamps the pin."""
    target_width_tiles = 10
    lon_span = e - w
    if lon_span <= 0: lon_span = 0.001
    
    zoom = int(math.log2((360.0 / lon_span) * target_width_tiles))
    zoom = max(12, min(20, zoom)) 
    
    def deg2num(lat_deg, lon_deg, z):
        lat_rad = math.radians(lat_deg)
        n_tiles = 2.0 ** z
        xtile = int((lon_deg + 180.0) / 360.0 * n_tiles)
        ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n_tiles)
        return (xtile, ytile)
        
    x_min, y_min = deg2num(n, w, zoom)
    x_max, y_max = deg2num(s, e, zoom)
    
    if (x_max - x_min + 1) * (y_max - y_min + 1) > 150:
        zoom -= 1
        x_min, y_min = deg2num(n, w, zoom)
        x_max, y_max = deg2num(s, e, zoom)
        
    width_tiles = x_max - x_min + 1
    height_tiles = y_max - y_min + 1
    tile_size = 256
    
    stitched = Image.new('RGB', (width_tiles * tile_size, height_tiles * tile_size))
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
    
    cropped = stitched.crop((left, top, right, bottom)).convert("RGBA")
    
    # STAMP VECTOR PIN AT EXACT GEOSPATIAL PIXEL COORDINATES
    draw = ImageDraw.Draw(cropped)
    pin_px_x, pin_px_y = num2px(pin_lat, pin_lon, zoom)
    pin_local_x = int(pin_px_x - base_x) - left
    pin_local_y = int(pin_px_y - base_y) - top
    
    scale = (pin_size / 32.0) * 2.0
    w_px = 16 * scale
    h_px = 32 * scale
    
    draw.polygon([(pin_local_x, pin_local_y), (pin_local_x - w_px, pin_local_y - h_px), (pin_local_x + w_px, pin_local_y - h_px)], fill="#ffffff")
    draw.ellipse([pin_local_x - w_px, pin_local_y - h_px - w_px, pin_local_x + w_px, pin_local_y - h_px + w_px], fill="#ffffff")
    draw.polygon([(pin_local_x, pin_local_y - (4 * scale)), (pin_local_x - (w_px * 0.75), pin_local_y - h_px), (pin_local_x + (w_px * 0.75), pin_local_y - h_px)], fill=pin_color)
    draw.ellipse([pin_local_x - (w_px * 0.75), pin_local_y - h_px - (w_px * 0.75), pin_local_x + (w_px * 0.75), pin_local_y - h_px + (w_px * 0.75)], fill=pin_color)
    draw.ellipse([pin_local_x - (w_px * 0.33), pin_local_y - h_px - (w_px * 0.33), pin_local_x + (w_px * 0.33), pin_local_y - h_px + (w_px * 0.33)], fill="#ffffff")
    
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
        if st.button("Back to Document"):
            st.session_state.active_map_editor_token = None
            st.rerun()
    with col_title:
        st.markdown(f"### Full-Screen Map Editor: `{token_key}`")
    
    st.markdown("</div><br>", unsafe_allow_html=True)

    config_key = f"map_conf_{token_key}"
    if config_key not in st.session_state:
        st.session_state[config_key] = {
            "style": "Hybrid", "lat": 14.3294, "lon": 120.9368,
            "color": "#DC3545", "size": 32, "zoom": 15
        }
    conf = st.session_state[config_key]

    # Live Updating Configuration Bar (No forms, values reflect instantly on change)
    st.markdown("##### Pin & View Settings")
    c1, c2, c3, c4 = st.columns([1.5, 2, 1, 2])
    
    new_style = c1.selectbox("Map Layer", ["Hybrid", "Satellite", "Carto Light", "OSM"], index=["Hybrid", "Satellite", "Carto Light", "OSM"].index(conf["style"]), label_visibility="collapsed")
    new_coord = c2.text_input("Coordinates (Lat, Lon)", f"{conf['lat']}, {conf['lon']}", label_visibility="collapsed", help="Coordinate Format: Lat, Lon")
    new_color = c3.color_picker("Pin Color", conf["color"], label_visibility="collapsed")
    new_size = c4.slider("Pin Size", 16, 64, conf["size"], label_visibility="collapsed")
    
    # Commit changes dynamically directly to memory
    conf["style"] = new_style
    conf["color"] = new_color
    conf["size"] = new_size
    try:
        plat, plon = map(float, new_coord.split(","))
        conf["lat"] = plat
        conf["lon"] = plon
    except Exception:
        pass
        
    st.session_state[config_key] = conf

    # RENDER MAP CORE
    tiles_dict = {
        "OSM": "OpenStreetMap",
        "Carto Light": "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        "Satellite": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        "Hybrid": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}&apistyle=s.t%3A2%7Cp.v%3Aoff"
    }
    attr_dict = {
        "OSM": "OpenStreetMap",
        "Carto Light": "&copy; CartoDB",
        "Satellite": "Google Maps",
        "Hybrid": "Google Maps (Clean Streets)"
    }
    
    m = folium.Map(
        location=[conf["lat"], conf["lon"]], 
        zoom_start=conf["zoom"],
        tiles=tiles_dict[conf["style"]],
        attr=attr_dict[conf["style"]],
        zoom_control=True
    )

    icon_html = f"""
    <div style="position: relative;">
        <span style="position: absolute; left: -{conf["size"]//2}px; top: -{conf["size"]}px; width: {conf["size"]}px; height: {conf["size"]}px; background-color: {conf["color"]}; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.4);"></span>
        <span style="position: absolute; left: -{max(2, int(conf["size"]/6))}px; top: -{int(conf["size"] * 0.66)}px; width: {max(4, int(conf["size"]/3))}px; height: {max(4, int(conf["size"]/3))}px; background-color: white; border-radius: 50%;"></span>
    </div>
    """
    
    folium.Marker([conf["lat"], conf["lon"]], draggable=True, icon=folium.DivIcon(html=icon_html)).add_to(m)
    
    draw = Draw(
        export=False, position='topleft',
        draw_options={'polyline':False, 'polygon':False, 'circle':False, 'marker':False, 'circlemarker':False, 'rectangle':True},
        edit_options={'edit':True}
    )
    draw.add_to(m)
    
    st.info("Use the Rectangle tool to frame your export area. Drag the pin to move it. Size and Color changes apply immediately.")
    
    map_data = st_folium(
        m, height=600, width=1300, use_container_width=True, key=f"int_map_{token_key}",
        returned_objects=["last_active_drawing", "bounds", "last_marker_moved"]
    )

    # Sync dragging the marker back to the text input
    if isinstance(map_data, dict) and map_data.get("last_marker_moved"):
        moved = map_data["last_marker_moved"]
        mlat, mlon = round(moved["lat"], 5), round(moved["lng"], 5)
        if mlat != conf["lat"] or mlon != conf["lon"]:
            conf["lat"] = mlat
            conf["lon"] = mlon
            st.session_state[config_key] = conf
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    
    # FINAL HIGH RES EXPORT TRIGGER
    if st.button("Confirm & Export High-Res Image to Document", type="primary", use_container_width=True):
        with st.spinner("Compiling Crisp High-Density API Asset. This takes approximately 3 seconds..."):
            
            export_lat, export_lon = conf["lat"], conf["lon"]
            if isinstance(map_data, dict) and map_data.get("last_marker_moved"):
                export_lat = map_data["last_marker_moved"]["lat"]
                export_lon = map_data["last_marker_moved"]["lng"]

            # Intercept Bounding Box
            n, s, e, w = None, None, None, None
            if isinstance(map_data, dict) and map_data.get("last_active_drawing"):
                drawing = map_data["last_active_drawing"]
                if drawing and drawing["geometry"]["type"] == "Polygon":
                    coords = drawing["geometry"]["coordinates"][0]
                    lats = [c[1] for c in coords]
                    lons = [c[0] for c in coords]
                    n, s = max(lats), min(lats)
                    e, w = max(lons), min(lons)
            
            if n is None and isinstance(map_data, dict) and map_data.get("bounds"):
                b = map_data["bounds"]
                n, s = b["_northEast"]["lat"], b["_southWest"]["lat"]
                e, w = b["_northEast"]["lng"], b["_southWest"]["lng"]
            
            if n is None:
                n, s, e, w = export_lat + 0.01, export_lat - 0.01, export_lon + 0.01, export_lon - 0.01

            map_img_bytes = generate_static_map_bounds(
                n, s, e, w, export_lat, export_lon, 
                style=conf["style"], pin_color=conf["color"], pin_size=conf["size"]
            )
            
            st.session_state[f"map_bytes_holder_{token_key}"] = map_img_bytes
            
            # Save final state
            conf["lat"] = export_lat
            conf["lon"] = export_lon
            st.session_state[config_key] = conf
            
            # Auto-Return to main app
            st.session_state.active_map_editor_token = None
            st.success("High-res map rendering attached successfully! Returning to document...")
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
        img.save(img_byte_arr, format='PNG')
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

if "active_map_editor_token" not in st.session_state: st.session_state.active_map_editor_token = None
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


# --- ISOLATED APP ROUTER ---
if st.session_state.active_map_editor_token:
    render_isolated_map_editor()
else:
    # --- MAIN DOCUMENT GENERATOR APP ---
    st.markdown("<hr style='margin: 4px 0 12px 0;'>", unsafe_allow_html=True)
    
    st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Template Setup</div>', unsafe_allow_html=True)

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
                                
                                saved_map_img = st.session_state.get(f"map_bytes_holder_{token}")
                                if saved_map_img:
                                    image_data[token] = saved_map_img
                                    st.caption("Map snapshot attached.")
                                
                                if st.button(f"Open Map Editor", key=f"btn_map_{token}", use_container_width=True):
                                    st.session_state.active_map_editor_token = token
                                    st.rerun()
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
