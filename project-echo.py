import os
import time
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
PUTER_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InYyIn0.eyJ0IjoidCIsInYiOiIyIiwidG9rZW5fdWlkIjoiODUxNzZhZjYtZmM2Ni00M2ZjLTk2NmEtN2ZhMGQ3YWFlMjhhIiwidXUiOiJXQkx3bS9QM1ErQ3VBVDNTQjZDS1ZBPT0iLCJzdSI6ImkwL1N5ajZQUkZHbWhVTGdTS2lkYlE9PSIsImFpIjoiV0JMd20vUDNRK0N1QVQzU0I2Q0tWQT09IiwiZnVsbF9hY2Nlc3MiOnRydWUsImlhdCI6MTc4NzYyMjk4M30.C1hpyilomEizU-bP5ZXimpssrCUOMS1Pv6abBKjYFMQ"
GROQ_API_KEY = "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"

GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
PUTER_CHAT_URL = "https://api.puter.com/v1/chat/completions"

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
.block-container { padding-top: 5.5rem !important; }

.echo-topbar {
    position: fixed; top: 0; left: 0; right: 0; height: 60px;
    background-color: #161616;
    border-bottom: 1px solid #333333;
    display: flex; align-items: center; padding: 0 2rem;
    z-index: 999999; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}
