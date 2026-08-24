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

# ==================== CORE CONFIGURATION ====================
st.set_page_config(
    page_title="Project Eco / Meeting Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

GROQ_API_KEY = "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"[cite: 1]
GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"[cite: 1]
PUTER_CHAT_URL = "https://api.puter.com/v1/ai/chat"[cite: 1]

# ==================== PROJECT ECO / PRIME PHILIPPINES DESIGN SYSTEM ====================
# Uses Prime Philippines signature corporate tones: Deep Obsidian, Subtle Grid Canvas, Emerald Accent (#10B981)
st.markdown("""
<style>
    /* Global Reset & Grid Background */
    :root, html, body, [data-testid="stAppViewContainer"], .stApp {
        color-scheme: dark !important;
        background-color: #121316 !important;
        background-image: 
            linear-gradient(to right, rgba(255, 255, 255, 0.035) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.035) 1px, transparent 1px) !important;
        background-size: 48px 48px !important;
        color: #e5e7eb !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    /* Complete removal of default headers & decoration */
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
        font-size: 1.4rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .app-badge {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        font-size: 0.65rem;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
        border: 1px solid rgba(16, 185, 129, 0.3);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .open-note {
        font-size: 0.82rem;
        color: #9ca3af;
        letter-spacing: 0.01em;
        margin-top: 0.25rem;
        margin-bottom: 1.8rem;
        font-weight: 400;
    }

    /* Architectural Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
        gap: 28px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 8px 0px 12px 0px !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        color: #6b7280 !important;
        background-color: transparent !important;
        border: none !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        border-bottom: 2px solid #10b981 !important;
    }

    /* Dark Grid-Aligned File Uploader */
    [data-testid="stFileUploader"],
    [data-testid="stFileUploader"] > div,
    [data-testid="stFileUploaderDropzone"] {
        background-color: rgba(18, 20, 26, 0.85) !important;
        border: 1px dashed rgba(255, 255, 255, 0.12) !important;
        border-radius: 6px !important;
        color: #9ca3af !important;
        backdrop-filter: blur(8px);
    }

    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #10b981 !important;
        background-color: rgba(24, 27, 35, 0.9) !important;
    }

    [data-testid="stFileUploaderDropzone"] button {
        background-color: #1f2430 !important;
        color: #f3f4f6 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 4px !important;
    }

    [data-testid="stFileUploaderDropzone"] span,
    [data-testid="stFileUploaderDropzone"] small,
    [data-testid="stFileUploaderDropzone"] div {
        color: #9ca3af !important;
    }

    /* Audio Input Frame */
    [data-testid="stAudioInput"] {
        background-color: rgba(18, 20, 26, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 6px !important;
        padding: 12px !important;
        backdrop-filter: blur(8px);
    }

    /* Solid Precision Buttons */
    .stButton > button {
        background: #181b22 !important;
        color: #e5e7eb !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 4px !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.02em !important;
        padding: 0.45rem 1.1rem !important;
        transition: all 0.15s ease-in-out !important;
    }
    
    .stButton > button:hover {
        background: #232834 !important;
        color: #ffffff !important;
        border-color: rgba(255, 255, 255, 0.25) !important;
    }

    .stButton > button[kind="primary"] {
        background: #10b981 !important;
        color: #060709 !important;
        border: 1px solid #10b981 !important;
        font-weight: 600 !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: #059669 !important;
        border-color: #059669 !important;
        color: #ffffff !important;
        box-shadow: 0 0 16px rgba(16, 185, 129, 0.3) !important;
    }

    /* Text Inputs & Areas */
    .stTextArea textarea {
        background-color: #141720 !important;
        color: #e5e7eb !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 6px !important;
        font-size: 0.85rem !important;
        line-height: 1.6 !important;
    }

    .stTextArea textarea:focus {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 1px #10b981 !important;
    }

    /* Data Editor Glass Table */
    [data-testid="stDataEditor"] {
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 6px !important;
        background-color: #141720 !important;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.5) !important;
    }

    .streamlit-expanderHeader {
        background-color: rgba(18, 20, 26, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 4px !important;
        color: #d1d5db !important;
        font-size: 0.84rem !important;
    }

    hr {
        border: none !important;
        border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
        margin: 1.8rem 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== STATE MANAGEMENT ====================
if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""
if "df" not in st.session_state:
    st.session_state["df"] = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])

# ==================== ENGINE BACKENDS ====================
def transcribe_audio(audio_bytes):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}[cite: 1]
    files = {
        "file": ("audio.wav", audio_bytes),[cite: 1]
        "model": (None, "whisper-large-v3-turbo"),[cite: 1]
        "response_format": (None, "json")[cite: 1]
    }
    try:
        resp = requests.post(GROQ_URL, headers=headers, files=files, timeout=60)[cite: 1]
        if resp.status_code == 200:[cite: 1]
            return resp.json().get("text", "")[cite: 1]
        else:
            st.error(f"Engine status: {resp.status_code}")
            return None
    except Exception as e:
        st.error(f"Transcription error: {e}")
        return None

def generate_minutes(text):
    system_prompt = (
        "You are an executive meeting intelligence engine for Project Eco. Parse the transcript into key points, "
        "corresponding detailed action plans, and assignees.\n"
        "Rules:\n"
        "- Action Plan must cleanly format multiline lists (bullets with '•' or numbering '1.', '2.').\n"
        "- Output strictly a JSON array of objects with keys: 'Key Point', 'Action Plan', 'Assigned'.\n"
        "- Output raw JSON only."
    )
    
    payload = {
        "model": "gpt-4o-mini",[cite: 1]
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Transcript:\n{text}"}[cite: 1]
        ]
    }
    
    try:
        resp = requests.post(PUTER_CHAT_URL, json=payload, timeout=45)[cite: 1]
        if resp.status_code == 200:[cite: 1]
            result = resp.json()[cite: 1]
            content = ""
            if "choices" in result:[cite: 1]
                content = result["choices"][0]["message"]["content"].strip()[cite: 1]
            elif "response" in result:[cite: 1]
                content = result["response"].strip()[cite: 1]
            else:
                content = result.get("content", "").strip()[cite: 1]

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
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()][cite: 1]
    rows = []
    for s in sentences[:4]:
        rows.append({
            "Key Point": s,
            "Action Plan": "• Align with project milestones\n• Execute operational review",
            "Assigned": "Project Team"
        })
    return pd.DataFrame(rows if rows else [{"Key Point": "Strategic Directives", "Action Plan": "• Follow up on agenda items", "Assigned": "Unassigned"}])

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
    section = doc.sections[0][cite: 1]
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)
    section.page_width = Inches(8.5)[cite: 1]
    section.page_height = Inches(11.0)[cite: 1]

    # Header
    h1 = doc.add_heading("PROJECT ECO // MINUTES OF THE MEETING", level=1)
    h1.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for r in h1.runs:
        r.font.name = "Segoe UI"
        r.font.size = Pt(15)
        r.font.bold = True
        r.font.color.rgb = RGBColor(16, 185, 129)

    table = doc.add_table(rows=len(df) + 1, cols=3)[cite: 1]
    table.autofit = False
    col_widths = [Inches(2.5), Inches(2.9), Inches(1.1)]
    headers = ["Key Point", "Action Plan", "Assigned"][cite: 1]
    
    # Table Header
    hdr_row = table.rows[0][cite: 1]
    trPr = hdr_row._tr.get_or_add_trPr()
    trPr.append(parse_xml(r'<w:tblHeader %s/>' % nsdecls('w')))
    
    for idx, name in enumerate(headers):
        cell = hdr_row.cells[idx][cite: 1]
        cell.width = col_widths[idx]
        set_cell_margins(cell, top=160, bottom=160)
        shading = parse_xml(r'<w:shd {} w:fill="181B22"/>'.format(nsdecls('w')))
        cell._tc.get_or_add_tcPr().append(shading)
        
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(name)[cite: 1]
        run.bold = True
        run.font.name = "Segoe UI"
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(255, 255, 255)

    # Table Body
    for row_idx, data in df.iterrows():[cite: 1]
        row_cells = table.rows[row_idx + 1].cells[cite: 1]
        for col_idx, col_name in enumerate(headers):
            cell = row_cells[col_idx][cite: 1]
            cell.width = col_widths[col_idx]
            set_cell_margins(cell)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
            
            raw_text = str(data[col_name]) if pd.notna(data[col_name]) else ""[cite: 1]
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
        h2 = doc.add_heading("Session Transcript", level=2)[cite: 1]
        for r in h2.runs:
            r.font.name = "Segoe UI"
            r.font.size = Pt(11)
            r.font.color.rgb = RGBColor(16, 185, 129)
            
        p_trans = doc.add_paragraph(transcript)[cite: 1]
        p_trans.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for r in p_trans.runs:
            r.font.name = "Segoe UI"
            r.font.size = Pt(8)
            r.font.color.rgb = RGBColor(100, 116, 139)

    bio = BytesIO()[cite: 1]
    doc.save(bio)[cite: 1]
    bio.seek(0)[cite: 1]
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
        kp_text = str(row["Key Point"]).replace('\n', '<br/>') if pd.notna(row["Key Point"]) else ""[cite: 1]
        ap_text = str(row["Action Plan"]).replace('\n', '<br/>') if pd.notna(row["Action Plan"]) else ""[cite: 1]
        as_text = str(row["Assigned"]).replace('\n', '<br/>') if pd.notna(row["Assigned"]) else ""[cite: 1]
        
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
    <div class="app-title">
        Project Eco <span class="app-badge">PRIME CORE</span>
    </div>
    <div class="open-note">Open architecture for intelligence capture, structured directives, and operational agility.</div>
""", unsafe_allow_html=True)

tab_rec, tab_up = st.tabs(["Record", "Upload"])
audio_payload = None

with tab_rec:
    rec_buffer = st.audio_input("Record Audio Stream", label_visibility="collapsed")
    if rec_buffer:
        audio_payload = rec_buffer.read()

with tab_up:
    up_buffer = st.file_uploader(
        "Upload Audio",
        type=["wav", "mp3", "m4a", "ogg", "flac", "webm"],[cite: 1]
        label_visibility="collapsed"
    )
    if up_buffer:
        audio_payload = up_buffer.read()[cite: 1]

if audio_payload:
    st.write("")
    if st.button("Transcribe", type="primary"):
        with st.spinner("Processing speech matrix..."):
            res = transcribe_audio(audio_payload)
        if res:
            st.session_state["transcript"] = res[cite: 1]
            st.session_state["df"] = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])[cite: 1]
            st.rerun()[cite: 1]

