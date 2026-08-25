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
st.set_page_config(page_title="Project Echo", layout="wide", initial_sidebar_state="collapsed")

# --- PROGRAMMATIC LIGHT MODE & 200MB LIMIT ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
os.makedirs(_config_dir, exist_ok=True)
with open(_config_file, "w", encoding="utf-8") as f:
    f.write('[theme]\nbase="light"\n[server]\nmaxUploadSize = 200\n')

# Simple Password Gate at the start of app execution (Read strictly from Streamlit Cloud Secrets)
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    pw_input = st.text_input("Enter Team Access Key to use Project Echo:", type="password")
    if st.button("Log In"):
        configured_password = str(st.secrets.get("APP_PASSWORD", "crd3ch0")).strip()
        if pw_input == configured_password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Invalid access key. Contact the administrator.")
    st.stop()

# API Keys loaded strictly from Streamlit Cloud Secrets
DEEPSEEK_API_KEY = str(st.secrets.get("DEEPSEEK_API_KEY", "")).strip()
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/chat/completions"

GROQ_API_KEY = str(st.secrets.get("GROQ_API_KEY", "")).strip()
GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

OPENAI_API_KEY = str(st.secrets.get("OPENAI_API_KEY", "")).strip()
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
if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""
if "df" not in st.session_state:
    st.session_state["df"] = pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"])
if "other_discussions" not in st.session_state:
    st.session_state["other_discussions"] = ""
if "show_settings" not in st.session_state:
    st.session_state["show_settings"] = False
if "tokens_used" not in st.session_state:
    st.session_state["tokens_used"] = 0
if "last_api_call" not in st.session_state:
    st.session_state["last_api_call"] = None
if "selected_engine" not in st.session_state:
    st.session_state["selected_engine"] = "AI - DeepSeek"
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# ========== CUSTOM CSS ==========
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600&family=Playfair+Display:ital,wght@1,400;1,500;1,600&display=swap');

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

/* Playfair Display Styling for Labels & Tab Headers */
.playfair-label {
    font-family: 'Playfair Display', serif !important;
    font-style: italic !important;
    font-weight: 400 !important;
    color: #1A2B4C !important;
    font-size: 1.05rem !important;
    margin-bottom: 0.25rem !important;
    display: block;
}

button[data-baseweb="tab"] p {
    font-family: 'Playfair Display', serif !important;
    font-style: italic !important;
    font-weight: 400 !important;
    color: #1A2B4C !important;
    font-size: 1.05rem !important;
}

/* Strict Symmetrical Card Heights for Top Row */
div[data-testid="stVerticalBlockBorderWrapper"]:has(div.top-card-anchor) {
    min-height: 470px !important;
    height: 470px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
    background-color: #FFFFFF !important; 
    border-radius: 12px !important;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.04) !important;
    border: 1px solid rgba(0, 0, 0, 0.04) !important; 
    padding: 1.25rem !important; 
    margin-bottom: 1rem !important;
}

/* Strict Symmetrical Card Heights for Bottom Row */
div[data-testid="stVerticalBlockBorderWrapper"]:has(div.bottom-card-anchor) {
    min-height: 540px !important;
    height: 540px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    background-color: #FFFFFF !important; 
    border-radius: 12px !important;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.04) !important;
    border: 1px solid rgba(0, 0, 0, 0.04) !important; 
    padding: 1.25rem !important; 
    margin-bottom: 1rem !important;
}

/* Uniform Small Pill Buttons */
.stButton > button, .stDownloadButton > button {
    background-color: #222222 !important; 
    color: #FFFFFF !important;
    border: 1px solid #444444 !important; 
    border-radius: 50px !important; 
    font-family: 'Montserrat', sans-serif !important; 
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.5px; 
    padding: 0.35rem 1.1rem !important;
    min-height: 34px !important;
    height: 34px !important;
    transition: all 0.25s ease !important; 
    width: 100% !important;
}

