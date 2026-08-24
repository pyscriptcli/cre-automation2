import streamlit as st
import requests
import json
import pandas as pd
from io import BytesIO
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import re

# ========== CONFIG ==========
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
PUTER_CHAT_URL = "https://api.puter.com/v1/ai/chat"

# ========== CUSTOM CSS (Corporate Crimson Enterprise) ==========
def apply_custom_css():
    st.markdown("""
    <style>
        /* ----- Global Reset & Font ----- */
        body {
            font-family: 'Inter', 'Montserrat', 'Plus Jakarta Sans', system-ui, sans-serif;
            background-color: #F8FAFC;
            color: #0F172A;
        }
        .main .block-container {
            max-width: 1280px;
            padding: 2rem 2rem 4rem 2rem;
            margin: 0 auto;
        }

        /* ----- Typography ----- */
        h1, h2, h3, h4, h5, h6 {
            font-weight: 700 !important;
            letter-spacing: -0.025em !important;
            color: #0F172A !important;
        }
        h1 {
            font-size: 2.5rem !important;
        }
        h2 {
            font-size: 2rem !important;
            margin-top: 1.5rem !important;
        }
        .stMarkdown p, .stText, .stTextArea textarea, .stDataFrame {
            font-size: 0.9rem !important;
            line-height: 1.6 !important;
            color: #475569 !important;
        }

        /* ----- Eyebrow / Sub‑header ----- */
        .eyebrow {
            font-size: 0.75rem !important;
            text-transform: uppercase !important;
            font-weight: 600 !important;
            letter-spacing: 0.1em !important;
            color: #990000 !important;
            margin-bottom: 0.25rem !important;
        }

        /* ----- Buttons ----- */
        .stButton > button {
            font-weight: 500 !important;
            padding: 0.6rem 1.5rem !important;
            border-radius: 6px !important;
            transition: all 200ms ease !important;
            border: none !important;
            background-color: transparent;
        }
        /* Primary CTA */
        .stButton > button[kind="primary"] {
            background-color: #990000 !important;
            color: white !important;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #7F1D1D !important;
            box-shadow: 0 8px 16px -6px rgba(153, 0, 0, 0.25);
        }
        /* Secondary / Outline */
        .stButton > button[kind="secondary"] {
            border: 1px solid #0F172A !important;
            background-color: transparent !important;
            color: #0F172A !important;
        }
        .stButton > button[kind="secondary"]:hover {
            background-color: #F8FAFC !important;
        }
        /* Danger/Reset */
        .stButton > button[kind="danger"] {
            background-color: transparent !important;
            color: #990000 !important;
            border: 1px solid #FEE2E2 !important;
        }
        .stButton > button[kind="danger"]:hover {
            background-color: #FEE2E2 !important;
        }

        /* ----- Cards (containers) ----- */
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

        /* ----- Data Editor (pandas) ----- */
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
        .stDataFrame tbody td {
            color: #0F172A !important;
        }

        /* ----- File Uploader ----- */
        .stFileUploader {
            border: 2px dashed #E2E8F0 !important;
            border-radius: 8px !important;
            background-color: #F8FAFC !important;
            padding: 1rem !important;
        }
        .stFileUploader:hover {
            border-color: #990000 !important;
        }

        /* ----- Text Area & Inputs ----- */
        .stTextArea textarea, .stTextInput input {
            border: 1px solid #E2E8F0 !important;
            border-radius: 6px !important;
            font-size: 0.9rem !important;
            background-color: #FFFFFF !important;
        }
        .stTextArea textarea:focus, .stTextInput input:focus {
            border-color: #990000 !important;
            box-shadow: 0 0 0 2px rgba(153, 0, 0, 0.1) !important;
        }

        /* ----- Footer (Enterprise) ----- */
        .footer {
            background-color: #0F172A;
            color: #94A3B8;
            padding: 2rem 0;
            margin-top: 3rem;
            border-radius: 8px 8px 0 0;
        }
        .footer h4 {
            color: #FFFFFF !important;
            font-weight: 700 !important;
            font-size: 1rem !important;
            margin-bottom: 0.5rem;
        }
        .footer a {
            color: #94A3B8;
            text-decoration: none;
        }
        .footer a:hover {
            color: #FFFFFF;
        }
        .footer .copyright {
            border-top: 1px solid #1E293B;
            padding-top: 1rem;
            font-size: 0.8rem;
        }

        /* ----- Metrics / KPI ----- */
        .metric {
            background: white;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 1rem 1.5rem;
            text-align: center;
        }
        .metric .value {
            font-size: 2.5rem;
            font-weight: 800;
            color: #990000;
            line-height: 1.2;
        }
        .metric .label {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748B;
        }

        /* ----- Misc ----- */
        .badge {
            background-color: #FEE2E2;
            color: #990000;
            font-size: 0.7rem;
            font-weight: 600;
            padding: 0.2rem 0.8rem;
            border-radius: 20px;
            display: inline-block;
        }
        hr {
            border-color: #E2E8F0 !important;
        }
        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: #990000;
            margin-right: 8px;
        }
    </style>
    """, unsafe_allow_html=True)

