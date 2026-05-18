import os
import io
import sys
import subprocess
import streamlit as st
from pptx import Presentation
from PIL import Image

# --- BULLETPROOF COMPONENT RESET LAYER ---
PRIME_UI_ENGINE = """
<style>
    /* 1. Global Canvas Reset */
    .stApp {
        background-color: #F8FAFC !important;
        color: #1E293B !important;
    }
    
    /* 2. Container Surface Cards */
    div[data-testid="stContainer"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 4px !important;
        padding: 24px !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05) !important;
    }
    
    /* 3. Global Input Fields Reset (Fixes the dark-on-dark bug) */
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[role="textbox"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 2px !important;
        color: #1E293B !important;
    }
    
    /* Target raw input text fields directly */
    input[type="text"], .stTextInput input {
        color: #1E293B !important;
        background-color: #FFFFFF !important;
        font-size: 14px !important;
    }
    
    /* Input field focus state */
    div[data-baseweb="input"]:focus-within {
        border-color: #C5A059 !important;
        box-shadow: none !important;
    }
    
    /* 4. Structural Form Label Typography */
    div[data-testid="stTextInput"] label p, div[data-testid="stFileUploader"] label p {
        color: #002B49 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        letter-spacing: 0.02em !important;
    }
    
    /* 5. File Uploader Layout Adjustments */
    section[data-testid="stFileUploader"] {
        background-color: #FAFAFA !important;
        border: 1px dashed #C5A059 !important; /* Gold dash border accent */
        border-radius: 2px !important;
    }
    section[data-testid="stFileUploader"] div, section[data-testid="stFileUploader"] span {
        color: #64748B !important;
    }

    /* 6. Asymmetric Left Gold Accent Header Box */
    .premium-header-box {
        border-left: 4px solid #C5A059;
        padding-left: 12px;
        margin-bottom: 20px;
        margin-top: 10px;
    }
    .premium-header-box h3 {
        font-size: 13px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        color: #002B49 !important;
        margin: 0 !important;
    }

    /* 7. Action Button Overrides */
    button[data-testid="baseButton-secondary"] {
        border-radius: 2px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        font-size: 13px !important;
        transition: all 0.2s ease !important;
    }
    
    /* Target the generate button using the specific unique markup identifier */
    div.stButton > button {
        background-color: #002B49 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-bottom: 3px solid #C5A059 !important; /* Institutional Gold Edge */
        padding: 12px 30px !important;
    }
    div.stButton > button:hover {
        background-color: #0F3B59 !important;
        color: #FFFFFF !important;
        border-bottom-color: #C5A059 !important;
    }
    
    /* Target the reset button layout specifically */
    div[data-testid="stHorizontalBlock"] div.stButton > button {
        background-color: transparent !important;
        color: #64748B !important;
        border: 1px solid #E2E8F0 !important;
    }
    div[data-testid="stHorizontalBlock"] div.stButton > button:hover {
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

# --- APP LAYOUT EXECUTION ---
st.set_page_config(page_title="PRIME Pitch Engine", page_icon="🏢", layout="wide")
st.markdown(PRIME_UI_ENGINE, unsafe_allow_html=True)

# Portal Header Block
st.markdown("<h2 style='color:#002B49; font-weight:700; font-size:24px; margin-bottom:4px;'>🏢 PRIME Philippines</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:#64748B; font-size:13px; margin-bottom:25px;'>Commercial Real Estate Automated Pitch Deck Compiler</p>", unsafe_allow_html=True)

# Main Two-Column Panel System
left_panel, right_panel = st.columns([1, 1], gap="large")

with left_panel:
    with st.container():
        st.markdown('<div class="premium-header-box"><h3>--- Property Text Metrics ---</h3></div>', unsafe_allow_html=True)
        
        prop_location = st.text_input("📍 Property Location", "Tagaytay, Cavite")
        prop_size     = st.text_input("📐 Property Size (SQM)", "386")
        prop_type     = st.text_input("🏢 Property Type", "Commercial Space")
        prop_address  = st.text_input("🗺️ Full Address", "Mendez Crossing East, Tagaytay City, Cavite")
        lease_rates   = st.text_input("💰 Lease Rates", "200,000 per month")
        sec_deposit   = st.text_input("🌓 Security Deposit", "3 months")
        adv_rent      = st.text_input("💵 Advance Rent", "3 months")
        escalation    = st.text_input("📈 Escalation", "5%")
        lease_term    = st.text_input("📅 Lease Term", "5 years")
        handover      = st.text_input("🏗️ Handover Condition", "As is where is")

with right_panel:
    with st.container():
        st.markdown('<div class="premium-header-box"><h3>--- Branded Asset Archive ---</h3></div>', unsafe_allow_html=True)
        u_photo1  = st.file_uploader("📸 Property Photo 1 Container", type=["png", "jpg", "jpeg"])
        u_map     = st.file_uploader("🗺️ Location Map Container", type=["png", "jpg", "jpeg"])
        u_lotplan = st.file_uploader("📐 Lot Plan Container", type=["png", "jpg", "jpeg"])
        u_photo2  = st.file_uploader("📸 Property Photo 2 Container", type=["png", "jpg", "jpeg"])
        u_photo3  = st.file_uploader("📸 Property Photo 3 Container", type=["png", "jpg", "jpeg"])

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="premium-header-box"><h3>--- System Blueprint ---</h3></div>', unsafe_allow_html=True)
        u_template = st.file_uploader("📂 Upload Master Template PPTX File", type=["pptx"])

# Data Processing Arrays
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

# --- PERSISTENT FOOTER CONTROL STRIP ---
st.markdown("<div style='margin-top: 30px; border-top: 1px solid #E2E8F0; padding-top: 20px;'></div>", unsafe_allow_html=True)
control_col1, control_col2 = st.columns([1, 3])

with control_col1:
    if st.button("↺ Reset Parameters", use_container_width=True):
        st.rerun()

with control_col2:
    if u_template is None:
        st.markdown("<div style='padding-top:14px; font-size:12px; color:#64748B; text-align:right;'>⚠️ Connect a Master Template blueprint file above to activate deployment functions.</div>", unsafe_allow_html=True)
    else:
        if st.button("⚙️ GENERATE DECK BUILD", use_container_width=True):
            with st.spinner("Parsing layout trees and applying smart graphic crops..."):
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
                    
                    st.success("🎉 Presentation compiled successfully!")
                    
                    st.download_button(
                        label="📥 DOWNLOAD BRANDED PPTX DECK",
                        data=output_stream,
                        file_name=f"PIS_{prop_location.replace(' ', '_')}.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"Compilation engine fault: {str(e)}")
