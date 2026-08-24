import streamlit as st
import requests
import pandas as pd
import json
import io
import re
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- Configuration ---
GROQ_API_KEY = "gsk_YOUR_API_KEY_HERE"
WHISPER_MODEL = "whisper-large-v3-turbo"
LLM_MODEL = "llama-3.3-70b-versatile"

# --- CSS Design System (Corporate Crimson) ---
st.set_page_config(page_title="Project Echo", page_icon="🎙️", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Montserrat:wght@600;700&display=swap');

:root {
    --primary-accent: #990000;
    --primary-hover: #7F1D1D;
    --accent-light: #FEE2E2;
    --surface-base: #FFFFFF;
    --surface-alt: #F8FAFC;
    --text-primary: #0F172A;
    --text-body: #475569;
    --border-color: #E2E8F0;
}

.main .block-container {
    max-width: 1280px;
    background-color: var(--surface-alt);
    padding: 2rem;
    border-radius: 8px;
}

h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary);
    font-family: 'Montserrat', system-ui, sans-serif;
    letter-spacing: -0.02em;
}

p, span, div {
    font-family: 'Inter', system-ui, sans-serif;
    color: var(--text-body);
}

.eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--primary-accent);
    font-size: 0.75rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.card {
    background-color: var(--surface-base);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    margin-bottom: 1.5rem;
    transition: box-shadow 0.3s ease;
}
.card:hover {
    box-shadow: 0 12px 24px -6px rgba(0, 0, 0, 0.08);
}

div.stButton>button {
    border-radius: 6px;
    font-weight: 600;
    font-family: 'Inter', system-ui, sans-serif;
    transition: all 0.2s ease;
}
div.stButton>button:first-child {
    background-color: var(--primary-accent);
    color: white;
    border: 1px solid var(--primary-accent);
}
div.stButton>button:first-child:hover {
    background-color: var(--primary-hover);
    border-color: var(--primary-hover);
}

.stDataFrame {
    border: 1px solid var(--border-color);
    border-radius: 8px;
    overflow: hidden;
}

.footer {
    background-color: #0F172A;
    color: #94A3B8;
    padding: 3rem 2rem 1.5rem 2rem;
    margin-top: 4rem;
    font-family: 'Inter', system-ui, sans-serif;
}
.footer-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 2rem;
    max-width: 1280px;
    margin: 0 auto;
}
.footer h4 {
    color: #FFFFFF;
    font-size: 0.875rem;
    font-weight: 600;
    margin-bottom: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.footer ul {
    list-style: none;
    padding: 0;
    margin: 0;
}
.footer li {
    margin-bottom: 0.5rem;
}
.footer a {
    color: #94A3B8;
    text-decoration: none;
}
.footer a:hover {
    color: #FFFFFF;
}
.copyright {
    text-align: center;
    border-top: 1px solid #1E293B;
    margin-top: 2rem;
    padding-top: 1.5rem;
    color: #64748B;
    font-size: 0.75rem;
}
</style>
""", unsafe_allow_html=True)

# --- State Management ---
if 'transcript' not in st.session_state:
    st.session_state.transcript = ""
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = {}
if 'action_df' not in st.session_state:
    st.session_state.action_df = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])

# --- Core Functions ---
def transcribe_audio(file_bytes: bytes, filename: str) -> str:
    """Transcribes audio using Groq Whisper API."""
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {"file": (filename, file_bytes)}
    data = {"model": WHISPER_MODEL}
    
    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        return response.json()["text"]
    except requests.exceptions.RequestException as e:
        st.error(f"Transcription failed: {e}")
        return ""

def extract_meeting_intelligence(transcript: str) -> dict:
    """Extracts structured meeting minutes using Groq LLM API."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = (
        "You are a Senior Executive Assistant with 15 years of experience. "
        "Extract structured meeting minutes. Extract assignees only if explicitly mentioned, do not guess. "
        "Return ONLY valid JSON matching the requested schema."
    )
    
    user_prompt = f"""
    Transcript: {transcript}
    
    Return ONLY valid JSON matching this exact schema:
    {{
      "summary": "string",
      "key_points": ["string"],
      "deliverables": ["string"],
      "action_items": [
        {{"description": "string", "assigned_to": "string or null", "deadline": "string or null"}}
      ],
      "decisions": ["string"]
    }}
    """
    
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "top_p": 0.9,
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return json.loads(response.json()["choices"][0]["message"]["content"])
    except Exception as e:
        st.warning("API extraction failed. Applying fallback extractive summarization.")
        sentences = re.split(r'(?<=[.!?])\s+', transcript)
        return {
            "summary": transcript[:500] + ("..." if len(transcript) > 500 else ""),
            "key_points": sentences[:3] if len(sentences) >= 3 else [transcript],
            "deliverables": [],
            "action_items": [],
            "decisions": []
        }

