import os
import streamlit as st
import requests
import json
import pandas as pd
import datetime
import re
from io import BytesIO
import PyPDF2
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml

# ========== CONFIG ==========
st.set_page_config(page_title="Project Echo", layout="wide", initial_sidebar_state="collapsed")

# --- PROGRAMMATIC LIGHT MODE LOCK ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write('[theme]\nbase="light"\n')

# API Keys & Endpoints
GEMINI_API_KEY = "AIzaSyDlBkIdAth2AesZ9rr3xTe7t_IXl2_IEQM"
GROQ_API_KEY = "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"
GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

CRD_MEMBERS = [
    "Sondi Tuazon", "Kristina Balajadia", "Meliza Zapata", "Dykstra Pineda",
    "Cedtrix Rena", "Carlo Medina", "Dave Policarpio", "Irish Rima"
]

# 12-Hour AM/PM Time Options
TIME_OPTIONS = []
for h in range(24):
    for m in (0, 30):
        t = datetime.time(h, m)
        TIME_OPTIONS.append(t.strftime("%I:%M %p"))

# ========== CUSTOM CSS ==========
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600&family=Playfair+Display:ital,wght@1,400;1,500&display=swap');

html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
.stApp {
    background-color: #F4F2EC; 
    background-image: linear-gradient(rgba(0, 0, 0, 0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 0, 0, 0.02) 1px, transparent 1px);
    background-size: 80px 80px; color: #333333;
}
.stApp > header { display: none !important; }
.block-container { padding-top: 5.5rem !important; }

.echo-topbar {
    position: fixed; top: 0; left: 0; right: 0; height: 60px;
    background-color: #161616; border-bottom: 1px solid #333333;
    display: flex; align-items: center; padding: 0 2rem;
    z-index: 999999; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}
.echo-topbar h1 {
    font-family: 'Playfair Display', serif !important; font-style: italic !important; 
    font-weight: 400 !important; font-size: 1.35rem !important; 
    color: #FFFFFF !important; margin: 0 !important;
}
.echo-topbar h1 span { color: #D4AF37 !important; }

h3 {
    font-family: 'Playfair Display', serif !important; font-style: italic !important; 
    font-weight: 400 !important; color: #1A2B4C !important; 
    letter-spacing: 0.02em; margin-bottom: 0.25rem; font-size: 1.25rem !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important; border-radius: 12px !important;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.04) !important;
    border: 1px solid rgba(0, 0, 0, 0.04) !important; 
    padding: 1.25rem !important; margin-bottom: 1rem !important;
}

.stButton > button, .stDownloadButton > button {
    background-color: #222222 !important; color: #FFFFFF !important;
    border: 1px solid #444444 !important; border-radius: 50px !important; 
    font-family: 'Montserrat', sans-serif !important; font-weight: 500 !important;
    letter-spacing: 0.5px; padding: 0.4rem 1.5rem !important;
    transition: all 0.3s ease !important; width: 100% !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: #D4AF37 !important; color: #D4AF37 !important;
    background-color: #1A1A1A !important;
}
.stTextArea textarea { font-size: 0.95rem !important; line-height: 1.6 !important; }
</style>
"""

# ========== CORE LOGIC ==========
def extract_json_from_text(text):
    """Robustly extracts JSON from LLM responses, handling markdown and formatting quirks."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text).strip()
    
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
            
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
        
    return None

def extract_text_from_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.txt'):
            return uploaded_file.getvalue().decode("utf-8")
        elif uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            return "\n".join([page.extract_text() or "" for page in reader.pages])
        elif uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            return "\n".join([para.text for para in doc.paragraphs])
        return ""
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return ""

def transcribe_audio(audio_bytes):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {
        "file": ("audio.wav", audio_bytes), 
        "model": (None, "whisper-large-v3-turbo"), 
        "response_format": (None, "json")
    }
    resp = requests.post(GROQ_AUDIO_URL, headers=headers, files=files)
    if resp.status_code == 200:
        return resp.json().get("text", "")
    else:
        error_msg = resp.json().get("error", {}).get("message", resp.text)
        if "rate limit" in error_msg.lower():
            st.error("Transcription rate limit reached. Please wait or use the 'Upload Text' tab.")
        else:
            st.error(f"Transcription failed: {error_msg}")
        return None

