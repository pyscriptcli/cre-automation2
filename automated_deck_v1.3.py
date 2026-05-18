import os
import io
import streamlit as st
from pptx import Presentation
from PIL import Image

# --- PRIME PHILIPPINES BRANDED CSS OVERRIDE ---
BRAND_CSS = """
<style>
    /* Force canvas background color */
    .stApp {
        background-color: #F8FAFC !important;
        color: #1E293B !important;
        font-family: 'Inter', 'Helvetica Neue', sans-serif !important;
    }
    
    /* Input Fields Styling: Sharp edges and corporate borders */
    div[data-baseweb="input"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 2px !important; /* Sharp corporate corners */
        transition: border-color 0.15s ease-in-out;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #C5A059 !important; /* Gold accent on active focus */
        box-shadow: none !important;
    }
    input {
        color: #1E293B !important;
        font-size: 14px !important;
    }
    
    /* File Uploader styling */
    section[data-testid="stFileUploader"] {
        background-color: #FFFFFF !important;
        border: 1px dashed #E2E8F0 !important;
        border-radius: 2px !important;
    }

    /* Section Header styling */
    .section-header {
        font-size: 12px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #002B49 !important;
        border-bottom: 1px solid #E2E8F0;
        padding-bottom: 6px;
        margin-top: 25px;
        margin-bottom: 15px;
    }
    
    /* Premium Asymmetric Left Border for Form Context */
    .metric-card-wrapper {
        border-left: 4px solid #C5A059 !important;
        background-color: #FFFFFF;
        padding: 10px;
        border-top: 1px solid #E2E8F0;
        border-right: 1px solid #E2E8F0;
        border-bottom: 1px solid #E2E8F0;
        border-radius: 2px;
    }

    /* Primary Generate Button Override */
    div.stButton > button:first-child {
        background-color: #002B49 !important; /* Deep Navy Base */
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        border: none !important;
        border-radius: 2px !important;
        border-bottom: 3px solid #C5A059 !important; /* Rigid Gold base border line */
        padding: 12px 24px !important;
        width: 100% !important;
        transition: background-color 0.15s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #0F3B59 !important;
        color: #FFFFFF !important;
    }
    
    /* Secondary Reset Button Override */
    div.stButton > button[key="reset_btn"] {
        background-color: transparent !important;
        color: #64748B !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 2px !important;
    }
    div.stButton > button[key="reset_btn"]:hover {
        color: #1E293B !important;
        border-color: #64748B !important;
    }
</style>
"""

# --- OBJECT-FIT COVER CROP ENGINE ---
def smart_crop_to_fit(img_file, target_w_emu, target_h_emu):
    try:
        img = Image.open(img_file)
        img_w, img_h = img.size
        target_ratio = target_w_emu / target_h_emu
        img_ratio = img_w / img_h
        
        if img_ratio > target_ratio:
            new_w = int(img_h * target_ratio)
            left = (img_w - new_w) // 2
            right = left + new_w
            img = img.crop((left, 0, right, img_h))
        else:
            new_h = int(img_w / target_ratio)
            top = (img_h - new_h) // 2
            bottom = top + new_h
            img = img.crop((0, top, img_w, bottom))
            
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr
    except Exception:
        return img_file

# --- APP CONFIGURATION & RENDERING ---
st.set_page_config(page_title="PRIME App Engine", page_icon="🏢", layout="wide")
st.markdown(BRAND_CSS, unsafe_allow_html=True)

# App Title Banner mimicking a native internal portal header
st.markdown("<h2 style='color:#002B49; font-weight:700; font-size:22px; margin-bottom:20px;'>🏢 PRIME Philippines Asset Pitch Engine</h2>", unsafe_allow_html=True)

# HIGH DENSITY MATRIX FORM LAYOUT (Horizontal alignment grid)
def dense_input_row(icon, label_text, default_val, state_key):
    col1, col2 = st.columns([2, 3])
    with col1:
        st.markdown(f"<div style='padding-top: 28px; font-size: 13px; font-weight: 500; color: #64748B;'>{icon} {label_text}</div>", unsafe_allow_html=True)
    with col2:
        return st.text_input("", value=default_val, key=state_key, label_visibility="collapsed")

# Main Split Pane Workspace
left_panel, right_panel = st.columns([1, 1], gap="large")

with left_panel:
    st.markdown('<div class="section-header">--- TEXT DATA METADATA ---</div>', unsafe_allow_html=True)
    
    prop_location = dense_input_row("📍", "Property Location:", "Tagaytay, Cavite", "loc")
    prop_size     = dense_input_row("📐", "Property Size (SQM):", "386", "size")
    prop_type     = dense_input_row("🏢", "Property Type:", "Commercial Space", "type")
    prop_address  = dense_input_row("🗺️", "Full Address:", "Mendez Crossing East, Tagaytay City, Cavite", "addr")
    lease_rates   = dense_input_row("💰", "Lease Rates:", "200,000 per month", "rates")
    sec_deposit   = dense_input_row("🌓", "Security Deposit:", "3 months", "sec")
    adv_rent      = dense_input_row("💵", "Advance Rent:", "3 months", "adv")
    escalation    = dense_input_row("📈", "Escalation:", "5%", "esc")
    lease_term    = dense_input_row("📅", "Lease Term:", "5 years", "term")
    handover      = dense_input_row("🏗️", "Handover Condition:", "As is where is", "hand")

