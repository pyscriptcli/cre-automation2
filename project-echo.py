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
from concurrent.futures import ThreadPoolExecutor, as_completed

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
if "df" not in st.session_state: st.session_state["df"] = pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"])
if "other_discussions" not in st.session_state: st.session_state["other_discussions"] = ""
if "show_settings" not in st.session_state: st.session_state["show_settings"] = False
if "tokens_used" not in st.session_state: st.session_state["tokens_used"] = 0
if "last_api_call" not in st.session_state: st.session_state["last_api_call"] = None
if "selected_engine" not in st.session_state: st.session_state["selected_engine"] = "AI - DeepSeek"
if "chat_history" not in st.session_state: st.session_state["chat_history"] = []

# ========== SVG ICONS ==========
SVG_ALERT = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#D4AF37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>"""
SVG_CHECK = """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#D4AF37" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-left: 6px;"><polyline points="20 6 9 17 4 12"></polyline></svg>"""
SVG_INFO = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1A2B4C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>"""

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
    -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='3'%3E%3C/circle%3E%3Cpath d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l-.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z'%3E%3C/path%3E%3C/svg%3E") no-repeat center;
    mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='3'%3E%3C/circle%3E%3Cpath d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l-.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z'%3E%3C/path%3E%3C/svg%3E") no-repeat center;
    -webkit-mask-size: contain;
    mask-size: contain;
    transition: background-color 0.2s ease;
}

.stTextArea textarea {
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
}

[data-testid="column"] .stSelectbox {
    margin-bottom: 0 !important;
}
</style>
"""

# ========== CORE LOGIC ==========
def extract_text_from_file(uploaded_file):
    try:
        uploaded_file.seek(0)
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

def _call_openai_transcribe(audio_bytes, filename="audio.mp3"):
    if not OPENAI_API_KEY:
        st.error("OpenAI API Key is missing. Please add it to your Streamlit Cloud Secrets.")
        return None
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    files = {"file": (filename, audio_bytes, "audio/mpeg")}
    data = {"model": "whisper-1", "response_format": "json"}
    try:
        resp = requests.post(OPENAI_AUDIO_URL, headers=headers, files=files, data=data, timeout=180)
        if resp.status_code == 200:
            return resp.json().get("text", "")
        st.error(f"OpenAI transcription error ({resp.status_code}): {resp.text}")
        return None
    except Exception as e:
        st.error(f"OpenAI connection error: {e}")
        return None

def _call_groq_whisper(audio_bytes, filename="audio.mp3"):
    if not GROQ_API_KEY:
        return None
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {"file": (filename, audio_bytes, "audio/mpeg")}
    data = {"model": "whisper-large-v3-turbo", "response_format": "json"}
    try:
        resp = requests.post(GROQ_AUDIO_URL, headers=headers, files=files, data=data, timeout=60)
        if resp.status_code == 200:
            return resp.json().get("text", "")
        return None
    except Exception:
        return None

def _transcribe_single_segment_task(idx, seg_path):
    try:
        with open(seg_path, "rb") as f:
            seg_bytes = f.read()
        res = _call_openai_transcribe(seg_bytes, f"part_{idx}.mp3")
        return idx, res or ""
    finally:
        if os.path.exists(seg_path):
            try: os.remove(seg_path)
            except: pass

def check_ffmpeg_available():
    try:
        res = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return res.returncode == 0
    except Exception:
        return False

