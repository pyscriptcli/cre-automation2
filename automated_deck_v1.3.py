import os
import io
import streamlit as st
from pptx import Presentation
from PIL import Image

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
            
        # Save to memory instead of local disk for web environment
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr
    except Exception as e:
        return img_file

# --- STREAMLIT WEB UI SETUP ---
st.set_page_config(page_title="CRE Deck Generator", page_icon="🏢", layout="centered")
st.title("🏢 CRE Deck Generator")

st.subheader("--- TEXT DATA ---")
prop_location = st.text_input("📍 Property Location", "Tagaytay, Cavite")
prop_size     = st.text_input("📐 Property Size (SQM)", "386")
prop_type     = st.text_input("🏢 Property Type", "Commercial Space")
prop_address  = st.text_input("🗺️ Full Address", "Mendez Crossing East, Tagaytay City, Cavite")
lease_rates   = st.text_input("💰 Lease Rates", "200,000 per month")
sec_deposit   = st.text_input("🛡️ Security Deposit", "3 months")
adv_rent      = st.text_input("💵 Advance Rent", "3 months")
escalation    = st.text_input("📈 Escalation", "5%")
lease_term    = st.text_input("📅 Lease Term", "5 years")
handover      = st.text_input("🏗️ Handover Condition", "As is where is")

st.subheader("--- IMAGE ASSETS ---")
u_photo1  = st.file_uploader("📸 Property Photo 1", type=["png", "jpg", "jpeg"])
u_map     = st.file_uploader("🗺️ Location Map", type=["png", "jpg", "jpeg"])
u_lotplan = st.file_uploader("📐 Lot Plan", type=["png", "jpg", "jpeg"])
u_photo2  = st.file_uploader("📸 Property Photo 2", type=["png", "jpg", "jpeg"])
u_photo3  = st.file_uploader("📸 Property Photo 3", type=["png", "jpg", "jpeg"])

st.subheader("--- SYSTEM TEMPLATE ---")
u_template = st.file_uploader("📂 Upload Master Template PPTX", type=["pptx"])

# Mapping structures
data_inputs = {
    "{{PROPERTY_LOCATION}}": prop_location, "{{PROPERTY_SIZE}}": prop_size,
    "{{PROPERTY_TYPE}}": prop_type, "{{PROPERTY_ADDRESS}}": prop_address,
    "{{LEASE_RATES}}": lease_rates, "{{SECURITY_DEPOSIT}}": sec_deposit,
    "{{ADVANCE_RENT}}": adv_rent, "{{ESCALATION}}": escalation,
    "{{LEASE TERM}}": lease_term, "{{HANDOVER CONDITION}}": handover
}

image_inputs = {
    "{{PROPERTY_PHOTO}}": u_photo1, "{{PROPERTY_LOCATION_MAP}}": u_map,
    "{{PROPERTY_LOTPLAN}}": u_lotplan, "{{PROPERTY_PHOTO2}}": u_photo2,
    "{{PROPERTY_PHOTO3}}": u_photo3
}

if u_template and st.button("⚙️ GENERATE DECK", use_container_width=True):
    with st.spinner("Processing slides and applying smart image crops..."):
        try:
            # Load template from file uploader object memory
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

            # Save the document stream directly into web memory
            output_stream = io.BytesIO()
            prs.save(output_stream)
            output_stream.seek(0)
            
            st.success("🎉 Presentation compiled successfully!")
            
            # Web download interface widget
            st.download_button(
                label="📥 DOWNLOAD PPTX DECK",
                data=output_stream,
                file_name=f"PIS_{prop_location.replace(' ', '_')}.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True
            )
            
        except Exception as e:
            st.error(f"Critical execution failure: {str(e)}")