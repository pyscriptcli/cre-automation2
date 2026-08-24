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

# ==================== CORE CONFIGURATION ====================
st.set_page_config(
    page_title="Chronicle / Open Audio Core",
    layout="wide",
    initial_sidebar_state="collapsed"
)

GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
PUTER_CHAT_URL = "https://api.puter.com/v1/ai/chat"

# ==================== SOPHISTICATED DARK DESIGN SYSTEM ====================
st.markdown("""
<style>
    /* Full viewport reset & removal of default Streamlit top bar/footer */
    header[data-testid="stHeader"], footer, #MainMenu, .stDeployButton {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Background Canvas */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #14161b 0%, #090a0f 100%) !important;
        color: #e2e8f0;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", "Segoe UI", Roboto, sans-serif;
    }

    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 1100px !important;
        margin: 0 auto;
    }

    /* Minimal Header Typography */
    .app-title {
        font-size: 1.35rem;
        font-weight: 600;
        letter-spacing: -0.03em;
        color: #f8fafc;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .open-note {
        font-size: 0.82rem;
        color: #64748b;
        letter-spacing: 0.01em;
        margin-top: 0.15rem;
        font-weight: 400;
    }

    /* Architectural Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        gap: 32px;
        padding-bottom: 0px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 8px 0px 12px 0px;
        font-size: 0.84rem;
        font-weight: 500;
        letter-spacing: 0.02em;
        color: #64748b;
        background-color: transparent !important;
        border: none !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: #f1f5f9 !important;
        border-bottom: 2px solid #38bdf8 !important;
    }

    /* Precision Buttons */
    .stButton > button {
        background: #0f172a !important;
        color: #cbd5e1 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 6px !important;
        font-size: 0.83rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.02em !important;
        padding: 0.45rem 1.1rem !important;
        transition: all 0.18s ease-in-out !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
    }
    
    .stButton > button:hover {
        background: #1e293b !important;
        color: #ffffff !important;
        border-color: rgba(255, 255, 255, 0.25) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6);
    }

    .stButton > button[kind="primary"] {
        background: #f8fafc !important;
        color: #090a0f !important;
        border: 1px solid #ffffff !important;
        font-weight: 600 !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: #e2e8f0 !important;
        color: #000000 !important;
        box-shadow: 0 0 16px rgba(255, 255, 255, 0.15) !important;
    }

    /* Data Table Custom Glassmorphism Frame */
    [data-testid="stDataEditor"] {
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 8px;
        background: #0b0f17;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45);
        overflow: hidden;
    }

    /* Ensure textareas/inputs match dark tone */
    .stTextArea textarea {
        background-color: #0b0f17 !important;
        color: #cbd5e1 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 6px !important;
        font-size: 0.85rem !important;
        line-height: 1.6 !important;
        white-space: pre-wrap !important;
    }

    .stTextArea textarea:focus {
        border-color: rgba(56, 189, 248, 0.4) !important;
        box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.4) !important;
    }

    /* Divider */
    hr {
        border: none;
        border-top: 1px solid rgba(255, 255, 255, 0.06) !important;
        margin: 2rem 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== STATE MANAGEMENT ====================
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
            st.error(f"Transcription failure: {resp.status_code}")
            return None
    except Exception as e:
        st.error(f"Engine connection failed: {e}")
        return None

def generate_minutes(text):
    system_prompt = (
        "You are an analytical meeting intelligence engine. Parse the discussion transcript "
        "and produce a structured list of key decisions/points, concrete action steps, and assignees.\n"
        "Rules:\n"
        "- Action plans should naturally support multiline lists (bullets with '•' or numbers '1.', '2.').\n"
        "- Output strictly valid JSON matching this schema: "
        "[{\"Key Point\": \"...\", \"Action Plan\": \"...\", \"Assigned\": \"...\"}].\n"
        "- Do not wrap inside code block notations if possible, or provide raw JSON only."
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

    # Rows formatting
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

# ==================== INTERFACE ====================
st.markdown('<div class="app-title">Chronicle</div>', unsafe_allow_html=True)
st.markdown('<div class="open-note">Open-source meeting transcription and decision orchestration kernel.</div>', unsafe_allow_html=True)

st.write("")

# Input Section
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

# Action trigger
if audio_payload:
    st.write("")
    if st.button("Transcribe", type="primary"):
        with st.spinner("Processing speech matrix..."):
            res = transcribe_audio(audio_payload)
        if res:
            st.session_state["transcript"] = res
            st.session_state["df"] = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])
            st.rerun()

# Processing workspace
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
            with st.spinner("Structuring discussions and action matrices..."):
                structured_df = generate_minutes(st.session_state["transcript"])
            if not structured_df.empty:
                st.session_state["df"] = structured_df
                st.rerun()

# Structured Matrix Editor
if not st.session_state["df"].empty:
    st.markdown("---")
    
    column_config = {
        "Key Point": st.column_config.TextColumn(
            "Key Point",
            help="Discussion core item (supports wrapped multiline text)",
            required=True,
            width="large"
        ),
        "Action Plan": st.column_config.TextColumn(
            "Action Plan",
            help="Direct actions, bullets, or numbered lists (supports wrapped multiline text)",
            required=False,
            width="large"
        ),
        "Assigned": st.column_config.TextColumn(
            "Assigned",
            help="Designated owner or system",
            required=False,
            width="medium"
        ),
    }

    # Data editor supporting full wrapped dynamic text editing, row insertion, and deletions
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
