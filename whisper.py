import streamlit as st
import requests
import json
import pandas as pd
import re
from io import BytesIO
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# ========== CONFIG ==========
GROQ_API_KEY = "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"
GROQ_WHISPER_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

# ========== CUSTOM CSS (Corporate Crimson) ==========
def apply_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        html, body, .stApp {
            font-family: 'Inter', 'Montserrat', system-ui, sans-serif;
            background-color: #F8FAFC;
            color: #0F172A;
        }
        .main .block-container {
            max-width: 1280px;
            padding: 2rem 2rem 4rem 2rem;
            margin: 0 auto;
        }
        h1, h2, h3, h4 {
            font-weight: 700 !important;
            letter-spacing: -0.025em !important;
            color: #0F172A !important;
        }
        h1 { font-size: 2.5rem !important; }
        h2 { font-size: 2rem !important; margin-top: 1.5rem !important; }
        .eyebrow {
            font-size: 0.75rem !important;
            text-transform: uppercase !important;
            font-weight: 600 !important;
            letter-spacing: 0.1em !important;
            color: #990000 !important;
            margin-bottom: 0.25rem !important;
        }
        .stButton > button {
            font-weight: 500 !important;
            padding: 0.6rem 1.5rem !important;
            border-radius: 6px !important;
            transition: all 200ms ease !important;
            border: none !important;
        }
        .stButton > button[kind="primary"] {
            background-color: #990000 !important;
            color: white !important;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #7F1D1D !important;
            box-shadow: 0 8px 16px -6px rgba(153, 0, 0, 0.25);
        }
        .stButton > button[kind="secondary"] {
            border: 1px solid #0F172A !important;
            background-color: transparent !important;
            color: #0F172A !important;
        }
        .stButton > button[kind="secondary"]:hover {
            background-color: #F8FAFC !important;
        }
        .card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            transition: box-shadow 200ms ease, transform 200ms ease;
        }
        .card:hover {
            box-shadow: 0 12px 24px -6px rgba(0, 0, 0, 0.08);
            transform: translateY(-1px);
        }
        .card-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: #0F172A;
            margin-bottom: 0.75rem;
        }
        .stDataFrame {
            border: 1px solid #E2E8F0 !important;
            border-radius: 8px !important;
            overflow: hidden;
        }
        .stDataFrame thead th {
            background-color: #F1F5F9 !important;
            color: #0F172A !important;
            font-weight: 600 !important;
            font-size: 0.8rem !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .badge {
            background-color: #FEE2E2;
            color: #990000;
            font-size: 0.7rem;
            font-weight: 600;
            padding: 0.2rem 0.8rem;
            border-radius: 20px;
            display: inline-block;
        }
        .footer {
            background-color: #0F172A;
            color: #94A3B8;
            padding: 2rem 0;
            margin-top: 3rem;
            border-radius: 8px 8px 0 0;
        }
        .footer h4 { color: #FFFFFF !important; font-weight: 700 !important; }
        .footer a { color: #94A3B8; text-decoration: none; }
        .footer a:hover { color: #FFFFFF; }
        .copyright { border-top: 1px solid #1E293B; padding-top: 1rem; font-size: 0.8rem; text-align: center; }
        hr { border-color: #E2E8F0 !important; }
    </style>
    """, unsafe_allow_html=True)

# ========== TRANSCRIPTION ==========
def transcribe_audio(audio_bytes):
    """Transcribe using Groq Whisper (free tier)."""
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {
        "file": ("audio.wav", audio_bytes),
        "model": (None, "whisper-large-v3-turbo"),
        "response_format": (None, "json")
    }
    resp = requests.post(GROQ_WHISPER_URL, headers=headers, files=files)
    if resp.status_code == 200:
        return resp.json().get("text", "")
    else:
        st.error(f"Transcription failed: {resp.text}")
        return None

# ========== SUMMARIZATION & ACTION EXTRACTION (Groq Llama) ==========
def extract_meeting_intelligence(transcript):
    """
    Uses Groq's Llama 3.3 70B to extract structured meeting minutes.
    Returns a dictionary with keys: summary, key_points, deliverables, action_items, decisions.
    """
    system_prompt = (
        "You are a Senior Executive Assistant with 15 years of experience in corporate governance. "
        "Your task is to distill unstructured meeting transcripts into concise, professional minutes."
    )
    user_prompt = f"""
    Extract the following from the meeting transcript below:
    1. **Summary**: A 1-2 paragraph high-level recap of the meeting's purpose and outcome.
    2. **Key Points**: 3-5 bullet points of the most critical discussion topics.
    3. **Deliverables**: Any specific outputs, documents, or assets mentioned as required.
    4. **Action Items**: A list of actions with:
       - description: what needs to be done
       - assigned_to: the person or team responsible (explicitly mentioned in the transcript; if not mentioned, set to null)
       - deadline: if a date or timeframe is mentioned, otherwise null
    5. **Decisions**: Any hard decisions made during the meeting (e.g., budget approval, policy changes).

    Output **only** valid JSON in the following schema:
    {{
      "summary": "string",
      "key_points": ["point1", "point2", ...],
      "deliverables": ["deliverable1", ...],
      "action_items": [
        {{"description": "string", "assigned_to": "string or null", "deadline": "string or null"}}
      ],
      "decisions": ["decision1", ...]
    }}
    Do not include any additional text outside the JSON.

    Transcript:
    {transcript}
    """
    payload = {
        "model": "llama3-70b-8192",        # stable, high-quality
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,                # deterministic
        "top_p": 0.9,
        "response_format": {"type": "json_object"},
        "max_tokens": 1024
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        resp = requests.post(GROQ_CHAT_URL, headers=headers, json=payload)
        if resp.status_code == 200:
            result = resp.json()
            content = result["choices"][0]["message"]["content"]
            # Parse JSON
            data = json.loads(content)
            # Ensure all expected keys exist
            required_keys = ["summary", "key_points", "deliverables", "action_items", "decisions"]
            for key in required_keys:
                if key not in data:
                    data[key] = [] if key != "summary" else ""
            return data
        else:
            st.warning(f"Summarization API error: {resp.status_code}. Using fallback.")
            return fallback_extraction(transcript)
    except Exception as e:
        st.warning(f"Summarization failed: {e}. Using fallback.")
        return fallback_extraction(transcript)

def fallback_extraction(transcript):
    """Simple rule‑based fallback if the AI API fails."""
    sentences = re.split(r'(?<=[.!?])\s+', transcript)
    key_points = sentences[:3] if len(sentences) >= 3 else sentences
    return {
        "summary": transcript[:500] + ("..." if len(transcript) > 500 else ""),
        "key_points": [s.strip() for s in key_points],
        "deliverables": [],
        "action_items": [],
        "decisions": []
    }

# ========== EXPORT FUNCTIONS ==========
def export_to_word(df, transcript="", summary=""):
    doc = Document()
    doc.sections[0].orientation = 0
    doc.sections[0].page_width = Inches(8.5)
    doc.sections[0].page_height = Inches(11.0)
    title = doc.add_heading("Project Echo – Summary Report", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if summary:
        doc.add_heading("Executive Summary", level=2)
        doc.add_paragraph(summary)
    if transcript:
        doc.add_heading("Full Transcript", level=2)
        doc.add_paragraph(transcript)
    doc.add_heading("Action Items", level=2)
    table = doc.add_table(rows=len(df)+1, cols=3)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    hdr[0].text = "Key Point"
    hdr[1].text = "Action Plan"
    hdr[2].text = "Assigned"
    for i, row in df.iterrows():
        cells = table.rows[i+1].cells
        cells[0].text = str(row["Key Point"])
        cells[1].text = str(row["Action Plan"])
        cells[2].text = str(row["Assigned"])
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def export_to_pdf(df, transcript="", summary=""):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, alignment=1, spaceAfter=12)
    heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontSize=14, spaceAfter=6)
    normal_style = styles['Normal']
    elements = []
    elements.append(Paragraph("Project Echo – Summary Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    if summary:
        elements.append(Paragraph("Executive Summary", heading_style))
        elements.append(Paragraph(summary, normal_style))
        elements.append(Spacer(1, 0.2*inch))
    if transcript:
        elements.append(Paragraph("Full Transcript", heading_style))
        elements.append(Paragraph(transcript[:1000] + ("..." if len(transcript)>1000 else ""), normal_style))
        elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("Action Items", heading_style))
    data = [["Key Point", "Action Plan", "Assigned"]]
    for _, row in df.iterrows():
        data.append([str(row["Key Point"]), str(row["Action Plan"]), str(row["Assigned"])])
    table = Table(data, colWidths=[2.5*inch, 2.5*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#FFFFFF')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ========== STREAMLIT APP ==========
def main():
    st.set_page_config(page_title="Project Echo · Enterprise", layout="wide")
    apply_custom_css()

    # Header
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #E2E8F0; padding-bottom: 1rem; margin-bottom: 2rem;">
        <div style="display: flex; align-items: center;">
            <span style="font-size: 1.8rem; font-weight: 800; color: #0F172A;">PROJECT<span style="color: #990000;">·</span>ECHO</span>
            <span class="badge" style="margin-left: 1rem;">v2.0 · Enterprise</span>
        </div>
        <div style="display: flex; gap: 1.5rem; font-weight: 500; color: #475569;">
            <a href="#" style="text-decoration: none; color: #0F172A;">Dashboard</a>
            <a href="#" style="text-decoration: none; color: #475569;">Reports</a>
            <a href="#" style="text-decoration: none; color: #475569;">Settings</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Title
    st.markdown('<div class="eyebrow">AI‑Powered Meeting Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<h1 style="margin-top: 0;">Transcribe & Summarize</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #64748B; font-size: 1.1rem;">Upload a voice recording. Get a transcript, extract key points, assign actions, and export professional reports.</p>', unsafe_allow_html=True)

    # Session State
    if "transcript" not in st.session_state:
        st.session_state["transcript"] = ""
    if "summary" not in st.session_state:
        st.session_state["summary"] = ""
    if "key_points" not in st.session_state:
        st.session_state["key_points"] = []
    if "action_items" not in st.session_state:
        st.session_state["action_items"] = []
    if "df" not in st.session_state:
        st.session_state["df"] = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])
    if "processed" not in st.session_state:
        st.session_state["processed"] = False

    # Layout: Upload & Transcribe
    col_left, col_right = st.columns([2, 1])
    with col_left:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">📁 Upload Audio</div>', unsafe_allow_html=True)
            uploaded = st.file_uploader("Choose a voice file", type=["wav", "mp3", "m4a", "ogg", "flac", "mp4", "webm"])
            st.markdown('</div>', unsafe_allow_html=True)
    with col_right:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">⚡ Transcribe</div>', unsafe_allow_html=True)
            if uploaded:
                if st.button("🔊 Transcribe with Groq", key="transcribe", use_container_width=True):
                    with st.spinner("Transcribing..."):
                        transcript = transcribe_audio(uploaded.read())
                    if transcript:
                        st.session_state["transcript"] = transcript
                        st.session_state["summary"] = ""
                        st.session_state["key_points"] = []
                        st.session_state["action_items"] = []
                        st.session_state["df"] = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])
                        st.session_state["processed"] = False
                        st.success("✅ Transcription complete!")
                        st.rerun()
            else:
                st.info("Please upload a file first.")
            st.markdown('</div>', unsafe_allow_html=True)

    # Display Transcript
    if st.session_state["transcript"]:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">📋 Full Transcript</div>', unsafe_allow_html=True)
            st.text_area("", st.session_state["transcript"], height=150, label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)

    # Summarization & Action Extraction
    if st.session_state["transcript"] and not st.session_state["processed"]:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">🧠 Generate Intelligence</div>', unsafe_allow_html=True)
            if st.button("📝 Extract Summary & Actions", key="summarize", use_container_width=True):
                with st.spinner("Analyzing with Groq Llama..."):
                    data = extract_meeting_intelligence(st.session_state["transcript"])
                if data:
                    st.session_state["summary"] = data.get("summary", "")
                    st.session_state["key_points"] = data.get("key_points", [])
                    st.session_state["action_items"] = data.get("action_items", [])
                    # Build the DataFrame
                    rows = []
                    for kp in st.session_state["key_points"]:
                        rows.append({"Key Point": kp, "Action Plan": "", "Assigned": ""})
                    for ai in st.session_state["action_items"]:
                        rows.append({
                            "Key Point": ai.get("description", ""),
                            "Action Plan": ai.get("description", ""),  # duplicate as Action Plan for clarity
                            "Assigned": ai.get("assigned_to", "")
                        })
                    # If no rows, add a placeholder
                    if not rows:
                        rows.append({"Key Point": "No key points extracted.", "Action Plan": "", "Assigned": ""})
                    st.session_state["df"] = pd.DataFrame(rows)
                    st.session_state["processed"] = True
                    st.success("✅ Intelligence extracted!")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # Display Summary (if available)
    if st.session_state["summary"]:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">📄 Executive Summary</div>', unsafe_allow_html=True)
            st.write(st.session_state["summary"])
            st.markdown('</div>', unsafe_allow_html=True)

    # Editable Table
    if not st.session_state["df"].empty:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">✏️ Edit Action Items</div>', unsafe_allow_html=True)
            st.markdown("Add **Action Plan** and **Assigned** for each key point below. You can also add/delete rows.")
            edited_df = st.data_editor(
                st.session_state["df"],
                num_rows="dynamic",
                use_container_width=True,
                key="editor",
                column_config={
                    "Key Point": st.column_config.TextColumn("Key Point", width="large"),
                    "Action Plan": st.column_config.TextColumn("Action Plan", width="large"),
                    "Assigned": st.column_config.TextColumn("Assigned", width="medium"),
                }
            )
            st.session_state["df"] = edited_df
            st.markdown('</div>', unsafe_allow_html=True)

    # Export Section
    if not st.session_state["df"].empty:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">📄 Export Report</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("📥 Word (.docx)", key="exp_word", use_container_width=True):
                    doc_bio = export_to_word(st.session_state["df"], st.session_state["transcript"], st.session_state["summary"])
                    st.download_button("⬇️ Download", data=doc_bio, file_name="project_echo.docx",
                                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                       key="dw_word", use_container_width=True)
            with c2:
                if st.button("📥 PDF (.pdf)", key="exp_pdf", use_container_width=True):
                    pdf_bio = export_to_pdf(st.session_state["df"], st.session_state["transcript"], st.session_state["summary"])
                    st.download_button("⬇️ Download", data=pdf_bio, file_name="project_echo.pdf",
                                       mime="application/pdf", key="dw_pdf", use_container_width=True)
            with c3:
                if st.button("📥 JSON (.json)", key="exp_json", use_container_width=True):
                    json_data = {
                        "transcript": st.session_state["transcript"],
                        "summary": st.session_state["summary"],
                        "actions": st.session_state["df"].to_dict(orient="records")
                    }
                    st.download_button("⬇️ Download", data=json.dumps(json_data, indent=2),
                                       file_name="project_echo.json", mime="application/json",
                                       key="dw_json", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div class="footer">
        <div style="max-width: 1280px; margin: 0 auto; padding: 0 2rem;">
            <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 2rem;">
                <div><h4>PROJECT·ECHO</h4><p style="font-size: 0.9rem;">Enterprise voice intelligence for modern teams.</p>
                <p style="color: #64748B; font-size: 0.8rem;">© 2026 All rights reserved.</p></div>
                <div><h4>Product</h4><a href="#">Features</a><br><a href="#">Pricing</a><br><a href="#">Docs</a></div>
                <div><h4>Company</h4><a href="#">About</a><br><a href="#">Careers</a><br><a href="#">Contact</a></div>
                <div><h4>Legal</h4><a href="#">Privacy</a><br><a href="#">Terms</a><br><a href="#">Cookies</a></div>
            </div>
            <div class="copyright">Built with Streamlit · Groq Whisper + Llama 3.3 70B</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
