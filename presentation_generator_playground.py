import os
import io
import subprocess
import tempfile
import base64
import re
import streamlit as st
from pptx import Presentation
from PIL import Image

# --- PROGRAMMATIC LIGHT MODE LOCK ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\n")

# --- LUXURY DESIGN SYSTEM (CSS INJECTION) ---
LUXURY_CRE_SYSTEM = """
<style>
    .stApp { background-color: #FFFFFF !important; color: #002B49 !important; font-family: 'Inter', -apple-system, sans-serif !important; }
    div[data-testid="stHeader"] { background-color: #FFFFFF !important; }
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; max-width: 1600px !important; }
    
    /* Inputs */
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[role="textbox"], div[data-baseweb="select"] {
        background-color: #FFFFFF !important; border: 1px solid #002B49 !important; border-radius: 0px !important;
        color: #002B49 !important; transition: border-color 0.15s ease-in-out !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within { border-color: #C5A059 !important; box-shadow: none !important; }
    input[type="text"], .stTextInput input, div[data-baseweb="select"] div { color: #002B49 !important; font-size: 14px !important; font-weight: 500 !important; }
    
    /* File Uploader */
    section[data-testid="stFileUploader"] { background-color: #FFFFFF !important; border: 1px solid #002B49 !important; border-radius: 0px !important; padding: 4px 12px !important; }
    section[data-testid="stFileUploader"] div, section[data-testid="stFileUploader"] span { color: #002B49 !important; font-size: 13px !important; font-weight: 500 !important; }
    
    /* Typography & Cards */
    .row-metric-label { font-size: 14px !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.08em !important; color: #002B49 !important; display: flex; align-items: center; padding-top: 12px; }
    .luxury-workspace-card { background-color: #FFFFFF; border-top: 4px solid #002B49; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .preview-panel { border: 1px solid #002B49; background-color: #F8FAFC; height: 850px; display: flex; align-items: center; justify-content: center; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; }
    
    /* Buttons */
    div.stButton > button { background-color: #002B49 !important; color: #FFFFFF !important; font-weight: 700 !important; font-size: 14px !important; text-transform: uppercase !important; border: none !important; border-radius: 0px !important; border-bottom: 4px solid #C5A059 !important; padding: 12px 24px !important; width: 100% !important; transition: background-color 0.15s ease; }
    div.stButton > button:hover { background-color: #0A3352 !important; border-bottom-color: #C5A059 !important; color: #FFFFFF !important; }
</style>
"""

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

def extract_placeholders(pptx_bytes):
    prs = Presentation(io.BytesIO(pptx_bytes))
    tokens = set()
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                tokens.update(re.findall(r'\{\{.*?\}\}', shape.text))
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        tokens.update(re.findall(r'\{\{.*?\}\}', cell.text))
    return sorted(list(tokens))

def generate_pptx_bytes(template_bytes, text_inputs, image_inputs):
    prs = Presentation(io.BytesIO(template_bytes))
    for slide in prs.slides:
        shapes_to_delete, images_to_add = [], []

        for shape in slide.shapes:
            # Process Images first
            if shape.has_text_frame:
                text_content = shape.text
                for img_token, img_file in image_inputs.items():
                    if img_token in text_content and img_file is not None:
                        images_to_add.append((img_file, shape.left, shape.top, shape.width, shape.height))
                        shapes_to_delete.append(shape)

            # Process Text & Tables
            if shape not in shapes_to_delete:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        for run in paragraph.runs:
                            for token, value in text_inputs.items():
                                if token in run.text:
                                    run.text = run.text.replace(token, str(value))
                if shape.has_table:
                    for row in shape.table.rows:
                        for cell in row.cells:
                            for paragraph in cell.text_frame.paragraphs:
                                for run in paragraph.runs:
                                    for token, value in text_inputs.items():
                                        if token in run.text:
                                            run.text = run.text.replace(token, str(value))

        for img_file, left, top, width, height in images_to_add:
            processed_img = smart_crop_to_fit(img_file, width, height)
            slide.shapes.add_picture(processed_img, left, top, width=width, height=height)

        for old_shape in shapes_to_delete:
            sp = old_shape._element
            sp.getparent().remove(sp)

    pptx_stream = io.BytesIO()
    prs.save(pptx_stream)
    return pptx_stream.getvalue()

def display_pdf(pdf_bytes):
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="850" type="application/pdf" style="border: none;"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- UI HELPERS ---
def dynamic_form_row(icon, label_text, key):
    r_col1, r_col2 = st.columns([2, 3])
    with r_col1: st.markdown(f'<div class="row-metric-label">{icon} {label_text}</div>', unsafe_allow_html=True)
    with r_col2: return st.text_input("", key=key, label_visibility="collapsed")

def dynamic_uploader_row(icon, label_text, allowed_types, key):
    r_col1, r_col2 = st.columns([2, 3])
    with r_col1: st.markdown(f'<div class="row-metric-label">{icon} {label_text}</div>', unsafe_allow_html=True)
    with r_col2: return st.file_uploader(label_text, type=allowed_types, key=key, label_visibility="collapsed")

def dynamic_selector_row(icon, label_text, options, key):
    r_col1, r_col2 = st.columns([2, 3])
    with r_col1: st.markdown(f'<div class="row-metric-label">{icon} {label_text}</div>', unsafe_allow_html=True)
    with r_col2: return st.selectbox(label_text, options, key=key, label_visibility="collapsed")


