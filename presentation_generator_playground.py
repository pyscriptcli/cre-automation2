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
    .block-container { padding-top: 0.25rem !important; padding-bottom: 0.25rem !important; max-width: 1000px !important; padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
    
    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }
    
    /* Inputs */
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[role="textbox"], div[data-baseweb="select"], textarea {
        background-color: #FFFFFF !important; border: 1px solid #CCCCCC !important; border-radius: 3px !important;
        color: #1A1A1A !important;
        min-height: 28px !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within, textarea:focus { border-color: #666666 !important; box-shadow: none !important; }
    input[type="text"], .stTextInput input, div[data-baseweb="select"] div, textarea { color: #1A1A1A !important; font-size: 12px !important; padding: 2px 6px !important; }
    
    /* File Uploader */
    section[data-testid="stFileUploader"] { background-color: #F8F8F8 !important; border: 1px solid #CCCCCC !important; border-radius: 3px !important; padding: 2px 6px !important; }
    section[data-testid="stFileUploader"] button { padding: 2px 8px !important; font-size: 11px !important; }
    
    /* Cards */
    .workspace-card { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 3px; padding: 8px 12px; margin-bottom: 4px; }
    .config-card { background-color: #F8F8F8; border: 1px solid #E0E0E0; border-radius: 3px; padding: 8px 12px; margin-bottom: 4px; }
    
    /* Buttons */
    div.stButton > button { background-color: #1A1A1A !important; color: #FFFFFF !important; font-weight: 600 !important; font-size: 12px !important; border: none !important; border-radius: 3px !important; padding: 4px 12px !important; width: 100% !important; transition: background-color 0.15s ease; min-height: 28px !important; }
    div.stButton > button:hover { background-color: #333333 !important; color: #FFFFFF !important; }
    
    div[data-testid="stDownloadButton"] > button { background-color: #1A1A1A !important; border-radius: 3px !important; color: #FFFFFF !important; font-weight: 600 !important; padding: 4px 12px !important; width: 100% !important; font-size: 12px !important; min-height: 28px !important; }
    div[data-testid="stDownloadButton"] > button:hover { background-color: #333333 !important; }
    
    /* Delete button */
    div[data-testid="column"] button { background-color: transparent !important; color: #DC3545 !important; border: 1px solid #DC3545 !important; border-radius: 3px !important; padding: 2px 10px !important; font-size: 12px !important; min-height: 26px !important; width: auto !important; }
    div[data-testid="column"] button:hover { background-color: #DC3545 !important; color: white !important; }
    
    /* Labels */
    .field-label { font-size: 11px !important; font-weight: 600 !important; color: #1A1A1A !important; padding-top: 4px !important; margin-bottom: 2px !important; }
    .section-header { font-size: 13px !important; font-weight: 700 !important; color: #1A1A1A !important; margin-bottom: 6px !important; }
    .saved-indicator { background-color: #E8F5E9; padding: 4px 10px; border-radius: 3px; font-size: 11px; color: #2E7D32; border-left: 3px solid #2E7D32; margin-top: 4px; }
    
    hr { margin: 6px 0 !important; border-color: #E0E0E0 !important; }
    
    /* Compact spacing */
    .stSelectbox { margin-bottom: 2px !important; }
    .stSelectbox > div { min-height: 28px !important; }
    .stTextInput { margin-bottom: 2px !important; }
    .stTextArea { margin-bottom: 2px !important; }
    .stFileUploader { margin-bottom: 2px !important; }
    .stCheckbox { margin-bottom: 2px !important; }
    .stNumberInput { margin-bottom: 2px !important; }
    
    /* Make select boxes smaller */
    div[data-baseweb="select"] { min-height: 28px !important; }
    div[data-baseweb="select"] > div { min-height: 28px !important; padding: 0 6px !important; }
    div[data-baseweb="select"] select { font-size: 12px !important; padding: 2px 6px !important; }
    
    /* Smaller dropdown icon */
    svg[data-testid="stSelectbox"] { width: 14px !important; height: 14px !important; }
    div[data-baseweb="select"] svg { width: 14px !important; height: 14px !important; }
    
    /* Compact columns */
    .row-widget.stColumns { gap: 4px !important; }
    div[data-testid="column"] { padding: 0 2px !important; }
    
    /* Title container with no title */
    .title-container { height: 12px; margin-bottom: 2px; border-bottom: 1px solid #E0E0E0; }
    
    /* Info message styling */
    .stAlert { padding: 4px 8px !important; font-size: 11px !important; margin-bottom: 2px !important; }
    
    /* Expander */
    .streamlit-expanderHeader { font-size: 12px !important; font-weight: 600 !important; padding: 4px !important; }
    
    /* Confirmation dialog styling */
    .confirmation-row { display: flex; gap: 8px; align-items: center; margin-top: 8px; }
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

def smart_stretch_to_fit(img_file, target_w_emu, target_h_emu):
    try:
        img = Image.open(img_file)
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

def generate_pptx_bytes(template_bytes, text_inputs, image_inputs, font_settings, image_fit_mode):
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
                        # Apply font settings
                        if font_settings:
                            for run in paragraph.runs:
                                if font_settings.get('font_size'):
                                    run.font.size = Pt(font_settings['font_size'])
                                if font_settings.get('font_style'):
                                    run.font.name = font_settings['font_style']
                                if font_settings.get('alignment'):
                                    if font_settings['alignment'] == 'left':
                                        paragraph.alignment = 1
                                    elif font_settings['alignment'] == 'center':
                                        paragraph.alignment = 2
                                    elif font_settings['alignment'] == 'right':
                                        paragraph.alignment = 3
                        
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

        for img_file, left, top, width, height in images_to_add:
            try:
                if image_fit_mode == 'Crop':
                    processed_img = smart_crop_to_fit(img_file, width, height)
                elif image_fit_mode == 'Stretch':
                    processed_img = smart_stretch_to_fit(img_file, width, height)
                else:  # Fill default
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

def generate_docx_bytes(template_bytes, text_inputs, image_inputs, font_settings, image_fit_mode):
    doc = Document(io.BytesIO(template_bytes))
    
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            # Apply font settings
            if font_settings:
                if font_settings.get('font_size'):
                    run.font.size = DocxPt(font_settings['font_size'])
                if font_settings.get('font_style'):
                    run.font.name = font_settings['font_style']
                if font_settings.get('alignment'):
                    if font_settings['alignment'] == 'left':
                        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    elif font_settings['alignment'] == 'center':
                        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    elif font_settings['alignment'] == 'right':
                        paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            
            for token, value in text_inputs.items():
                if token in run.text:
                    run.text = run.text.replace(token, str(value) if value else '')
    
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
def compact_upload_row(label_text, token):
    col1, col2 = st.columns([3, 0.8])
    with col1:
        st.markdown(f'<div class="field-label">{label_text}</div>', unsafe_allow_html=True)
        return st.file_uploader("", type=["png", "jpg", "jpeg"], key=f"val_{token}", label_visibility="collapsed")
    with col2:
        st.markdown('<div style="padding-top: 4px;"></div>', unsafe_allow_html=True)
        st.selectbox("Type", ["Image"], key=f"type_{token}", label_visibility="collapsed", disabled=True)

# --- INIT APP ---
st.set_page_config(page_title="Document Generator", layout="wide")
st.markdown(MINIMAL_CRE_SYSTEM, unsafe_allow_html=True)

# Title container (empty with bottom border)
st.markdown('<div class="title-container"></div>', unsafe_allow_html=True)

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
if "config_saved" not in st.session_state:
    st.session_state.config_saved = False
if "show_delete_confirm" not in st.session_state:
    st.session_state.show_delete_confirm = False
if "font_settings" not in st.session_state:
    st.session_state.font_settings = {
        'font_size': 12,
        'font_style': 'Arial',
        'alignment': 'left'
    }
if "image_fit_mode" not in st.session_state:
    st.session_state.image_fit_mode = 'Crop'

# --- TEMPLATE MANAGEMENT ---
st.markdown('<div class="workspace-card">', unsafe_allow_html=True)

# Template dropdown and upload in one row
col1, col2, col3 = st.columns([3, 0.8, 0.6])

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
            
            config_name = template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
            config_data = load_config_from_file(config_name)
            if config_data:
                st.session_state.custom_mapping = config_data
                if 'font_settings' in config_data:
                    st.session_state.font_settings = config_data['font_settings']
                if 'image_fit_mode' in config_data:
                    st.session_state.image_fit_mode = config_data['image_fit_mode']
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
        
        tokens = extract_placeholders(template_bytes, st.session_state.template_type)
        st.session_state.tokens = tokens
        st.session_state.custom_mapping = {token: "Text" for token in tokens}
        
        save_as = st.checkbox("Save template")
        if save_as:
            save_template_to_file(template_bytes, uploaded_template.name)
            config_data = {
                'mapping': st.session_state.custom_mapping,
                'font_settings': st.session_state.font_settings,
                'image_fit_mode': st.session_state.image_fit_mode
            }
            config_name = uploaded_template.name.replace('.pptx', '').replace('.docx', '') + '_config.json'
            save_config_to_file(config_data, config_name)
            st.success(f"Saved: {uploaded_template.name}")
            st.rerun()

with col3:
    st.markdown('<div style="padding-top: 2px;"></div>', unsafe_allow_html=True)
    if st.session_state.saved_template_name:
        if st.button("Delete", key="delete_template"):
            st.session_state.show_delete_confirm = True

# Show delete confirmation dialog inline
if st.session_state.show_delete_confirm and st.session_state.saved_template_name:
    st.markdown(f'<div style="background-color: #FFF3CD; padding: 8px 12px; border-radius: 4px; border: 1px solid #FFE69C; margin-top: 4px;">', unsafe_allow_html=True)
    st.markdown(f'<span style="font-size: 13px;">Delete "{st.session_state.saved_template_name}"?</span>', unsafe_allow_html=True)
    col_confirm1, col_confirm2, col_confirm3 = st.columns([1, 1, 2])
    with col_confirm1:
        if st.button("Yes", key="confirm_delete", use_container_width=True):
            if delete_template_file(st.session_state.saved_template_name):
                st.session_state.template_bytes = None
                st.session_state.saved_template_name = None
                st.session_state.template_loaded = False
                st.session_state.tokens = []
                st.session_state.generated = False
                st.session_state.custom_mapping = {}
                st.session_state.show_delete_confirm = False
                st.rerun()
    with col_confirm2:
        if st.button("Cancel", key="cancel_delete", use_container_width=True):
            st.session_state.show_delete_confirm = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Show active template indicator
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
                    img = compact_upload_row(clean_label, token)
                    image_data[token] = img
                    st.session_state.custom_mapping[token] = "Image"
                else:
                    col_a, col_b = st.columns([3, 0.8])
                    with col_a:
                        st.markdown(f'<div class="field-label">{clean_label}</div>', unsafe_allow_html=True)
                        val = st.text_input("", key=f"val_{token}", label_visibility="collapsed")
                        text_data[token] = val
                    with col_b:
                        st.markdown('<div style="padding-top: 4px;"></div>', unsafe_allow_html=True)
                        data_type = st.selectbox(
                            "Type",
                            ["Text", "Image"],
                            index=0 if stored_type == "Text" else 1,
                            key=f"type_{token}",
                            label_visibility="collapsed"
                        )
                        st.session_state.custom_mapping[token] = data_type
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Fields</div>', unsafe_allow_html=True)
            for token in col2_tokens:
                clean_label = token.replace("{", "").replace("}", "")
                stored_type = st.session_state.custom_mapping.get(token, "Text")
                
                if stored_type == "Image" and template_type == 'pptx':
                    img = compact_upload_row(clean_label, token)
                    image_data[token] = img
                    st.session_state.custom_mapping[token] = "Image"
                else:
                    col_a, col_b = st.columns([3, 0.8])
                    with col_a:
                        st.markdown(f'<div class="field-label">{clean_label}</div>', unsafe_allow_html=True)
                        val = st.text_input("", key=f"val_{token}_2", label_visibility="collapsed")
                        text_data[token] = val
                    with col_b:
                        st.markdown('<div style="padding-top: 4px;"></div>', unsafe_allow_html=True)
                        data_type = st.selectbox(
                            "Type",
                            ["Text", "Image"],
                            index=0 if stored_type == "Text" else 1,
                            key=f"type_{token}_2",
                            label_visibility="collapsed"
                        )
                        st.session_state.custom_mapping[token] = data_type
            st.markdown('</div>', unsafe_allow_html=True)

# --- CONFIGURATION SETTINGS ---
if u_template is not None:
    with st.expander("⚙️ Configuration Settings", expanded=False):
        st.markdown('<div class="config-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Default Font Settings</div>', unsafe_allow_html=True)
        
        col_font1, col_font2, col_font3 = st.columns(3)
        
        with col_font1:
            st.markdown('<div class="field-label">Font Size</div>', unsafe_allow_html=True)
            font_size = st.number_input(
                "Font Size",
                min_value=8,
                max_value=72,
                value=st.session_state.font_settings.get('font_size', 12),
                step=1,
                key="font_size",
                label_visibility="collapsed"
            )
            st.session_state.font_settings['font_size'] = font_size
        
        with col_font2:
            st.markdown('<div class="field-label">Font Style</div>', unsafe_allow_html=True)
            font_style = st.selectbox(
                "Font Style",
                ["Arial", "Calibri", "Times New Roman", "Verdana", "Helvetica", "Georgia"],
                index=["Arial", "Calibri", "Times New Roman", "Verdana", "Helvetica", "Georgia"].index(
                    st.session_state.font_settings.get('font_style', 'Arial')
                ),
                key="font_style",
                label_visibility="collapsed"
            )
            st.session_state.font_settings['font_style'] = font_style
        
        with col_font3:
            st.markdown('<div class="field-label">Alignment</div>', unsafe_allow_html=True)
            alignment = st.selectbox(
                "Alignment",
                ["left", "center", "right"],
                index=["left", "center", "right"].index(
                    st.session_state.font_settings.get('alignment', 'left')
                ),
                key="alignment",
                label_visibility="collapsed"
            )
            st.session_state.font_settings['alignment'] = alignment
        
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">Photo Settings</div>', unsafe_allow_html=True)
        
        col_photo1, col_photo2 = st.columns(2)
        
        with col_photo1:
            st.markdown('<div class="field-label">Image Fit Mode</div>', unsafe_allow_html=True)
            image_fit = st.selectbox(
                "Image Fit Mode",
                ["Crop", "Stretch", "Fill"],
                index=["Crop", "Stretch", "Fill"].index(
                    st.session_state.image_fit_mode
                ),
                key="image_fit_mode",
                label_visibility="collapsed"
            )
            st.session_state.image_fit_mode = image_fit
        
        with col_photo2:
            st.markdown('<div class="field-label">Description</div>', unsafe_allow_html=True)
            if image_fit == "Crop":
                st.info("Crops image to fit frame while maintaining aspect ratio")
            elif image_fit == "Stretch":
                st.info("Stretches image to fill entire frame")
            else:
                st.info("Fills frame by cropping minimally")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Save configuration button
        col_save1, col_save2 = st.columns([1, 1])
        with col_save1:
            if st.button("Save Configuration", use_container_width=True):
                config_data = {
                    'mapping': st.session_state.custom_mapping,
                    'font_settings': st.session_state.font_settings,
                    'image_fit_mode': st.session_state.image_fit_mode
                }
                if st.session_state.saved_template_name:
                    config_name = st.session_state.saved_template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
                    save_config_to_file(config_data, config_name)
                    st.success("Configuration saved!")
                else:
                    st.warning("Please save the template first")
        
        with col_save2:
            # Load config button
            config_json_str = json.dumps({
                'mapping': st.session_state.custom_mapping,
                'font_settings': st.session_state.font_settings,
                'image_fit_mode': st.session_state.image_fit_mode
            }, indent=4)
            st.download_button(
                label="Download Config",
                data=config_json_str,
                file_name="config.json",
                mime="application/json",
                use_container_width=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- GENERATION SECTION ---
if u_template is not None:
    st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
    
    if st.button("Generate", use_container_width=True):
        with st.spinner("Generating..."):
            try:
                if template_type == 'pptx':
                    raw_pptx = generate_pptx_bytes(
                        template_bytes, 
                        text_data, 
                        image_data,
                        st.session_state.font_settings,
                        st.session_state.image_fit_mode
                    )
                    st.session_state.final_pptx = raw_pptx
                    st.session_state.final_pdf = convert_pptx_to_pdf(raw_pptx)
                    st.session_state.final_docx = None
                else:
                    raw_docx = generate_docx_bytes(
                        template_bytes, 
                        text_data, 
                        image_data,
                        st.session_state.font_settings,
                        st.session_state.image_fit_mode
                    )
                    st.session_state.final_docx = raw_docx
                    st.session_state.final_pdf = convert_docx_to_pdf(raw_docx)
                    st.session_state.final_pptx = None
                st.session_state.generated = True
                st.success("Done!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    
    if st.session_state.generated:
        st.markdown("<hr style='margin: 4px 0;'>", unsafe_allow_html=True)
        dl_col1, dl_col2, dl_col3 = st.columns(3)
        
        with dl_col1:
            if st.session_state.final_pptx:
                st.download_button(
                    "PPTX",
                    data=st.session_state.final_pptx,
                    file_name="Generated.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True
                )
            else:
                st.button("PPTX", disabled=True, use_container_width=True)
        
        with dl_col2:
            if st.session_state.final_pdf:
                st.download_button(
                    "PDF",
                    data=st.session_state.final_pdf,
                    file_name="Generated.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.button("PDF", disabled=True, use_container_width=True)
        
        with dl_col3:
            if st.session_state.final_docx:
                st.download_button(
                    "DOCX",
                    data=st.session_state.final_docx,
                    file_name="Generated.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            else:
                st.button("DOCX", disabled=True, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Select or upload a template")
