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

# --- GITHUB CONFIG ---
GITHUB_REPO = "openflux_templates"
GITHUB_BRANCH = "main"

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

# --- GITHUB FUNCTIONS ---
def get_github_token():
    try:
        return st.secrets["github"]["token"]
    except:
        return os.environ.get("GITHUB_TOKEN")

def get_github_repo():
    token = get_github_token()
    if not token:
        return None
    try:
        from github import Github
        g = Github(token)
        return g.get_user().get_repo(GITHUB_REPO)
    except:
        return None

def list_github_templates():
    try:
        repo = get_github_repo()
        if not repo:
            return []
        templates = []
        contents = repo.get_contents("", ref=GITHUB_BRANCH)
        for content in contents:
            if content.type == "file" and (content.name.endswith('.pptx') or content.name.endswith('.docx')):
                templates.append({
                    'name': content.name,
                    'sha': content.sha,
                    'type': 'PPTX' if content.name.endswith('.pptx') else 'DOCX',
                    'source': 'github'
                })
        return templates
    except:
        return []

def upload_to_github(file_bytes, filename):
    try:
        repo = get_github_repo()
        if not repo:
            return False
        try:
            contents = repo.get_contents(filename, ref=GITHUB_BRANCH)
            repo.update_file(
                path=filename,
                message=f"Update: {filename}",
                content=base64.b64encode(file_bytes).decode('utf-8'),
                sha=contents.sha,
                branch=GITHUB_BRANCH
            )
        except:
            repo.create_file(
                path=filename,
                message=f"Add: {filename}",
                content=base64.b64encode(file_bytes).decode('utf-8'),
                branch=GITHUB_BRANCH
            )
        return True
    except:
        return False

def download_from_github(filename):
    try:
        repo = get_github_repo()
        if not repo:
            return None
        contents = repo.get_contents(filename, ref=GITHUB_BRANCH)
        return base64.b64decode(contents.content)
    except:
        return None

# --- FILE MANAGEMENT ---
def get_storage_dir():
    storage_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stored_templates")
    os.makedirs(storage_dir, exist_ok=True)
    return storage_dir

def save_template_local(template_bytes, template_name):
    storage_dir = get_storage_dir()
    safe_name = re.sub(r'[^\w\-_. ]', '_', template_name)
    filepath = os.path.join(storage_dir, safe_name)
    with open(filepath, 'wb') as f:
        f.write(template_bytes)
    return filepath

def load_template_local(template_name):
    storage_dir = get_storage_dir()
    filepath = os.path.join(storage_dir, template_name)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            return f.read()
    return None

def get_all_templates():
    templates = []
    storage_dir = get_storage_dir()
    if os.path.exists(storage_dir):
        for file in os.listdir(storage_dir):
            if file.endswith('.pptx') or file.endswith('.docx'):
                templates.append({
                    'name': file,
                    'type': 'PPTX' if file.endswith('.pptx') else 'DOCX',
                    'source': 'local'
                })
    for t in list_github_templates():
        if not any(x['name'] == t['name'] for x in templates):
            templates.append(t)
    return templates

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

# --- CORE UTILITIES ---
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
                run.text = run.text.replace(token, str(value) if value else '')

def generate_pptx_bytes(template_bytes, text_inputs, image_inputs):
    prs = Presentation(io.BytesIO(template_bytes))
    for slide in prs.slides:
        shapes_to_delete = []
        images_to_add = []
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
                slide.shapes.add_picture(img_file, left, top, width=width, height=height)
            except:
                pass
        for old_shape in shapes_to_delete:
            try:
                sp = old_shape._element
                sp.getparent().remove(sp)
            except:
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
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{base_name}_{timestamp}.{file_type}"
    return f"Document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_type}"

# --- MAP FUNCTIONS ---
def get_basemap_tiles(basemap):
    basemaps = {
        'satellite': 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        'openstreetmap': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        'carto_light': 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
    }
    return basemaps.get(basemap, basemaps['satellite'])