# --- INIT APP ---
st.set_page_config(page_title="Matrix Generator", layout="wide")
st.markdown(LUXURY_CRE_SYSTEM, unsafe_allow_html=True)

if "preview_pdf" not in st.session_state: st.session_state.preview_pdf = None
if "final_pptx" not in st.session_state: st.session_state.final_pptx = None
if "custom_mapping" not in st.session_state: st.session_state.custom_mapping = {}

st.sidebar.markdown("### MODE SELECTION")
app_mode = st.sidebar.radio("Active Protocol:", ["Standard PIS", "Custom Adaptive"])

# --- MAIN LAYOUT ---
col_left, col_right = st.columns([1.2, 1], gap="large")

text_data = {}
image_data = {}

with col_left:
    st.markdown('<div class="luxury-workspace-card">', unsafe_allow_html=True)
    u_template = st.file_uploader("📂 UPLOAD MASTER BLUEPRINT (PPTX)", type=["pptx"])
    st.markdown('</div>', unsafe_allow_html=True)

    if app_mode == "Standard PIS":
        st.markdown('<div class="luxury-workspace-card">', unsafe_allow_html=True)
        st.markdown("### STANDARD PROPERTY SPECS")
        prop_location = dynamic_form_row("📍", "Property Location", "cre_loc")
        prop_size     = dynamic_form_row("📐", "Property Size", "cre_size")
        prop_type     = dynamic_form_row("🏢", "Property Type", "cre_type")
        lease_rates   = dynamic_form_row("💰", "Lease Rates", "cre_rates")
        
        contacts_db = {"None": "", "Dave Policarpio": "0908 865 8945", "Sondi Tuazon": "0917 843 6128"}
        cta1_name = dynamic_selector_row("📞", "CTA 1 Name", list(contacts_db.keys()), "cta1_nm")
        
        u_photo1 = dynamic_uploader_row("📸", "Property Photo 1", ["png", "jpg", "jpeg"], "p1")
        u_map    = dynamic_uploader_row("🗺️", "Location Map", ["png", "jpg", "jpeg"], "m1")
        st.markdown('</div>', unsafe_allow_html=True)

        text_data = {
            "{{PROPERTY_LOCATION}}": prop_location, "{{PROPERTY_SIZE}}": prop_size,
            "{{PROPERTY_TYPE}}": prop_type, "{{LEASE_RATES}}": lease_rates,
            "{{CTA1_NAME}}": "" if cta1_name == "None" else cta1_name,
            "{{CTA1_CONTACT_NUMBER}}": contacts_db.get(cta1_name, "")
        }
        image_data = {"{{PROPERTY_PHOTO1}}": u_photo1, "{{PROPERTY_LOCATION_MAP}}": u_map}

    elif app_mode == "Custom Adaptive" and u_template is not None:
        raw_bytes = u_template.getvalue()
        tokens = extract_placeholders(raw_bytes)
        
        st.markdown('<div class="luxury-workspace-card">', unsafe_allow_html=True)
        st.markdown("### 1. MAP DATA TYPES")
        with st.expander("Configure Placeholders Detected in PPTX", expanded=True):
            for token in tokens:
                c1, c2 = st.columns([3, 2])
                c1.code(token)
                st.session_state.custom_mapping[token] = c2.selectbox("Type", ["Text", "Image"], key=f"map_{token}", label_visibility="collapsed")
        
        st.markdown("### 2. INPUT DATA")
        for token in tokens:
            t_type = st.session_state.custom_mapping.get(token, "Text")
            if t_type == "Text":
                text_data[token] = dynamic_form_row("📝", token.replace("{", "").replace("}", ""), f"val_{token}")
            else:
                image_data[token] = dynamic_uploader_row("📸", token.replace("{", "").replace("}", ""), ["png", "jpg", "jpeg"], f"val_{token}")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- ACTION DESK ---
    st.markdown("<div style='margin-top: 10px; border-top: 1px solid #002B49; padding-top: 20px;'></div>", unsafe_allow_html=True)
    btn_col1, btn_col2, btn_col3 = st.columns(3)

    if u_template:
        with btn_col1:
            if st.button("👁️ GENERATE PREVIEW"):
                with st.spinner("Processing & Rendering PDF..."):
                    try:
                        raw_pptx = generate_pptx_bytes(u_template.getvalue(), text_data, image_data)
                        pdf_bytes = convert_pptx_to_pdf(raw_pptx)
                        st.session_state.preview_pdf = pdf_bytes
                        st.session_state.final_pptx = raw_pptx
                    except Exception as e:
                        st.error(f"Render Core Error: {e}")

        with btn_col2:
            if st.session_state.preview_pdf:
                st.download_button("📥 DOWNLOAD PDF", data=st.session_state.preview_pdf, file_name="Document_Export.pdf", mime="application/pdf", use_container_width=True)
            else:
                st.button("📥 DOWNLOAD PDF", disabled=True)

        with btn_col3:
            if st.session_state.final_pptx:
                st.download_button("📥 DOWNLOAD PPTX", data=st.session_state.final_pptx, file_name="Document_Export.pptx", mime="application/vnd.openxmlformats-officedocument.presentationml.presentation", use_container_width=True)
            else:
                st.button("📥 DOWNLOAD PPTX", disabled=True)

with col_right:
    if st.session_state.preview_pdf:
        display_pdf(st.session_state.preview_pdf)
    else:
        st.markdown('<div class="preview-panel">DOCUMENT PREVIEW RENDERED HERE</div>', unsafe_allow_html=True)
