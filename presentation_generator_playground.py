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
                    'type': 'PPTX' if file.endswith('.pptx') else 'DOCX'
                })
    return templates

def delete_template_file(template_name):
    """Delete a saved template"""
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
    for run in paragraph.runs:
        for token, value in text_inputs.items():
            if token in run.text:
                run.text = run.text.replace(token, str(value) if value else '')
    
    if hasattr(paragraph, 'text') and paragraph.text:
        for token, value in text_inputs.items():
            if token in paragraph.text:
                if not paragraph.runs:
                    paragraph.add_run()
                for run in paragraph.runs:
                    if token in run.text:
                        run.text = run.text.replace(token, str(value) if value else '')

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

def generate_docx_bytes(template_bytes, text_inputs, image_inputs, table_data=None):
    """Generate DOCX with text, image, and table replacements"""
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
        # Check if this is a placeholder table with dynamic rows
        if table_data and len(table.rows) > 0:
            # Check if first row (header) has placeholders or actual headers
            header_row = table.rows[0]
            has_placeholders = False
            
            # Check if header row has any placeholders
            for cell in header_row.cells:
                if '{{' in cell.text and '}}' in cell.text:
                    has_placeholders = True
                    break
            
            if has_placeholders:
                # This is a placeholder table - replace with dynamic data
                # Keep the header row
                while len(table.rows) > 1:
                    table._element.remove(table.rows[-1]._element)
                
                # Add data rows from table_data
                for data_item in table_data:
                    new_row = table.add_row()
                    # Assuming the table has 3 columns: Company, Representative, Designation
                    if len(new_row.cells) >= 3:
                        new_row.cells[0].text = str(data_item.get('company', ''))
                        new_row.cells[1].text = str(data_item.get('rep', ''))
                        new_row.cells[2].text = str(data_item.get('designation', ''))
            else:
                # Regular table with fixed rows - just replace text
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            replace_text_in_paragraph(paragraph, text_inputs)
        else:
            # No dynamic data, just replace text
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        replace_text_in_paragraph(paragraph, text_inputs)
    
    doc_stream = io.BytesIO()
    doc.save(doc_stream)
    doc_stream.seek(0)
    return doc_stream.getvalue()

# --- UI HELPERS ---
def simple_uploader_row(label_text, allowed_types, key):
    st.markdown(f'<div class="field-label">{label_text}</div>', unsafe_allow_html=True)
    return st.file_uploader(label_text, type=allowed_types, key=f"val_{key}", label_visibility="collapsed")

def organize_table_rows(tokens):
    """Organize table placeholders into rows"""
    rows = []
    
    # Find all company name placeholders to determine number of rows
    company_placeholders = [t for t in tokens if 'COMPANY_NAME_' in t]
    company_numbers = []
    for p in company_placeholders:
        match = re.search(r'COMPANY_NAME_(\d+)', p)
        if match:
            company_numbers.append(int(match.group(1)))
    
    # Sort numbers to get row count
    max_rows = max(company_numbers) if company_numbers else 0
    
    for i in range(1, max_rows + 1):
        row = {
            'company': f'{{{{COMPANY_NAME_{i}}}}}',
            'rep': f'{{{{REPRESENTATIVE_{i}}}}}',
            'designation': f'{{{{DESIGNATION_{i}}}}}'
        }
        rows.append(row)
    
    return rows

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

# Dynamic table data
if "table_data" not in st.session_state:
    st.session_state.table_data = []

