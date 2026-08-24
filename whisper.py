import streamlit as st
import requests
import json
import pandas as pd
from io import BytesIO
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

# ==================== APP CONFIGURATION ====================
st.set_page_config(
    page_title="Executive Meeting Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== MINIMALIST STYLING & FULLSCREEN ====================
st.markdown("""
<style>
    /* Hide top header bar, footer, and menu */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    #MainMenu, footer, .stDeployButton {
        visibility: hidden !important;
        display: none !important;
    }
    
    /* Layout Spacing */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px !important;
        margin: 0 auto;
    }

    /* Minimalist Typography */
    body, .stMarkdown, .stText {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #1a1a1a;
    }

    /* Header styling */
    .app-header {
        font-size: 1.6rem;
        font-weight: 600;
        letter-spacing: -0.02em;
        margin-bottom: 0.2rem;
        color: #111827;
    }
    .app-subtitle {
        font-size: 0.9rem;
        color: #6b7280;
        margin-bottom: 1.5rem;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 6px !important;
        border: 1px solid #e5e7eb !important;
        font-weight: 500 !important;
        padding: 0.45rem 1rem !important;
        transition: all 0.15s ease !important;
        background-color: #ffffff !important;
        color: #111827 !important;
    }
    .stButton > button:hover {
        border-color: #111827 !important;
        background-color: #f9fafb !important;
    }
    .stButton > button:active {
        background-color: #f3f4f6 !important;
    }
    
    /* Primary action buttons */
    div[data-testid="stVerticalBlock"] > div > div > .stButton > button[kind="primary"] {
        background-color: #111827 !important;
        color: #ffffff !important;
        border: 1px solid #111827 !important;
    }

    /* Clean Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 1px solid #e5e7eb;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 4px;
        font-size: 0.9rem;
        font-weight: 500;
        color: #6b7280;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        color: #111827 !important;
        border-bottom: 2px solid #111827 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== CONFIGURATION & ENDPOINTS ====================
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
PUTER_CHAT_URL = "https://api.puter.com/v1/ai/chat"

# ==================== SESSION STATE INIT ====================
if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""
if "df" not in st.session_state:
    st.session_state["df"] = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])

# ==================== BACKEND FUNCTIONS ====================
def transcribe_audio(audio_bytes):
    """Transcribe audio using Groq Whisper model."""
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {
        "file": ("audio.wav", audio_bytes),
        "model": (None, "whisper-large-v3-turbo"),
        "response_format": (None, "json")
    }
    try:
        resp = requests.post(GROQ_URL, headers=headers, files=files, timeout=60)
        if resp.status_code == 200:
            return resp.json().get("text", "")
        else:
            st.error(f"Transcription error ({resp.status_code}): {resp.text}")
            return None
    except Exception as e:
        st.error(f"Transcription request failed: {e}")
        return None

def generate_meeting_minutes(text):
    """Extract key points, action items, and assignees formatted directly as structured JSON."""
    system_prompt = (
        "You are an executive assistant. Extract the critical discussion points, their corresponding "
        "concrete action plans, and assignees from the provided transcript.\n"
        "Return ONLY a valid JSON array of objects without markdown fences or additional explanation. "
        "Each object must strictly have these keys:\n"
        "- \"Key Point\": Concise summary of the decision or discussion point.\n"
        "- \"Action Plan\": Concrete follow-up step (use bullet formats like '• Step 1' or '1. Step 1' if multiple).\n"
        "- \"Assigned\": Person, team, or 'Unassigned'."
    )
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Transcript:\n{text}"}
        ]
    }
    
    try:
        resp = requests.post(PUTER_CHAT_URL, json=payload, timeout=45)
        if resp.status_code == 200:
            result = resp.json()
            if "choices" in result:
                content = result["choices"][0]["message"]["content"].strip()
            elif "response" in result:
                content = result["response"].strip()
            else:
                content = result.get("content", "").strip()

            # Clean markdown codeblocks if returned
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            data = json.loads(content)
            return pd.DataFrame(data)
        else:
            return fallback_parsing(text)
    except Exception:
        return fallback_parsing(text)

def fallback_parsing(text):
    """Rule-based fallback when model response is unavailable or invalid."""
    import re
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    rows = []
    for s in sentences[:4]:
        rows.append({
            "Key Point": s,
            "Action Plan": "• Review discussion notes\n• Confirm next milestone",
            "Assigned": "Team"
        })
    return pd.DataFrame(rows if rows else [{"Key Point": "General Discussion", "Action Plan": "Review recording", "Assigned": "All"}])

def set_cell_margins(cell, top=140, bottom=140, start=160, end=160):
    """Set inner padding for Word table cells (values in dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', start), ('right', end)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def export_to_word(df, transcript):
    """Export formatted document with left-aligned, wrapped-text table formatting."""
    doc = Document()
    
    # Page Setup
    section = doc.sections[0]
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)
    section.page_width = Inches(8.5)
    section.page_height = Inches(11.0)

    # Document Title
    h1 = doc.add_heading("Minutes of the Meeting", level=1)
    h1.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for r in h1.runs:
        r.font.name = "Segoe UI"
        r.font.size = Pt(18)
        r.font.color.rgb = RGBColor(17, 24, 39)

    # Action Items Section
    h2 = doc.add_heading("Key Points & Action Plan", level=2)
    for r in h2.runs:
        r.font.name = "Segoe UI"
        r.font.size = Pt(13)
        r.font.color.rgb = RGBColor(55, 65, 81)

    # Table Layout
    table = doc.add_table(rows=len(df) + 1, cols=3)
    table.autofit = False
    
    col_widths = [Inches(2.5), Inches(2.8), Inches(1.2)]
    headers = ["Key Point", "Action Plan", "Assigned"]
    
    # Header Row
    hdr_row = table.rows[0]
    trPr = hdr_row._tr.get_or_add_trPr()
    trPr.append(parse_xml(r'<w:tblHeader %s/>' % nsdecls('w')))
    
    for idx, name in enumerate(headers):
        cell = hdr_row.cells[idx]
        cell.width = col_widths[idx]
        set_cell_margins(cell, top=180, bottom=180)
        # Background shading
        shading = parse_xml(r'<w:shd {} w:fill="F3F4F6"/>'.format(nsdecls('w')))
        cell._tc.get_or_add_tcPr().append(shading)
        
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(name)
        run.bold = True
        run.font.name = "Segoe UI"
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(17, 24, 39)

    # Data Rows
    for row_idx, data in df.iterrows():
        row_cells = table.rows[row_idx + 1].cells
        for col_idx, col_name in enumerate(headers):
            cell = row_cells[col_idx]
            cell.width = col_widths[col_idx]
            set_cell_margins(cell)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
            
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            text_val = str(data[col_name]) if pd.notna(data[col_name]) else ""
            
            # Handle multi-line bullets/numbers
            lines = text_val.split("\n")
            for l_idx, line in enumerate(lines):
                if l_idx > 0:
                    p = cell.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run = p.add_run(line)
                run.font.name = "Segoe UI"
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(31, 41, 55)

    # Transcript Section
    if transcript:
        doc.add_paragraph().paragraph_format.space_before = Pt(16)
        h3 = doc.add_heading("Full Transcript", level=2)
        for r in h3.runs:
            r.font.name = "Segoe UI"
            r.font.size = Pt(13)
            r.font.color.rgb = RGBColor(55, 65, 81)
            
        p_trans = doc.add_paragraph(transcript)
        p_trans.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for r in p_trans.runs:
            r.font.name = "Segoe UI"
            r.font.size = Pt(8.5)
            r.font.color.rgb = RGBColor(75, 85, 99)

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# ==================== USER INTERFACE ====================
st.markdown('<div class="app-header">Meeting Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Capture, summarize, and structure executive meeting minutes.</div>', unsafe_allow_html=True)

# Input Tabs
tab_record, tab_upload = st.tabs(["Record Audio", "Upload File"])
audio_data = None

with tab_record:
    recorded_audio = st.audio_input("Record Meeting")
    if recorded_audio:
        audio_data = recorded_audio.read()

with tab_upload:
    uploaded_file = st.file_uploader(
        "Upload audio recording",
        type=["wav", "mp3", "m4a", "ogg", "flac", "webm"],
        label_visibility="collapsed"
    )
    if uploaded_file:
        audio_data = uploaded_file.read()

# Action Bar: Transcription
st.write("")
if audio_data:
    if st.button("Transcribe Audio", type="primary"):
        with st.spinner("Processing speech transcription..."):
            transcript_res = transcribe_audio(audio_data)
        if transcript_res:
            st.session_state["transcript"] = transcript_res
            st.session_state["df"] = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])
            st.rerun()

