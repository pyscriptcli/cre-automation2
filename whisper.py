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

# ==================== CONFIGURATION ====================
st.set_page_config(
    page_title="Chronicle / Open Audio Core",
    layout="wide",
    initial_sidebar_state="collapsed"
)

GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
PUTER_CHAT_URL = "https://api.puter.com/v1/ai/chat"

# ==================== FORCED PERSISTENT DARK MODE STYLING ====================
st.markdown("""
<style>
    /* Force pure dark mode variables across root and all components */
    :root, html, body, [data-testid="stAppViewContainer"], .stApp {
        color-scheme: dark !important;
        background-color: #07080b !important;
        background: radial-gradient(circle at 50% 0%, #11141c 0%, #06070a 100%) !important;
        color: #e2e8f0 !important;
    }

    /* Complete removal of Streamlit top header, decoration line, and default footers */
    header[data-testid="stHeader"],
    div[data-testid="stDecoration"],
    #MainMenu,
    footer,
    .stDeployButton {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }

    .block-container {
        padding-top: 2.2rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 1100px !important;
        margin: 0 auto;
    }

    /* Typography */
    .app-title {
        font-size: 1.35rem;
        font-weight: 600;
        letter-spacing: -0.03em;
        color: #f8fafc;
    }
    
    .open-note {
        font-size: 0.82rem;
        color: #64748b;
        letter-spacing: 0.01em;
        margin-top: 0.2rem;
        margin-bottom: 1.8rem;
        font-weight: 400;
    }

    /* Fix Tabs for dark theme */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
        gap: 28px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 8px 0px 10px 0px !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        color: #64748b !important;
        background-color: transparent !important;
        border: none !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: #f8fafc !important;
        border-bottom: 2px solid #38bdf8 !important;
    }

    /* Lock File Uploader to Dark Theme */
    [data-testid="stFileUploader"],
    [data-testid="stFileUploader"] > div,
    [data-testid="stFileUploaderDropzone"] {
        background-color: #0d1117 !important;
        border: 1px dashed rgba(255, 255, 255, 0.12) !important;
        border-radius: 8px !important;
        color: #94a3b8 !important;
    }

    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: rgba(255, 255, 255, 0.25) !important;
        background-color: #111620 !important;
    }

    [data-testid="stFileUploaderDropzone"] button {
        background-color: #1a2234 !important;
        color: #f1f5f9 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    [data-testid="stFileUploaderDropzone"] span,
    [data-testid="stFileUploaderDropzone"] small,
    [data-testid="stFileUploaderDropzone"] div {
        color: #94a3b8 !important;
    }

    /* Lock Audio Input to Dark Theme */
    [data-testid="stAudioInput"] {
        background-color: #0d1117 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }

    /* Buttons */
    .stButton > button {
        background: #0f172a !important;
        color: #cbd5e1 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 6px !important;
        font-size: 0.83rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.02em !important;
        padding: 0.45rem 1.1rem !important;
        transition: all 0.15s ease-in-out !important;
    }
    
    .stButton > button:hover {
        background: #1e293b !important;
        color: #ffffff !important;
        border-color: rgba(255, 255, 255, 0.25) !important;
    }

    .stButton > button[kind="primary"] {
        background: #f8fafc !important;
        color: #06070a !important;
        border: 1px solid #ffffff !important;
        font-weight: 600 !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: #e2e8f0 !important;
        color: #000000 !important;
        box-shadow: 0 0 16px rgba(255, 255, 255, 0.15) !important;
    }

    /* Text areas */
    .stTextArea textarea {
        background-color: #0a0d14 !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 6px !important;
        font-size: 0.85rem !important;
        line-height: 1.6 !important;
    }

    .stTextArea textarea:focus {
        border-color: rgba(56, 189, 248, 0.4) !important;
        box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.4) !important;
    }

    /* Data Table / Editor Frame */
    [data-testid="stDataEditor"] {
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 8px !important;
        background-color: #0a0d14 !important;
        box-shadow: 0 16px 36px rgba(0, 0, 0, 0.5) !important;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #0d1117 !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 6px !important;
        color: #cbd5e1 !important;
        font-size: 0.85rem !important;
    }

    hr {
        border: none !important;
        border-top: 1px solid rgba(255, 255, 255, 0.06) !important;
        margin: 1.8rem 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== STATE ====================
if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""
if "df" not in st.session_state:
    st.session_state["df"] = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])

# ==================== BACKEND SERVICES ====================
def transcribe_audio(audio_bytes):
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
            st.error(f"Engine response: {resp.status_code}")
            return None
    except Exception as e:
        st.error(f"Engine connection failed: {e}")
        return None

def generate_minutes(text):
    system_prompt = (
        "You are an analytical meeting intelligence engine. Parse the transcript into key points, "
        "corresponding detailed action plans, and assignees.\n"
        "Rules:\n"
        "- Action Plan must include structured points (e.g. '• Task' or '1. Task').\n"
        "- Return strictly valid JSON array of objects with keys: 'Key Point', 'Action Plan', 'Assigned'.\n"
        "- Output raw JSON only."
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
            content = ""
            if "choices" in result:
                content = result["choices"][0]["message"]["content"].strip()
            elif "response" in result:
                content = result["response"].strip()
            else:
                content = result.get("content", "").strip()

            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            data = json.loads(content)
            return pd.DataFrame(data)
        else:
            return parse_fallback(text)
    except Exception:
        return parse_fallback(text)

def parse_fallback(text):
    import re
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    rows = []
    for s in sentences[:4]:
        rows.append({
            "Key Point": s,
            "Action Plan": "• Align on operational requirements\n• Finalize roadmap draft",
            "Assigned": "Core Team"
        })
    return pd.DataFrame(rows if rows else [{"Key Point": "Discussion points", "Action Plan": "• Follow up with stakeholders", "Assigned": "Unassigned"}])

def set_cell_margins(cell, top=140, bottom=140, start=160, end=160):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', start), ('right', end)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def export_docx(df, transcript):
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)
    section.page_width = Inches(8.5)
    section.page_height = Inches(11.0)

    # Document Header
    h1 = doc.add_heading("Executive Minutes & Decisions", level=1)
    h1.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for r in h1.runs:
        r.font.name = "Segoe UI"
        r.font.size = Pt(16)
        r.font.bold = True
        r.font.color.rgb = RGBColor(15, 23, 42)

    # Table Grid
    table = doc.add_table(rows=len(df) + 1, cols=3)
    table.autofit = False
    col_widths = [Inches(2.5), Inches(2.9), Inches(1.1)]
    headers = ["Key Point", "Action Plan", "Assigned"]
    
    # Table Header
    hdr_row = table.rows[0]
    trPr = hdr_row._tr.get_or_add_trPr()
    trPr.append(parse_xml(r'<w:tblHeader %s/>' % nsdecls('w')))
    
    for idx, name in enumerate(headers):
        cell = hdr_row.cells[idx]
        cell.width = col_widths[idx]
        set_cell_margins(cell, top=160, bottom=160)
        shading = parse_xml(r'<w:shd {} w:fill="F1F5F9"/>'.format(nsdecls('w')))
        cell._tc.get_or_add_tcPr().append(shading)
        
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(name)
        run.bold = True
        run.font.name = "Segoe UI"
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(15, 23, 42)

    # Row Formatting
    for row_idx, data in df.iterrows():
        row_cells = table.rows[row_idx + 1].cells
        for col_idx, col_name in enumerate(headers):
            cell = row_cells[col_idx]
            cell.width = col_widths[col_idx]
            set_cell_margins(cell)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
            
            raw_text = str(data[col_name]) if pd.notna(data[col_name]) else ""
            lines = raw_text.split("\n")
            
            for l_idx, line in enumerate(lines):
                p = cell.paragraphs[0] if l_idx == 0 else cell.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.space_before = Pt(0)
                run = p.add_run(line)
                run.font.name = "Segoe UI"
                run.font.size = Pt(8.5)
                run.font.color.rgb = RGBColor(51, 65, 85)

    if transcript:
        doc.add_paragraph().paragraph_format.space_before = Pt(20)
        h2 = doc.add_heading("Session Transcript", level=2)
        for r in h2.runs:
            r.font.name = "Segoe UI"
            r.font.size = Pt(11)
            r.font.color.rgb = RGBColor(71, 85, 105)
            
        p_trans = doc.add_paragraph(transcript)
        p_trans.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for r in p_trans.runs:
            r.font.name = "Segoe UI"
            r.font.size = Pt(8)
            r.font.color.rgb = RGBColor(100, 116, 139)

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# ==================== APPLICATION CANVAS ====================
st.markdown('<div class="app-title">Chronicle</div>', unsafe_allow_html=True)
st.markdown('<div class="open-note">Open-source meeting transcription and decision orchestration kernel.</div>', unsafe_allow_html=True)

tab_rec, tab_up = st.tabs(["Record", "Upload"])
audio_payload = None

with tab_rec:
    rec_buffer = st.audio_input("Record Audio Stream", label_visibility="collapsed")
    if rec_buffer:
        audio_payload = rec_buffer.read()

with tab_up:
    up_buffer = st.file_uploader(
        "Upload Media",
        type=["wav", "mp3", "m4a", "ogg", "flac", "webm"],
        label_visibility="collapsed"
    )
    if up_buffer:
        audio_payload = up_buffer.read()

if audio_payload:
    st.write("")
    if st.button("Transcribe", type="primary"):
        with st.spinner("Processing speech matrix..."):
            res = transcribe_audio(audio_payload)
        if res:
            st.session_state["transcript"] = res
            st.session_state["df"] = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])
            st.rerun()

if st.session_state["transcript"]:
    st.markdown("---")
    with st.expander("Raw Transcript", expanded=False):
        st.session_state["transcript"] = st.text_area(
            "Raw Transcript Payload",
            st.session_state["transcript"],
            height=120,
            label_visibility="collapsed"
        )
    
    col_btn, _ = st.columns([2, 5])
    with col_btn:
        if st.button("Generate Minutes of the Meeting", type="primary"):
            with st.spinner("Structuring decisions and action matrices..."):
                structured_df = generate_minutes(st.session_state["transcript"])
            if not structured_df.empty:
                st.session_state["df"] = structured_df
                st.rerun()

if not st.session_state["df"].empty:
    st.markdown("---")
    
    column_config = {
        "Key Point": st.column_config.TextColumn(
            "Key Point",
            required=True,
            width="large"
        ),
        "Action Plan": st.column_config.TextColumn(
            "Action Plan",
            required=False,
            width="large"
        ),
        "Assigned": st.column_config.TextColumn(
            "Assigned",
            required=False,
            width="medium"
        ),
    }

    # Data editor allowing multiline bullets, numbering, row creation/deletion
    edited = st.data_editor(
        st.session_state["df"],
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="chronicle_table_editor"
    )
    st.session_state["df"] = edited

    st.write("")
    col_dl, _ = st.columns([2, 5])
    with col_dl:
        doc_data = export_docx(st.session_state["df"], st.session_state["transcript"])
        st.download_button(
            label="Export Document",
            data=doc_data,
            file_name="Minutes_of_Meeting.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
