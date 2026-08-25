import os
import time
import subprocess
import tempfile
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
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

# ========== CONFIG ==========
st.set_page_config(page_title="Project Echo", layout="wide", initial_sidebar_state="collapsed")

# --- PROGRAMMATIC LIGHT MODE & 200MB LIMIT ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
os.makedirs(_config_dir, exist_ok=True)
with open(_config_file, "w", encoding="utf-8") as f:
    f.write('[theme]\nbase="light"\n[server]\nmaxUploadSize = 200\n')

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

# 12-Hour AM/PM Time Options with blank default
TIME_OPTIONS = [""]
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
.block-container { padding-top: 5.2rem !important; }

/* Fixed Topbar */
.echo-topbar-wrapper {
    position: fixed; top: 0; left: 0; right: 0; height: 60px;
    background-color: #161616;
    border-bottom: 1px solid #333333;
    z-index: 999999; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 2rem;
}

.echo-title {
    font-family: 'Playfair Display', serif !important;
    font-style: italic !important; font-weight: 400 !important;
    font-size: 1.35rem !important; color: #FFFFFF !important; margin: 0 !important;
}
.echo-title span { color: #D4AF37 !important; }

/* Topbar Settings Button Styling */
div[data-testid="stHorizontalBlock"]:has(button[key="topbar_settings_btn"]) {
    position: fixed !important;
    top: 10px !important;
    right: 2rem !important;
    z-index: 1000000 !important;
    width: auto !important;
}

button[key="topbar_settings_btn"] {
    background: transparent !important;
    border: 1px solid #444444 !important;
    border-radius: 50% !important;
    width: 40px !important;
    height: 40px !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.3s ease !important;
}
button[key="topbar_settings_btn"]:hover {
    border-color: #D4AF37 !important;
    background-color: #222222 !important;
}

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

.loading-banner {
    display: flex;
    align-items: center;
    gap: 12px;
    background-color: #FFFFFF;
    border: 1px solid #D4AF37;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 12px 0;
    box-shadow: 0 4px 12px rgba(212, 175, 55, 0.15);
}
.loading-banner span {
    font-size: 0.9rem;
    font-weight: 500;
    color: #161616;
}
</style>
"""

# ========== SVG ICONS ==========
SVG_ALERT = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#D4AF37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>"""
SVG_SPINNER = """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#D4AF37" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="animation: spin 1s linear infinite;"><style>@keyframes spin { 100% { transform: rotate(360deg); } }</style><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>"""

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

def _call_groq_whisper(audio_bytes, filename="audio.mp3"):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {"file": (filename, audio_bytes), "model": (None, "whisper-large-v3-turbo"), "response_format": (None, "json")}
    resp = requests.post(GROQ_AUDIO_URL, headers=headers, files=files)
    if resp.status_code == 200:
        return resp.json().get("text", "")
    else:
        error_msg = resp.json().get("error", {}).get("message", resp.text)
        if "rate limit" in error_msg.lower():
            time.sleep(10)
            resp = requests.post(GROQ_AUDIO_URL, headers=headers, files=files)
            if resp.status_code == 200:
                return resp.json().get("text", "")
        st.error(f"Transcription error: {error_msg}")
        return None

def transcribe_audio_pipeline(audio_bytes, original_filename, progress_container=None):
    file_size_mb = len(audio_bytes) / (1024 * 1024)

    if file_size_mb <= 24.0:
        if progress_container:
            progress_container.markdown(f'<div class="loading-banner">{SVG_SPINNER} <span>Sending audio directly to Groq Whisper ({file_size_mb:.1f} MB)...</span></div>', unsafe_allow_html=True)
        return _call_groq_whisper(audio_bytes, original_filename)

    ext = os.path.splitext(original_filename)[1] or ".m4a"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as src:
        src.write(audio_bytes)
        src_path = src.name

    compressed_mp3 = src_path + "_whisper_ready.mp3"
    
    if progress_container:
        progress_container.markdown(f'<div class="loading-banner">{SVG_SPINNER} <span>Compressing {file_size_mb:.1f} MB audio to mono 16kHz (CPU & RAM protected)...</span></div>', unsafe_allow_html=True)

    try:
        cmd = [
            "ffmpeg", "-y",
            "-threads", "1",
            "-preset", "ultrafast",
            "-i", src_path,
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "libmp3lame",
            "-b:a", "24k",
            compressed_mp3
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        comp_size_mb = os.path.getsize(compressed_mp3) / (1024 * 1024)

        if comp_size_mb <= 24.0:
            if progress_container:
                progress_container.markdown(f'<div class="loading-banner">{SVG_SPINNER} <span>Transcribing compressed file ({comp_size_mb:.1f} MB) with Groq Whisper...</span></div>', unsafe_allow_html=True)
            with open(compressed_mp3, "rb") as f:
                c_bytes = f.read()
            return _call_groq_whisper(c_bytes, "compressed.mp3")

        if progress_container:
            progress_container.markdown(f'<div class="loading-banner">{SVG_SPINNER} <span>Slicing multi-hour recording into safe 15-minute segments...</span></div>', unsafe_allow_html=True)

        segment_pattern = src_path + "_seg_%03d.mp3"
        subprocess.run([
            "ffmpeg", "-y", "-i", compressed_mp3,
            "-f", "segment", "-segment_time", "900", "-c", "copy",
            segment_pattern
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        seg_dir = os.path.dirname(src_path)
        base_name = os.path.basename(src_path) + "_seg_"
        segments = sorted([os.path.join(seg_dir, f) for f in os.listdir(seg_dir) if f.startswith(base_name)])

        full_transcript = []
        for idx, seg in enumerate(segments):
            if progress_container:
                progress_container.markdown(f'<div class="loading-banner">{SVG_SPINNER} <span>Transcribing segment {idx + 1} of {len(segments)}...</span></div>', unsafe_allow_html=True)
            with open(seg, "rb") as f:
                seg_bytes = f.read()
            t = _call_groq_whisper(seg_bytes, f"part_{idx}.mp3")
            if t:
                full_transcript.append(t)
            time.sleep(1.0)
            try: os.remove(seg)
            except: pass

        return " ".join(full_transcript)

    except Exception as e:
        st.warning(f"Audio processing fallback: {e}")
        return _call_groq_whisper(audio_bytes, original_filename)
    finally:
        if os.path.exists(src_path):
            try: os.remove(src_path)
            except: pass
        if os.path.exists(compressed_mp3):
            try: os.remove(compressed_mp3)
            except: pass

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
    progress_container.markdown(f'<div class="loading-banner">{SVG_SPINNER} <span>Translating Taglish conversation & structuring MOM with {engine}...</span></div>', unsafe_allow_html=True)

    if engine == "Python Heuristic (Non-AI)":
        time.sleep(0.5)
        res_df, res_other = heuristic_non_ai_extraction(transcript)
        progress_container.empty()
        return res_df, res_other

    df, other = extract_with_deepseek(transcript)
    
    if df is not None and not df.empty:
        progress_container.empty()
        return df, other

    df_fb, other_fb = heuristic_non_ai_extraction(transcript)
    progress_container.empty()
    st.markdown(f"{SVG_ALERT} DeepSeek request could not be completed. The table below was populated using offline Keyword Heuristics.", unsafe_allow_html=True)
    return df_fb, other_fb

def set_cell_shading(cell, color_hex):
    shd = parse_xml(f'<w:shd xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shd)

def export_to_word(df, meeting_details, other_discussions):
    template_files = ["MOM_Template.docx", "MOM Template.docx"]
    template_path = next((f for f in template_files if os.path.exists(f)), None)

    if template_path:
        doc = Document(template_path)
    else:
        doc = Document()
        if os.path.exists("header.png"):
            for section in doc.sections:
                section.top_margin = Inches(0.4)
                section.bottom_margin = Inches(0.4)
                section.left_margin = Inches(0.75)
                section.right_margin = Inches(0.75)
                hp = section.header.paragraphs[0]
                hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                hp.add_run().add_picture("header.png", width=Inches(7.0))
                if os.path.exists("footer.png"):
                    fp = section.footer.paragraphs[0]
                    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    fp.add_run().add_picture("footer.png", width=Inches(7.0))

    for section in doc.sections:
        section.top_margin = Inches(0.4)
        section.bottom_margin = Inches(0.4)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(2)
    r_title = p_title.add_run("MINUTES OF THE MEETING")
    r_title.bold = True
    r_title.underline = True
    r_title.font.name = "Arial"
    r_title.font.size = Pt(11)

    company_target = meeting_details.get("external_attendees", [])
    primary_client_rep = company_target[0] if company_target else meeting_details.get("company_name", "").strip() or "CLIENT"
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(12)
    r_sub = p_sub.add_run(f"PRIME PHILIPPINES & {primary_client_rep.upper()}")
    r_sub.bold = True
    r_sub.font.name = "Arial"
    r_sub.font.size = Pt(11)

    date_str = meeting_details.get("date", "____________")
    time_str = meeting_details.get("time_range", "")
    full_date = f"Date: {date_str}" + (f", {time_str}" if time_str.strip() else "")
    
    p_date = doc.add_paragraph(full_date)
    p_date.paragraph_format.space_after = Pt(2)
    for r in p_date.runs: r.font.name = "Arial"; r.font.size = Pt(10)

    p_loc = doc.add_paragraph(f"Location: {meeting_details.get('location', '____________')}")
    p_loc.paragraph_format.space_after = Pt(2)
    for r in p_loc.runs: r.font.name = "Arial"; r.font.size = Pt(10)

    prime_atts = meeting_details.get("prime_attendees", [])
    ext_atts = meeting_details.get("external_attendees", [])
    
    p_att = doc.add_paragraph()
    p_att.paragraph_format.space_after = Pt(2)
    p_att.paragraph_format.tab_stops.add_tab_stop(Inches(1.35), WD_TAB_ALIGNMENT.LEFT)
    r_att_label = p_att.add_run("Attended by:")
    r_att_label.font.name = "Arial"
    r_att_label.font.size = Pt(10)
    
    first_attendee = True
    if ext_atts:
        for att in ext_atts:
            if not att.strip(): continue
            p = p_att if first_attendee else doc.add_paragraph()
            p.paragraph_format.space_after = Pt(2)
            if not first_attendee:
                p.paragraph_format.left_indent = Inches(1.35)
            else:
                p.add_run("\t")
            comp_label = f", {meeting_details.get('company_name')}" if meeting_details.get('company_name') else ""
            r = p.add_run(f"{att}{comp_label}")
            r.font.name = "Arial"
            r.font.size = Pt(10)
            first_attendee = False

    if prime_atts:
        for att in prime_atts:
            p = p_att if first_attendee else doc.add_paragraph()
            p.paragraph_format.space_after = Pt(2)
            if not first_attendee:
                p.paragraph_format.left_indent = Inches(1.35)
            else:
                p.add_run("\t")
            r = p.add_run(f"{att} – PRIME Philippines")
            r.font.name = "Arial"
            r.font.size = Pt(10)
            first_attendee = False

    p_line = doc.add_paragraph()
    p_line.paragraph_format.space_before = Pt(4)
    p_line.paragraph_format.space_after = Pt(6)
    r_line = p_line.add_run("_________________________________________________________________________________")
    r_line.font.name = "Arial"
    r_line.font.color.rgb = RGBColor(160, 160, 160)

    client_display = meeting_details.get('company_name', '').strip() or "the Client"
    p_intro = doc.add_paragraph(
        f"During the meeting held last {date_str}, PRIME Philippines, represented by the attendee/s shown above, "
        f"met with {client_display} to discuss opportunities for collaboration."
    )
    p_intro.paragraph_format.space_after = Pt(10)
    for r in p_intro.runs: r.font.name = "Arial"; r.font.size = Pt(9.5)

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
            p.runs[0].font.size = Pt(9)
            p.runs[0].font.name = "Arial"

    for i, row in df.iterrows():
        cells = table.rows[i+1].cells
        cells[0].text = f"{i+1}. {str(row.get('Discussion Points', ''))}"
        cells[1].text = str(row.get("Action Plan", ""))
        cells[2].text = str(row.get("Indicative Delivery Date", ""))
        cells[3].text = str(row.get("Person-in-charge", ""))
        for c_idx, cell in enumerate(cells):
            p = cell.paragraphs[0]
            if c_idx in [2, 3]: p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if p.runs:
                p.runs[0].font.size = Pt(8.5)
                p.runs[0].font.name = "Arial"

    doc.add_paragraph()
    p_note = doc.add_paragraph("*Note: The indicative delivery date serves as reference point and still subject to changes. Furthermore, it depends on the progress of both parties.")
    p_note.paragraph_format.space_after = Pt(8)
    p_note.runs[0].font.italic = True
    p_note.runs[0].font.name = "Arial"
    p_note.runs[0].font.size = Pt(8)

    if other_discussions.strip():
        p_od_head = doc.add_paragraph()
        p_od_head.paragraph_format.space_before = Pt(6)
        p_od_head.paragraph_format.space_after = Pt(4)
        r_od_head = p_od_head.add_run("Other Discussions:")
        r_od_head.bold = True
        r_od_head.font.size = Pt(10)
        r_od_head.font.name = "Arial"
        
        p_od = doc.add_paragraph(other_discussions)
        p_od.paragraph_format.space_after = Pt(12)
        for r in p_od.runs: r.font.name = "Arial"; r.font.size = Pt(9.5)

    p_prep_label = doc.add_paragraph("Prepared by:")
    p_prep_label.paragraph_format.space_before = Pt(12)
    p_prep_label.paragraph_format.space_after = Pt(2)
    p_prep_label.runs[0].font.name = "Arial"; p_prep_label.runs[0].font.bold = True; p_prep_label.runs[0].font.size = Pt(9.5)

    p_prep_line = doc.add_paragraph("_______________________________")
    p_prep_line.paragraph_format.space_after = Pt(2)
    p_prep_line.runs[0].font.name = "Arial"

    prep_name = meeting_details.get("prep_name", "").strip() or "____________________"
    prep_desig = meeting_details.get("prep_desig", "").strip() or "PRIME Philippines"
    p_prep_info = doc.add_paragraph(f"{prep_name}\n{prep_desig}")
    p_prep_info.paragraph_format.space_after = Pt(12)
    for r in p_prep_info.runs: r.font.name = "Arial"; r.font.size = Pt(9.5)

    p_conf_label = doc.add_paragraph("Confirmed by:")
    p_conf_label.paragraph_format.space_after = Pt(2)
    p_conf_label.runs[0].font.name = "Arial"; p_conf_label.runs[0].font.bold = True; p_conf_label.runs[0].font.size = Pt(9.5)

    p_conf_line = doc.add_paragraph("_______________________________")
    p_conf_line.paragraph_format.space_after = Pt(2)
    p_conf_line.runs[0].font.name = "Arial"

    conf_name = meeting_details.get("conf_name", "").strip() or (ext_atts[0] if ext_atts else "____________________")
    conf_desig = meeting_details.get("conf_desig", "").strip() or (meeting_details.get("company_name", "").strip() or "Client")
    p_conf_info = doc.add_paragraph(f"{conf_name}\n{conf_desig}")
    p_conf_info.paragraph_format.space_after = Pt(6)
    for r in p_conf_info.runs: r.font.name = "Arial"; r.font.size = Pt(9.5)

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def export_to_pdf(df, meeting_details, other_discussions):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch
    )
    story = []
    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        alignment=1,
        spaceAfter=2
    )
    company_target = meeting_details.get("external_attendees", [])
    primary_client_rep = company_target[0] if company_target else meeting_details.get("company_name", "").strip() or "CLIENT"
    style_subtitle = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        alignment=1,
        spaceAfter=10
    )
    style_body = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        spaceAfter=3
    )
    style_th = ParagraphStyle(
        'TableHead',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=10,
        alignment=1
    )
    style_td = ParagraphStyle(
        'TableData',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10
    )
    style_td_center = ParagraphStyle(
        'TableDataCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        alignment=1
    )

    if os.path.exists("header.png"):
        story.append(Image("header.png", width=6.8 * inch, height=0.75 * inch))
        story.append(Spacer(1, 6))

    story.append(Paragraph("<u>MINUTES OF THE MEETING</u>", style_title))
    story.append(Paragraph(f"PRIME PHILIPPINES & {primary_client_rep.upper()}", style_subtitle))

    date_str = meeting_details.get("date", "____________")
    time_str = meeting_details.get("time_range", "")
    full_date = f"<b>Date:</b> {date_str}" + (f", {time_str}" if time_str.strip() else "")
    story.append(Paragraph(full_date, style_body))
    story.append(Paragraph(f"<b>Location:</b> {meeting_details.get('location', '____________')}", style_body))

    prime_atts = meeting_details.get("prime_attendees", [])
    ext_atts = meeting_details.get("external_attendees", [])
    att_list = []
    if ext_atts:
        for att in ext_atts:
            if att.strip():
                comp_label = f", {meeting_details.get('company_name')}" if meeting_details.get('company_name') else ""
                att_list.append(f"{att}{comp_label}")
    if prime_atts:
        for att in prime_atts:
            att_list.append(f"{att} – PRIME Philippines")

    if att_list:
        story.append(Paragraph(f"<b>Attended by:</b>&nbsp;&nbsp;&nbsp;&nbsp;{att_list[0]}", style_body))
        for a in att_list[1:]:
            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{a}", style_body))

    story.append(Spacer(1, 4))
    client_display = meeting_details.get('company_name', '').strip() or "the Client"
    story.append(Paragraph(
        f"During the meeting held last {date_str}, PRIME Philippines, represented by the attendee/s shown above, "
        f"met with {client_display} to discuss opportunities for collaboration.",
        style_body
    ))
    story.append(Spacer(1, 6))

    table_data = [[
        Paragraph("<b>Discussion Points</b>", style_th),
        Paragraph("<b>Action Plan</b>", style_th),
        Paragraph("<b>Indicative Delivery Date</b>", style_th),
        Paragraph("<b>Person-in-charge</b>", style_th)
    ]]

    for i, row in df.iterrows():
        table_data.append([
            Paragraph(f"{i+1}. {str(row.get('Discussion Points', ''))}", style_td),
            Paragraph(str(row.get("Action Plan", "")), style_td),
            Paragraph(str(row.get("Indicative Delivery Date", "")), style_td_center),
            Paragraph(str(row.get("Person-in-charge", "")), style_td_center)
        ])

    col_widths = [2.4 * inch, 2.3 * inch, 1.1 * inch, 1.0 * inch]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFFF00')),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)

    note_style = ParagraphStyle('Note', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=7.5, leading=9, spaceBefore=4)
    story.append(Paragraph("*Note: The indicative delivery date serves as reference point and still subject to changes. Furthermore, it depends on the progress of both parties.", note_style))

    if other_discussions.strip():
        story.append(Spacer(1, 6))
        story.append(Paragraph("<b>Other Discussions:</b>", style_body))
        story.append(Paragraph(other_discussions, style_body))

    story.append(Spacer(1, 8))
    prep_name = meeting_details.get("prep_name", "").strip() or "____________________"
    prep_desig = meeting_details.get("prep_desig", "").strip() or "PRIME Philippines"
    conf_name = meeting_details.get("conf_name", "").strip() or (ext_atts[0] if ext_atts else "____________________")
    conf_desig = meeting_details.get("conf_desig", "").strip() or (meeting_details.get("company_name", "").strip() or "Client")

    sign_data = [
        [Paragraph("<b>Prepared by:</b>", style_body), Paragraph("<b>Confirmed by:</b>", style_body)],
        [Paragraph("_______________________________", style_body), Paragraph("_______________________________", style_body)],
        [Paragraph(f"{prep_name}<br/>{prep_desig}", style_body), Paragraph(f"{conf_name}<br/>{conf_desig}", style_body)]
    ]
    sign_table = Table(sign_data, colWidths=[3.4 * inch, 3.4 * inch])
    sign_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(sign_table)

    if os.path.exists("footer.png"):
        story.append(Spacer(1, 8))
        story.append(Image("footer.png", width=6.8 * inch, height=0.65 * inch))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ========== STREAMLIT UI SETUP ==========
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Top Bar (Title + Right In-line Settings Button)
st.markdown("""
<div class="echo-topbar-wrapper">
 <h1 class="echo-title">Project <span>Echo</span></h1>
</div>
""", unsafe_allow_html=True)

# Right In-Line Settings Action Button (Positioned over Topbar)
topbar_cols = st.columns([0.94, 0.06])
with topbar_cols[1]:
    if st.button("⚙️", key="topbar_settings_btn", help="Open Engine & Regeneration Settings"):
        st.session_state["show_settings"] = not st.session_state["show_settings"]
        st.rerun()

# Top Settings Drawer
if st.session_state["show_settings"]:
    with st.container(border=True):
        st.markdown('<h3>Engine Configuration & Usage Diagnostics</h3>', unsafe_allow_html=True)
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

# ---- Compact Details & Audio (Blank Defaults) ----
with st.container(border=True):
    st.markdown('<h3>Meeting Details & Audio</h3>', unsafe_allow_html=True)
    
    # ROW 1
    r1_c1, r1_c2, r1_c3, r1_c4, r1_c5, r1_c6 = st.columns([1.3, 2.0, 1.1, 1.1, 1.5, 1.5])
    with r1_c1: meeting_date = st.date_input("Date", value=datetime.date(2026, 8, 25))
    with r1_c2: meeting_location = st.text_input("Location", value="", placeholder="e.g. Boardroom")
    with r1_c3: start_time = st.selectbox("Start", options=TIME_OPTIONS, index=0)
    with r1_c4: end_time = st.selectbox("End", options=TIME_OPTIONS, index=0)
    with r1_c5: prep_name = st.text_input("Prepared By (Name)", value="", placeholder="e.g. John Doe")
    with r1_c6: prep_desig = st.text_input("Designation", value="", placeholder="e.g. Associate")

    # ROW 2
    r2_c1, r2_c2, r2_c3, r2_c4, r2_c5 = st.columns([1.5, 2.0, 2.0, 1.5, 1.5])
    with r2_c1: client_name = st.text_input("Client / Company", value="", placeholder="XYZ Company")
    with r2_c2: selected_crd = st.multiselect("CRD Team Attendees", options=CRD_MEMBERS, default=[])
    with r2_c3: ext_attendees_raw = st.text_input("External Attendees", value="", placeholder="e.g. Mr. ABCD, Jane Doe")
    with r2_c4: conf_name = st.text_input("Confirmed By (Name)", value="", placeholder="e.g. Client Rep")
    with r2_c5: conf_desig = st.text_input("Designation", value="", placeholder="e.g. Managing Director")

    # Three Tabs
    tab_upload, tab_record, tab_text = st.tabs(["Upload Audio", "Record Audio", "Upload Text"])

    with tab_upload:
        u_col1, u_col2 = st.columns([5, 1.5])
        with u_col1:
            uploaded_file = st.file_uploader(
                "Upload audio file (200MB limit supported)",
                type=["wav", "mp3", "m4a", "ogg", "flac", "mp4", "webm"],
                help="Audio uploads up to 200MB are supported."
            )
        if uploaded_file:
            with u_col2:
                st.write("")
                st.write("")
                if st.button("Transcribe Audio", key="btn_tx_upload"):
                    loading_placeholder = st.empty()
                    transcript = transcribe_audio_pipeline(uploaded_file.read(), uploaded_file.name, loading_placeholder)
                    loading_placeholder.empty()
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
                st.download_button(label="Save Recording (.wav)", data=rec_bytes, file_name=f"Recording_{meeting_date.strftime('%Y%m%d')}.wav", mime="audio/wav")
            with r_col3:
                if st.button("Transcribe Audio", key="btn_tx_record"):
                    loading_placeholder = st.empty()
                    transcript = transcribe_audio_pipeline(rec_bytes, "recording.wav", loading_placeholder)
                    loading_placeholder.empty()
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
                loading_placeholder = st.empty()
                loading_placeholder.markdown(f'<div class="loading-banner">{SVG_SPINNER} <span>Extracting document text...</span></div>', unsafe_allow_html=True)
                
                extracted_str = ""
                if uploaded_text_file:
                    extracted_str = extract_text_from_file(uploaded_text_file)
                if pasted_text and pasted_text.strip():
                    extracted_str += "\n" + pasted_text.strip()
                
                loading_placeholder.empty()
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

        # Build formatted time range only if provided
        time_range_str = f"{start_time} to {end_time}" if (start_time and end_time) else (start_time or end_time or "")

        meeting_details = {
            "date": meeting_date.strftime("%B %d, %Y"),
            "time_range": time_range_str,
            "location": meeting_location if meeting_location.strip() else "____________",
            "company_name": client_name.strip() if client_name.strip() else "",
            "prime_attendees": selected_crd,
            "external_attendees": [x.strip() for x in ext_attendees_raw.split(",") if x.strip()],
            "prep_name": prep_name.strip(),
            "prep_desig": prep_desig.strip(),
            "conf_name": conf_name.strip(),
            "conf_desig": conf_desig.strip()
        }

        # Dual Export Section (Word DOCX and PDF)
        exp_col1, exp_col2 = st.columns(2)
        
        with exp_col1:
            doc_bio = export_to_word(
                st.session_state["df"],
                meeting_details,
                st.session_state["other_discussions"]
            )
            st.download_button(
                label="Download Word Document (.docx)",
                data=doc_bio,
                file_name=f"MOM_{client_name.replace(' ', '_') if client_name else 'Report'}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="btn_download_docx"
            )

        with exp_col2:
            pdf_bio = export_to_pdf(
                st.session_state["df"],
                meeting_details,
                st.session_state["other_discussions"]
            )
            st.download_button(
                label="Download PDF Document (.pdf)",
                data=pdf_bio,
                file_name=f"MOM_{client_name.replace(' ', '_') if client_name else 'Report'}.pdf",
                mime="application/pdf",
                key="btn_download_pdf"
            )
