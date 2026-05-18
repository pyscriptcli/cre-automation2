import os
import io
import streamlit as st
from pptx import Presentation
from PIL import Image

# --- FLAT & LUXURIOUS LUXURY DESIGN SYSTEM (CSS INJECTION) ---
LUXURY_CRE_SYSTEM = """
<style>
    /* 1. Global Page Core Reset to White & Navy */
    .stApp {
        background-color: #FFFFFF !important;
        color: #002B49 !important;
        font-family: 'Inter', -apple-system, sans-serif !important;
    }
    
    /* Remove all default header and padding layers */
    div[data-testid="stHeader"] {
        background-color: #FFFFFF !important;
    }
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 4rem !important;
        max-width: 800px !important; /* Centered spacious layout column */
    }
    
    /* 2. Flat Luxury Input Fields (Larger Fonts, Sharp 0px Corners) */
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[role="textbox"] {
        background-color: #FFFFFF !important;
        border: 1px solid #002B49 !important; /* Solid Navy Border Line */
        border-radius: 0px !important; /* Flat luxury edge */
        color: #002B49 !important;
        transition: border-color 0.15s ease-in-out !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #C5A059 !important; /* Corporate Gold Accent */
        box-shadow: none !important;
    }
    
    /* Scaled Input text parameters */
    input[type="text"], .stTextInput input {
        color: #002B49 !important;
        background-color: #FFFFFF !important;
        font-size: 16px !important; /* Larger font size override */
        font-weight: 500 !important;
        padding: 12px 16px !important;
    }
    
    /* 3. Minimalist Template File Uploader */
    section[data-testid="stFileUploader"] {
        background-color: #F8FAFC !important;
        border: 1px dashed #C5A059 !important; /* Gold dashed line for files */
        border-radius: 0px !important;
        padding: 16px !important;
    }
    section[data-testid="stFileUploader"] div, section[data-testid="stFileUploader"] span {
        color: #002B49 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }
    div[data-testid="stFileUploader"] label {
        display: none !important; /* Remove native duplicate labels */
    }
    
    /* 4. Large Bold Typography Row Layouts */
    .row-metric-label {
        font-size: 15px !important; /* Scaled up text label */
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        color: #002B49 !important;
        display: flex;
        align-items: center;
        padding-top: 14px;
    }
    .large-icon {
        font-size: 24px !important; /* Magnified flat icon framework */
        margin-right: 12px;
        display: inline-block;
    }
    
    /* 5. Clean Section Framing */
    .luxury-workspace-card {
        background-color: #FFFFFF;
        border-top: 4px solid #002B49; /* Massive Navy Block Line */
        padding-top: 20px;
        margin-bottom: 35px;
    }
    
    .luxury-tagline {
        font-size: 13px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
        color: #C5A059 !important; /* Gold section marker text */
        margin-bottom: 24px;
        display: block;
    }

    /* 6. Heavy Command Button Overrides */
    div.stButton > button {
        background-color: #002B49 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        border: none !important;
        border-radius: 0px !important;
        border-bottom: 4px solid #C5A059 !important; /* Prominent Gold Base Accent */
        padding: 16px 32px !important;
        width: 100% !important;
        transition: background-color 0.15s ease;
    }
    div.stButton > button:hover {
        background-color: #0A3352 !important;
        border-bottom-color: #C5A059 !important;
        color: #FFFFFF !important;
    }
    
    /* Reset Button alternative alignment */
    div[data-testid="column"] div.stButton > button[key="reset_btn_key"] {
        background-color: transparent !important;
        color: #64748B !important;
        border: 1px solid #CBD5E1 !important;
        border-bottom: 1px solid #CBD5E1 !important;
        padding: 12px 24px !important;
    }
    div[data-testid="column"] div.stButton > button[key="reset_btn_key"]:hover {
        color: #002B49 !important;
        border-color: #002B49 !important;
    }
</style>
"""

# --- BACKEND SPATIAL PROCESSING UTILS ---
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

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Asset Engine", page_icon="🏢", layout="centered")
st.markdown(LUXURY_CRE_SYSTEM, unsafe_allow_html=True)

# HIGH DENSITY STRUCTURAL ROW HELPERS
def dynamic_form_row(icon, label_text, default_val, state_key):
    r_col1, r_col2 = st.columns([9, 11])
    with r_col1:
        st.markdown(f'<div class="row-metric-label"><span class="large-icon">{icon}</span> {label_text}</div>', unsafe_allow_html=True)
    with r_col2:
        return st.text_input("", value=default_val, key=state_key, label_visibility="collapsed")

# --- STEP 1: COMPILER ARCHITECTURE BLUEPRINT (TEMPLATE FIRST) ---
st.markdown('<div class="luxury-workspace-card">', unsafe_allow_html=True)
st.markdown('<span class="luxury-tagline">BLUEPRINT BLUEPRINT COMPILER</span>', unsafe_allow_html=True)