if "use_dynamic_table" not in st.session_state:
    st.session_state.use_dynamic_table = False

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
                    st.session_state.table_data = []
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
            
            # Detect if this is a table template
            table_tokens = [t for t in tokens if any(x in t for x in ['COMPANY_NAME_', 'REPRESENTATIVE_', 'DESIGNATION_'])]
            if table_tokens and st.session_state.template_type == 'docx':
                st.session_state.use_dynamic_table = True
                # Initialize table data with empty rows based on placeholders
                if not st.session_state.table_data:
                    row_count = len([t for t in table_tokens if 'COMPANY_NAME_' in t])
                    st.session_state.table_data = [
                        {"company": "", "rep": "", "designation": ""} for _ in range(row_count)
                    ]

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
        
        tokens = extract_placeholders(template_bytes, st.session_state.template_type)
        st.session_state.tokens = tokens
        
        # Detect if this is a table template
        table_tokens = [t for t in tokens if any(x in t for x in ['COMPANY_NAME_', 'REPRESENTATIVE_', 'DESIGNATION_'])]
        if table_tokens and st.session_state.template_type == 'docx':
            st.session_state.use_dynamic_table = True
            row_count = len([t for t in table_tokens if 'COMPANY_NAME_' in t])
            st.session_state.table_data = [
                {"company": "", "rep": "", "designation": ""} for _ in range(row_count)
            ]
        else:
            st.session_state.use_dynamic_table = False
        
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
        # Separate table tokens from regular tokens
        table_tokens = [t for t in tokens if any(x in t for x in ['COMPANY_NAME_', 'REPRESENTATIVE_', 'DESIGNATION_'])]
        regular_tokens = [t for t in tokens if t not in table_tokens]
        
        # --- DISPLAY REGULAR FIELDS (Grouped) ---
        if regular_tokens:
            st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">General Information</div>', unsafe_allow_html=True)
            
            # Split regular tokens into two columns
            mid_point = len(regular_tokens) // 2
            col1, col2 = st.columns(2)
            
            with col1:
                for token in regular_tokens[:mid_point]:
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
                for token in regular_tokens[mid_point:]:
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
        
        # --- DISPLAY DYNAMIC TABLE (Grouped) ---
        if table_tokens and st.session_state.use_dynamic_table and template_type == 'docx':
            st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Company Information Table</div>', unsafe_allow_html=True)
            
            # Table controls
            col_controls1, col_controls2, col_controls3 = st.columns([1, 1, 6])
            with col_controls1:
                if st.button("Add Row", use_container_width=True, key="add_table_row"):
                    st.session_state.table_data.append({"company": "", "rep": "", "designation": ""})
                    st.rerun()
            with col_controls2:
                if len(st.session_state.table_data) > 1:
                    if st.button("Remove Last", use_container_width=True, key="remove_last_row"):
                        st.session_state.table_data.pop()
                        st.rerun()
            
            # Table header
            col_headers = st.columns([2, 2, 2, 0.5])
            with col_headers[0]:
                st.markdown('<strong>Company Name</strong>', unsafe_allow_html=True)
            with col_headers[1]:
                st.markdown('<strong>Representative</strong>', unsafe_allow_html=True)
            with col_headers[2]:
                st.markdown('<strong>Designation</strong>', unsafe_allow_html=True)
            with col_headers[3]:
                st.markdown('', unsafe_allow_html=True)
            
            # Display each row with delete button
            rows_to_delete = []
            for idx, row_data in enumerate(st.session_state.table_data):
                cols = st.columns([2, 2, 2, 0.5])
                with cols[0]:
                    row_data["company"] = st.text_input(
                        f"Company {idx+1}", 
                        value=row_data["company"], 
                        key=f"table_company_{idx}",
                        label_visibility="collapsed",
                        placeholder=f"Company {idx+1}"
                    )
                with cols[1]:
                    row_data["rep"] = st.text_input(
                        f"Rep {idx+1}", 
                        value=row_data["rep"], 
                        key=f"table_rep_{idx}",
                        label_visibility="collapsed",
                        placeholder=f"Rep {idx+1}"
                    )
                with cols[2]:
                    row_data["designation"] = st.text_input(
                        f"Designation {idx+1}", 
                        value=row_data["designation"], 
                        key=f"table_designation_{idx}",
                        label_visibility="collapsed",
                        placeholder=f"Designation {idx+1}"
                    )
                with cols[3]:
                    if len(st.session_state.table_data) > 1:
                        if st.button("Delete", key=f"delete_row_{idx}"):
                            rows_to_delete.append(idx)
            
            # Delete rows after loop to avoid issues
            if rows_to_delete:
                for idx in sorted(rows_to_delete, reverse=True):
                    st.session_state.table_data.pop(idx)
                st.rerun()
            
            st.markdown(f'<div style="font-size:12px;color:#666;margin-top:8px;">Total rows: {len(st.session_state.table_data)}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Update text_data with table data for placeholder replacement
            # For fixed placeholders (COMPANY_NAME_1, etc.), map the dynamic data
            for idx, row_data in enumerate(st.session_state.table_data):
                if idx < len(table_tokens) // 3:  # Make sure we don't exceed placeholder count
                    company_placeholder = f"{{{{COMPANY_NAME_{idx+1}}}}}"
                    rep_placeholder = f"{{{{REPRESENTATIVE_{idx+1}}}}}"
                    designation_placeholder = f"{{{{DESIGNATION_{idx+1}}}}}"
                    
                    if company_placeholder in tokens:
                        text_data[company_placeholder] = row_data.get("company", "")
                    if rep_placeholder in tokens:
                        text_data[rep_placeholder] = row_data.get("rep", "")
                    if designation_placeholder in tokens:
                        text_data[designation_placeholder] = row_data.get("designation", "")

# --- DOWNLOAD SECTION ---
if u_template is not None:
    st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Download Document</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        pptx_disabled = template_type != 'pptx'
        if pptx_disabled:
            st.button("Download PPTX", disabled=True, use_container_width=True, help="Only available for PPTX templates")
        else:
            st.download_button(
                label="Download PPTX",
                data=generate_pptx_bytes(template_bytes, text_data, image_data),
                file_name="Generated_Document.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
                key="download_pptx"
            )
    
    with col2:
        docx_disabled = template_type != 'docx'
        if docx_disabled:
            st.button("Download DOCX", disabled=True, use_container_width=True, help="Only available for DOCX templates")
        else:
            # Generate the document data directly (not inside a function)
            try:
                if st.session_state.use_dynamic_table and st.session_state.table_data:
                    docx_data = generate_docx_bytes(template_bytes, text_data, image_data, st.session_state.table_data)
                else:
                    docx_data = generate_docx_bytes(template_bytes, text_data, image_data)
            except Exception as e:
                st.error(f"Error generating document: {str(e)}")
                docx_data = None
            
            if docx_data:
                st.download_button(
                    label="Download DOCX",
                    data=docx_data,
                    file_name="Generated_Document.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key="download_docx"
                )
            else:
                st.error("Failed to generate document. Please check the template and try again.")
    
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Please upload or select a template to begin")
