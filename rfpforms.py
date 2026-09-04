import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Request For Payment", layout="wide")

st.markdown("<h4 style='text-align: center; margin-bottom: 0px;'>PROPERTY INTERACTIVE MARKETING ENTERPRISE</h4>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align: center; margin-bottom: 0px;'>PRIME Philippines,</h5>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align: center; margin-top: 0px;'>REALTY CORP</h5>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>REQUEST FOR PAYMENT</h3>", unsafe_allow_html=True)
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    date = st.date_input("DATE:")
    payee = st.text_input("PAYEE:")
with col2:
    department = st.text_input("DEPARTMENT:")

st.markdown("**ITEMS/DESCRIPTION**")
if 'items_df' not in st.session_state:
    st.session_state.items_df = pd.DataFrame(
        columns=["ITEMS/DESCRIPTION", "QTY", "UNIT", "UNIT PRICE", "AMOUNT"]
    )

edited_df = st.data_editor(
    st.session_state.items_df,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True
)

edited_df['AMOUNT'] = pd.to_numeric(edited_df['AMOUNT'], errors='coerce')
total_amount = edited_df['AMOUNT'].sum()
st.markdown(f"**TOTAL AMOUNT:** {total_amount:,.2f}")
st.markdown("---")

purpose = st.text_area("Purpose:")

st.markdown("**Payment Details:**")
payment_method = st.radio("Payment Type", ["Cash", "Check", "Online Payment/Bank Transfer"], horizontal=True, label_visibility="collapsed")
st.caption("*If not applicable kindly put N/A")

col3, col4, col5 = st.columns(3)
with col3:
    bank = st.text_input("Bank")
with col4:
    account_name = st.text_input("Account Name")
with col5:
    account_number = st.text_input("Account Number")
st.markdown("---")

st.markdown("**Urgency:**")
urgency = st.radio("Urgency Status", ["Urgent", "Not urgent"], horizontal=True, label_visibility="collapsed")
date_needed = st.date_input("Date Needed (M-D-Y):")
st.markdown("---")

col6, col7, col8 = st.columns(3)
with col6:
    st.markdown("**Requested By:**")
    req_name = st.text_input("Signature Over Printed Name", key="req_name")
    req_remarks = st.text_input("Remarks:", key="req_remarks")

with col7:
    st.markdown("**Approved By:**")
    app_name = st.text_input("Signature Over Printed Name", key="app_name")
    st.caption("Team Leader/Co-TL")
    app_remarks = st.text_input("Remarks:", key="app_remarks")

with col8:
    st.markdown("**Received By:**")
    rec_name = st.text_input("Signature Over Printed Name", key="rec_name")
    st.caption("Finance Officer")

st.markdown("---")

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
    "Items": edited_df.fillna("").to_dict(orient="records"),
    "Total_Amount": total_amount,
    "Purpose": purpose,
    "Payment_Details": {
        "Method": payment_method,
        "Bank": bank,
        "Account_Name": account_name,
        "Account_Number": account_number
    },
    "Status": {
        "Urgency": urgency,
        "Date_Needed": str(date_needed)
    },
    "Signatures": {
        "Requested_By": {
            "Name": req_name,
            "Remarks": req_remarks
        },
        "Approved_By": {
            "Name": app_name,
            "Role": "Team Leader/Co-TL",
            "Remarks": app_remarks
        },
        "Received_By": {
            "Name": rec_name,
            "Role": "Finance Officer"
        }
    }
}

json_output = json.dumps(form_data, indent=4)

st.download_button(
    label="Export to JSON",
    data=json_output,
    file_name="RFP_Output.json",
    mime="application/json"
)