# Transcript & Generation Workspace
if st.session_state["transcript"]:
    st.markdown("---")
    with st.expander("Transcript View", expanded=False):
        st.session_state["transcript"] = st.text_area(
            "Full Transcript",
            st.session_state["transcript"],
            height=130,
            label_visibility="collapsed"
        )
    
    col_gen, col_empty = st.columns([1, 4])
    with col_gen:
        if st.button("Generate Minutes of the Meeting", type="primary"):
            with st.spinner("Analyzing discussion and structuring actions..."):
                generated_df = generate_meeting_minutes(st.session_state["transcript"])
            if not generated_df.empty:
                st.session_state["df"] = generated_df
                st.rerun()

# Editable Table & Actions
if not st.session_state["df"].empty:
    st.markdown("---")
    
    # Helper controls to add bullets or numbered outlines
    col_help1, col_help2, _ = st.columns([1, 1, 4])
    with col_help1:
        if st.button("Add Bullet Template"):
            new_row = pd.DataFrame([{"Key Point": "New discussion item", "Action Plan": "• Sub-task 1\n• Sub-task 2", "Assigned": "Unassigned"}])
            st.session_state["df"] = pd.concat([st.session_state["df"], new_row], ignore_index=True)
            st.rerun()
    with col_help2:
        if st.button("Add Numbered Template"):
            new_row = pd.DataFrame([{"Key Point": "New decision item", "Action Plan": "1. Step one\n2. Step two", "Assigned": "Unassigned"}])
            st.session_state["df"] = pd.concat([st.session_state["df"], new_row], ignore_index=True)
            st.rerun()

    # Data Editor Configuration
    column_config = {
        "Key Point": st.column_config.TextColumn(
            "Key Point",
            help="Summary of the discussed topic or decision",
            required=True,
            width="large"
        ),
        "Action Plan": st.column_config.TextColumn(
            "Action Plan",
            help="Direct actions, bullets (•), or numbered steps (1.)",
            required=False,
            width="large"
        ),
        "Assigned": st.column_config.TextColumn(
            "Assigned",
            help="Owner or department responsible",
            required=False,
            width="medium"
        ),
    }

    edited_df = st.data_editor(
        st.session_state["df"],
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="meeting_editor"
    )
    st.session_state["df"] = edited_df

    # Export Area
    col_exp, _ = st.columns([1, 5])
    with col_exp:
        doc_stream = export_to_word(st.session_state["df"], st.session_state["transcript"])
        st.download_button(
            label="Export Document",
            data=doc_stream,
            file_name="Minutes_of_Meeting.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
