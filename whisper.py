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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ==================== STREAMLIT CONFIGURATION ====================
st.set_page_config(
    page_title="Project Eco",
    layout="wide",
    initial_sidebar_state="collapsed"
)

GROQ_API_KEY = "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"
GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

# ==================== LIGHT MODE / FLOATING iOS UI ====================
st.markdown("""
<style>
    /* Global Reset & Light Background */
    :root, html, body, [data-testid="stAppViewContainer"], .stApp {
        color-scheme: light !important;
        background-color: #f4f7f9 !important;
        color: #1e293b !important;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, Helvetica, sans-serif !important;
        -webkit-font-smoothing: antialiased;
    }

    /* Hide Default Elements */
    header[data-testid="stHeader"],
    div[data-testid="stDecoration"],
    #MainMenu,
    footer,
    .stDeployButton {
        display: none !important;
    }

    .block-container {
        padding-top: 6rem !important; /* Space for Dynamic Island */
        padding-bottom: 4rem !important;
        max-width: 1000px !important;
        margin: 0 auto;
    }

    /* Dynamic Island Top Bar */
    .dynamic-island {
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        padding: 12px 28px;
        border-radius: 40px;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08), 0 2px 8px rgba(0,0,0,0.03);
        border: 1px solid rgba(255, 255, 255, 0.6);
        z-index: 999999;
        display: flex;
        align-items: center;
        gap: 14px;
        transition: all 0.3s ease;
    }
    
    .island-title {
        font-weight: 700;
        font-size: 1.1rem;
        color: #0f172a;
        letter-spacing: -0.02em;
    }
    
    .island-badge {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        font-size: 0.65rem;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3);
    }

    /* Floating Cards with Depth */
    [data-testid="stFileUploader"], [data-testid="stAudioInput"] {
        background: #ffffff !important;
        border-radius: 24px !important;
        border: none !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04), 0 2px 10px rgba(0,0,0,0.02) !important;
        padding: 16px !important;
        margin-bottom: 1.5rem !important;
    }
    
    [data-testid="stFileUploaderDropzone"] {
        border: 2px dashed #e2e8f0 !important;
        border-radius: 16px !important;
        background: #f8fafc !important;
    }

    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #10b981 !important;
        background: #f0fdf4 !important;
    }

    /* Pill Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #ffffff !important;
        border-radius: 20px !important;
        padding: 6px !important;
        gap: 8px !important;
        width: fit-content;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.05);
        margin: 0 auto 2rem auto !important;
        display: flex;
        justify-content: center;
        border: none !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 8px 24px !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: #64748b !important;
        border-radius: 14px !important;
        background: transparent !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        background: #0f172a !important;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.2) !important;
    }

    /* Rounded & Floating Buttons */
    .stButton > button {
        border-radius: 30px !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.8rem !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        background: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.04) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08) !important;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 10px 24px rgba(16, 185, 129, 0.3) !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 14px 32px rgba(16, 185, 129, 0.4) !important;
    }

    /* Floating Data Editor & Text Areas */
    [data-testid="stDataEditor"] {
        background-color: #ffffff !important;
        border-radius: 20px !important;
        border: none !important;
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.06) !important;
        overflow: hidden !important;
    }

    .stTextArea textarea {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border: 1px solid #f1f5f9 !important;
        border-radius: 20px !important;
        padding: 16px !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04) !important;
        font-size: 0.9rem !important;
        line-height: 1.6 !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #10b981 !important;
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.15) !important;
    }

    /* Custom Header texts */
    h3, h4, h5 {
        color: #0f172a !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
    }
    
    hr {
        border-top: 1px solid rgba(0, 0, 0, 0.05) !important;
        margin: 2.5rem 0 !important;
    }
    
    .info-card {
        background: white;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.04);
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Dynamic Island Injection
st.markdown("""
<div class="dynamic-island">
    <span class="island-title">Project Eco</span>
    <span class="island-badge">Intelligence</span>
</div>
""", unsafe_allow_html=True)

# ==================== STATE MANAGEMENT ====================
if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""
if "structured_data" not in st.session_state:
    st.session_state["structured_data"] = None
if "df_actions" not in st.session_state:
    st.session_state["df_actions"] = pd.DataFrame(columns=["Task", "Assigned To"])

# ==================== ENGINE BACKENDS ====================
def transcribe_audio(audio_bytes):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {
        "file": ("audio.wav", audio_bytes),
        "model": (None, "whisper-large-v3-turbo"),
        "response_format": (None, "json")
    }
    try:
        resp = requests.post(GROQ_AUDIO_URL, headers=headers, files=files, timeout=60)
        if resp.status_code == 200:
            return resp.json().get("text", "")
        else:
            st.error(f"Engine status: {resp.status_code}")
            return None
    except Exception as e:
        st.error(f"Transcription error: {e}")
        return None

def extract_summary_and_actions(text):
    system_prompt = (
        "You are an executive meeting intelligence engine. Analyze the provided meeting transcript "
        "and return a structured response exactly matching the JSON format below. "
        "Draw solely from the transcript. Do not use default or filler action items.\n\n"
        "Required JSON format:\n"
        "{\n"
        "  \"summary\": \"Concise paragraph summarizing the meeting.\",\n"
        "  \"key_points\": [\"Point 1\", \"Point 2\"],\n"
        "  \"deliverables\": [\"Deliverable 1\", \"Deliverable 2\"],\n"
        "  \"decisions\": [\"Decision 1\", \"Decision 2\"],\n"
        "  \"action_items\": [\n"
        "    {\"task\": \"Concrete action to take\", \"assigned_to\": \"Name or Team\"}\n"
        "  ]\n"
        "}"
    )
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Transcript:\n{text}"}
        ],
        "response_format": {"type": "json_object"}
    }
    
    try:
        resp = requests.post(GROQ_CHAT_URL, headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            result = resp.json()
            content = result["choices"][0]["message"]["content"].strip()
            data = json.loads(content)
            return data
        else:
            st.error(f"Extraction failed: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

# ==================== EXPORT UTILITIES ====================
def set_cell_margins(cell, top=120, bottom=120, start=160, end=160):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', start), ('right', end)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def export_docx(data, actions_df, transcript):
    doc = Document()
    
    # Doc Title
    h1 = doc.add_heading("Meeting Intelligence Report", level=1)
    for r in h1.runs:
        r.font.color.rgb = RGBColor(16, 185, 129)
        
    def add_section(title, content, is_list=False):
        if not content: return
        doc.add_heading(title, level=2)
        if is_list:
            for item in content:
                doc.add_paragraph(str(item), style='List Bullet')
        else:
            doc.add_paragraph(str(content))

    add_section("Summary", data.get("summary", ""))
    add_section("Key Points", data.get("key_points", []), is_list=True)
    add_section("Deliverables", data.get("deliverables", []), is_list=True)
    add_section("Decisions", data.get("decisions", []), is_list=True)

    # Action Items Table
    if not actions_df.empty:
        doc.add_heading("Action Items", level=2)
        table = doc.add_table(rows=len(actions_df) + 1, cols=2)
        table.style = 'Table Grid'
        
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "Task"
        hdr_cells[1].text = "Assigned To"
        
        for idx, row in actions_df.iterrows():
            cells = table.rows[idx + 1].cells
            cells[0].text = str(row["Task"])
            cells[1].text = str(row["Assigned To"])

    if transcript:
        doc.add_heading("Session Transcript", level=2)
        doc.add_paragraph(transcript)

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def export_pdf(data, actions_df, transcript):
    bio = BytesIO()
    doc = SimpleDocTemplate(bio, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], textColor=colors.HexColor('#10B981'))
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'], textColor=colors.HexColor('#0F172A'))
    body_style = styles['Normal']
    
    story = [Paragraph("Meeting Intelligence Report", title_style), Spacer(1, 10)]
    
    def build_section(title, content, is_list=False):
        if not content: return
        story.append(Paragraph(title, h2_style))
        if is_list:
            items = [ListItem(Paragraph(str(i), body_style)) for i in content]
            story.append(ListFlowable(items, bulletType='bullet'))
        else:
            story.append(Paragraph(str(content), body_style))
        story.append(Spacer(1, 12))

    build_section("Summary", data.get("summary", ""))
    build_section("Key Points", data.get("key_points", []), is_list=True)
    build_section("Deliverables", data.get("deliverables", []), is_list=True)
    build_section("Decisions", data.get("decisions", []), is_list=True)
    
    if not actions_df.empty:
        story.append(Paragraph("Action Items", h2_style))
        table_data = [["Task", "Assigned To"]]
        for _, row in actions_df.iterrows():
            table_data.append([Paragraph(str(row["Task"]), body_style), Paragraph(str(row["Assigned To"]), body_style)])
        
        t = Table(table_data, colWidths=[350, 150])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F8FAFC')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0F172A')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

    if transcript:
        story.append(Paragraph("Session Transcript", h2_style))
        story.append(Paragraph(transcript.replace('\n', '<br/>'), body_style))

    doc.build(story)
    bio.seek(0)
    return bio

# ==================== UI CANVAS ====================

# Input Section
tab_rec, tab_up = st.tabs(["🎙️ Record", "📁 Upload"])
audio_payload = None

with tab_rec:
    rec_buffer = st.audio_input("Record Audio Stream", label_visibility="collapsed")
    if rec_buffer:
        audio_payload = rec_buffer.read()

with tab_up:
    up_buffer = st.file_uploader("Upload Audio", type=["wav", "mp3", "m4a", "ogg", "flac"], label_visibility="collapsed")
    if up_buffer:
        audio_payload = up_buffer.read()

if audio_payload:
    if st.button("Process Audio", type="primary"):
        with st.spinner("Transcribing via Groq Whisper..."):
            res = transcribe_audio(audio_payload)
        if res:
            st.session_state["transcript"] = res
            st.session_state["structured_data"] = None
            st.session_state["df_actions"] = pd.DataFrame(columns=["Task", "Assigned To"])
            st.rerun()

# Processing Workspace
if st.session_state["transcript"]:
    st.markdown("---")
    
    st.subheader("Session Transcript")
    st.session_state["transcript"] = st.text_area(
        "Transcript Edit",
        st.session_state["transcript"],
        height=140,
        label_visibility="collapsed"
    )
    
    st.write("")
    if st.button("Extract Summary & Actions", type="primary"):
        with st.spinner("Analyzing intelligence via Llama 3.3 70B..."):
            ext_data = extract_summary_and_actions(st.session_state["transcript"])
            if ext_data:
                st.session_state["structured_data"] = ext_data
                
                # Format action items into DataFrame
                actions = ext_data.get("action_items", [])
                formatted_actions = []
                for act in actions:
                    formatted_actions.append({"Task": act.get("task", ""), "Assigned To": act.get("assigned_to", "")})
                st.session_state["df_actions"] = pd.DataFrame(formatted_actions)
                st.rerun()

# Output Dashboard
if st.session_state["structured_data"]:
    st.markdown("---")
    data = st.session_state["structured_data"]
    
    # Intelligence View Layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("#### 📝 Summary")
        st.write(data.get("summary", "No summary extracted."))
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("#### 🎯 Deliverables")
        for d in data.get("deliverables", []):
            st.markdown(f"- {d}")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("#### 💡 Key Points")
        for k in data.get("key_points", []):
            st.markdown(f"- {k}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown("#### ⚖️ Decisions")
        for dec in data.get("decisions", []):
            st.markdown(f"- {dec}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("#### 📋 Action Matrix")
    st.caption("Double click cells to edit. Add or remove rows dynamically.")
    
    col_config = {
        "Task": st.column_config.TextColumn("Task", width="large", required=True),
        "Assigned To": st.column_config.TextColumn("Assigned To", width="medium")
    }
    
    edited_actions = st.data_editor(
        st.session_state["df_actions"],
        column_config=col_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True
    )
    st.session_state["df_actions"] = edited_actions

    st.write("")
    dl1, dl2, _ = st.columns([1.5, 1.5, 5])
    
    with dl1:
        doc_bio = export_docx(st.session_state["structured_data"], st.session_state["df_actions"], st.session_state["transcript"])
        st.download_button(
            label="Download Word",
            data=doc_bio,
            file_name="Eco_Intelligence.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    with dl2:
        pdf_bio = export_pdf(st.session_state["structured_data"], st.session_state["df_actions"], st.session_state["transcript"])
        st.download_button(
            label="Download PDF",
            data=pdf_bio,
            file_name="Eco_Intelligence.pdf",
            mime="application/pdf"
        )