def transcribe_audio_pipeline(audio_bytes, original_filename, progress_bar, status_placeholder):
    if not audio_bytes or len(audio_bytes) == 0:
        st.error("Audio data is empty. Please check the file and try again.")
        return None

    raw_size_mb = len(audio_bytes) / (1024 * 1024)
    ffmpeg_available = check_ffmpeg_available()

    # Fast path: Under 25MB without requiring ffmpeg compression
    if raw_size_mb <= 24.0:
        progress_bar.progress(30, text="Evaluating transcription engine (30%)...")
        
        # Primary: Groq Whisper
        if GROQ_API_KEY:
            status_placeholder.markdown(f"{SVG_INFO} Routing via Groq Whisper Primary...", unsafe_allow_html=True)
            progress_bar.progress(60, text="Transcribing via Groq Whisper (60%)...")
            text = _call_groq_whisper(audio_bytes, original_filename)
            if text and text.strip():
                progress_bar.progress(100, text="Transcription completed (100%).")
                status_placeholder.empty()
                return text.strip()
            status_placeholder.markdown(f"{SVG_ALERT} Groq unavailable. Falling back to OpenAI...", unsafe_allow_html=True)

        # Fallback: OpenAI Direct
        if OPENAI_API_KEY:
            status_placeholder.markdown(f"{SVG_INFO} Transcribing via OpenAI...", unsafe_allow_html=True)
            progress_bar.progress(70, text="Transcribing via OpenAI (70%)...")
            text = _call_openai_transcribe(audio_bytes, original_filename)
            if text and text.strip():
                progress_bar.progress(100, text="Transcription completed (100%).")
                status_placeholder.empty()
                return text.strip()
            return None
        else:
            st.error("Both Groq and OpenAI API keys are missing or invalid in st.secrets.")
            return None

    # Heavy path: Files > 25MB requiring compression / chunking
    if not ffmpeg_available:
        st.error(f"File size is {raw_size_mb:.1f}MB, which exceeds the 25MB API limit, and 'ffmpeg' is not installed on this system. Please upload a smaller audio file or install ffmpeg.")
        return None

    progress_bar.progress(10, text="Preprocessing audio container (10%)...")
    ext = os.path.splitext(original_filename)[1] or ".m4a"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as src:
        src.write(audio_bytes)
        src_path = src.name

    compressed_mp3 = src_path + "_compressed.mp3"
    progress_bar.progress(25, text="Compressing audio to 16kHz Mono MP3 (25%)...")

    try:
        cmd = [
            "ffmpeg", "-y", "-threads", "1",
            "-i", src_path, "-vn", "-ac", "1", "-ar", "16000",
            "-c:a", "libmp3lame", "-b:a", "24k", compressed_mp3
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            st.error(f"FFmpeg compression failed: {res.stderr[:200]}")
            return None

        comp_size_mb = os.path.getsize(compressed_mp3) / (1024 * 1024)

        if comp_size_mb <= 24.0 and GROQ_API_KEY:
            status_placeholder.markdown(f"{SVG_INFO} Transcribing compressed audio via Groq Whisper...", unsafe_allow_html=True)
            progress_bar.progress(70, text="Transcribing via Groq Whisper (70%)...")
            with open(compressed_mp3, "rb") as f:
                c_bytes = f.read()
            text = _call_groq_whisper(c_bytes, "audio.mp3")
            if text and text.strip():
                progress_bar.progress(100, text="Transcription completed (100%).")
                status_placeholder.empty()
                return text.strip()

        # Chunk and transcribe in parallel
        status_placeholder.markdown(f"{SVG_INFO} Chunking and transcribing in parallel via OpenAI...", unsafe_allow_html=True)
        progress_bar.progress(55, text="Chunking audio segments for parallel processing (55%)...")
        
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
        if total_segs == 0:
            st.error("Failed to generate audio segments.")
            return None

        transcript_parts = [None] * total_segs
        completed_count = 0
        max_workers = min(5, total_segs)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {
                executor.submit(_transcribe_single_segment_task, idx, seg): idx
                for idx, seg in enumerate(segments)
            }
            for future in as_completed(future_to_idx):
                idx, segment_transcript = future.result()
                transcript_parts[idx] = segment_transcript
                completed_count += 1
                pct = int(55 + (completed_count / total_segs) * 40)
                progress_bar.progress(pct, text=f"Transcribed {completed_count}/{total_segs} chunks ({pct}%)...")

        progress_bar.progress(100, text="Transcription completed successfully (100%).")
        time.sleep(0.3)
        status_placeholder.empty()
        full_res = " ".join([part for part in transcript_parts if part and part.strip()])
        return full_res.strip() if full_res else None

    except Exception as e:
        st.error(f"Audio processing failure: {e}")
        return None
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
            
    df = df[["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]].drop_duplicates().reset_index(drop=True)
    return df, other_disc

def extract_with_deepseek(transcript):
    if not DEEPSEEK_API_KEY:
        st.error("DeepSeek API Key is missing. Please add it to your Streamlit Cloud Secrets.")
        return None, ""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "You are an expert executive assistant for PRIME Philippines tasked with producing comprehensive, "
        "high-level executive Minutes of the Meeting (MOM). "
        "The transcript contains Tagalog, English, and Taglish dialogue. "
        "Analyze the full conversation context and translate all colloquial, informal, and mixed-language statements "
        "into polished, high-level corporate English. "
        "Synthesize all key agreements, status reports, core discussion points, definitive action plans, "
        "indicative delivery timelines, and assigned persons-in-charge without omitting critical business context. "
        "Output valid JSON only matching the exact schema provided."
    )

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
{transcript[:28000]}"""

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 1800
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
            
    df = df[["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]].reset_index(drop=True)
    other_text = "\n\n".join(other_discussions[:4])
    return df, other_text

def extract_structured_insights(transcript, engine="AI - DeepSeek"):
    progress_bar = st.progress(0, text="Initializing MOM extraction (0%)...")
    time.sleep(0.2)
    progress_bar.progress(40, text=f"Translating Taglish conversation & extracting with {engine} (40%)...")

    if engine == "Non-AI - Python Heuristic":
        time.sleep(0.5)
        res_df, res_other = heuristic_non_ai_extraction(transcript)
        progress_bar.progress(100, text="Extraction completed (100%).")
        time.sleep(0.2)
        progress_bar.empty()
        return res_df, res_other

    df, other = extract_with_deepseek(transcript)
    
    if df is not None and not df.empty:
        progress_bar.progress(100, text="Finalizing Minutes of the Meeting (100%).")
        time.sleep(0.3)
        progress_bar.empty()
        return df, other

    df_fb, other_fb = heuristic_non_ai_extraction(transcript)
    progress_bar.empty()
    st.markdown(f"{SVG_ALERT} AI completion request could not be completed. The table below was populated using offline Keyword Heuristics.", unsafe_allow_html=True)
    return df_fb, other_fb

def query_transcript_assistant(transcript, user_question, chat_history):
    if not DEEPSEEK_API_KEY:
        return "DeepSeek API Key is missing. Please add it to your Streamlit secrets to use the assistant."
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = (
        "You are an intelligent executive meeting assistant. "
        "Answer the user's questions accurately based ONLY on the provided meeting transcript. "
        "If something was not discussed or is unclear from the transcript, state that politely. "
        "Provide direct, professional, and well-structured answers."
    )
    
    messages = [{"role": "system", "content": f"{system_prompt}\n\nTRANSCRIPT:\n{transcript[:28000]}"}]
    for msg in chat_history[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_question})
    
    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 1000
    }
    
    try:
        resp = requests.post(DEEPSEEK_CHAT_URL, headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            res_json = resp.json()
            return res_json["choices"][0]["message"]["content"].strip()
        return f"Error ({resp.status_code}): {resp.text}"
    except Exception as e:
        return f"Connection error: {e}"

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
    table.autofit = False
    table.allow_autofit = False

    col_widths = [Inches(2.5), Inches(2.2), Inches(1.1), Inches(1.2)]

    headers = ["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.width = col_widths[i]
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
            cell.width = col_widths[c_idx]
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

# Top Bar Fixed Header
st.markdown("""
<div class="echo-topbar-wrapper">
 <h1 class="echo-title">Project <span>Echo</span></h1>
</div>
""", unsafe_allow_html=True)

# ---- Meeting Details Card ----
with st.container(border=True):
    head_col1, head_col2 = st.columns([9.3, 0.7])
    with head_col1:
        st.markdown('<h3>Meeting Details</h3>', unsafe_allow_html=True)
    with head_col2:
        if st.button("", key="card_settings_btn", help="Open MoM Generation Engine & Diagnostics"):
            st.session_state["show_settings"] = not st.session_state["show_settings"]
            st.rerun()

    # Settings Drawer
    if st.session_state["show_settings"]:
        with st.expander("Settings & Engine Diagnostics", expanded=True):
            set_col1, set_col2 = st.columns([1.5, 1.5])
            
            with set_col1:
                engine_options = [
                    "AI - DeepSeek",
                    "Non-AI - Python Heuristic"
                ]
                selected_eng = st.selectbox(
                    "MoM Generation Engine",
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
                st.markdown("**Diagnostics & Usage**")
                st.write(f"• **Session Tokens Processed:** `{st.session_state['tokens_used']:,}`")
                
                if st.session_state["last_api_call"]:
                    last_call = st.session_state["last_api_call"]
                    st.write(f"• **Last Request Time:** `{last_call.strftime('%I:%M:%S %p')}`")
                    st.write(f"• **Engine Status ({selected_eng}):** `Active & Ready`")
                else:
                    st.write("• **Engine Status:** `Ready`")
        st.markdown("---")
    
    # ROW 1
    r1_c1, r1_c2, r1_c3, r1_c4, r1_c5, r1_c6 = st.columns([1.2, 2.0, 1.6, 1.6, 1.2, 1.2])
    
    with r1_c1:
        meeting_date = st.date_input("Date", value=datetime.date.today())
    
    with r1_c2:
        loc_preset = st.selectbox("Location Preset", options=LOCATION_PRESETS, index=0)
        custom_loc = st.text_input("Location", value="", placeholder="e.g. Boardroom", label_visibility="collapsed")
        meeting_location = custom_loc.strip() if custom_loc.strip() else ("" if loc_preset == LOCATION_PRESETS[0] else loc_preset)

    with r1_c3:
        st.markdown("<p style='font-size:0.88rem; margin-bottom:0.2rem; color:#333; font-weight:500;'>Start Time</p>", unsafe_allow_html=True)
        sc1, sc2, sc3 = st.columns([1, 1, 1.3])
        sh = sc1.selectbox("SH", [f"{i:02d}" for i in range(1,13)], key="sh", label_visibility="collapsed")
        sm = sc2.selectbox("SM", [f"{i:02d}" for i in range(0,60,5)], key="sm", label_visibility="collapsed")
        sap = sc3.selectbox("SAP", ["AM", "PM"], key="sap", label_visibility="collapsed")
        start_str = f"{sh}:{sm} {sap}"

    with r1_c4:
        st.markdown("<p style='font-size:0.88rem; margin-bottom:0.2rem; color:#333; font-weight:500;'>End Time</p>", unsafe_allow_html=True)
        ec1, ec2, ec3 = st.columns([1, 1, 1.3])
        eh = ec1.selectbox("EH", [f"{i:02d}" for i in range(1,13)], key="eh", label_visibility="collapsed")
        em = ec2.selectbox("EM", [f"{i:02d}" for i in range(0,60,5)], key="em", label_visibility="collapsed")
        eap = ec3.selectbox("EAP", ["AM", "PM"], key="eap", label_visibility="collapsed")
        end_str = f"{eh}:{em} {eap}"

    with r1_c5:
        prep_name = st.text_input("Prepared By (Name)", value="", placeholder="e.g. John Doe")
    with r1_c6:
        prep_desig = st.text_input("Designation", value="", placeholder="e.g. Associate")

    # ROW 2
    r2_c1, r2_c2, r2_c3, r2_c4, r2_c5 = st.columns([1.5, 2.0, 2.0, 1.5, 1.5])
    with r2_c1: client_name = st.text_input("Client / Company", value="", placeholder="XYZ Company")
    with r2_c2: selected_crd = st.multiselect("CRD Team Attendees", options=CRD_MEMBERS, default=[])
    with r2_c3: ext_attendees_raw = st.text_input("External Attendees", value="", placeholder="e.g. Mr. ABCD, Jane Doe")
    with r2_c4: conf_name = st.text_input("Confirmed By (Name)", value="", placeholder="e.g. Client Rep")
    with r2_c5: conf_desig = st.text_input("Designation", value="", placeholder="e.g. Managing Director")

    # Three Tabs
    tab_upload, tab_record, tab_text = st.tabs(["Upload Audio", "Record Audio", "Upload Text"])

    # TAB 1: UPLOAD AUDIO
    with tab_upload:
        u_col1, u_col2 = st.columns([5, 1.5])
        with u_col1:
            uploaded_file = st.file_uploader(
                "Upload audio file (200MB limit supported)",
                type=["wav", "mp3", "m4a", "ogg", "flac", "mp4", "webm"],
                help="Audio uploads up to 200MB are supported."
            )
        with u_col2:
            st.write("")
            st.write("")
            if st.button("Transcribe Audio", key="btn_tx_upload"):
                if uploaded_file is not None:
                    file_bytes = uploaded_file.getvalue()
                    if file_bytes and len(file_bytes) > 0:
                        p_bar = st.progress(0, text="Initializing audio pipeline (0%)...")
                        p_status = st.empty()
                        transcript = transcribe_audio_pipeline(file_bytes, uploaded_file.name, p_bar, p_status)
                        p_bar.empty()
                        p_status.empty()
                        if transcript and transcript.strip():
                            st.session_state["transcript"] = transcript.strip()
                            st.session_state["df"] = pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"])
                            st.session_state["other_discussions"] = ""
                            st.session_state["chat_history"] = []
                            st.rerun()
                        else:
                            st.error("Transcription returned empty text. Please verify your audio file and API credentials.")
                    else:
                        st.warning("Uploaded file is empty. Please select a valid audio file.")
                else:
                    st.warning("Please select an audio file first.")

    # TAB 2: RECORD AUDIO
    with tab_record:
        r_col1, r_col2, r_col3 = st.columns([4, 1.5, 1.5])
        with r_col1:
            recorded_audio = st.audio_input("Record audio directly", label_visibility="collapsed")
        
        rec_bytes = recorded_audio.getvalue() if recorded_audio is not None else None

        with r_col2:
            if rec_bytes:
                st.download_button(label="Save Recording (.wav)", data=rec_bytes, file_name=f"Recording_{meeting_date.strftime('%Y%m%d')}.wav", mime="audio/wav")
            else:
                st.button("Save Recording (.wav)", disabled=True)
                
        with r_col3:
            if st.button("Transcribe Audio", key="btn_tx_record"):
                if rec_bytes and len(rec_bytes) > 0:
                    p_bar = st.progress(0, text="Initializing audio pipeline (0%)...")
                    p_status = st.empty()
                    transcript = transcribe_audio_pipeline(rec_bytes, "recording.wav", p_bar, p_status)
                    p_bar.empty()
                    p_status.empty()
                    if transcript and transcript.strip():
                        st.session_state["transcript"] = transcript.strip()
                        st.session_state["df"] = pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"])
                        st.session_state["other_discussions"] = ""
                        st.session_state["chat_history"] = []
                        st.rerun()
                    else:
                        st.error("Transcription returned empty text. Please record again.")
                else:
                    st.warning("Please record audio before initiating transcription.")

    # TAB 3: TEXT UPLOAD
    with tab_text:
        text_col1, text_col2 = st.columns([5, 1.5])
        with text_col1:
            uploaded_text_file = st.file_uploader("Upload Document (.txt, .docx, .pdf)", type=["txt", "docx", "pdf"])
            pasted_text = st.text_area("Or Paste Transcript Here", height=100, placeholder="Paste transcript text directly here...")
        with text_col2:
            st.write("") 
            st.write("") 
            if st.button("Process Text", key="btn_tx_text"):
                p_bar = st.progress(0, text="Extracting document text (0%)...")
                time.sleep(0.2)
                p_bar.progress(50, text="Reading document stream (50%)...")
                extracted_str = ""
                if uploaded_text_file:
                    extracted_str = extract_text_from_file(uploaded_text_file)
                if pasted_text and pasted_text.strip():
                    extracted_str += "\n" + pasted_text.strip()
                
                p_bar.progress(100, text="Document processed (100%).")
                time.sleep(0.2)
                p_bar.empty()
                if extracted_str.strip():
                    st.session_state["transcript"] = extracted_str.strip()
                    st.session_state["df"] = pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"])
                    st.session_state["other_discussions"] = ""
                    st.session_state["chat_history"] = []
                    st.rerun()
                else:
                    st.warning("Please upload a file or paste text to proceed.")

# ---- Step 2: Full Transcript UI ----
if st.session_state["transcript"]:
    with st.container(border=True):
        f_col1, f_col2, f_col3 = st.columns([7.6, 1.2, 1.2])
        with f_col1:
            st.markdown('<h3 style="margin-top:0.3rem;">Full Transcript</h3>', unsafe_allow_html=True)
            
        with f_col2:
            copy_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
            body {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Montserrat', sans-serif; }}
            button {{
                width: 100%;
                height: 41px;
                background-color: #222222;
                color: #FFFFFF;
                border: 1px solid #444444;
                border-radius: 50px;
                font-size: 15px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 0;
            }}
            button:hover {{
                border-color: #D4AF37;
                color: #D4AF37;
                background-color: #1A1A1A;
            }}
            </style>
            </head>
            <body>
                <button id="copy-btn">Copy Text</button>
                <script>
                document.getElementById("copy-btn").addEventListener("click", function() {{
                    navigator.clipboard.writeText({json.dumps(st.session_state["transcript"])}).then(function() {{
                        document.getElementById("copy-btn").innerHTML = 'Copied! {SVG_CHECK}';
                        setTimeout(() => document.getElementById("copy-btn").innerText = "Copy Text", 2000);
                    }});
                }});
                </script>
            </body>
            </html>
            """
            components.html(copy_html, height=41)
            
        with f_col3:
            st.download_button(
                label="Download Text",
                data=st.session_state["transcript"],
                file_name=f"Transcript_{meeting_date.strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )

        st.text_area("Transcript Content", st.session_state["transcript"], height=300, label_visibility="collapsed")
        
        if st.session_state["df"].empty:
            if st.button("Generate MOM", key="btn_gen_mom"):
                extracted_df, other_disc = extract_structured_insights(st.session_state["transcript"], st.session_state["selected_engine"])
                if not extracted_df.empty:
                    st.session_state["df"] = extracted_df
                    st.session_state["other_discussions"] = other_disc
                    st.rerun()

    # ---- Transcript Q&A Chatbot ----
    with st.container(border=True):
        st.markdown('<h3>Meeting Transcript Q&A Assistant</h3>', unsafe_allow_html=True)
        st.caption("Ask questions, check specific discussions, or clarify details from the meeting transcript.")
        
        for msg in st.session_state["chat_history"]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        user_query = st.chat_input("Ask a question about this meeting transcript...")
        if user_query:
            st.session_state["chat_history"].append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.write(user_query)
            
            with st.chat_message("assistant"):
                with st.spinner("Analyzing transcript..."):
                    bot_reply = query_transcript_assistant(
                        st.session_state["transcript"],
                        user_query,
                        st.session_state["chat_history"]
                    )
                    st.write(bot_reply)
            st.session_state["chat_history"].append({"role": "assistant", "content": bot_reply})

# ---- Step 3: Minutes of Meeting Card/Row-Based Editor ----
if not st.session_state["df"].empty:
    with st.container(border=True):
        st.markdown('<h3>Minutes of Meeting Editor</h3>', unsafe_allow_html=True)
        st.caption("Review and edit each discussion point, deliverable, target date, and assignee below.")

        records = st.session_state["df"].to_dict("records")
        updated_records = []
        item_to_delete = None

        for idx, row in enumerate(records):
            with st.container(border=True):
                r_top_left, r_top_right = st.columns([9, 1])
                with r_top_left:
                    st.markdown(f"**Discussion Item #{idx + 1}**")
                with r_top_right:
                    if st.button("Delete Item", key=f"del_{idx}", help="Remove this discussion item"):
                        item_to_delete = idx

                c1, c2 = st.columns([1.2, 1.2])
                with c1:
                    disc_val = st.text_area(
                        "Discussion Points",
                        value=str(row.get("Discussion Points", "")),
                        key=f"disc_{idx}",
                        height=100
                    )
                    act_val = st.text_area(
                        "Action Plan",
                        value=str(row.get("Action Plan", "")),
                        key=f"act_{idx}",
                        height=100
                    )
                with c2:
                    date_val = st.text_input(
                        "Indicative Delivery Date",
                        value=str(row.get("Indicative Delivery Date", "")),
                        key=f"date_{idx}"
                    )
                    pic_val = st.text_input(
                        "Person-in-charge",
                        value=str(row.get("Person-in-charge", "")),
                        key=f"pic_{idx}"
                    )

                updated_records.append({
                    "Discussion Points": disc_val,
                    "Action Plan": act_val,
                    "Indicative Delivery Date": date_val,
                    "Person-in-charge": pic_val
                })

        if item_to_delete is not None:
            updated_records.pop(item_to_delete)
            st.session_state["df"] = pd.DataFrame(updated_records)
            st.rerun()
        else:
            st.session_state["df"] = pd.DataFrame(updated_records)

        if st.button("Add New Discussion Item", key="btn_add_item"):
            new_row = pd.DataFrame([{
                "Discussion Points": "",
                "Action Plan": "",
                "Indicative Delivery Date": "TBD",
                "Person-in-charge": "Unassigned"
            }])
            st.session_state["df"] = pd.concat([st.session_state["df"], new_row], ignore_index=True)
            st.rerun()

        st.markdown("---")
        st.session_state["other_discussions"] = st.text_area("Other Discussions", value=st.session_state["other_discussions"], height=100)

        time_range_str = f"{start_str} to {end_str}"

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

        # Dual Export Section
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
