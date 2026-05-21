import os
import io
import subprocess
import tempfile
import base64
import re
import streamlit as st
import streamlit.components.v1 as components
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
    .preview-panel { border: 1px solid #002B49; background-color: #F8FAFC; height: 850px; display: flex; align-items: center; justify-content: center; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; text-align: center; padding: 20px; }
    
    /* Buttons */
    div.stButton > button { background-color: #002B49 !important; color: #FFFFFF !important; font-weight: 700 !important; font-size: 14px !important; text-transform: uppercase !important; border: none !important; border-radius: 0px !important; border-bottom: 4px solid #C5A059 !important; padding: 12px 24px !important; width: 100% !important; transition: background-color 0.15s ease; }
    div.stButton > button:hover { background-color: #0A3352 !important; border-bottom-color: #C5A059 !important; color: #FFFFFF !important; }
    
    /* Minimalist Radio Toggle Fix */
    div[role="radiogroup"] { flex-direction: row !important; gap: 20px; padding-bottom: 10px; }
    div[role="radiogroup"] label { font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.05em; color: #002B49 !important; }
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
            if shape.has_text_frame:
                text_content = shape.text
                for img_token, img_file in image_inputs.items():
                    if img_token in text_content and img_file is not None:
                        images_to_add.append((img_file, shape.left, shape.top, shape.width, shape.height))
                        shapes_to_delete.append(shape)

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
    # BLOB URL WORKAROUND: Bypasses Chromium Edge/Brave data-uri blocks by rendering in-memory
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    js_blob_injection = f"""
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 0; background-color: #F8FAFC; }}
            #pdf-container {{ width: 100%; height: 850px; border: 1px solid #002B49; box-sizing: border-box; }}
            iframe {{ width: 100%; height: 100%; border: none; }}
        </style>
    </head>
    <body>
        <div id="pdf-container"></div>
        <script>
            const b64 = "{base64_pdf}";
            const binary = atob(b64);
            const array = new Uint8Array(binary.length);
            for(let i = 0; i < binary.length; i++) {{
                array[i] = binary.charCodeAt(i);
            }}
            const blob = new Blob([array], {{type: 'application/pdf'}});
            const url = URL.createObjectURL(blob);
            const iframe = document.createElement('iframe');
            iframe.src = url;
            document.getElementById('pdf-container').appendChild(iframe);
        </script>
    </body>
    </html>
    """
    components.html(js_blob_injection, height=860)

# --- UI HELPERS ---
def dynamic_form_row(icon, label_text, key):
    r_col1, r_col2 = st.columns([9, 11])
    with r_col1: st.markdown(f'<div class="row-metric-label">{icon} {label_text}</div>', unsafe_allow_html=True)
    with r_col2: return st.text_input("", key=key, label_visibility="collapsed")

def dynamic_uploader_row(icon, label_text, allowed_types, key):
    r_col1, r_col2 = st.columns([9, 11])
    with r_col1: st.markdown(f'<div class="row-metric-label">{icon} {label_text}</div>', unsafe_allow_html=True)
    with r_col2: return st.file_uploader(label_text, type=allowed_types, key=key, label_visibility="collapsed")

def dynamic_selector_row(icon, label_text, options, key):
    r_col1, r_col2 = st.columns([9, 11])
    with r_col1: st.markdown(f'<div class="row-metric-label">{icon} {label_text}</div>', unsafe_allow_html=True)
    with r_col2: return st.selectbox(label_text, options, key=key, label_visibility="collapsed")

# --- INIT APP ---
st.set_page_config(page_title="Matrix Generator", layout="wide")
st.markdown(LUXURY_CRE_SYSTEM, unsafe_allow_html=True)

if "preview_pdf" not in st.session_state: st.session_state.preview_pdf = None
if "final_pptx" not in st.session_state: st.session_state.final_pptx = None
if "custom_mapping" not in st.session_state: st.session_state.custom_mapping = {}

# --- MAIN LAYOUT ---
st.markdown("### WORKSPACE PROTOCOL")
app_mode = st.radio("Select Generation Mode:", ["Standard PIS (Legacy Specs)", "Custom Adaptive Template"], horizontal=True, label_visibility="collapsed")
st.markdown("<hr style='margin-top:0px; border-color:#002B49;'>", unsafe_allow_html=True)

col_left, col_right = st.columns([1.1, 1], gap="large")

text_data = {}
image_data = {}

with col_left:
    st.markdown('<div class="luxury-workspace-card">', unsafe_allow_html=True)
    u_template = st.file_uploader("📂 UPLOAD MASTER BLUEPRINT (PPTX)", type=["pptx"])
    st.markdown('</div>', unsafe_allow_html=True)

    if app_mode == "Standard PIS (Legacy Specs)":
        st.markdown('<div class="luxury-workspace-card">', unsafe_allow_html=True)
        prop_location = dynamic_form_row("📍", "Property Location", "cre_loc")
        prop_size     = dynamic_form_row("📐", "Property Size (SQM)", "cre_size")
        prop_type     = dynamic_form_row("🏢", "Property Type", "cre_type")
        prop_address  = dynamic_form_row("🗺️", "Full Address", "cre_addr")
        lease_rates   = dynamic_form_row("💰", "Lease Rates", "cre_rates")
        sec_deposit   = dynamic_form_row("🛡️", "Security Deposit", "cre_sec")
        adv_rent      = dynamic_form_row("💵", "Advance Rent", "cre_adv")
        escalation    = dynamic_form_row("📈", "Rental Escalation", "cre_esc")
        lease_term    = dynamic_form_row("📅", "Lease Term", "cre_term")
        handover      = dynamic_form_row("🏗️", "Handover Condition", "cre_hand")
        prop_high1    = dynamic_form_row("✨", "Property Highlight 1", "cre_high1")
        prop_high2    = dynamic_form_row("✨", "Property Highlight 2", "cre_high2")
        
        contacts_database = {
            "Sondi Tuazon": {"phone": "0917 843 6128", "email": "sondi.tuazon@primephilippines.com"},
            "Meliza Zapata": {"phone": "0996 880 5399", "email": "meliza.zapata@primephilippines.com"},
            "Dykstra Pineda": {"phone": "0920 986 2748", "email": "dykstra.pineda@primephilippines.com"},
            "Cedtrix Rena": {"phone": "0977 653 1494", "email": "cedtriz.rena@primephilippines.com"},
            "Carlo Medina": {"phone": "0920 986 2763", "email": "carlo.medina@primephilippines.com"},
            "Dave Policarpio": {"phone": "0908 865 8945", "email": "dave.policarpio@primephilippines.com"},
            "Irish Rima": {"phone": "0917 000 0000", "email": "irish.rima@primephilippines.com"}
        }
        dropdown_options = ["None"] + list(contacts_database.keys())
        cta1_selection = dynamic_selector_row("📞", "CTA 1", dropdown_options, "web_cta1")
        cta2_selection = dynamic_selector_row("📞", "CTA 2", dropdown_options, "web_cta2")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="luxury-workspace-card">', unsafe_allow_html=True)
        img_types = ["png", "jpg", "jpeg"]
        u_map     = dynamic_uploader_row("🗺️", "Location Map", img_types, "web_mp")
        u_lotplan = dynamic_uploader_row("📐", "Lot Plan", img_types, "web_lp")
        u_photo1  = dynamic_uploader_row("📸", "Property Photo 1", img_types, "web_p1")
        u_photo2  = dynamic_uploader_row("📸", "Property Photo 2", img_types, "web_p2")
        u_photo3  = dynamic_uploader_row("📸", "Property Photo 3", img_types, "web_p3")
        st.markdown('</div>', unsafe_allow_html=True)

        text_data = {
            "{{PROPERTY_LOCATION}}": prop_location, "{{PROPERTY_SIZE}}": prop_size,
            "{{PROPERTY_TYPE}}": prop_type, "{{PROPERTY_ADDRESS}}": prop_address,
            "{{LEASE_RATES}}": lease_rates, "{{SECURITY_DEPOSIT}}": sec_deposit,
            "{{ADVANCE_RENT}}": adv_rent, "{{ESCALATION}}": escalation,
            "{{LEASE TERM}}": lease_term, "{{HANDOVER CONDITION}}": handover,
            "{{PROPERTY_HIGHLIGHTS1}}": prop_high1, "{{PROPERTY_HIGHLIGHTS2}}": prop_high2
        }

        for i, selection in enumerate([cta1_selection, cta2_selection], start=1):
            name_token  = f"{{{{CTA{i}_NAME}}}}"
            phone_token = f"{{{{CTA{i}_CONTACT_NUMBER}}}}"
            email_token = f"{{{{CTA{i}_EMAIL_ADDRESS}}}}"
            
            if selection and selection != "None":
                text_data[name_token]  = selection
                text_data[phone_token] = contacts_database[selection]["phone"]
                text_data[email_token] = contacts_database[selection]["email"]
            else:
                text_data[name_token], text_data[phone_token], text_data[email_token] = "", "", ""
                
        image_data = {
            "{{PROPERTY_PHOTO1}}": u_photo1, "{{PROPERTY_LOCATION_MAP}}": u_map,
            "{{PROPERTY_LOTPLAN}}": u_lotplan, "{{PROPERTY_PHOTO2}}": u_photo2,
            "{{PROPERTY_PHOTO3}}": u_photo3
        }

    elif app_mode == "Custom Adaptive Template" and u_template is not None:
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
    elif app_mode == "Custom Adaptive Template" and u_template is None:
        st.warning("⚠️ Please upload a Master Blueprint (PPTX) to map dynamic placeholders.")

    # --- CONTROL DESK ACTION LAYER ---
    st.markdown("<div style='margin-top: 10px; border-top: 1px solid #002B49; padding-top: 20px;'></div>", unsafe_allow_html=True)
    btn_col1, btn_col2, btn_col3 = st.columns(3)

    if u_template:
        with btn_col1:
            if st.button("👁️ GENERATE PREVIEW"):
                with st.spinner("Processing Matrix Assets & Rendering PDF..."):
                    try:
                        raw_pptx = generate_pptx_bytes(u_template.getvalue(), text_data, image_data)
                        pdf_bytes = convert_pptx_to_pdf(raw_pptx)
                        st.session_state.preview_pdf = pdf_bytes
                        st.session_state.final_pptx = raw_pptx
                    except Exception as e:
                        st.error(f"Compilation core failure log description: {e}")

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
        st.markdown('<div class="preview-panel">WAITING FOR PREVIEW RENDERING PROTOCOL<br><br><span style="font-size:12px; font-weight:400; color:#94A3B8;">(Upload template, input data, and click Generate Preview)</span></div>', unsafe_allow_html=True)
