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

# API Keys & Endpoints loaded via st.secrets with fallback defaults
DEEPSEEK_API_KEY = st.secrets.get("DEEPSEEK_API_KEY", "sk-7b4c611f153f4fe0adc1a1cbd13a2930")
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/chat/completions"

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "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")
GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

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

# Initialize Session State Variables
if "transcript" not in st.session_state: st.session_state["transcript"] = ""
if "df" not in st.session_state: st.session_state["df"] = pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"])
if "other_discussions" not in st.session_state: st.session_state["other_discussions"] = ""
if "show_settings" not in st.session_state: st.session_state["show_settings"] = False
if "tokens_used" not in st.session_state: st.session_state["tokens_used"] = 0
if "last_api_call" not in st.session_state: st.session_state["last_api_call"] = None
if "selected_engine" not in st.session_state: st.session_state["selected_engine"] = "DeepSeek (Primary)"

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
.stTextArea textarea {
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
}

.settings-header-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}
</style>
"""

# ========== SVG ICONS ==========
SVG_SETTINGS = """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#222222" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>"""
SVG_REFRESH = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>"""
SVG_DOWNLOAD = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>"""
SVG_ALERT = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#D4AF37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>"""

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

def extract_with_deepseek(transcript):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "You are an expert executive assistant for PRIME Philippines extracting Minutes of the Meeting (MOM). "
        "The transcript contains Tagalog and English (Taglish) dialogue. "
        "Understand the core thought and context, translating all colloquial conversation into polished, professional corporate English. "
        "Extract every discussion topic, report update, action plan, delivery date, and person-in-charge. "
        "Respond ONLY with a valid JSON object matching the requested schema."
    )

    user_prompt = f"""Extract the Minutes of Meeting from this transcript into valid JSON.
Extract 4 to 10 clear, distinct items covering all topics discussed.

JSON Schema:
{{
  "table_items": [
    {{
      "Discussion Points": "Core discussion topic, report update, or milestone",
      "Action Plan": "Concrete next step, deliverable, or requirement (put 'None' if none)",
      "Indicative Delivery Date": "Specific date, timeline (e.g. Friday, Q1 2027), or 'TBD'",
      "Person-in-charge": "Responsible entity (e.g. PRIME, Client name, or Unassigned)"
    }}
  ],
  "other_discussions": "Summary of informal remarks, administrative notes, or general context"
}}

Transcript:
{transcript[:35000]}"""

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
        "max_tokens": 2048
    }

    try:
        resp = requests.post(DEEPSEEK_CHAT_URL, headers=headers, json=payload, timeout=120)
        if resp.status_code == 200:
            res_json = resp.json()
            usage = res_json.get("usage", {})
            st.session_state["tokens_used"] += usage.get("total_tokens", len(transcript) // 4)
            st.session_state["last_api_call"] = datetime.datetime.now()

            raw_text = res_json["choices"][0]["message"]["content"].strip()
            clean_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            clean_text = re.sub(r"\s*```$", "", clean_text).strip()
            match = re.search(r"\{.*\}", clean_text, re.DOTALL)
            data = json.loads(match.group(0)) if match else json.loads(clean_text)
            return normalize_llm_json_to_df(data)
        else:
            st.warning(f"DeepSeek Notice ({resp.status_code}): {resp.text}")
    except Exception as e:
        st.warning(f"DeepSeek connection error: {e}")

    return None, ""

def heuristic_non_ai_extraction(transcript):
    sentences = re.split(r'(?<=[.!?]) +', transcript)
    
    action_keywords = ['send', 'prepare', 'submit', 'update', 'review', 'check', 'email', 'kailangan', 'gagawin', 'ipapasa', 'provide', 'target', 'ipresent', 'kukunin']
    date_keywords = ['tomorrow', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'q1', 'q2', 'q3', 'q4', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december', 'bukas', 'deadline']
    
    table_items = []
    other_discussions = []
    
    for i in range(0, len(sentences), 3):
        chunk = sentences[i:i+3]
        if not chunk: continue
        chunk_text = " ".join(chunk)
        
        has_action = any(kw in chunk_text.lower() for kw in action_keywords)
        has_date = any(kw in chunk_text.lower() for kw in date_keywords)
        
        if has_action or has_date:
            action_text = " ".join([s for s in chunk if any(kw in s.lower() for kw in action_keywords)])
            table_items.append({
                "Discussion Points": chunk[0].strip() + "...",
                "Action Plan": action_text.strip() if action_text else "Review discussion for actions",
                "Indicative Delivery Date": "Check transcript (Date mentioned)" if has_date else "TBD",
                "Person-in-charge": "Unassigned"
            })
        else:
            other_discussions.append(chunk_text)
            
    if not table_items:
        table_items = [{
            "Discussion Points": "Meeting Overview",
            "Action Plan": "Please review transcript manually.",
            "Indicative Delivery Date": "TBD",
            "Person-in-charge": "Unassigned"
        }]
        
    df = pd.DataFrame(table_items[:10])
    for col in ["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]:
        if col not in df.columns:
            df[col] = ""
            
    df = df[["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]]
    other_text = "\n\n".join(other_discussions[:4])
    return df, other_text

def extract_structured_insights(transcript, engine="DeepSeek (Primary)"):
    progress_container = st.empty()
    bar = progress_container.progress(0, text=f"Initializing {engine}...")

    if engine == "Python Heuristic (Non-AI)":
        bar.progress(100, text="Extracting with Rule-Based Heuristic...")
        time.sleep(0.5)
        progress_container.empty()
        return heuristic_non_ai_extraction(transcript)

    bar.progress(35, text="Translating Taglish & Extracting MOM via DeepSeek V3...")
    df, other = extract_with_deepseek(transcript)
    
    if df is not None and not df.empty:
        bar.progress(100, text="Finalizing Minutes of the Meeting...")
        time.sleep(0.3)
        progress_container.empty()
        return df, other

    bar.progress(90, text="DeepSeek unavailable. Running Non-AI Keyword Extraction...")
    df_fb, other_fb = heuristic_non_ai_extraction(transcript)
    progress_container.empty()
    st.markdown(f"{SVG_ALERT} DeepSeek request could not be completed. The table below was populated using offline Keyword Heuristics.", unsafe_allow_html=True)
    return df_fb, other_fb

def set_cell_shading(cell, color_hex):
    shd = parse_xml(f'<w:shd xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shd)

def export_to_word(df, meeting_details, other_discussions):
    doc = Document()
    
    # Configure 0.5-inch compact page margins for professional MOM templates
    for section in doc.sections:
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
        
        # Apply Header Image
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if os.path.exists("header.png"):
            hp.add_run().add_picture("header.png", width=Inches(6.8))
        else:
            # Fallback Corporate Header Text
            hrun = hp.add_run("PRIME PHILIPPINES | COMMERCIAL REAL ESTATE ADVISORY")
            hrun.font.name = "Arial"
            hrun.font.size = Pt(8.5)
            hrun.font.color.rgb = RGBColor(128, 128, 128)
            
        # Apply Footer Image
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if os.path.exists("footer.png"):
            fp.add_run().add_picture("footer.png", width=Inches(6.8))
        else:
            # Fallback Corporate Footer Text
            frun = fp.add_run("Confidential - For Internal and Client Collaboration Only")
            frun.font.name = "Arial"
            frun.font.size = Pt(8)
            frun.font.italic = True
            frun.font.color.rgb = RGBColor(150, 150, 150)

    # Document Header Title
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
        p_od_head = doc.add_paragraph()
        p_od_head.paragraph_format.space_before = Pt(8)
        r_od_head = p_od_head.add_run("Other Discussions:")
        r_od_head.bold = True
        r_od_head.font.size = Pt(10)
        r_od_head.font.name = "Arial"
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
                extracted_df, other_disc = extract_structured_insights(st.session_state["transcript"], st.session_state["selected_engine"])
                if not extracted_df.empty:
                    st.session_state["df"] = extracted_df
                    st.session_state["other_discussions"] = other_disc
                    st.rerun()

# ---- Step 3: Minutes of Meeting Editor with SVG Settings ----
if not st.session_state["df"].empty:
    with st.container(border=True):
        h_col1, h_col2 = st.columns([9.4, 0.6])
        with h_col1:
            st.markdown('<h3>Minutes of Meeting Editor</h3>', unsafe_allow_html=True)
        with h_col2:
            st.markdown(
                f'<div style="text-align: right; padding-top: 5px;">{SVG_SETTINGS}</div>', 
                unsafe_allow_html=True
            )
            if st.button("Settings", key="btn_toggle_settings", help="Open Engine & Regeneration Settings"):
                st.session_state["show_settings"] = not st.session_state["show_settings"]
                st.rerun()

        # Engine Settings & Usage Drawer
        if st.session_state["show_settings"]:
            with st.expander("Engine Configuration & Usage Diagnostics", expanded=True):
                set_col1, set_col2 = st.columns([1.5, 1.5])
                
                with set_col1:
                    engine_options = [
                        "DeepSeek (Primary)",
                        "Python Heuristic (Non-AI)"
                    ]
                    selected_eng = st.selectbox(
                        "Extraction Engine",
                        options=engine_options,
                        index=engine_options.index(st.session_state["selected_engine"]) if st.session_state["selected_engine"] in engine_options else 0
                    )
                    st.session_state["selected_engine"] = selected_eng

                    if st.button("Regenerate MOM", key="btn_regen_mom"):
                        if st.session_state["transcript"]:
                            extracted_df, other_disc = extract_structured_insights(st.session_state["transcript"], selected_eng)
                            if not extracted_df.empty:
                                st.session_state["df"] = extracted_df
                                st.session_state["other_discussions"] = other_disc
                                st.rerun()

                with set_col2:
                    st.markdown("**Token Usage Diagnostics**")
                    st.write(f"• **Session Tokens Processed:** `{st.session_state['tokens_used']:,}`")
                    
                    if st.session_state["last_api_call"]:
                        last_call = st.session_state["last_api_call"]
                        st.write(f"• **Last Request Time:** `{last_call.strftime('%I:%M:%S %p')}`")
                        st.write("• **DeepSeek Server Status:** `Active & Ready`")
                    else:
                        st.write("• **DeepSeek Server Status:** `Ready`")
                st.markdown("---")

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
