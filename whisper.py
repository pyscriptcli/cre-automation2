import streamlit as st
import requests
import json
import pandas as pd
import re
from io import BytesIO
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ========== CONFIG ==========
# Set page config must be the first Streamlit command
st.set_page_config(page_title="Project Echo | Voice App", layout="wide", initial_sidebar_state="collapsed")

# API Keys & Endpoints
GROQ_API_KEY = "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"
GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

# ========== CUSTOM CSS INJECTION ==========
# Design Decisions:
# - Typography: Plus Jakarta Sans for a modern, clean enterprise look.
# - Color Palette: Dark Navy (#0B1A2E) base, Gold (#F5B041) accents.
# - Depth: Radial gradients on the background and box-shadows on buttons/containers.
# - Border Radius: 12px for standard elements, 24px for larger cards.
# - Transitions: Smooth 0.2s ease on all interactive elements.
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* Global Font & Background */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    .stApp {
        background-color: #0B1A2E;
        background-image: radial-gradient(circle at 50% 0%, #13273F 0%, #0B1A2E 70%);
        color: #B0C4DE;
    }

    /* Headings */
    h1, h2, h3 {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    /* Custom Header */
    .echo-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1.5rem 2rem;
        background: rgba(19, 39, 63, 0.6);
        backdrop-filter: blur(12px);
        border-radius: 20px;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }
    .echo-logo {
        font-size: 1.5rem;
        font-weight: 800;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .echo-logo span { color: #F5B041; }
    .echo-nav {
        display: flex;
        gap: 1.5rem;
    }
    .echo-nav-item {
        color: #B0C4DE;
        text-decoration: none;
        font-weight: 500;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    .echo-nav-item.active {
        color: #FFFFFF;
        border-bottom: 2px solid #F5B041;
        padding-bottom: 4px;
    }

    /* Primary Buttons (Gold) */
    .stButton > button {
        background-color: #F5B041 !important;
        color: #1A1A1A !important;
        border: none !important;
        border-radius: 50px !important; /* Pill shape */
        font-weight: 700 !important;
        padding: 0.6rem 2rem !important;
        box-shadow: 0 4px 16px rgba(245, 176, 65, 0.2) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: #C79A2E !important;
        box-shadow: 0 6px 24px rgba(245, 176, 65, 0.4) !important;
        transform: translateY(-2px) !important;
        color: #1A1A1A !important;
    }

    /* File Uploader Dropzone */
    [data-testid="stFileUploadDropzone"] {
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 2px dashed #7A8DA0 !important;
        border-radius: 24px !important;
        padding: 3rem !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        border-color: #F5B041 !important;
        background-color: rgba(245, 176, 65, 0.05) !important;
    }
    [data-testid="stFileUploadDropzone"] * {
        color: #FFFFFF !important;
    }

    /* Text Area (Transcript) */
    .stTextArea textarea {
        background-color: #13273F !important;
        border: 1px solid #1C3A5A !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.2) !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
        transition: all 0.2s ease !important;
    }
    .stTextArea textarea:focus {
        border-color: #F5B041 !important;
        box-shadow: 0 0 0 1px #F5B041 !important;
    }

    /* Dataframe / Table overriding */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #1C3A5A;
        box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    }

    /* Spinners & Progress */
    .stSpinner > div > div {
        border-color: #F5B041 transparent transparent transparent !important;
    }

    /* Info / Success Badges */
    [data-testid="stAlert"] {
        background-color: rgba(245, 176, 65, 0.1) !important;
        color: #FDEBD0 !important;
        border: 1px solid rgba(245, 176, 65, 0.2) !important;
        border-radius: 12px !important;
    }

    /* Custom Footer */
    .echo-footer {
        margin-top: 4rem;
        padding: 2rem;
        background-color: #1A1A1A;
        border-radius: 24px 24px 0 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #7A8DA0;
        font-size: 0.85rem;
    }
    .echo-footer-links a {
        color: #F5B041;
        text-decoration: none;
        margin-left: 1rem;
        transition: color 0.2s ease;
    }
    .echo-footer-links a:hover {
        color: #FDEBD0;
    }
</style>
"""

# ========== HELPER FUNCTIONS ==========
def transcribe_audio(audio_bytes):
    """Transcribe using Groq Whisper."""
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
        st.error(f"Transcription failed: {resp.text}")
        return None

def summarize_text(text):
    """Generate key points using Groq Llama (Replacing Puter)."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"""
    You are an expert summarizer. Read the following transcript and extract the 3-5 most important key points.
    Output each key point as a separate line, starting with a dash "-". Do not include any extra text, pleasantries, or numbering.
    Transcript:
    {text}
    """
    payload = {
        "model": "llama-3.1-8b-instant", 
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    
    try:
        resp = requests.post(GROQ_CHAT_URL, headers=headers, json=payload)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            # Parse bullet points
            lines = [line.strip() for line in content.split("\n") if line.strip().startswith("-")]
            if not lines:
                sentences = re.split(r'(?<=[.!?])\s+', text)
                lines = [f"- {s}" for s in sentences[:3]]
            return [line.lstrip("- ").strip() for line in lines]
        else:
            st.warning(f"Summarization API error: {resp.status_code}.")
            return fallback_summary(text)
    except Exception as e:
        st.warning(f"Summarization failed: {e}.")
        return fallback_summary(text)

def fallback_summary(text):
    """Simple fallback: extract first 3 sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences[:3] if s.strip()]

def export_to_word(df, transcript):
    """Generate a themed Word document with the table."""
    doc = Document()
    doc.sections[0].orientation = 0
    doc.sections[0].page_width = Inches(8.5)
    doc.sections[0].page_height = Inches(11.0)

    # Document Styling
    title = doc.add_heading("Project Echo: Meeting Summary", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add Transcript Optional Section
    if transcript:
        doc.add_heading("Full Transcript", level=2)
        p = doc.add_paragraph(transcript)
        p.style.font.size = Pt(10)

    doc.add_heading("Action Items & Key Points", level=2)
    table = doc.add_table(rows=len(df)+1, cols=3)
    table.style = "Table Grid"

    # Header styling (Simulating the Gold theme in Word)
    hdr_cells = table.rows[0].cells
    headers = ["Key Point", "Action Plan", "Assigned"]
    for i, header in enumerate(headers):
        hdr_cells[i].text = header
        run = hdr_cells[i].paragraphs[0].runs[0]
        run.font.bold = True
        run.font.color.rgb = RGBColor(199, 154, 46) # Gold Dark

    # Data population
    for i, row in df.iterrows():
        cells = table.rows[i+1].cells
        cells[0].text = str(row["Key Point"])
        cells[1].text = str(row["Action Plan"])
        cells[2].text = str(row["Assigned"])

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# ========== STREAMLIT UI SETUP ==========
# Inject CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Custom Header HTML
header_html = """
<div class="echo-header">
    <div class="echo-logo">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#F5B041" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="22"></line></svg>
        Project <span>Echo</span>
    </div>
    <div class="echo-nav">
        <a class="echo-nav-item active">Dashboard</a>
        <a class="echo-nav-item">Reports</a>
        <a class="echo-nav-item">Settings</a>
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# Initialize session state[cite: 1]
if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""
if "key_points" not in st.session_state:
    st.session_state["key_points"] = []
if "df" not in st.session_state:
    st.session_state["df"] = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])

# ---- UI Layout: Main Content ----
st.markdown("### 🎙️ Audio Processing Hub")
st.markdown("<span style='color:#7A8DA0;'>Upload your meeting recording to automatically generate transcripts and actionable insights.</span>", unsafe_allow_html=True)
st.write("") # Spacer

# ---- Step 1: Upload & Transcribe ----
uploaded = st.file_uploader("Drag and drop your audio file here", type=["wav", "mp3", "m4a", "ogg", "flac", "mp4", "webm"], label_visibility="collapsed")[cite: 1]

if uploaded:
    col_btn, _ = st.columns([2, 10])
    with col_btn:
        if st.button("✨ Transcribe Audio"):
            with st.spinner("Processing audio with Groq Whisper..."):
                transcript = transcribe_audio(uploaded.read())[cite: 1]
            if transcript:
                st.session_state["transcript"] = transcript
                st.session_state["key_points"] = []
                st.session_state["df"] = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])[cite: 1]
                st.rerun()

# ---- Step 2: Transcript Display & Summarize ----
if st.session_state["transcript"]:
    st.markdown("---")
    
    # Extra Credit: Word Count & Reading Time calculation
    word_count = len(st.session_state["transcript"].split())
    read_time = max(1, word_count // 200)
    
    col_title, col_meta = st.columns([3, 1])
    with col_title:
        st.markdown(f"### 📋 Full Transcript")
    with col_meta:
        st.markdown(f"<div style='text-align: right; color: #F5B041; font-size: 0.9rem; font-weight: 600; padding-top: 0.5rem;'>{word_count} words • ~{read_time} min read</div>", unsafe_allow_html=True)
    
    st.text_area("Transcript Content", st.session_state["transcript"], height=200, label_visibility="collapsed")[cite: 1]
    
    if not st.session_state["key_points"]:
        st.write("")
        if st.button("📝 Generate Action Items"):
            with st.spinner("Analyzing context with Groq Llama..."):
                points = summarize_text(st.session_state["transcript"])
            if points:
                st.session_state["key_points"] = points
                df = pd.DataFrame({
                    "Key Point": points,
                    "Action Plan": [""] * len(points),
                    "Assigned": [""] * len(points)
                })[cite: 1]
                st.session_state["df"] = df
                st.rerun()

# ---- Step 3: Table Editor & Export ----
if not st.session_state["df"].empty:
    st.markdown("---")
    st.markdown("### 🎯 Action Plan Editor")
    st.markdown("<span style='color:#B0C4DE; font-size: 0.95rem;'>Double-click cells below to assign tasks and define action plans. Changes are saved automatically.</span>", unsafe_allow_html=True)
    
    # Styled Data Editor Wrapper
    st.markdown("<div style='padding: 1rem 0;'>", unsafe_allow_html=True)
    edited_df = st.data_editor(
        st.session_state["df"],
        num_rows="dynamic",
        use_container_width=True,
        key="data_editor",
        hide_index=True
    )[cite: 1]
    st.session_state["df"] = edited_df[cite: 1]
    st.markdown("</div>", unsafe_allow_html=True)

    # Export Section
    st.write("")
    col_exp1, col_exp2 = st.columns([2, 8])
    with col_exp1:
        doc_bio = export_to_word(st.session_state["df"], st.session_state["transcript"])[cite: 1]
        st.download_button(
            label="⬇️ Export to Word (.docx)",
            data=doc_bio,
            file_name="Echo_Action_Report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )[cite: 1]

# ---- Footer ----
footer_html = """
<div class="echo-footer">
    <div>&copy; 2026 Project Echo Enterprise. All rights reserved.</div>
    <div class="echo-footer-links">
        <a href="#">Documentation</a>
        <a href="#">Privacy Policy</a>
        <a href="#">Support</a>
    </div>
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