with right_panel:
    st.markdown('<div class="section-header">--- IMAGE ASSETS ARCHIVE ---</div>', unsafe_allow_html=True)
    u_photo1  = st.file_uploader("📸 Property Photo 1", type=["png", "jpg", "jpeg"], key="p1")
    u_map     = st.file_uploader("🗺️ Location Map", type=["png", "jpg", "jpeg"], key="mp")
    u_lotplan = st.file_uploader("📐 Lot Plan", type=["png", "jpg", "jpeg"], key="lp")
    u_photo2  = st.file_uploader("📸 Property Photo 2", type=["png", "jpg", "jpeg"], key="p2")
    u_photo3  = st.file_uploader("📸 Property Photo 3", type=["png", "jpg", "jpeg"], key="p3")

    st.markdown('<div class="section-header">--- PRODUCTION COMPILER ARCHITECTURE ---</div>', unsafe_allow_html=True)
    u_template = st.file_uploader("📂 Master Template PPTX Blueprint", type=["pptx"], key="tpl")

# Unified Dictionaries for mapping pipelines
data_inputs = {
    "{{PROPERTY_LOCATION}}": prop_location, "{{PROPERTY_SIZE}}": prop_size,
    "{{PROPERTY_TYPE}}": prop_type, "{{PROPERTY_ADDRESS}}": prop_address,
    "{{LEASE_RATES}}": lease_rates, "{{SECURITY_DEPOSIT}}": sec_deposit,
    "{{ADVANCE_RENT}}": adv_rent, "{{ESCALATION}}": escalation,
    "{{LEASE TERM}}": lease_term, "{{HANDOVER CONDITION}}": handover
}

image_inputs = {
    "{{PROPERTY_PHOTO 1}}": u_photo1, "{{PROPERTY_LOCATION_MAP}}": u_map,
    "{{PROPERTY_LOTPLAN}}": u_lotplan, "{{PROPERTY_PHOTO2}}": u_photo2,
    "{{PROPERTY_PHOTO3}}": u_photo3
}

# --- PERSISTENT FOOTER CONTROL LAYER ---
st.markdown("<div style='margin-top: 30px; border-t: 1px solid #E2E8F0;'></div>", unsafe_allow_html=True)
footer_col1, footer_col2 = st.columns([1, 4])

with footer_col1:
    if st.button("↺ RESET FORM", key="reset_btn", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with footer_col2:
    if u_template is None:
        st.markdown("<div style='padding-top:12px; font-size:12px; color:#64748B; text-align:right;'>⚠️ Upload a Master Template PPTX file to unlock the generation engine.</div>", unsafe_allow_html=True)
    else:
        if st.button("⚙️ GENERATE DECK", key="gen_btn", use_container_width=True):
            with st.spinner("Executing OpenXML parsing and spatial aspect ratio image corrections..."):
                try:
                    prs = Presentation(u_template)
                    
                    for slide in prs.slides:
                        shapes_to_delete = []
                        images_to_add = []

                        for shape in slide.shapes:
                            if shape.has_text_frame and not any(img_token in shape.text_frame.text for img_token in image_inputs):
                                for paragraph in shape.text_frame.paragraphs:
                                    for run in paragraph.runs:
                                        for token, value in data_inputs.items():
                                            if token in run.text:
                                                run.text = run.text.replace(token, value)

                            if shape.has_table:
                                for row in shape.table.rows:
                                    for cell in row.cells:
                                        for paragraph in cell.text_frame.paragraphs:
                                            for run in paragraph.runs:
                                                for token, value in data_inputs.items():
                                                    if token in run.text:
                                                        run.text = run.text.replace(token, value)

                            if shape.has_text_frame:
                                text_content = shape.text_frame.text
                                for img_token, img_file in image_inputs.items():
                                    if img_token in text_content and img_file is not None:
                                        images_to_add.append((img_file, shape.left, shape.top, shape.width, shape.height))
                                        shapes_to_delete.append(shape)

                        for img_file, left, top, width, height in images_to_add:
                            processed_img = smart_crop_to_fit(img_file, width, height)
                            slide.shapes.add_picture(processed_img, left, top, width=width, height=height)

                        for old_shape in shapes_to_delete:
                            sp = old_shape._element
                            sp.getparent().remove(sp)

                    output_stream = io.BytesIO()
                    prs.save(output_stream)
                    output_stream.seek(0)
                    
                    st.markdown('<div class="metric-card-wrapper" style="margin-top:15px; text-align:center;"><b>🎉 Presentation Compiled Successfully!</b> Your file is optimized and cached in active application memory.</div>', unsafe_allow_html=True)
                    
                    st.download_button(
                        label="📥 DOWNLOAD PPTX DECK",
                        data=output_stream,
                        file_name=f"PIS_{prop_location.replace(' ', '_')}.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"Runtime execution compilation failure: {str(e)}")
