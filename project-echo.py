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
import streamlit.components.v1 as components

# ========== CONFIG ==========
st.set_page_config(page_title="Project Echo", layout="wide", initial_sidebar_state="collapsed")[cite: 1]

# --- PROGRAMMATIC LIGHT MODE & 200MB LIMIT ---
_config_dir = ".streamlit"[cite: 1]
_config_file = os.path.join(_config_dir, "config.toml")[cite: 1]
os.makedirs(_config_dir, exist_ok=True)[cite: 1]
with open(_config_file, "w", encoding="utf-8") as f:[cite: 1]
    f.write('[theme]\nbase="light"\n[server]\nmaxUploadSize = 200\n')[cite: 1]

# Simple Password Gate at the start of app execution (Read strictly from Streamlit Cloud Secrets)
if "authenticated" not in st.session_state:[cite: 1]
    st.session_state["authenticated"] = False[cite: 1]

if not st.session_state["authenticated"]:[cite: 1]
    pw_input = st.text_input("Enter Team Access Key to use Project Echo:", type="password")[cite: 1]
    if st.button("Log In"):[cite: 1]
        configured_password = str(st.secrets.get("APP_PASSWORD", "crd3ch0")).strip()
        if pw_input == configured_password:[cite: 1]
            st.session_state["authenticated"] = True[cite: 1]
            st.rerun()[cite: 1]
        else:
            st.error("Invalid access key. Contact the administrator.")[cite: 1]
    st.stop()  # Prevents unauthorized access to app functions[cite: 1]

# API Keys loaded strictly and securely from Streamlit Cloud Secrets (with whitespace stripping)
DEEPSEEK_API_KEY = str(st.secrets.get("DEEPSEEK_API_KEY", "")).strip()
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/chat/completions"[cite: 1]

GROQ_API_KEY = str(st.secrets.get("GROQ_API_KEY", "")).strip()
GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"[cite: 1]

OPENAI_API_KEY = str(st.secrets.get("OPENAI_API_KEY", "")).strip()
OPENAI_AUDIO_URL = "https://api.openai.com/v1/audio/transcriptions"[cite: 1]

# ========== DAILY AUDIO LIMIT & CHAT LIMIT CONFIG ==========
MAX_DAILY_AUDIO = 5
MAX_CHAT_QUERIES = 10
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

CRD_MEMBERS = [[cite: 1]
    "Sondi Tuazon",[cite: 1]
    "Kristina Balajadia",[cite: 1]
    "Meliza Zapata",[cite: 1]
    "Dykstra Pineda",[cite: 1]
    "Cedtrix Rena",[cite: 1]
    "Carlo Medina",[cite: 1]
    "Dave Policarpio",[cite: 1]
    "Irish Rima"[cite: 1]
][cite: 1]

LOCATION_PRESETS = [[cite: 1]
    "— Select a Preset (Optional) —",[cite: 1]
    "GreatWork Mega Tower 32F - Secret Room",[cite: 1]
    "GreatWork Mega Tower 32F - Small Meeting Room",[cite: 1]
    "GreatWork Mega Tower 24F - Meeting Room",[cite: 1]
    "GreatWork Mega Tower 32F - Board Room",[cite: 1]
    "GreatWork Mega Tower 32F - Co-working",[cite: 1]
    "Online Meeting"[cite: 1]
][cite: 1]

# Initialize Session State Variables
if "transcript" not in st.session_state: st.session_state["transcript"] = ""[cite: 1]
if "df" not in st.session_state: st.session_state["df"] = pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"])[cite: 1]
if "other_discussions" not in st.session_state: st.session_state["other_discussions"] = ""[cite: 1]
if "show_settings" not in st.session_state: st.session_state["show_settings"] = False[cite: 1]
if "tokens_used" not in st.session_state: st.session_state["tokens_used"] = 0[cite: 1]
if "last_api_call" not in st.session_state: st.session_state["last_api_call"] = None[cite: 1]
if "selected_engine" not in st.session_state: st.session_state["selected_engine"] = "AI - DeepSeek"[cite: 1]
if "chat_history" not in st.session_state: st.session_state["chat_history"] = []
if "chat_count" not in st.session_state: st.session_state["chat_count"] = 0

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

/* Small SVG-only Settings Icon Button in the Card Header */
div[data-testid="stButton"]:has(button[key="card_settings_btn"]) {
    display: flex !important;
    justify-content: flex-end !important;
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
    box-shadow: none !important;
}

