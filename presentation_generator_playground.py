import os
import io
import subprocess
import tempfile
import re
import json
import streamlit as st
from pptx import Presentation
from pptx.util import Pt
from PIL import Image
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt as DocxPt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import base64
import traceback

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
    /* Hide Streamlit top bar */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { margin-top: -50px; }
    .stDeployButton {display: none;}
    .stStatusWidget {display: none;}
    
    .stApp { background-color: #FFFFFF !important; color: #1A1A1A !important; font-family: 'Segoe UI', Arial, sans-serif !important; }
    div[data-testid="stHeader"] { background-color: #FFFFFF !important; display: none !important; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; max-width: 1200px !important; }
    
    /* Inputs */
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[role="textbox"], div[data-baseweb="select"], textarea {
        background-color: #FFFFFF !important; border: 1px solid #CCCCCC !important; border-radius: 4px !important;
        color: #1A1A1A !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within, textarea:focus { border-color: #003366 !important; box-shadow: none !important; }
    input[type="text"], .stTextInput input, div[data-baseweb="select"] div, textarea { color: #1A1A1A !important; font-size: 14px !important; }
    
    /* Make select boxes and dropdown icons smaller */
    div[data-baseweb="select"] { min-height: 32px !important; }
    div[data-baseweb="select"] > div { min-height: 32px !important; padding: 0 8px !important; }
    div[data-baseweb="select"] select { font-size: 13px !important; padding: 2px 8px !important; }
    svg[data-testid="stSelectbox"] { width: 16px !important; height: 16px !important; }
    div[data-baseweb="select"] svg { width: 16px !important; height: 16px !important; }
    
    /* File Uploader */
    section[data-testid="stFileUploader"] { background-color: #F8F8F8 !important; border: 1px solid #CCCCCC !important; border-radius: 4px !important; padding: 4px 12px !important; }
    
    /* Cards */
    .workspace-card { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 4px; padding: 16px; margin-bottom: 12px; }
    
    /* Buttons - #003366 color - made smaller */
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
    
    /* Download Buttons - #003366 color - made smaller */
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
    
    /* Delete button - made smaller */
    div[data-testid="column"] button { 
        background-color: transparent !important; 
        color: #DC3545 !important; 
        border: 1px solid #DC3545 !important; 
        border-radius: 3px !important; 
        padding: 3px 10px !important; 
        font-size: 11px !important; 
        min-height: 26px !important; 
        width: auto !important; 
    }
    div[data-testid="column"] button:hover { 
        background-color: #DC3545 !important; 
        color: white !important; 
    }
    
    /* Labels */
    .field-label { font-size: 13px !important; font-weight: 600 !important; color: #1A1A1A !important; padding-top: 6px; }
    .section-header { font-size: 15px !important; font-weight: 700 !important; color: #1A1A1A !important; margin-bottom: 10px; }
    .saved-indicator { background-color: #E8F5E9; padding: 6px 12px; border-radius: 4px; font-size: 13px; color: #2E7D32; border-left: 3px solid #2E7D32; margin-top: 6px; }
    
    hr { margin: 12px 0 !important; border-color: #E0E0E0 !important; }
    
    /* Expander */
    .streamlit-expanderHeader { font-size: 14px !important; font-weight: 600 !important; }
    
    /* Table row styling */
    .table-row { 
        background-color: #F8F9FA; 
        padding: 8px; 
        border-radius: 4px; 
        margin-bottom: 8px; 
        border: 1px solid #E0E0E0;
    }
    .row-number {
        font-weight: 600;
        color: #003366;
        padding-right: 10px;
        font-size: 13px;
    }
</style>
"""

# --- FILE MANAGEMENT FUNCTIONS ---
def get_root_templates():
    """Scan root directory for files starting with 'template_'"""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    templates = []
    
    for file in os.listdir(root_dir):
        if file.startswith('template_') and (file.endswith('.pptx') or file.endswith('.docx')):
            # Extract display name (remove 'template_' prefix and extension)
            display_name = file.replace('template_', '')
            display_name = re.sub(r'\.(pptx|docx)$', '', display_name)
            templates.append({
                'name': display_name,
                'file': file,
                'type': 'PPTX' if file.endswith('.pptx') else 'DOCX',
                'source': 'root',
                'path': os.path.join(root_dir, file)
            })
    
    return templates

def load_template_from_root(template_file):
    """Load template from root directory"""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(root_dir, template_file)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            return f.read()
    return None

def get_storage_dir():
    """Get the directory for storing templates and configs"""
    storage_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stored_templates")
    os.makedirs(storage_dir, exist_ok=True)
    return storage_dir

def save_template_to_file(template_bytes, template_name):
    """Save template to file system"""
    storage_dir = get_storage_dir()
    safe_name = re.sub(r'[^\w\-_. ]', '_', template_name)
    if not safe_name.endswith('.pptx') and not safe_name.endswith('.docx'):
        safe_name += '.docx'
    
    filepath = os.path.join(storage_dir, safe_name)
    with open(filepath, 'wb') as f:
        f.write(template_bytes)
    return filepath

def load_template_from_file(template_name):
    """Load template from file system"""
    storage_dir = get_storage_dir()
    filepath = os.path.join(storage_dir, template_name)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            return f.read()
    return None

def get_saved_templates():
    """Get list of saved templates (user uploaded + root templates)"""
    templates = []
    
    # Get root templates (template_*.pptx/docx)
    root_templates = get_root_templates()
    for t in root_templates:
        templates.append({
            'name': t['name'],
            'file': t['file'],
            'type': t['type'],
            'source': 'root',
            'display': f"{t['name']} (root)"
        })
    
    # Get user uploaded templates
    storage_dir = get_storage_dir()
    if os.path.exists(storage_dir):
        for file in os.listdir(storage_dir):
            if file.endswith('.pptx') or file.endswith('.docx'):
                filepath = os.path.join(storage_dir, file)
                stat = os.stat(filepath)
                templates.append({
                    'name': file,
                    'path': filepath,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'PPTX' if file.endswith('.pptx') else 'DOCX',
                    'source': 'user',
                    'display': f"{file} (uploaded)"
                })
    
    return templates

def delete_template_file(template_name):
    """Delete a saved template (user uploaded only)"""
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
    """Save configuration to file"""
    storage_dir = get_storage_dir()
    filepath = os.path.join(storage_dir, config_name)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4)
    return filepath

def load_config_from_file(config_name="template_config.json"):
    """Load configuration from file"""
    storage_dir = get_storage_dir()
    filepath = os.path.join(storage_dir, config_name)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def auto_save_config():
    """Automatically save the current configuration"""
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
    """Replace text in a paragraph while preserving formatting"""
    # First pass: replace in runs
    for run in paragraph.runs:
        for token, value in text_inputs.items():
            if token in run.text:
                # Replace with empty string if value is None or empty
                replacement = str(value) if value else ''
                run.text = run.text.replace(token, replacement)
    
    # Second pass: handle text that might not be in runs
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
    """Generate DOCX with text replacements"""
    doc = Document(io.BytesIO(template_bytes))
    
    # Process regular paragraphs
    for paragraph in doc.paragraphs:
        # Check for image placeholders - skip them for text replacement
        has_image = False
        for img_token in image_inputs.keys():
            if img_token in paragraph.text:
                has_image = True
                break
        
        # Only replace text if no image placeholder is present
        if not has_image:
            replace_text_in_paragraph(paragraph, text_inputs)
    
    # Process tables
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
    """Generate download filename based on template name"""
    if template_name:
        # Remove the extension if present
        base_name = re.sub(r'\.(pptx|docx)$', '', template_name)
        # Clean up the name
        base_name = re.sub(r'[^\w\-_. ]', '_', base_name)
        # Add timestamp to avoid overwriting
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{base_name}_{timestamp}.{file_type}"
    else:
        # Default name if no template name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"Generated_Document_{timestamp}.{file_type}"

# --- UI HELPERS ---
def simple_uploader_row(label_text, allowed_types, key):
    st.markdown(f'<div class="field-label">{label_text}</div>', unsafe_allow_html=True)
    return st.file_uploader(label_text, type=allowed_types, key=f"val_{key}", label_visibility="collapsed")

# --- INIT APP ---
st.set_page_config(page_title="OpenFlux", layout="wide", initial_sidebar_state="collapsed")
st.markdown(MINIMAL_CRE_SYSTEM, unsafe_allow_html=True)

# Initialize all session state variables
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

# --- MAIN LAYOUT ---
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
            if t.get('source') == 'root':
                template_options.append(f"{t['name']} (root)")
            else:
                template_options.append(f"{t['name']} ({t['type']})")
    
    dropdown_col, delete_col = st.columns([4, 1])
    
    with dropdown_col:
        selected_template = st.selectbox(
            "Load Template",
            template_options,
            key="saved_template_select",
            label_visibility="collapsed"
        )
    
    with delete_col:
        if selected_template and selected_template != "Select saved template":
            # Only show delete for user uploaded templates
            is_root = "(root)" in selected_template
            if not is_root:
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
                    st.success(f"Deleted: {st.session_state.template_to_delete}")
                    st.rerun()
        with col_confirm2:
            if st.button("Cancel", key="cancel_delete"):
                st.session_state.show_delete_confirm = False
                st.session_state.template_to_delete = None
                st.rerun()
    
    if selected_template and selected_template != "Select saved template" and not st.session_state.delete_trigger:
        is_root = "(root)" in selected_template
        template_name = selected_template.split(' (')[0]
        template_bytes = None
        
        if is_root:
            # Load from root directory
            root_templates = get_root_templates()
            for t in root_templates:
                if t['name'] == template_name:
                    template_bytes = load_template_from_root(t['file'])
                    st.session_state.template_type = 'pptx' if t['type'] == 'PPTX' else 'docx'
                    break
        else:
            # Load from user storage
            template_bytes = load_template_from_file(template_name)
            st.session_state.template_type = 'pptx' if template_name.endswith('.pptx') else 'docx'
        
        if template_bytes:
            st.session_state.template_bytes = template_bytes
            st.session_state.saved_template_name = template_name
            st.session_state.template_loaded = True
            
            config_name = template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
            config_data = load_config_from_file(config_name)
            if config_data:
                st.session_state.custom_mapping = config_data
            
            # Simply extract all placeholders - no auto-detection
            tokens = extract_placeholders(template_bytes, st.session_state.template_type)
            st.session_state.tokens = tokens

with col_template2:
    uploader_key = "new_template_upload_clear" if st.session_state.clear_uploader else "new_template_upload"
    
    uploaded_template = st.file_uploader(
        "Upload New Template", 
        type=["pptx", "docx"], 
        label_visibility="collapsed", 
        key=uploader_key
    )
    
    if st.session_state.clear_uploader:
        st.session_state.clear_uploader = False
    
    if uploaded_template:
        template_bytes = uploaded_template.getvalue()
        st.session_state.template_bytes = template_bytes
        st.session_state.saved_template_name = None
        st.session_state.template_loaded = True
        st.session_state.template_type = 'pptx' if uploaded_template.name.endswith('.pptx') else 'docx'
        
        # Simply extract all placeholders - no auto-detection
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
    st.success(f"Template '{st.session_state.saved_file_name}' saved successfully! Refresh the page to see it in the dropdown.")
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
        
        # Split tokens into two columns
        mid_point = len(tokens) // 2
        col1, col2 = st.columns(2)
        
        with col1:
            for token in tokens[:mid_point]:
                clean_label = token.replace("{", "").replace("}", "")
                
                current_type = st.session_state.custom_mapping.get(token, "Text")
                col_a, col_b = st.columns([3, 1])
                
                with col_b:
                    st.markdown('<div style="padding-top: 6px;"></div>', unsafe_allow_html=True)
                    type_key = f"type_{token}"
                    data_type = st.selectbox(
                        "Type",
                        ["Text", "Image"],
                        index=0 if current_type == "Text" else 1,
                        key=type_key,
                        label_visibility="collapsed"
                    )
                    if data_type != current_type:
                        st.session_state.custom_mapping[token] = data_type
                        auto_save_config()
                        st.rerun()
                
                with col_a:
                    if data_type == "Image" and template_type == 'pptx':
                        image_data[token] = simple_uploader_row(clean_label, ["png", "jpg", "jpeg"], token)
                        field_types[token] = "Image"
                        st.caption("Upload image (PNG, JPG)")
                    else:
                        if data_type == "Image" and template_type != 'pptx':
                            st.warning("Image replacement only supported in PPTX templates")
                        st.markdown(f'<div class="field-label">{clean_label}</div>', unsafe_allow_html=True)
                        text_data[token] = st.text_input(
                            clean_label, 
                            key=f"val_{token}", 
                            label_visibility="collapsed"
                        )
                        field_types[token] = "Text"
        
        with col2:
            for token in tokens[mid_point:]:
                clean_label = token.replace("{", "").replace("}", "")
                
                current_type = st.session_state.custom_mapping.get(token, "Text")
                col_a, col_b = st.columns([3, 1])
                
                with col_b:
                    st.markdown('<div style="padding-top: 6px;"></div>', unsafe_allow_html=True)
                    type_key = f"type_{token}_2"
                    data_type = st.selectbox(
                        "Type",
                        ["Text", "Image"],
                        index=0 if current_type == "Text" else 1,
                        key=type_key,
                        label_visibility="collapsed"
                    )
                    if data_type != current_type:
                        st.session_state.custom_mapping[token] = data_type
                        auto_save_config()
                        st.rerun()
                
                with col_a:
                    if data_type == "Image" and template_type == 'pptx':
                        image_data[token] = simple_uploader_row(clean_label, ["png", "jpg", "jpeg"], token)
                        field_types[token] = "Image"
                        st.caption("Upload image (PNG, JPG)")
                    else:
                        if data_type == "Image" and template_type != 'pptx':
                            st.warning("Image replacement only supported in PPTX templates")
                        st.markdown(f'<div class="field-label">{clean_label}</div>', unsafe_allow_html=True)
                        text_data[token] = st.text_input(
                            clean_label, 
                            key=f"val_{token}", 
                            label_visibility="collapsed"
                        )
                        field_types[token] = "Text"
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- DOWNLOAD SECTION ---
if u_template is not None:
    st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Download Document</div>', unsafe_allow_html=True)
    
    # Get template name for file naming
    template_name = st.session_state.saved_template_name or "Generated_Document"
    # Remove extension for clean name
    base_template_name = re.sub(r'\.(pptx|docx)$', '', template_name)
    
    col1, col2 = st.columns(2)
    
    with col1:
        pptx_disabled = template_type != 'pptx'
        if pptx_disabled:
            st.button("Download PPTX", disabled=True, use_container_width=True, help="Only available for PPTX templates")
        else:
            try:
                pptx_data = generate_pptx_bytes(template_bytes, text_data, image_data)
                pptx_filename = get_download_filename(base_template_name, "pptx")
                st.download_button(
                    label="Download PPTX",
                    data=pptx_data,
                    file_name=pptx_filename,
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True,
                    key="download_pptx"
                )
            except Exception as e:
                st.error(f"Error generating PPTX: {str(e)}")
    
    with col2:
        docx_disabled = template_type != 'docx'
        if docx_disabled:
            st.button("Download DOCX", disabled=True, use_container_width=True, help="Only available for DOCX templates")
        else:
            # Generate the document data
            try:
                docx_data = generate_docx_bytes(template_bytes, text_data, image_data)
                
                if docx_data:
                    docx_filename = get_download_filename(base_template_name, "docx")
                    st.download_button(
                        label="Download DOCX",
                        data=docx_data,
                        file_name=docx_filename,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                        key="download_docx"
                    )
                else:
                    st.error("Failed to generate document. Please check the template and try again.")
            except Exception as e:
                st.error(f"Error generating document: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Please upload or select a template to begin")
