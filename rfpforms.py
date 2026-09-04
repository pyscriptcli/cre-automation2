import streamlit as st
import pandas as pd
import json
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="Request For Payment", layout="wide")

st.markdown("""
    <style>
    .stApp { max-width: 950px; margin: 0 auto; }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    div[data-testid="stVerticalBlock"] > div { margin-bottom: -10px; }
    .header-blue { color: #002B5B; font-weight: bold; font-family: sans-serif; text-align: center;}
    .title-box { background-color: #002B5B; color: white; text-align: center; font-weight: bold; padding: 4px; font-size: 18px; border: 1px solid #002B5B; margin-top: 5px;}
    .red-italic { color: red; font-style: italic; font-weight: bold; font-size: 11px;}
    hr { margin: 5px 0; border-bottom: 1.5px solid black; }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
col1, col2 = st.columns([2.5, 1], gap="small")
with col1:
    st.markdown("<div class='header-blue' style='font-size:20px; line-height: 1;'>PROPERTY INTERACTIVE MARKETING ENTERPRISE<br>REALTY CORP</div>", unsafe_allow_html=True)
with col2:
    st.markdown("<div style='text-align: right; color:#002B5B; font-weight:bold; font-size:20px; line-height: 1;'>PRIME <span style='font-size:10px; font-style:italic;'>Philippines >></span></div>", unsafe_allow_html=True)
    st.markdown("<div class='title-box'>REQUEST FOR PAYMENT</div>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# --- TOP INPUTS ---
col_date, col_payee, col_dept = st.columns([1, 2, 1.5], gap="small")
with col_date:
    date = st.date_input("DATE:", label_visibility="collapsed")
with col_payee:
    payee = st.text_input("PAYEE:", placeholder="PAYEE", label_visibility="collapsed")
with col_dept:
    department = st.text_input("DEPARTMENT:", placeholder="DEPARTMENT", label_visibility="collapsed")

st.markdown("<hr>", unsafe_allow_html=True)

# --- DATA TABLE & AUTO-COMPUTE ---
if 'table_data' not in st.session_state:
    st.session_state.table_data = pd.DataFrame([{"ITEMS/DESCRIPTION": "", "QTY": 0.0, "UNIT": "", "UNIT PRICE": 0.0, "AMOUNT": 0.0} for _ in range(5)])

edited_df = st.data_editor(
    st.session_state.table_data,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    disabled=["AMOUNT"],
    column_config={
        "QTY": st.column_config.NumberColumn("QTY", min_value=0.0, step=1.0),
        "UNIT PRICE": st.column_config.NumberColumn("UNIT PRICE", min_value=0.0, step=0.01, format="%.2f"),
        "AMOUNT": st.column_config.NumberColumn("AMOUNT", format="%.2f")
    }
)

edited_df['AMOUNT'] = edited_df['QTY'] * edited_df['UNIT PRICE']
total_amount = float(edited_df['AMOUNT'].sum())

if not edited_df.equals(st.session_state.table_data):
    st.session_state.table_data = edited_df
    st.rerun()

st.markdown(f"<div style='text-align: right; font-weight: bold; font-size: 14px;'>TOTAL AMOUNT &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {total_amount:,.2f}</div>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# --- PURPOSE & PAYMENT ---
purpose = st.text_area("Purpose:", height=68, label_visibility="collapsed", placeholder="Purpose:")

col_c1, col_c2, col_c3, col_c4 = st.columns([1, 1, 1, 2], gap="small")
with col_c1: st.markdown("**Payment Details:**")
with col_c2: cash = st.checkbox("Cash")
with col_c3: check = st.checkbox("Check")
with col_c4: online = st.checkbox("Online Payment/Bank Transfer")

col_bank, col_remarks = st.columns([2, 1.5], gap="small")
with col_bank:
    st.markdown("<div class='red-italic'>*If not applicable kindly put N/A</div>", unsafe_allow_html=True)
    bank = st.text_input("Bank", placeholder="Bank", label_visibility="collapsed")
    account_name = st.text_input("Account Name", placeholder="Account Name", label_visibility="collapsed")
    account_number = st.text_input("Account Number", placeholder="Account Number", label_visibility="collapsed")
with col_remarks:
    st.write("Remarks:")
    col_r1, col_r2 = st.columns(2)
    with col_r1: urgent = st.checkbox("Urgent")
    with col_r2: not_urgent = st.checkbox("Not urgent")
    date_needed = st.date_input("Date Needed (M-D-Y):", label_visibility="collapsed")

st.markdown("<hr>", unsafe_allow_html=True)

# --- E-SIGNATURES ---
def create_canvas(key_name):
    return st_canvas(stroke_width=2, stroke_color="black", background_color="#eeeeee", height=60, width=220, drawing_mode="freedraw", key=key_name)

col_sig1, col_sig2, col_sig3 = st.columns(3, gap="small")
with col_sig1:
    st.markdown("<span style='font-size:12px;'>Requested By:</span>", unsafe_allow_html=True)
    req_canvas = create_canvas("canvas_req")
    req_name = st.text_input("Signature Over Printed Name", key="req_name", placeholder="Printed Name", label_visibility="collapsed")
    req_remarks = st.text_input("Remarks:", key="req_remarks", placeholder="Remarks", label_visibility="collapsed")

with col_sig2:
    st.markdown("<span style='font-size:12px;'>Approved By:</span>", unsafe_allow_html=True)
    app_canvas = create_canvas("canvas_app")
    app_name = st.text_input("Signature Over Printed Name", key="app_name", placeholder="Printed Name", label_visibility="collapsed")
    st.markdown("<div style='font-size:11px; text-align:center;'>Team Leader/Co-TL</div>", unsafe_allow_html=True)

with col_sig3:
    st.markdown("<span style='font-size:12px;'>Received By:</span>", unsafe_allow_html=True)
    rec_canvas = create_canvas("canvas_rec")
    rec_name = st.text_input("Signature Over Printed Name", key="rec_name", placeholder="Printed Name", label_visibility="collapsed")
    st.markdown("<div style='font-size:11px; text-align:center;'>Finance Officer</div>", unsafe_allow_html=True)

# --- JSON EXPORT ---
payment_methods = [method for method, checked in zip(["Cash", "Check", "Online Payment/Bank Transfer"], [cash, check, online]) if checked]
urgency_status = "Urgent" if urgent else "Not urgent" if not_urgent else ""

def has_signature(canvas_result):
    if canvas_result is not None and canvas_result.json_data is not None:
        return len(canvas_result.json_data.get("objects", [])) > 0
    return False

form_data = {
    "Document_Info": {"Company": "PROPERTY INTERACTIVE MARKETING ENTERPRISE", "Entity": "PRIME Philippines, REALTY CORP", "Form_Type": "REQUEST FOR PAYMENT"},
    "Basic_Details": {"Date": str(date), "Payee": payee, "Department": department},
    "Items": edited_df.fillna("").astype(str).to_dict(orient="records"),
    "Total_Amount": total_amount,
    "Purpose": purpose,
    "Payment_Details": {"Method": payment_methods, "Bank": bank, "Account_Name": account_name, "Account_Number": account_number},
    "Status": {"Urgency": urgency_status, "Date_Needed": str(date_needed)},
    "Signatures": {
        "Requested_By": {"Name": req_name, "Remarks": req_remarks, "Signed": has_signature(req_canvas)},
        "Approved_By": {"Name": app_name, "Role": "Team Leader/Co-TL", "Signed": has_signature(app_canvas)},
        "Received_By": {"Name": rec_name, "Role": "Finance Officer", "Signed": has_signature(rec_canvas)}
    }
}

st.download_button(label="Export Completed Form to JSON", data=json.dumps(form_data, indent=4), file_name="RFP_Completed.json", mime="application/json")
