import streamlit as st
import requests
import json
import pandas as pd
from io import BytesIO
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ========== CONFIG ==========
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
PUTER_CHAT_URL = "https://api.puter.com/v1/ai/chat"   # Official Puter API endpoint

# ========== TRANSCRIPTION ==========
def transcribe_audio(audio_bytes):
    """Transcribe using Groq Whisper (free tier: 2,000 req/day, 7,200 sec/min)."""
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {
        "file": ("audio.wav", audio_bytes),
        "model": (None, "whisper-large-v3-turbo"),   # Faster and free-tier friendly
        "response_format": (None, "json")
    }
    resp = requests.post(GROQ_URL, headers=headers, files=files)
    if resp.status_code == 200:
        return resp.json().get("text", "")
    else:
        st.error(f"Transcription failed: {resp.text}")
        return None

# ========== SUMMARIZATION (Puter API - no API key needed) ==========
def summarize_text(text):
    """
    Generate key points using Puter's AI (same as the official JS SDK).
    Returns a list of key points (strings).
    """
    prompt = f"""
    You are an expert summarizer. Read the following transcript and extract the 3-5 most important key points.
    Output each key point as a separate line, starting with a dash "-". Do not include any extra text or numbering.
    Transcript:
    {text}
    """
    payload = {
        "model": "gpt-4o-mini",   # or any model supported by Puter (e.g., "gpt-5.4-nano")
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        resp = requests.post(PUTER_CHAT_URL, json=payload)
        if resp.status_code == 200:
            result = resp.json()
            # The response structure may vary; we assume it returns a "choices" array or "response"
            # Let's try common formats
            if "choices" in result:
                content = result["choices"][0]["message"]["content"]
            elif "response" in result:
                content = result["response"]
            else:
                content = result.get("content", "")
            # Parse bullet points
            lines = [line.strip() for line in content.split("\n") if line.strip().startswith("-")]
            if not lines:
                # Fallback: split by sentences and take first few
                import re
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
    """Simple fallback: extract first 3 sentences."""
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences[:3] if s.strip()]

# ========== EXPORT TO WORD ==========
def export_to_word(df):
    """Generate a Word document with a table (portrait, columns: Key Point, Action Plan, Assigned)."""
    doc = Document()
    doc.sections[0].orientation = 0  # 0 = portrait
    doc.sections[0].page_width = Inches(8.5)
    doc.sections[0].page_height = Inches(11.0)

    title = doc.add_heading("Meeting Summary Report", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Add transcript (optional)
    if "transcript" in st.session_state:
        doc.add_heading("Full Transcript", level=2)
        doc.add_paragraph(st.session_state["transcript"])

    doc.add_heading("Action Items", level=2)
    table = doc.add_table(rows=len(df)+1, cols=3)
    table.style = "Table Grid"

    # Header
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Key Point"
    hdr_cells[1].text = "Action Plan"
    hdr_cells[2].text = "Assigned"

    # Data
    for i, row in df.iterrows():
        cells = table.rows[i+1].cells
        cells[0].text = str(row["Key Point"])
        cells[1].text = str(row["Action Plan"])
        cells[2].text = str(row["Assigned"])

    # Save to BytesIO
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# ========== STREAMLIT UI ==========
st.set_page_config(page_title="Voice Assistant", layout="wide")
st.title("🎤 Voice Transcriber + Summarizer")
st.markdown("Powered by **Groq Whisper** (free) + **Puter AI** (free)")

# Initialize session state
if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""
if "key_points" not in st.session_state:
    st.session_state["key_points"] = []
if "df" not in st.session_state:
    st.session_state["df"] = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])

# ---- Step 1: Upload & Transcribe ----
uploaded = st.file_uploader("Upload voice recording", type=["wav", "mp3", "m4a", "ogg", "flac", "mp4", "webm"])

col1, col2 = st.columns([1, 1])
with col1:
    if uploaded and st.button("🔊 Transcribe"):
        with st.spinner("Transcribing with Groq Whisper..."):
            transcript = transcribe_audio(uploaded.read())
        if transcript:
            st.session_state["transcript"] = transcript
            st.success("Transcription complete!")
            # Clear previous summary
            st.session_state["key_points"] = []
            st.session_state["df"] = pd.DataFrame(columns=["Key Point", "Action Plan", "Assigned"])
            st.rerun()

# Display transcript
if st.session_state["transcript"]:
    st.subheader("📋 Full Transcript")
    st.text_area("Transcript", st.session_state["transcript"], height=150)

# ---- Step 2: Summarize ----
if st.session_state["transcript"] and not st.session_state["key_points"]:
    if st.button("📝 Generate Key Points"):
        with st.spinner("Summarizing with Puter AI..."):
            points = summarize_text(st.session_state["transcript"])
        if points:
            st.session_state["key_points"] = points
            # Initialize dataframe with key points
            df = pd.DataFrame({
                "Key Point": points,
                "Action Plan": [""] * len(points),
                "Assigned": [""] * len(points)
            })
            st.session_state["df"] = df
            st.success("Key points generated!")
            st.rerun()

# ---- Step 3: Edit Key Points ----
if not st.session_state["df"].empty:
    st.subheader("✏️ Edit Key Points & Add Action Plan / Assigned")
    st.markdown("Modify the table below. The columns **Action Plan** and **Assigned** are for you to fill in.")
    
    edited_df = st.data_editor(
        st.session_state["df"],
        num_rows="dynamic",  # allow adding/removing rows
        use_container_width=True,
        key="data_editor"
    )
    # Update session state with any changes
    st.session_state["df"] = edited_df

    # ---- Step 4: Export ----
    if st.button("📄 Export to Word"):
        if st.session_state["df"].empty:
            st.warning("No key points to export.")
        else:
            doc_bio = export_to_word(st.session_state["df"])
            st.download_button(
                label="⬇️ Download Word Document",
                data=doc_bio,
                file_name="summary_report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
else:
    if st.session_state["transcript"]:
        st.info("Click 'Generate Key Points' to create the summary table.")
    else:
        st.info("Upload an audio file and transcribe it first.")

# Optional: Display raw transcript if needed
st.markdown("---")
st.caption("Built with Streamlit · Groq Whisper · Puter AI · python-docx")
