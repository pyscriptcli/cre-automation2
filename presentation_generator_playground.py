import os
import io
import re
import json
import streamlit as st
from pptx import Presentation
from PIL import Image
from datetime import datetime
from docx import Document
import folium
from streamlit_folium import folium_static
import requests
import base64
import tempfile
import shutil

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
    svg[data-testid="stSelectbox"] { width: 16px !important; height: 16px !important; }
    div[data-baseweb="select"] svg { width: 16px !important; height: 16px !important; }
    
    section[data-testid="stFileUploader"] { background-color: #F8F8F8 !important; border: 1px solid #CCCCCC !important; border-radius: 4px !important; padding: 4px 12px !important; }
    
    .workspace-card { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 4px; padding: 16px; margin-bottom: 12px; }
    
    div.stButton > button { 
        background-color: #003366 !important; 
        color: #FFFFFF !important; 
        font-weight: 600 !important; 
        font-size: 11px !important; 
        border: none !important; 
        border-radius: 3px !important; 
        padding: 5px 12px !important; 
        width: 100% !important; 
        transition: background-color 0.15s ease; 
        min-height: 28px !important;
    }
    div.stButton > button:hover { 
        background-color: #002244 !important; 
        color: #FFFFFF !important; 
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 51, 102, 0.3);
    }
    div.stButton > button:disabled { 
        background-color: #6688AA !important; 
        color: #CCCCCC !important; 
        cursor: not-allowed !important; 
    }
    
    div[data-testid="stDownloadButton"] > button { 
        background-color: #003366 !important;
        color: #FFFFFF !important;
        border-radius: 3px !important; 
        font-weight: 600 !important; 
        padding: 5px 12px !important; 
        width: 100% !important; 
        transition: all 0.15s ease;
        font-size: 11px !important;
        min-height: 28px !important;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        background-color: #002244 !important;
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 51, 102, 0.3);
    }
    
    .field-label { font-size: 13px !important; font-weight: 600 !important; color: #1A1A1A !important; padding-top: 6px; }
    .section-header { font-size: 15px !important; font-weight: 700 !important; color: #1A1A1A !important; margin-bottom: 10px; }
    .saved-indicator { background-color: #E8F5E9; padding: 6px 12px; border-radius: 4px; font-size: 13px; color: #2E7D32; border-left: 3px solid #2E7D32; margin-top: 6px; }
    
    .map-container { 
        border: 1px solid #E0E0E0; 
        border-radius: 4px; 
        padding: 8px; 
        background-color: #F8F9FA;
        margin: 8px 0;
    }
    .map-saved-indicator {
        background-color: #E3F2FD;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 11px;
        color: #003366;
        border-left: 3px solid #003366;
        margin: 4px 0;
    }
    
    .cta-preview {
        background-color: #F8F9FA;
        padding: 8px 12px;
        border-radius: 4px;
        border-left: 3px solid #003366;
        font-size: 13px;
        margin: 4px 0;
        font-family: monospace;
    }
    .cta-preset-card {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 4px;
        padding: 8px 12px;
        margin-bottom: 6px;
    }
    .cta-preset-card .cta-name {
        font-weight: 700;
        color: #003366;
        font-size: 13px;
    }
    .cta-preset-card .cta-detail {
        font-size: 11px;
        color: #666;
    }
    
    hr { margin: 12px 0 !important; border-color: #E0E0E0 !important; }
</style>
"""

# --- FILE MANAGEMENT FUNCTIONS ---
def get_templates_from_root():
    """
    Scan the root directory for files starting with 'template_'
    Returns a list of template names (without the 'template_' prefix and extension)
    """
    templates = []
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    for file in os.listdir(root_dir):
        if file.startswith('template_') and (file.endswith('.pptx') or file.endswith('.docx')):
            # Extract template name (remove 'template_' prefix and extension)
            name = file.replace('template_', '')
            # Remove extension
            name = re.sub(r'\.(pptx|docx)$', '', name)
            templates.append({
                'name': name,
                'file': file,
                'type': 'PPTX' if file.endswith('.pptx') else 'DOCX',
                'source': 'root',
                'path': os.path.join(root_dir, file)
            })
    
    return templates

def get_storage_dir():
    """Get the stored_templates directory for user-uploaded templates"""
    storage_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stored_templates")
    os.makedirs(storage_dir, exist_ok=True)
    return storage_dir

def load_template_from_root(template_file):
    """Load a template from the root directory"""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(root_dir, template_file)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            return f.read()
    return None

def save_template_user(template_bytes, template_name):
    """Save user-uploaded template to stored_templates folder"""
    storage_dir = get_storage_dir()
    safe_name = re.sub(r'[^\w\-_. ]', '_', template_name)
    if not safe_name.endswith('.pptx') and not safe_name.endswith('.docx'):
        safe_name += '.docx'
    filepath = os.path.join(storage_dir, safe_name)
    with open(filepath, 'wb') as f:
        f.write(template_bytes)
    return filepath

def load_template_user(template_name):
    """Load user-uploaded template from stored_templates folder"""
    storage_dir = get_storage_dir()
    filepath = os.path.join(storage_dir, template_name)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            return f.read()
    return None

def get_user_templates():
    """Get user-uploaded templates from stored_templates folder"""
    storage_dir = get_storage_dir()
    templates = []
    if os.path.exists(storage_dir):
        for file in os.listdir(storage_dir):
            if file.endswith('.pptx') or file.endswith('.docx'):
                filepath = os.path.join(storage_dir, file)
                stat = os.stat(filepath)
                templates.append({
                    'name': file,
                    'type': 'PPTX' if file.endswith('.pptx') else 'DOCX',
                    'source': 'user',
                    'path': filepath,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
    return templates

def get_all_templates():
    """Get all templates from both root and user storage"""
    templates = []
    
    # Get root templates (template_*.pptx/docx)
    root_templates = get_templates_from_root()
    templates.extend(root_templates)
    
    # Get user templates
    user_templates = get_user_templates()
    templates.extend(user_templates)
    
    return templates

def delete_user_template(template_name):
    """Delete a user-uploaded template"""
    storage_dir = get_storage_dir()
    filepath = os.path.join(storage_dir, template_name)
    if os.path.exists(filepath):
        os.remove(filepath)
        # Delete associated config
        config_name = template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
        config_path = os.path.join(storage_dir, config_name)
        if os.path.exists(config_path):
            os.remove(config_path)
        return True
    return False

def save_config_to_file(config_data, config_name="template_config.json"):
    storage_dir = get_storage_dir()
    filepath = os.path.join(storage_dir, config_name)
    serializable_config = {}
    for key, value in config_data.items():
        if isinstance(value, dict) and 'screenshot' in value:
            serializable_config[key] = {
                'type': value.get('type', 'Map'),
                'lat': value.get('lat'),
                'lng': value.get('lng'),
                'basemap': value.get('basemap', 'satellite')
            }
        else:
            serializable_config[key] = value
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(serializable_config, f, indent=4)
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
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"Generated_Document_{timestamp}.{file_type}"

# --- MAP FUNCTIONS ---
def get_basemap_tiles(basemap_choice):
    basemaps = {
        'satellite': 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        'openstreetmap': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        'carto_light': 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
    }
    return basemaps.get(basemap_choice, basemaps['satellite'])

def capture_map_simple(lat, lng, basemap='satellite', zoom=15):
    try:
        api_key = "AIzaSyA5oEohxJ-jB5WBR6pR3D8VtaY8X2CkT-8"
        maptype = 'satellite' if basemap == 'satellite' else 'roadmap'
        url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom={zoom}&size=800x600&maptype={maptype}&markers=color:red%7C{lat},{lng}&key={api_key}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            return img_bytes
    except:
        pass
    
    try:
        from PIL import ImageDraw
        img = Image.new('RGB', (800, 600), color='#F0F4F8')
        draw = ImageDraw.Draw(img)
        draw.text((300, 280), f"Location: {lat:.6f}, {lng:.6f}", fill='#003366')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes
    except:
        return None

def parse_coordinates(coord_string):
    match = re.match(r'^\s*(-?\d+(?:\.\d+)?)\s*[,;]\s*(-?\d+(?:\.\d+)?)\s*$', coord_string.strip())
    if match:
        return float(match.group(1)), float(match.group(2))
    return None, None

def map_input_component(token, label, default_lat=14.5995, default_lng=120.9842):
    map_key = f"map_{token}"
    
    if map_key not in st.session_state:
        st.session_state[map_key] = {
            "lat": default_lat,
            "lng": default_lng,
            "screenshot": None,
            "saved": False,
            "basemap": "satellite",
            "zoom": 15,
            "open": False
        }
    
    if st.session_state[map_key]["saved"]:
        st.markdown(
            f'<div class="map-saved-indicator">Location: {st.session_state[map_key]["lat"]:.6f}, {st.session_state[map_key]["lng"]:.6f}</div>',
            unsafe_allow_html=True
        )
        if st.session_state[map_key]["screenshot"]:
            st.image(st.session_state[map_key]["screenshot"], width=200)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("Open Map", key=f"open_{token}", use_container_width=True):
            st.session_state[map_key]["open"] = not st.session_state[map_key].get("open", False)
            st.rerun()
    with col2:
        if st.button("Clear", key=f"clear_{token}", use_container_width=True):
            st.session_state[map_key]["saved"] = False
            st.session_state[map_key]["screenshot"] = None
            st.rerun()
    
    if st.session_state[map_key].get("open", False):
        with st.expander("Map Editor", expanded=True):
            col_a, col_b = st.columns(2)
            with col_a:
                basemap = st.selectbox(
                    "Basemap",
                    ["satellite", "openstreetmap", "carto_light"],
                    index=["satellite", "openstreetmap", "carto_light"].index(
                        st.session_state[map_key].get("basemap", "satellite")
                    ),
                    key=f"basemap_{token}",
                    label_visibility="collapsed"
                )
                st.session_state[map_key]["basemap"] = basemap
            with col_b:
                zoom = st.slider("Zoom", 10, 18, st.session_state[map_key]["zoom"], key=f"zoom_{token}")
                st.session_state[map_key]["zoom"] = zoom
            
            coords = st.text_input(
                "Coordinates (lat, lon)",
                value=f"{st.session_state[map_key]['lat']:.6f}, {st.session_state[map_key]['lng']:.6f}",
                key=f"coords_{token}"
            )
            lat, lng = parse_coordinates(coords)
            if lat and lng:
                st.session_state[map_key]["lat"] = lat
                st.session_state[map_key]["lng"] = lng
            
            try:
                tile_url = get_basemap_tiles(basemap)
                m = folium.Map(
                    location=[st.session_state[map_key]["lat"], st.session_state[map_key]["lng"]],
                    zoom_start=zoom,
                    width='100%',
                    height=350,
                    tiles=tile_url
                )
                folium.Marker(
                    [st.session_state[map_key]["lat"], st.session_state[map_key]["lng"]],
                    draggable=True
                ).add_to(m)
                folium_static(m, width=700, height=350)
            except:
                st.info("Enter coordinates manually.")
            
            if st.button("Capture Map", key=f"capture_{token}", use_container_width=True):
                with st.spinner("Capturing..."):
                    result = capture_map_simple(
                        st.session_state[map_key]["lat"],
                        st.session_state[map_key]["lng"],
                        basemap,
                        zoom
                    )
                    if result:
                        st.session_state[map_key]["screenshot"] = result
                        st.session_state[map_key]["saved"] = True
                        st.success("Map captured!")
                        st.rerun()
    
    if st.session_state[map_key]["saved"] and st.session_state[map_key]["screenshot"]:
        return st.session_state[map_key]["screenshot"]
    return None

# --- CTA PRESET FUNCTIONS ---
def load_cta_presets():
    storage_dir = get_storage_dir()
    presets_file = os.path.join(storage_dir, "cta_presets.json")
    if os.path.exists(presets_file):
        try:
            with open(presets_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_cta_presets(presets):
    storage_dir = get_storage_dir()
    presets_file = os.path.join(storage_dir, "cta_presets.json")
    with open(presets_file, 'w', encoding='utf-8') as f:
        json.dump(presets, f, indent=4)

def format_cta_list(cta_list):
    if not cta_list:
        return ""
    formatted = []
    for cta in cta_list:
        parts = [cta['name']]
        if cta.get('phone'):
            parts.append(f"({cta['phone']})")
        if cta.get('email'):
            parts.append(cta['email'])
        if cta.get('company'):
            parts.append(f"- {cta['company']}")
        formatted.append(" ".join(parts))
    return ", ".join(formatted)

def get_cta_token_names():
    return ['cta', 'contact', 'contacts', 'contact_person', 'point_of_contact']

def cta_preset_manager():
    if "cta_presets" not in st.session_state:
        st.session_state.cta_presets = load_cta_presets()
    
    with st.expander("CTA Preset Manager", expanded=False):
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
        with col1:
            name = st.text_input("Name", key="cta_name", placeholder="Name", label_visibility="collapsed")
        with col2:
            phone = st.text_input("Phone", key="cta_phone", placeholder="Phone", label_visibility="collapsed")
        with col3:
            email = st.text_input("Email", key="cta_email", placeholder="Email", label_visibility="collapsed")
        with col4:
            company = st.text_input("Company", key="cta_company", placeholder="Company", label_visibility="collapsed")
        with col5:
            if st.button("Add", key="add_cta", use_container_width=True):
                if name.strip():
                    st.session_state.cta_presets.append({
                        "name": name.strip(),
                        "phone": phone.strip(),
                        "email": email.strip(),
                        "company": company.strip()
                    })
                    st.session_state.cta_presets.sort(key=lambda x: x['name'].lower())
                    save_cta_presets(st.session_state.cta_presets)
                    st.rerun()
        
        if st.session_state.cta_presets:
            for idx, preset in enumerate(st.session_state.cta_presets):
                col_display, col_delete = st.columns([5, 1])
                with col_display:
                    st.markdown(f"""
                    <div class="cta-preset-card">
                        <div class="cta-name">{preset['name']}</div>
                        <div class="cta-detail">{preset.get('phone', '')} {preset.get('email', '')} {preset.get('company', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_delete:
                    if st.button("X", key=f"del_cta_{idx}", use_container_width=True):
                        del st.session_state.cta_presets[idx]
                        save_cta_presets(st.session_state.cta_presets)
                        st.rerun()

def cta_selector(token, label):
    cta_token = f"cta_{token}"
    if cta_token not in st.session_state:
        st.session_state[cta_token] = []
    
    preset_names = [p['name'] for p in st.session_state.cta_presets]
    if not preset_names:
        return ""
    
    selected = st.multiselect(
        label,
        options=preset_names,
        default=st.session_state[cta_token],
        key=f"cta_select_{token}"
    )
    st.session_state[cta_token] = selected
    selected_presets = [p for p in st.session_state.cta_presets if p['name'] in selected]
    if selected_presets:
        preview = format_cta_list(selected_presets)
        st.markdown(f'<div class="cta-preview">{preview}</div>', unsafe_allow_html=True)
    return format_cta_list(selected_presets)

# --- INIT APP ---
st.set_page_config(page_title="OpenFlux - Template Automation", layout="wide", initial_sidebar_state="collapsed")
st.markdown(MINIMAL_CRE_SYSTEM, unsafe_allow_html=True)

# Initialize session state
if "custom_mapping" not in st.session_state:
    st.session_state.custom_mapping = {}
if "tokens" not in st.session_state:
    st.session_state.tokens = []
if "template_bytes" not in st.session_state:
    st.session_state.template_bytes = None
if "saved_template_name" not in st.session_state:
    st.session_state.saved_template_name = None
if "template_loaded" not in st.session_state:
    st.session_state.template_loaded = False
if "template_type" not in st.session_state:
    st.session_state.template_type = None
if "delete_trigger" not in st.session_state:
    st.session_state.delete_trigger = False
if "show_delete_confirm" not in st.session_state:
    st.session_state.show_delete_confirm = False
if "template_to_delete" not in st.session_state:
    st.session_state.template_to_delete = None
if "save_success" not in st.session_state:
    st.session_state.save_success = False
if "saved_file_name" not in st.session_state:
    st.session_state.saved_file_name = None
if "clear_uploader" not in st.session_state:
    st.session_state.clear_uploader = False
if "map_data" not in st.session_state:
    st.session_state.map_data = {}
if "cta_presets" not in st.session_state:
    st.session_state.cta_presets = load_cta_presets()

# --- MAIN UI ---
st.markdown("<hr>", unsafe_allow_html=True)

# Template Management
st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
st.markdown('<div class="section-header">Templates</div>', unsafe_allow_html=True)

col_template1, col_template2 = st.columns(2)

with col_template1:
    templates = get_all_templates()
    template_options = ["Select template"]
    
    # Separate root and user templates
    root_templates = [t for t in templates if t.get('source') == 'root']
    user_templates = [t for t in templates if t.get('source') == 'user']
    
    # Add root templates (show clean names without template_ prefix)
    if root_templates:
        for t in root_templates:
            template_options.append(f"{t['name']} (root)")
    
    # Add user templates
    if user_templates:
        for t in user_templates:
            template_options.append(f"{t['name']} (uploaded)")
    
    dropdown_col, delete_col = st.columns([4, 1])
    
    with dropdown_col:
        selected_template = st.selectbox(
            "Load Template",
            template_options,
            key="template_select",
            label_visibility="collapsed"
        )
    
    with delete_col:
        if selected_template and selected_template != "Select template" and "(uploaded)" in selected_template:
            template_name = selected_template.split(' (')[0]
            if st.button("Delete", key="delete_template", help="Delete this template"):
                st.session_state.show_delete_confirm = True
                st.session_state.template_to_delete = template_name
                st.rerun()
    
    if st.session_state.show_delete_confirm:
        st.warning(f"Delete '{st.session_state.template_to_delete}'?")
        col_yes, col_no = st.columns([1, 1])
        with col_yes:
            if st.button("Yes", key="confirm_delete"):
                if delete_user_template(st.session_state.template_to_delete):
                    st.session_state.delete_trigger = True
                    st.session_state.template_bytes = None
                    st.session_state.saved_template_name = None
                    st.session_state.template_loaded = False
                    st.session_state.tokens = []
                    st.session_state.show_delete_confirm = False
                    st.success(f"Deleted: {st.session_state.template_to_delete}")
                    st.rerun()
        with col_no:
            if st.button("No", key="cancel_delete"):
                st.session_state.show_delete_confirm = False
                st.rerun()
    
    if selected_template and selected_template != "Select template":
        # Parse selection
        name_parts = selected_template.split(' (')
        template_name = name_parts[0]
        source = name_parts[1].replace(')', '') if len(name_parts) > 1 else 'root'
        
        template_bytes = None
        
        if source == 'root':
            # Find the actual file name
            for t in root_templates:
                if t['name'] == template_name:
                    template_bytes = load_template_from_root(t['file'])
                    break
        else:
            template_bytes = load_template_user(template_name)
        
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
    uploaded_template = st.file_uploader(
        "Upload Template",
        type=["pptx", "docx"],
        key="template_upload",
        label_visibility="collapsed"
    )
    
    if uploaded_template:
        template_bytes = uploaded_template.getvalue()
        template_name = uploaded_template.name
        st.session_state.template_bytes = template_bytes
        st.session_state.saved_template_name = None
        st.session_state.template_loaded = True
        st.session_state.template_type = 'pptx' if template_name.endswith('.pptx') else 'docx'
        
        tokens = extract_placeholders(template_bytes, st.session_state.template_type)
        st.session_state.tokens = tokens
        st.session_state.custom_mapping = {}
        
        if st.button("Save Template", key="save_template_btn", use_container_width=True):
            save_template_user(template_bytes, template_name)
            st.session_state.saved_template_name = template_name
            st.session_state.save_success = True
            st.session_state.saved_file_name = template_name
            st.success(f"Template saved: {template_name}")
            st.rerun()

if st.session_state.save_success:
    st.success(f"Template '{st.session_state.saved_file_name}' saved!")
    st.session_state.save_success = False
    st.session_state.saved_file_name = None

if st.session_state.template_bytes:
    template_name = st.session_state.saved_template_name or "Unsaved"
    template_type = st.session_state.template_type or "Unknown"
    st.markdown(f'<div class="saved-indicator">Active: {template_name} ({template_type.upper()})</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# CTA Preset Manager
cta_preset_manager()

# Placeholder Values
template_bytes = st.session_state.template_bytes
template_type = st.session_state.template_type

if template_bytes and st.session_state.tokens:
    st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Placeholder Values</div>', unsafe_allow_html=True)
    
    tokens = st.session_state.tokens
    text_data = {}
    image_data = {}
    cta_tokens = get_cta_token_names()
    
    mid = len(tokens) // 2
    col1, col2 = st.columns(2)
    
    for idx, token in enumerate(tokens):
        clean_label = token.replace("{", "").replace("}", "").strip()
        current_type = st.session_state.custom_mapping.get(token, "Text")
        is_cta = any(cta_token in clean_label.lower() for cta_token in cta_tokens) or clean_label.lower() in cta_tokens
        
        col_a, col_b = st.columns([3, 1])
        with col_b:
            if is_cta:
                dtype = "CTA"
                st.markdown("CTA")
            else:
                dtype = st.selectbox(
                    "Type",
                    ["Text", "Image", "Map"],
                    index=["Text", "Image", "Map"].index(current_type) if current_type in ["Text", "Image", "Map"] else 0,
                    key=f"type_{token}",
                    label_visibility="collapsed"
                )
                if dtype != current_type:
                    st.session_state.custom_mapping[token] = dtype
        
        with col_a:
            if is_cta:
                text_data[token] = cta_selector(token, clean_label)
            elif dtype == "Image" and template_type == 'pptx':
                image_data[token] = st.file_uploader(
                    clean_label,
                    type=["png", "jpg", "jpeg"],
                    key=f"img_{token}",
                    label_visibility="collapsed"
                )
            elif dtype == "Map":
                st.session_state.map_data[token] = map_input_component(token, clean_label)
            else:
                text_data[token] = st.text_input(
                    clean_label,
                    key=f"txt_{token}",
                    label_visibility="collapsed"
                )
    
    st.markdown('</div>', unsafe_allow_html=True)

# Download Section
if template_bytes:
    st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Download</div>', unsafe_allow_html=True)
    
    for token, map_img in st.session_state.map_data.items():
        if map_img:
            image_data[token] = map_img
    
    template_name = st.session_state.saved_template_name or "Document"
    base_name = re.sub(r'\.(pptx|docx)$', '', template_name)
    
    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        if template_type == 'pptx':
            try:
                pptx_data = generate_pptx_bytes(template_bytes, text_data, image_data)
                filename = get_download_filename(base_name, "pptx")
                st.download_button(
                    label="Download PPTX",
                    data=pptx_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.button("Download PPTX", disabled=True, use_container_width=True, help="Only for PPTX templates")
    
    with col_dl2:
        if template_type == 'docx':
            try:
                docx_data = generate_docx_bytes(template_bytes, text_data, image_data)
                filename = get_download_filename(base_name, "docx")
                st.download_button(
                    label="Download DOCX",
                    data=docx_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.button("Download DOCX", disabled=True, use_container_width=True, help="Only for DOCX templates")
    
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Upload or select a template to begin")

st.markdown("---")
st.caption("OpenFlux")
