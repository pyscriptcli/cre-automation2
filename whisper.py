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
st.set_page_config(page_title="Project Echo | Voice App", layout="wide", initial_sidebar_state="collapsed")

# API Keys & Endpoints
GROQ_API_KEY = "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"
GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

# ========== CUSTOM CSS INJECTION ==========
CUSTOM_CSS = """
<style>
    /* Fonts matching the uploaded image */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600&family=Playfair+Display:ital,wght@1,400;1,500&display=swap');

    /* Global Font & Light Background (Off-white/Cream from bottom half of image) */
    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif !important;
    }
    
    .stApp {
        background-color: #F4F2EC; 
        color: #333333;
    }

    /* Headings (Elegant Serif, Not Bold) */
    h1, h2, h3 {
        font-family: 'Playfair Display', serif !important;
        font-style: italic !important;
        font-weight: 400 !important; /* Forces normal/light weight */
        color: #1A2B4C !important; /* Deep Navy from image */
        letter-spacing: 0.02em;
        margin-bottom: 0.5rem;
    }

    /* Top Dark Header Card (Mimicking Top half of image) */
    .echo-header {
        background-color: #161616;
        background-image: 
            linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
        background-size: 40px 40px;
        padding: 3rem 2rem;
        border-radius: 16px;
        margin-bottom: 2.5rem;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
        text-align: center;
        border: 1px solid #222;
    }
    .echo-header .eyebrow {
        color: #D4AF37; /* Gold */
        font-family: 'Montserrat', sans-serif;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }
    .echo-header .eyebrow::after {
        content: "";
        display: block;
        width: 40px;
        height: 2px;
        background-color: #D4AF37;
        margin: 8px auto 0 auto;
    }
    .echo-header h1 {
        font-size: 2.5rem;
        color: #FFFFFF !important;
        margin: 0;
    }
    .echo-header h1 span { color: #D4AF37; }

    /* Container Cards (Depth) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border-radius: 16px !important;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.06) !important;
        border: 1px solid rgba(0, 0, 0, 0.03) !important;
        padding: 2rem !important;
        margin-bottom: 2rem !important;
    }

    /* Primary Buttons */
    .stButton > button {
        background-color: transparent !important;
        color: #1A2B4C !important;
        border: 1px solid #1A2B4C !important;
        border-radius: 6px !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 500 !important;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        padding: 0.5rem 1.5rem !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background-color: #1A2B4C !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 15px rgba(26, 43, 76, 0.2) !important;
    }

    /* File Uploader Dropzone */
    [data-testid="stFileUploadDropzone"] {
        background-color: #FDFDFD !important;
        border: 1px dashed #CCC !important;
        border-radius: 12px !important;
        padding: 3rem !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        border-color: #1A2B4C !important;
        background-color: #F8FAFC !important;
    }

    /* Text Area (Transcript) */
    .stTextArea textarea {
        background-color: #FDFDFD !important;
        border: 1px solid #E5E5E5 !important;
        color: #333 !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        font-size: 0.95rem !important;
        line-height: 1.8 !important;
        box-shadow: inset 0 2px 5px rgba(0,0,0,0.02) !important;
    }

    /* Toolbar Ribbon */
    .editor-toolbar {
        display: flex;
        gap: 15px;
        padding: 12px 20px;
        background-color: #FDFDFD;
        border: 1px solid #E5E5E5;
        border-radius: 8px 8px 0 0;
        align-items: center;
        border-bottom: none;
    }
    .toolbar-icon {
        cursor: pointer;
        stroke: #A0A0A0;
        transition: stroke 0.2s ease;
    }
    .toolbar-icon:hover { stroke: #D4AF37; }
    .toolbar-divider {
        width: 1px;
        height: 20px;
        background-color: #E5E5E5;
        margin: 0 5px;
    }

    /* Dataframe wrapper overrides */
    [data-testid="stDataFrame"] {
        border-radius: 0 0 8px 8px;
        overflow: hidden;
        border: 1px solid #E5E5E5;
    }

    /* Tabs styling */
    [data-baseweb="tab"] {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 500 !important;
        letter-spacing: 1px !important;
    }
</style>
"""

