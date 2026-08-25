import os
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
st.set_page_config(page_title="Project Echo", layout="wide", initial_sidebar_state="collapsed")

# --- PROGRAMMATIC LIGHT MODE LOCK ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\n")

# API Keys & Endpoints
GROQ_API_KEY = "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"
GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

# ========== CUSTOM CSS INJECTION ==========
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600&family=Playfair+Display:ital,wght@1,400;1,500&display=swap');

    /* Global Font & Background with Large, Low-Opacity Gridlines */
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
    
    /* Hide default Streamlit header */
    .stApp > header {
        display: none !important;
    }

    /* Adjust main container padding */
    .block-container {
        padding-top: 6rem !important;
    }

    /* Custom Left-Aligned Topbar with its own gridlines */
    .echo-topbar {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 70px;
        background-color: #161616;
        background-image: 
            linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
        background-size: 80px 80px;
        border-bottom: 1px solid #333333;
        display: flex;
        align-items: center;
        padding: 0 2rem;
        z-index: 999999;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .echo-topbar .logo-wrapper {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .echo-topbar h1 {
        font-family: 'Playfair Display', serif !important;
        font-style: italic !important;
        font-weight: 400 !important;
        font-size: 1.5rem !important;
        color: #FFFFFF !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    .echo-topbar h1 span {
        color: #D4AF37 !important; 
    }

    /* Headings */
    h3 {
        font-family: 'Playfair Display', serif !important;
        font-style: italic !important;
        font-weight: 400 !important; 
        color: #1A2B4C !important;
        letter-spacing: 0.02em;
        margin-bottom: 0.5rem;
    }

    /* Container Cards */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border-radius: 16px !important;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.06) !important;
        border: 1px solid rgba(0, 0, 0, 0.03) !important;
        padding: 1.5rem !important;
        margin-bottom: 1.5rem !important;
    }

    /* Dark Pill-Shaped Buttons */
    .stButton > button, .stDownloadButton > button {
        background-color: #222222 !important; 
        color: #FFFFFF !important;
        border: 1px solid #444444 !important;
        border-radius: 50px !important; 
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 500 !important;
        letter-spacing: 0.5px;
        padding: 0.5rem 1.75rem !important;
        transition: all 0.3s ease !important;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 100% !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        border-color: #D4AF37 !important; 
        color: #D4AF37 !important;
        background-color: #1A1A1A !important;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.15) !important;
    }

    /* File Uploader Dropzone */
    [data-testid="stFileUploadDropzone"] {
        background-color: #FDFDFD !important;
        border: 1px dashed #CCC !important;
        border-radius: 12px !important;
        padding: 2.5rem !important;
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
        padding: 1rem !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
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
        justify-content: space-between;
    }
    .toolbar-left, .toolbar-right {
        display: flex;
        gap: 15px;
        align-items: center;
    }
    .toolbar-icon {
        cursor: pointer;
        stroke: #A0A0A0;
        transition: stroke 0.2s ease;
    }
    .toolbar-icon:hover { stroke: #D4AF37; }
    .toolbar-icon.delete-icon:hover { stroke: #D9534F; }
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

    /* Chat Messages Box */
    .chat-scroll-container {
        max-height: 480px;
        overflow-y: auto;
        padding-right: 8px;
        margin-bottom: 1rem;
    }
    
    [data-testid="stChatMessage"] {
        background-color: #F8F7F2 !important;
        border: 1px solid #E8E5DD !important;
        border-radius: 12px !important;
        margin-bottom: 0.75rem !important;
    }

    /* Tabs styling */
    [data-baseweb="tab"] {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 500 !important;
        letter-spacing: 0.5px !important;
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

def extract_structured_insights(transcript, user_instruction="", current_df=None):
    """
    AI Engine: Analyzes transcript and conversation to generate or modify
    structured Key Points, Deliverables, and Action Items.
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    context_data = ""
    if current_df is not None and not current_df.empty:
        context_data = f"\nCurrent Table State:\n{current_df.to_json(orient='records')}\n"
    
    prompt = f"""
    You are an AI Executive Assistant managing meeting outcomes.
    
    Analyze the transcript and user instructions, then return a valid JSON array representing the structured table items.
    
    Categories allowed: "Key Point", "Deliverable", "Action Item".
    
    Each item in the JSON array must follow this exact schema:
    [
      {{
        "Category": "Key Point" | "Deliverable" | "Action Item",
        "Description": "Clear description of the point, item, or deliverable",
        "Action Plan": "Concrete next steps or requirements",
        "Assigned": "Name or role assigned (or 'Unassigned')"
      }}
    ]

    Transcript:
    {transcript}
    {context_data}
    User Instruction:
    {user_instruction if user_instruction else "Extract 4-6 primary items balancing Key Points, Deliverables, and Action Items."}
    
    Respond ONLY with the raw JSON array. Do not wrap in markdown or backticks.
    """
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }
    
    try:
        resp = requests.post(GROQ_CHAT_URL, headers=headers, json=payload)
        if resp.status_code == 200:
            raw_content = resp.json()["choices"][0]["message"]["content"].strip()
            clean_json = re.sub(r"^```json\s*|^```\s*|\s*```$", "", raw_content, flags=re.MULTILINE).strip()
            data = json.loads(clean_json)
            df = pd.DataFrame(data)
            # Ensure proper schema
            for col in ["Category", "Description", "Action Plan", "Assigned"]:
                if col not in df.columns:
                    df[col] = ""
            return df[["Category", "Description", "Action Plan", "Assigned"]]
        else:
            st.warning(f"AI Service Error: {resp.status_code}")
    except Exception as e:
        st.warning(f"Structured extraction error: {e}")
        
    return pd.DataFrame(columns=["Category", "Description", "Action Plan", "Assigned"])

def export_to_word(df, transcript):
    doc = Document()
    doc.sections[0].orientation = 0
    title = doc.add_heading("Project Echo: Meeting Summary", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if transcript:
        doc.add_heading("Full Transcript", level=2)
        p = doc.add_paragraph(transcript)
        p.style.font.size = Pt(10)
    doc.add_heading("Outcomes & Action Items", level=2)
    table = doc.add_table(rows=len(df)+1, cols=4)
    table.style = "Table Grid"
    hdr_cells = table.rows[0].cells
    headers = ["Category", "Description", "Action Plan", "Assigned"]
    for i, header in enumerate(headers):
        hdr_cells[i].text = header
        run = hdr_cells[i].paragraphs[0].runs[0]
        run.font.bold = True
        run.font.color.rgb = RGBColor(26, 43, 76)
    for i, row in df.iterrows():
        cells = table.rows[i+1].cells
        cells[0].text = str(row.get("Category", ""))
        cells[1].text = str(row.get("Description", ""))
        cells[2].text = str(row.get("Action Plan", ""))
        cells[3].text = str(row.get("Assigned", ""))
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
        pdf.cell(0, 10, "Outcomes & Action Items", ln=True)
        pdf.ln(5)
        for i, row in df.iterrows():
            pdf.set_font("Arial", 'B', 10)
            pdf.multi_cell(0, 7, f"[{row.get('Category', '')}] {row.get('Description', '')}")
            pdf.set_font("Arial", '', 9)
            pdf.multi_cell(0, 6, f"Action: {row.get('Action Plan', '')} | Assigned: {row.get('Assigned', '')}")
            pdf.ln(3)
        return pdf.output(dest='S').encode('latin-1')
    except ImportError:
        return b"Error: Please run 'pip install fpdf' to enable PDF export."

# ========== STREAMLIT UI SETUP ==========
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Full-width Fixed Topbar
topbar_html = """
<div class="echo-topbar">
    <div class="logo-wrapper">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#D4AF37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="22"></line>
        </svg>
        <h1>Project <span>Echo</span></h1>
    </div>
</div>
"""
st.markdown(topbar_html, unsafe_allow_html=True)

# Initialize Session State
if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""
if "df" not in st.session_state:
    st.session_state["df"] = pd.DataFrame(columns=["Category", "Description", "Action Plan", "Assigned"])
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# ---- Step 1: Input Audio Card ----
with st.container(border=True):
    st.markdown(
        """<h3 style="display: flex; align-items: center; margin-bottom: 1.5rem;">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#D4AF37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 12px;">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
        </svg> Upload Audio</h3>""", 
        unsafe_allow_html=True
    )
    
    tab1, tab2 = st.tabs(["Upload File", "Record Audio"])
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
            col_rec, _ = st.columns([2, 8])
            with col_rec:
                st.download_button(
                    label="Save Audio File",
                    data=audio_data,
                    file_name="Echo_Recording.wav",
                    mime="audio/wav"
                )
            
    if audio_data:
        st.markdown("<br>", unsafe_allow_html=True)
        col_btn, _ = st.columns([2, 8])
        with col_btn:
            if st.button("Transcribe Audio"):
                with st.spinner("Processing audio with Groq Whisper..."):
                    transcript = transcribe_audio(audio_data)
                if transcript:
                    st.session_state["transcript"] = transcript
                    st.session_state["df"] = pd.DataFrame(columns=["Category", "Description", "Action Plan", "Assigned"])
                    st.session_state["chat_history"] = [
                        {"role": "assistant", "content": "Transcription complete. You can ask me to extract key points, deliverables, and actions, or use the prompt below to generate them automatically."}
                    ]
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
        
        st.text_area("Transcript Content", st.session_state["transcript"], height=180, label_visibility="collapsed")
        
        if st.session_state["df"].empty:
            col_gen, _ = st.columns([2, 8])
            with col_gen:
                if st.button("Generate Outcomes"):
                    with st.spinner("Analyzing transcript and creating structured items..."):
                        extracted_df = extract_structured_insights(st.session_state["transcript"])
                    if not extracted_df.empty:
                        st.session_state["df"] = extracted_df
                        st.session_state["chat_history"].append(
                            {"role": "assistant", "content": "I've analyzed the transcript and populated the editor with categorized Key Points, Deliverables, and Action Items. You can chat with me on the left to refine them."}
                        )
                        st.rerun()

# ---- Step 3: Split Layout (AI Chatbot on Left | Live Table on Right) ----
if not st.session_state["df"].empty or st.session_state["transcript"]:
    col_chat, col_editor = st.columns([4, 6], gap="medium")
    
    # === LEFT COLUMN: AI Assistant ===
    with col_chat:
        with st.container(border=True):
            st.markdown(
                """<h3 style="display: flex; align-items: center;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#D4AF37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 12px;">
                    <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
                </svg> Assistant</h3>""", 
                unsafe_allow_html=True
            )
            
            # Chat history container
            st.markdown('<div class="chat-scroll-container">', unsafe_allow_html=True)
            for msg in st.session_state["chat_history"]:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
            st.markdown('</div>', unsafe_allow_html=True)
            
            # User Chat Input
            user_prompt = st.chat_input("E.g., 'Add a deliverable for security audit', 'Reassign task 1 to Marketing'...")
            
            if user_prompt:
                st.session_state["chat_history"].append({"role": "user", "content": user_prompt})
                
                with st.spinner("Updating table and analyzing request..."):
                    updated_df = extract_structured_insights(
                        st.session_state["transcript"],
                        user_instruction=user_prompt,
                        current_df=st.session_state["df"]
                    )
                
                if not updated_df.empty:
                    st.session_state["df"] = updated_df
                    bot_reply = "I have updated the table with the requested deliverables, action items, and key points."
                else:
                    bot_reply = "I wasn't able to extract modifications for the table. Please try rephrasing your request."
                    
                st.session_state["chat_history"].append({"role": "assistant", "content": bot_reply})
                st.rerun()

    # === RIGHT COLUMN: Live Table Editor & Export ===
    with col_editor:
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
                <div class="toolbar-left">
                    <svg class="toolbar-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"></path><path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"></path></svg>
                    <svg class="toolbar-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="4" x2="10" y2="4"></line><line x1="14" y1="20" x2="5" y2="20"></line><line x1="15" y1="4" x2="9" y2="20"></line></svg>
                    <svg class="toolbar-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3v7a6 6 0 0 0 6 6 6 6 0 0 0 6-6V3"></path><line x1="4" y1="21" x2="20" y2="21"></line></svg>
                    <div class="toolbar-divider"></div>
                    <svg class="toolbar-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
                </div>
                <div class="toolbar-right" title="Select a row checkbox to delete">
                    <svg class="toolbar-icon delete-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                </div>
            </div>
            """
            st.markdown(toolbar_html, unsafe_allow_html=True)

            # Live Interactive Data Editor with Categorization Dropdown
            edited_df = st.data_editor(
                st.session_state["df"],
                num_rows="dynamic",
                use_container_width=True,
                key="action_editor", 
                hide_index=False, 
                column_config={
                    "Category": st.column_config.SelectboxColumn(
                        "Category",
                        options=["Key Point", "Deliverable", "Action Item"],
                        required=True,
                        width="small"
                    ),
                    "Description": st.column_config.TextColumn("Description", width="large"),
                    "Action Plan": st.column_config.TextColumn("Action Plan", width="medium"),
                    "Assigned": st.column_config.TextColumn("Assigned", width="small")
                }
            )
            
            st.session_state["df"] = edited_df

            st.write("")
            col_exp1, col_exp2 = st.columns([1, 1])
            
            with col_exp1:
                doc_bio = export_to_word(st.session_state["df"], st.session_state["transcript"])
                st.download_button(
                    label="Export to Word",
                    data=doc_bio,
                    file_name="Echo_Outcomes_Report.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
            with col_exp2:
                pdf_bytes = export_to_pdf(st.session_state["df"], st.session_state["transcript"])
                st.download_button(
                    label="Export to PDF",
                    data=pdf_bytes,
                    file_name="Echo_Outcomes_Report.pdf",
                    mime="application/pdf"
                )