def capture_map_simple(lat, lng, basemap='satellite', zoom=15):
    """Simple map capture using static API"""
    try:
        # Try Google Static API
        url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom={zoom}&size=800x600&maptype=satellite&markers=color:red%7C{lat},{lng}&key=AIzaSyA5oEohxJ-jB5WBR6pR3D8VtaY8X2CkT-8"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            return img_bytes
    except:
        pass
    # Fallback: Create placeholder
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
            "lat": default_lat, "lng": default_lng,
            "screenshot": None, "saved": False,
            "basemap": "satellite", "zoom": 15, "open": False
        }
    
    if st.session_state[map_key]["saved"]:
        st.markdown(f'<div class="map-saved-indicator">Location: {st.session_state[map_key]["lat"]:.6f}, {st.session_state[map_key]["lng"]:.6f}</div>', unsafe_allow_html=True)
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
                basemap = st.selectbox("Basemap", ["satellite", "openstreetmap", "carto_light"], 
                    index=["satellite", "openstreetmap", "carto_light"].index(st.session_state[map_key].get("basemap", "satellite")),
                    key=f"basemap_{token}", label_visibility="collapsed")
                st.session_state[map_key]["basemap"] = basemap
            with col_b:
                zoom = st.slider("Zoom", 10, 18, st.session_state[map_key]["zoom"], key=f"zoom_{token}")
                st.session_state[map_key]["zoom"] = zoom
            
            coords = st.text_input("Coordinates (lat, lon)",
                value=f"{st.session_state[map_key]['lat']:.6f}, {st.session_state[map_key]['lng']:.6f}",
                key=f"coords_{token}")
            lat, lng = parse_coordinates(coords)
            if lat and lng:
                st.session_state[map_key]["lat"] = lat
                st.session_state[map_key]["lng"] = lng
            
            try:
                tile_url = get_basemap_tiles(basemap)
                m = folium.Map(location=[st.session_state[map_key]["lat"], st.session_state[map_key]["lng"]],
                    zoom_start=zoom, width='100%', height=350, tiles=tile_url)
                folium.Marker([st.session_state[map_key]["lat"], st.session_state[map_key]["lng"]], draggable=True).add_to(m)
                folium_static(m, width=700, height=350)
            except:
                st.info("Enter coordinates manually.")
            
            if st.button("Capture Map", key=f"capture_{token}", use_container_width=True):
                with st.spinner("Capturing..."):
                    result = capture_map_simple(st.session_state[map_key]["lat"], st.session_state[map_key]["lng"], basemap, zoom)
                    if result:
                        st.session_state[map_key]["screenshot"] = result
                        st.session_state[map_key]["saved"] = True
                        st.success("Map captured!")
                        st.rerun()
    
    if st.session_state[map_key]["saved"] and st.session_state[map_key]["screenshot"]:
        return st.session_state[map_key]["screenshot"]
    return None

# --- CTA PRESET MANAGER UI ---
def cta_preset_manager():
    if "cta_presets" not in st.session_state:
        st.session_state.cta_presets = load_cta_presets()
    
    with st.expander("CTA Preset Manager", expanded=False):
        # Add new preset
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
                        "name": name.strip(), "phone": phone.strip(),
                        "email": email.strip(), "company": company.strip()
                    })
                    st.session_state.cta_presets.sort(key=lambda x: x['name'].lower())
                    save_cta_presets(st.session_state.cta_presets)
                    st.rerun()
        
        # Display presets
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
    
    selected = st.multiselect(label, options=preset_names, default=st.session_state[cta_token], key=f"cta_select_{token}")
    st.session_state[cta_token] = selected
    selected_presets = [p for p in st.session_state.cta_presets if p['name'] in selected]
    if selected_presets:
        preview = format_cta_list(selected_presets)
        st.markdown(f'<div class="cta-preview">{preview}</div>', unsafe_allow_html=True)
    return format_cta_list(selected_presets)

# --- INIT APP ---
st.set_page_config(page_title="OpenFlux - Template Automation", layout="wide", initial_sidebar_state="collapsed")
st.markdown(MINIMAL_CRE_SYSTEM, unsafe_allow_html=True)