# ========== CORE LOGIC ==========
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
        st.error(f"Transcription failed: {resp.text}")
        return None

def summarize_text(text):
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
            lines = [line.strip() for line in content.split("\n") if line.strip().startswith("-")]
            if not lines:
                sentences = re.split(r'(?<=[.!?])\s+', text)
                lines = [f"- {s}" for s in sentences[:3]]
            return [line.lstrip("- ").strip() for line in lines]
        return fallback_summary(text)
    except:
        return fallback_summary(text)

def fallback_summary(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences[:3] if s.strip()]

def export_to_word(df, transcript):
    doc = Document()
    doc.sections[0].orientation = 0
    title = doc.add_heading("Project Echo: Meeting Summary", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if transcript:
        doc.add_heading("Full Transcript", level=2)
        p = doc.add_paragraph(transcript)
        p.style.font.size = Pt(10)
    doc.add_heading("Action Items & Key Points", level=2)
    table = doc.add_table(rows=len(df)+1, cols=3)
    table.style = "Table Grid"
    hdr_cells = table.rows[0].cells
    headers = ["Key Point", "Action Plan", "Assigned"]
    for i, header in enumerate(headers):
        hdr_cells[i].text = header
        run = hdr_cells[i].paragraphs[0].runs[0]
        run.font.bold = True
        run.font.color.rgb = RGBColor(26, 43, 76)
    for i, row in df.iterrows():
        cells = table.rows[i+1].cells
        cells[0].text = str(row["Key Point"])
        cells[1].text = str(row["Action Plan"])
        cells[2].text = str(row["Assigned"])
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def export_to_pdf(df, transcript):
    try:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Project Echo: Meeting Summary", ln=True, align='C')
        pdf.ln(5)
        if transcript:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Full Transcript", ln=True)
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 8, transcript.encode('latin-1', 'replace').decode('latin-1'))
            pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Action Items & Key Points", ln=True)
        pdf.ln(5)
        for i, row in df.iterrows():
            pdf.set_font("Arial", 'B', 10)
            pdf.multi_cell(0, 8, f"Key Point: {row['Key Point']}")
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 8, f"Action: {row['Action Plan']} | Assigned: {row['Assigned']}")
            pdf.ln(3)
        return pdf.output(dest='S').encode('latin-1')
    except ImportError:
        return b"Error: Please run 'pip install fpdf' to enable PDF export."

