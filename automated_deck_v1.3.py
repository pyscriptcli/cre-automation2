import os
import io
import streamlit as st
from pptx import Presentation
from PIL import Image

# --- PRIME CORPORATE DESIGN SYSTEM (CSS INJECTION) ---
PRIME_DESIGN_SYSTEM = """
<style>
    /* 1. Global Page Reset & Typography */
    .stApp {
        background-color: #F8FAFC !important; /* Muted Canvas off-white */
        color: #1E293B !important;
        font-family: 'Inter', 'Helvetica Neue', 'SF Pro Display', sans-serif !important;
    }
    h2, h3, h4, .aligned-label {
        font-family: 'Inter', 'Helvetica Neue', sans-serif !important;
    }

    /* 2. Form Input Grid Density and Institutional Sharp Corners */
    /* Target inputs within the custom grid macro */
    div[data-testid="stColumns"] div[data-baseweb="input"] {
        border-radius: 2px !important; /* Sharp corporate radius */
        border: 1px solid #E2E8F0 !important; /* Light separator gray */
        background-color: #FFFFFF !important;
        transition: all 0.1s ease-in-out;
    }
    div[data-testid="stColumns"] div[data-baseweb="input"]:focus-within {
        border-color: #C5A059 !important; /* Muted Gold accent on focus */
        box-shadow: none !important;
    }
    div[data-testid="stColumns"] input {
        font-size: 14px !important;
        color: #1E293B !important;
        padding-top: 6px !important;
        padding-bottom: 6px !important;
    }

    /* 3. Section Header styling matching Marketing Site aesthetics */
    .prime-section-header {
        font-size: 12px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #002B49 !important; /* Deep Navy primary token */
        border-bottom: 1px solid #E2E8F0;
        padding-bottom: 8px;
        margin-top: 25px;
        margin-bottom: 15px;
        width: 100%;
    }
    
    /* 4. Horizontal Grid Aligned Label styling */
    .aligned-label {
        font-size: 13px !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.02em !important;
        color: #64748B !important; /* Muted Gray label color */
        padding-top: 30px; /* Precise vertical alignment offset for Streamlit grid */
    }

    /* 5. Institutional Asymmetric Left Border for Form Card (Demonstration Component) */
    .prime-metric-card {
        border-left: 4px solid #C5A059 !important; /* Key Muted Gold accent line */
        background-color: #FFFFFF;
        padding: 15px;
        border-top: 1px solid #E2E8F0;
        border-right: 1px solid #E2E8F0;
        border-bottom: 1px solid #E2E8F0;
        border-radius: 2px;
        margin-bottom: 15px;
    }

    /* 6. File Uploader Layout Adjustments (Mockup mimicry) */
    section[data-testid="stFileUploader"] {
        background-color: #FFFFFF !important;
        border: 1px dashed #E2E8F0 !important;
        border-radius: 2px !important;
        padding: 10px !important;
    }
    section[data-testid="stFileUploader"] div, section[data-testid="stFileUploader"] span {
        color: #64748B !important;
        font-size: 12px !important;
    }

    /* 7. Action Button Overrides (Anchored Design) */
    /* Target the generate button specifically through its container context */
    div[data-testid="column"]:last-child div.stButton > button {
        background-color: #002B49 !important; /* Deep Navy solid base */
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        border: none !important;
        border-radius: 2px !important;
        border-bottom: 3px solid #C5A059 !important; /* Institutional Gold base border line */
        padding: 12px 24px !important;
        width: 100% !important;
        transition: background-color 0.15s ease;
    }
    div[data-testid="column"]:last-child div.stButton > button:hover {
        background-color: #0F3B59 !important;
        color: #FFFFFF !important;
    }
    
    /* Target the reset button using unique markup pattern matching (secondary transparent style) */
    div[data-testid="column"]:first-child div.stButton > button {
        background-color: transparent !important;
        color: #64748B !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 2px !important;
    }
    div[data-testid="column"]:first-child div.stButton > button:hover {
        color: #1E293B !important;
        border-color: #64748B !important;
    }
</style>
"""

# --- OBJECT-FIT COVER CROP ENGINE (Functional Backend remain unchanged) ---
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

# --- UI WORKFLOW TEMPLATING ---
st.set_page_config(page_title="Asset Pitch Engine", page_icon="🏢", layout="wide")
st.markdown(PRIME_DESIGN_SYSTEM, unsafe_allow_html=True)

# PORTAL HEADER (Removed PRIME Philippines constraint)
st.markdown("<h2 style='color:#002B49; font-weight:700; font-size:22px; margin-bottom:20px;'>🏢 Asset Pitch Engine</h2>", unsafe_allow_html=True)

# Define UIs components with high data density alignment structure
def aligned_input_row(icon, label_text, default_val, key):
    # Split row into [Icon+Label] channel and [Input] channel
    col1, col2 = st.columns([2, 3], gap="small")
    with col1:
        st.markdown(f'<div class="aligned-label">{icon} {label_text.upper()}</div>', unsafe_allow_html=True)
    with col2:
        # Standard input with collapsed label visibility to preserve grid context
        return st.text_input("", value=default_val, label_visibility="collapsed", key=key)

def section_header(text):
    st.markdown(f'<div class="prime-section-header">--- {text.upper()} ---</div>', unsafe_allow_html=True)

# Main Multi-Panel Grid Layout
panel_left, panel_right = st.columns([1, 1], gap="large")