button[key="card_settings_btn"]::before {
    content: "";
    display: inline-block;
    width: 17px;
    height: 17px;
    background-color: #C5A059;
    -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='3'%3E%3C/circle%3E%3Cpath d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z'%3E%3C/path%3E%3C/svg%3E") no-repeat center;
    mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='3'%3E%3C/circle%3E%3Cpath d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z'%3E%3C/path%3E%3C/svg%3E") no-repeat center;
    -webkit-mask-size: contain;
    mask-size: contain;
    transition: background-color 0.2s ease;
}

button[key="card_settings_btn"]:hover {
    background-color: #F8F5EE !important;
    border-color: #A07828 !important;
}

button[key="card_settings_btn"]:hover::before {
    background-color: #A07828 !important;
}

.stTextArea textarea {
    font-size: 0.95rem !important;[cite: 1]
    line-height: 1.6 !important;[cite: 1]
}

/* Time Picker Clean Layout */
[data-testid="column"] .stSelectbox {
    margin-bottom: 0 !important;[cite: 1]
}
</style>
"""

# ========== SVG ICONS ==========
SVG_ALERT = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#D4AF37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>"""[cite: 1]

# ========== CORE LOGIC ==========
def extract_text_from_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.txt'):[cite: 1]
            return uploaded_file.getvalue().decode("utf-8")[cite: 1]
        elif uploaded_file.name.endswith('.pdf'):[cite: 1]
            reader = PyPDF2.PdfReader(uploaded_file)[cite: 1]
            text = ""[cite: 1]
            for page in reader.pages:[cite: 1]
                text += page.extract_text() + "\n"[cite: 1]
            return text[cite: 1]
        elif uploaded_file.name.endswith('.docx'):[cite: 1]
            doc = Document(uploaded_file)[cite: 1]
            return "\n".join([para.text for para in doc.paragraphs])[cite: 1]
        return ""[cite: 1]
    except Exception as e:[cite: 1]
        st.error(f"Error reading file: {e}")[cite: 1]
        return ""[cite: 1]

def _call_openai_transcribe(audio_bytes, filename="audio.mp3"):
    if not OPENAI_API_KEY:[cite: 1]
        st.error("OpenAI API Key is missing. Please add it to your Streamlit Cloud Secrets.")[cite: 1]
        return None[cite: 1]
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}[cite: 1]
    files = {"file": (filename, audio_bytes), "model": (None, "gpt-4o-mini-transcribe"), "response_format": (None, "json")}[cite: 1]
    try:
        resp = requests.post(OPENAI_AUDIO_URL, headers=headers, files=files, timeout=180)[cite: 1]
        if resp.status_code == 200:[cite: 1]
            return resp.json().get("text", "")[cite: 1]
        st.error(f"OpenAI fallback error: {resp.text}")[cite: 1]
        return None[cite: 1]
    except Exception as e:[cite: 1]
        st.error(f"OpenAI connection error: {e}")[cite: 1]
        return None[cite: 1]

def _call_groq_whisper(audio_bytes, filename="audio.mp3"):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}[cite: 1]
    files = {"file": (filename, audio_bytes), "model": (None, "whisper-large-v3-turbo"), "response_format": (None, "json")}[cite: 1]
    try:
        resp = requests.post(GROQ_AUDIO_URL, headers=headers, files=files, timeout=60)[cite: 1]
        if resp.status_code == 200:[cite: 1]
            return resp.json().get("text", "")[cite: 1]
        return None[cite: 1]
    except:
        return None[cite: 1]

