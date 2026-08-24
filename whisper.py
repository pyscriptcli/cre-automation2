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
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ==================== STREAMLIT CONFIGURATION ====================
st.set_page_config(
    page_title="Project Eco",
    layout="wide",
    initial_sidebar_state="collapsed"
)

GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
PUTER_CHAT_URL = "https://api.puter.com/v1/ai/chat"

# ==================== ADVANCED DARK MODE iOS / GLASSMORPHIC UI ====================
st.markdown("""
<style>
    /* Full Viewport Reset & Smooth Antialiasing */
    :root, html, body, [data-testid="stAppViewContainer"], .stApp {
        color-scheme: dark !important;
        background-color: #07080b !important;
        background-image: 
            linear-gradient(to right, rgba(255, 255, 255, 0.028) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.028) 1px, transparent 1px) !important;
        background-size: 52px 52px !important;
        color: #f1f5f9 !important;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", Roboto, Helvetica, sans-serif !important;
        -webkit-font-smoothing: antialiased;
        letter-spacing: -0.01em;
    }

    /* Remove Streamlit Header / Status / Footers */
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
        padding-top: 2.8rem !important;
        padding-bottom: 4rem !important;
        max-width: 1060px !important;
        margin: 0 auto;
    }

    /* iOS Glassmorphic Panel Cards */
    .ios-card {
        background: rgba(22, 26, 35, 0.65);
        backdrop-filter: blur(28px) saturate(190%);
        -webkit-backdrop-filter: blur(28px) saturate(190%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        border-radius: 18px;
        padding: 22px 24px;
        margin-bottom: 1.25rem;
    }

    /* Header & Badge Styling */
    .header-group {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 4px;
    }

    .app-title {
        font-size: 1.55rem;
        font-weight: 700;
        letter-spacing: -0.035em;
        color: #ffffff;
    }
    
    .app-badge {
        background: rgba(16, 185, 129, 0.12);
        color: #34d399;
        font-size: 0.68rem;
        padding: 3px 9px;
        border-radius: 20px;
        font-weight: 600;
        border: 1px solid rgba(16, 185, 129, 0.28);
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    
    .open-note {
        font-size: 0.85rem;
        color: #8b949e;
        letter-spacing: 0.01em;
        margin-bottom: 2rem;
        font-weight: 400;
    }

    /* iOS Segmented Pill Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(15, 18, 26, 0.7) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        padding: 4px !important;
        gap: 4px !important;
        width: fit-content;
        margin-bottom: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 6px 20px !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        color: #8b949e !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 8px !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        background: rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35) !important;
        border-bottom: none !important;
    }

    /* Clean Dark Audio Recorder / Uploader */
    [data-testid="stAudioInput"] {
        background: rgba(18, 22, 31, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
        padding: 10px 16px !important;
        backdrop-filter: blur(20px) !important;
    }

    [data-testid="stFileUploader"],
    [data-testid="stFileUploader"] > div,
    [data-testid="stFileUploaderDropzone"] {
        background-color: rgba(18, 22, 31, 0.5) !important;
        border: 1px dashed rgba(255, 255, 255, 0.14) !important;
        border-radius: 14px !important;
        color: #94a3b8 !important;
        backdrop-filter: blur(20px) !important;
    }

    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #10b981 !important;
        background-color: rgba(24, 30, 42, 0.65) !important;
    }

    [data-testid="stFileUploaderDropzone"] button {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #f1f5f9 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }

    [data-testid="stFileUploaderDropzone"] span,
    [data-testid="stFileUploaderDropzone"] small,
    [data-testid="stFileUploaderDropzone"] div {
        color: #8b949e !important;
    }

    /* iOS Precision Tactile Buttons */
    .stButton > button {
        background: rgba(255, 255, 255, 0.06) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        font-size: 0.84rem !important;
        font-weight: 500 !important;
        letter-spacing: -0.01em !important;
        padding: 0.5rem 1.25rem !important;
        backdrop-filter: blur(16px);
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    
    .stButton > button:hover {
        background: rgba(255, 255, 255, 0.12) !important;
        border-color: rgba(255, 255, 255, 0.22) !important;
        color: #ffffff !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(180deg, #10b981 0%, #059669 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        box-shadow: 0 4px 18px rgba(16, 185, 129, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
        font-weight: 600 !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(180deg, #34d399 0%, #059669 100%) !important;
        box-shadow: 0 6px 24px rgba(16, 185, 129, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.4) !important;
        transform: translateY(-1px);
    }

    /* Fully Darkened & Border-Free Expander Container */
    .streamlit-expanderHeader {
        background-color: rgba(18, 22, 31, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        backdrop-filter: blur(20px) !important;
    }

    /* Pure Dark Streamlit Data Editor */
    [data-testid="stDataEditor"] {
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
        background-color: rgba(14, 17, 24, 0.95) !important;
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.65), inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
        overflow: hidden !important;
    }

    .stTextArea textarea {
        background-color: rgba(14, 17, 24, 0.8) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        font-size: 0.86rem !important;
        line-height: 1.65 !important;
        backdrop-filter: blur(16px);
    }

    .stTextArea textarea:focus {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 1px #10b981 !important;
    }

    hr {
        border: none !important;
        border-top: 1px solid rgba(255, 255, 255, 0.07) !important;
        margin: 1.8rem 0 !important;
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
            st.error(f"Engine status: {resp.status_code}")
            return None
    except Exception as e:
        st.error(f"Transcription error: {e}")
        return None

def generate_minutes(text):
    system_prompt = (
        "You are an executive intelligence engine for Project Eco. Thoroughly analyze the meeting transcript "
        "and produce a comprehensive breakdown of key points, actionable plans, and assignees.\n\n"
        "Output Format Rules:\n"
        "- Return ONLY a valid JSON array of objects.\n"
        "- Schema: [{\"Key Point\": \"...\", \"Action Plan\": \"...\", \"Assigned\": \"...\"}]\n"
        "- 'Action Plan' should contain multiline bullet points (•) or numbers (1., 2.) where appropriate.\n"
        "- Accurately capture specific names, teams, and deliverables mentioned in the audio.\n"
        "- Do not include markdown ticks (```json), commentary, or extra keys."
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
            "Action Plan": "• Align deliverables with project scope\n• Execute milestone tracking",
            "Assigned": "Project Team"
        })
    return pd.DataFrame(rows if rows else [{"Key Point": "Discussion points", "Action Plan": "• Conduct follow-up review", "Assigned": "Unassigned"}])

# ==================== EXPORT UTILITIES ====================
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

    # Document Title
    h1 = doc.add_heading("PROJECT ECO // MINUTES OF THE MEETING", level=1)
    h1.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for r in h1.runs:
        r.font.name = "Segoe UI"
        r.font.size = Pt(15)
        r.font.bold = True
        r.font.color.rgb = RGBColor(16, 185, 129)

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
        shading = parse_xml(r'<w:shd {} w:fill="181B22"/>'.format(nsdecls('w')))
        cell._tc.get_or_add_tcPr().append(shading)
        
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(name)
        run.bold = True
        run.font.name = "Segoe UI"
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(255, 255, 255)

    # Table Body
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
                run.font.color.rgb = RGBColor(30, 41, 59)

    if transcript:
        doc.add_paragraph().paragraph_format.space_before = Pt(20)
        h2 = doc.add_heading("Session Transcript", level=2)
        for r in h2.runs:
            r.font.name = "Segoe UI"
            r.font.size = Pt(11)
            r.font.color.rgb = RGBColor(16, 185, 129)
            
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

def export_pdf(df, transcript):
    bio = BytesIO()
    doc = SimpleDocTemplate(
        bio,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        textColor=colors.HexColor('#10B981'),
        spaceAfter=14
    )
    section_style = ParagraphStyle(
        'DocSection',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=colors.HexColor('#10B981'),
        spaceBefore=14,
        spaceAfter=8
    )
    header_cell_style = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        textColor=colors.white
    )
    body_cell_style = ParagraphStyle(
        'BodyCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#1F2937')
    )
    transcript_style = ParagraphStyle(
        'TranscriptText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor('#4B5563')
    )
    
    story = [Paragraph("PROJECT ECO // MINUTES OF THE MEETING", title_style)]
    
    table_data = [[
        Paragraph("Key Point", header_cell_style),
        Paragraph("Action Plan", header_cell_style),
        Paragraph("Assigned", header_cell_style)
    ]]
    
    for _, row in df.iterrows():
        kp_text = str(row["Key Point"]).replace('\n', '<br/>') if pd.notna(row["Key Point"]) else ""
        ap_text = str(row["Action Plan"]).replace('\n', '<br/>') if pd.notna(row["Action Plan"]) else ""
        as_text = str(row["Assigned"]).replace('\n', '<br/>') if pd.notna(row["Assigned"]) else ""
        
        table_data.append([
            Paragraph(kp_text, body_cell_style),
            Paragraph(ap_text, body_cell_style),
            Paragraph(as_text, body_cell_style)
        ])
        
    t = Table(table_data, colWidths=[185, 230, 89])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#181B22')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
    ]))
    story.append(t)
    
    if transcript:
        story.append(Spacer(1, 14))
        story.append(Paragraph("Session Transcript", section_style))
        story.append(Paragraph(transcript.replace('\n', '<br/>'), transcript_style))
        
    doc.build(story)
    bio.seek(0)
    return bio

# ==================== APPLICATION CANVAS ====================
st.markdown("""
    <div class="header-group">
        <div class="app-title">Project Eco</div>
        <span class="app-badge">PRIME CORE</span>
    </div>
    <div class="open-note">Open architecture for intelligence capture, structured directives, and operational agility.</div>
""", unsafe_allow_html=True)

# Input Section Card
tab_rec, tab_up = st.tabs(["Record", "Upload"])
audio_payload = None

with tab_rec:
    rec_buffer = st.audio_input("Record Audio Stream", label_visibility="collapsed")
    if rec_buffer:
        audio_payload = rec_buffer.read()

with tab_up:
    up_buffer = st.file_uploader(
        "Upload Audio",
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

# Workspace Section Card
if st.session_state["transcript"]:
    st.markdown("---")
    with st.expander("Session Transcript", expanded=False):
        st.session_state["transcript"] = st.text_area(
            "Session Transcript",
            st.session_state["transcript"],
            height=120,
            label_visibility="collapsed"
        )
    
    col_btn, _ = st.columns([2.5, 4.5])
    with col_btn:
        if st.button("Generate Minutes of the Meeting", type="primary"):
            with st.spinner("Compiling decisions and execution matrix..."):
                structured_df = generate_minutes(st.session_state["transcript"])
            if not structured_df.empty:
                st.session_state["df"] = structured_df
                st.rerun()

# Matrix Editor & Exports
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

    edited = st.data_editor(
        st.session_state["df"],
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="project_eco_editor"
    )
    st.session_state["df"] = edited

    st.write("")
    col_word, col_pdf, _ = st.columns([1.5, 1.5, 4])
    
    with col_word:
        doc_data = export_docx(st.session_state["df"], st.session_state["transcript"])
        st.download_button(
            label="Export Word",
            data=doc_data,
            file_name="Project_Eco_Minutes.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    with col_pdf:
        pdf_data = export_pdf(st.session_state["df"], st.session_state["transcript"])
        st.download_button(
            label="Export PDF",
            data=pdf_data,
            file_name="Project_Eco_Minutes.pdf",
            mime="application/pdf"
        )
