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
from concurrent.futures import ThreadPoolExecutor, as_completed
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
import streamlit.components.v1 as components

# ========== CONFIG ==========
st.set_page_config(page_title="Project Echo", layout="wide", initial_sidebar_state="collapsed")

# --- PROGRAMMATIC LIGHT MODE & 200MB LIMIT ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
os.makedirs(_config_dir, exist_ok=True)
with open(_config_file, "w", encoding="utf-8") as f:
    f.write('[theme]\nbase="light"\n[server]\nmaxUploadSize = 200\n')

# API Keys loaded strictly from Streamlit Cloud Secrets
DEEPSEEK_API_KEY = st.secrets.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/chat/completions"

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
OPENAI_AUDIO_URL = "https://api.openai.com/v1/audio/transcriptions"

# ========== DAILY AUDIO LIMIT CONFIGURATION ==========
MAX_DAILY_AUDIO = 5
USAGE_FILE = ".daily_audio_usage.json"

def get_daily_audio_count():
    today_str = datetime.date.today().isoformat()
    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, "r") as f:
                data = json.load(f)
                if data.get("date") == today_str:
                    return data.get("count", 0)
        except Exception:
            pass
    return 0

def increment_daily_audio_count():
    today_str = datetime.date.today().isoformat()
    current = get_daily_audio_count()
    try:
        with open(USAGE_FILE, "w") as f:
            json.dump({"date": today_str, "count": current + 1}, f)
    except Exception:
        pass

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

LOCATION_PRESETS = [
    "— Select a Preset (Optional) —",
    "GreatWork Mega Tower 32F - Secret Room",
    "GreatWork Mega Tower 32F - Small Meeting Room",
    "GreatWork Mega Tower 24F - Meeting Room",
    "GreatWork Mega Tower 32F - Board Room",
    "GreatWork Mega Tower 32F - Co-working",
    "Online Meeting"
]

# Initialize Session State Variables
if "transcript" not in st.session_state: st.session_state["transcript"] = ""
if "mom_items" not in st.session_state: st.session_state["mom_items"] = []
if "other_discussions" not in st.session_state: st.session_state["other_discussions"] = ""
if "show_settings" not in st.session_state: st.session_state["show_settings"] = False
if "tokens_used" not in st.session_state: st.session_state["tokens_used"] = 0
if "last_api_call" not in st.session_state: st.session_state["last_api_call"] = None
if "selected_engine" not in st.session_state: st.session_state["selected_engine"] = "AI - DeepSeek"
if "chat_messages" not in st.session_state: st.session_state["chat_messages"] = []

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

/* Fixed Topbar */
.echo-topbar-wrapper {
    position: fixed; top: 0; left: 0; right: 0; height: 60px;
    background-color: #161616;
    border-bottom: 1px solid #333333;
    z-index: 999990; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    display: flex; align-items: center; justify-content: flex-start;
    padding: 0 2rem;
}

