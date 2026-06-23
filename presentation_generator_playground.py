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
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; max-width: 1200px !important; }
    
    /* Inputs */
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[role="textbox"], div[data-baseweb="select"], textarea {
        background-color: #FFFFFF !important; border: 1px solid #CCCCCC !important; border-radius: 4px !important;
        color: #1A1A1A !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within, textarea:focus { border-color: #666666 !important; box-shadow: none !important; }
    input[type="text"], .stTextInput input, div[data-baseweb="select"] div, textarea { color: #1A1A1A !important; font-size: 13px !important; }
    
    /* File Uploader */
    section[data-testid="stFileUploader"] { background-color: #F8F8F8 !important; border: 1px solid #CCCCCC !important; border-radius: 4px !important; padding: 2px 8px !important; }
    section[data-testid="stFileUploader"] button { padding: 4px 8px !important; font-size: 12px !important; }
    
    /* Cards */
    .workspace-card { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 4px; padding: 12px; margin-bottom: 8px; }
    
    /* Buttons */
    div.stButton > button { background-color: #1A1A1A !important; color: #FFFFFF !important; font-weight: 600 !important; font-size: 13px !important; border: none !important; border-radius: 4px !important; padding: 6px 12px !important; width: 100% !important; transition: background-color 0.15s ease; }
    div.stButton > button:hover { background-color: #333333 !important; color: #FFFFFF !important; }
    
    div[data-testid="stDownloadButton"] > button { background-color: #1A1A1A !important; border-radius: 4px !important; color: #FFFFFF !important; font-weight: 600 !important; padding: 6px 12px !important; width: 100% !important; font-size: 13px !important; }
    div[data-testid="stDownloadButton"] > button:hover { background-color: #333333 !important; }
    
    /* Delete button */
    div[data-testid="column"] button { background-color: transparent !important; color: #DC3545 !important; border: 1px solid #DC3545 !important; border-radius: 4px !important; padding: 2px 8px !important; font-size: 16px !important; min-height: 32px !important; width: auto !important; }
    div[data-testid="column"] button:hover { background-color: #DC3545 !important; color: white !important; }
    
    /* Labels */
    .field-label { font-size: 12px !important; font-weight: 600 !important; color: #1A1A1A !important; padding-top: 4px !important; margin-bottom: 2px !important; }
    .section-header { font-size: 14px !important; font-weight: 700 !important; color: #1A1A1A !important; margin-bottom: 6px !important; }
    .saved-indicator { background-color: #E8F5E9; padding: 4px 10px; border-radius: 4px; font-size: 12px; color: #2E7D32; border-left: 3px solid #2E7D32; margin-top: 4px; }
    
    hr { margin: 8px 0 !important; border-color: #E0E0E0 !important; }
    
    /* Compact spacing */
    .stSelectbox { margin-bottom: 4px !important; }
    .stTextInput { margin-bottom: 2px !important; }
    .stTextArea { margin-bottom: 2px !important; }
    .stFileUploader { margin-bottom: 2px !important; }
    .stCheckbox { margin-bottom: 2px !important; }
    
    /* Row with delete button */
    .template-row { display: flex; gap: 4px; align-items: center; }
    
    /* Expander */
    .streamlit-expanderHeader { font-size: 13px !important; font-weight: 600 !important; }
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
def field_with_type(label_text, token, default_value=""):
    col1, col2, col3 = st.columns([3, 1.2, 0.5])
    with col1:
        st.markdown(f'<div class="field-label">{label_text}</div>', unsafe_allow_html=True)
        value = st.text_input("", key=f"val_{token}", label_visibility="collapsed", value=default_value)
    with col2:
        st.markdown('<div style="padding-top: 4px;"></div>', unsafe_allow_html=True)
        data_type = st.selectbox(
            "Type",
            ["Text", "Image"],
            key=f"type_{token}",
            label_visibility="collapsed"
        )
    with col3:
        st.markdown('<div style="padding-top: 4px;"></div>', unsafe_allow_html=True)
        if data_type == "Image":
            upload = st.file_uploader("", type=["png", "jpg", "jpeg"], key=f"upload_{token}", label_visibility="collapsed")
            return value, data_type, upload
        else:
            return value, data_type, None

def compact_upload_row(label_text, token):
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f'<div class="field-label">{label_text}</div>', unsafe_allow_html=True)
        return st.file_uploader("", type=["png", "jpg", "jpeg"], key=f"val_{token}", label_visibility="collapsed")
    with col2:
        st.markdown('<div style="padding-top: 4px;"></div>', unsafe_allow_html=True)
        st.selectbox("Type", ["Image"], key=f"type_{token}", label_visibility="collapsed", disabled=True)

# --- INIT APP ---
st.set_page_config(page_title="Document Generator", layout="wide")
st.markdown(MINIMAL_CRE_SYSTEM, unsafe_allow_html=True)

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
if "delete_trigger" not in st.session_state:
    st.session_state.delete_trigger = False

# --- MAIN LAYOUT ---
st.markdown('<h3 style="font-weight: 700; color: #1A1A1A; margin-bottom: 2px;">Document Generator</h3>', unsafe_allow_html=True)
st.markdown("<hr style='margin: 4px 0 8px 0;'>", unsafe_allow_html=True)

# --- TEMPLATE MANAGEMENT ---
st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
st.markdown('<div class="section-header">Template</div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    saved_templates = get_saved_templates()
    template_options = ["Select saved template"]
    if saved_templates:
        for t in saved_templates:
            template_options.append(f"{t['name']} ({t['type']})")
    
    # Row for dropdown and delete button
    drop_col, del_col = st.columns([6, 1])
    with drop_col:
        selected_template = st.selectbox(
            "Load Template",
            template_options,
            key="saved_template_select",
            label_visibility="collapsed"
        )
    
    with del_col:
        if selected_template and selected_template != "Select saved template":
            template_name = selected_template.split(' (')[0]
            if st.button("🗑️", key="delete_template", help="Delete this template"):
                if delete_template_file(template_name):
                    st.session_state.delete_trigger = True
                    st.session_state.template_bytes = None
                    st.session_state.saved_template_name = None
                    st.session_state.template_loaded = False
                    st.session_state.tokens = []
                    st.success(f"Deleted: {template_name}")
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

with col2:
    uploaded_template = st.file_uploader(
        "Upload New", 
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
        
        tokens = extract_placeholders(template_bytes, st.session_state.template_type)
        st.session_state.tokens = tokens
        
        save_as = st.checkbox("Save template")
        if save_as:
            save_template_to_file(template_bytes, uploaded_template.name)
            config_name = uploaded_template.name.replace('.pptx', '').replace('.docx', '') + '_config.json'
            if st.session_state.custom_mapping:
                save_config_to_file(st.session_state.custom_mapping, config_name)
            st.success(f"Saved: {uploaded_template.name}")
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
                    img = compact_upload_row(clean_label, token)
                    image_data[token] = img
                    # Store type in mapping
                    st.session_state.custom_mapping[token] = "Image"
                else:
                    # Text field with type selector
                    col_a, col_b, col_c = st.columns([3, 1.2, 0.5])
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
                    with col_c:
                        pass
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
                    col_a, col_b, col_c = st.columns([3, 1.2, 0.5])
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
                    with col_c:
                        pass
            st.markdown('</div>', unsafe_allow_html=True)

# --- GENERATION SECTION ---
if u_template is not None:
    st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
    
    gen_col, dl1, dl2, dl3 = st.columns([1, 1, 1, 1])
    
    with gen_col:
        if st.button("Generate", use_container_width=True):
            with st.spinner("Generating..."):
                try:
                    if template_type == 'pptx':
                        raw_pptx = generate_pptx_bytes(template_bytes, text_data, image_data)
                        st.session_state.final_pptx = raw_pptx
                        st.session_state.final_pdf = convert_pptx_to_pdf(raw_pptx)
                        st.session_state.final_docx = None
                    else:
                        raw_docx = generate_docx_bytes(template_bytes, text_data, image_data)
                        st.session_state.final_docx = raw_docx
                        st.session_state.final_pdf = convert_docx_to_pdf(raw_docx)
                        st.session_state.final_pptx = None
                    st.success("Done!")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with dl1:
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
    
    with dl2:
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
    
    with dl3:
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
