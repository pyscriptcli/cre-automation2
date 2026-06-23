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
    
    .field-label { font-size: 13px !important; font-weight: 600 !important; color: #1A1A1A !important; padding-top: 6px; }
    .section-header { font-size: 15px !important; font-weight: 700 !important; color: #1A1A1A !important; margin-bottom: 10px; }
    .saved-indicator { background-color: #E8F5E9; padding: 6px 12px; border-radius: 4px; font-size: 13px; color: #2E7D32; border-left: 3px solid #2E7D32; margin-top: 6px; }
    
    hr { margin: 12px 0 !important; border-color: #E0E0E0 !important; }
    .streamlit-expanderHeader { font-size: 14px !important; font-weight: 600 !important; }
    
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
    
    .detection-dialog {
        background-color: #F8F9FA;
        border: 2px solid #003366;
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
    }
    .detection-dialog h3 {
        color: #003366;
        margin-top: 0;
    }
    .token-badge {
        background-color: #E8F0FE;
        padding: 2px 8px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 12px;
        display: inline-block;
        margin: 2px;
    }
    .group-card {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 4px;
        padding: 12px;
        margin: 8px 0;
    }
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
    try:
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
    except Exception as e:
        print(f"Error extracting from PPTX: {e}")
        return []

def extract_placeholders_from_docx(docx_bytes):
    try:
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
    except Exception as e:
        print(f"Error extracting from DOCX: {e}")
        return []

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

def detect_table_placeholders(tokens):
    table_groups = {}
    
    pattern = r'\{\{([A-Z_]+)_(\d+)\}\}'
    
    for token in tokens:
        match = re.match(pattern, token)
        if match:
            base_name = match.group(1)
            row_num = int(match.group(2))
            
            if base_name not in table_groups:
                table_groups[base_name] = {
                    'rows': set(),
                    'tokens': []
                }
            table_groups[base_name]['rows'].add(row_num)
            table_groups[base_name]['tokens'].append(token)
    
    validated_groups = {}
    for base_name, data in table_groups.items():
        row_numbers = sorted(data['rows'])
        max_row = max(row_numbers)
        
        expected_rows = set(range(1, max_row + 1))
        current_rows = set(row_numbers)
        missing_rows = expected_rows - current_rows
        
        if len(row_numbers) >= 2:
            validated_groups[base_name] = {
                'max_row': max_row,
                'tokens': data['tokens'],
                'missing_rows': list(missing_rows) if missing_rows else []
            }
    
    return validated_groups

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

def generate_docx_bytes(template_bytes, text_inputs, image_inputs, table_data=None, table_config=None):
    doc = Document(io.BytesIO(template_bytes))
    
    for paragraph in doc.paragraphs:
        has_image = False
        for img_token in image_inputs.keys():
            if img_token in paragraph.text:
                has_image = True
                break
        
        if not has_image:
            replace_text_in_paragraph(paragraph, text_inputs)
    
    if table_data and table_config:
        base_names = list(table_config.keys())
        
        for table in doc.tables:
            has_placeholders = False
            for row in table.rows:
                for cell in row.cells:
                    if '{{' in cell.text and '}}' in cell.text:
                        has_placeholders = True
                        break
                if has_placeholders:
                    break
            
            if has_placeholders:
                while len(table.rows) > 1:
                    table._element.remove(table.rows[-1]._element)
                
                for row_idx, row_data in enumerate(table_data):
                    new_row = table.add_row()
                    for col_idx, cell in enumerate(new_row.cells):
                        for base_name in base_names:
                            placeholder = f"{{{{{base_name}_{row_idx + 1}}}}}"
                            if placeholder in cell.text:
                                value = row_data.get(base_name, '')
                                cell.text = str(value) if value else ''
                                break
    
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

def load_saved_template_config(template_name):
    """Load saved configuration for a template if it exists"""
    config_name = template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
    config_data = load_config_from_file(config_name)
    
    if config_data and 'table_config' in config_data:
        return config_data['table_config']
    return None

def save_and_load_template(template_bytes, template_name, template_type, tokens, confirmed_groups):
    """Save template to file and load with confirmed configuration"""
    # Save the template file
    saved_path = save_template_to_file(template_bytes, template_name)
    
    # Save config with table_config
    config_data = {
        'table_config': confirmed_groups,
        'custom_mapping': st.session_state.custom_mapping
    }
    config_name = template_name.replace('.pptx', '').replace('.docx', '') + '_config.json'
    save_config_to_file(config_data, config_name)
    
    # Load into session state
    st.session_state.table_config = confirmed_groups
    st.session_state.tokens = tokens
    st.session_state.template_bytes = template_bytes
    st.session_state.template_type = template_type
    st.session_state.template_loaded = True
    st.session_state.saved_template_name = template_name
    st.session_state.saved_file_name = template_name
    st.session_state.save_success = True
    st.session_state.use_dynamic_table = True if confirmed_groups else False
    st.session_state.table_headers = list(confirmed_groups.keys()) if confirmed_groups else []
    
    if confirmed_groups and template_type == 'docx':
        max_rows = 0
        for base_name, config in confirmed_groups.items():
            max_rows = max(max_rows, config['max_row'])
        
        st.session_state.table_data = []
        for i in range(max_rows):
            row_data = {}
            for base_name in confirmed_groups.keys():
                row_data[base_name] = ""
            st.session_state.table_data.append(row_data)
    else:
        st.session_state.table_data = []
    
    # Reset pending state
    st.session_state.show_detection_dialog = False
    st.session_state.pending_tokens = []
    st.session_state.pending_template_bytes = None
    st.session_state.pending_template_type = None
    st.session_state.pending_template_name = None
    st.session_state.confirmed_groups = {}

# --- UI HELPERS ---
def simple_uploader_row(label_text, allowed_types, key):
    st.markdown(f'<div class="field-label">{label_text}</div>', unsafe_allow_html=True)
    return st.file_uploader(label_text, type=allowed_types, key=f"val_{key}", label_visibility="collapsed")

def show_placeholder_detection_dialog(tokens, detected_groups):
    """Show detected placeholders and ask for confirmation"""
    
    st.markdown('<div class="detection-dialog">', unsafe_allow_html=True)
    st.markdown("### Placeholder Detection Results")
    st.markdown(f"**Total placeholders found:** {len(tokens)}")
    
    with st.expander("View All Placeholders", expanded=False):
        cols = st.columns(4)
        for idx, token in enumerate(sorted(tokens)):
            cols[idx % 4].markdown(f'<span class="token-badge">{token}</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    confirmed_groups = {}
    
    if detected_groups:
        st.markdown("### Detected Table Groups")
        st.markdown("Patterns with numbered suffixes (_1, _2, _3) were detected:")
        
        for base_name, config in detected_groups.items():
            st.markdown('<div class="group-card">', unsafe_allow_html=True)
            
            cols = st.columns([1, 2, 1])
            with cols[0]:
                st.markdown(f"**{base_name}**")
                st.caption(f"Max rows: {config['max_row']}")
            
            with cols[1]:
                tokens_display = ", ".join(config['tokens'])
                st.markdown(f'<span style="font-size:12px;">{tokens_display}</span>', unsafe_allow_html=True)
            
            with cols[2]:
                confirm = st.checkbox(
                    "Group as table",
                    value=True,
                    key=f"confirm_group_{base_name}"
                )
                if confirm:
                    confirmed_groups[base_name] = config
            
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No table patterns detected. All placeholders will be treated as regular fields.")
    
    st.markdown("---")
    
    with st.expander("Manual Grouping (Optional)"):
        st.markdown("Create a custom table group by specifying the base name and number of rows.")
        st.caption("Example: If you have CUSTOM_1, CUSTOM_2, CUSTOM_3, enter base name as 'CUSTOM'")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            manual_base = st.text_input("Base Name (without _number)", key="manual_base", placeholder="e.g., CUSTOM")
        with col2:
            manual_rows = st.number_input("Number of Rows", min_value=1, value=1, key="manual_rows", step=1)
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Add Group", key="add_manual_group"):
                if manual_base:
                    manual_tokens = []
                    for i in range(1, manual_rows + 1):
                        manual_tokens.append(f"{{{{{manual_base}_{i}}}}}")
                    
                    existing_tokens = [t for t in manual_tokens if t in tokens]
                    if existing_tokens:
                        confirmed_groups[manual_base] = {
                            'max_row': manual_rows,
                            'tokens': existing_tokens,
                            'missing_rows': []
                        }
                        st.success(f"Added manual group: {manual_base}")
                        st.rerun()
                    else:
                        st.warning(f"No tokens found matching pattern {manual_base}_1, {manual_base}_2, ...")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Save Template button
    if st.button("Save Template", use_container_width=True, type="primary"):
        if st.session_state.pending_template_name:
            save_and_load_template(
                st.session_state.pending_template_bytes,
                st.session_state.pending_template_name,
                st.session_state.pending_template_type,
                st.session_state.pending_tokens,
                confirmed_groups
            )
            st.rerun()
        else:
            st.error("Template name not found. Please try uploading again.")
    
    return confirmed_groups

# --- MAIN APP ---
st.set_page_config(page_title="OpenFlux", layout="wide", initial_sidebar_state="collapsed")
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
if "table_data" not in st.session_state:
    st.session_state.table_data = []
if "use_dynamic_table" not in st.session_state:
    st.session_state.use_dynamic_table = False
if "table_config" not in st.session_state:
    st.session_state.table_config = {}
if "table_headers" not in st.session_state:
    st.session_state.table_headers = []
if "show_detection_dialog" not in st.session_state:
    st.session_state.show_detection_dialog = False
if "confirmed_groups" not in st.session_state:
    st.session_state.confirmed_groups = {}
if "pending_tokens" not in st.session_state:
    st.session_state.pending_tokens = []
if "pending_template_bytes" not in st.session_state:
    st.session_state.pending_template_bytes = None
if "pending_template_type" not in st.session_state:
    st.session_state.pending_template_type = None
if "pending_template_name" not in st.session_state:
    st.session_state.pending_template_name = None

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
            # Determine template type from file extension
            template_type = 'pptx' if template_name.endswith('.pptx') else 'docx'
            
            # Check if this template has a saved configuration
            saved_table_config = load_saved_template_config(template_name)
            
            if saved_table_config:
                # Load directly from saved config
                st.session_state.template_bytes = template_bytes
                st.session_state.saved_template_name = template_name
                st.session_state.template_loaded = True
                st.session_state.template_type = template_type
                
                tokens = extract_placeholders(template_bytes, template_type)
                st.session_state.tokens = tokens
                
                # Load saved config
                st.session_state.table_config = saved_table_config
                st.session_state.use_dynamic_table = True
                st.session_state.table_headers = list(saved_table_config.keys())
                
                # Initialize table data
                max_rows = 0
                for base_name, config in saved_table_config.items():
                    max_rows = max(max_rows, config['max_row'])
                
                st.session_state.table_data = []
                for i in range(max_rows):
                    row_data = {}
                    for base_name in saved_table_config.keys():
                        row_data[base_name] = ""
                    st.session_state.table_data.append(row_data)
                
                # Load custom mapping
                config_data = load_config_from_file(template_name.replace('.pptx', '').replace('.docx', '') + '_config.json')
                if config_data and 'custom_mapping' in config_data:
                    st.session_state.custom_mapping = config_data['custom_mapping']
            else:
                # No saved config, check for detection
                tokens = extract_placeholders(template_bytes, template_type)
                st.session_state.tokens = tokens
                
                detected_groups = detect_table_placeholders(tokens)
                
                if detected_groups and template_type == 'docx':
                    st.session_state.show_detection_dialog = True
                    st.session_state.pending_tokens = tokens
                    st.session_state.pending_template_bytes = template_bytes
                    st.session_state.pending_template_type = template_type
                    st.session_state.pending_template_name = template_name
                    st.session_state.template_loaded = False
                else:
                    st.session_state.template_bytes = template_bytes
                    st.session_state.saved_template_name = template_name
                    st.session_state.template_loaded = True
                    st.session_state.template_type = template_type
                    st.session_state.use_dynamic_table = False
                    st.session_state.table_config = {}
                    st.session_state.table_data = []
                    st.session_state.table_headers = []

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
        template_name = uploaded_template.name
        template_type = 'pptx' if template_name.endswith('.pptx') else 'docx'
        
        tokens = extract_placeholders(template_bytes, template_type)
        detected_groups = detect_table_placeholders(tokens)
        
        if detected_groups and template_type == 'docx':
            st.session_state.show_detection_dialog = True
            st.session_state.pending_tokens = tokens
            st.session_state.pending_template_bytes = template_bytes
            st.session_state.pending_template_type = template_type
            st.session_state.pending_template_name = template_name
            st.session_state.template_bytes = None
            st.session_state.template_loaded = False
        else:
            st.session_state.template_bytes = template_bytes
            st.session_state.saved_template_name = None
            st.session_state.template_loaded = True
            st.session_state.template_type = template_type
            st.session_state.tokens = tokens
            st.session_state.use_dynamic_table = False
            st.session_state.table_config = {}
            st.session_state.table_data = []
            st.session_state.table_headers = []
            
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

# --- SHOW DETECTION DIALOG ---
if st.session_state.show_detection_dialog and st.session_state.pending_tokens:
    st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
    detected_groups = detect_table_placeholders(st.session_state.pending_tokens)
    show_placeholder_detection_dialog(st.session_state.pending_tokens, detected_groups)
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.save_success:
    st.success(f"Template '{st.session_state.saved_file_name}' saved successfully!")
    st.session_state.save_success = False
    st.session_state.saved_file_name = None

if st.session_state.template_bytes is not None and st.session_state.template_loaded:
    template_name = st.session_state.saved_template_name or "Unsaved Template"
    template_type = st.session_state.template_type or "Unknown"
    st.markdown(f'<div class="saved-indicator">Active: {template_name} ({template_type.upper()})</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- MAIN CONTENT ---
template_bytes = st.session_state.template_bytes
template_type = st.session_state.template_type
u_template = None
if template_bytes is not None and st.session_state.template_loaded:
    u_template = type('obj', (object,), {'getvalue': lambda: template_bytes})()

text_data = {}
image_data = {}
field_types = {}

if u_template is not None and st.session_state.tokens:
    tokens = st.session_state.tokens
    table_config = st.session_state.table_config
    
    if not tokens:
        st.info("No placeholders found in the template.")
    else:
        table_tokens = set()
        for base_name, config in table_config.items():
            for token in config['tokens']:
                table_tokens.add(token)
        
        regular_tokens = [t for t in tokens if t not in table_tokens]
        
        # --- DISPLAY REGULAR FIELDS ---
        if regular_tokens:
            st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">General Information</div>', unsafe_allow_html=True)
            
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
        
        # --- DISPLAY DYNAMIC TABLE ---
        if table_config and st.session_state.use_dynamic_table and template_type == 'docx' and st.session_state.table_data:
            st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Table Data</div>', unsafe_allow_html=True)
            
            table_headers = list(table_config.keys())
            
            max_rows = 0
            for base_name, config in table_config.items():
                max_rows = max(max_rows, config['max_row'])
            
            st.markdown(f'<div style="font-size:12px;color:#666;margin-bottom:10px;">{len(table_headers)} columns, {max_rows} base rows</div>', unsafe_allow_html=True)
            
            col_controls1, col_controls2, col_controls3 = st.columns([1, 1, 6])
            with col_controls1:
                if st.button("Add Row", use_container_width=True, key="add_table_row"):
                    new_row = {}
                    for header in table_headers:
                        new_row[header] = ""
                    st.session_state.table_data.append(new_row)
                    st.rerun()
            with col_controls2:
                if len(st.session_state.table_data) > 1:
                    if st.button("Remove Last", use_container_width=True, key="remove_last_row"):
                        st.session_state.table_data.pop()
                        st.rerun()
            
            col_count = len(table_headers)
            col_widths = [2] * col_count + [0.5]
            col_headers = st.columns(col_widths)
            
            for idx, header in enumerate(table_headers):
                display_header = header.replace('_', ' ').title()
                with col_headers[idx]:
                    st.markdown(f'<strong>{display_header}</strong>', unsafe_allow_html=True)
            with col_headers[-1]:
                st.markdown('', unsafe_allow_html=True)
            
            rows_to_delete = []
            for idx, row_data in enumerate(st.session_state.table_data):
                col_widths = [2] * col_count + [0.5]
                cols = st.columns(col_widths)
                
                for col_idx, header in enumerate(table_headers):
                    with cols[col_idx]:
                        row_data[header] = st.text_input(
                            f"{header}_{idx+1}", 
                            value=row_data.get(header, ""), 
                            key=f"table_{header}_{idx}",
                            label_visibility="collapsed",
                            placeholder=f"{header.replace('_', ' ').title()} {idx+1}"
                        )
                
                with cols[-1]:
                    if len(st.session_state.table_data) > 1:
                        if st.button("Delete", key=f"delete_row_{idx}"):
                            rows_to_delete.append(idx)
            
            if rows_to_delete:
                for idx in sorted(rows_to_delete, reverse=True):
                    st.session_state.table_data.pop(idx)
                st.rerun()
            
            st.markdown(f'<div style="font-size:12px;color:#666;margin-top:8px;">Total rows: {len(st.session_state.table_data)}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            for key in list(text_data.keys()):
                if '{{' in key and '_' in key:
                    for base_name in table_config.keys():
                        if f'{{{{{base_name}_' in key:
                            del text_data[key]
                            break
            
            for idx, row_data in enumerate(st.session_state.table_data):
                for base_name in table_config.keys():
                    placeholder = f"{{{{{base_name}_{idx+1}}}}}"
                    text_data[placeholder] = row_data.get(base_name, "")

# --- DOWNLOAD SECTION ---
if u_template is not None and st.session_state.template_loaded:
    st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Download Document</div>', unsafe_allow_html=True)
    
    template_name = st.session_state.saved_template_name or "Generated_Document"
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
            try:
                if st.session_state.use_dynamic_table and st.session_state.table_data and st.session_state.table_config:
                    docx_data = generate_docx_bytes(
                        template_bytes, 
                        text_data, 
                        image_data, 
                        st.session_state.table_data,
                        st.session_state.table_config
                    )
                else:
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
                st.error(traceback.format_exc())
    
    st.markdown('</div>', unsafe_allow_html=True)
else:
    if not st.session_state.show_detection_dialog:
        st.info("Please upload or select a template to begin")