# ========== TRANSCRIPTION ==========
def transcribe_audio(audio_bytes):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {
        "file": ("audio.wav", audio_bytes),
        "model": (None, "whisper-large-v3-turbo"),
        "response_format": (None, "json")
    }
    resp = requests.post(GROQ_URL, headers=headers, files=files)
    if resp.status_code == 200:
        return resp.json().get("text", "")
    else:
        st.error(f"Transcription failed: {resp.text}")
        return None

# ========== SUMMARIZATION ==========
def summarize_text(text):
    prompt = f"""
    You are an expert summarizer. Read the following transcript and extract the 3-5 most important key points.
    Output each key point as a separate line, starting with a dash "-". Do not include any extra text or numbering.
    Transcript:
    {text}
    """
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        resp = requests.post(PUTER_CHAT_URL, json=payload)
        if resp.status_code == 200:
            result = resp.json()
            if "choices" in result:
                content = result["choices"][0]["message"]["content"]
            elif "response" in result:
                content = result["response"]
            else:
                content = result.get("content", "")
            lines = [line.strip() for line in content.split("\n") if line.strip().startswith("-")]
            if not lines:
                sentences = re.split(r'(?<=[.!?])\s+', text)
                lines = [f"- {s}" for s in sentences[:3]]
            return [line.lstrip("- ").strip() for line in lines]
        else:
            st.warning(f"Summarization API error: {resp.status_code}. Using fallback.")
            return fallback_summary(text)
    except Exception as e:
        st.warning(f"Summarization failed: {e}. Using fallback.")
        return fallback_summary(text)

def fallback_summary(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences[:3] if s.strip()]

