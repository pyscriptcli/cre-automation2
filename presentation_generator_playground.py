import os
import io
import re
import base64
import subprocess
import tempfile
import json
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

# --- FLAT & LUXURIOUS LUXURY DESIGN SYSTEM ---
LUXURY_CRE_SYSTEM = """
<style>
    .stApp { background-color: #FFFFFF !important; color: #002B49 !important; font-family: 'Inter', -apple-system, sans-serif !important; }
    div[data-testid="stHeader"] { background-color: #FFFFFF !important; }
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; max-width: 1200px !important; }
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[role="textbox"], div[data-baseweb="select"] {
        background-color: #FFFFFF !important; border: 1px solid #002B49 !important; border-radius: 0px !important; color: #002B49 !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within { border-color: #C5A059 !important; box-shadow: none !important; }
    input[type="text"], .stTextInput input, div[data-baseweb="select"] div, textarea { color: #002B49 !important; font-size: 15px !important; font-weight: 500 !important; }
    section[data-testid="stFileUploader"] { background-color: #FFFFFF !important; border: 1px solid #002B49 !important; border-radius: 0px !important; padding: 4px 12px !important; }
    .row-metric-label { font-size: 13px !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.08em !important; color: #002B49 !important; display: flex; align-items: center; padding-top: 12px; }
    .large-icon { font-size: 20px !important; margin-right: 12px; }
    .luxury-workspace-card { background-color: #FFFFFF; border-top: 4px solid #002B49; padding-top: 20px; margin-bottom: 25px; }
    div.stButton > button { background-color: #002B49 !important; color: #FFFFFF !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.08em !important; border: none !important; border-radius: 0px !important; border-bottom: 4px solid #C5A059 !important; padding: 12px 24px !important; width: 100% !important; }
    div.stButton > button:hover { background-color: #0A3352 !important; border-bottom-color: #C5A059 !important; }
</style>
"""

# --- EXTERNALIZED CONFIGURATION (Simulated Database) ---
CONTACTS_DATABASE = {
    "Sondi Tuazon": {"phone": "0917 843 6128", "email": "sondi.tuazon@primephilippines.com"},
    "Dave Policarpio": {"phone": "0908 865 8945", "email": "dave.policarpio@primephilippines.com"},
    "Meliza Zapata": {"phone": "0996 880 5399", "email": "meliza.zapata@primephilippines.com"}
}

# --- BACKEND UTILS ---
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

@st.cache_data(show_spinner=False)
def convert_pptx_to_pdf(pptx_bytes):
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, "doc.pptx")
        output_path = os.path.join(temp_dir, "doc.pdf")
        with open(input_path, "wb") as f:
            f.write(pptx_bytes)
        try:
            subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", temp_dir, input_path], 
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if os.path.exists(output_path):
                with open(output_path, "rb") as f:
                    return f.read()
        except Exception:
            return None
    return None

def extract_template_tokens(prs):
    """Scans OpenXML geometries for {{TOKENS}} and categorizes them."""
    tokens = {"TXT": set(), "NUM": set(), "IMG": set(), "LST": set(), "CTA": set()}
    pattern = re.compile(r'\{\{(.*?)\}\}')
    
    for slide in prs.slides:
        for shape in slide.shapes:
            text_frames = []
            if shape.has_text_frame:
                text_frames.append(shape.text_frame)
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        text_frames.append(cell.text_frame)
                        
            for frame in text_frames:
                for paragraph in frame.paragraphs:
                    matches = pattern.findall(paragraph.text)
                    for match in matches:
                        if match.startswith("TXT:"): tokens["TXT"].add(match)
                        elif match.startswith("NUM:"): tokens["NUM"].add(match)
                        elif match.startswith("IMG:"): tokens["IMG"].add(match)
                        elif match.startswith("LST:"): tokens["LST"].add(match)
                        elif match.startswith("CTA"): tokens["CTA"].add(match) # e.g., CTA1_NAME
                        else: tokens["TXT"].add(match) # Default to text
    return {k: sorted(list(v)) for k, v in tokens.items()}

# --- CORE COMPILE ENGINE ---
def compile_presentation(prs, text_data, image_data):
    for slide in prs.slides:
        shapes_to_delete = []
        images_to_add = []

        for shape in slide.shapes:
            text_frames = []
            if shape.has_text_frame:
                text_frames.append(shape.text_frame)
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        text_frames.append(cell.text_frame)

            for frame in text_frames:
                # Text Replacement
                for paragraph in frame.paragraphs:
                    for run in paragraph.runs:
                        for token, value in text_data.items():
                            target = f"{{{{{token}}}}}"
                            if target in run.text:
                                run.text = run.text.replace(target, str(value))
                                # Auto-scaling heuristic
                                if len(str(value)) > 100 and run.font.size:
                                    run.font.size = int(run.font.size * 0.8)

                # Image Replacement Detection
                if shape.has_text_frame:
                    text_content = frame.text
                    for img_token, img_file in image_data.items():
                        target = f"{{{{{img_token}}}}}"
                        if target in text_content:
                            if img_file is not None:
                                images_to_add.append((img_file, shape.left, shape.top, shape.width, shape.height))
                            shapes_to_delete.append(shape)

        for img_file, left, top, width, height in images_to_add:
            processed_img = smart_crop_to_fit(img_file, width, height)
            slide.shapes.add_picture(processed_img, left, top, width=width, height=height)

        for old_shape in shapes_to_delete:
            sp = old_shape._element
            sp.getparent().remove(sp)

    pptx_stream = io.BytesIO()
    prs.save(pptx_stream)
    return pptx_stream.getvalue()


