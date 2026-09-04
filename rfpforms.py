import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Request For Payment", layout="wide")

# Custom CSS to mimic the PDF borders and exact layout
st.markdown("""
    <style>
    .stApp { max-width: 1000px; margin: 0 auto; }
    .header-text { color: #002B5B; font-weight: bold; text-align: center; }
    .title-box { background-color: #002B5B; color: white; padding: 5px; text-align: center; font-weight: bold; font-size: 20px;}
    .bordered-container { border: 2px solid black; padding: 15px; margin-bottom: 10px; }
    .red-text { color: red; font-style: italic; font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

with st.container():
    # Header Section
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("<div class='header-text' style='font-size:22px;'>PROPERTY INTERACTIVE MARKETING ENTERPRISE</div>", unsafe_allow_html=True)
        st.markdown("<div class='header-text' style='font-size:20px;'>REALTY CORP</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='text-align: right; color:#002B5B; font-weight:bold; font-size:24px; margin-bottom:5px;'>PRIME <span style='font-size:12px'>Philippines</span>>></div>", unsafe_allow_html=True)
        st.markdown("<div class='title-box'>REQUEST FOR PAYMENT</div>", unsafe_allow_html=True)
    
    st.markdown("---")

    # Top Inputs
    col_date, col_empty = st.columns([1, 3])
    with col_date:
        date = st.date_input("DATE:")
    
    col_payee, col_dept = st.columns([2, 1])
    with col_payee:
        payee = st.text_input("PAYEE:")
    with col_dept:
        department = st.text_input("DEPARTMENT:")

    st.markdown("---")

    # Data Table
    if 'items_df' not in st.session_state:
        st.session_state.items_df = pd.DataFrame(
            [["", 0, "", 0.0, 0.0] for _ in range(5)],
            columns=["ITEMS/DESCRIPTION", "QTY", "UNIT", "UNIT PRICE", "AMOUNT"]
        )

    edited_df = st.data_editor(
        st.session_state.items_df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True
    )

    # Force numeric conversion to avoid serialization errors
    edited_df['AMOUNT'] = pd.to_numeric(edited_df['AMOUNT'], errors='coerce').fillna(0)
    total_amount = float(edited_df['AMOUNT'].sum())  # Cast to native float
    
    st.markdown(f"<div style='text-align: right; font-weight: bold; border-top: 1px solid black; padding-top: 5px;'>TOTAL AMOUNT &nbsp;&nbsp;&nbsp;&nbsp; {total_amount:,.2f}</div>", unsafe_allow_html=True)
    
    st.markdown("---")

    # Purpose
    purpose = st.text_area("Purpose:", height=100)

    # Payment Details
    st.markdown("Payment Details:")
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        cash = st.checkbox("Cash")
    with col_c2:
        check = st.checkbox("Check")
    with col_c3:
        online = st.checkbox("Online Payment/Bank Transfer")

    col_bank1, col_bank2 = st.columns([2, 1])
    with col_bank1:
        st.markdown("<div class='red-text'>*If not applicable kindly put N/A</div>", unsafe_allow_html=True)
        bank = st.text_input("Bank")
        account_name = st.text_input("Account Name")
        account_number = st.text_input("Account Number")
    
    with col_bank2:
        st.markdown("Remarks:")
        urgent = st.checkbox("Urgent")
        not_urgent = st.checkbox("Not urgent")
        date_needed = st.date_input("Date Needed (M-D-Y):")

    st.markdown("---")

    # Signatures
    col_sig1, col_sig2, col_sig3 = st.columns(3)
    with col_sig1:
        st.write("Requested By:")
        req_name = st.text_input("Signature Over Printed Name", key="req")
        req_remarks = st.text_input("Remarks:")
    with col_sig2:
        st.write("Approved By:")
        app_name = st.text_input("Signature Over Printed Name", key="app")
        st.caption("Team Leader/Co-TL")
    with col_sig3:
        st.write("Received By:")
        rec_name = st.text_input("Signature Over Printed Name", key="rec")
        st.caption("Finance Officer")

# Serialize Output Safely
payment_methods = []
if cash: payment_methods.append("Cash")
if check: payment_methods.append("Check")
if online: payment_methods.append("Online Payment/Bank Transfer")

urgency_status = "Urgent" if urgent else "Not urgent" if not_urgent else ""

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
        "Requested_By": {"Name": req_name, "Remarks": req_remarks},
        "Approved_By": {"Name": app_name, "Role": "Team Leader/Co-TL"},
        "Received_By": {"Name": rec_name, "Role": "Finance Officer"}
    }
}

json_output = json.dumps(form_data, indent=4)

st.download_button(
    label="Export to JSON",
    data=json_output,
    file_name="RFP_Output.json",
    mime="application/json"
)