# ========== STREAMLIT UI SETUP ==========
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Image-Inspired Header
header_html = """
<div class="echo-header">
    <div class="eyebrow">Project Input</div>
    <h1>Project <span>Echo</span></h1>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# Session State
if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""
if "key_points" not in st.session_state:
    st.session_state["key_points"] = []
if "df" not in st.session_state:
    st.session_state["df"] = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])

# ---- Step 1: Input Card (Upload or Record) ----
with st.container(border=True):
    st.markdown(
        """<h3 style="display: flex; align-items: center; margin-bottom: 1.5rem;">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#D4AF37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 12px;">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="22"></line>
        </svg> Input Audio Source</h3>""", 
        unsafe_allow_html=True
    )
    
    tab1, tab2 = st.tabs(["📁 Upload File", "🎙️ Record Audio"])
    
    audio_data = None
    
    with tab1:
        uploaded = st.file_uploader("Upload recording", type=["wav", "mp3", "m4a", "ogg", "flac", "mp4", "webm"], label_visibility="collapsed")
        if uploaded:
            audio_data = uploaded.read()
            
    with tab2:
        st.write("Record directly from your microphone:")
        recorded_audio = st.audio_input("Record Audio", label_visibility="collapsed")
        if recorded_audio:
            audio_data = recorded_audio.read()
            # Allow user to save the recorded audio file locally
            st.download_button(
                label="Save Audio File",
                data=audio_data,
                file_name="Echo_Recording.wav",
                mime="audio/wav"
            )
            
    if audio_data:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Transcribe Audio"):
            with st.spinner("Processing audio with Groq Whisper..."):
                transcript = transcribe_audio(audio_data)
            if transcript:
                st.session_state["transcript"] = transcript
                st.session_state["key_points"] = []
                st.session_state["df"] = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])
                st.rerun()

# ---- Step 2: Transcript Card ----
if st.session_state["transcript"]:
    with st.container(border=True):
        word_count = len(st.session_state["transcript"].split())
        read_time = max(1, word_count // 200)
        
        col_title, col_meta = st.columns([3, 1])
        with col_title:
            st.markdown(
                """<h3 style="display: flex; align-items: center;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#D4AF37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 12px;">
                    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
                    <rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
                </svg> Full Transcript</h3>""", 
                unsafe_allow_html=True
            )
        with col_meta:
            st.markdown(f"<div style='text-align: right; color: #1A2B4C; font-size: 0.85rem; font-family: Montserrat; font-weight: 500; padding-top: 0.5rem;'>{word_count} words • ~{read_time} min read</div>", unsafe_allow_html=True)
        
        st.text_area("Transcript Content", st.session_state["transcript"], height=250, label_visibility="collapsed")
        
        if not st.session_state["key_points"]:
            st.write("")
            if st.button("Generate Action Items"):
                with st.spinner("Analyzing context..."):
                    points = summarize_text(st.session_state["transcript"])
                if points:
                    st.session_state["key_points"] = points
                    df = pd.DataFrame({
                        "Key Point": points,
                        "Action Plan": [""] * len(points),
                        "Assigned": [""] * len(points)
                    })
                    st.session_state["df"] = df
                    st.rerun()

# ---- Step 3: Editor Card ----
if not st.session_state["df"].empty:
    with st.container(border=True):
        st.markdown(
            """<h3 style="display: flex; align-items: center;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#D4AF37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 12px;">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg> Editor</h3>""", 
            unsafe_allow_html=True
        )
        
        # Toolbar
        toolbar_html = """
        <div class="editor-toolbar">
            <svg class="toolbar-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"></path><path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"></path></svg>
            <svg class="toolbar-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="4" x2="10" y2="4"></line><line x1="14" y1="20" x2="5" y2="20"></line><line x1="15" y1="4" x2="9" y2="20"></line></svg>
            <svg class="toolbar-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3v7a6 6 0 0 0 6 6 6 6 0 0 0 6-6V3"></path><line x1="4" y1="21" x2="20" y2="21"></line></svg>
            <div class="toolbar-divider"></div>
            <svg class="toolbar-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
        </div>
        """
        st.markdown(toolbar_html, unsafe_allow_html=True)

        # Editor with wrapped text configurations
        edited_df = st.data_editor(
            st.session_state["df"],
            num_rows="dynamic",
            use_container_width=True,
            key="data_editor",
            hide_index=True,
            column_config={
                "Key Point": st.column_config.TextColumn("Key Point", width="large"),
                "Action Plan": st.column_config.TextColumn("Action Plan", width="large"),
                "Assigned": st.column_config.TextColumn("Assigned", width="medium")
            }
        )
        st.session_state["df"] = edited_df

        st.write("")
        col_exp1, col_exp2, _ = st.columns([2, 2, 8])
        
        with col_exp1:
            doc_bio = export_to_word(st.session_state["df"], st.session_state["transcript"])
            st.download_button(
                label="Export to Word",
                data=doc_bio,
                file_name="Echo_Action_Report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
        with col_exp2:
            pdf_bytes = export_to_pdf(st.session_state["df"], st.session_state["transcript"])
            st.download_button(
                label="Export to PDF",
                data=pdf_bytes,
                file_name="Echo_Action_Report.pdf",
                mime="application/pdf"
            )