t_col1, t_col2 = st.columns([9, 11])
with t_col1:
    st.markdown('<div class="row-metric-label"><span class="large-icon">📂</span> TEMPLATE</div>', unsafe_allow_html=True)
with t_col2:
    u_template = st.file_uploader("Template File Input", type=["pptx"], key="web_tpl")
st.markdown('</div>', unsafe_allow_html=True)


# --- STEP 2: METADATA DETAILS (PROPERTY DETAILS) ---
st.markdown('<div class="luxury-workspace-card">', unsafe_allow_html=True)
st.markdown('<span class="luxury-tagline">PROPERTY DETAILS</span>', unsafe_allow_html=True)

prop_location = dynamic_form_row("📍", "Property Location", "Tagaytay, Cavite", "cre_loc")
prop_size     = dynamic_form_row("📐", "Property Size (SQM)", "386", "cre_size")
prop_type     = dynamic_form_row("🏢", "Property Type", "Commercial Space", "cre_type")
prop_address  = dynamic_form_row("🗺️", "Full Address", "Mendez Crossing East, Tagaytay City, Cavite", "cre_addr")
lease_rates   = dynamic_form_row("💰", "Lease Rates", "200,000 per month", "cre_rates")
sec_deposit   = dynamic_form_row("🛡️", "Security Deposit", "3 months", "cre_sec")
adv_rent      = dynamic_form_row("💵", "Advance Rent", "3 months", "cre_adv")
escalation    = dynamic_form_row("📈", "Rental Escalation", "5%", "cre_esc")
lease_term    = dynamic_form_row("📅", "Lease Term", "5 years", "cre_term")
handover      = dynamic_form_row("🏗️", "Handover Condition", "As is where is", "cre_hand")
st.markdown('</div>', unsafe_allow_html=True)

# Data Mapping Containers (Image objects pass empty handles gracefully since fields are omitted)
data_inputs = {
    "{{PROPERTY_LOCATION}}": prop_location, "{{PROPERTY_SIZE}}": prop_size,
    "{{PROPERTY_TYPE}}": prop_type, "{{PROPERTY_ADDRESS}}": prop_address,
    "{{LEASE_RATES}}": lease_rates, "{{SECURITY_DEPOSIT}}": sec_deposit,
    "{{ADVANCE_RENT}}": adv_rent, "{{ESCALATION}}": escalation,
    "{{LEASE TERM}}": lease_term, "{{HANDOVER CONDITION}}": handover
}

image_inputs = {
    "{{PROPERTY_PHOTO 1}}": None, "{{PROPERTY_LOCATION_MAP}}": None,
    "{{PROPERTY_LOTPLAN}}": None, "{{PROPERTY_PHOTO2}}": None,
    "{{PROPERTY_PHOTO3}}": None
}

# --- CONTROL DESK ACTION LAYER ---
st.markdown("<div style='margin-top: 20px; border-top: 1px solid #002B49; padding-top: 25px;'></div>", unsafe_allow_html=True)
action_col1, action_col2 = st.columns([1, 2])

with action_col1:
    if st.button("↺ Clear", key="reset_btn_key", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with action_col2:
    if u_template is None:
        st.markdown("<div style='padding-top:16px; font-size:12px; font-weight:700; color:#002B49; text-align:right; letter-spacing:0.04em;'>⚠️ UPLOAD A MASTER PPTX BLUEPRINT TO MOUNT GENERATION FUNCTIONS.</div>", unsafe_allow_html=True)
    else:
        if st.button("⚙️ GENERATE DECK", key="generate_btn_key", use_container_width=True):
            with st.spinner("Processing template slide assets..."):
                try:
                    prs = Presentation(u_template)
                    
                    for slide in prs.slides:
                        shapes_to_delete = []
                        images_to_add = []

                        for shape in slide.shapes:
                            if shape.has_text_frame:
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

                    output_stream = io.BytesIO()
                    prs.save(output_stream)
                    output_stream.seek(0)
                    
                    # FIXED: Secure double quotes inside the single-quoted block to prevent compilation syntax errors
                    st.markdown("""<div style="border-left: 4px solid #C5A059; background-color: #FFFFFF; padding: 16px; border-top: 1px solid #002B49; border-right: 1px solid #002B49; border-bottom: 1px solid #002B49; margin-top: 20px; text-align: center; color: #002B49; font-weight: 700; font-size: 13px; letter-spacing: 0.05em;">🎉 PRESENTATION COMPILED SUCCESSFUL. PLATFORM BLOCKS EXTRACTED.</div>""", unsafe_allow_html=True)
                    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
                    
                    st.download_button(
                        label="📥 DOWNLOAD BRANDED PPTX DECK",
                        data=output_stream,
                        file_name=f"PIS_{prop_location.replace(' ', '_')}.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"Compilation core failure log description: {str(e)}")