# Session state
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

col1, col2 = st.columns(2)

with col1:
    templates = get_all_templates()
    options = ["Select template"] + [f"{t['name']} ({t['type']})" for t in templates]
    selected = st.selectbox("Load Template", options, label_visibility="collapsed")
    
    if selected and selected != "Select template":
        name = selected.split(' (')[0]
        is_github = any(t['source'] == 'github' for t in templates if t['name'] == name)
        bytes_data = download_from_github(name) if is_github else load_template_local(name)
        if bytes_data:
            st.session_state.template_bytes = bytes_data
            st.session_state.saved_template_name = name
            st.session_state.template_loaded = True
            st.session_state.template_type = 'pptx' if name.endswith('.pptx') else 'docx'
            st.session_state.tokens = extract_placeholders(bytes_data, st.session_state.template_type)

with col2:
    uploaded = st.file_uploader("Upload Template", type=["pptx", "docx"], label_visibility="collapsed")
    if uploaded:
        bytes_data = uploaded.getvalue()
        st.session_state.template_bytes = bytes_data
        st.session_state.saved_template_name = None
        st.session_state.template_loaded = True
        st.session_state.template_type = 'pptx' if uploaded.name.endswith('.pptx') else 'docx'
        st.session_state.tokens = extract_placeholders(bytes_data, st.session_state.template_type)
        if st.button("Save Template", use_container_width=True):
            save_template_local(bytes_data, uploaded.name)
            upload_to_github(bytes_data, uploaded.name)
            st.session_state.saved_template_name = uploaded.name
            st.success("Template saved!")

if st.session_state.template_bytes:
    st.markdown(f'<div class="saved-indicator">Active: {st.session_state.saved_template_name or "Unsaved"} ({st.session_state.template_type.upper()})</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- CTA PRESET MANAGER (Before Placeholders) ---
cta_preset_manager()

# --- PLACEHOLDER VALUES ---
template_bytes = st.session_state.template_bytes
template_type = st.session_state.template_type

if template_bytes and st.session_state.tokens:
    st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Placeholder Values</div>', unsafe_allow_html=True)
    
    tokens = st.session_state.tokens
    text_data = {}
    image_data = {}
    cta_tokens = get_cta_token_names()
    
    # Split into two columns
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
                st.markdown("**CTA**")
            else:
                dtype = st.selectbox("Type", ["Text", "Image", "Map"],
                    index=["Text", "Image", "Map"].index(current_type) if current_type in ["Text", "Image", "Map"] else 0,
                    key=f"type_{token}", label_visibility="collapsed")
                if dtype != current_type:
                    st.session_state.custom_mapping[token] = dtype
        
        with col_a:
            if is_cta:
                text_data[token] = cta_selector(token, clean_label)
            elif dtype == "Image" and template_type == 'pptx':
                image_data[token] = st.file_uploader(clean_label, type=["png", "jpg", "jpeg"], key=f"img_{token}", label_visibility="collapsed")
            elif dtype == "Map":
                st.session_state.map_data[token] = map_input_component(token, clean_label)
            else:
                text_data[token] = st.text_input(clean_label, key=f"txt_{token}", label_visibility="collapsed")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- DOWNLOAD SECTION ---
if template_bytes:
    st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Download</div>', unsafe_allow_html=True)
    
    for token, map_img in st.session_state.map_data.items():
        if map_img:
            image_data[token] = map_img
    
    template_name = st.session_state.saved_template_name or "Document"
    base_name = re.sub(r'\.(pptx|docx)$', '', template_name)
    
    if template_type == 'pptx':
        try:
            data = generate_pptx_bytes(template_bytes, text_data, image_data)
            st.download_button("Download PPTX", data, get_download_filename(base_name, "pptx"), use_container_width=True)
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        try:
            data = generate_docx_bytes(template_bytes, text_data, image_data)
            st.download_button("Download DOCX", data, get_download_filename(base_name, "docx"), use_container_width=True)
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Upload or select a template to begin")

st.markdown("---")
st.caption("OpenFlux")
