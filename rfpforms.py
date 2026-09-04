import streamlit as st
import pandas as pd
import json
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="Request For Payment", layout="wide")

st.markdown("""
    <style>
    .stApp { max-width: 1100px; margin: 0 auto; color: black;}
    .border-box { border: 2px solid black; padding: 10px; border-radius: 5px; }
    .header-blue { color: #002B5B; font-weight: bold; font-family: sans-serif; text-align: center;}
    .title-box { background-color: #002B5B; color: white; text-align: center; font-weight: bold; padding: 8px; font-size: 20px; border: 1px solid #002B5B;}
    .red-italic { color: red; font-style: italic; font-weight: bold; font-size: 13px;}
    hr { margin: 10px 0; border-bottom: 2px solid black; }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("<div class='header-blue' style='font-size:22px; margin-top:10px;'>PROPERTY INTERACTIVE MARKETING ENTERPRISE</div>", unsafe_allow_html=True)
    st.markdown("<div class='header-blue' style='font-size:20px;'>REALTY CORP</div>", unsafe_allow_html=True)
with col2:
    st.markdown("<div style='text-align: right; color:#002B5B; font-weight:bold; font-size:26px;'>PRIME <span style='font-size:12px; font-style:italic;'>Philippines >></span></div>", unsafe_allow_html=True)
    st.markdown("<div class='title-box'>REQUEST FOR PAYMENT</div>", unsafe_allow_html=True)

st.markdown("<hr style='border: 1.5px solid black;'>", unsafe_allow_html=True)

# --- TOP INPUTS ---
col_date, space = st.columns([1, 3])
with col_date:
    date = st.date_input("DATE:")

col_payee, col_dept = st.columns([2, 1])
with col_payee:
    payee = st.text_input("PAYEE:")
with col_dept:
    department = st.text_input("DEPARTMENT:")

st.markdown("<hr style='border: 1.5px solid black;'>", unsafe_allow_html=True)

# --- DATA TABLE & AUTO-COMPUTE ---
if 'table_data' not in st.session_state:
    st.session_state.table_data = pd.DataFrame([{"ITEMS/DESCRIPTION": "", "QTY": 0.0, "UNIT": "", "UNIT PRICE": 0.0} for _ in range(7)])

edited_df = st.data_editor(
    st.session_state.table_data,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    column_config={
        "QTY": st.column_config.NumberColumn("QTY", min_value=0.0, step=1.0),
        "UNIT PRICE": st.column_config.NumberColumn("UNIT PRICE", min_value=0.0, step=0.01, format="%.2f")
    }
)

# Auto-compute Amount
edited_df['AMOUNT'] = edited_df['QTY'] * edited_df['UNIT PRICE']
st.dataframe(edited_df[['AMOUNT']], use_container_width=True, hide_index=True)

total_amount = float(edited_df['AMOUNT'].sum())
st.markdown(f"<div style='text-align: right; font-weight: bold; font-size: 16px; padding-right: 10px;'>TOTAL AMOUNT &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {total_amount:,.2f}</div>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1.5px solid black;'>", unsafe_allow_html=True)

# --- PURPOSE ---
purpose = st.text_area("Purpose:", height=80)
st.markdown("<hr style='border: 1.5px solid black;'>", unsafe_allow_html=True)

# --- PAYMENT DETAILS ---
st.markdown("**Payment Details:**")
col_chk1, col_chk2, col_chk3, col_chk4 = st.columns(4)
with col_chk2: cash = st.checkbox("Cash")
with col_chk3: check = st.checkbox("Check")
with col_chk4: online = st.checkbox("Online Payment/Bank Transfer")

col_bank, col_remarks = st.columns([2, 1])
with col_bank:
    st.markdown("<div class='red-italic'>*If not applicable kindly put N/A</div>", unsafe_allow_html=True)
    bank = st.text_input("Bank")
    account_name = st.text_input("Account Name")
    account_number = st.text_input("Account Number")

with col_remarks:
    st.markdown("Remarks:")
    urgent = st.checkbox("Urgent")
    not_urgent = st.checkbox("Not urgent")
    date_needed = st.date_input("Date Needed (M-D-Y):")

st.markdown("<hr style='border: 1.5px solid black;'>", unsafe_allow_html=True)

# --- E-SIGNATURES ---
def create_canvas(key_name):
    return st_canvas(
        stroke_width=2,
        stroke_color="black",
        background_color="#eeeeee",
        height=80,
        width=250,
        drawing_mode="freedraw",
        key=key_name,
    )

col_sig1, col_sig2, col_sig3 = st.columns(3)
with col_sig1:
    st.write("Requested By:")
    req_canvas = create_canvas("canvas_req")
    req_name = st.text_input("Signature Over Printed Name", key="req_name")
    req_remarks = st.text_input("Remarks:", key="req_remarks")

with col_sig2:
    st.write("Approved By:")
    app_canvas = create_canvas("canvas_app")
    app_name = st.text_input("Signature Over Printed Name", key="app_name")
    st.caption("Team Leader/Co-TL")
    app_remarks = st.text_input("Remarks:", key="app_remarks")

with col_sig3:
    st.write("Received By:")
    rec_canvas = create_canvas("canvas_rec")
    rec_name = st.text_input("Signature Over Printed Name", key="rec_name")
    st.caption("Finance Officer")

# --- JSON EXPORT ---
payment_methods = [method for method, checked in zip(["Cash", "Check", "Online Payment/Bank Transfer"], [cash, check, online]) if checked]
urgency_status = "Urgent" if urgent else "Not urgent" if not_urgent else ""

def has_signature(canvas_result):
    return canvas_result.image_data is not None if canvas_result else False

form_data = {
    "Document_Info": {
        "Company": "PROPERTY INTERACTIVE MARKETING ENTERPRISE",
        "Entity": "PRIME Philippines, REALTY CORP",
        "Form_Type": "REQUEST FOR PAYMENT"
    },
    "Basic_Details": {
        "Date": str(date),
        "Payee": payee,
        "Department": department
    },
    "Items": edited_df.fillna("").astype(str).to_dict(orient="records"),
    "Total_Amount": total_amount,
    "Purpose": purpose,
    "Payment_Details": {
        "Method": payment_methods,
        "Bank": bank,
        "Account_Name": account_name,
        "Account_Number": account_number
    },
    "Status": {
        "Urgency": urgency_status,
        "Date_Needed": str(date_needed)
    },
    "Signatures": {
        "Requested_By": {"Name": req_name, "Remarks": req_remarks, "Signed": has_signature(req_canvas)},
        "Approved_By": {"Name": app_name, "Role": "Team Leader/Co-TL", "Remarks": app_remarks, "Signed": has_signature(app_canvas)},
        "Received_By": {"Name": rec_name, "Role": "Finance Officer", "Signed": has_signature(rec_canvas)}
    }
}

st.download_button(
    label="Export Completed Form to JSON",
    data=json.dumps(form_data, indent=4),
    file_name="RFP_Completed.json",
    mime="application/json"
)