def extract_with_gemini(transcript):
    gemini_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"]
    
    prompt = f"""You are an executive assistant for PRIME Philippines extracting Minutes of the Meeting (MOM).
The transcript contains Tagalog and English (Taglish) discussion regarding property sourcing, sites (A1 sites), reports, tax maps, LGUs, trade areas, and client updates.
Translate all colloquial and Taglish dialogue into clear, professional corporate English.

Extract at least 3 to 10 clear, distinct table items covering all discussed tasks, updates, and deliverables.

Output valid JSON ONLY matching this schema:
{{
  "table_items": [
    {{
      "Discussion Points": "Core discussion topic, site status, or milestone",
      "Action Plan": "Concrete next step, format to provide, report to send, or requirement",
      "Indicative Delivery Date": "Specific date, timeline (e.g., Friday, Q1 2027), or 'TBD'",
      "Person-in-charge": "Responsible entity (e.g., PRIME, Client, or name)"
    }}
  ],
  "other_discussions": "Summary of informal remarks, administrative notes, or general context"
}}

Transcript:
{transcript[:30000]}"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.1
        }
    }
    
    for model_name in gemini_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                result = resp.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                    data = extract_json_from_text(raw_text)
                    if data:
                        items = data.get("table_items", [])
                        if items and len(items) > 0:
                            df = pd.DataFrame(items)
                            for col in ["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]:
                                if col not in df.columns:
                                    df[col] = ""
                            return df[["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]].drop_duplicates(), data.get("other_discussions", "")
            else:
                st.warning(f"Gemini API Error ({model_name}): {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            st.warning(f"Gemini Exception ({model_name}): {e}")
            continue
            
    return None, None

def extract_with_groq_backup(transcript):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = (
        "You are an executive assistant extracting Minutes of the Meeting (MOM). "
        "The transcript contains Tagalog and English (Taglish). Translate dialogue into professional English. "
        "Extract all key discussion points and action items. Respond ONLY with valid JSON."
    )
    
    user_prompt = f"""Extract all Minutes of the Meeting items into valid JSON:
{{
  "table_items": [
    {{
      "Discussion Points": "Core discussion topic, report, or milestone",
      "Action Plan": "Specific follow-up action or deliverable",
      "Indicative Delivery Date": "Specific date, timeline, or 'TBD'",
      "Person-in-charge": "Responsible entity (e.g., PRIME, Client, or Unassigned)"
    }}
  ],
  "other_discussions": "Summary of other points discussed"
}}

