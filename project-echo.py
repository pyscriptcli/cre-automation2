import os
import streamlit as st
import requests
import json
import pandas as pd
import re
import datetime
from io import BytesIO
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ========== CONFIG ==========
st.set_page_config(page_title="Project Echo | Voice App", layout="wide", initial_sidebar_state="collapsed")

# --- PROGRAMMATIC LIGHT MODE LOCK ---
_config_dir = ".streamlit"
_config_file = os.path.join(_config_dir, "config.toml")
if not os.path.exists(_config_file):
    os.makedirs(_config_dir, exist_ok=True)
    with open(_config_file, "w", encoding="utf-8") as f:
        f.write('[theme]\nbase="light"\n')

# API Keys & Endpoints
GROQ_API_KEY = "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"
GROQ_AUDIO_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

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
    position: fixed; top: 0; left: 0; right: 0; height: 70px;
    background-color: #161616;
    background-image: linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
    background-size: 80px 80px; border-bottom: 1px solid #333333;
    display: flex; align-items: center; padding: 0 2rem;
    z-index: 999999; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}
.echo-topbar .logo-wrapper { display: flex; align-items: center; gap: 0.75rem; }
.echo-topbar h1 {
    font-family: 'Playfair Display', serif !important; font-style: italic !important;
    font-weight: 400 !important; font-size: 1.5rem !important; color: #FFFFFF !important; margin: 0 !important; padding: 0 !important;
}
.echo-topbar h1 span { color: #D4AF37 !important; }

h3 {
    font-family: 'Playfair Display', serif !important; font-style: italic !important;
    font-weight: 400 !important; color: #1A2B4C !important; letter-spacing: 0.02em; margin-bottom: 0.5rem;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important; border-radius: 16px !important;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.06) !important; border: 1px solid rgba(0, 0, 0, 0.03) !important; 
    padding: 1.5rem !important; margin-bottom: 1.5rem !important;
}

.stButton > button, .stDownloadButton > button {
    background-color: #222222 !important; color: #FFFFFF !important;
    border: 1px solid #444444 !important; border-radius: 50px !important; 
    font-family: 'Montserrat', sans-serif !important; font-weight: 500 !important;
    letter-spacing: 0.5px; padding: 0.5rem 1.75rem !important;
    transition: all 0.3s ease !important; display: inline-flex;
    align-items: center; justify-content: center; width: 100% !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: #D4AF37 !important; color: #D4AF37 !important;
    background-color: #1A1A1A !important; box-shadow: 0 4px 15px rgba(212, 175, 55, 0.15) !important;
}

[data-testid="stFileUploadDropzone"] {
    background-color: #FDFDFD !important; border: 1px dashed #CCC !important;
    border-radius: 12px !important; padding: 2.5rem !important; transition: all 0.2s ease !important;
}
[data-testid="stFileUploadDropzone"]:hover { border-color: #1A2B4C !important; background-color: #F8FAFC !important; }

.stTextArea textarea {
    background-color: #FDFDFD !important; border: 1px solid #E5E5E5 !important;
    color: #333 !important; border-radius: 12px !important; padding: 1rem !important;
    font-size: 0.95rem !important; line-height: 1.6 !important;
    box-shadow: inset 0 2px 5px rgba(0,0,0,0.02) !important;
}

[data-testid="stDataFrame"] { border-radius: 0 0 8px 8px; overflow: hidden; border: 1px solid #E5E5E5; }

.chat-scroll-container { max-height: 480px; overflow-y: auto; padding-right: 8px; margin-bottom: 1rem; }
[data-testid="stChatMessage"] {
    background-color: #F8F7F2 !important; border: 1px solid #E8E5DD !important;
    border-radius: 12px !important; margin-bottom: 0.75rem !important;
}
</style>
"""

# ========== CORE LOGIC ==========
def transcribe_audio(audio_bytes):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {"file": ("audio.wav", audio_bytes), "model": (None, "whisper-large-v3-turbo"), "response_format": (None, "json")}
    resp = requests.post(GROQ_AUDIO_URL, headers=headers, files=files)
    if resp.status_code == 200:
        return resp.json().get("text", "")
    else:
        st.error(f"Transcription failed: {resp.text}")
        return None

def parse_json_robust(text):
    """Bulletproof JSON extraction for LLM outputs."""
    # Strip markdown code blocks
    text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    text = text.strip()
    
    # 1. Try direct parse
    try: return json.loads(text)
    except json.JSONDecodeError: pass
        
    # 2. Extract first { ... } block
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try: return json.loads(match.group(0))
        except json.JSONDecodeError: pass
            
    # 3. If it returned an array instead of object, wrap it
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try: 
            items = json.loads(match.group(0))
            return {"action_items": items, "other_discussions": ""}
        except json.JSONDecodeError: pass
            
    return None

def extract_structured_insights(transcript, user_instruction="", current_df=None):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    context_data = ""
    if current_df is not None and not current_df.empty:
        context_data = f"\nCurrent Table State:\n{current_df.to_json(orient='records')}\n"

    prompt = f"""
    You are an expert AI executive assistant. Extract meeting minutes from the transcript.
    Return a valid JSON object with exactly two keys: "action_items" and "other_discussions".
    
    "action_items" must be an array of objects:
    [
      {{
        "Discussion Points": "Main topic or deliverable discussed",
        "Action Plan": "Concrete next steps or requirements",
        "Indicative Delivery Date": "Specific date, timeframe (e.g., Q1 2027), or 'TBD'",
        "Person-in-charge": "Name or team assigned (e.g., PRIME, XYZ, John Doe)"
      }}
    ]
    
    "other_discussions" must be a string summarizing secondary topics not requiring direct action.
    
    Transcript:
    {transcript}
    {context_data}
    User Instruction:
    {user_instruction if user_instruction else "Extract all action items, dates, and assignees. Summarize other discussions."}
    
    Output ONLY raw JSON. No markdown, no explanations.
    """

    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    
    # Primary: 70B (Best at JSON), Fallback: 8B
    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    
    for model in models:
        payload["model"] = model
        try:
            resp = requests.post(GROQ_CHAT_URL, headers=headers, json=payload)
            if resp.status_code == 200:
                raw_content = resp.json()["choices"][0]["message"]["content"]
                data = parse_json_robust(raw_content)
                
                if data:
                    items = data.get("action_items", [])
                    df = pd.DataFrame(items)
                    for col in ["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]:
                        if col not in df.columns: df[col] = ""
                    df = df[["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]]
                    return df, data.get("other_discussions", "")
        except Exception as e:
            continue
            
    st.warning("AI Extraction failed. Please try again or edit manually.")
    return pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]), ""

def export_to_word(df, transcript, meeting_details, other_discussions):
    doc = Document()
    
    # Header
    title = doc.add_heading("MINUTES OF THE MEETING", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    company = meeting_details.get("company_name", "[Client/Company]")
    subtitle = doc.add_heading(f"PRIME PHILIPPINES & {company.upper()}", level=2)
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Metadata
    date_str = meeting_details.get("date", "____________")
    doc.add_paragraph(f"Date: {date_str}")
    doc.add_paragraph(f"Location: {meeting_details.get('location', '____________')}")
    
    # Attendees formatting
    attendees = meeting_details.get("attendees", "____________")
    att_para = doc.add_paragraph()
    att_run = att_para.add_run("Attended by: ")
    att_run.bold = True
    att_para.add_run(attendees)
    
    # Intro
    doc.add_paragraph(f"During the meeting held last {date_str}, PRIME Philippines, represented by the attendee/s shown above, met with {company} to discuss opportunities for collaboration.")
    
    # Table
    doc.add_paragraph()
    table = doc.add_table(rows=len(df)+1, cols=4)
    table.style = "Table Grid"
    hdr_cells = table.rows[0].cells
    headers = ["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"]
    for i, header in enumerate(headers):
        hdr_cells[i].text = header
        run = hdr_cells[i].paragraphs[0].runs[0]
        run.font.bold = True
        run.font.color.rgb = RGBColor(26, 43, 76)
        
    for i, row in df.iterrows():
        cells = table.rows[i+1].cells
        cells[0].text = str(row.get("Discussion Points", ""))
        cells[1].text = str(row.get("Action Plan", ""))
        cells[2].text = str(row.get("Indicative Delivery Date", ""))
        cells[3].text = str(row.get("Person-in-charge", ""))
        
    # Note
    doc.add_paragraph("*Note: The indicative delivery date serves as reference point and still subject to changes. Furthermore, it depends on the progress of the both parties.")
    
    # Other Discussions
    if other_discussions:
        doc.add_heading("Other Discussions:", level=2)
        doc.add_paragraph(other_discussions)
        
    # Signatures
    doc.add_paragraph()
    doc.add_paragraph("Prepared by:")
    doc.add_paragraph("_______________________________")
    doc.add_paragraph("AVP for Capital Markets")
    doc.add_paragraph("PRIME Philippines")
    
    doc.add_paragraph()
    doc.add_paragraph("Confirmed by:")
    doc.add_paragraph("_________________________________")
    doc.add_paragraph(f"{company}")
    
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# ========== STREAMLIT UI SETUP ==========
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Topbar
topbar_html = """
<div class="echo-topbar">
 <div class="logo-wrapper">
 <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#D4AF37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
 <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
 <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path> <line x1="12" y1="19" x2="12" y2="22"></line>
 </svg>
 <h1>Project <span>Echo</span></h1>
 </div>
</div>
"""
st.markdown(topbar_html, unsafe_allow_html=True)

# Initialize Session State
if "transcript" not in st.session_state: st.session_state["transcript"] = ""
if "df" not in st.session_state: st.session_state["df"] = pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"])
if "other_discussions" not in st.session_state: st.session_state["other_discussions"] = ""
if "chat_history" not in st.session_state: st.session_state["chat_history"] = []
if "meeting_details" not in st.session_state: 
    st.session_state["meeting_details"] = {"date": "", "location": "", "company_name": "", "attendees": ""}

# CRD Team Preset
CRD_TEAM = [
    "Sondi Tuazon", "Kristina Balajadia", "Meliza Zapata", "Dykstra Pineda", 
    "Cedtrix Rena", "Carlo Medina", "Dave Policarpio", "Irish Rima"
]

# ---- Step 1: Meeting Details & Audio ----
with st.container(border=True):
    st.markdown('<h3 style="display: flex; align-items: center;"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#D4AF37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 12px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg> Meeting Details & Audio Input</h3>', unsafe_allow_html=True)
    
    # Date & Time Pickers
    col_dt1, col_dt2, col_dt3 = st.columns([2, 1, 1])
    with col_dt1:
        meeting_date = st.date_input("Meeting Date", value=datetime.date.today())
    with col_dt2:
        start_time = st.time_input("Start Time", value=datetime.time(14, 0))
    with col_dt3:
        end_time = st.time_input("End Time", value=datetime.time(17, 0))
        
    # Format Date/Time string for Word Doc
    date_str = meeting_date.strftime("%B %d, %Y")
    time_str = f"{start_time.strftime('%I:%M%p').lstrip('0').lower()} to {end_time.strftime('%I:%M%p').lstrip('0').lower()}"
    st.session_state["meeting_details"]["date"] = f"{date_str}, {time_str}"
    
    col_loc, col_comp = st.columns(2)
    with col_loc: st.session_state["meeting_details"]["location"] = st.text_input("Location", value=st.session_state["meeting_details"].get("location", ""))
    with col_comp: st.session_state["meeting_details"]["company_name"] = st.text_input("Client/Company", value=st.session_state["meeting_details"].get("company_name", ""))
    
    # Attendees Management
    st.markdown("##### Attendees")
    selected_team = st.multiselect(
        "Internal Team (CRD) - Uncheck if absent", 
        CRD_TEAM, 
        default=CRD_TEAM,
        help="All CRD members are selected by default. Uncheck those who did not attend."
    )
    external_attendees = st.text_input("External Attendees / Guests", placeholder="e.g., Mr. ABCD (XYZ Company), John Doe")
    
    # Combine Attendees
    all_attendees = selected_team.copy()
    if external_attendees:
        all_attendees.extend([name.strip() for name in external_attendees.split(",") if name.strip()])
    st.session_state["meeting_details"]["attendees"] = ", ".join(all_attendees) if all_attendees else "None"
    
    st.divider()
    tab1, tab2 = st.tabs(["Upload File", "Record Audio"])
    audio_data = None
    with tab1:
        uploaded = st.file_uploader("Upload recording", type=["wav", "mp3", "m4a", "ogg", "flac", "mp4", "webm"], label_visibility="collapsed")
        if uploaded: audio_data = uploaded.read()
    with tab2:
        st.write("Record directly from your microphone:")
        recorded_audio = st.audio_input("Record Audio", label_visibility="collapsed")
        if recorded_audio: audio_data = recorded_audio.read()

    if audio_data:
        col_btn, _ = st.columns([2, 8])
        with col_btn:
            if st.button("Transcribe Audio"):
                with st.spinner("Processing audio with Groq Whisper..."):
                    transcript = transcribe_audio(audio_data)
                if transcript:
                    st.session_state["transcript"] = transcript
                    st.session_state["df"] = pd.DataFrame(columns=["Discussion Points", "Action Plan", "Indicative Delivery Date", "Person-in-charge"])
                    st.session_state["other_discussions"] = ""
                    st.session_state["chat_history"] = [] # Cleared initial message as requested
                    st.rerun()

# ---- Step 2: Transcript & Generation ----
if st.session_state["transcript"]:
    with st.container(border=True):
        st.markdown('<h3 style="display: flex; align-items: center;"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#D4AF37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 12px;"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg> Full Transcript</h3>', unsafe_allow_html=True)
        st.text_area("Transcript Content", st.session_state["transcript"], height=150, label_visibility="collapsed")
        
        if st.session_state["df"].empty:
            col_gen, _ = st.columns([2, 8])
            with col_gen:
                if st.button("Generate MOM"):
                    with st.spinner("Analyzing transcript and generating Minutes of Meeting..."):
                        extracted_df, other_disc = extract_structured_insights(st.session_state["transcript"])
                    if not extracted_df.empty:
                        st.session_state["df"] = extracted_df
                        st.session_state["other_discussions"] = other_disc
                        st.session_state["chat_history"].append({"role": "assistant", "content": "MOM generated. You can edit the table below or chat to refine."})
                        st.rerun()

# ---- Step 3: Split Layout (AI Chatbot | Live Editor) ----
if not st.session_state["df"].empty or st.session_state["transcript"]:
    col_chat, col_editor = st.columns([4, 6], gap="medium")
    
    # === LEFT COLUMN: AI Assistant ===
    with col_chat:
        with st.container(border=True):
            st.markdown('<h3 style="display: flex; align-items: center;"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#D4AF37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 12px;"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg> Assistant</h3>', unsafe_allow_html=True)
            
            st.markdown('<div class="chat-scroll-container">', unsafe_allow_html=True)
            for msg in st.session_state["chat_history"]:
                with st.chat_message(msg["role"]): st.write(msg["content"])
            st.markdown('</div>', unsafe_allow_html=True)
            
            user_prompt = st.chat_input("E.g., 'Change delivery date to Q2', 'Add action item for John'...")
            if user_prompt:
                st.session_state["chat_history"].append({"role": "user", "content": user_prompt})
                with st.spinner("Updating MOM..."):
                    updated_df, _ = extract_structured_insights(
                        st.session_state["transcript"],
                        user_instruction=user_prompt,
                        current_df=st.session_state["df"]
                    )
                if not updated_df.empty:
                    st.session_state["df"] = updated_df
                    bot_reply = "I have updated the MOM table with your requested changes."
                else:
                    bot_reply = "I couldn't process that request. Please try rephrasing."
                st.session_state["chat_history"].append({"role": "assistant", "content": bot_reply})
                st.rerun()

    # === RIGHT COLUMN: Live Table Editor & Export ===
    with col_editor:
        with st.container(border=True):
            st.markdown('<h3 style="display: flex; align-items: center;"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#D4AF37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 12px;"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg> MOM Editor</h3>', unsafe_allow_html=True)
            
            edited_df = st.data_editor(
                st.session_state["df"],
                num_rows="dynamic",
                use_container_width=True,
                key="action_editor", 
                hide_index=False, 
                column_config={
                    "Discussion Points": st.column_config.TextColumn("Discussion Points", width="large"),
                    "Action Plan": st.column_config.TextColumn("Action Plan", width="medium"),
                    "Indicative Delivery Date": st.column_config.TextColumn("Indicative Delivery Date", width="small"),
                    "Person-in-charge": st.column_config.TextColumn("Person-in-charge", width="small")
                }
            )
            st.session_state["df"] = edited_df
            
            st.session_state["other_discussions"] = st.text_area("Other Discussions", value=st.session_state["other_discussions"], height=100)
            
            st.write("")
            doc_bio = export_to_word(
                st.session_state["df"], 
                st.session_state["transcript"], 
                st.session_state["meeting_details"],
                st.session_state["other_discussions"]
            )
            st.download_button(
                label="Export Minutes of Meeting (Word)",
                data=doc_bio,
                file_name="MOM_Report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
