import os
import streamlit as st
import requests
import json
import pandas as pd
import re
from io import BytesIO
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ========== CONFIG ==========
st.set_page_config(page_title="Project Echo | Minutes Maker", layout="wide", initial_sidebar_state="collapsed")

# --- PROGRAMMATIC LIGHT MODE LOCK ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write("[theme]\nbase=\"light\"\n")

# API Keys & Endpoints
GROQ_API_KEY = "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"
GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

# Puter AI Fallback setup (Requires your Puter Auth Token)
PUTER_API_KEY = "YOUR_PUTER_AUTH_TOKEN_HERE" 
PUTER_CHAT_URL = "https://api.puter.com/puterai/openai/v1/chat/completions"

# ========== CUSTOM CSS INJECTION ==========
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600&family=Playfair+Display:ital,wght@1,400;1,500&display=swap');

    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    
    .stApp {
        background-color: #F4F2EC; 
        background-image: linear-gradient(rgba(0, 0, 0, 0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 0, 0, 0.02) 1px, transparent 1px);
        background-size: 80px 80px; color: #333333;
    }
    .stApp > header { display: none !important; }
    .block-container { padding-top: 6rem !important; }

    .echo-topbar {
        position: fixed; top: 0; left: 0; right: 0; height: 70px; background-color: #161616;
        border-bottom: 1px solid #333333; display: flex; align-items: center; padding: 0 2rem; z-index: 999999; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .echo-topbar .logo-wrapper { display: flex; align-items: center; gap: 0.75rem; }
    .echo-topbar h1 { font-family: 'Playfair Display', serif !important; font-style: italic !important; font-size: 1.5rem !important; color: #FFFFFF !important; margin: 0 !important; }
    .echo-topbar h1 span { color: #D4AF37 !important; }

    h3 { font-family: 'Playfair Display', serif !important; font-style: italic !important; font-weight: 400 !important; color: #1A2B4C !important; }
    [data-testid="stVerticalBlockBorderWrapper"] { background-color: #FFFFFF !important; border-radius: 16px !important; box-shadow: 0 12px 40px rgba(0, 0, 0, 0.06) !important; padding: 1.5rem !important; margin-bottom: 1.5rem !important; }

    .stButton > button, .stDownloadButton > button { background-color: #222222 !important; color: #FFFFFF !important; border-radius: 50px !important; transition: all 0.3s ease !important; width: 100% !important; }
    .stButton > button:hover, .stDownloadButton > button:hover { border-color: #D4AF37 !important; color: #D4AF37 !important; background-color: #1A1A1A !important; }
</style>
"""

# ========== CORE LOGIC ==========
def transcribe_audio(audio_bytes):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {
        "file": ("audio.wav", audio_bytes),
        "model": (None, "whisper-large-v3-turbo"),
        "response_format": (None, "json")
    }
    resp = requests.post(GROQ_AUDIO_URL, headers=headers, files=files)
    if resp.status_code == 200:
        return resp.json().get("text", "")
    else:
        st.error(f"Transcription failed: {resp.text}")
        return None

def extract_structured_insights(transcript, user_instruction="", current_data=None):
    prompt = f"""
    You are an AI Executive Assistant extracting formal Meeting Minutes.
    Analyze the transcript and output a valid JSON object matching this strict schema:
    {{
        "Title": "Meeting Subject / Title (e.g. PRIME PHILIPPINES & MR. ABCD)",
        "Date": "Date of meeting (e.g. July 22, 2026)",
        "Time": "Time of meeting (e.g. 2:30pm to 9:00pm)",
        "Location": "Location of meeting",
        "Attendees": "List of attendees (e.g. Mr. ABCD, XYZ Company\\nMr. Jet Yu...)",
        "MetWith": "The external party or client met with",
        "Table": [
            {{
                "Discussion Points": "Main topic/phase",
                "Action Plan": "Concrete next steps",
                "Indicative Delivery Date": "Deadline/Q1/Date",
                "Person-in-charge": "Assigned person/entity"
            }}
        ],
        "Other Discussions": "Numbered list or paragraphs of other matters discussed",
        "Prepared By": "Name\\nRole\\nCompany of the preparer",
        "Confirmed By": "Name\\nCompany of confirming party"
    }}

    Transcript: {transcript}
    Context/Current Data: {current_data if current_data else "None"}
    User Instruction: {user_instruction if user_instruction else "Extract comprehensive meeting minutes."}
    
    Respond ONLY with raw JSON. Do not use markdown blocks.
    """
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    try:
        # Try Groq First
        resp = requests.post(GROQ_CHAT_URL, headers=headers, json=payload)
        resp.raise_for_status()
        raw_content = resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        st.warning(f"Groq AI failed ({e}). Falling back to Puter AI...")
        # Fallback to Puter AI
        headers_puter = {"Authorization": f"Bearer {PUTER_API_KEY}", "Content-Type": "application/json"}
        payload["model"] = "gpt-4o" # Switch model tag for Puter if preferred
        try:
            resp = requests.post(PUTER_CHAT_URL, headers=headers_puter, json=payload)
            resp.raise_for_status()
            raw_content = resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e2:
            st.error(f"Both Groq and Puter AI failed. Error: {e2}")
            return None

    clean_json = re.sub(r"^```json\s*|^```\s*|\s*```$", "", raw_content, flags=re.MULTILINE).strip()
    try:
        data = json.loads(clean_json)
        # Normalize Table
        if "Table" not in data or not data["Table"]:
            data["Table"] = [{"Discussion Points": "", "Action Plan": "", "Indicative Delivery Date": "", "Person-in-charge": ""}]
        return data
    except json.JSONDecodeError:
        st.error("Failed to parse AI output as JSON.")
        return None

def export_to_word(meta, df):
    doc = Document()
    doc.sections[0].orientation = 0
    
    title = doc.add_heading("MINUTES OF THE MEETING", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(meta.get("Title", "")).alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph(f"Date: {meta.get('Date', '')}, {meta.get('Time', '')}")
    doc.add_paragraph(f"Location: {meta.get('Location', '')}")
    doc.add_paragraph(f"Attended by:\n{meta.get('Attendees', '')}")
    
    doc.add_paragraph(f"\nDuring the meeting held last {meta.get('Date', '')}, our team, represented by the attendee/s shown above, met with {meta.get('MetWith', '')} to discuss opportunities for collaboration.")
    
    doc.add_heading("Discussion Points & Action Plan", level=2)
    table = doc.add_table(rows=len(df)+1, cols=4)
    table.style = "Table Grid"
    headers = ["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]
    for i, header in enumerate(headers):
        run = table.rows[0].cells[i].paragraphs[0].add_run(header)
        run.font.bold = True
    
    for i, row in df.iterrows():
        cells = table.rows[i+1].cells
        cells[0].text = str(row.get("Discussion Points", ""))
        cells[1].text = str(row.get("Action Plan", ""))
        cells[2].text = str(row.get("Indicative Delivery Date", ""))
        cells[3].text = str(row.get("Person-in-charge", ""))
        
    doc.add_paragraph("\n*Note: The indicative delivery date serves as reference point and still subject to changes. Furthermore, it depends on the progress of the both parties.\n")
    
    doc.add_heading("Other Discussions:", level=2)
    doc.add_paragraph(meta.get("Other Discussions", ""))
    
    doc.add_paragraph("\nPrepared by:")
    doc.add_paragraph("_______________________________")
    doc.add_paragraph(meta.get("Prepared By", ""))
    
    doc.add_paragraph("\nConfirmed by:")
    doc.add_paragraph("_______________________________")
    doc.add_paragraph(meta.get("Confirmed By", ""))
    
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# ========== STREAMLIT UI SETUP ==========
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown('<div class="echo-topbar"><div class="logo-wrapper"><h1>Project <span>Echo</span></h1></div></div>', unsafe_allow_html=True)

# Initialize Session State
if "transcript" not in st.session_state: st.session_state["transcript"] = ""
if "meta" not in st.session_state: 
    st.session_state["meta"] = {"Title": "", "Date": "", "Time": "", "Location": "", "Attendees": "", "MetWith": "", "Other Discussions": "", "Prepared By": "", "Confirmed By": ""}
if "df" not in st.session_state:
    st.session_state["df"] = pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"])
if "chat_history" not in st.session_state: st.session_state["chat_history"] = []

# ---- Step 1: Input Audio Card ----
with st.container(border=True):
    st.markdown("<h3>Upload Audio</h3>", unsafe_allow_html=True)
    audio_data = None
    uploaded = st.file_uploader("Upload recording", type=["wav", "mp3", "m4a"], label_visibility="collapsed")
    if uploaded: audio_data = uploaded.read()
    
    if audio_data and st.button("Transcribe Audio"):
        with st.spinner("Transcribing..."):
            transcript = transcribe_audio(audio_data)
        if transcript:
            st.session_state["transcript"] = transcript
            st.rerun()

# ---- Step 2: Transcript & Analysis ----
if st.session_state["transcript"]:
    with st.container(border=True):
        st.markdown("<h3>Transcript</h3>", unsafe_allow_html=True)
        st.text_area("Content", st.session_state["transcript"], height=100)
        
        if st.button("Generate Minutes of Meeting"):
            with st.spinner("Extracting meeting insights via Groq/Puter AI..."):
                extracted_data = extract_structured_insights(st.session_state["transcript"])
                if extracted_data:
                    st.session_state["df"] = pd.DataFrame(extracted_data.pop("Table"))
                    st.session_state["meta"].update(extracted_data)
                    st.rerun()

# ---- Step 3: Editor Layout ----
if not st.session_state["df"].empty:
    col_chat, col_editor = st.columns([3, 7], gap="medium")
    
    with col_chat:
        with st.container(border=True):
            st.markdown("<h3>AI Assistant</h3>", unsafe_allow_html=True)
            for msg in st.session_state["chat_history"]:
                st.chat_message(msg["role"]).write(msg["content"])
            
            prompt = st.chat_input("Ask AI to modify the table...")
            if prompt:
                st.session_state["chat_history"].append({"role": "user", "content": prompt})
                context = {"meta": st.session_state["meta"], "df": st.session_state["df"].to_dict("records")}
                updated_data = extract_structured_insights(st.session_state["transcript"], prompt, context)
                if updated_data:
                    st.session_state["df"] = pd.DataFrame(updated_data.pop("Table"))
                    st.session_state["meta"].update(updated_data)
                    st.session_state["chat_history"].append({"role": "assistant", "content": "Updated the minutes!"})
                st.rerun()

    with col_editor:
        with st.container(border=True):
            st.markdown("<h3>Minutes Editor</h3>", unsafe_allow_html=True)
            
            # Form Overrides
            st.session_state["meta"]["Title"] = st.text_input("Meeting Title", st.session_state["meta"]["Title"])
            c1, c2, c3 = st.columns(3)
            st.session_state["meta"]["Date"] = c1.text_input("Date", st.session_state["meta"]["Date"])
            st.session_state["meta"]["Time"] = c2.text_input("Time", st.session_state["meta"]["Time"])
            st.session_state["meta"]["Location"] = c3.text_input("Location", st.session_state["meta"]["Location"])
            
            c4, c5 = st.columns(2)
            st.session_state["meta"]["Attendees"] = c4.text_area("Attendees", st.session_state["meta"]["Attendees"], height=80)
            st.session_state["meta"]["MetWith"] = c5.text_area("Met With", st.session_state["meta"]["MetWith"], height=80)
            
            st.markdown("#### Discussion Points & Action Plan")
            edited_df = st.data_editor(st.session_state["df"], num_rows="dynamic", use_container_width=True)
            st.session_state["df"] = edited_df
            
            st.session_state["meta"]["Other Discussions"] = st.text_area("Other Discussions", st.session_state["meta"]["Other Discussions"], height=100)
            
            c6, c7 = st.columns(2)
            st.session_state["meta"]["Prepared By"] = c6.text_area("Prepared By", st.session_state["meta"]["Prepared By"], height=80)
            st.session_state["meta"]["Confirmed By"] = c7.text_area("Confirmed By", st.session_state["meta"]["Confirmed By"], height=80)
            
            doc_file = export_to_word(st.session_state["meta"], st.session_state["df"])
            st.download_button("Download Word Document", data=doc_file, file_name="Meeting_Minutes.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