Transcript:
{transcript[:25000]}"""

    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    for model in models:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }
        try:
            resp = requests.post(GROQ_CHAT_URL, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                resp_json = resp.json()
                raw_text = resp_json["choices"][0]["message"]["content"].strip()
                data = extract_json_from_text(raw_text)
                if data:
                    items = data.get("table_items", [])
                    if items and len(items) > 0:
                        df = pd.DataFrame(items)
                        for col in ["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]:
                            if col not in df.columns:
                                df[col] = ""
                        return df[["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]].drop_duplicates(), data.get("other_discussions", "")
            else:
                st.warning(f"Groq API Error ({model}): {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            st.warning(f"Groq Exception ({model}): {e}")
            continue
    return None, None

def extract_structured_insights(transcript):
    if not transcript or not transcript.strip():
        st.error("Transcript is empty. Please provide valid text or audio to transcribe.")
        return pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]), ""

    # 1. Primary: Gemini
    df, other_disc = extract_with_gemini(transcript)
    if df is not None and not df.empty:
        return df, other_disc

    # 2. Backup: Groq
    df_groq, other_disc_groq = extract_with_groq_backup(transcript)
    if df_groq is not None and not df_groq.empty:
        return df_groq, other_disc_groq

    st.error("Extraction encountered an issue on both APIs. Please verify your transcript and retry. Check the warning messages above for specific API error details.")
    return pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]), ""

def set_cell_shading(cell, color_hex):
    shd = parse_xml(f'<w:shd xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shd)

def export_to_word(df, meeting_details, other_discussions):
    doc = Document()
    
    for section in doc.sections:
        section.top_margin = Inches(0.4)
        section.bottom_margin = Inches(0.4)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
        if os.path.exists("header.png"):
            hp = section.header.paragraphs[0]
            hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            hp.add_run().add_picture("header.png", width=Inches(7.0))
            
        if os.path.exists("footer.png"):
            fp = section.footer.paragraphs[0]
            fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            fp.add_run().add_picture("footer.png", width=Inches(7.0))

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("MINUTES OF THE MEETING")
    r_title.bold = True
    r_title.underline = True
    r_title.font.name = "Arial"
    r_title.font.size = Pt(11)

    company = meeting_details.get("company_name", "CLIENT").strip().upper()
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run(f"PRIME PHILIPPINES & {company}")
    r_sub.bold = True
    r_sub.font.name = "Arial"
    r_sub.font.size = Pt(11)

    doc.add_paragraph()

    date_str = meeting_details.get("date", "____________")
    time_str = meeting_details.get("time_range", "")
    full_date = f"Date: {date_str}" + (f", {time_str}" if time_str else "")
    
    doc.add_paragraph(full_date).paragraph_format.space_after = Pt(2)
    doc.add_paragraph(f"Location: {meeting_details.get('location', '____________')}").paragraph_format.space_after = Pt(2)
    
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

    p_line = doc.add_paragraph()
    p_line.paragraph_format.space_before = Pt(4)
    p_line.paragraph_format.space_after = Pt(4)
    p_line.add_run("_________________________________________________________________________________").font.color.rgb = RGBColor(180, 180, 180)

    doc.add_paragraph(
        f"During the meeting held last {date_str}, PRIME Philippines, represented by the attendee/s shown above, "
        f"met with {meeting_details.get('company_name', 'the Client')} to discuss opportunities for collaboration."
    )

    table = doc.add_table(rows=len(df)+1, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"

    headers = ["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = header
        set_cell_shading(cell, "FFFF00")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if p.runs:
            p.runs[0].font.bold = True
            p.runs[0].font.size = Pt(9.5)
            p.runs[0].font.name = "Arial"

    for i, row in df.iterrows():
        cells = table.rows[i+1].cells
        cells[0].text = f"{i+1}.  {str(row.get('Discussion Points', ''))}"
        cells[1].text = str(row.get("Action Plan", ""))
        cells[2].text = str(row.get("Indicative Delivery Date", ""))
        cells[3].text = str(row.get("Person-in-charge", ""))
        for c_idx, cell in enumerate(cells):
            p = cell.paragraphs[0]
            if c_idx in [2, 3]: p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if p.runs:
                p.runs[0].font.size = Pt(9)
                p.runs[0].font.name = "Arial"

    doc.add_paragraph()
    p_note = doc.add_paragraph("*Note: The indicative delivery date serves as reference point and still subject to changes. Furthermore, it depends on the progress of both parties.")
    p_note.runs[0].font.italic = True
    p_note.runs[0].font.size = Pt(8.5)

    if other_discussions.strip():
        doc.add_heading("Other Discussions:", level=2)
        doc.add_paragraph(other_discussions)

    doc.add_paragraph()
    doc.add_paragraph("Prepared by:")
    doc.add_paragraph("_______________________________")
    prep_name = meeting_details.get("prep_name", "").strip()
    prep_desig = meeting_details.get("prep_desig", "").strip()
    doc.add_paragraph(f"{prep_name if prep_name else '____________________'}\n{prep_desig if prep_desig else 'PRIME Philippines'}")

    doc.add_paragraph()
    doc.add_paragraph("Confirmed by:")
    doc.add_paragraph("_______________________________")
    conf_name = meeting_details.get("conf_name", "").strip()
    conf_desig = meeting_details.get("conf_desig", "").strip()
    doc.add_paragraph(f"{conf_name if conf_name else '____________________'}\n{conf_desig if conf_desig else company}")

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# ========== STREAMLIT UI SETUP ==========
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown("""
<div class="echo-topbar">
 <h1>Project <span>Echo</span></h1>
