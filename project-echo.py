import os
import streamlit as st
import requests
import json
import pandas as pd
import datetime
from io import BytesIO
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

# ========== CONFIG ==========
st.set_page_config(page_title="Project Echo | MOM Generator", layout="wide", initial_sidebar_state="collapsed")

# --- PROGRAMMATIC LIGHT MODE LOCK ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write('[theme]\nbase="light"\n')

# API Keys & Endpoints
GROQ_API_KEY = "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"
GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

CRD_MEMBERS = [
    "Sondi Tuazon",
    "Kristina Balajadia",
    "Meliza Zapata",
    "Dykstra Pineda",
    "Cedtrix Rena",
    "Carlo Medina",
    "Dave Policarpio",
    "Irish Rima"
]

# ========== CUSTOM CSS INJECTION ==========
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600&family=Playfair+Display:ital,wght@1,400;1,500&display=swap');

html, body, [class*="css"] {
    font-family: 'Montserrat', sans-serif !important;
}

.stApp {
    background-color: #F4F2EC; 
    background-image: 
        linear-gradient(rgba(0, 0, 0, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 0, 0, 0.02) 1px, transparent 1px);
    background-size: 80px 80px;
    color: #333333;
}

.stApp > header { display: none !important; }
.block-container { padding-top: 6rem !important; }

.echo-topbar {
    position: fixed; top: 0; left: 0; right: 0; height: 70px;
    background-color: #161616;
    background-image: 
        linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
    background-size: 80px 80px;
    border-bottom: 1px solid #333333;
    display: flex; align-items: center; padding: 0 2rem;
    z-index: 999999; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}
