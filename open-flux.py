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
    .stApp { background-color: #FFFFFF !important; color: #1A1A1A !important; font-family: 'Segoe UI', Arial, sans-serif !important; }
    div[data-testid="stHeader"] { background-color: #FFFFFF !important; display: none !important; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; max-width: 1200px !important; padding-left: 1rem !important; padding-right: 1rem !important; }
    
    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }
    
    /* Title */
    .app-title { font-size: 24px; font-weight: 700; color: #1A1A1A; margin-bottom: 4px; letter-spacing: -0.5px; }
    .app-subtitle { font-size: 13px; color: #666; margin-bottom: 8px; }
    
    /* Inputs */
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[role="textbox"], div[data-baseweb="select"], textarea {
        background-color: #FFFFFF !important; border: 1px solid #CCCCCC !important; border-radius: 4px !important;
        color: #1A1A1A !important;
        min-height: 28px !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within, textarea:focus { border-color: #666666 !important; box-shadow: none !important; }
    input[type="text"], .stTextInput input, div[data-baseweb="select"] div, textarea { color: #1A1A1A !important; font-size: 13px !important; padding: 2px 8px !important; }
    
    /* Make select boxes and dropdown icons smaller */
    div[data-baseweb="select"] { min-height: 28px !important; }
    div[data-baseweb="select"] > div { min-height: 28px !important; padding: 0 6px !important; }
    div[data-baseweb="select"] select { font-size: 13px !important; padding: 2px 6px !important; }
    svg[data-testid="stSelectbox"] { width: 16px !important; height: 16px !important; }
    div[data-baseweb="select"] svg { width: 16px !important; height: 16px !important; }
    
    /* File Uploader */
    section[data-testid="stFileUploader"] { background-color: #F8F8F8 !important; border: 1px solid #CCCCCC !important; border-radius: 4px !important; padding: 2px 8px !important; }
    section[data-testid="stFileUploader"] button { padding: 2px 10px !important; font-size: 12px !important; }
    
    /* Cards */
    .workspace-card { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 4px; padding: 10px 12px; margin-bottom: 6px; }
    .config-card { background-color: #F8F8F8; border: 1px solid #E0E0E0; border-radius: 4px; padding: 10px 12px; margin-bottom: 6px; }
    
    /* Buttons */
    div.stButton > button { background-color: #1A1A1A !important; color: #FFFFFF !important; font-weight: 600 !important; font-size: 13px !important; border: none !important; border-radius: 4px !important; padding: 6px 14px !important; width: 100% !important; transition: background-color 0.15s ease; min-height: 32px !important; }
    div.stButton > button:hover { background-color: #333333 !important; color: #FFFFFF !important; }
    
    div[data-testid="stDownloadButton"] > button { background-color: #1A1A1A !important; border-radius: 4px !important; color: #FFFFFF !important; font-weight: 600 !important; padding: 6px 14px !important; width: 100% !important; font-size: 13px !important; min-height: 32px !important; }
    div[data-testid="stDownloadButton"] > button:hover { background-color: #333333 !important; }
    
    /* Delete button */
    div[data-testid="column"] button { background-color: #DC3545 !important; color: white !important; border: none !important; border-radius: 4px !important; padding: 4px 12px !important; font-size: 12px !important; min-height: 28px !important; width: auto !important; }
    div[data-testid="column"] button:hover { background-color: #C82333 !important; color: white !important; }
    
    /* Confirmation buttons */
    .confirm-yes button { background-color: #DC3545 !important; color: white !important; }
    .confirm-no button { background-color: #6C757D !important; color: white !important; }
    
    /* Labels */
    .field-label { font-size: 12px !important; font-weight: 600 !important; color: #1A1A1A !important; padding-top: 4px !important; margin-bottom: 2px !important; }
    .section-header { font-size: 13px !important; font-weight: 700 !important; color: #1A1A1A !important; margin-bottom: 6px !important; }
    .saved-indicator { background-color: #E8F5E9; padding: 3px 10px; border-radius: 4px; font-size: 12px; color: #2E7D32; border-left: 3px solid #2E7D32; margin-top: 4px; }
    .config-label { font-size: 12px !important; font-weight: 500 !important; color: #1A1A1A !important; padding-top: 4px !important; }
    
    hr { margin: 6px 0 !important; border-color: #E0E0E0 !important; }
    
    /* Compact spacing */
    .stSelectbox { margin-bottom: 2px !important; }
    .stSelectbox > div { min-height: 28px !important; }
    .stTextInput { margin-bottom: 2px !important; }
    .stTextArea { margin-bottom: 2px !important; }
    .stFileUploader { margin-bottom: 2px !important; }
    .stCheckbox { margin-bottom: 2px !important; }
    
    /* Compact columns */
    .row-widget.stColumns { gap: 8px !important; }
    div[data-testid="column"] { padding: 0 4px !important; }
    
    /* Expander */
    .streamlit-expanderHeader { font-size: 13px !important; font-weight: 600 !important; padding: 6px !important; }
    .streamlit-expanderContent { padding: 6px !important; }
    
    /* Loading spinner */
    .loading-container { display: flex; justify-content: center; align-items: center; padding: 20px; }
    .loading-text { font-size: 14px; color: #666; margin-left: 10px; }
    
    /* Info message */
    .stAlert { padding: 6px 12px !important; font-size: 12px !important; margin-bottom: 4px !important; }
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

def generate_pptx_bytes(template_bytes, text_inputs, image_inputs, config_settings):
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
                            
                            # Apply font settings if configured
                            if config_settings.get('font_size'):
                                run.font.size = Pt(config_settings['font_size'])
                    
                    # Apply alignment if configured
                    if config_settings.get('text_alignment'):
                        align_map = {
                            'Left': 1,
                            'Center': 2,
                            'Right': 3
                        }
                        if config_settings['text_alignment'] in align_map:
                            paragraph.alignment = align_map[config_settings['text_alignment']]
                
                if hasattr(shape, 'table') and shape.table:
                    for row in shape.table.rows:
                        for cell in row.cells:
                            if cell.text_frame:
                                for paragraph in cell.text_frame.paragraphs:
                                    for run in paragraph.runs:
                                        for token, value in text_inputs.items():
                                            if token in run.text:
                                                run.text = run.text.replace(token, str(value) if value else '')
                                        
                                        if config_settings.get('font_size'):
                                            run.font.size = Pt(config_settings['font_size'])
                                    
                                    if config_settings.get('text_alignment'):
                                        align_map = {
                                            'Left': 1,
                                            'Center': 2,
                                            'Right': 3
                                        }
                                        if config_settings['text_alignment'] in align_map:
                                            paragraph.alignment = align_map[config_settings['text_alignment']]

        # Add images with fit settings
        for img_file, left, top, width, height in images_to_add:
            try:
                if config_settings.get('image_fit') == 'Crop':
                    processed_img = smart_crop_to_fit(img_file, width, height)
                    slide.shapes.add_picture(processed_img, left, top, width=width, height=height)
                else:  # Fill or Stretch
                    slide.shapes.add_picture(img_file, left, top, width=width, height=height)
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

def generate_docx_bytes(template_bytes, text_inputs, image_inputs, config_settings):
    doc = Document(io.BytesIO(template_bytes))
    
    # Replace text in paragraphs while preserving formatting
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            for token, value in text_inputs.items():
                if token in run.text:
                    run.text = run.text.replace(token, str(value) if value else '')
            
            # Apply font settings
            if config_settings.get('font_size'):
                run.font.size = DocxPt(config_settings['font_size'])
        
        # Apply alignment
        if config_settings.get('text_alignment'):
            align_map = {
                'Left': WD_ALIGN_PARAGRAPH.LEFT,
                'Center': WD_ALIGN_PARAGRAPH.CENTER,
                'Right': WD_ALIGN_PARAGRAPH.RIGHT
            }
            if config_settings['text_alignment'] in align_map:
                paragraph.alignment = align_map[config_settings['text_alignment']]
    
    # Replace text in tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        for token, value in text_inputs.items():
                            if token in run.text:
                                run.text = run.text.replace(token, str(value) if value else '')
                        
                        if config_settings.get('font_size'):
                            run.font.size = DocxPt(config_settings['font_size'])
                    
                    if config_settings.get('text_alignment'):
                        align_map = {
                            'Left': WD_ALIGN_PARAGRAPH.LEFT,
                            'Center': WD_ALIGN_PARAGRAPH.CENTER,
                            'Right': WD_ALIGN_PARAGRAPH.RIGHT
                        }
                        if config_settings['text_alignment'] in align_map:
                            paragraph.alignment = align_map[config_settings['text_alignment']]
    
    doc_stream = io.BytesIO()
    doc.save(doc_stream)
    doc_stream.seek(0)
    return doc_stream.getvalue()

# --- UI HELPERS ---
def field_with_type(label_text, token):
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f'<div class="field-label">{label_text}</div>', unsafe_allow_html=True)
        val = st.text_input("", key=f"val_{token}", label_visibility="collapsed")
    with col2:
        st.markdown('<div style="padding-top: 4px;"></div>', unsafe_allow_html=True)
        data_type = st.selectbox(
            "Type",
            ["Text", "Image"],
            key=f"type_{token}",
            label_visibility="collapsed"
        )
    return val, data_type

def upload_row(label_text, token):
    st.markdown(f'<div class="field-label">{label_text}</div>', unsafe_allow_html=True)
    return st.file_uploader("", type=["png", "jpg", "jpeg"], key=f"val_{token}", label_visibility="collapsed")

# --- INIT APP ---
st.set_page_config(page_title="OpenFlux", layout="wide")
st.markdown(MINIMAL_CRE_SYSTEM, unsafe_allow_html=True)

# Title
st.markdown('<div class="app-title">OpenFlux</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Document Automation Platform</div>', unsafe_allow_html=True)

# Initialize session state
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
if "generated" not in st.session_state:
    st.session_state.generated = False
if "generating" not in st.session_state:
    st.session_state.generating = False
if "config_settings" not in st.session_state:
    st.session_state.config_settings = {
        'font_size': 12,
        'font_style': 'Arial',
        'text_alignment': 'Left',
        'image_fit': 'Crop'
    }
if "show_delete_confirm" not in st.session_state:
    st.session_state.show_delete_confirm = False
if "template_to_delete" not in st.session_state:
    st.session_state.template_to_delete = None

# --- TEMPLATE MANAGEMENT ---
st.markdown('<div class="workspace-card">', unsafe_allow_html=True)

# Template dropdown and upload in one row
col1, col2, col3 = st.columns([3, 0.8, 0.5])

with col1:
    saved_templates = get_saved_templates()
    template_options = ["Select saved template"]
    if saved_templates:
        for t in saved_templates:
            template_options.append(f"{t['name']} ({t['type']})")
    
    selected_template = st.selectbox(
        "Template",
        template_options,
        key="saved_template_select",
        label_visibility="collapsed"
    )
    
    if selected_template and selected_template != "Select saved template":
        template_name = selected_template.split(' (')[0]
        template_bytes = load_template_from_file(template_name)
        if template_bytes:
            st.session_state.template_bytes = template_bytes
            st.session_state.saved_template_name = template_name
            st.session_state.template_loaded = True
            st.session_state.template_type = 'pptx' if template_name.endswith('.pptx') else 'docx'
            st.session_state.generated = False
            st.session_state.generating = False
            
            config_name = template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
            config_data = load_config_from_file(config_name)
            if config_data:
                st.session_state.custom_mapping = config_data.get('mapping', {})
                st.session_state.config_settings = config_data.get('settings', st.session_state.config_settings)
            else:
                st.session_state.custom_mapping = {}
            
            tokens = extract_placeholders(template_bytes, st.session_state.template_type)
            st.session_state.tokens = tokens
            st.rerun()

with col2:
    uploaded_template = st.file_uploader(
        "Upload", 
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
        st.session_state.generating = False
        
        tokens = extract_placeholders(template_bytes, st.session_state.template_type)
        st.session_state.tokens = tokens
        st.session_state.custom_mapping = {token: "Text" for token in tokens}
        
        save_as = st.checkbox("Save template")
        if save_as:
            save_template_to_file(template_bytes, uploaded_template.name)
            config_data = {
                'mapping': st.session_state.custom_mapping,
                'settings': st.session_state.config_settings
            }
            config_name = uploaded_template.name.replace('.pptx', '').replace('.docx', '') + '_config.json'
            save_config_to_file(config_data, config_name)
            st.success(f"Saved: {uploaded_template.name}")
            st.rerun()

with col3:
    st.markdown('<div style="padding-top: 2px;"></div>', unsafe_allow_html=True)
    if st.session_state.saved_template_name:
        if st.button("Delete", key="delete_template", help="Delete this template"):
            st.session_state.show_delete_confirm = True
            st.session_state.template_to_delete = st.session_state.saved_template_name
            st.rerun()

# Show delete confirmation
if st.session_state.show_delete_confirm and st.session_state.template_to_delete:
    col_confirm1, col_confirm2, col_confirm3 = st.columns([1, 0.5, 0.5])
    with col_confirm1:
        st.markdown(f'<small>Delete "{st.session_state.template_to_delete}"?</small>', unsafe_allow_html=True)
    with col_confirm2:
        if st.button("Yes", key="confirm_delete_yes"):
            if delete_template_file(st.session_state.template_to_delete):
                st.session_state.template_bytes = None
                st.session_state.saved_template_name = None
                st.session_state.template_loaded = False
                st.session_state.tokens = []
                st.session_state.generated = False
                st.session_state.generating = False
                st.session_state.custom_mapping = {}
                st.session_state.show_delete_confirm = False
                st.session_state.template_to_delete = None
                st.rerun()
    with col_confirm3:
        if st.button("No", key="confirm_delete_no"):
            st.session_state.show_delete_confirm = False
            st.session_state.template_to_delete = None
            st.rerun()

if st.session_state.template_bytes is not None:
    template_name = st.session_state.saved_template_name or "Unsaved"
    template_type = st.session_state.template_type or "Unknown"
    st.markdown(f'<div class="saved-indicator">Active: {template_name} ({template_type.upper()})</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- Get current template ---
template_bytes = st.session_state.template_bytes
template_type = st.session_state.template_type
u_template = None
if template_bytes is not None:
    u_template = type('obj', (object,), {'getvalue': lambda: template_bytes})()

text_data = {}
image_data = {}

# --- DISPLAY FIELDS ---
if u_template is not None and st.session_state.tokens:
    tokens = st.session_state.tokens
    
    if not tokens:
        st.info("No placeholders found")
    else:
        mid_point = len(tokens) // 2
        col1_tokens = tokens[:mid_point]
        col2_tokens = tokens[mid_point:]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Fields</div>', unsafe_allow_html=True)
            for token in col1_tokens:
                clean_label = token.replace("{", "").replace("}", "")
                stored_type = st.session_state.custom_mapping.get(token, "Text")
                
                if stored_type == "Image" and template_type == 'pptx':
                    image_data[token] = upload_row(clean_label, token)
                    st.session_state.custom_mapping[token] = "Image"
                else:
                    val, data_type = field_with_type(clean_label, token)
                    text_data[token] = val
                    st.session_state.custom_mapping[token] = data_type
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Fields</div>', unsafe_allow_html=True)
            for token in col2_tokens:
                clean_label = token.replace("{", "").replace("}", "")
                stored_type = st.session_state.custom_mapping.get(token, "Text")
                
                if stored_type == "Image" and template_type == 'pptx':
                    image_data[token] = upload_row(clean_label, token)
                    st.session_state.custom_mapping[token] = "Image"
                else:
                    val, data_type = field_with_type(clean_label, token + "_2")
                    text_data[token] = val
                    st.session_state.custom_mapping[token] = data_type
            st.markdown('</div>', unsafe_allow_html=True)

# --- CONFIGURATION SETTINGS ---
if u_template is not None:
    with st.expander("⚙️ Configuration Settings", expanded=False):
        st.markdown('<div class="config-card">', unsafe_allow_html=True)
        
        # Font Settings
        st.markdown('<div class="section-header">Font Settings</div>', unsafe_allow_html=True)
        col_font1, col_font2, col_font3 = st.columns([1, 1, 1])
        with col_font1:
            font_size = st.number_input(
                "Font Size",
                min_value=8,
                max_value=72,
                value=st.session_state.config_settings.get('font_size', 12),
                key="font_size",
                label_visibility="collapsed"
            )
            st.session_state.config_settings['font_size'] = font_size
        with col_font2:
            font_style = st.selectbox(
                "Font Style",
                ["Arial", "Calibri", "Times New Roman", "Verdana", "Tahoma"],
                index=0,
                key="font_style",
                label_visibility="collapsed"
            )
            st.session_state.config_settings['font_style'] = font_style
        with col_font3:
            text_alignment = st.selectbox(
                "Alignment",
                ["Left", "Center", "Right"],
                index=0,
                key="text_alignment",
                label_visibility="collapsed"
            )
            st.session_state.config_settings['text_alignment'] = text_alignment
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Photo Settings
        st.markdown('<div class="section-header">Photo Settings</div>', unsafe_allow_html=True)
        image_fit = st.selectbox(
            "Image Fit",
            ["Crop", "Fill", "Stretch"],
            index=0,
            key="image_fit",
            label_visibility="collapsed"
        )
        st.session_state.config_settings['image_fit'] = image_fit
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Save Config
        col_save1, col_save2 = st.columns([1, 1])
        with col_save1:
            config_data = {
                'mapping': st.session_state.custom_mapping,
                'settings': st.session_state.config_settings
            }
            config_json_str = json.dumps(config_data, indent=4)
            config_filename = "template_config.json"
            if st.session_state.saved_template_name:
                config_filename = st.session_state.saved_template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
            
            st.download_button(
                label="Download Config",
                data=config_json_str,
                file_name=config_filename,
                mime="application/json",
                use_container_width=True
            )
        
        with col_save2:
            if st.session_state.saved_template_name:
                if st.button("Save Config", use_container_width=True):
                    config_data = {
                        'mapping': st.session_state.custom_mapping,
                        'settings': st.session_state.config_settings
                    }
                    config_filename = st.session_state.saved_template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
                    save_config_to_file(config_data, config_filename)
                    st.success("Config saved!")
        
        # Load config
        st.markdown("<br>", unsafe_allow_html=True)
        u_json = st.file_uploader("Load Config", type=["json"], label_visibility="collapsed")
        if u_json is not None:
            try:
                loaded_config = json.load(u_json)
                st.session_state.custom_mapping = loaded_config.get('mapping', {})
                st.session_state.config_settings = loaded_config.get('settings', st.session_state.config_settings)
                st.success("Config loaded!")
                st.rerun()
            except Exception:
                st.error("Invalid JSON file")
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- GENERATION SECTION ---
if u_template is not None:
    st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
    
    # Generate button
    if st.button("Generate", use_container_width=True):
        st.session_state.generating = True
        st.session_state.generated = False
        st.rerun()
    
    # Show loading screen while generating
    if st.session_state.generating:
        with st.spinner("Generating document..."):
            try:
                if template_type == 'pptx':
                    raw_pptx = generate_pptx_bytes(template_bytes, text_data, image_data, st.session_state.config_settings)
                    st.session_state.final_pptx = raw_pptx
                    st.session_state.final_pdf = convert_pptx_to_pdf(raw_pptx)
                    st.session_state.final_docx = None
                else:
                    raw_docx = generate_docx_bytes(template_bytes, text_data, image_data, st.session_state.config_settings)
                    st.session_state.final_docx = raw_docx
                    st.session_state.final_pdf = convert_docx_to_pdf(raw_docx)
                    st.session_state.final_pptx = None
                st.session_state.generated = True
                st.session_state.generating = False
                st.success("Document generated successfully!")
                st.rerun()
            except Exception as e:
                st.session_state.generating = False
                st.error(f"Error: {e}")
    
    # Show export buttons after generation
    if st.session_state.generated:
        st.markdown("<hr style='margin: 6px 0;'>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">Export</div>', unsafe_allow_html=True)
        dl_col1, dl_col2, dl_col3 = st.columns(3)
        
        with dl_col1:
            if st.session_state.final_pptx:
                st.download_button(
                    "📊 PPTX",
                    data=st.session_state.final_pptx,
                    file_name="Generated.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True
                )
            else:
                st.button("📊 PPTX", disabled=True, use_container_width=True)
        
        with dl_col2:
            if st.session_state.final_pdf:
                st.download_button(
                    "📄 PDF",
                    data=st.session_state.final_pdf,
                    file_name="Generated.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.button("📄 PDF", disabled=True, use_container_width=True)
        
        with dl_col3:
            if st.session_state.final_docx:
                st.download_button(
                    "📝 DOCX",
                    data=st.session_state.final_docx,
                    file_name="Generated.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            else:
                st.button("📝 DOCX", disabled=True, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Select or upload a template to begin")

# Clear generating state on template change
if st.session_state.template_bytes is None:
    st.session_state.generating = False
    st.session_state.generated = False