# --- FRONTEND INTERFACE ---
st.set_page_config(page_title="Dynamic PPTX Engine", layout="wide")
st.markdown(LUXURY_CRE_SYSTEM, unsafe_allow_html=True)

st.markdown('<div class="luxury-workspace-card">', unsafe_allow_html=True)
st.markdown('<div class="row-metric-label"><span class="large-icon">📂</span> 1. UPLOAD MASTER TEMPLATE</div>', unsafe_allow_html=True)
u_template = st.file_uploader("", type=["pptx"], key="master_template")
st.markdown('</div>', unsafe_allow_html=True)

if u_template:
    try:
        prs = Presentation(io.BytesIO(u_template.getvalue()))
        tokens = extract_template_tokens(prs)
        
        # Validation UI
        with st.expander("Template Diagnostics (Found Tokens)", expanded=False):
            st.json(tokens)
            
        st.markdown('<div class="row-metric-label"><span class="large-icon">⚙️</span> 2. CONFIGURE DATA</div>', unsafe_allow_html=True)
        
        with st.form("dynamic_data_form"):
            col_left, col_right = st.columns([1, 1], gap="large")
            text_inputs = {}
            image_inputs = {}
            cta_inputs = {}
            
            with col_left:
                st.markdown("**Text & Metrics**")
                for token in tokens["TXT"]:
                    clean_label = token.replace("TXT:", "").replace("_", " ")
                    text_inputs[token] = st.text_input(clean_label, key=f"in_{token}")
                
                for token in tokens["NUM"]:
                    clean_label = token.replace("NUM:", "").replace("_", " ")
                    text_inputs[token] = st.number_input(clean_label, value=0.0, key=f"in_{token}")
                    
                for token in tokens["LST"]:
                    clean_label = token.replace("LST:", "").replace("_", " ")
                    raw_list = st.text_area(f"{clean_label} (One item per line)", key=f"in_{token}")
                    # Convert to bullet-friendly string
                    text_inputs[token] = "\n".join([f"• {line.strip()}" for line in raw_list.split("\n") if line.strip()])

            with col_right:
                st.markdown("**Media & Assets**")
                for token in tokens["IMG"]:
                    clean_label = token.replace("IMG:", "").replace("_", " ")
                    image_inputs[token] = st.file_uploader(clean_label, type=["png", "jpg", "jpeg"], key=f"up_{token}")
                
                # Check if CTA variables exist (e.g., CTA1_NAME) and render single dropdown
                has_cta1 = any("CTA1" in t for t in tokens["CTA"])
                if has_cta1:
                    st.markdown("**Call to Action**")
                    cta_sel = st.selectbox("Assign Agent Profile", ["None"] + list(CONTACTS_DATABASE.keys()))
                    if cta_sel != "None":
                        text_inputs["CTA1_NAME"] = cta_sel
                        text_inputs["CTA1_CONTACT_NUMBER"] = CONTACTS_DATABASE[cta_sel]["phone"]
                        text_inputs["CTA1_EMAIL_ADDRESS"] = CONTACTS_DATABASE[cta_sel]["email"]
                    else:
                        text_inputs["CTA1_NAME"] = text_inputs["CTA1_CONTACT_NUMBER"] = text_inputs["CTA1_EMAIL_ADDRESS"] = ""

            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("GENERATE & PREVIEW ⚡")

        # --- PROCESS & PREVIEW LOGIC ---
        if submitted:
            with st.spinner("Compiling Presentation..."):
                final_pptx_bytes = compile_presentation(prs, text_inputs, image_inputs)
                st.session_state['pptx_bytes'] = final_pptx_bytes
                
            with st.spinner("Rendering Print Preview via LibreOffice Engine..."):
                pdf_bytes = convert_pptx_to_pdf(final_pptx_bytes)
                st.session_state['pdf_bytes'] = pdf_bytes

        # --- RENDER OUTPUT ---
        if 'pdf_bytes' in st.session_state and st.session_state['pdf_bytes']:
            st.markdown('<div class="luxury-workspace-card">', unsafe_allow_html=True)
            st.markdown('<div class="row-metric-label"><span class="large-icon">👁️</span> 3. PRINT PREVIEW</div>', unsafe_allow_html=True)
            
            # Base64 iframe integration
            base64_pdf = base64.b64encode(st.session_state['pdf_bytes']).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf" style="border: 1px solid #002B49; margin-top: 15px;"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                st.download_button("📥 DOWNLOAD AS PDF", data=st.session_state['pdf_bytes'], file_name="Presentation_Generated.pdf", mime="application/pdf", use_container_width=True)
            with d_col2:
                st.download_button("📥 DOWNLOAD AS PPTX", data=st.session_state['pptx_bytes'], file_name="Presentation_Generated.pptx", mime="application/vnd.openxmlformats-officedocument.presentationml.presentation", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Template Initialization Failure: {str(e)}")
