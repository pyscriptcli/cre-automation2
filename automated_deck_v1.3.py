import os
import io
import streamlit as st
from pptx import Presentation
from PIL import Image

# --- UNCONVENTIONAL HIGH-END CRE DESIGN SYSTEM ---
EXECUTIVE_WORKSPACE_CSS = """
<style>
    /* 1. Global Page Core Reset */
    .stApp {
        background-color: #F8FAFC !important;
        color: #1E293B !important;
        font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif !important;
    }
    
    /* 2. Remove standard Streamlit top layout header padding */
    div[data-testid="stHeader"] {
        background-color: transparent !important;
    }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px !important;
    }
    
    /* 3. High-Density Form Inputs & Absolute Dark Block Deletion */
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[role="textbox"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 2px !important; /* Premium sharp edges */
        color: #002B49 !important;
        transition: border-color 0.15s ease-in-out !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #C5A059 !important; /* Elegant corporate gold accent */
        box-shadow: none !important;
    }
    
    /* Force crisp white backgrounds and navy text to eliminate dark overlays */
    input[type="text"], .stTextInput input {
        color: #002B49 !important;
        background-color: #FFFFFF !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        padding: 8px 12px !important;
    }
    
    /* 4. Minimalist Executive File Uploaders */
    section[data-testid="stFileUploader"] {
        background-color: #FFFFFF !important;
        border: 1px dashed #CBD5E1 !important;
        border-radius: 2px !important;
        padding: 8px !important;
        transition: border-color 0.15s ease !important;
    }
    section[data-testid="stFileUploader"]:hover {
        border-color: #C5A059 !important;
    }
    section[data-testid="stFileUploader"] div, section[data-testid="stFileUploader"] span {
        color: #64748B !important;
        font-size: 11px !important;
    }
    
    /* Hide default upload label string layouts since custom grids are used */
    div[data-testid="stFileUploader"] label {
        display: none !important;
    }
    
    /* 5. Custom Typography Row Elements */
    .row-metric-label {
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        color: #475569 !important;
        padding-top: 10px;
    }
    
    /* 6. Asymmetric Workspace Border Framework */
    .workspace-section-card {
        background-color: #FFFFFF;
        border-top: 3px solid #002B49; /* Deep Navy Header Strip */
        border-left: 1px solid #E2E8F0;
        border-right: 1px solid #E2E8F0;
        border-bottom: 1px solid #E2E8F0;
        border-radius: 2px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.02);
    }
    
    .section-title-tag {
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        color: #C5A059 !important; /* Gold category subline */
        margin-bottom: 16px;
        display: block;
    }

    /* 7. Action Button Overrides */
    div.stButton > button {
        background-color: #002B49 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        border: none !important;
        border-radius: 2px !important;
        border-bottom: 3px solid #C5A059 !important; /* Corporate Gold Base Base Line */
        padding: 14px 28px !important;
        width: 100% !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.15s ease;
    }
    div.stButton > button:hover {
        background-color: #0B3654 !important;
        border-bottom-color: #C5A059 !important;
        color: #FFFFFF !important;
        transform: translateY(-1px);
    }
    
    /* Reset Button alternative alignment */
    div[data-testid="column"] div.stButton > button[key="reset_btn_key"] {
        background-color: transparent !important;
        color: #94A3B8 !important;
        border: 1px solid #E2E8F0 !important;
        border-bottom: 1px solid #E2E8F0 !important;
        padding: 10px 20px !important;
    }
    div[data-testid="column"] div.stButton > button[key="reset_btn_key"]:hover {
        color: #475569 !important;
        border-color: #94A3B8 !important;
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

# --- APP LAYOUT STREAM INITIALIZATION ---
st.set_page_config(page_title="Workspace Engine", page_icon="🏢", layout="wide")
st.markdown(EXECUTIVE_WORKSPACE_CSS, unsafe_allow_html=True)

# HIGH DENSITY GRID ROW CONTEXT HELPER
def matrix_row(icon, label_text, default_val, state_key):
    r_col1, r_col2 = st.columns([5, 7])
    with r_col1:
        st.markdown(f'<div class="row-metric-label">{icon} {label_text}</div>', unsafe_allow_html=True)
    with r_col2:
        return st.text_input("", value=default_val, key=state_key, label_visibility="collapsed")

def uploader_row(icon, label_text, state_key):
    r_col1, r_col2 = st.columns([5, 7])
    with r_col1:
        st.markdown(f'<div class="row-metric-label">{icon} {label_text}</div>', unsafe_allow_html=True)
    with r_col2:
        return st.file_uploader(label_text, type=["png", "jpg", "jpeg"], key=state_key)

# Main Multi-Card Dashboard Workspace Partition
workspace_left, workspace_right = st.columns([11, 10], gap="large")

with workspace_left:
    st.markdown('<div class="workspace-section-card">', unsafe_allow_html=True)
    st.markdown('<span class="section-title-tag">DATA METADATA GRID</span>', unsafe_allow_html=True)
    
    prop_location = matrix_row("📍", "Property Location", "Tagaytay, Cavite", "cre_loc")
    prop_size     = matrix_row("📐", "Property Size (SQM)", "386", "cre_size")
    prop_type     = matrix_row("🏢", "Property Type", "Commercial Space", "cre_type")
    prop_address  = matrix_row("🗺️", "Full Address", "Mendez Crossing East, Tagaytay City, Cavite", "cre_addr")
    lease_rates   = matrix_row("💰", "Lease Rates", "200,000 per month", "cre_rates")
    sec_deposit   = matrix_row("🛡️", "Security Deposit", "3 months", "cre_sec")
    adv_rent      = matrix_row("💵", "Advance Rent", "3 months", "cre_adv")
    escalation    = matrix_row("📈", "Rental Escalation", "5%", "cre_esc")
    lease_term    = matrix_row("📅", "Lease Term", "5 years", "cre_term")
    handover      = matrix_row("🏗️", "Handover Condition", "As is where is", "cre_hand")
    st.markdown('</div>', unsafe_allow_html=True)

with workspace_right:
    st.markdown('<div class="workspace-section-card">', unsafe_allow_html=True)
    st.markdown('<span class="section-title-tag">ASSET STORAGE STREAM</span>', unsafe_allow_html=True)
    
    u_photo1  = uploader_row("📸", "Property Photo 1", "web_p1")
    u_map     = uploader_row("🗺️", "Location Map", "web_mp")
    u_lotplan = uploader_row("📐", "Lot Plan Layout", "web_lp")
    u_photo2  = uploader_row("📸", "Property Photo 2", "web_p2")
    u_photo3  = uploader_row("📸", "Property Photo 3", "web_p3")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="workspace-section-card">', unsafe_allow_html=True)
    st.markdown('<span class="section-title-tag">BLUEPRINT LAYOUT MODEL</span>', unsafe_allow_html=True)
    
    t_col1, t_col2 = st.columns([5, 7])
    with t_col1:
        st.markdown('<div class="row-metric-label">📂 Master PPTX Template</div>', unsafe_allow_html=True)
    with t_col2:
        u_template = st.file_uploader("Template File", type=["pptx"], key="web_tpl")
    st.markdown('</div>', unsafe_allow_html=True)

# Central Data Pipelines Mapping
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

# --- CONTROL DESK ANCHOR ZONE ---
st.markdown("<div style='margin-top: 10px; border-top: 1px solid #E2E8F0; padding-top: 20px;'></div>", unsafe_allow_html=True)
action_col1, action_col2 = st.columns([1, 3])

with action_col1:
    if st.button("↺ Clear Fields", key="reset_btn_key", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with action_col2:
    if u_template is None:
        st.markdown("<div style='padding-top:14px; font-size:12px; color:#64748B; text-align:right;'>⚠️ Connect a local master PPTX layout blueprint to mount the compilation deck.</div>", unsafe_allow_html=True)
    else:
        if st.button("⚙️ GENERATE DECK", key="generate_btn_key", use_container_width=True):
            with st.spinner("Processing slides and applying smart image crops..."):
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
                    
                    st.markdown('<div style="border-left:4px solid #C5A059; background-color:#FFFFFF; padding:15px; border-top:1px solid #E2E8F0; border-right:1px solid #E2E8F0; border-bottom:1px solid #E2E8F0; border-radius:2px; margin-top:15px; text-align:center; color:#002B49; font-weight:600; font-size:14px;">🎉 Presentation compiled successfully! Ready for production download.</div>', unsafe_allow_html=True)
                    
                    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
                    st.download_button(
                        label="📥 DOWNLOAD BRANDED PPTX DECK",
                        data=output_stream,
                        file_name=f"PIS_{prop_location.replace(' ', '_')}.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"Compilation pipeline fault: {str(e)}")