.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: #D4AF37 !important; 
    color: #D4AF37 !important;
    background-color: #1A1A1A !important;
}

button[key^="del_"] {
    min-height: 32px !important;
    height: 32px !important;
    padding: 0.2rem 0.5rem !important;
    background-color: #F7F5F0 !important;
    color: #A03030 !important;
    border: 1px solid rgba(160, 48, 48, 0.25) !important;
}

button[key^="del_"]:hover {
    background-color: #A03030 !important;
    color: #FFFFFF !important;
    border-color: #A03030 !important;
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
    -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='3'%3E%3C/circle%3E%3Cpath d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l-.06-.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z'%3E%3C/path%3E%3C/svg%3E") no-repeat center;
    mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='3'%3E%3C/circle%3E%3Cpath d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l-.06-.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z'%3E%3C/path%3E%3C/svg%3E") no-repeat center;
    -webkit-mask-size: contain;
    mask-size: contain;
    transition: background-color 0.2s ease;
}

/* Auto-wrapping text inputs */
.stTextArea textarea {
    font-size: 0.92rem !important;
    line-height: 1.45 !important;
    border-radius: 8px !important;
}

/* Time Picker Clean Layout */
[data-testid="column"] .stSelectbox {
    margin-bottom: 0 !important;
}

/* Sophisticated, Mature & Minimalist Ask Echo Chat UI */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
    margin-top: 0.5rem;
    height: 380px;
    max-height: 380px;
    overflow-y: auto;
    padding-right: 0.35rem;
}

.chat-bubble-ai-wrap {
    display: flex;
    justify-content: flex-start;
    align-items: flex-start;
    gap: 0.5rem;
}

.chat-bubble-ai {
    background-color: #FAF9F5;
    color: #222222;
    padding: 0.85rem 1.1rem;
    border-radius: 4px 14px 14px 14px;
    max-width: 88%;
    font-size: 0.88rem;
    line-height: 1.55;
    border: 1px solid rgba(212, 175, 55, 0.35);
    box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}

.chat-bubble-ai .ai-header {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-weight: 600;
    color: #A07828;
    margin-bottom: 0.35rem;
}

.chat-bubble-user-wrap {
    display: flex;
    justify-content: flex-end;
}

