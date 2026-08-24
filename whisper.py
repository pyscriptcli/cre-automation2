import streamlit as st
import requests
import json
import re
import pandas as pd
from io import BytesIO
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

# ==========================================
# 1. PAGE CONFIGURATION & THEME STYLING
# ==========================================
st.set_page_config(
    page_title="Executive Meeting Intelligence Portal",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS implementing Corporate Crimson Theme and Full-Screen Mode
st.markdown("""
<style>
    /* 1. Fullscreen Adjustments: Hide Streamlit Header, Top Toolbar, and Footer */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    #MainMenu {
        visibility: hidden !important;
    }
    footer {
        visibility: hidden !important;
    }
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        max-width: 1400px !important;
    }

    /* 2. Global Typography & Background */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        color: #0F172A;
    }
    .stApp {
        background-color: #F8FAFC;
    }

    /* 3. Header and Navigation Aesthetics */
    .portal-header {
        background-color: #FFFFFF;
        border-bottom: 1px solid #E2E8F0;
        padding: 1.25rem 2rem;
        margin: -1.5rem -2.5rem 2rem -2.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .brand-title {
        font-size: 1.15rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #0F172A;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .brand-accent {
        color: #990000;
    }
    .portal-eyebrow {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #990000;
        margin-bottom: 0.25rem;
    }

    /* 4. Card Container Aesthetics */
    .portal-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
    }
    .card-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.25rem;
    }
    .card-desc {
        font-size: 0.875rem;
        color: #64748B;
        margin-bottom: 1rem;
    }

    /* 5. Custom Button Overrides */
    div.stButton > button {
        background-color: #990000 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        padding: 0.6rem 1.4rem !important;
        border-radius: 6px !important;
        border: 1px solid #990000 !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
    }
    div.stButton > button:hover {
        background-color: #7F1D1D !important;
        border-color: #7F1D1D !important;
        color: #FFFFFF !important;
    }
    div.stDownloadButton > button {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        padding: 0.6rem 1.4rem !important;
        border-radius: 6px !important;
        border: 1px solid #0F172A !important;
        transition: all 0.2s ease-in-out !important;
    }
    div.stDownloadButton > button:hover {
        background-color: #1E293B !important;
        border-color: #1E293B !important;
    }

    /* 6. Form Inputs & Text Areas */
    .stTextArea textarea {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
        font-size: 0.875rem !important;
        color: #1E293B !important;
    }
    .stTextArea textarea:focus {
        border-color: #990000 !important;
        box-shadow: 0 0 0 1px #990000 !important;
    }

    /* 7. Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 1px solid #E2E8F0;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.875rem;
        font-weight: 600;
        color: #64748B;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        color: #990000 !important;
        border-bottom: 2px solid #990000 !important;
    }

    /* 8. Data Editor Enhancements */
    [data-testid="stDataEditor"] {
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        background-color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONFIGURATION & STATE INITIALIZATION
# ==========================================
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
PUTER_CHAT_URL = "https://api.puter.com/v1/ai/chat"

if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""
if "df" not in st.session_state:
    st.session_state["df"] = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])

# ==========================================
# 3. CORE LOGIC & BACKEND SERVICES
# ==========================================
def transcribe_audio(audio_bytes):
    """Transcribe audio payload using Groq Whisper Turbo."""
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {
        "file": ("recording.wav", audio_bytes),
        "model": (None, "whisper-large-v3-turbo"),
        "response_format": (None, "json")
    }
    try:
        resp = requests.post(GROQ_URL, headers=headers, files=files, timeout=60)
        if resp.status_code == 200:
            return resp.json().get("text", "")
        else:
            st.error(f"Transcription service error: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        st.error(f"Network error during transcription: {e}")
        return None

def generate_minutes_of_meeting(transcript_text):
    """
    Extract key points, action items, and assignees in structured JSON format.
    """
    system_instruction = (
        "You are an executive corporate secretary and meeting minutes analyst. "
        "Analyze the transcript and generate structured minutes of the meeting. "
        "Extract 3 to 8 actionable meeting items. "
        "For each item, identify: "
        "1. Key Point (the core discussion or decision) "
        "2. Action Plan (concrete next step or execution plan) "
        "3. Assigned (department, person, or 'Team' responsible; default to 'Unassigned' if not mentioned). "
        "Output ONLY a valid JSON array of objects with the exact keys: 'Key Point', 'Action Plan', 'Assigned'. "
        "Do not include markdown codeblocks or conversational text."
    )
    
    prompt = f"Transcript:\n{transcript_text}"
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        resp = requests.post(PUTER_CHAT_URL, json=payload, timeout=60)
        if resp.status_code == 200:
            result = resp.json()
            raw_content = ""
            if "choices" in result and result["choices"]:
                raw_content = result["choices"][0]["message"]["content"]
            elif "response" in result:
                raw_content = result["response"]
            elif "content" in result:
                raw_content = result["content"]
            
            # Clean JSON formatting wrappers if present
            cleaned_json = re.sub(r'```json\s*|```\s*', '', raw_content).strip()
            parsed_data = json.loads(cleaned_json)
            
            if isinstance(parsed_data, list) and len(parsed_data) > 0:
                return pd.DataFrame(parsed_data)
        
        # Fallback parsing if JSON parsing fails
        return fallback_dataframe_generation(transcript_text)
    except Exception:
        return fallback_dataframe_generation(transcript_text)

def fallback_dataframe_generation(transcript_text):
    """Heuristic fallback to extract bullet points and build a default table."""
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', transcript_text) if len(s.strip()) > 10]
    items = sentences[:5] if sentences else ["General meeting discussion reviewed."]
    return pd.DataFrame({
        "Key Point": items,
        "Action Plan": ["Review notes and implement operational requirements" for _ in items],
        "Assigned": ["Management Team" for _ in items]
    })

def export_to_corporate_docx(df, transcript_text):
    """Exports structured executive minutes to DOCX formatted with Corporate Crimson styling."""
    doc = Document()
    
    # Page Setup
    section = doc.sections[0]
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

    # Document Header
    p_pre = doc.add_paragraph()
    r_pre = p_pre.add_run("EXECUTIVE INTELLIGENCE & ADVISORY")
    r_pre.font.name = "Arial"
    r_pre.font.size = Pt(8.5)
    r_pre.font.bold = True
    r_pre.font.color.rgb = RGBColor(153, 0, 0) # Crimson

    p_title = doc.add_paragraph()
    r_title = p_title.add_run("MINUTES OF THE MEETING")
    r_title.font.name = "Arial"
    r_title.font.size = Pt(18)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(15, 23, 42) # Slate 900

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Section 1: Action Plan & Assigned Items Table
    h1 = doc.add_heading(level=2)
    r_h1 = h1.add_run("1. Executive Summary & Action Items")
    r_h1.font.name = "Arial"
    r_h1.font.size = Pt(12)
    r_h1.font.bold = True
    r_h1.font.color.rgb = RGBColor(15, 23, 42)

    table = doc.add_table(rows=len(df) + 1, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    col_widths = [Inches(3.0), Inches(2.3), Inches(1.2)]
    headers = ["Key Point / Discussion", "Action Plan", "Assigned"]

    # Table Header Styling (Slate 900 Background with White Text)
    hdr_row = table.rows[0]
    for idx, heading in enumerate(headers):
        cell = hdr_row.cells[idx]
        cell.width = col_widths[idx]
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run(heading)
        run.font.name = "Arial"
        run.font.size = Pt(9.5)
        run.font.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        
        # Set dark slate cell shading
        shading = parse_xml(r'<w:shd {} w:fill="0F172A"/>'.format(nsdecls('w')))
        cell._tc.get_or_add_tcPr().append(shading)

    # Table Rows Data
    for i, row in df.iterrows():
        row_cells = table.rows[i + 1].cells
        for col_idx, col_name in enumerate(["Key Point", "Action Plan", "Assigned"]):
            cell = row_cells[col_idx]
            cell.width = col_widths[col_idx]
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(5)
            p.paragraph_format.space_after = Pt(5)
            run = p.add_run(str(row.get(col_name, "")))
            run.font.name = "Arial"
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(51, 65, 85)

    doc.add_paragraph().paragraph_format.space_after = Pt(14)

    # Section 2: Full Transcript Section
    if transcript_text:
        h2 = doc.add_heading(level=2)
        r_h2 = h2.add_run("2. Full Meeting Transcript")
        r_h2.font.name = "Arial"
        r_h2.font.size = Pt(12)
        r_h2.font.bold = True
        r_h2.font.color.rgb = RGBColor(15, 23, 42)

        p_t = doc.add_paragraph()
        p_t.paragraph_format.space_before = Pt(4)
        p_t.paragraph_format.line_spacing = 1.2
        r_t = p_t.add_run(transcript_text)
        r_t.font.name = "Arial"
        r_t.font.size = Pt(9)
        r_t.font.color.rgb = RGBColor(71, 85, 105)

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# ==========================================
# 4. APPLICATION INTERFACE
# ==========================================

# Top Brand Navigation Bar
st.markdown("""
<div class="portal-header">
    <div>
        <div class="portal-eyebrow">Enterprise Productivity Suite</div>
        <div class="brand-title">Corporate Intelligence <span class="brand-accent">Portal</span></div>
    </div>
    <div style="font-size: 0.8rem; font-weight: 600; color: #64748B;">
        Secure Transcription & Governance System
    </div>
</div>
""", unsafe_allow_html=True)

# Main Two-Column Layout
left_col, right_col = st.columns([1, 1], gap="large")

with left_col:
    st.markdown('<div class="portal-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">1. Audio Capture & Transcription</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-desc">Select an audio source to capture the meeting audio for analysis.</div>', unsafe_allow_html=True)

    input_tab1, input_tab2 = st.tabs(["Upload Audio File", "Live In-Browser Recording"])
    
    audio_data_to_process = None
    
    with input_tab1:
        uploaded_file = st.file_uploader(
            "Upload meeting recording",
            type=["wav", "mp3", "m4a", "ogg", "flac", "mp4", "webm"],
            label_visibility="collapsed"
        )
        if uploaded_file is not None:
            audio_data_to_process = uploaded_file.read()
            st.caption(f"Loaded: {uploaded_file.name} ({len(audio_data_to_process) / (1024*1024):.2f} MB)")

    with input_tab2:
        st.write("Click the microphone below to record directly from your system:")
        mic_audio = st.audio_input("Record Meeting Audio", label_visibility="collapsed")
        if mic_audio is not None:
            audio_data_to_process = mic_audio.read()
            st.caption("Live microphone audio captured successfully.")

    st.write("")
    if st.button("Transcribe Audio Recording", use_container_width=True):
        if audio_data_to_process is not None:
            with st.spinner("Processing audio with Whisper Intelligence Engine..."):
                transcript_result = transcribe_audio(audio_data_to_process)
            if transcript_result:
                st.session_state["transcript"] = transcript_result
                st.session_state["df"] = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])
                st.rerun()
        else:
            st.warning("Please upload a file or record audio before requesting transcription.")

    st.markdown('</div>', unsafe_allow_html=True)

    # Transcript Box
    if st.session_state["transcript"]:
        st.markdown('<div class="portal-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Transcript Review</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-desc">Verified transcription output from the meeting recording.</div>', unsafe_allow_html=True)
        
        updated_transcript = st.text_area(
            "Verified Transcript",
            value=st.session_state["transcript"],
            height=280,
            label_visibility="collapsed"
        )
        st.session_state["transcript"] = updated_transcript
        
        st.write("")
        if st.button("Generate Minutes of the Meeting", use_container_width=True):
            with st.spinner("Analyzing transcript and structuring executive action items..."):
                extracted_df = generate_minutes_of_meeting(st.session_state["transcript"])
                st.session_state["df"] = extracted_df
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

with right_col:
    st.markdown('<div class="portal-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">2. Minutes of the Meeting & Action Governance</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-desc">Review, edit, add, or delete key points, action items, and assignees directly in the governance table.</div>', unsafe_allow_html=True)

    if not st.session_state["df"].empty:
        # Interactive Editable Grid
        edited_table = st.data_editor(
            st.session_state["df"],
            num_rows="dynamic",
            use_container_width=True,
            height=380,
            column_config={
                "Key Point": st.column_config.TextColumn(
                    "Key Point / Discussion",
                    help="Core discussion topic or key decision",
                    width="medium",
                    required=True
                ),
                "Action Plan": st.column_config.TextColumn(
                    "Action Plan",
                    help="Operational next step or resolution",
                    width="medium",
                    required=True
                ),
                "Assigned": st.column_config.TextColumn(
                    "Assigned",
                    help="Responsible party or department",
                    width="small",
                    required=True
                )
            }
        )
        st.session_state["df"] = edited_table

        st.markdown("---")
        
        # Export Actions
        doc_buffer = export_to_corporate_docx(
            st.session_state["df"], 
            st.session_state["transcript"]
        )
        
        st.download_button(
            label="Export Structured Report (.docx)",
            data=doc_buffer,
            file_name="Minutes_of_Meeting_Report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    else:
        st.info("No minutes generated yet. Transcribe an audio recording and click 'Generate Minutes of the Meeting' to populate this table.")
    
    st.markdown('</div>', unsafe_allow_html=True)
