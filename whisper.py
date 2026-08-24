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
    page_title="Project Echo",
    layout="wide",
    initial_sidebar_state="collapsed"
)

GROQ_API_KEY = "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"
GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

# ==================== iOS 26 LIGHT MODE UI & FONTS ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&display=swap');

    /* Global Reset & Century Gothic Body */
    :root, html, body, [data-testid="stAppViewContainer"], .stApp {
        color-scheme: light !important;
        background-color: #f2f5f8 !important;
        color: #0A1128 !important;
        font-family: 'Century Gothic', CenturyGothic, AppleGothic, sans-serif !important;
        -webkit-font-smoothing: antialiased;
    }

    /* Headings in Cormorant Garamond */
    h1, h2, h3, h4, h5, h6, .island-title, [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {
        font-family: 'Cormorant Garamond', serif !important;
        color: #0A1128 !important;
        font-weight: 700 !important;
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
        padding-top: 1rem !important;
        padding-bottom: 4rem !important;
        max-width: 1000px !important;
        margin: 0 auto;
    }

    /* iOS 26 Dynamic Island Toolbar Styling */
    .toolbar-container {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(30px);
        -webkit-backdrop-filter: blur(30px);
        border-radius: 40px;
        padding: 12px 24px;
        box-shadow: 0 16px 40px rgba(10, 17, 40, 0.08), 0 2px 10px rgba(10, 17, 40, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.9);
        margin-bottom: 2rem;
        position: sticky;
        top: 20px;
        z-index: 999;
    }

    /* Rounded & Floating Buttons (Navy Blue & White) */
    .stButton > button {
        border-radius: 30px !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.4rem !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        background: #0A1128 !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 8px 20px rgba(10, 17, 40, 0.2) !important;
        font-family: 'Century Gothic', sans-serif !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 28px rgba(10, 17, 40, 0.3) !important;
        background: #14214c !important;
    }

    .stDownloadButton > button {
        background: #ffffff !important;
        color: #0A1128 !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.05) !important;
    }

    .stDownloadButton > button:hover {
        background: #f8fafc !important;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.08) !important;
    }

    /* Floating Cards with Depth */
    [data-testid="stFileUploader"], [data-testid="stAudioInput"] {
        background: #ffffff !important;
        border-radius: 28px !important;
        border: none !important;
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.05) !important;
        padding: 20px !important;
        margin-bottom: 1.5rem !important;
    }
    
    [data-testid="stFileUploaderDropzone"] {
        border: 2px dashed #cbd5e1 !important;
        border-radius: 20px !important;
        background: #f8fafc !important;
    }

    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #0A1128 !important;
        background: #f1f5f9 !important;
    }

    /* Pill Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #ffffff !important;
        border-radius: 24px !important;
        padding: 6px !important;
        gap: 8px !important;
        width: fit-content;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04);
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
        border-radius: 18px !important;
        background: transparent !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        background: #0A1128 !important;
        box-shadow: 0 4px 12px rgba(10, 17, 40, 0.2) !important;
    }

    /* Floating Data Editor & Text Areas */
    [data-testid="stDataEditor"] {
        background-color: #ffffff !important;
        border-radius: 24px !important;
        border: none !important;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.06) !important;
        overflow: hidden !important;
    }

    .stTextArea textarea {
        background-color: #ffffff !important;
        color: #0A1128 !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 24px !important;
        padding: 16px !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.03) !important;
        font-size: 0.9rem !important;
        line-height: 1.6 !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #0A1128 !important;
        box-shadow: 0 8px 24px rgba(10, 17, 40, 0.1) !important;
    }
    
    hr {
        border-top: 1px solid rgba(10, 17, 40, 0.08) !important;
        margin: 2.5rem 0 !important;
    }
    
    .info-card {
        background: white;
        padding: 24px;
        border-radius: 24px;
        box-shadow: 0 12px 32px rgba(0,0,0,0.04);
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ==================== STATE MANAGEMENT ====================
if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""
if "structured_data" not in st.session_state:
    st.session_state["structured_data"] = None
if "df_actions" not in st.session_state:
    st.session_state["df_actions"] = pd.DataFrame(columns=["Description", "Assigned To", "Deadline"])
if "audio_payload" not in st.session_state:
    st.session_state["audio_payload"] = None

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
        "You are a Senior Executive Assistant with exceptional communication skills. "
        "Your task is to turn messy meeting transcripts into polished, professional meeting minutes. "
        "Write in a clear, human-friendly style, as if you were briefing a busy executive."
    )
    
    user_prompt = f"""
    Please analyze the meeting transcript below and produce a structured summary in the following JSON format:

    {{
      "summary": "A 2-3 paragraph narrative summary that explains the meeting's purpose, main discussion points, decisions made, and overall outcome. Write this in a fluid, report-style language.",
      "key_points": ["Key point 1", "Key point 2"],
      "deliverables": ["Document X", "Report Y"],
      "action_items": [
        {{"description": "Clear, actionable sentence describing who does what", "assigned_to": "Person or team explicitly named, or null", "deadline": "Date or timeframe, or null"}}
      ],
      "decisions": ["Decision 1", "Decision 2"],
      "next_steps": ["Step 1", "Step 2"]
    }}

    **Important instructions:**
    - Use professional yet natural language.
    - For action items, if the assignee is not explicitly mentioned, leave it as null - do not guess.
    - The summary should read like a fluent paragraph, not a list of bullet points.

    Transcript:
    {text}
    """
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama3-70b-8192",  # Updated to valid Groq 70B model
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
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
    h1 = doc.add_heading("Meeting Intelligence Report", level=1)
    for r in h1.runs:
        r.font.color.rgb = RGBColor(10, 17, 40)
        
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
    add_section("Next Steps", data.get("next_steps", []), is_list=True)

    if not actions_df.empty:
        doc.add_heading("Action Items", level=2)
        table = doc.add_table(rows=len(actions_df) + 1, cols=3)
        table.style = 'Table Grid'
        
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "Description"
        hdr_cells[1].text = "Assigned To"
        hdr_cells[2].text = "Deadline"
        
        for idx, row in actions_df.iterrows():
            cells = table.rows[idx + 1].cells
            cells[0].text = str(row["Description"])
            cells[1].text = str(row["Assigned To"]) if pd.notna(row["Assigned To"]) else ""
            cells[2].text = str(row["Deadline"]) if pd.notna(row["Deadline"]) else ""

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
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontName='Helvetica-Bold', textColor=colors.HexColor('#0A1128'))
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontName='Helvetica-Bold', textColor=colors.HexColor('#0A1128'))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', textColor=colors.HexColor('#1e293b'))
    
    story = [Paragraph("Meeting Intelligence Report", title_style), Spacer(1, 10)]
    
    def build_section(title, content, is_list=False):
        if not content: return
        story.append(Paragraph(title, h2_style))
        if is_list:
            items = [ListItem(Paragraph(str(i), body_style)) for i in content]
            story.append(ListFlowable(items, bulletType='bullet'))
        else:
            story.append(Paragraph(str(content).replace('\n', '<br/>'), body_style))
        story.append(Spacer(1, 12))

    build_section("Summary", data.get("summary", ""))
    build_section("Key Points", data.get("key_points", []), is_list=True)
    build_section("Deliverables", data.get("deliverables", []), is_list=True)
    build_section("Decisions", data.get("decisions", []), is_list=True)
    build_section("Next Steps", data.get("next_steps", []), is_list=True)
    
    if not actions_df.empty:
        story.append(Paragraph("Action Items", h2_style))
        table_data = [["Description", "Assigned To", "Deadline"]]
        for _, row in actions_df.iterrows():
            desc = str(row["Description"])
            assigned = str(row["Assigned To"]) if pd.notna(row["Assigned To"]) and str(row["Assigned To"]).strip().lower() != 'none' else ""
            deadline = str(row["Deadline"]) if pd.notna(row["Deadline"]) and str(row["Deadline"]).strip().lower() != 'none' else ""
            table_data.append([Paragraph(desc, body_style), Paragraph(assigned, body_style), Paragraph(deadline, body_style)])
        
        t = Table(table_data, colWidths=[250, 150, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0A1128')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
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

# 1. DYNAMIC ISLAND (TOP TOOLBAR)
st.markdown('<div class="toolbar-container">', unsafe_allow_html=True)
col_title, col_tools = st.columns([1.5, 4.5])

with col_title:
    st.markdown("<h2 style='margin:0; padding-top:4px;'>Project Echo</h2>", unsafe_allow_html=True)

with col_tools:
    # Action Tools layout horizontally aligned
    tools_cols = st.columns([1, 1, 1, 1, 1])
    
    # Save Audio Tool
    if st.session_state["audio_payload"]:
        with tools_cols[0]:
            st.download_button("💾 Save Audio", data=st.session_state["audio_payload"], file_name="echo_recording.wav", mime="audio/wav")
    
    # Process Audio Tool
    if st.session_state["audio_payload"] and not st.session_state["transcript"]:
        with tools_cols[1]:
            if st.button("🎙️ Process Audio"):
                with st.spinner("Transcribing..."):
                    res = transcribe_audio(st.session_state["audio_payload"])
                if res:
                    st.session_state["transcript"] = res
                    st.rerun()

    # Extract Summary Tool
    if st.session_state["transcript"] and not st.session_state["structured_data"]:
        with tools_cols[2]:
            if st.button("✨ Extract Actions"):
                with st.spinner("Generating Intelligence..."):
                    ext_data = extract_summary_and_actions(st.session_state["transcript"])
                    if ext_data:
                        st.session_state["structured_data"] = ext_data
                        actions = ext_data.get("action_items", [])
                        formatted_actions = []
                        for act in actions:
                            formatted_actions.append({
                                "Description": act.get("description", ""), 
                                "Assigned To": act.get("assigned_to", ""),
                                "Deadline": act.get("deadline", "")
                            })
                        st.session_state["df_actions"] = pd.DataFrame(formatted_actions)
                        st.rerun()

    # Document Export Tools
    if st.session_state["structured_data"]:
        with tools_cols[3]:
            doc_bio = export_docx(st.session_state["structured_data"], st.session_state["df_actions"], st.session_state["transcript"])
            st.download_button("📄 Word Export", data=doc_bio, file_name="Echo_Minutes.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with tools_cols[4]:
            pdf_bio = export_pdf(st.session_state["structured_data"], st.session_state["df_actions"], st.session_state["transcript"])
            st.download_button("📑 PDF Export", data=pdf_bio, file_name="Echo_Minutes.pdf", mime="application/pdf")
            
st.markdown('</div>', unsafe_allow_html=True)


# 2. AUDIO INPUT SECTION (Shown only if no transcript yet to keep UI clean)
if not st.session_state["transcript"]:
    tab_rec, tab_up = st.tabs(["🎙️ Record", "📁 Upload"])
    
    with tab_rec:
        rec_buffer = st.audio_input("Record Audio Stream", label_visibility="collapsed")
        if rec_buffer:
            st.session_state["audio_payload"] = rec_buffer.read()
            st.rerun()
            
    with tab_up:
        up_buffer = st.file_uploader("Upload Audio", type=["wav", "mp3", "m4a", "ogg", "flac"], label_visibility="collapsed")
        if up_buffer:
            st.session_state["audio_payload"] = up_buffer.read()
            st.rerun()


# 3. PROCESSING WORKSPACE
if st.session_state["transcript"]:
    
    st.markdown("<h3>Session Transcript</h3>", unsafe_allow_html=True)
    st.session_state["transcript"] = st.text_area(
        "Transcript Edit",
        st.session_state["transcript"],
        height=140,
        label_visibility="collapsed"
    )
    
    # 4. OUTPUT DASHBOARD
    if st.session_state["structured_data"]:
        st.markdown("<hr>", unsafe_allow_html=True)
        data = st.session_state["structured_data"]
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.markdown("<h4>📝 Summary</h4>", unsafe_allow_html=True)
            st.write(data.get("summary", "No summary extracted."))
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.markdown("<h4>🎯 Deliverables</h4>", unsafe_allow_html=True)
            for d in data.get("deliverables", []):
                st.markdown(f"- {d}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.markdown("<h4>🚀 Next Steps</h4>", unsafe_allow_html=True)
            for step in data.get("next_steps", []):
                st.markdown(f"- {step}")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.markdown("<h4>💡 Key Points</h4>", unsafe_allow_html=True)
            for k in data.get("key_points", []):
                st.markdown(f"- {k}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.markdown("<h4>⚖️ Decisions</h4>", unsafe_allow_html=True)
            for dec in data.get("decisions", []):
                st.markdown(f"- {dec}")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<h4>📋 Action Items</h4>", unsafe_allow_html=True)
        st.caption("Double click cells to edit. Add or remove rows dynamically.")
        
        col_config = {
            "Description": st.column_config.TextColumn("Description", width="large", required=True),
            "Assigned To": st.column_config.TextColumn("Assigned To", width="medium"),
            "Deadline": st.column_config.TextColumn("Deadline", width="medium")
        }
        
        edited_actions = st.data_editor(
            st.session_state["df_actions"],
            column_config=col_config,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True
        )
        st.session_state["df_actions"] = edited_actions