.chat-bubble-user {
    background-color: #ECE8DD;
    color: #1A1A1A;
    padding: 0.65rem 1rem;
    border-radius: 14px 14px 4px 14px;
    max-width: 85%;
    font-size: 0.88rem;
    line-height: 1.45;
    border: 1px solid rgba(0,0,0,0.06);
}
</style>
"""

# ========== SVG ICONS ==========
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

def _call_openai_transcribe(audio_bytes, filename="audio.mp3"):
    if not OPENAI_API_KEY:
        st.error("OpenAI API Key is missing. Please add it to your Streamlit Cloud Secrets.")
        return None
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    files = {"file": (filename, audio_bytes), "model": (None, "gpt-4o-mini-transcribe"), "response_format": (None, "json")}
    try:
        resp = requests.post(OPENAI_AUDIO_URL, headers=headers, files=files, timeout=180)
        if resp.status_code == 200:
            return resp.json().get("text", "")
        st.error(f"OpenAI fallback error: {resp.text}")
        return None
    except Exception as e:
        st.error(f"OpenAI connection error: {e}")
        return None

def _call_groq_whisper(audio_bytes, filename="audio.mp3"):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {"file": (filename, audio_bytes), "model": (None, "whisper-large-v3-turbo"), "response_format": (None, "json")}
    try:
        resp = requests.post(GROQ_AUDIO_URL, headers=headers, files=files, timeout=60)
        if resp.status_code == 200:
            return resp.json().get("text", "")
        return None
    except:
        return None

def transcribe_audio_pipeline(audio_bytes, original_filename, progress_bar, status_placeholder):
    progress_bar.progress(10, text="Preprocessing audio container (10%)...")
    
    ext = os.path.splitext(original_filename)[1] or ".m4a"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as src:
        src.write(audio_bytes)
        src_path = src.name

    compressed_mp3 = src_path + "_compressed.mp3"
    progress_bar.progress(25, text="Compressing audio to 16kHz Mono 24k MP3 (25%)...")

    try:
        cmd = [
            "ffmpeg", "-y",
            "-threads", "1",
            "-i", src_path,
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "libmp3lame",
            "-b:a", "24k",
            compressed_mp3
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            st.error(f"FFmpeg compression error: {res.stderr[:200]}")
            return None

        comp_size_mb = os.path.getsize(compressed_mp3) / (1024 * 1024)
        progress_bar.progress(45, text="Evaluating audio duration & routing (45%)...")

        if comp_size_mb <= 10.0 and GROQ_API_KEY:
            status_placeholder.info("Processing via Groq Whisper Primary...")
            progress_bar.progress(70, text="Transcribing via Groq Whisper (70%)...")
            with open(compressed_mp3, "rb") as f:
                c_bytes = f.read()
            text = _call_groq_whisper(c_bytes, "audio.mp3")
            if text:
                progress_bar.progress(100, text="Transcription completed (100%)!")
                status_placeholder.empty()
                return text
            status_placeholder.warning("Groq rate limit reached. Switching automatically to OpenAI...")

        status_placeholder.info("Processing recording via OpenAI...")
        progress_bar.progress(55, text="Preparing audio segments for OpenAI (55%)...")
        
        segment_pattern = src_path + "_seg_%03d.mp3"
        subprocess.run([
            "ffmpeg", "-y", "-i", compressed_mp3,
            "-f", "segment", "-segment_time", "600", "-c", "copy",
            segment_pattern
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        seg_dir = os.path.dirname(src_path)
        base_name = os.path.basename(src_path) + "_seg_"
        segments = sorted([os.path.join(seg_dir, f) for f in os.listdir(seg_dir) if f.startswith(base_name)])

        full_transcript = []
        total_segs = len(segments)

        for idx, seg in enumerate(segments):
            pct = int(55 + ((idx + 1) / total_segs) * 40)
            progress_bar.progress(pct, text=f"Transcribing segment {idx + 1} of {total_segs} ({pct}%)...")
            
            with open(seg, "rb") as f:
                seg_bytes = f.read()
            t = _call_openai_transcribe(seg_bytes, f"part_{idx}.mp3")
            if t:
                full_transcript.append(t)
            time.sleep(0.2)
            try:
                os.remove(seg)
            except:
                pass

        progress_bar.progress(100, text="Transcription completed successfully (100%)!")
        time.sleep(0.3)
        status_placeholder.empty()
        return " ".join(full_transcript)

    except Exception as e:
        st.error(f"Audio processing failure: {e}")
        return None
    finally:
        if os.path.exists(src_path):
            try:
                os.remove(src_path)
            except:
                pass
        if os.path.exists(compressed_mp3):
            try:
                os.remove(compressed_mp3)
            except:
                pass

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
        if not chunk:
            continue
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

def extract_structured_insights(transcript, engine="AI - DeepSeek"):
    progress_bar = st.progress(0, text="Initializing MOM extraction (0%)...")
    time.sleep(0.2)
    progress_bar.progress(40, text=f"Translating Taglish conversation & extracting with {engine} (40%)...")

    if engine == "Non-AI - Python Heuristic":
        time.sleep(0.5)
        res_df, res_other = heuristic_non_ai_extraction(transcript)
        progress_bar.progress(100, text="Extraction completed (100%)!")
        time.sleep(0.2)
        progress_bar.empty()
        return res_df, res_other

    df, other = extract_with_deepseek(transcript)
    
    if df is not None and not df.empty:
        progress_bar.progress(100, text="Finalizing Minutes of the Meeting (100%)...")
        time.sleep(0.3)
        progress_bar.empty()
        return df, other

    df_fb, other_fb = heuristic_non_ai_extraction(transcript)
    progress_bar.empty()
    st.markdown(f"{SVG_ALERT} AI completion request could not be completed. The table below was populated using offline Keyword Heuristics.", unsafe_allow_html=True)
    return df_fb, other_fb

def ask_deepseek_question(transcript, question, chat_history):
    if not DEEPSEEK_API_KEY:
        return "DeepSeek API key is missing. Please check your configuration."

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "You are Ask Echo, an authentic, executive AI assistant for PRIME Philippines. "
        "Answer questions based accurately and concisely on the provided meeting transcript. "
        "Use subtle, clean Markdown with bullet points where appropriate. "
        "If a specific detail is not in the transcript, concisely state that it was not mentioned."
    )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": f"Transcript:\n{transcript[:22000]}\n\nQuestion: {question}"})

    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 600
    }

    try:
        resp = requests.post(DEEPSEEK_CHAT_URL, headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            res_json = resp.json()
            usage = res_json.get("usage", {})
            st.session_state["tokens_used"] += usage.get("total_tokens", 0)
            st.session_state["last_api_call"] = datetime.datetime.now()
            return res_json["choices"][0]["message"]["content"].strip()
        else:
            return f"Service notice ({resp.status_code}): {resp.text}"
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
    for r in p_date.runs:
        r.font.name = "Arial"
        r.font.size = Pt(10)

    p_loc = doc.add_paragraph(f"Location: {meeting_details.get('location', '____________')}")
    p_loc.paragraph_format.space_after = Pt(2)
    for r in p_loc.runs:
        r.font.name = "Arial"
        r.font.size = Pt(10)

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
            if not att.strip():
                continue
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
    for r in p_intro.runs:
        r.font.name = "Arial"
        r.font.size = Pt(9.5)

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
            if c_idx in [2, 3]:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
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
        for r in p_od.runs:
            r.font.name = "Arial"
            r.font.size = Pt(9.5)

    p_prep_label = doc.add_paragraph("Prepared by:")
    p_prep_label.paragraph_format.space_before = Pt(12)
    p_prep_label.paragraph_format.space_after = Pt(2)
    p_prep_label.runs[0].font.name = "Arial"
    p_prep_label.runs[0].font.bold = True
    p_prep_label.runs[0].font.size = Pt(9.5)

    p_prep_line = doc.add_paragraph("_______________________________")
    p_prep_line.paragraph_format.space_after = Pt(2)
    p_prep_line.runs[0].font.name = "Arial"

    prep_name = meeting_details.get("prep_name", "").strip() or "____________________"
    prep_desig = meeting_details.get("prep_desig", "").strip() or "PRIME Philippines"
    p_prep_info = doc.add_paragraph(f"{prep_name}\n{prep_desig}")
    p_prep_info.paragraph_format.space_after = Pt(12)
    for r in p_prep_info.runs:
        r.font.name = "Arial"
        r.font.size = Pt(9.5)

    p_conf_label = doc.add_paragraph("Confirmed by:")
    p_conf_label.paragraph_format.space_after = Pt(2)
    p_conf_label.runs[0].font.name = "Arial"
    p_conf_label.runs[0].font.bold = True
    p_conf_label.runs[0].font.size = Pt(9.5)

    p_conf_line = doc.add_paragraph("_______________________________")
    p_conf_line.paragraph_format.space_after = Pt(2)
    p_conf_line.runs[0].font.name = "Arial"

    conf_name = meeting_details.get("conf_name", "").strip() or (ext_atts[0] if ext_atts else "____________________")
    conf_desig = meeting_details.get("conf_desig", "").strip() or (meeting_details.get("company_name", "").strip() or "Client")
    p_conf_info = doc.add_paragraph(f"{conf_name}\n{conf_desig}")
    p_conf_info.paragraph_format.space_after = Pt(6)
    for r in p_conf_info.runs:
        r.font.name = "Arial"
        r.font.size = Pt(9.5)

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

# ---- TOP ROW: Symmetrical Fixed Containers (Upload Left, Meeting Details Right) ----
col_upload, col_details = st.columns(2)

# LEFT CONTAINER: Audio & Text Upload Section
with col_upload:
    with st.container(border=True):
        st.markdown('<div class="top-card-anchor" style="display:none;"></div>', unsafe_allow_html=True)
        st.markdown('<h3>Input & Transcription</h3>', unsafe_allow_html=True)
        
        tab_upload, tab_record, tab_text = st.tabs(["Upload Audio", "Record Audio", "Upload Text"])

        # TAB 1: UPLOAD AUDIO
        with tab_upload:
            uploaded_file = st.file_uploader(
                "Upload audio file (200MB limit supported)",
                type=["wav", "mp3", "m4a", "ogg", "flac", "mp4", "webm"],
                help="Audio uploads up to 200MB are supported."
            )
            if uploaded_file:
                st.write("")
                if st.button("Transcribe Audio", key="btn_tx_upload"):
                    p_bar = st.progress(0, text="Initializing audio pipeline (0%)...")
                    p_status = st.empty()
                    transcript = transcribe_audio_pipeline(uploaded_file.read(), uploaded_file.name, p_bar, p_status)
                    p_bar.empty()
                    p_status.empty()
                    if transcript:
                        st.session_state["transcript"] = transcript
                        st.session_state["df"] = pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"])
                        st.session_state["other_discussions"] = ""
                        st.session_state["chat_history"] = []
                        st.rerun()

        # TAB 2: RECORD AUDIO
        with tab_record:
            recorded_audio = st.audio_input("Record audio directly", label_visibility="collapsed")
            if recorded_audio:
                rec_bytes = recorded_audio.read()
                r_btn1, r_btn2 = st.columns(2)
                with r_btn1:
                    st.download_button(label="Save Recording (.wav)", data=rec_bytes, file_name=f"Recording_{datetime.date.today().strftime('%Y%m%d')}.wav", mime="audio/wav", use_container_width=True)
                with r_btn2:
                    if st.button("Transcribe Audio", key="btn_tx_record"):
                        p_bar = st.progress(0, text="Initializing audio pipeline (0%)...")
                        p_status = st.empty()
                        transcript = transcribe_audio_pipeline(rec_bytes, "recording.wav", p_bar, p_status)
                        p_bar.empty()
                        p_status.empty()
                        if transcript:
                            st.session_state["transcript"] = transcript
                            st.session_state["df"] = pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"])
                            st.session_state["other_discussions"] = ""
                            st.session_state["chat_history"] = []
                            st.rerun()

        # TAB 3: TEXT UPLOAD
        with tab_text:
            uploaded_text_file = st.file_uploader("Upload Document (.txt, .docx, .pdf)", type=["txt", "docx", "pdf"])
            pasted_text = st.text_area("Or Paste Transcript Here", height=95, placeholder="Paste transcript text directly here...")
            if st.button("Process Text", key="btn_tx_text"):
                p_bar = st.progress(0, text="Extracting document text (0%)...")
                time.sleep(0.2)
                p_bar.progress(50, text="Reading document stream (50%)...")
                extracted_str = ""
                if uploaded_text_file:
                    extracted_str = extract_text_from_file(uploaded_text_file)
                if pasted_text and pasted_text.strip():
                    extracted_str += "\n" + pasted_text.strip()
                
                p_bar.progress(100, text="Document processed (100%)!")
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

# RIGHT CONTAINER: Meeting Details Card
with col_details:
    with st.container(border=True):
        st.markdown('<div class="top-card-anchor" style="display:none;"></div>', unsafe_allow_html=True)
        head_col1, head_col2 = st.columns([9.0, 1.0])
        with head_col1:
            st.markdown('<h3>Meeting Details</h3>', unsafe_allow_html=True)
        with head_col2:
            if st.button("", key="card_settings_btn", help="Open MoM Generation Engine & Token Diagnostics"):
                st.session_state["show_settings"] = not st.session_state["show_settings"]
                st.rerun()

        # Settings Drawer
        if st.session_state["show_settings"]:
            with st.expander("Settings & Engine Diagnostics", expanded=True):
                set_col1, set_col2 = st.columns(2)
                with set_col1:
                    engine_options = ["AI - DeepSeek", "Non-AI - Python Heuristic"]
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
                    st.markdown("**Diagnostics**")
                    st.write(f"• **Session Tokens:** `{st.session_state['tokens_used']:,}`")
                    if st.session_state["last_api_call"]:
                        last_call = st.session_state["last_api_call"]
                        st.write(f"• **Last Call:** `{last_call.strftime('%I:%M:%S %p')}`")
                    st.write(f"• **Status:** `Active & Ready`")
            st.markdown("---")

        # Row 1: Date, Location Preset & Input
        r1_c1, r1_c2 = st.columns([1.2, 2.0])
        with r1_c1:
            meeting_date = st.date_input("Date", value=datetime.date(2026, 8, 25))
        with r1_c2:
            loc_preset = st.selectbox("Location Preset", options=LOCATION_PRESETS, index=0)
            custom_loc = st.text_input("Location", value="", placeholder="e.g. Boardroom", label_visibility="collapsed")
            meeting_location = custom_loc.strip() if custom_loc.strip() else ("" if loc_preset == LOCATION_PRESETS[0] else loc_preset)

        # Row 2: Time Pickers
        r2_c1, r2_c2 = st.columns(2)
        with r2_c1:
            st.markdown("<p style='font-size:0.85rem; margin-bottom:0.2rem; color:#333; font-weight:500;'>Start Time</p>", unsafe_allow_html=True)
            sc1, sc2, sc3 = st.columns([1, 1, 1.2])
            sh = sc1.selectbox("SH", [f"{i:02d}" for i in range(1,13)], key="sh", label_visibility="collapsed")
            sm = sc2.selectbox("SM", [f"{i:02d}" for i in range(0,60,5)], key="sm", label_visibility="collapsed")
            sap = sc3.selectbox("SAP", ["AM", "PM"], key="sap", label_visibility="collapsed")
            start_str = f"{sh}:{sm} {sap}"
        with r2_c2:
            st.markdown("<p style='font-size:0.85rem; margin-bottom:0.2rem; color:#333; font-weight:500;'>End Time</p>", unsafe_allow_html=True)
            ec1, ec2, ec3 = st.columns([1, 1, 1.2])
            eh = ec1.selectbox("EH", [f"{i:02d}" for i in range(1,13)], key="eh", label_visibility="collapsed")
            em = ec2.selectbox("EM", [f"{i:02d}" for i in range(0,60,5)], key="em", label_visibility="collapsed")
            eap = ec3.selectbox("EAP", ["AM", "PM"], key="eap", label_visibility="collapsed")
            end_str = f"{eh}:{em} {eap}"

        # Row 3: Attendees & Parties
        r3_c1, r3_c2 = st.columns(2)
        with r3_c1:
            client_name = st.text_input("Client / Company", value="", placeholder="XYZ Company")
            selected_crd = st.multiselect("CRD Team Attendees", options=CRD_MEMBERS, default=[])
        with r3_c2:
            ext_attendees_raw = st.text_input("External Attendees", value="", placeholder="e.g. Mr. ABCD, Jane Doe")
            prep_col, conf_col = st.columns(2)
            with prep_col:
                prep_name = st.text_input("Prepared By", value="", placeholder="Name")
                prep_desig = st.text_input("Prep Designation", value="", placeholder="Designation")
            with conf_col:
                conf_name = st.text_input("Confirmed By", value="", placeholder="Name")
                conf_desig = st.text_input("Conf Designation", value="", placeholder="Designation")

# ---- Step 2: Symmetrical Bottom Row (Full Transcript Left, Ask Echo Right) ----
if st.session_state["transcript"]:
    row_left, row_right = st.columns(2)
    
    # LEFT CONTAINER: Full Transcript
    with row_left:
        with st.container(border=True):
            st.markdown('<div class="bottom-card-anchor" style="display:none;"></div>', unsafe_allow_html=True)
            
            ft_head, ft_btn1, ft_btn2 = st.columns([6, 2, 2])
            with ft_head:
                st.markdown('<h3 style="margin-top:0.2rem;">Full Transcript</h3>', unsafe_allow_html=True)
            with ft_btn1:
                copy_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <style>
                body {{ margin: 0; padding: 0; font-family: 'Montserrat', sans-serif; }}
                button {{
                    width: 100%;
                    height: 34px;
                    background-color: #222222;
                    color: #FFFFFF;
                    border: 1px solid #444444;
                    border-radius: 50px;
                    font-size: 0.82rem;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.25s ease;
                    display: flex;
                    align-items: center;
                    justify-content: center;
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
                            document.getElementById("copy-btn").innerText = "Copied";
                            setTimeout(() => document.getElementById("copy-btn").innerText = "Copy Text", 2000);
                        }});
                    }});
                    </script>
                </body>
                </html>
                """
                components.html(copy_html, height=34)
            with ft_btn2:
                st.download_button(
                    label="Download",
                    data=st.session_state["transcript"],
                    file_name=f"Transcript_{meeting_date.strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            st.text_area(
                "Transcript Content", 
                st.session_state["transcript"], 
                height=340, 
                label_visibility="collapsed"
            )
            
            if st.session_state["df"].empty:
                st.write("")
                if st.button("Generate MOM", key="btn_gen_mom"):
                    extracted_df, other_disc = extract_structured_insights(st.session_state["transcript"], selected_eng=st.session_state["selected_engine"])
                    if not extracted_df.empty:
                        st.session_state["df"] = extracted_df
                        st.session_state["other_discussions"] = other_disc
                        st.rerun()
            else:
                st.write("")

    # RIGHT CONTAINER: Ask Echo (AI on Left, User on Right, Symmetrical)
    with row_right:
        with st.container(border=True):
            st.markdown('<div class="bottom-card-anchor" style="display:none;"></div>', unsafe_allow_html=True)
            
            st.markdown('<h3 style="margin-top:0.2rem;">Ask Echo</h3>', unsafe_allow_html=True)
            st.caption("Ask specific questions regarding action items, timelines, deliverables, or remarks.")
            
            # Chat history container with Minimalist/Mature Styling
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            if not st.session_state["chat_history"]:
                st.markdown(
                    '<div class="chat-bubble-ai-wrap">'
                    '<div class="chat-bubble-ai"><div class="ai-header">Echo</div>How may I assist you regarding this meeting transcript?</div>'
                    '</div>',
                    unsafe_allow_html=True
                )
            else:
                for msg in st.session_state["chat_history"]:
                    if msg["role"] == "assistant":
                        formatted_content = msg["content"].replace("\n", "<br>")
                        st.markdown(
                            f'<div class="chat-bubble-ai-wrap">'
                            f'<div class="chat-bubble-ai"><div class="ai-header">Echo</div>{formatted_content}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f'<div class="chat-bubble-user-wrap">'
                            f'<div class="chat-bubble-user">{msg["content"]}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Chat input
            if prompt := st.chat_input("Ask Echo a question..."):
                st.session_state["chat_history"].append({"role": "user", "content": prompt})
                with st.spinner("Analyzing transcript..."):
                    answer = ask_deepseek_question(st.session_state["transcript"], prompt, st.session_state["chat_history"])
                st.session_state["chat_history"].append({"role": "assistant", "content": answer})
                st.rerun()

# ---- Step 3: Minutes of Meeting Editor ----
if not st.session_state["df"].empty:
    with st.container(border=True):
        st.markdown('<h3>Minutes of Meeting Editor</h3>', unsafe_allow_html=True)
        
        st.markdown(
            "<p style='font-size:0.85rem; color:#666; margin-bottom: 0.75rem;'>"
            "<i>*Note: Each discussion item is rendered as a clean card with auto-wrapping text boxes. Edit fields inline directly.</i></p>", 
            unsafe_allow_html=True
        )
        
        df = st.session_state["df"].copy().reset_index(drop=True)
        
        row_to_delete = None
        for idx in range(len(df)):
            with st.container(border=True):
                # Single Horizontal Row per discussion card with auto-wrapping text areas
                c_disc, c_act, c_date, c_pic, c_del = st.columns([3.2, 3.2, 1.8, 1.8, 0.6])
                
                with c_disc:
                    st.markdown('<span class="playfair-label">Discussion Points</span>', unsafe_allow_html=True)
                    st.text_area(
                        "DP",
                        value=str(df.at[idx, "Discussion Points"]),
                        key=f"dp_{idx}",
                        height=75,
                        label_visibility="collapsed"
                    )
                with c_act:
                    st.markdown('<span class="playfair-label">Action Plan</span>', unsafe_allow_html=True)
                    st.text_area(
                        "AP",
                        value=str(df.at[idx, "Action Plan"]),
                        key=f"ap_{idx}",
                        height=75,
                        label_visibility="collapsed"
                    )
                with c_date:
                    st.markdown('<span class="playfair-label">Delivery Date</span>', unsafe_allow_html=True)
                    st.text_area(
                        "DD",
                        value=str(df.at[idx, "Indicative Delivery Date"]),
                        key=f"date_{idx}",
                        height=75,
                        label_visibility="collapsed"
                    )
                with c_pic:
                    st.markdown('<span class="playfair-label">Person-in-charge</span>', unsafe_allow_html=True)
                    st.text_area(
                        "PIC",
                        value=str(df.at[idx, "Person-in-charge"]),
                        key=f"pic_{idx}",
                        height=75,
                        label_visibility="collapsed"
                    )
                with c_del:
                    st.write("<div style='height: 38px;'></div>", unsafe_allow_html=True)
                    if st.button("Delete", key=f"del_{idx}", help=f"Remove item {idx+1}"):
                        row_to_delete = idx
        
        # Handle Deletion
        if row_to_delete is not None:
            df = df.drop(index=row_to_delete).reset_index(drop=True)
            st.session_state["df"] = df
            st.rerun()
        
        # Collect updated values using robust list aggregation
        rows_data = []
        for idx in range(len(df)):
            discussion_val = st.session_state.get(f"dp_{idx}", df.at[idx, "Discussion Points"])
            action_val = st.session_state.get(f"ap_{idx}", df.at[idx, "Action Plan"])
            date_val = st.session_state.get(f"date_{idx}", df.at[idx, "Indicative Delivery Date"])
            pic_val = st.session_state.get(f"pic_{idx}", df.at[idx, "Person-in-charge"])
            
            rows_data.append({
                "Discussion Points": discussion_val,
                "Action Plan": action_val,
                "Indicative Delivery Date": date_val,
                "Person-in-charge": pic_val
            })
        
        st.session_state["df"] = pd.DataFrame(rows_data, columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"])
        
        # Add Item Button
        add_col, _ = st.columns([2, 8])
        with add_col:
            if st.button("+ Add Item", key="add_row"):
                new_row_df = pd.DataFrame([{
                    "Discussion Points": "",
                    "Action Plan": "",
                    "Indicative Delivery Date": "",
                    "Person-in-charge": ""
                }])
                st.session_state["df"] = pd.concat([st.session_state["df"], new_row_df], ignore_index=True)
                st.rerun()
        
        st.markdown('<span class="playfair-label" style="margin-top:0.75rem;">Other Discussions</span>', unsafe_allow_html=True)
        st.session_state["other_discussions"] = st.text_area(
            "Other Discussions Content",
            value=st.session_state["other_discussions"],
            height=100,
            label_visibility="collapsed"
        )

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