.echo-title {
    font-family: 'Playfair Display', serif !important;
    font-style: italic !important; font-weight: 400 !important;
    font-size: 1.35rem !important; color: #FFFFFF !important; margin: 0 !important;
}
.echo-title span { color: #D4AF37 !important; }

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

/* Delete Item Button */
button[key^="del_item_"] {
    border-color: #d9534f !important;
    color: #d9534f !important;
    background: transparent !important;
}
button[key^="del_item_"]:hover {
    background: #d9534f !important;
    color: #ffffff !important;
}

button[key="card_settings_btn"] {
    background-color: transparent !important;
    border: 1px solid #C5A059 !important;
    border-radius: 50% !important;
    width: 32px !important;
    height: 32px !important;
    min-height: 32px !important;
    padding: 0 !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
}

.stTextArea textarea {
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
}
</style>
"""

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

def _transcribe_single_chunk(seg_info):
    idx, seg_path = seg_info
    try:
        with open(seg_path, "rb") as f:
            seg_bytes = f.read()

        if GROQ_API_KEY:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
            files = {"file": (f"chunk_{idx}.mp3", seg_bytes), "model": (None, "whisper-large-v3-turbo"), "response_format": (None, "json")}
            resp = requests.post(GROQ_AUDIO_URL, headers=headers, files=files, timeout=75)
            if resp.status_code == 200:
                return idx, resp.json().get("text", "")

        if OPENAI_API_KEY:
            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
            files = {"file": (f"chunk_{idx}.mp3", seg_bytes), "model": (None, "gpt-4o-mini-transcribe"), "response_format": (None, "json")}
            resp = requests.post(OPENAI_AUDIO_URL, headers=headers, files=files, timeout=120)
            if resp.status_code == 200:
                return idx, resp.json().get("text", "")
    except Exception:
        pass
    return idx, ""

def transcribe_audio_pipeline(audio_bytes, original_filename, progress_bar, status_placeholder):
    progress_bar.progress(10, text="Preprocessing audio container (10%)...")
    
    ext = os.path.splitext(original_filename)[1] or ".m4a"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as src:
        src.write(audio_bytes)
        src_path = src.name

    compressed_mp3 = src_path + "_compressed.mp3"
    progress_bar.progress(25, text="Compressing audio to 16kHz Mono MP3 (25%)...")

    try:
        cmd = [
            "ffmpeg", "-y", "-threads", "1", "-i", src_path,
            "-vn", "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame", "-b:a", "24k",
            compressed_mp3
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            st.error(f"FFmpeg compression error: {res.stderr[:200]}")
            return None

        comp_size_mb = os.path.getsize(compressed_mp3) / (1024 * 1024)

        if comp_size_mb <= 20.0:
            status_placeholder.info("⚡ Processing directly in single pass...")
            progress_bar.progress(70, text="Transcribing audio (70%)...")
            _, text = _transcribe_single_chunk((0, compressed_mp3))
            if text:
                progress_bar.progress(100, text="Transcription completed (100%)!")
                status_placeholder.empty()
                increment_daily_audio_count()
                return text

        # Parallel Chunking for large files (splits into 600-second / 10-min parts)
        status_placeholder.info("🚀 Splitting file into chunks & running parallel transcription workers...")
        progress_bar.progress(40, text="Chunking audio into 10-minute segments (40%)...")
        
        segment_pattern = src_path + "_seg_%03d.mp3"
        subprocess.run([
            "ffmpeg", "-y", "-i", compressed_mp3,
            "-f", "segment", "-segment_time", "600", "-c", "copy",
            segment_pattern
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        seg_dir = os.path.dirname(src_path)
        base_name = os.path.basename(src_path) + "_seg_"
        segments = sorted([os.path.join(seg_dir, f) for f in os.listdir(seg_dir) if f.startswith(base_name)])
        total_segs = len(segments)

        progress_bar.progress(55, text=f"Launching {min(5, total_segs)} parallel workers for {total_segs} chunks...")

        results = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_idx = {executor.submit(_transcribe_single_chunk, (idx, seg)): idx for idx, seg in enumerate(segments)}
            completed = 0
            for future in as_completed(future_to_idx):
                idx, text = future.result()
                results[idx] = text
                completed += 1
                pct = int(55 + (completed / total_segs) * 40)
                progress_bar.progress(pct, text=f"Completed chunk {completed}/{total_segs} ({pct}%)...")

        # Clean segment files
        for seg in segments:
            try: os.remove(seg)
            except: pass

        full_transcript = " ".join([results[i] for i in range(total_segs) if results.get(i)])
        progress_bar.progress(100, text="Parallel transcription completed (100%)!")
        time.sleep(0.3)
        status_placeholder.empty()
        increment_daily_audio_count()
        return full_transcript

    except Exception as e:
        st.error(f"Audio pipeline error: {e}")
        return None
    finally:
        for p in [src_path, compressed_mp3]:
            if os.path.exists(p):
                try: os.remove(p)
                except: pass

def parse_items_to_dict_list(data):
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
        return [], ""

    clean_items = []
    for it in items:
        clean_items.append({
            "Discussion Points": it.get("Discussion Points") or it.get("topic") or it.get("discussion") or "",
            "Action Plan": it.get("Action Plan") or it.get("action") or it.get("plan") or "None",
            "Indicative Delivery Date": it.get("Indicative Delivery Date") or it.get("date") or it.get("deadline") or "TBD",
            "Person-in-charge": it.get("Person-in-charge") or it.get("pic") or it.get("assigned") or "Unassigned"
        })
    return clean_items, other_disc

def extract_with_deepseek(transcript):
    if not DEEPSEEK_API_KEY:
        st.error("DeepSeek API Key is missing.")
        return [], ""

    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    system_prompt = (
        "You are an expert executive assistant for PRIME Philippines tasked with producing high-level Minutes of Meeting (MOM). "
        "The transcript contains Tagalog, English, and Taglish. Translate informal/colloquial speech into polished corporate English. "
        "Synthesize key agreements, status reports, discussion points, action plans, timelines, and PICs. Output valid JSON matching the schema."
    )
    user_prompt = f"""Synthesize this transcript into formal MOM JSON:
Schema:
{{
  "table_items": [
    {{
      "Discussion Points": "Summary of topic or discussion point",
      "Action Plan": "Actionable deliverable (or 'None')",
      "Indicative Delivery Date": "Specific date, timeline, or 'TBD'",
      "Person-in-charge": "Assigned entity or 'Unassigned'"
    }}
  ],
  "other_discussions": "Peripheral notes or alignments"
}}

Transcript:
{transcript[:28000]}"""

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 1800
    }

    try:
        resp = requests.post(DEEPSEEK_CHAT_URL, headers=headers, json=payload, timeout=120)
        if resp.status_code == 200:
            res_json = resp.json()
            st.session_state["tokens_used"] += res_json.get("usage", {}).get("total_tokens", 0)
            st.session_state["last_api_call"] = datetime.datetime.now()
            raw_text = res_json["choices"][0]["message"]["content"].strip()
            clean_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            clean_text = re.sub(r"\s*```$", "", clean_text).strip()
            match = re.search(r"\{.*\}", clean_text, re.DOTALL)
            data = json.loads(match.group(0)) if match else json.loads(clean_text)
            return parse_items_to_dict_list(data)
    except Exception as e:
        st.warning(f"DeepSeek connection error: {e}")
    return [], ""

def heuristic_non_ai_extraction(transcript):
    sentences = re.split(r'(?<=[.!?]) +', transcript)
    action_keywords = ['send', 'prepare', 'submit', 'update', 'review', 'check', 'email', 'kailangan', 'gagawin', 'provide']
    items = []
    for i in range(0, min(len(sentences), 15), 3):
        chunk = " ".join(sentences[i:i+3]).strip()
        if chunk:
            items.append({
                "Discussion Points": chunk[:120] + "...",
                "Action Plan": "Review transcript details",
                "Indicative Delivery Date": "TBD",
                "Person-in-charge": "Unassigned"
            })
    return items or [{"Discussion Points": "Meeting Overview", "Action Plan": "Review manually", "Indicative Delivery Date": "TBD", "Person-in-charge": "Unassigned"}], ""

def query_meeting_chatbot(transcript, messages):
    if not DEEPSEEK_API_KEY:
        return "DeepSeek API key not found in secrets."

    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    sys_content = (
        "You are an intelligent executive meeting assistant. Answer user queries strictly using the provided meeting transcript. "
        "Provide direct, concise, and accurate answers based on what was discussed, agreed upon, or assigned.\n\n"
        f"MEETING TRANSCRIPT:\n{transcript[:28000]}"
    )
    api_messages = [{"role": "system", "content": sys_content}]
    for m in messages:
        api_messages.append({"role": m["role"], "content": m["content"]})

    try:
        resp = requests.post(DEEPSEEK_CHAT_URL, headers=headers, json={"model": "deepseek-chat", "messages": api_messages, "temperature": 0.2}, timeout=60)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        return f"Chatbot error ({resp.status_code}): {resp.text}"
    except Exception as e:
        return f"Connection error: {e}"

def set_cell_shading(cell, color_hex):
    shd = parse_xml(f'<w:shd xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shd)

def export_to_word(items, meeting_details, other_discussions):
    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(0.4)
        section.bottom_margin = Inches(0.4)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("MINUTES OF THE MEETING")
    r_title.bold = True
    r_title.underline = True
    r_title.font.name = "Arial"

    primary_client_rep = meeting_details.get("external_attendees", ["CLIENT"])[0] if meeting_details.get("external_attendees") else "CLIENT"
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run(f"PRIME PHILIPPINES & {primary_client_rep.upper()}")
    r_sub.bold = True
    r_sub.font.name = "Arial"

    doc.add_paragraph(f"Date: {meeting_details.get('date')} {meeting_details.get('time_range', '')}")
    doc.add_paragraph(f"Location: {meeting_details.get('location')}")

    table = doc.add_table(rows=len(items)+1, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    headers = ["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = header
        set_cell_shading(cell, "FFFF00")

    for i, it in enumerate(items):
        cells = table.rows[i+1].cells
        cells[0].text = f"{i+1}. {it.get('Discussion Points', '')}"
        cells[1].text = str(it.get('Action Plan', ''))
        cells[2].text = str(it.get('Indicative Delivery Date', ''))
        cells[3].text = str(it.get('Person-in-charge', ''))

    if other_discussions.strip():
        doc.add_paragraph(f"\nOther Discussions:\n{other_discussions}")

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def export_to_pdf(items, meeting_details, other_discussions):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=0.6*inch, rightMargin=0.6*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()

    story.append(Paragraph("<u><b>MINUTES OF THE MEETING</b></u>", styles['Title']))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<b>Date:</b> {meeting_details.get('date')} {meeting_details.get('time_range', '')}", styles['Normal']))
    story.append(Paragraph(f"<b>Location:</b> {meeting_details.get('location')}", styles['Normal']))
    story.append(Spacer(1, 8))

    table_data = [[
        Paragraph("<b>Discussion Points</b>", styles['Normal']),
        Paragraph("<b>Action Plan</b>", styles['Normal']),
        Paragraph("<b>Indicative Delivery Date</b>", styles['Normal']),
        Paragraph("<b>Person-in-charge</b>", styles['Normal'])
    ]]
    for i, it in enumerate(items):
        table_data.append([
            Paragraph(f"{i+1}. {it.get('Discussion Points','')}", styles['Normal']),
            Paragraph(it.get('Action Plan',''), styles['Normal']),
            Paragraph(it.get('Indicative Delivery Date',''), styles['Normal']),
            Paragraph(it.get('Person-in-charge',''), styles['Normal'])
        ])

    t = Table(table_data, colWidths=[2.4*inch, 2.3*inch, 1.1*inch, 1.0*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#FFFF00')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'TOP')
    ]))
    story.append(t)
    if other_discussions.strip():
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"<b>Other Discussions:</b><br/>{other_discussions}", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ========== STREAMLIT UI SETUP ==========
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown("""<div class="echo-topbar-wrapper"><h1 class="echo-title">Project <span>Echo</span></h1></div>""", unsafe_allow_html=True)

daily_audio_used = get_daily_audio_count()
audio_quota_reached = daily_audio_used >= MAX_DAILY_AUDIO

# ---- Meeting Details Card ----
with st.container(border=True):
    head_col1, head_col2 = st.columns([9.3, 0.7])
    with head_col1:
        st.markdown('<h3>Meeting Details</h3>', unsafe_allow_html=True)
    with head_col2:
        if st.button("⚙️", key="card_settings_btn", help="Settings & Token Diagnostics"):
            st.session_state["show_settings"] = not st.session_state["show_settings"]
            st.rerun()

    if st.session_state["show_settings"]:
        with st.expander("Settings & Diagnostics", expanded=True):
            s1, s2 = st.columns(2)
            with s1:
                st.session_state["selected_engine"] = st.selectbox("MoM Engine", ["AI - DeepSeek", "Non-AI - Python Heuristic"])
            with s2:
                st.write(f"• **Audio Quota:** `{daily_audio_used} / {MAX_DAILY_AUDIO}` used")
                st.write(f"• **Tokens Processed:** `{st.session_state['tokens_used']:,}`")
        st.markdown("---")

    r1_c1, r1_c2, r1_c3, r1_c4 = st.columns([1.5, 2.0, 1.5, 1.5])
    with r1_c1: meeting_date = st.date_input("Date", value=datetime.date(2026, 8, 25))
    with r1_c2:
        loc_preset = st.selectbox("Preset Location", options=LOCATION_PRESETS, index=0)
        meeting_location = loc_preset if loc_preset != LOCATION_PRESETS[0] else "Meeting Room"
    with r1_c3: prep_name = st.text_input("Prepared By", placeholder="e.g. John Doe")
    with r1_c4: client_name = st.text_input("Client / Company", placeholder="XYZ Company")

    tab_upload, tab_record, tab_text = st.tabs(["Upload Audio", "Record Audio", "Upload Text (Unlimited)"])

    with tab_upload:
        if audio_quota_reached:
            st.warning("Daily audio transcription limit reached. Use Upload Text tab for unlimited use.")
        else:
            up_file = st.file_uploader("Upload audio file", type=["wav", "mp3", "m4a", "ogg", "flac", "mp4"])
            if up_file and st.button("Transcribe Audio (Parallel Powered)", key="btn_tx_upload"):
                p_bar, p_status = st.progress(0), st.empty()
                txt = transcribe_audio_pipeline(up_file.read(), up_file.name, p_bar, p_status)
                p_bar.empty(); p_status.empty()
                if txt:
                    st.session_state["transcript"] = txt
                    st.session_state["mom_items"] = []
                    st.rerun()

    with tab_record:
        if not audio_quota_reached:
            rec = st.audio_input("Record audio", label_visibility="collapsed")
            if rec and st.button("Transcribe Recording", key="btn_tx_rec"):
                p_bar, p_status = st.progress(0), st.empty()
                txt = transcribe_audio_pipeline(rec.read(), "recording.wav", p_bar, p_status)
                p_bar.empty(); p_status.empty()
                if txt:
                    st.session_state["transcript"] = txt
                    st.session_state["mom_items"] = []
                    st.rerun()

    with tab_text:
        doc_file = st.file_uploader("Upload Document", type=["txt", "docx", "pdf"])
        paste_txt = st.text_area("Or Paste Transcript", height=80)
        if st.button("Process Document / Text"):
            extracted = ""
            if doc_file: extracted = extract_text_from_file(doc_file)
            if paste_txt: extracted += "\n" + paste_txt
            if extracted.strip():
                st.session_state["transcript"] = extracted.strip()
                st.session_state["mom_items"] = []
                st.rerun()

# ---- Step 2: Full Transcript UI ----
if st.session_state["transcript"]:
    with st.container(border=True):
        st.markdown('<h3>Full Transcript</h3>', unsafe_allow_html=True)
        st.text_area("Transcript Content", st.session_state["transcript"], height=200, label_visibility="collapsed")
        
        if not st.session_state["mom_items"]:
            if st.button("Generate MOM Cards", key="btn_gen_mom"):
                if st.session_state["selected_engine"] == "AI - DeepSeek":
                    items, od = extract_with_deepseek(st.session_state["transcript"])
                else:
                    items, od = heuristic_non_ai_extraction(st.session_state["transcript"])
                st.session_state["mom_items"] = items
                st.session_state["other_discussions"] = od
                st.rerun()

# ---- Step 3: Card-by-Card MoM Item Editor ----
if st.session_state["mom_items"]:
    with st.container(border=True):
        st.markdown('<h3>Minutes of Meeting: Card Editor</h3>', unsafe_allow_html=True)
        st.caption("Each discussion point is laid out as an individual editable card below.")

        del_index = None
        for idx, item in enumerate(st.session_state["mom_items"]):
            with st.container(border=True):
                c_top1, c_top2 = st.columns([9, 1])
                with c_top1:
                    st.markdown(f"**Discussion Point #{idx+1}**")
                with c_top2:
                    if st.button("🗑️ Delete", key=f"del_item_{idx}"):
                        del_index = idx

                col1, col2 = st.columns([2, 1])
                with col1:
                    item["Discussion Points"] = st.text_area("Discussion Topic & Milestone", value=item.get("Discussion Points", ""), key=f"dp_{idx}", height=85)
                    item["Action Plan"] = st.text_area("Action Plan", value=item.get("Action Plan", ""), key=f"ap_{idx}", height=75)
                with col2:
                    item["Indicative Delivery Date"] = st.text_input("Delivery Date", value=item.get("Indicative Delivery Date", "TBD"), key=f"date_{idx}")
                    item["Person-in-charge"] = st.text_input("Person-in-charge", value=item.get("Person-in-charge", "Unassigned"), key=f"pic_{idx}")

        if del_index is not None:
            st.session_state["mom_items"].pop(del_index)
            st.rerun()

        if st.button("➕ Add New Discussion Item"):
            st.session_state["mom_items"].append({
                "Discussion Points": "",
                "Action Plan": "",
                "Indicative Delivery Date": "TBD",
                "Person-in-charge": "Unassigned"
            })
            st.rerun()

        st.session_state["other_discussions"] = st.text_area("Other Discussions", value=st.session_state["other_discussions"], height=80)

        # Export Controls
        m_details = {
            "date": meeting_date.strftime("%B %d, %Y"),
            "location": meeting_location,
            "company_name": client_name,
            "prep_name": prep_name
        }
        exp1, exp2 = st.columns(2)
        with exp1:
            docx_b = export_to_word(st.session_state["mom_items"], m_details, st.session_state["other_discussions"])
            st.download_button("Download Word Document (.docx)", data=docx_b, file_name="MOM.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with exp2:
            pdf_b = export_to_pdf(st.session_state["mom_items"], m_details, st.session_state["other_discussions"])
            st.download_button("Download PDF Document (.pdf)", data=pdf_b, file_name="MOM.pdf", mime="application/pdf")

# ---- Step 4: AI Meeting Q&A Chatbot ----
if st.session_state["transcript"]:
    with st.container(border=True):
        st.markdown('<h3>💬 Ask Questions About This Meeting</h3>', unsafe_allow_html=True)
        st.caption("Ask questions about deliverables, attendee comments, deadlines, or specific points mentioned in the recording.")

        for msg in st.session_state["chat_messages"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if user_prompt := st.chat_input("e.g., What were the agreed deadlines for the marketing deck?"):
            st.session_state["chat_messages"].append({"role": "user", "content": user_prompt})
            with st.chat_message("user"):
                st.markdown(user_prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analyzing transcript..."):
                    reply = query_meeting_chatbot(st.session_state["transcript"], st.session_state["chat_messages"])
                    st.markdown(reply)
                    st.session_state["chat_messages"].append({"role": "assistant", "content": reply})