def build_initial_dataframe(extracted_data: dict) -> pd.DataFrame:
    """Builds the initial action DataFrame from extracted data."""
    rows = []
    for kp in extracted_data.get("key_points", []):
        rows.append({"Key Point": kp, "Action Plan": "", "Assigned": ""})
    for ai in extracted_data.get("action_items", []):
        rows.append({
            "Key Point": ai.get("description", ""),
            "Action Plan": ai.get("description", ""),
            "Assigned": ai.get("assigned_to", "") or ""
        })
    
    if not rows:
        rows.append({"Key Point": "", "Action Plan": "", "Assigned": ""})
        
    return pd.DataFrame(rows, columns=["Key Point", "Action Plan", "Assigned"])

# --- Export Functions ---
def export_to_docx(transcript: str, summary: str, df: pd.DataFrame) -> bytes:
    """Generates a Word document."""
    doc = Document()
    
    # Title
    title = doc.add_heading('Project Echo - Meeting Report', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Executive Summary
    doc.add_heading('Executive Summary', level=1)
    doc.add_paragraph(summary)
    
    # Full Transcript
    doc.add_heading('Full Transcript', level=1)
    doc.add_paragraph(transcript)
    
    # Action Items Table
    doc.add_heading('Action Items', level=1)
    table = doc.add_table(rows=1, cols=3)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Key Point'
    hdr_cells[1].text = 'Action Plan'
    hdr_cells[2].text = 'Assigned'
    
    for _, row in df.iterrows():
        row_cells = table.add_row().cells
        row_cells[0].text = str(row['Key Point'])
        row_cells[1].text = str(row['Action Plan'])
        row_cells[2].text = str(row['Assigned'])
        
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def export_to_pdf(transcript: str, summary: str, df: pd.DataFrame) -> bytes:
    """Generates a PDF document."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(name='Title', fontSize=18, alignment=1, spaceAfter=12, textColor=colors.HexColor('#0F172A'))
    heading_style = ParagraphStyle(name='Heading1', fontSize=14, spaceBefore=12, spaceAfter=6, textColor=colors.HexColor('#990000'), fontName='Helvetica-Bold')
    
    story = []
    story.append(Paragraph("Project Echo - Meeting Report", title_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Paragraph(summary, styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Full Transcript", heading_style))
    story.append(Paragraph(transcript, styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Action Items", heading_style))
    
    # Table data
    data = [["Key Point", "Action Plan", "Assigned"]]
    for _, row in df.iterrows():
        data.append([str(row['Key Point']), str(row['Action Plan']), str(row['Assigned'])])
        
    t = Table(data, colWidths=[200, 200, 150])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#990000')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
        ('FONTSIZE', (0, 0), (-1, -1), 9)
    ]))
    story.append(t)
    
    doc.build(story)
    return buffer.getvalue()

def export_to_json(transcript: str, summary: str, df: pd.DataFrame) -> bytes:
    """Generates a JSON file."""
    data = {
        "transcript": transcript,
        "summary": summary,
        "action_table": df.to_dict(orient='records')
    }
    return json.dumps(data, indent=2).encode('utf-8')

# --- UI Layout ---
st.markdown('<div class="eyebrow">Enterprise Voice Intelligence</div>', unsafe_allow_html=True)
st.title("Project Echo")
st.markdown("Upload audio to generate structured meeting minutes, action items, and exportable reports.")

# Upload Section
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload Audio File", 
        type=['wav', 'mp3', 'm4a', 'ogg', 'flac', 'mp4', 'webm'],
        help="Supported formats: WAV, MP3, M4A, OGG, FLAC, MP4, WebM"
    )
    
    if uploaded_file is not None:
        st.success(f"File loaded: **{uploaded_file.name}** ({uploaded_file.size / 1024 / 1024:.2f} MB)")
        
        if st.button("Transcribe Audio", type="primary"):
            with st.spinner("Transcribing audio via Groq Whisper..."):
                file_bytes = uploaded_file.getvalue()
                st.session_state.transcript = transcribe_audio(file_bytes, uploaded_file.name)
                
            if st.session_state.transcript:
                st.success("Transcription complete!")
    st.markdown('</div>', unsafe_allow_html=True)

# Extraction Section
if st.session_state.transcript:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Transcript Preview")
        with st.expander("View Full Transcript", expanded=False):
            st.text_area("Transcript", value=st.session_state.transcript, height=200, disabled=True)
            
        if st.button("Extract Summary & Actions", type="primary"):
            with st.spinner("Analyzing transcript via Groq Llama 3.3..."):
                st.session_state.extracted_data = extract_meeting_intelligence(st.session_state.transcript)
                st.session_state.action_df = build_initial_dataframe(st.session_state.extracted_data)
            st.success("Intelligence extracted successfully!")
        st.markdown('</div>', unsafe_allow_html=True)

# Action Table Section
if not st.session_state.action_df.empty:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Action Items & Key Points")
        st.markdown("Edit the table below to refine action plans and assignees before exporting.")
        
        edited_df = st.data_editor(
            st.session_state.action_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Key Point": st.column_config.TextColumn("Key Point", width="large"),
                "Action Plan": st.column_config.TextColumn("Action Plan", width="large"),
                "Assigned": st.column_config.TextColumn("Assigned", width="medium")
            }
        )
        
        # Update state with edited data
        st.session_state.action_df = edited_df
        st.markdown('</div>', unsafe_allow_html=True)

# Export Section
if not st.session_state.action_df.empty and st.session_state.transcript:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Export Report")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            docx_data = export_to_docx(st.session_state.transcript, st.session_state.extracted_data.get("summary", ""), st.session_state.action_df)
            st.download_button(
                label="Download .DOCX",
                data=docx_data,
                file_name="project_echo_report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
            
        with col2:
            pdf_data = export_to_pdf(st.session_state.transcript, st.session_state.extracted_data.get("summary", ""), st.session_state.action_df)
            st.download_button(
                label="Download .PDF",
                data=pdf_data,
                file_name="project_echo_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        with col3:
            json_data = export_to_json(st.session_state.transcript, st.session_state.extracted_data.get("summary", ""), st.session_state.action_df)
            st.download_button(
                label="Download .JSON",
                data=json_data,
                file_name="project_echo_report.json",
                mime="application/json",
                use_container_width=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer">
    <div class="footer-grid">
        <div class="footer-col">
            <h4>Project Echo</h4>
            <ul>
                <li>Enterprise Voice Intelligence</li>
                <li>Powered by Groq AI</li>
            </ul>
        </div>
        <div class="footer-col">
            <h4>Features</h4>
            <ul>
                <li><a href="#">Audio Transcription</a></li>
                <li><a href="#">Smart Extraction</a></li>
                <li><a href="#">Multi-format Export</a></li>
            </ul>
        </div>
        <div class="footer-col">
            <h4>Support</h4>
            <ul>
                <li><a href="#">Documentation</a></li>
                <li><a href="#">API Status</a></li>
                <li><a href="#">Contact IT</a></li>
            </ul>
        </div>
        <div class="footer-col">
            <h4>Legal</h4>
            <ul>
                <li><a href="#">Privacy Policy</a></li>
                <li><a href="#">Terms of Service</a></li>
                <li><a href="#">Data Security</a></li>
            </ul>
        </div>
    </div>
    <div class="copyright">
        &copy; 2026 Corporate Crimson Enterprise. All rights reserved.
    </div>
</div>
""", unsafe_allow_html=True)