def transcribe_audio_pipeline(audio_bytes, original_filename, progress_bar, status_placeholder):
    progress_bar.progress(10, text="Preprocessing audio container (10%)...")[cite: 1]
    
    ext = os.path.splitext(original_filename)[1] or ".m4a"[cite: 1]
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as src:[cite: 1]
        src.write(audio_bytes)[cite: 1]
        src_path = src.name[cite: 1]

    compressed_mp3 = src_path + "_compressed.mp3"[cite: 1]
    progress_bar.progress(25, text="Compressing audio to 16kHz Mono 24k MP3 (25%)...")[cite: 1]

    try:
        cmd = [[cite: 1]
            "ffmpeg", "-y",[cite: 1]
            "-threads", "1",[cite: 1]
            "-i", src_path,[cite: 1]
            "-vn",[cite: 1]
            "-ac", "1",[cite: 1]
            "-ar", "16000",[cite: 1]
            "-c:a", "libmp3lame",[cite: 1]
            "-b:a", "24k",[cite: 1]
            compressed_mp3[cite: 1]
        ][cite: 1]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)[cite: 1]
        if res.returncode != 0:[cite: 1]
            st.error(f"FFmpeg compression error: {res.stderr[:200]}")[cite: 1]
            return None[cite: 1]

        comp_size_mb = os.path.getsize(compressed_mp3) / (1024 * 1024)[cite: 1]
        progress_bar.progress(45, text="Evaluating audio duration & routing (45%)...")[cite: 1]

        if comp_size_mb <= 10.0 and GROQ_API_KEY:[cite: 1]
            status_placeholder.info("Processing via Groq Whisper Primary...")[cite: 1]
            progress_bar.progress(70, text="Transcribing via Groq Whisper (70%)...")[cite: 1]
            with open(compressed_mp3, "rb") as f:[cite: 1]
                c_bytes = f.read()[cite: 1]
            text = _call_groq_whisper(c_bytes, "audio.mp3")[cite: 1]
            if text:[cite: 1]
                progress_bar.progress(100, text="Transcription completed (100%)!")[cite: 1]
                status_placeholder.empty()[cite: 1]
                increment_daily_audio_count()
                return text[cite: 1]
            status_placeholder.warning("Notice: Groq rate limit reached. Switching automatically to OpenAI...")[cite: 1]

        status_placeholder.info("Processing recording via OpenAI...")[cite: 1]
        progress_bar.progress(55, text="Preparing audio segments for OpenAI (55%)...")[cite: 1]
        
        segment_pattern = src_path + "_seg_%03d.mp3"[cite: 1]
        subprocess.run([[cite: 1]
            "ffmpeg", "-y", "-i", compressed_mp3,[cite: 1]
            "-f", "segment", "-segment_time", "600", "-c", "copy",[cite: 1]
            segment_pattern[cite: 1]
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)[cite: 1]

        seg_dir = os.path.dirname(src_path)[cite: 1]
        base_name = os.path.basename(src_path) + "_seg_"[cite: 1]
        segments = sorted([os.path.join(seg_dir, f) for f in os.listdir(seg_dir) if f.startswith(base_name)])[cite: 1]

        full_transcript = [][cite: 1]
        total_segs = len(segments)[cite: 1]
        
        for idx, seg in enumerate(segments):[cite: 1]
            pct = int(55 + ((idx + 1) / total_segs) * 40)[cite: 1]
            progress_bar.progress(pct, text=f"Transcribing segment {idx + 1} of {total_segs} ({pct}%)...")[cite: 1]
            
            with open(seg, "rb") as f:[cite: 1]
                seg_bytes = f.read()[cite: 1]
            t = _call_openai_transcribe(seg_bytes, f"part_{idx}.mp3")[cite: 1]
            if t:[cite: 1]
                full_transcript.append(t)[cite: 1]
            time.sleep(0.2)[cite: 1]
            try: os.remove(seg)[cite: 1]
            except: pass[cite: 1]

        progress_bar.progress(100, text="Transcription completed successfully (100%)!")[cite: 1]
        time.sleep(0.3)[cite: 1]
        status_placeholder.empty()[cite: 1]
        increment_daily_audio_count()
        return " ".join(full_transcript)[cite: 1]

    except Exception as e:[cite: 1]
        st.error(f"Audio processing failure: {e}")[cite: 1]
        return None[cite: 1]
    finally:
        if os.path.exists(src_path):[cite: 1]
            try: os.remove(src_path)[cite: 1]
            except: pass[cite: 1]
        if os.path.exists(compressed_mp3):[cite: 1]
            try: os.remove(compressed_mp3)[cite: 1]
            except: pass[cite: 1]

def normalize_llm_json_to_df(data):
    items = None[cite: 1]
    other_disc = ""[cite: 1]
    
    if isinstance(data, list):[cite: 1]
        items = data[cite: 1]
    elif isinstance(data, dict):[cite: 1]
        for key in ["table_items", "items", "minutes", "table", "data", "discussion_items", "discussions", "action_items"]:[cite: 1]
            if key in data and isinstance(data[key], list) and len(data[key]) > 0:[cite: 1]
                items = data[key][cite: 1]
                break[cite: 1]
        if items is None:[cite: 1]
            for v in data.values():[cite: 1]
                if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):[cite: 1]
                    items = v[cite: 1]
                    break[cite: 1]
            if items is None:[cite: 1]
                items = [data][cite: 1]
                
        other_disc = str(data.get("other_discussions", "") or data.get("notes", "") or data.get("summary", ""))[cite: 1]

    if not items or not isinstance(items, list):[cite: 1]
        return None, ""[cite: 1]

    df = pd.DataFrame(items)[cite: 1]
    col_mapping = {}[cite: 1]
    for c in df.columns:[cite: 1]
        c_clean = str(c).lower().replace("_", " ").replace("-", " ")[cite: 1]
        if any(k in c_clean for k in ["discuss", "point", "topic", "milestone"]):[cite: 1]
            col_mapping[c] = "Discussion Points"[cite: 1]
        elif any(k in c_clean for k in ["action", "plan", "step", "deliverable"]):[cite: 1]
            col_mapping[c] = "Action Plan"[cite: 1]
        elif any(k in c_clean for k in ["date", "time", "delivery", "deadline"]):[cite: 1]
            col_mapping[c] = "Indicative Delivery Date"[cite: 1]
        elif any(k in c_clean for k in ["person", "charge", "pic", "assign", "who", "responsible"]):[cite: 1]
            col_mapping[c] = "Person-in-charge"[cite: 1]

    df = df.rename(columns=col_mapping)[cite: 1]
    for col in ["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]:[cite: 1]
        if col not in df.columns:[cite: 1]
            df[col] = ""[cite: 1]
            
    df = df[["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]].drop_duplicates()[cite: 1]
    return df, other_disc[cite: 1]

def extract_with_deepseek(transcript):
    if not DEEPSEEK_API_KEY:[cite: 1]
        st.error("DeepSeek API Key is missing. Please add it to your Streamlit Cloud Dashboard Secrets.")
        return None, ""[cite: 1]

    headers = {[cite: 1]
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",[cite: 1]
        "Content-Type": "application/json"[cite: 1]
    }[cite: 1]

    system_prompt = ([cite: 1]
        "You are an expert executive assistant for PRIME Philippines tasked with producing comprehensive, "[cite: 1]
        "high-level executive Minutes of the Meeting (MOM). "[cite: 1]
        "The transcript contains Tagalog, English, and Taglish dialogue. "[cite: 1]
        "Analyze the full conversation context and translate all colloquial, informal, and mixed-language statements "[cite: 1]
        "into polished, high-level corporate English. "[cite: 1]
        "Synthesize all key agreements, status reports, core discussion points, definitive action plans, "[cite: 1]
        "indicative delivery timelines, and assigned persons-in-charge without omitting critical business context. "[cite: 1]
        "Output valid JSON only matching the exact schema provided."[cite: 1]
    )[cite: 1]

    user_prompt = f"""Synthesize the following meeting transcript into formal, high-level Minutes of Meeting (MOM) formatted as valid JSON:

Schema:
{{
  "table_items": [
    {{
      "Discussion Points": "Formal summary of key milestones, operational updates, or strategic topics discussed",
      "Action Plan": "Concrete, actionable executive deliverables and next steps (state 'None' if purely informational)",
      "Indicative Delivery Date": "Specific date, timeline, or 'TBD'",
      "Person-in-charge": "Designated individual, department (e.g., PRIME Philippines, Client name), or 'Unassigned'"
    }}
  ],
  "other_discussions": "High-level summary of peripheral discussions, informal remarks, or general alignment"
}}

Transcript:
{transcript[:28000]}"""[cite: 1]

    payload = {[cite: 1]
        "model": "deepseek-chat",[cite: 1]
        "messages": [[cite: 1]
            {"role": "system", "content": system_prompt},[cite: 1]
            {"role": "user", "content": user_prompt}[cite: 1]
        ],[cite: 1]
        "response_format": {"type": "json_object"},[cite: 1]
        "temperature": 0.1,[cite: 1]
        "max_tokens": 1800[cite: 1]
    }[cite: 1]

    try:
        resp = requests.post(DEEPSEEK_CHAT_URL, headers=headers, json=payload, timeout=120)[cite: 1]
        if resp.status_code == 200:[cite: 1]
            res_json = resp.json()[cite: 1]
            usage = res_json.get("usage", {})[cite: 1]
            st.session_state["tokens_used"] += usage.get("total_tokens", len(transcript) // 4)[cite: 1]
            st.session_state["last_api_call"] = datetime.datetime.now()[cite: 1]

            raw_text = res_json["choices"][0]["message"]["content"].strip()[cite: 1]
            clean_text = re.sub(r"^```(?:json)?\s*", "", raw_text)[cite: 1]
            clean_text = re.sub(r"\s*
