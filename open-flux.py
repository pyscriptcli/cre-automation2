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
    .stDeployButton {display: none;}
    .stApp > header {display: none !important;}
    .stApp > header + div {padding-top: 0 !important;}
    
    /* Hide the "Manage app" button */
    .stApp > div:last-child button {display: none !important;}
    
    .stApp { background-color: #FFFFFF !important; color: #1A1A1A !important; font-family: 'Segoe UI', Arial, sans-serif !important; }
    div[data-testid="stHeader"] { background-color: #FFFFFF !important; display: none !important; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; max-width: 1200px !important; }
    
    /* Inputs */
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[role="textbox"], div[data-baseweb="select"], textarea {
        background-color: #FFFFFF !important; border: 1px solid #CCCCCC !important; border-radius: 4px !important;
        color: #1A1A1A !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within, textarea:focus { border-color: #666666 !important; box-shadow: none !important; }
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
    .config-card { background-color: #F8F8F8; border: 1px solid #E0E0E0; border-radius: 4px; padding: 16px; margin-bottom: 12px; }
    
    /* Buttons */
    div.stButton > button { background-color: #1A1A1A !important; color: #FFFFFF !important; font-weight: 600 !important; font-size: 14px !important; border: none !important; border-radius: 4px !important; padding: 8px 16px !important; width: 100% !important; transition: background-color 0.15s ease; }
    div.stButton > button:hover { background-color: #333333 !important; color: #FFFFFF !important; }
    div.stButton > button:disabled { background-color: #666666 !important; color: #CCCCCC !important; cursor: not-allowed !important; }
    
    div[data-testid="stDownloadButton"] > button { background-color: #1A1A1A !important; border-radius: 4px !important; color: #FFFFFF !important; font-weight: 600 !important; padding: 8px 16px !important; width: 100% !important; }
    div[data-testid="stDownloadButton"] > button:hover { background-color: #333333 !important; }
    
    /* Delete button */
    div[data-testid="column"] button { background-color: transparent !important; color: #DC3545 !important; border: 1px solid #DC3545 !important; border-radius: 4px !important; padding: 4px 12px !important; font-size: 13px !important; min-height: 32px !important; width: auto !important; }
    div[data-testid="column"] button:hover { background-color: #DC3545 !important; color: white !important; }
    
    /* Labels */
    .field-label { font-size: 13px !important; font-weight: 600 !important; color: #1A1A1A !important; padding-top: 6px; }
    .section-header { font-size: 15px !important; font-weight: 700 !important; color: #1A1A1A !important; margin-bottom: 10px; }
    .saved-indicator { background-color: #E8F5E9; padding: 6px 12px; border-radius: 4px; font-size: 13px; color: #2E7D32; border-left: 3px solid #2E7D32; margin-top: 6px; }
    
    hr { margin: 12px 0 !important; border-color: #E0E0E0 !important; }
    
    /* Template row with delete button */
    .template-row { display: flex; gap: 8px; align-items: center; }
    .template-select { flex: 1; }
    
    /* Expander */
    .streamlit-expanderHeader { font-size: 14px !important; font-weight: 600 !important; }
    
    /* Loading overlay */
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.9);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        flex-direction: column;
    }
    .loading-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #1A1A1A;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .loading-text {
        margin-top: 20px;
        font-size: 16px;
        color: #1A1A1A;
        font-weight: 600;
    }
    
    /* Modal/Popup styling */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
        padding: 20px;
    }
    .modal-content {
        background: #FFFFFF;
        border-radius: 8px;
        padding: 30px;
        max-width: 500px;
        width: 100%;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        position: relative;
    }
    .modal-title {
        font-size: 20px;
        font-weight: 700;
        color: #1A1A1A;
        margin-bottom: 10px;
    }
    .modal-subtitle {
        font-size: 14px;
        color: #666;
        margin-bottom: 20px;
    }
    .modal-checkboxes {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin: 15px 0;
    }
    .modal-checkbox-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 12px;
        border: 1px solid #E0E0E0;
        border-radius: 4px;
        background: #FAFAFA;
    }
    .modal-checkbox-item input[type="checkbox"] {
        width: 18px;
        height: 18px;
        cursor: pointer;
    }
    .modal-checkbox-item label {
        font-size: 15px;
        font-weight: 500;
        color: #1A1A1A;
        cursor: pointer;
        flex: 1;
    }
    .modal-buttons {
        display: flex;
        gap: 10px;
        margin-top: 20px;
    }
    .modal-buttons .stButton > button {
        padding: 10px 20px !important;
        min-width: 120px;
    }
    .modal-buttons .stButton {
        flex: 1;
    }
    
    /* Custom checkbox styling for Streamlit */
    .stCheckbox {
        margin: 0 !important;
        padding: 0 !important;
    }
    .stCheckbox label {
        font-size: 15px !important;
        font-weight: 500 !important;
        color: #1A1A1A !important;
    }
    .stCheckbox > div {
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        padding: 10px 15px !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 4px !important;
        background: #FAFAFA !important;
        margin: 5px 0 !important;
    }
    
    /* Download buttons container */
    .download-buttons-container {
        display: flex;
        gap: 10px;
        margin-top: 10px;
        flex-wrap: wrap;
    }
    .download-buttons-container .stButton {
        flex: 1;
        min-width: 100px;
    }
    
    /* Hide the default Streamlit checkbox label */
    .stCheckbox label {
        display: flex !important;
        align-items: center !important;
    }
</style>
"""

# --- FILE MANAGEMENT FUNCTIONS ---
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
    """Get list of saved templates"""
    storage_dir = get_storage_dir()
    templates = []
    for file in os.listdir(storage_dir):
        if file.endswith('.pptx') or file.endswith('.docx'):
            filepath = os.path.join(storage_dir, file)
            stat = os.stat(filepath)
            templates.append({
                'name': file,
                'path': filepath,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'type': 'PPTX' if file.endswith('.pptx') else 'DOCX'
            })
    return templates

def delete_template_file(template_name):
    """Delete a saved template"""
    storage_dir = get_storage_dir()
    filepath = os.path.join(storage_dir, template_name)
    if os.path.exists(filepath):
        os.remove(filepath)
        # Also delete associated config
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

def convert_pptx_to_pdf(pptx_bytes):
    with tempfile.TemporaryDirectory() as temp_dir:
        input_pptx_path = os.path.join(temp_dir, "document.pptx")
        with open(input_pptx_path, "wb") as f:
            f.write(pptx_bytes)
        try:
            command = ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", temp_dir, input_pptx_path]
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output_pdf_path = os.path.join(temp_dir, "document.pdf")
            if os.path.exists(output_pdf_path):
                with open(output_pdf_path, "rb") as f:
                    return f.read()
        except Exception:
            return None
    return None

def convert_docx_to_pdf(docx_bytes):
    with tempfile.TemporaryDirectory() as temp_dir:
        input_docx_path = os.path.join(temp_dir, "document.docx")
        with open(input_docx_path, "wb") as f:
            f.write(docx_bytes)
        try:
            command = ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", temp_dir, input_docx_path]
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output_pdf_path = os.path.join(temp_dir, "document.pdf")
            if os.path.exists(output_pdf_path):
                with open(output_pdf_path, "rb") as f:
                    return f.read()
        except Exception:
            return None
    return None

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

def generate_pptx_bytes(template_bytes, text_inputs, image_inputs):
    prs = Presentation(io.BytesIO(template_bytes))
    
    for slide in prs.slides:
        shapes_to_delete = []
        images_to_add = []

        # First pass: collect image placeholders
        for shape in slide.shapes:
            if shape.has_text_frame:
                text_content = shape.text
                for img_token, img_file in image_inputs.items():
                    if img_token in text_content and img_file is not None:
                        images_to_add.append((img_file, shape.left, shape.top, shape.width, shape.height))
                        shapes_to_delete.append(shape)
                        break

        # Second pass: replace text while preserving formatting
        for shape in slide.shapes:
            if shape not in shapes_to_delete:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        for run in paragraph.runs:
                            for token, value in text_inputs.items():
                                if token in run.text:
                                    run.text = run.text.replace(token, str(value) if value else '')
                
                if hasattr(shape, 'table') and shape.table:
                    for row in shape.table.rows:
                        for cell in row.cells:
                            if cell.text_frame:
                                for paragraph in cell.text_frame.paragraphs:
                                    for run in paragraph.runs:
                                        for token, value in text_inputs.items():
                                            if token in run.text:
                                                run.text = run.text.replace(token, str(value) if value else '')

        # Add images
        for img_file, left, top, width, height in images_to_add:
            try:
                processed_img = smart_crop_to_fit(img_file, width, height)
                slide.shapes.add_picture(processed_img, left, top, width=width, height=height)
            except Exception:
                pass

        # Delete placeholder shapes after adding images
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
    
    # Replace text in paragraphs while preserving formatting
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            for token, value in text_inputs.items():
                if token in run.text:
                    run.text = run.text.replace(token, str(value) if value else '')
    
    # Replace text in tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        for token, value in text_inputs.items():
                            if token in run.text:
                                run.text = run.text.replace(token, str(value) if value else '')
    
    doc_stream = io.BytesIO()
    doc.save(doc_stream)
    doc_stream.seek(0)
    return doc_stream.getvalue()

# --- UI HELPERS ---
def simple_form_row_with_type(label_text, key, placeholder="", value=""):
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f'<div class="field-label">{label_text}</div>', unsafe_allow_html=True)
        result = st.text_input("", key=f"val_{key}", label_visibility="collapsed", placeholder=placeholder, value=value)
    with col2:
        st.markdown('<div style="padding-top: 6px;"></div>', unsafe_allow_html=True)
        data_type = st.selectbox(
            "Type",
            ["Text", "Image"],
            key=f"type_{key}",
            label_visibility="collapsed"
        )
    return result, data_type

def simple_textarea_row_with_type(label_text, key, placeholder="", value=""):
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f'<div class="field-label">{label_text}</div>', unsafe_allow_html=True)
        result = st.text_area("", key=f"val_{key}", label_visibility="collapsed", placeholder=placeholder, height=100, value=value)
    with col2:
        st.markdown('<div style="padding-top: 6px;"></div>', unsafe_allow_html=True)
        data_type = st.selectbox(
            "Type",
            ["Text", "Image"],
            key=f"type_{key}",
            label_visibility="collapsed"
        )
    return result, data_type

def simple_uploader_row(label_text, allowed_types, key):
    st.markdown(f'<div class="field-label">{label_text}</div>', unsafe_allow_html=True)
    return st.file_uploader(label_text, type=allowed_types, key=f"val_{key}", label_visibility="collapsed")

# --- INIT APP ---
st.set_page_config(page_title="Document Generator", layout="wide", initial_sidebar_state="collapsed")
st.markdown(MINIMAL_CRE_SYSTEM, unsafe_allow_html=True)

# Initialize all session state variables
if "final_pptx" not in st.session_state:
    st.session_state.final_pptx = None
if "final_docx" not in st.session_state:
    st.session_state.final_docx = None
if "final_pdf" not in st.session_state:
    st.session_state.final_pdf = None
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
if "config_expanded" not in st.session_state:
    st.session_state.config_expanded = False
if "generated" not in st.session_state:
    st.session_state.generated = False
if "is_loading" not in st.session_state:
    st.session_state.is_loading = False
if "show_file_selector" not in st.session_state:
    st.session_state.show_file_selector = False
if "generated_files" not in st.session_state:
    st.session_state.generated_files = {}
if "generation_complete" not in st.session_state:
    st.session_state.generation_complete = False
if "selected_formats" not in st.session_state:
    st.session_state.selected_formats = {"pptx": True, "pdf": True, "docx": True}

# --- MAIN LAYOUT ---
st.markdown("<hr style='margin: 4px 0 12px 0;'>", unsafe_allow_html=True)

# --- TEMPLATE MANAGEMENT SECTION ---
st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
st.markdown('<div class="section-header">Template</div>', unsafe_allow_html=True)

# Create row with dropdown and upload
col_template1, col_template2 = st.columns(2)

with col_template1:
    # Show saved templates dropdown with delete button
    saved_templates = get_saved_templates()
    template_options = ["Select saved template"]
    if saved_templates:
        for t in saved_templates:
            template_options.append(f"{t['name']} ({t['type']})")
    
    # Use columns for dropdown and delete button
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
            template_name = selected_template.split(' (')[0]
            if st.button("🗑️", key="delete_template", help="Delete this template"):
                # Use a confirmation dialog
                st.warning(f"Are you sure you want to delete '{template_name}'?")
                col_confirm1, col_confirm2 = st.columns(2)
                with col_confirm1:
                    if st.button("Yes, Delete", key="confirm_delete"):
                        if delete_template_file(template_name):
                            st.session_state.delete_trigger = True
                            st.session_state.template_bytes = None
                            st.session_state.saved_template_name = None
                            st.session_state.template_loaded = False
                            st.session_state.tokens = []
                            st.success(f"Deleted: {template_name}")
                            st.rerun()
                with col_confirm2:
                    if st.button("Cancel", key="cancel_delete"):
                        st.rerun()
    
    if selected_template and selected_template != "Select saved template" and not st.session_state.delete_trigger:
        template_name = selected_template.split(' (')[0]
        template_bytes = load_template_from_file(template_name)
        if template_bytes:
            st.session_state.template_bytes = template_bytes
            st.session_state.saved_template_name = template_name
            st.session_state.template_loaded = True
            st.session_state.template_type = 'pptx' if template_name.endswith('.pptx') else 'docx'
            
            # Load associated config
            config_name = template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
            config_data = load_config_from_file(config_name)
            if config_data:
                st.session_state.custom_mapping = config_data
            
            # Extract placeholders
            tokens = extract_placeholders(template_bytes, st.session_state.template_type)
            st.session_state.tokens = tokens

with col_template2:
    uploaded_template = st.file_uploader(
        "Upload New Template", 
        type=["pptx", "docx"], 
        label_visibility="collapsed", 
        key="new_template_upload"
    )
    
    if uploaded_template:
        template_bytes = uploaded_template.getvalue()
        st.session_state.template_bytes = template_bytes
        st.session_state.saved_template_name = None
        st.session_state.template_loaded = True
        st.session_state.template_type = 'pptx' if uploaded_template.name.endswith('.pptx') else 'docx'
        st.session_state.generated = False
        
        # Extract placeholders immediately
        tokens = extract_placeholders(template_bytes, st.session_state.template_type)
        st.session_state.tokens = tokens
        
        # Ask if user wants to save as template
        save_as_template = st.checkbox("Save as template for future use")
        
        if save_as_template:
            saved_path = save_template_to_file(template_bytes, uploaded_template.name)
            st.success(f"Template saved: {uploaded_template.name}")
            
            # Save config if exists
            if st.session_state.custom_mapping:
                config_name = uploaded_template.name.replace('.pptx', '').replace('.docx', '') + '_config.json'
                save_config_to_file(st.session_state.custom_mapping, config_name)
            st.rerun()

# Show current template info
if st.session_state.template_bytes is not None:
    template_name = st.session_state.saved_template_name or "Unsaved Template"
    template_type = st.session_state.template_type or "Unknown"
    st.markdown(f'<div class="saved-indicator">Active: {template_name} ({template_type.upper()})</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- Get current template bytes ---
template_bytes = st.session_state.template_bytes
template_type = st.session_state.template_type
u_template = None
if template_bytes is not None:
    u_template = type('obj', (object,), {'getvalue': lambda: template_bytes})()

text_data = {}
image_data = {}
field_types = {}

# --- DISPLAY FIELDS ---
if u_template is not None and st.session_state.tokens:
    tokens = st.session_state.tokens
    
    if not tokens:
        st.info("No placeholders found in the template.")
    else:
        # Distribute tokens evenly between two columns
        mid_point = len(tokens) // 2
        col1_tokens = tokens[:mid_point]
        col2_tokens = tokens[mid_point:]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Field Values</div>', unsafe_allow_html=True)
            for token in col1_tokens:
                clean_label = token.replace("{", "").replace("}", "")
                # Get the stored type or default to Text
                stored_type = st.session_state.custom_mapping.get(token, "Text")
                
                if stored_type == "Image" and template_type == 'pptx':
                    image_data[token] = simple_uploader_row(clean_label, ["png", "jpg", "jpeg"], token)
                    field_types[token] = "Image"
                else:
                    # For text fields, show text input with type selector
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.markdown(f'<div class="field-label">{clean_label}</div>', unsafe_allow_html=True)
                        text_data[token] = st.text_input("", key=f"val_{token}", label_visibility="collapsed")
                    with col_b:
                        st.markdown('<div style="padding-top: 6px;"></div>', unsafe_allow_html=True)
                        data_type = st.selectbox(
                            "Type",
                            ["Text", "Image"],
                            index=0 if stored_type == "Text" else 1,
                            key=f"type_{token}",
                            label_visibility="collapsed"
                        )
                        field_types[token] = data_type
                        # Update mapping
                        st.session_state.custom_mapping[token] = data_type
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Field Values</div>', unsafe_allow_html=True)
            for token in col2_tokens:
                clean_label = token.replace("{", "").replace("}", "")
                stored_type = st.session_state.custom_mapping.get(token, "Text")
                
                if stored_type == "Image" and template_type == 'pptx':
                    image_data[token] = simple_uploader_row(clean_label, ["png", "jpg", "jpeg"], token)
                    field_types[token] = "Image"
                else:
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.markdown(f'<div class="field-label">{clean_label}</div>', unsafe_allow_html=True)
                        text_data[token] = st.text_input("", key=f"val_{token}", label_visibility="collapsed")
                    with col_b:
                        st.markdown('<div style="padding-top: 6px;"></div>', unsafe_allow_html=True)
                        data_type = st.selectbox(
                            "Type",
                            ["Text", "Image"],
                            index=0 if stored_type == "Text" else 1,
                            key=f"type_{token}_2",
                            label_visibility="collapsed"
                        )
                        field_types[token] = data_type
                        st.session_state.custom_mapping[token] = data_type
            st.markdown('</div>', unsafe_allow_html=True)

# --- DATA MAPPING SECTION (Collapsible) ---
if u_template is not None and st.session_state.tokens:
    # Create expander for configuration
    with st.expander("⚙️ Configuration Settings", expanded=st.session_state.config_expanded):
        st.markdown('<div class="config-card">', unsafe_allow_html=True)
        
        # Save Configuration
        config_json_str = json.dumps(st.session_state.custom_mapping, indent=4)
        col_json1, col_json2 = st.columns([1, 1])
        with col_json1:
            config_filename = "template_config.json"
            if st.session_state.saved_template_name:
                config_filename = st.session_state.saved_template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
            
            st.download_button(
                label="Download Configuration",
                data=config_json_str,
                file_name=config_filename,
                mime="application/json",
                use_container_width=True
            )
        
        with col_json2:
            if st.session_state.saved_template_name:
                if st.button("Save Config with Template", use_container_width=True):
                    config_filename = st.session_state.saved_template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
                    save_config_to_file(st.session_state.custom_mapping, config_filename)
                    st.success(f"Config saved: {config_filename}")
            else:
                st.info("Save template first to persist config")
        
        # Load config
        st.markdown("<br>", unsafe_allow_html=True)
        u_json = st.file_uploader("Load Configuration", type=["json"], label_visibility="collapsed")
        if u_json is not None:
            try:
                loaded_config = json.load(u_json)
                st.session_state.custom_mapping.update(loaded_config)
                st.success("Configuration loaded")
                st.rerun()
            except Exception:
                st.error("Invalid JSON file")
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- GENERATION SECTION ---
if u_template is not None:
    st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Generate Document</div>', unsafe_allow_html=True)
    
    # Loading state
    if st.session_state.is_loading:
        st.markdown("""
        <div class="loading-overlay">
            <div class="loading-spinner"></div>
            <div class="loading-text">Generating document...</div>
        </div>
        """, unsafe_allow_html=True)
    
    # File type selection popup
    if st.session_state.show_file_selector:
        st.markdown("""
        <div class="modal-overlay">
            <div class="modal-content">
                <div class="modal-title">📋 Choose Output Format</div>
                <div class="modal-subtitle">Select the file types you want to generate:</div>
        """, unsafe_allow_html=True)
        
        # Custom styled checkboxes
        col1, col2, col3 = st.columns(3)
        with col1:
            st.session_state.selected_formats["pptx"] = st.checkbox(
                "📊 PPTX", 
                value=st.session_state.selected_formats.get("pptx", True),
                key="dl_pptx"
            )
        with col2:
            st.session_state.selected_formats["pdf"] = st.checkbox(
                "📄 PDF", 
                value=st.session_state.selected_formats.get("pdf", True),
                key="dl_pdf"
            )
        with col3:
            st.session_state.selected_formats["docx"] = st.checkbox(
                "📝 DOCX", 
                value=st.session_state.selected_formats.get("docx", True),
                key="dl_docx"
            )
        
        # Buttons
        col_btns1, col_btns2 = st.columns(2)
        with col_btns1:
            if st.button("✅ Generate Selected", key="generate_selected", use_container_width=True):
                # Check if at least one format is selected
                if any(st.session_state.selected_formats.values()):
                    st.session_state.show_file_selector = False
                    st.session_state.is_loading = True
                    st.session_state.generation_complete = False
                    st.rerun()
                else:
                    st.warning("Please select at least one format")
        
        with col_btns2:
            if st.button("❌ Cancel", key="cancel_generation", use_container_width=True):
                st.session_state.show_file_selector = False
                st.rerun()
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Generate button (disabled while loading)
    generate_disabled = st.session_state.is_loading or st.session_state.show_file_selector
    if st.button("🚀 Generate", use_container_width=True, disabled=generate_disabled):
        # Show the file selector popup
        st.session_state.show_file_selector = True
        st.rerun()
    
    # Actual generation happens here (after user selects file types)
    if st.session_state.is_loading and not st.session_state.generation_complete:
        with st.spinner("Generating document..."):
            try:
                generated_files = {}
                
                # Determine which files to generate based on user selection
                generate_pptx = st.session_state.selected_formats.get("pptx", False)
                generate_pdf = st.session_state.selected_formats.get("pdf", False)
                generate_docx = st.session_state.selected_formats.get("docx", False)
                
                # Generate based on template type
                if template_type == 'pptx':
                    # Always generate PPTX since it's the source
                    raw_pptx = generate_pptx_bytes(template_bytes, text_data, image_data)
                    generated_files['pptx'] = raw_pptx
                    
                    if generate_pdf:
                        pdf_bytes = convert_pptx_to_pdf(raw_pptx)
                        if pdf_bytes:
                            generated_files['pdf'] = pdf_bytes
                        else:
                            st.warning("PDF generation failed. LibreOffice might not be installed.")
                    
                    # For DOCX from PPTX - we'll note it's not available
                    if generate_docx:
                        st.warning("DOCX export from PPTX is not supported. Only PPTX and PDF are available for this template type.")
                        
                else:  # docx
                    # Always generate DOCX since it's the source
                    raw_docx = generate_docx_bytes(template_bytes, text_data, image_data)
                    generated_files['docx'] = raw_docx
                    
                    if generate_pdf:
                        pdf_bytes = convert_docx_to_pdf(raw_docx)
                        if pdf_bytes:
                            generated_files['pdf'] = pdf_bytes
                        else:
                            st.warning("PDF generation failed. LibreOffice might not be installed.")
                    
                    # For PPTX from DOCX - we'll note it's not available
                    if generate_pptx:
                        st.warning("PPTX export from DOCX is not supported. Only DOCX and PDF are available for this template type.")
                
                # Store generated files
                st.session_state.generated_files = generated_files
                
                # Store individual files for download buttons
                st.session_state.final_pptx = generated_files.get('pptx')
                st.session_state.final_pdf = generated_files.get('pdf')
                st.session_state.final_docx = generated_files.get('docx')
                
                st.session_state.generated = True
                st.session_state.generation_complete = True
                st.session_state.is_loading = False
                
                if generated_files:
                    st.success("✅ Document generated successfully!")
                else:
                    st.error("No files were generated. Please check your selections.")
                    
                st.rerun()
                
            except Exception as e:
                st.session_state.is_loading = False
                st.session_state.show_file_selector = False
                st.error(f"❌ Error: {str(e)}")
                st.rerun()
    
    # Show export buttons only after generation
    if st.session_state.generated and st.session_state.generation_complete:
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Determine which buttons to show based on what was generated
        available_formats = []
        if st.session_state.final_pptx:
            available_formats.append(('pptx', '📊 Download PPTX', 'Generated_Document.pptx', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'))
        if st.session_state.final_pdf:
            available_formats.append(('pdf', '📄 Download PDF', 'Generated_Document.pdf', 'application/pdf'))
        if st.session_state.final_docx:
            available_formats.append(('docx', '📝 Download DOCX', 'Generated_Document.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'))
        
        if available_formats:
            # Create columns for available formats
            cols = st.columns(len(available_formats))
            for idx, (format_key, label, filename, mime_type) in enumerate(available_formats):
                with cols[idx]:
                    data = None
                    if format_key == 'pptx':
                        data = st.session_state.final_pptx
                    elif format_key == 'pdf':
                        data = st.session_state.final_pdf
                    elif format_key == 'docx':
                        data = st.session_state.final_docx
                    
                    if data:
                        st.download_button(
                            label=label,
                            data=data,
                            file_name=filename,
                            mime=mime_type,
                            use_container_width=True
                        )
        
        # Reset button
        if st.button("🔄 Generate New", use_container_width=True):
            # Reset all generation-related states
            st.session_state.generated = False
            st.session_state.generation_complete = False
            st.session_state.generated_files = {}
            st.session_state.final_pptx = None
            st.session_state.final_pdf = None
            st.session_state.final_docx = None
            st.session_state.is_loading = False
            st.session_state.show_file_selector = False
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("📄 Please upload or select a template to begin")
