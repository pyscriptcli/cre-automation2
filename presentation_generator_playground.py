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
    div[data-testid="stHeader"] { background-color: #FFFFFF !important; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1.5rem !important; max-width: 1400px !important; }
    
    /* Inputs */
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[role="textbox"], div[data-baseweb="select"], textarea {
        background-color: #FFFFFF !important; border: 1px solid #CCCCCC !important; border-radius: 4px !important;
        color: #1A1A1A !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within, textarea:focus { border-color: #666666 !important; box-shadow: none !important; }
    input[type="text"], .stTextInput input, div[data-baseweb="select"] div, textarea { color: #1A1A1A !important; font-size: 14px !important; }
    
    /* File Uploader */
    section[data-testid="stFileUploader"] { background-color: #F8F8F8 !important; border: 1px solid #CCCCCC !important; border-radius: 4px !important; padding: 4px 12px !important; }
    
    /* Cards */
    .workspace-card { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 4px; padding: 20px; margin-bottom: 16px; }
    .config-card { background-color: #F8F8F8; border: 1px solid #E0E0E0; border-radius: 4px; padding: 20px; margin-bottom: 16px; }
    
    /* Buttons */
    div.stButton > button { background-color: #1A1A1A !important; color: #FFFFFF !important; font-weight: 600 !important; font-size: 14px !important; border: none !important; border-radius: 4px !important; padding: 10px 20px !important; width: 100% !important; transition: background-color 0.15s ease; }
    div.stButton > button:hover { background-color: #333333 !important; color: #FFFFFF !important; }
    
    div[data-testid="stDownloadButton"] > button { background-color: #1A1A1A !important; border-radius: 4px !important; color: #FFFFFF !important; font-weight: 600 !important; padding: 10px 20px !important; width: 100% !important; }
    div[data-testid="stDownloadButton"] > button:hover { background-color: #333333 !important; }
    
    /* Labels */
    .field-label { font-size: 13px !important; font-weight: 600 !important; color: #1A1A1A !important; padding-top: 8px; }
    .section-header { font-size: 16px !important; font-weight: 700 !important; color: #1A1A1A !important; margin-bottom: 12px; }
    .saved-indicator { background-color: #E8F5E9; padding: 8px 12px; border-radius: 4px; font-size: 13px; color: #2E7D32; border-left: 3px solid #2E7D32; margin-top: 8px; }
    
    hr { margin: 16px 0 !important; border-color: #E0E0E0 !important; }
    
    /* Field with inline dropdown */
    .field-row { display: flex; gap: 10px; align-items: center; }
    .field-input { flex: 3; }
    .field-type { flex: 1; }
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

        # Second pass: replace text preserving formatting
        for shape in slide.shapes:
            if shape not in shapes_to_delete:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        for run in paragraph.runs:
                            for token, value in text_inputs.items():
                                if token in run.text:
                                    # Preserve formatting by replacing only the token
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
    
    # Replace text in paragraphs preserving formatting
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
def field_with_type(token, key, default_type="text"):
    """Create a field with inline type selector"""
    # Get current type from session state
    current_type = st.session_state.custom_mapping.get(token, default_type)
    
    # Create row with columns
    col1, col2 = st.columns([3, 1])
    
    with col1:
        clean_label = token.replace("{", "").replace("}", "")
        value = st.text_input(
            clean_label,
            key=f"val_{key}",
            label_visibility="collapsed",
            placeholder=f"Enter value for {clean_label}"
        )
    
    with col2:
        # Type selector dropdown
        type_options = ["text", "image"] if st.session_state.template_type == 'pptx' else ["text"]
        type_idx = type_options.index(current_type) if current_type in type_options else 0
        field_type = st.selectbox(
            "Type",
            type_options,
            index=type_idx,
            key=f"type_{key}",
            label_visibility="collapsed"
        )
        st.session_state.custom_mapping[token] = field_type
    
    return value, field_type

# --- INIT APP ---
st.set_page_config(page_title="Document Generator", layout="wide")
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
if "delete_confirm" not in st.session_state:
    st.session_state.delete_confirm = None

# --- MAIN LAYOUT ---
st.markdown('<h2 style="font-weight: 700; color: #1A1A1A; margin-bottom: 4px;">Document Generator</h2>', unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# --- TEMPLATE MANAGEMENT SECTION ---
st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
st.markdown('<div class="section-header">Template</div>', unsafe_allow_html=True)

# Create two columns for dropdown and upload
col_template1, col_template2 = st.columns(2)

with col_template1:
    # Show saved templates dropdown
    saved_templates = get_saved_templates()
    template_options = ["Select saved template"]
    template_dict = {}
    if saved_templates:
        for t in saved_templates:
            display_name = f"{t['name']} ({t['type']})"
            template_options.append(display_name)
            template_dict[display_name] = t['name']
    
    selected_template = st.selectbox(
        "Load Template",
        template_options,
        key="saved_template_select",
        label_visibility="collapsed"
    )
    
    if selected_template and selected_template != "Select saved template":
        template_name = template_dict.get(selected_template, selected_template.split(' (')[0])
        template_bytes = load_template_from_file(template_name)
        if template_bytes:
            st.session_state.template_bytes = template_bytes
            st.session_state.saved_template_name = template_name
            st.session_state.template_loaded = True
            st.session_state.template_type = 'pptx' if template_name.endswith('.pptx') else 'docx'
            
            # Load associated config if exists
            config_name = template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
            config_data = load_config_from_file(config_name)
            if config_data:
                st.session_state.custom_mapping = config_data
            
            # Extract placeholders
            tokens = extract_placeholders(template_bytes, st.session_state.template_type)
            st.session_state.tokens = tokens
            
            st.rerun()
    
    # Delete template section
    if saved_templates:
        st.markdown("<hr>", unsafe_allow_html=True)
        delete_options = ["Select template to delete"] + [t['name'] for t in saved_templates]
        template_to_delete = st.selectbox(
            "Delete Template",
            delete_options,
            key="delete_template_select",
            label_visibility="collapsed"
        )
        
        if template_to_delete and template_to_delete != "Select template to delete":
            if st.button("Delete Selected Template", use_container_width=True, key="delete_btn"):
                if delete_template_file(template_to_delete):
                    st.success(f"Deleted: {template_to_delete}")
                    # Clear session state if the deleted template was active
                    if st.session_state.saved_template_name == template_to_delete:
                        st.session_state.template_bytes = None
                        st.session_state.saved_template_name = None
                        st.session_state.template_loaded = False
                        st.session_state.tokens = []
                        st.session_state.custom_mapping = {}
                    st.rerun()
                else:
                    st.error("Failed to delete template")

with col_template2:
    # Upload new template
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
                key = token.replace("{", "").replace("}", "").replace(" ", "_")
                value, field_type = field_with_type(token, key)
                
                if field_type == "text":
                    text_data[token] = value
                elif field_type == "image":
                    # Show image uploader
                    st.markdown(f'<div class="field-label">{token.replace("{", "").replace("}", "")} (Image)</div>', unsafe_allow_html=True)
                    img_file = st.file_uploader(
                        f"Upload image for {token}",
                        type=["png", "jpg", "jpeg"],
                        key=f"img_{key}",
                        label_visibility="collapsed"
                    )
                    if img_file:
                        image_data[token] = img_file
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Field Values</div>', unsafe_allow_html=True)
            for token in col2_tokens:
                key = token.replace("{", "").replace("}", "").replace(" ", "_")
                value, field_type = field_with_type(token, key)
                
                if field_type == "text":
                    text_data[token] = value
                elif field_type == "image":
                    # Show image uploader
                    st.markdown(f'<div class="field-label">{token.replace("{", "").replace("}", "")} (Image)</div>', unsafe_allow_html=True)
                    img_file = st.file_uploader(
                        f"Upload image for {token}",
                        type=["png", "jpg", "jpeg"],
                        key=f"img_{key}",
                        label_visibility="collapsed"
                    )
                    if img_file:
                        image_data[token] = img_file
            st.markdown('</div>', unsafe_allow_html=True)

# --- DATA MAPPING SECTION ---
if u_template is not None and st.session_state.tokens:
    st.markdown('<div class="config-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Configuration</div>', unsafe_allow_html=True)
    
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
            st.info("Save template first")
    
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
    
    if st.button("Generate", use_container_width=True):
        with st.spinner("Generating document..."):
            try:
                if template_type == 'pptx':
                    raw_pptx = generate_pptx_bytes(template_bytes, text_data, image_data)
                    st.session_state.final_pptx = raw_pptx
                    st.session_state.final_pdf = convert_pptx_to_pdf(raw_pptx)
                    # For DOCX output from PPTX
                    st.session_state.final_docx = convert_pptx_to_docx(raw_pptx)
                else:  # docx
                    raw_docx = generate_docx_bytes(template_bytes, text_data, image_data)
                    st.session_state.final_docx = raw_docx
                    st.session_state.final_pdf = convert_docx_to_pdf(raw_docx)
                    st.session_state.final_pptx = None
                
                st.success("Document generated successfully")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Downloads - Three columns for PPTX, PDF, DOCX
    dl_col1, dl_col2, dl_col3 = st.columns(3)
    
    with dl_col1:
        if st.session_state.final_pptx:
            st.download_button(
                "Download PPTX",
                data=st.session_state.final_pptx,
                file_name="Generated_Document.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True
            )
        else:
            st.button("Download PPTX", disabled=True, use_container_width=True)
    
    with dl_col2:
        if st.session_state.final_pdf:
            st.download_button(
                "Download PDF",
                data=st.session_state.final_pdf,
                file_name="Generated_Document.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.button("Download PDF", disabled=True, use_container_width=True)
    
    with dl_col3:
        if st.session_state.final_docx:
            st.download_button(
                "Download DOCX",
                data=st.session_state.final_docx,
                file_name="Generated_Document.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        else:
            st.button("Download DOCX", disabled=True, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Please upload or select a template to begin")