.echo-topbar h1 {
    font-family: 'Playfair Display', serif !important;
    font-style: italic !important; font-weight: 400 !important;
    font-size: 1.35rem !important; color: #FFFFFF !important; margin: 0 !important;
}
.echo-topbar h1 span { color: #D4AF37 !important; }

h3 {
    font-family: 'Playfair Display', serif !important;
    font-style: italic !important; font-weight: 400 !important; 
    color: #1A2B4C !important; letter-spacing: 0.02em; margin-bottom: 0.25rem; font-size: 1.25rem !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important; border-radius: 12px !important;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.04) !important;
    border: 1px solid rgba(0, 0, 0, 0.04) !important; 
    padding: 1.25rem !important margin-bottom: 1rem !important;
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
.stTextArea textarea {
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
}
</style>
"""

# ========== CORE LOGIC ==========
def extract_text_from_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.txt'):
            return uploaded_file.getvalue().decode("utf-8")
        elif uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        elif uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            return "\n".join([para.text for para in doc.paragraphs])
        return ""
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return ""

def transcribe_audio(audio_bytes):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {"file": ("audio.wav", audio_bytes), "model": (None, "whisper-large-v3-turbo"), "response_format": (None, "json")}
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

def normalize_llm_json_to_df(data):
    """Universal parser: Converts any LLM JSON format into the standardized MOM DataFrame."""
    items = None
    other_disc = ""
    
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for key in ["table_items", "items", "minutes", "table", "data", "discussion_items", "discussions", "action_items"]:
            if key in data and isinstance(data[key], list) and len(data[key]) > 0:
                items = data[key]
                break
        if items is None:
            for v in data.values():
                if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                    items = v
                    break
            if items is None:
                items = [data]
                
        other_disc = str(data.get("other_discussions", "") or data.get("notes", "") or data.get("summary", ""))

    if not items or not isinstance(items, list):
        return None, ""

    df = pd.DataFrame(items)
    col_mapping = {}
    for c in df.columns:
        c_clean = str(c).lower().replace("_", " ").replace("-", " ")
        if any(k in c_clean for k in ["discuss", "point", "topic", "milestone"]):
            col_mapping[c] = "Discussion Points"
        elif any(k in c_clean for k in ["action", "plan", "step", "deliverable"]):
            col_mapping[c] = "Action Plan"
        elif any(k in c_clean for k in ["date", "time", "delivery", "deadline"]):
            col_mapping[c] = "Indicative Delivery Date"
        elif any(k in c_clean for k in ["person", "charge", "pic", "assign", "who", "responsible"]):
            col_mapping[c] = "Person-in-charge"

    df = df.rename(columns=col_mapping)
    for col in ["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]:
        if col not in df.columns:
            df[col] = ""
            
    df = df[["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]].drop_duplicates()
    return df, other_disc

def extract_with_puter(prompt):
    """Engine 1: Puter AI. Proxies to GPT-4o-mini for robust large-context extraction."""
    headers = {"Authorization": f"Bearer {PUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You extract Minutes of the Meeting from transcripts. Translate colloquial terms to business English. Output ONLY valid JSON matching the schema."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }
    try:
        resp = requests.post(PUTER_CHAT_URL, headers=headers, json=payload, timeout=90)
        if resp.status_code == 200:
            raw_text = resp.json()["choices"][0]["message"]["content"].strip()
            clean_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            clean_text = re.sub(r"\s*```$", "", clean_text).strip()
            match = re.search(r"\{.*\}", clean_text, re.DOTALL)
            data = json.loads(match.group(0)) if match else json.loads(clean_text)
            return normalize_llm_json_to_df(data)
    except Exception:
        pass
    return None, ""

def call_groq_json(prompt, models=["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]):
    """Engine 2: Groq Direct API Call."""
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    for model in models:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are an executive assistant extracting Minutes of the Meeting. Translate Taglish to English. Respond ONLY with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }
        try:
            resp = requests.post(GROQ_CHAT_URL, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                raw_text = resp.json()["choices"][0]["message"]["content"].strip()
                clean_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                clean_text = re.sub(r"\s*```$", "", clean_text).strip()
                match = re.search(r"\{.*\}", clean_text, re.DOTALL)
                data = json.loads(match.group(0)) if match else json.loads(clean_text)
                return normalize_llm_json_to_df(data)
        except Exception:
            continue
    return None, ""

def build_schema_prompt(text_section):
    return f"""Extract Minutes of the Meeting from the transcript. Translate Taglish to professional English.
Output valid JSON ONLY matching:
{{
  "table_items": [
    {{
      "Discussion Points": "Core discussion topic, report, or milestone",
      "Action Plan": "Specific follow-up action, deliverable, or 'None'",
      "Indicative Delivery Date": "Specific date, timeline, or 'TBD'",
      "Person-in-charge": "Responsible entity (e.g., PRIME, Client, or Unassigned)"
    }}
  ],
  "other_discussions": "Summary of other points discussed"
}}

Transcript:
{text_section}"""

def heuristic_non_ai_extraction(transcript):
    """
    ENGINE 3 (NON-AI FALLBACK): 
    Uses Python heuristics, regex, and keywords to build the table if AI APIs fail completely.
    """
    sentences = re.split(r'(?<=[.!?]) +', transcript)
    
    # Taglish/English Action and Date Keywords
    action_keywords = ['send', 'prepare', 'submit', 'update', 'review', 'check', 'email', 'kailangan', 'gagawin', 'ipapasa', 'provide', 'gawa', 'target', 'need', 'will do', 'ipresent', 'kukunin']
    date_keywords = ['tomorrow', 'next week', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'q1', 'q2', 'q3', 'q4', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december', 'bukas', 'sa susunod', 'deadline']
    
    table_items = []
    other_discussions = []
    
    # Group sentences into chunks of 3 to form pseudo-topics
    for i in range(0, len(sentences), 3):
        chunk = sentences[i:i+3]
        if not chunk: continue
        
        chunk_text = " ".join(chunk)
        
        has_action = any(kw in chunk_text.lower() for kw in action_keywords)
        has_date = any(kw in chunk_text.lower() for kw in date_keywords)
        
        if has_action or has_date:
            action_text = " ".join([s for s in chunk if any(kw in s.lower() for kw in action_keywords)])
            date_text = " ".join([s for s in chunk if any(kw in s.lower() for kw in date_keywords)])
            
            table_items.append({
                "Discussion Points": chunk[0].strip() + "...",  # First sentence as topic
                "Action Plan": action_text.strip() if action_text else "Review discussion for actions",
                "Indicative Delivery Date": "Check transcript (Date mentioned)" if has_date else "TBD",
                "Person-in-charge": "Unassigned"
            })
        else:
            other_discussions.append(chunk_text)
            
    # Limit to top 10 items to keep table clean
    if len(table_items) > 10:
        table_items = table_items[:10]
        
    if not table_items:
        table_items = [{
            "Discussion Points": "Meeting Overview",
            "Action Plan": "No specific action keywords detected. Please review transcript manually.",
            "Indicative Delivery Date": "TBD",
            "Person-in-charge": "Unassigned"
        }]
        
    df = pd.DataFrame(table_items)
    for col in ["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]:
        if col not in df.columns:
            df[col] = ""
            
    df = df[["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]]
    other_text = "\n\n".join(other_discussions[:5]) + ("\n...(truncated)" if len(other_discussions) > 5 else "")
    
    return df, "Auto-extracted via Keyword Rules (AI Limit Reached):\n" + other_text

def extract_structured_insights(transcript):
    """Dynamic Engine: Puter AI -> Groq -> Non-AI Heuristic Regex Rule Engine"""
    progress_container = st.empty()
    bar = progress_container.progress(0, text="Initializing Extraction Engine...")

    # We use a safe substring limit for single-pass API calls (prevents 429 limits)
    safe_transcript = transcript[:18000]
    full_prompt = build_schema_prompt(safe_transcript)

    # 1. Try Puter API (GPT-4o-mini)
    bar.progress(20, text="Attempting extraction via Puter AI (Large Context)...")
    res_puter = extract_with_puter(full_prompt)
    if res_puter and res_puter[0] is not None and not res_puter[0].empty:
        progress_container.empty()
        return res_puter[0], res_puter[1]

    # 2. Try Groq (Llama 3.3)
    bar.progress(60, text="Puter busy. Attempting Groq Analysis...")
    res_groq = call_groq_json(full_prompt)
    if res_groq and res_groq[0] is not None and not res_groq[0].empty:
        progress_container.empty()
        return res_groq[0], res_groq[1]

    # 3. Non-AI Fallback Engine
    bar.progress(90, text="AI API Limits Reached. Running Non-AI Keyword Extraction...")
    df, other = heuristic_non_ai_extraction(transcript)
    
    progress_container.empty()
    st.warning("⚠️ AI servers are currently busy/rate-limited. The table below was populated using our offline Keyword Engine based on action words in the text.")
    return df, other

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
                extracted_df, other_disc = extract_structured_insights(st.session_state["transcript"])
                if not extracted_df.empty:
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