# ========== EXPORT TO WORD ==========
def export_to_word(df, transcript=""):
    doc = Document()
    doc.sections[0].orientation = 0
    doc.sections[0].page_width = Inches(8.5)
    doc.sections[0].page_height = Inches(11.0)

    title = doc.add_heading("Meeting Summary Report", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

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

# ========== STREAMLIT APP ==========
def main():
    st.set_page_config(page_title="Voice Assistant · Enterprise", layout="wide")

    # Inject custom CSS
    apply_custom_css()

    # --- Header (Enterprise) ---
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #E2E8F0; padding-bottom: 1rem; margin-bottom: 2rem;">
        <div style="display: flex; align-items: center;">
            <span style="font-size: 1.8rem; font-weight: 800; color: #0F172A;">VOICE<span style="color: #990000;">·</span>AI</span>
            <span class="badge" style="margin-left: 1rem;">v2.0 · Enterprise</span>
        </div>
        <div style="display: flex; gap: 1.5rem; font-weight: 500; color: #475569;">
            <a href="#" style="text-decoration: none; color: #0F172A;">Dashboard</a>
            <a href="#" style="text-decoration: none; color: #475569;">Reports</a>
            <a href="#" style="text-decoration: none; color: #475569;">Settings</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Page Title ---
    st.markdown('<div class="eyebrow">AI‑Powered Meeting Assistant</div>', unsafe_allow_html=True)
    st.markdown('<h1 style="margin-top: 0;">Transcribe & Summarize</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #64748B; font-size: 1.1rem;">Upload a voice recording, get a transcript and key points, then assign actions for your team.</p>', unsafe_allow_html=True)

    # --- Session State ---
    if "transcript" not in st.session_state:
        st.session_state["transcript"] = ""
    if "key_points" not in st.session_state:
        st.session_state["key_points"] = []
    if "df" not in st.session_state:
        st.session_state["df"] = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])
    if "processed" not in st.session_state:
        st.session_state["processed"] = False

    # --- Layout: Two columns for upload + actions ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        # Card for Upload
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">📁 Upload Audio</div>', unsafe_allow_html=True)
            uploaded = st.file_uploader("Choose a voice file", type=["wav", "mp3", "m4a", "ogg", "flac", "mp4", "webm"])
            st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        # Card for Transcription Action
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">⚡ Transcribe</div>', unsafe_allow_html=True)
            if uploaded:
                if st.button("🔊 Transcribe with Groq", key="transcribe_btn", use_container_width=True):
                    with st.spinner("Transcribing..."):
                        audio_bytes = uploaded.read()
                        transcript = transcribe_audio(audio_bytes)
                    if transcript:
                        st.session_state["transcript"] = transcript
                        st.session_state["key_points"] = []
                        st.session_state["df"] = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])
                        st.session_state["processed"] = False
                        st.success("✅ Transcription complete!")
                        st.rerun()
            else:
                st.info("Please upload a file first.")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- Display Transcript ---
    if st.session_state["transcript"]:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">📋 Full Transcript</div>', unsafe_allow_html=True)
            st.text_area("", st.session_state["transcript"], height=150, label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- Summarization & Editing ---
    if st.session_state["transcript"]:
        col_summary, col_actions = st.columns([1, 2])

        with col_summary:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown('<div class="card-title">🧠 Generate Key Points</div>', unsafe_allow_html=True)
                if not st.session_state["key_points"]:
                    if st.button("📝 Summarize with Puter AI", key="summarize_btn", use_container_width=True):
                        with st.spinner("Summarizing..."):
                            points = summarize_text(st.session_state["transcript"])
                        if points:
                            st.session_state["key_points"] = points
                            df = pd.DataFrame({
                                "Key Point": points,
                                "Action Plan": [""] * len(points),
                                "Assigned": [""] * len(points)
                            })
                            st.session_state["df"] = df
                            st.session_state["processed"] = True
                            st.success("✅ Key points generated!")
                            st.rerun()
                else:
                    st.success(f"✅ {len(st.session_state['key_points'])} key points ready.")
                    if st.button("🔄 Regenerate", key="regenerate_btn", use_container_width=True):
                        st.session_state["key_points"] = []
                        st.session_state["df"] = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])
                        st.session_state["processed"] = False
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        with col_actions:
            if not st.session_state["df"].empty:
                with st.container():
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown('<div class="card-title">✏️ Edit Action Items</div>', unsafe_allow_html=True)
                    st.markdown("Add **Action Plan** and **Assigned** for each key point below.")
                    edited_df = st.data_editor(
                        st.session_state["df"],
                        num_rows="dynamic",
                        use_container_width=True,
                        key="data_editor",
                        column_config={
                            "Key Point": st.column_config.TextColumn("Key Point", width="large"),
                            "Action Plan": st.column_config.TextColumn("Action Plan", width="large"),
                            "Assigned": st.column_config.TextColumn("Assigned", width="medium"),
                        }
                    )
                    st.session_state["df"] = edited_df
                    st.markdown('</div>', unsafe_allow_html=True)

    # --- Export Section ---
    if not st.session_state["df"].empty:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">📄 Export Report</div>', unsafe_allow_html=True)
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                if st.button("📥 Download Word Document", key="export_word", use_container_width=True):
                    doc_bio = export_to_word(st.session_state["df"], st.session_state["transcript"])
                    st.download_button(
                        label="⬇️ Click to Download",
                        data=doc_bio,
                        file_name="summary_report.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
            with col_exp2:
                # Optional: download JSON
                if st.button("📥 Download JSON", key="export_json", use_container_width=True):
                    json_data = {
                        "transcript": st.session_state["transcript"],
                        "actions": st.session_state["df"].to_dict(orient="records")
                    }
                    st.download_button(
                        label="⬇️ Download JSON",
                        data=json.dumps(json_data, indent=2),
                        file_name="summary.json",
                        mime="application/json",
                        use_container_width=True
                    )
            st.markdown('</div>', unsafe_allow_html=True)

    # --- Enterprise Footer ---
    st.markdown("""
    <div class="footer">
        <div style="max-width: 1280px; margin: 0 auto; padding: 0 2rem;">
            <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 2rem;">
                <div>
                    <h4>VOICE·AI</h4>
                    <p style="font-size: 0.9rem;">Enterprise‑grade voice intelligence for modern teams.</p>
                    <p style="color: #64748B; font-size: 0.8rem;">© 2026 All rights reserved.</p>
                </div>
                <div>
                    <h4>Product</h4>
                    <a href="#">Features</a><br>
                    <a href="#">Pricing</a><br>
                    <a href="#">Documentation</a>
                </div>
                <div>
                    <h4>Company</h4>
                    <a href="#">About</a><br>
                    <a href="#">Careers</a><br>
                    <a href="#">Contact</a>
                </div>
                <div>
                    <h4>Legal</h4>
                    <a href="#">Privacy</a><br>
                    <a href="#">Terms</a><br>
                    <a href="#">Cookie Policy</a>
                </div>
            </div>
            <div class="copyright" style="margin-top: 2rem; text-align: center;">
                Built with Streamlit · Groq Whisper · Puter AI
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
