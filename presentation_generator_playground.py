import os
import io
import subprocess
import tempfile
import re
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
    
    /* Radio */
    div[role="radiogroup"] { flex-direction: row !important; gap: 20px; padding-bottom: 10px; }
    div[role="radiogroup"] label { font-weight: 600 !important; color: #1A1A1A !important; }
    
    /* Labels */
    .field-label { font-size: 13px !important; font-weight: 600 !important; color: #1A1A1A !important; padding-top: 8px; }
    .section-header { font-size: 16px !important; font-weight: 700 !important; color: #1A1A1A !important; margin-bottom: 12px; }
    
    hr { margin: 16px 0 !important; border-color: #E0E0E0 !important; }
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

        # Second pass: replace text
        for shape in slide.shapes:
            if shape not in shapes_to_delete:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        full_text = paragraph.text
                        modified = False
                        for token, value in text_inputs.items():
                            if token in full_text:
                                full_text = full_text.replace(token, str(value) if value else '')
                                modified = True
                        if modified:
                            # Clear and rebuild the paragraph
                            paragraph.clear()
                            run = paragraph.add_run()
                            run.text = full_text
                
                if hasattr(shape, 'table') and shape.table:
                    for row in shape.table.rows:
                        for cell in row.cells:
                            if cell.text_frame:
                                for paragraph in cell.text_frame.paragraphs:
                                    full_text = paragraph.text
                                    modified = False
                                    for token, value in text_inputs.items():
                                        if token in full_text:
                                            full_text = full_text.replace(token, str(value) if value else '')
                                            modified = True
                                    if modified:
                                        paragraph.clear()
                                        run = paragraph.add_run()
                                        run.text = full_text

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

# --- UI HELPERS ---
def simple_form_row(label_text, key, placeholder=""):
    st.markdown(f'<div class="field-label">{label_text}</div>', unsafe_allow_html=True)
    return st.text_input("", key=key, label_visibility="collapsed", placeholder=placeholder)

def simple_textarea_row(label_text, key, placeholder=""):
    st.markdown(f'<div class="field-label">{label_text}</div>', unsafe_allow_html=True)
    return st.text_area("", key=key, label_visibility="collapsed", placeholder=placeholder, height=100)

def simple_uploader_row(label_text, allowed_types, key):
    st.markdown(f'<div class="field-label">{label_text}</div>', unsafe_allow_html=True)
    return st.file_uploader(label_text, type=allowed_types, key=key, label_visibility="collapsed")

def simple_selector_row(label_text, options, key):
    st.markdown(f'<div class="field-label">{label_text}</div>', unsafe_allow_html=True)
    return st.selectbox(label_text, options, key=key, label_visibility="collapsed")

# --- INIT APP ---
st.set_page_config(page_title="Document Generator", layout="wide")
st.markdown(MINIMAL_CRE_SYSTEM, unsafe_allow_html=True)

if "final_pptx" not in st.session_state:
    st.session_state.final_pptx = None
if "final_pdf" not in st.session_state:
    st.session_state.final_pdf = None
if "custom_mapping" not in st.session_state:
    st.session_state.custom_mapping = {}
if "tokens" not in st.session_state:
    st.session_state.tokens = []

# --- MAIN LAYOUT ---
st.markdown('<h2 style="font-weight: 700; color: #1A1A1A; margin-bottom: 4px;">Document Generator</h2>', unsafe_allow_html=True)

app_mode = st.radio("Select Mode:", ["Standard PIS", "Custom Template"], horizontal=True, label_visibility="collapsed")
st.markdown("<hr>", unsafe_allow_html=True)

# 3-COLUMN LAYOUT
col_in1, col_in2, col_out = st.columns([1, 1, 1.2], gap="medium")

text_data = {}
image_data = {}

# Global PPTX Upload
with col_in1:
    st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Upload Template</div>', unsafe_allow_html=True)
    u_template = st.file_uploader("Master Blueprint (PPTX)", type=["pptx"], label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

if app_mode == "Standard PIS":
    with col_in1:
        st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Property Details</div>', unsafe_allow_html=True)
        prop_location = simple_form_row("Property Location", "cre_loc")
        prop_size = simple_form_row("Property Size (SQM)", "cre_size")
        prop_type = simple_form_row("Property Type", "cre_type")
        prop_address = simple_form_row("Full Address", "cre_addr")
        lease_rates = simple_form_row("Lease Rates", "cre_rates")
        sec_deposit = simple_form_row("Security Deposit", "cre_sec")
        adv_rent = simple_form_row("Advance Rent", "cre_adv")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_in2:
        st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Additional Information</div>', unsafe_allow_html=True)
        escalation = simple_form_row("Rental Escalation", "cre_esc")
        lease_term = simple_form_row("Lease Term", "cre_term")
        handover = simple_form_row("Handover Condition", "cre_hand")
        prop_high1 = simple_form_row("Property Highlight 1", "cre_high1")
        prop_high2 = simple_form_row("Property Highlight 2", "cre_high2")
        
        contacts_database = {
            "Sondi Tuazon": {"phone": "0917 843 6128", "email": "sondi.tuazon@primephilippines.com"},
            "Meliza Zapata": {"phone": "0996 880 5399", "email": "meliza.zapata@primephilippines.com"},
            "Dykstra Pineda": {"phone": "0920 986 2748", "email": "dykstra.pineda@primephilippines.com"},
            "Cedtrix Rena": {"phone": "0977 653 1494", "email": "cedtriz.rena@primephilippines.com"},
            "Carlo Medina": {"phone": "0920 986 2763", "email": "carlo.medina@primephilippines.com"},
            "Dave Policarpio": {"phone": "0908 865 8945", "email": "dave.policarpio@primephilippines.com"}
        }
        dropdown_options = ["None"] + list(contacts_database.keys())
        cta1_selection = simple_selector_row("CTA Contact", dropdown_options, "web_cta1")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">Images</div>', unsafe_allow_html=True)
        img_types = ["png", "jpg", "jpeg"]
        u_map = simple_uploader_row("Location Map", img_types, "web_mp")
        u_lotplan = simple_uploader_row("Lot Plan", img_types, "web_lp")
        u_photo1 = simple_uploader_row("Property Photo 1", img_types, "web_p1")
        st.markdown('</div>', unsafe_allow_html=True)

    text_data = {
        "{{PROPERTY_LOCATION}}": prop_location,
        "{{PROPERTY_SIZE}}": prop_size,
        "{{PROPERTY_TYPE}}": prop_type,
        "{{PROPERTY_ADDRESS}}": prop_address,
        "{{LEASE_RATES}}": lease_rates,
        "{{SECURITY_DEPOSIT}}": sec_deposit,
        "{{ADVANCE_RENT}}": adv_rent,
        "{{ESCALATION}}": escalation,
        "{{LEASE TERM}}": lease_term,
        "{{HANDOVER CONDITION}}": handover,
        "{{PROPERTY_HIGHLIGHTS1}}": prop_high1,
        "{{PROPERTY_HIGHLIGHTS2}}": prop_high2
    }
    
    if cta1_selection != "None":
        text_data["{{CTA1_NAME}}"] = cta1_selection
        text_data["{{CTA1_CONTACT_NUMBER}}"] = contacts_database[cta1_selection]["phone"]
        text_data["{{CTA1_EMAIL_ADDRESS}}"] = contacts_database[cta1_selection]["email"]
    
    image_data = {
        "{{PROPERTY_PHOTO1}}": u_photo1,
        "{{PROPERTY_LOCATION_MAP}}": u_map,
        "{{PROPERTY_LOTPLAN}}": u_lotplan
    }

elif app_mode == "Custom Template" and u_template is not None:
    raw_bytes = u_template.getvalue()
    tokens = extract_placeholders(raw_bytes)
    st.session_state.tokens = tokens
    
    if not tokens:
        with col_in1:
            st.info("No placeholders found in the uploaded template.")
    else:
        # Distribute tokens evenly between columns
        mid_point = len(tokens) // 2
        col1_tokens = tokens[:mid_point]
        col2_tokens = tokens[mid_point:]
        
        with col_in1:
            st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Field Values</div>', unsafe_allow_html=True)
            for token in col1_tokens:
                t_type = st.session_state.custom_mapping.get(token, "Short Text")
                clean_label = token.replace("{", "").replace("}", "")
                
                if t_type == "Short Text":
                    text_data[token] = simple_form_row(clean_label, f"val_{token}")
                elif t_type == "Paragraph":
                    text_data[token] = simple_textarea_row(clean_label, f"val_{token}")
                elif t_type == "Image":
                    image_data[token] = simple_uploader_row(clean_label, ["png", "jpg", "jpeg"], f"val_{token}")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_in2:
            st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header">Field Values</div>', unsafe_allow_html=True)
            for token in col2_tokens:
                t_type = st.session_state.custom_mapping.get(token, "Short Text")
                clean_label = token.replace("{", "").replace("}", "")
                
                if t_type == "Short Text":
                    text_data[token] = simple_form_row(clean_label, f"val_{token}")
                elif t_type == "Paragraph":
                    text_data[token] = simple_textarea_row(clean_label, f"val_{token}")
                elif t_type == "Image":
                    image_data[token] = simple_uploader_row(clean_label, ["png", "jpg", "jpeg"], f"val_{token}")
            st.markdown('</div>', unsafe_allow_html=True)

# --- 3RD COLUMN: CONFIGURATION AND EXPORT ---
with col_out:
    if app_mode == "Custom Template" and u_template is not None and st.session_state.tokens:
        st.markdown('<div class="config-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Configuration</div>', unsafe_allow_html=True)
        
        # Upload Config
        u_json = st.file_uploader("Load Config (JSON)", type=["json"])
        if u_json is not None:
            try:
                loaded_config = json.load(u_json)
                st.session_state.custom_mapping.update(loaded_config)
                st.success("Configuration loaded")
            except Exception:
                st.error("Invalid JSON file")

        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Mapping
        st.markdown('<div class="section-header">Data Type Mapping</div>', unsafe_allow_html=True)
        valid_types = ["Short Text", "Paragraph", "Image"]
        
        for token in st.session_state.tokens:
            raw_type = st.session_state.custom_mapping.get(token, "Short Text")
            safe_type = raw_type if raw_type in valid_types else "Short Text"
            
            new_type = st.selectbox(
                f"{token}",
                valid_types,
                index=valid_types.index(safe_type),
                key=f"config_{token}",
                label_visibility="collapsed"
            )
            st.session_state.custom_mapping[token] = new_type
        
        # Export Config
        st.markdown("<hr>", unsafe_allow_html=True)
        config_json_str = json.dumps(st.session_state.custom_mapping, indent=4)
        st.download_button(
            label="Save Configuration",
            data=config_json_str,
            file_name="template_config.json",
            mime="application/json",
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # --- GENERATION SECTION ---
    st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Generate Document</div>', unsafe_allow_html=True)
    
    if u_template:
        if st.button("Generate Presentation", use_container_width=True):
            with st.spinner("Generating document..."):
                try:
                    raw_pptx = generate_pptx_bytes(u_template.getvalue(), text_data, image_data)
                    st.session_state.final_pptx = raw_pptx
                    st.session_state.final_pdf = convert_pptx_to_pdf(raw_pptx)
                    st.success("Document generated successfully")
                except Exception as e:
                    st.error(f"Error: {e}")

        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Downloads
        dl_col1, dl_col2 = st.columns(2)
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
    else:
        st.info("Upload a template to enable generation")
        
    st.markdown('</div>', unsafe_allow_html=True)