</div>
""", unsafe_allow_html=True)

if "transcript" not in st.session_state: st.session_state["transcript"] = ""
if "df" not in st.session_state: st.session_state["df"] = pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"])
if "other_discussions" not in st.session_state: st.session_state["other_discussions"] = ""

# ---- Compact 2-Row Details & Audio ----
with st.container(border=True):
    st.markdown('<h3>Meeting Details & Audio</h3>', unsafe_allow_html=True)
    
    # ROW 1
    r1_c1, r1_c2, r1_c3, r1_c4, r1_c5, r1_c6 = st.columns([1.3, 2.0, 1.1, 1.1, 1.5, 1.5])
    with r1_c1: meeting_date = st.date_input("Date", value=datetime.date.today())
    with r1_c2: meeting_location = st.text_input("Location", value="Greatwork Mega Tower Boardroom")
    with r1_c3:
        start_time_idx = TIME_OPTIONS.index("02:30 PM") if "02:30 PM" in TIME_OPTIONS else 29
        start_time = st.selectbox("Start", options=TIME_OPTIONS, index=start_time_idx)
    with r1_c4:
        end_time_idx = TIME_OPTIONS.index("05:00 PM") if "05:00 PM" in TIME_OPTIONS else 34
        end_time = st.selectbox("End", options=TIME_OPTIONS, index=end_time_idx)
    with r1_c5: prep_name = st.text_input("Prepared By (Name)", placeholder="e.g. John Doe")
    with r1_c6: prep_desig = st.text_input("Designation", placeholder="e.g. Associate")

    # ROW 2
    r2_c1, r2_c2, r2_c3, r2_c4, r2_c5 = st.columns([1.5, 2.0, 2.0, 1.5, 1.5])
    with r2_c1: client_name = st.text_input("Client / Company", placeholder="XYZ Company")
    with r2_c2: selected_crd = st.multiselect("CRD Team Attendees", options=CRD_MEMBERS, default=CRD_MEMBERS)
    with r2_c3: ext_attendees_raw = st.text_input("External Attendees", placeholder="e.g. Mr. ABCD, Jane Doe")
    with r2_c4: conf_name = st.text_input("Confirmed By (Name)", placeholder="e.g. Client Rep")
    with r2_c5: conf_desig = st.text_input("Designation", placeholder="e.g. Managing Director")

    # Three Tabs
    tab_upload, tab_record, tab_text = st.tabs(["Upload Audio", "Record Audio", "Upload Text"])

    with tab_upload:
        u_col1, u_col2 = st.columns([5, 1.5])
        with u_col1:
            uploaded_file = st.file_uploader("Upload audio file", type=["wav", "mp3", "m4a", "ogg", "flac", "mp4", "webm"], label_visibility="collapsed")
        if uploaded_file:
            with u_col2:
                if st.button("Transcribe Audio", key="btn_tx_upload"):
                    with st.spinner("Transcribing with Groq Whisper..."):
                        transcript = transcribe_audio(uploaded_file.read())
                    if transcript:
                        st.session_state["transcript"] = transcript
                        st.session_state["df"] = pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"])
                        st.session_state["other_discussions"] = ""
                        st.rerun()

    with tab_record:
        r_col1, r_col2, r_col3 = st.columns([4, 1.5, 1.5])
        with r_col1:
            recorded_audio = st.audio_input("Record audio directly", label_visibility="collapsed")
        if recorded_audio:
            rec_bytes = recorded_audio.read()
            with r_col2:
                st.download_button(label="Save Recording (.wav)", data=rec_bytes, file_name=f"Recording_{datetime.date.today().strftime('%Y%m%d')}.wav", mime="audio/wav")
            with r_col3:
                if st.button("Transcribe Audio", key="btn_tx_record"):
                    with st.spinner("Transcribing with Groq Whisper..."):
                        transcript = transcribe_audio(rec_bytes)
                    if transcript:
                        st.session_state["transcript"] = transcript
                        st.session_state["df"] = pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"])
                        st.session_state["other_discussions"] = ""
                        st.rerun()

    with tab_text:
        text_col1, text_col2 = st.columns([5, 1.5])
        with text_col1:
            uploaded_text_file = st.file_uploader("Upload Document (.txt, .docx, .pdf)", type=["txt", "docx", "pdf"])
            pasted_text = st.text_area("Or Paste Transcript Here", height=100, placeholder="Paste transcript text directly here...")
        with text_col2:
            st.write("") 
            st.write("") 
            if st.button("Process Text", key="btn_tx_text"):
                extracted_str = ""
                if uploaded_text_file:
                    extracted_str = extract_text_from_file(uploaded_text_file)
                if pasted_text and pasted_text.strip():
                    extracted_str += "\n" + pasted_text.strip()
                
                if extracted_str.strip():
                    st.session_state["transcript"] = extracted_str.strip()
                    st.session_state["df"] = pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"])
                    st.session_state["other_discussions"] = ""
                    st.rerun()
                else:
                    st.warning("Please upload a file or paste text to proceed.")

# ---- Step 2: Full Transcript UI ----
if st.session_state["transcript"]:
    with st.container(border=True):
        st.markdown('<h3>Full Transcript</h3>', unsafe_allow_html=True)
        st.text_area("Transcript Content", st.session_state["transcript"], height=350, label_visibility="collapsed")
        
        if st.session_state["df"].empty:
            if st.button("Generate MOM"):
                with st.spinner("Generating Minutes of the Meeting..."):
                    extracted_df, other_disc = extract_structured_insights(st.session_state["transcript"])
                if extracted_df is not None and not extracted_df.empty:
                    st.session_state["df"] = extracted_df
                    st.session_state["other_discussions"] = other_disc
                    st.rerun()

# ---- Step 3: Minutes of Meeting Editor ----
if not st.session_state["df"].empty:
    with st.container(border=True):
        st.markdown('<h3>Minutes of Meeting Editor</h3>', unsafe_allow_html=True)
        
        edited_df = st.data_editor(
            st.session_state["df"],
            num_rows="dynamic",
            use_container_width=True,
            key="mom_editor",
            column_config={
                "Discussion Points": st.column_config.TextColumn("Discussion Points", width="large"),
                "Action Plan": st.column_config.TextColumn("Action Plan", width="medium"),
                "Indicative Delivery Date": st.column_config.TextColumn("Indicative Delivery Date", width="small"),
                "Person-in-charge": st.column_config.TextColumn("Person-in-charge", width="small")
            }
        )
        st.session_state["df"] = edited_df

        st.session_state["other_discussions"] = st.text_area("Other Discussions", value=st.session_state["other_discussions"], height=100)

        meeting_details = {
            "date": meeting_date.strftime("%B %d, %Y"),
            "time_range": f"{start_time} to {end_time}",
            "location": meeting_location,
            "company_name": client_name if client_name else "CLIENT",
            "prime_attendees": selected_crd,
            "external_attendees": [x.strip() for x in ext_attendees_raw.split(",") if x.strip()],
            "prep_name": prep_name,
            "prep_desig": prep_desig,
            "conf_name": conf_name,
            "conf_desig": conf_desig
        }

        doc_bio = export_to_word(
            st.session_state["df"],
            meeting_details,
            st.session_state["other_discussions"]
        )

        st.download_button(
            label="Download Minutes of the Meeting (.docx)",
            data=doc_bio,
            file_name=f"MOM_{client_name.replace(' ', '_') if client_name else 'Report'}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