with panel_left:
    section_header("Text Data Metrics Matrix")
    
    # Render horizontally aligned form inputs
    prop_location = aligned_input_row("📍", "Property Location:", "Tagaytay, Cavite", "in_loc")
    prop_size     = aligned_input_row("📐", "Property Size (SQM):", "386", "in_size")
    prop_type     = aligned_input_row("🏢", "Property Type:", "Commercial Space", "in_type")
    prop_address  = aligned_input_row("🗺️", "Full Address:", "Mendez Crossing East, Tagaytay City, Cavite", "in_addr")
    lease_rates   = aligned_input_row("💰", "Lease Rates:", "200,000 per month", "in_rates")
    sec_deposit   = aligned_input_row("🛡️", "Security Deposit:", "3 months", "in_sec")
    adv_rent      = aligned_input_row("💵", "Advance Rent:", "3 months", "in_adv")
    escalation    = aligned_input_row("📈", "Rental Escalation:", "5%", "in_esc")
    lease_term    = aligned_input_row("📅", "Lease Term:", "5 years", "in_term")
    handover      = aligned_input_row("🏗️", "Handover Condition:", "As is where is", "in_hand")

with panel_right:
    section_header("Asset Upload Pipelines")
    # File uploaders styled to be more compact with design accents
    u_photo1  = st.file_uploader("📸 Property Photo 1 Container", type=["png", "jpg", "jpeg"])
    u_map     = st.file_uploader("🗺️ Location Map Container", type=["png", "jpg", "jpeg"])
    u_lotplan = st.file_uploader("📐 Lot Plan Container", type=["png", "jpg", "jpeg"])
    u_photo2  = st.file_uploader("📸 Property Photo 2 Container", type=["png", "jpg", "jpeg"])
    u_photo3  = st.file_uploader("📸 Property Photo 3 Container", type=["png", "jpg", "jpeg"])

    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    
    section_header("System Blueprint Architecture")
    u_template = st.file_uploader("📂 Upload Master Template PPTX blueprint", type=["pptx"])

# Optimized Data Dictionaries (v2.2 structure remains intact)
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

# --- UNBREAKABLE FOOTER ACTION REGION ---
st.markdown("<div style='margin-top: 30px; border-t: 1px solid #E2E8F0; padding-top: 20px;'></div>", unsafe_allow_html=True)
footer_col1, footer_col2 = st.columns([1, 4], gap="small")

with footer_col1:
    # Key matching "reset_btn" constraint from layout logic matrix
    if st.button("↺ Reset Form", key="action_reset", use_container_width=True):
        st.cache_data.clear() # Clear memory cache for standard deployment persistence
        st.rerun()

with footer_col2:
    # Key functional gate: Unlock button only when template is attached
    if u_template is None:
        st.markdown("<div style='padding-top:12px; font-size:12px; color:#64748B; text-align:right;'>⚠️ Connect a local Master Template blueprint PPTX file to unlock the generation engine.</div>", unsafe_allow_html=True)
    else:
        if st.button("⚙️ GENERATE DECK", key="action_gen", use_container_width=True):
            with st.spinner("Executing spatial OpenXML tree manipulation and smart graphic cropping..."):
                try:
                    # 1. Parse template stream from memory upload object
                    prs = Presentation(u_template)
                    
                    # Core spatial image replacement engine remains production-validated from v1.3
                    for slide in prs.slides:
                        shapes_to_delete = []
                        images_to_add = []

                        for shape in slide.shapes:
                            # Handle standard Text Swaps
                            if shape.has_text_frame and not any(img_token in shape.text_frame.text for img_token in image_inputs):
                                for paragraph in shape.text_frame.paragraphs:
                                    for run in paragraph.runs:
                                        for token, value in data_inputs.items():
                                            if token in run.text:
                                                run.text = run.text.replace(token, value)

                            # Handle Native Table Cell Swaps
                            if shape.has_table:
                                for row in shape.table.rows:
                                    for cell in row.cells:
                                        for paragraph in cell.text_frame.paragraphs:
                                            for run in paragraph.runs:
                                                for token, value in data_inputs.items():
                                                    if token in run.text:
                                                        run.text = run.text.replace(token, value)

                            # Handle Images using text-token replacement method
                            if shape.has_text_frame:
                                text_content = shape.text_frame.text
                                for img_token, img_file in image_inputs.items():
                                    if img_token in text_content and img_file is not None:
                                        images_to_add.append((img_file, shape.left, shape.top, shape.width, shape.height))
                                        shapes_to_delete.append(shape)

                        # Drop in optimized, center-cropped images perfectly filling bounds
                        for img_file, left, top, width, height in images_to_add:
                            processed_img = smart_crop_to_fit(img_file, width, height)
                            slide.shapes.add_picture(processed_img, left, top, width=width, height=height)

                        # Purge old vector text boxes to finalize the slide tree manipulation
                        for old_shape in shapes_to_delete:
                            sp = old_shape._element
                            sp.getparent().remove(sp)

                    # 2. Compile output back into buffered active memory
                    output_stream = io.BytesIO()
                    prs.save(output_stream)
                    output_stream.seek(0)
                    
                    # Show premium success metric card component
                    st.markdown('<div class="prime-metric-card" style="margin-top:15px; text-align:center; color:#002B49;"><b>🎉 Presentation Compiled Successfully!</b> Your file is optimized and cached in active application memory.</div>', unsafe_allow_html=True)
                    
                    # Display locked-and-loaded download widget
                    st.download_button(
                        label="📥 DOWNLOAD PPTX DECK",
                        data=output_stream,
                        file_name=f"PIS_{prop_location.replace(' ', '_')}.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"Critical Compilation Engine Runtime Fault: {str(e)}")
