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
import tempfile
import time
import base64
import requests
import math
from github import Github, GithubException
from github import Auth

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
    .map-editor-header {
        background-color: #F8F9FA;
        padding: 8px 12px;
        border-radius: 4px;
        margin-bottom: 8px;
        border: 1px solid #E0E0E0;
        font-weight: 600;
        font-size: 13px;
    }
    .github-status {
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 12px;
        margin: 4px 0;
    }
    .github-status.success {
        background-color: #E8F5E9;
        color: #2E7D32;
        border-left: 3px solid #2E7D32;
    }
    .github-status.error {
        background-color: #FFEBEE;
        color: #C62828;
        border-left: 3px solid #C62828;
    }
    
    hr { margin: 12px 0 !important; border-color: #E0E0E0 !important; }
</style>
"""

# --- GITHUB FUNCTIONS ---
def get_github_token():
    """Get GitHub token from Streamlit secrets or environment"""
    try:
        # Try Streamlit secrets
        token = st.secrets["github"]["token"]
        if token:
            return token
    except:
        pass
    
    # Try environment variable
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    
    st.warning("⚠️ GitHub token not found. Please set GITHUB_TOKEN in Streamlit secrets.")
    return None

def get_github_repo():
    """Get GitHub repository object"""
    token = get_github_token()
    if not token:
        return None
    
    try:
        g = Github(token)
        # Try to get the repository
        try:
            repo = g.get_user().get_repo(GITHUB_REPO)
            return repo
        except GithubException as e:
            if e.status == 404:
                st.error(f"❌ Repository '{GITHUB_REPO}' not found. Please create it first.")
            else:
                st.error(f"❌ GitHub error: {e}")
            return None
    except Exception as e:
        st.error(f"❌ Error connecting to GitHub: {e}")
        return None

def list_github_templates():
    """List templates from GitHub repository"""
    try:
        repo = get_github_repo()
        if not repo:
            return []
        
        templates = []
        contents = repo.get_contents("", ref=GITHUB_BRANCH)
        
        for content in contents:
            if content.type == "file":
                name = content.name
                if name.endswith('.pptx') or name.endswith('.docx'):
                    templates.append({
                        'name': name,
                        'sha': content.sha,
                        'size': content.size,
                        'type': 'PPTX' if name.endswith('.pptx') else 'DOCX',
                        'source': 'github'
                    })
        return templates
        
    except Exception as e:
        st.error(f"❌ Error listing templates: {str(e)}")
        return []

def upload_to_github(file_bytes, filename):
    """Upload template to GitHub repository"""
    try:
        repo = get_github_repo()
        if not repo:
            return False
        
        # Check if file exists
        try:
            contents = repo.get_contents(filename, ref=GITHUB_BRANCH)
            # Update existing file
            repo.update_file(
                path=filename,
                message=f"Update template: {filename}",
                content=base64.b64encode(file_bytes).decode('utf-8'),
                sha=contents.sha,
                branch=GITHUB_BRANCH
            )
            return True
        except GithubException:
            # File doesn't exist, create new
            repo.create_file(
                path=filename,
                message=f"Add template: {filename}",
                content=base64.b64encode(file_bytes).decode('utf-8'),
                branch=GITHUB_BRANCH
            )
            return True
            
    except Exception as e:
        st.error(f"❌ Error uploading to GitHub: {str(e)}")
        return False

def download_from_github(filename):
    """Download template from GitHub repository"""
    try:
        repo = get_github_repo()
        if not repo:
            return None
        
        contents = repo.get_contents(filename, ref=GITHUB_BRANCH)
        return base64.b64decode(contents.content)
        
    except Exception as e:
        st.error(f"❌ Error downloading from GitHub: {str(e)}")
        return None

def delete_from_github(filename):
    """Delete template from GitHub repository"""
    try:
        repo = get_github_repo()
        if not repo:
            return False
        
        contents = repo.get_contents(filename, ref=GITHUB_BRANCH)
        repo.delete_file(
            path=filename,
            message=f"Delete template: {filename}",
            sha=contents.sha,
            branch=GITHUB_BRANCH
        )
        return True
        
    except Exception as e:
        st.error(f"❌ Error deleting from GitHub: {str(e)}")
        return False

def upload_config_to_github(config_data, template_name):
    """Upload config to GitHub"""
    try:
        repo = get_github_repo()
        if not repo:
            return False
        
        config_name = template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
        config_json = json.dumps(config_data, indent=4).encode('utf-8')
        
        try:
            contents = repo.get_contents(config_name, ref=GITHUB_BRANCH)
            repo.update_file(
                path=config_name,
                message=f"Update config: {config_name}",
                content=base64.b64encode(config_json).decode('utf-8'),
                sha=contents.sha,
                branch=GITHUB_BRANCH
            )
        except:
            repo.create_file(
                path=config_name,
                message=f"Add config: {config_name}",
                content=base64.b64encode(config_json).decode('utf-8'),
                branch=GITHUB_BRANCH
            )
        return True
    except:
        return False

def download_config_from_github(template_name):
    """Download config from GitHub"""
    try:
        repo = get_github_repo()
        if not repo:
            return None
        
        config_name = template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
        contents = repo.get_contents(config_name, ref=GITHUB_BRANCH)
        config_json = base64.b64decode(contents.content).decode('utf-8')
        return json.loads(config_json)
    except:
        return None

# --- FILE MANAGEMENT FUNCTIONS ---
def get_storage_dir():
    """Get local storage directory"""
    storage_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stored_templates")
    os.makedirs(storage_dir, exist_ok=True)
    return storage_dir

def save_template_local(template_bytes, template_name):
    """Save template locally"""
    storage_dir = get_storage_dir()
    safe_name = re.sub(r'[^\w\-_. ]', '_', template_name)
    if not safe_name.endswith('.pptx') and not safe_name.endswith('.docx'):
        safe_name += '.docx'
    filepath = os.path.join(storage_dir, safe_name)
    with open(filepath, 'wb') as f:
        f.write(template_bytes)
    return filepath

def load_template_local(template_name):
    """Load template from local storage"""
    storage_dir = get_storage_dir()
    filepath = os.path.join(storage_dir, template_name)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            return f.read()
    return None

def delete_template_local(template_name):
    """Delete template from local storage"""
    storage_dir = get_storage_dir()
    filepath = os.path.join(storage_dir, template_name)
    if os.path.exists(filepath):
        os.remove(filepath)
    return True

def get_all_templates():
    """Get templates from both local and GitHub"""
    templates = []
    
    # Get local templates
    storage_dir = get_storage_dir()
    if os.path.exists(storage_dir):
        for file in os.listdir(storage_dir):
            if file.endswith('.pptx') or file.endswith('.docx'):
                templates.append({
                    'name': file,
                    'type': 'PPTX' if file.endswith('.pptx') else 'DOCX',
                    'source': 'local'
                })
    
    # Get GitHub templates
    github_templates = list_github_templates()
    for t in github_templates:
        # Check if already in list
        if not any(x['name'] == t['name'] for x in templates):
            templates.append(t)
    
    return templates

def delete_template(template_name):
    """Delete template from both local and GitHub"""
    delete_template_local(template_name)
    delete_from_github(template_name)
    return True

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
    except:
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
        base_name = re.sub(r'[^\w\-_. ]', '_', base_name)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{base_name}_{timestamp}.{file_type}"
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"Generated_Document_{timestamp}.{file_type}"

# --- MAP FUNCTIONS ---
def get_basemap_tiles(basemap):
    basemaps = {
        'satellite': 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        'openstreetmap': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        'carto_light': 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
    }
    return basemaps.get(basemap, basemaps['satellite'])

def capture_map(lat, lng, basemap='satellite', zoom=15):
    """Try to capture map using multiple methods"""
    # Method 1: Google Static API
    try:
        url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom={zoom}&size=800x600&maptype=satellite&markers=color:red%7C{lat},{lng}&key=AIzaSyA5oEohxJ-jB5WBR6pR3D8VtaY8X2CkT-8"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            return img_bytes, "Google Static API"
    except:
        pass
    
    # Method 2: OSM Static
    try:
        url = f"https://staticmap.openstreetmap.de/staticmap.php?center={lat},{lng}&zoom={zoom}&size=800x600&maptype=mapnik&markers={lat},{lng},red-pin"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            return img_bytes, "OSM Static API"
    except:
        pass
    
    # Fallback: placeholder
    img = Image.new('RGB', (800, 600), color='#F0F4F8')
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.text((300, 280), f"Location: {lat:.6f}, {lng:.6f}", fill='#003366')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes, "Placeholder"

def parse_coordinates(coord_string):
    match = re.match(r'^\s*(-?\d+(?:\.\d+)?)\s*[,;]\s*(-?\d+(?:\.\d+)?)\s*$', coord_string.strip())
    if match:
        return float(match.group(1)), float(match.group(2))
    return None, None

def map_input_component(token, label, default_lat=14.5995, default_lng=120.9842):
    """Map input component"""
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
            f'<div class="map-saved-indicator">✅ Location: {st.session_state[map_key]["lat"]:.6f}, {st.session_state[map_key]["lng"]:.6f}</div>',
            unsafe_allow_html=True
        )
        if st.session_state[map_key]["screenshot"]:
            st.image(st.session_state[map_key]["screenshot"], width=250)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("🗺️ Open Map Editor", key=f"open_{token}", use_container_width=True):
            st.session_state[map_key]["open"] = not st.session_state[map_key].get("open", False)
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear", key=f"clear_{token}", use_container_width=True):
            st.session_state[map_key]["saved"] = False
            st.session_state[map_key]["screenshot"] = None
            st.rerun()
    
    if st.session_state[map_key].get("open", False):
        with st.expander("📍 Map Editor", expanded=True):
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
                    height=400,
                    tiles=tile_url
                )
                folium.Marker(
                    [st.session_state[map_key]["lat"], st.session_state[map_key]["lng"]],
                    draggable=True
                ).add_to(m)
                folium_static(m, width=700, height=400)
            except:
                st.info("Map display limited. Enter coordinates manually.")
            
            if st.button("📷 Capture Map", key=f"capture_{token}", use_container_width=True):
                with st.spinner("Capturing..."):
                    result, method = capture_map(
                        st.session_state[map_key]["lat"],
                        st.session_state[map_key]["lng"],
                        basemap,
                        zoom
                    )
                    if result:
                        st.session_state[map_key]["screenshot"] = result
                        st.session_state[map_key]["saved"] = True
                        st.success(f"✅ Captured via: {method}")
                        st.rerun()
    
    if st.session_state[map_key]["saved"] and st.session_state[map_key]["screenshot"]:
        return st.session_state[map_key]["screenshot"]
    return None

# --- MAIN APP ---
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
if "github_connected" not in st.session_state:
    st.session_state.github_connected = None

# Check GitHub connection
if st.session_state.github_connected is None:
    token = get_github_token()
    if token:
        try:
            g = Github(token)
            g.get_user().login
            st.session_state.github_connected = True
        except:
            st.session_state.github_connected = False
    else:
        st.session_state.github_connected = False

# --- MAIN UI ---
st.markdown("<hr>", unsafe_allow_html=True)

# Header with GitHub status
col_header, col_status = st.columns([2, 1])
with col_header:
    st.markdown('<div class="section-header">📄 OpenFlux - Template Automation</div>', unsafe_allow_html=True)
with col_status:
    if st.session_state.github_connected:
        st.markdown('<div class="github-status success">✅ Connected to GitHub</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="github-status error">❌ Not connected to GitHub</div>', unsafe_allow_html=True)
        st.caption("Please set GITHUB_TOKEN in .streamlit/secrets.toml")

# --- TEMPLATE MANAGEMENT ---
st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
st.markdown('<div class="section-header">📁 Template Management</div>', unsafe_allow_html=True)

col_template1, col_template2 = st.columns(2)

with col_template1:
    templates = get_all_templates()
    template_options = ["Select a template"]
    for t in templates:
        source = " (GitHub)" if t.get('source') == 'github' else ""
        template_options.append(f"{t['name']} ({t['type']}){source}")
    
    selected_template = st.selectbox(
        "Load Template",
        template_options,
        key="template_select",
        label_visibility="collapsed"
    )
    
    if selected_template and selected_template != "Select a template":
        # Extract name
        name_parts = selected_template.split(' (')
        template_name = name_parts[0]
        is_github = "(GitHub)" in selected_template
        
        # Load template
        if is_github:
            template_bytes = download_from_github(template_name)
        else:
            template_bytes = load_template_local(template_name)
        
        if template_bytes:
            st.session_state.template_bytes = template_bytes
            st.session_state.saved_template_name = template_name
            st.session_state.template_loaded = True
            st.session_state.template_type = 'pptx' if template_name.endswith('.pptx') else 'docx'
            
            # Load config if exists
            config = download_config_from_github(template_name)
            if config:
                st.session_state.custom_mapping = config
            else:
                st.session_state.custom_mapping = {}
            
            # Extract placeholders
            tokens = extract_placeholders(template_bytes, st.session_state.template_type)
            st.session_state.tokens = tokens
            st.success(f"✅ Loaded: {template_name}")
    
    # Delete option
    if selected_template and selected_template != "Select a template":
        template_name = selected_template.split(' (')[0]
        if st.button("🗑️ Delete Template", key="delete_btn", use_container_width=True):
            st.session_state.show_delete_confirm = True
            st.session_state.template_to_delete = template_name
            st.rerun()
    
    if st.session_state.show_delete_confirm:
        st.warning(f"Are you sure you want to delete '{st.session_state.template_to_delete}'?")
        col_yes, col_no = st.columns([1, 1])
        with col_yes:
            if st.button("Yes, Delete", key="confirm_delete"):
                if delete_template(st.session_state.template_to_delete):
                    st.session_state.template_bytes = None
                    st.session_state.saved_template_name = None
                    st.session_state.template_loaded = False
                    st.session_state.tokens = []
                    st.session_state.show_delete_confirm = False
                    st.success(f"✅ Deleted: {st.session_state.template_to_delete}")
                    st.rerun()
        with col_no:
            if st.button("Cancel", key="cancel_delete"):
                st.session_state.show_delete_confirm = False
                st.rerun()

with col_template2:
    uploaded_template = st.file_uploader(
        "Upload New Template",
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
        
        if st.button("💾 Save to GitHub", key="save_github_btn", use_container_width=True):
            # Save locally
            save_template_local(template_bytes, template_name)
            # Upload to GitHub
            if upload_to_github(template_bytes, template_name):
                # Upload config
                if st.session_state.custom_mapping:
                    upload_config_to_github(st.session_state.custom_mapping, template_name)
                st.session_state.saved_template_name = template_name
                st.session_state.save_success = True
                st.session_state.saved_file_name = template_name
                st.success(f"✅ Template saved to GitHub: {template_name}")
                st.rerun()
            else:
                st.error("❌ Failed to save to GitHub")

if st.session_state.save_success:
    st.success(f"✅ Template '{st.session_state.saved_file_name}' saved successfully!")
    st.session_state.save_success = False
    st.session_state.saved_file_name = None

if st.session_state.template_bytes:
    template_name = st.session_state.saved_template_name or "Unsaved Template"
    template_type = st.session_state.template_type or "Unknown"
    st.markdown(f'<div class="saved-indicator">📌 Active: {template_name} ({template_type.upper()})</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- PLACEHOLDER VALUES ---
template_bytes = st.session_state.template_bytes
template_type = st.session_state.template_type

if template_bytes and st.session_state.tokens:
    st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">🔧 Placeholder Values</div>', unsafe_allow_html=True)
    
    tokens = st.session_state.tokens
    text_data = {}
    image_data = {}
    
    # Split tokens into two columns
    mid = len(tokens) // 2
    col1, col2 = st.columns(2)
    
    for idx, token in enumerate(tokens):
        clean_label = token.replace("{", "").replace("}", "")
        current_type = st.session_state.custom_mapping.get(token, "Text")
        
        col_a, col_b = st.columns([3, 1])
        
        with col_b:
            dtype = st.selectbox(
                "Type",
                ["Text", "Image", "Map"],
                index=["Text", "Image", "Map"].index(current_type),
                key=f"type_{token}",
                label_visibility="collapsed"
            )
            if dtype != current_type:
                st.session_state.custom_mapping[token] = dtype
                # Auto-save config to GitHub
                if st.session_state.saved_template_name:
                    upload_config_to_github(st.session_state.custom_mapping, st.session_state.saved_template_name)
        
        with col_a:
            if dtype == "Image" and template_type == 'pptx':
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

# --- DOWNLOAD SECTION ---
if template_bytes:
    st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">📥 Download Document</div>', unsafe_allow_html=True)
    
    # Merge map screenshots into image_data
    for token, map_img in st.session_state.map_data.items():
        if map_img:
            image_data[token] = map_img
    
    template_name = st.session_state.saved_template_name or "Generated_Document"
    base_name = re.sub(r'\.(pptx|docx)$', '', template_name)
    
    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        if template_type == 'pptx':
            try:
                pptx_data = generate_pptx_bytes(template_bytes, text_data, image_data)
                filename = get_download_filename(base_name, "pptx")
                st.download_button(
                    label="📊 Download PPTX",
                    data=pptx_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.button("📊 Download PPTX", disabled=True, use_container_width=True, help="Only for PPTX templates")
    
    with col_dl2:
        if template_type == 'docx':
            try:
                docx_data = generate_docx_bytes(template_bytes, text_data, image_data)
                filename = get_download_filename(base_name, "docx")
                st.download_button(
                    label="📄 Download DOCX",
                    data=docx_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.button("📄 Download DOCX", disabled=True, use_container_width=True, help="Only for DOCX templates")
    
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("📌 Please upload or select a template to begin")

st.markdown("---")
st.caption("")