if st.session_state["transcript"]:
    st.markdown("---")
    with st.expander("Session Transcript", expanded=False):
        st.session_state["transcript"] = st.text_area(
            "Session Transcript",
            st.session_state["transcript"],[cite: 1]
            height=120,
            label_visibility="collapsed"
        )
    
    col_btn, _ = st.columns([2, 5])
    with col_btn:
        if st.button("Generate Minutes of the Meeting", type="primary"):
            with st.spinner("Compiling decisions and execution matrix..."):
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

    # Data editor supporting full wrapped multiline text editing, row insertion, and deletions
    edited = st.data_editor(
        st.session_state["df"],[cite: 1]
        column_config=column_config,
        num_rows="dynamic",[cite: 1]
        use_container_width=True,[cite: 1]
        hide_index=True,
        key="project_eco_editor"
    )
    st.session_state["df"] = edited[cite: 1]

    st.write("")
    col_word, col_pdf, _ = st.columns([1.5, 1.5, 4])
    
    with col_word:
        doc_data = export_docx(st.session_state["df"], st.session_state["transcript"])
        st.download_button(
            label="Export Word",
            data=doc_data,
            file_name="Project_Eco_Minutes.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"[cite: 1]
        )
        
    with col_pdf:
        pdf_data = export_pdf(st.session_state["df"], st.session_state["transcript"])
        st.download_button(
            label="Export PDF",
            data=pdf_data,
            file_name="Project_Eco_Minutes.pdf",
            mime="application/pdf"
        )