.echo-topbar .logo-wrapper { display: flex; align-items: center; gap: 0.75rem; }
.echo-topbar h1 {
    font-family: 'Playfair Display', serif !important;
    font-style: italic !important; font-weight: 400 !important;
    font-size: 1.5rem !important; color: #FFFFFF !important; margin: 0 !important; padding: 0 !important;
}
.echo-topbar h1 span { color: #D4AF37 !important; }

h3 {
    font-family: 'Playfair Display', serif !important;
    font-style: italic !important; font-weight: 400 !important; 
    color: #1A2B4C !important; letter-spacing: 0.02em; margin-bottom: 0.5rem;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important; border-radius: 16px !important;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.06) !important;
    border: 1px solid rgba(0, 0, 0, 0.03) !important; 
    padding: 1.5rem !important; margin-bottom: 1.5rem !important;
}

.stButton > button, .stDownloadButton > button {
    background-color: #222222 !important; color: #FFFFFF !important;
    border: 1px solid #444444 !important; border-radius: 50px !important; 
    font-family: 'Montserrat', sans-serif !important; font-weight: 500 !important;
    letter-spacing: 0.5px; padding: 0.5rem 1.75rem !important;
    transition: all 0.3s ease !important; display: inline-flex;
    align-items: center; justify-content: center; width: 100% !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: #D4AF37 !important; color: #D4AF37 !important;
    background-color: #1A1A1A !important; box-shadow: 0 4px 15px rgba(212, 175, 55, 0.15) !important;
}

[data-testid="stFileUploadDropzone"] {
    background-color: #FDFDFD !important; border: 1px dashed #CCC !important;
    border-radius: 12px !important; padding: 2.5rem !important; transition: all 0.2s ease !important;
}
</style>
"""

# ========== CORE LOGIC ==========
def transcribe_audio(audio_bytes):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {"file": ("audio.wav", audio_bytes), "model": (None, "whisper-large-v3-turbo"), "response_format": (None, "json")}
    resp = requests.post(GROQ_AUDIO_URL, headers=headers, files=files)
    if resp.status_code == 200:
        return resp.json().get("text", "")
    else:
        st.error(f"Transcription failed: {resp.text}")
        return None

def extract_structured_insights(transcript):
    """
    Robust MOM extractor using Groq json_object mode.
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "You are an expert AI Executive Assistant. Extract Minutes of the Meeting (MOM) "
        "from the provided transcript. You must output JSON strictly following this schema:\n"
        "{\n"
        '  "table_items": [\n'
        "    {\n"
        '      "Discussion Points": "Key point or deliverable discussed",\n'
        '      "Action Plan": "Concrete next steps or requirements",\n'
        '      "Indicative Delivery Date": "Exact date, Quarter (e.g., Q1 2027), or TBD",\n'
        '      "Person-in-charge": "Responsible entity (e.g., PRIME, Client Name, or unassigned)"\n'
        "    }\n"
        "  ],\n"
        '  "other_discussions": "Summary of secondary discussions, notes, or informal remarks"\n'
        "}"
    )

    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

    for model in models:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Transcript:\n{transcript}"}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }
        try:
            resp = requests.post(GROQ_CHAT_URL, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                raw_json = resp.json()["choices"][0]["message"]["content"]
                data = json.loads(raw_json)
                
                items = data.get("table_items", [])
                df = pd.DataFrame(items)
                for col in ["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]:
                    if col not in df.columns:
                        df[col] = ""
                df = df[["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]]
                other_disc = data.get("other_discussions", "")
                return df, other_disc
        except Exception:
            continue

    st.error("AI Extraction encountered an error. Please verify the transcript length and retry.")
    return pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]), ""

def set_cell_shading(cell, color_hex):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def export_to_word(df, meeting_details, other_discussions):
    doc = Document()
    
    # Page setup - Margins
    for section in doc.sections:
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
        # Add Header Image if available
        if os.path.exists("header.png"):
            header_p = section.header.paragraphs[0]
            header_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            header_run = header_p.add_run()
            header_run.add_picture("header.png", width=Inches(7.0))
            
        # Add Footer Image if available
        if os.path.exists("footer.png"):
            footer_p = section.footer.paragraphs[0]
            footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            footer_run = footer_p.add_run()
            footer_run.add_picture("footer.png", width=Inches(7.0))

    # Header Titles
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("MINUTES OF THE MEETING")
    r_title.bold = True
    r_title.underline = True
    r_title.font.size = Pt(12)
    r_title.font.name = "Arial"

    company = meeting_details.get("company_name", "CLIENT").strip().upper()
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run(f"PRIME PHILIPPINES & {company}")
    r_sub.bold = True
    r_sub.font.size = Pt(12)
    r_sub.font.name = "Arial"

    doc.add_paragraph()

    # Meta Info
    date_str = meeting_details.get("date", "____________")
    time_str = meeting_details.get("time_range", "")
    full_date_text = f"Date: {date_str}" + (f", {time_str}" if time_str else "")
    
    p_date = doc.add_paragraph(full_date_text)
    p_date.paragraph_format.space_after = Pt(2)
    
    p_loc = doc.add_paragraph(f"Location: {meeting_details.get('location', '____________')}")
    p_loc.paragraph_format.space_after = Pt(2)
    
    # Attendees
    prime_atts = meeting_details.get("prime_attendees", [])
    ext_atts = meeting_details.get("external_attendees", [])
    
    p_att = doc.add_paragraph("Attended by:\t")
    p_att.paragraph_format.space_after = Pt(2)
    
    first = True
    if ext_atts:
        for att in ext_atts:
            if not att.strip(): continue
            p = p_att if first else doc.add_paragraph()
            if not first: p.paragraph_format.left_indent = Inches(1.2)
            p.add_run(f"{att} – {meeting_details.get('company_name', 'Client')}")
            first = False

    if prime_atts:
        for att in prime_atts:
            p = p_att if first else doc.add_paragraph()
            if not first: p.paragraph_format.left_indent = Inches(1.2)
            p.add_run(f"{att} – PRIME Philippines")
            first = False

    # Divider line
    p_line = doc.add_paragraph()
    p_line.paragraph_format.space_before = Pt(6)
    p_line.paragraph_format.space_after = Pt(6)
    r_line = p_line.add_run("_________________________________________________________________________________")
    r_line.font.color.rgb = RGBColor(180, 180, 180)

    # Intro sentence
    doc.add_paragraph(
        f"During the meeting held last {date_str}, PRIME Philippines, represented by the attendee/s shown above, "
        f"met with {meeting_details.get('company_name', 'the Client')} to discuss opportunities for collaboration."
    )

    # Table Setup
    table = doc.add_table(rows=len(df)+1, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"

    headers = ["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]
    hdr_cells = table.rows[0].cells
    for i, header in enumerate(headers):
        hdr_cells[i].text = header
        set_cell_shading(hdr_cells[i], "FFFF00")  # Yellow header
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.runs[0]
        run.font.bold = True
        run.font.size = Pt(10)
        run.font.name = "Arial"
        run.font.color.rgb = RGBColor(0, 0, 0)

    for i, row in df.iterrows():
        cells = table.rows[i+1].cells
        cells[0].text = f"{i+1}.  {str(row.get('Discussion Points', ''))}"
        cells[1].text = str(row.get("Action Plan", ""))
        cells[2].text = str(row.get("Indicative Delivery Date", ""))
        cells[3].text = str(row.get("Person-in-charge", ""))
        
        for c_idx, cell in enumerate(cells):
            p = cell.paragraphs[0]
            if c_idx in [2, 3]:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if len(p.runs) > 0:
                p.runs[0].font.size = Pt(9.5)
                p.runs[0].font.name = "Arial"

    doc.add_paragraph()
    p_note = doc.add_paragraph("*Note: The indicative delivery date serves as reference point and still subject to changes. Furthermore, it depends on the progress of both parties.")
    p_note.runs[0].font.italic = True
    p_note.runs[0].font.size = Pt(8.5)

    if other_discussions.strip():
        doc.add_heading("Other Discussions:", level=2)
        doc.add_paragraph(other_discussions)

    # Signatures
    doc.add_paragraph()
    doc.add_paragraph("Prepared by:")
    doc.add_paragraph("_______________________________")
    doc.add_paragraph("AVP for Capital Markets\nPRIME Philippines")

    doc.add_paragraph()
    doc.add_paragraph("Confirmed by:")
    doc.add_paragraph("_________________________________")
    doc.add_paragraph(f"{company}")

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# ========== STREAMLIT UI SETUP ==========
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

topbar_html = """
<div class="echo-topbar">
 <div class="logo-wrapper">
 <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#D4AF37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
 <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
 <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path> <line x1="12" y1="19" x2="12" y2="22"></line>
 </svg>
 <h1>Project <span>Echo</span></h1>
 </div>
</div>
"""
st.markdown(topbar_html, unsafe_allow_html=True)

# Session State Initialization
if "transcript" not in st.session_state: st.session_state["transcript"] = ""
if "df" not in st.session_state: st.session_state["df"] = pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"])
if "other_discussions" not in st.session_state: st.session_state["other_discussions"] = ""
if "crd_selected" not in st.session_state: st.session_state["crd_selected"] = {m: True for m in CRD_MEMBERS}

# ---- Step 1: Meeting Details & Audio Input ----
with st.container(border=True):
    st.markdown('<h3 style="display: flex; align-items: center;">Meeting Details & Audio</h3>', unsafe_allow_html=True)
    
    col_d1, col_d2, col_t1, col_t2 = st.columns(4)
    with col_d1:
        meeting_date = st.date_input("Meeting Date", value=datetime.date.today())
    with col_d2:
        meeting_location = st.text_input("Location", value="Greatwork Mega Tower Boardroom")
    with col_t1:
        start_time = st.time_input("Start Time", value=datetime.time(14, 30))
    with col_t2:
        end_time = st.time_input("End Time", value=datetime.time(17, 0))

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        client_name = st.text_input("Client / Company Name", placeholder="e.g. Mr. ABCD, XYZ Company")
    with col_c2:
        ext_attendees_raw = st.text_input("External Attendees (Comma-separated)", placeholder="e.g. Mr. John Doe, Jane Smith")

    st.markdown("**CRD Team Attendees:**")
    crd_cols = st.columns(4)
    selected_crd = []
    for idx, member in enumerate(CRD_MEMBERS):
        with crd_cols[idx % 4]:
            st.session_state["crd_selected"][member] = st.checkbox(
                member, 
                value=st.session_state["crd_selected"].get(member, True),
                key=f"crd_{member}"
            )
            if st.session_state["crd_selected"][member]:
                selected_crd.append(member)

    st.divider()
    tab1, tab2 = st.tabs(["Upload Recording", "Record Live Audio"])
    audio_data = None
    with tab1:
        uploaded = st.file_uploader("Upload audio file", type=["wav", "mp3", "m4a", "ogg", "flac", "mp4", "webm"], label_visibility="collapsed")
        if uploaded: audio_data = uploaded.read()
    with tab2:
        recorded_audio = st.audio_input("Record audio", label_visibility="collapsed")
        if recorded_audio: audio_data = recorded_audio.read()

    if audio_data:
        if st.button("Transcribe Audio"):
            with st.spinner("Transcribing audio with Groq Whisper..."):
                transcript = transcribe_audio(audio_data)
            if transcript:
                st.session_state["transcript"] = transcript
                st.session_state["df"] = pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"])
                st.session_state["other_discussions"] = ""
                st.rerun()

# ---- Step 2: Transcript & Generation ----
if st.session_state["transcript"]:
    with st.container(border=True):
        st.markdown('<h3>Full Transcript</h3>', unsafe_allow_html=True)
        st.text_area("Transcript", st.session_state["transcript"], height=160, label_visibility="collapsed")
        
        if st.button("Generate MOM"):
            with st.spinner("Extracting discussion points and action items..."):
                extracted_df, other_disc = extract_structured_insights(st.session_state["transcript"])
            if not extracted_df.empty:
                st.session_state["df"] = extracted_df
                st.session_state["other_discussions"] = other_disc
                st.rerun()

# ---- Step 3: Editable MOM Table & Export ----
if not st.session_state["df"].empty:
    with st.container(border=True):
        st.markdown('<h3>Minutes of Meeting Editor</h3>', unsafe_allow_html=True)
        
        edited_df = st.data_editor(
            st.session_state["df"],
            num_rows="dynamic",
            use_container_width=True,
            key="mom_data_editor",
            column_config={
                "Discussion Points": st.column_config.TextColumn("Discussion Points", width="large"),
                "Action Plan": st.column_config.TextColumn("Action Plan", width="medium"),
                "Indicative Delivery Date": st.column_config.TextColumn("Indicative Delivery Date", width="small"),
                "Person-in-charge": st.column_config.TextColumn("Person-in-charge", width="small")
            }
        )
        st.session_state["df"] = edited_df

        st.session_state["other_discussions"] = st.text_area("Other Discussions", value=st.session_state["other_discussions"], height=100)

        # Prepare payload for Word export
        meeting_details = {
            "date": meeting_date.strftime("%B %d, %Y"),
            "time_range": f"{start_time.strftime('%I:%M %p')} to {end_time.strftime('%I:%M %p')}",
            "location": meeting_location,
            "company_name": client_name if client_name else "CLIENT",
            "prime_attendees": selected_crd,
            "external_attendees": [x.strip() for x in ext_attendees_raw.split(",") if x.strip()]
        }

        doc_bio = export_to_word(
            st.session_state["df"],
            meeting_details,
            st.session_state["other_discussions"]
        )

        st.download_button(
            label="Download Minutes of the Meeting (.docx)",
            data=doc_bio,
            file_name=f"MOM_{client_name.replace(' ', '_') if client_name else 'Export'}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
