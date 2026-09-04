import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Request for Payment Form", layout="wide")

with st.container(border=True):
    # --- Header ---
    c_head1, c_head2 = st.columns([3, 1])
    with c_head1:
        st.markdown("<h2 style='text-align: center; margin-bottom: 0;'>PROPERTY INTERACTIVE MARKETING ENTERPRISE</h2>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; margin-top: 0;'>REALTY CORP</h2>", unsafe_allow_html=True)
    with c_head2:
        st.markdown("<div style='background-color: navy; color: white; text-align: center; padding: 10px; font-weight: bold; border-radius: 5px;'>REQUEST FOR PAYMENT</div>", unsafe_allow_html=True)

    # --- Top Fields ---
    c_date, c_payee, c_dept = st.columns([1, 2, 2])
    date = c_date.text_input("Date", label_visibility="collapsed", placeholder="DATE:")
    payee = c_payee.text_input("Payee", label_visibility="collapsed", placeholder="PAYEE:")
    department = c_dept.text_input("Department", label_visibility="collapsed", placeholder="DEPARTMENT:")

    # --- Items Table ---
    st.markdown("---")
    data = pd.DataFrame(
        [{"ITEMS/DESCRIPTION": "", "QTY": 0, "UNIT": "", "UNIT PRICE": 0.0, "AMOUNT": 0.0}]
    )
    edited_df = st.data_editor(
        data,
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        column_config={
            "ITEMS/DESCRIPTION": st.column_config.TextColumn("ITEMS/DESCRIPTION", width="large"),
            "QTY": st.column_config.NumberColumn("QTY", min_value=0, step=1),
            "UNIT": st.column_config.TextColumn("UNIT"),
            "UNIT PRICE": st.column_config.NumberColumn("UNIT PRICE", min_value=0.0, format="%.2f"),
            "AMOUNT": st.column_config.NumberColumn("AMOUNT", min_value=0.0, format="%.2f"),
        }
    )

    total_amount = edited_df["AMOUNT"].fillna(0).sum()
    c_total_label, c_total_val = st.columns([5, 1])
    with c_total_val:
        st.markdown(f"**TOTAL AMOUNT:** {total_amount:.2f}")

    # --- Purpose ---
    st.markdown("---")
    purpose = st.text_area("Purpose", label_visibility="collapsed", placeholder="Purpose:", height=80)

    # --- Payment Details ---
    st.markdown("---")
    c_pay_left, c_pay_right = st.columns(2)

    with c_pay_left:
        c_cash, c_check, c_online = st.columns(3)
        cash = c_cash.checkbox("Cash")
        check = c_check.checkbox("Check")
        online = c_online.checkbox("Online Payment/Bank Transfer")

        st.markdown("<span style='color: red;'>*if not applicable kindly put N/A</span>", unsafe_allow_html=True)

        bank = st.text_input("Bank", placeholder="Bank")
        account_name = st.text_input("Account Name", placeholder="Account Name")
        account_number = st.text_input("Account Number", placeholder="Account Number")

    with c_pay_right:
        st.markdown("**Remarks:**")
        c_urgent, c_not_urgent = st.columns(2)
        urgent = c_urgent.checkbox("Urgent")
        not_urgent = c_not_urgent.checkbox("Not urgent")
        date_needed = st.text_input("Date Needed (M-D-Y):", placeholder="Date Needed (M-D-Y):")

    # --- Signatures ---
    st.markdown("---")
    c_sig1, c_sig2, c_sig3 = st.columns(3)

    with c_sig1:
        st.markdown("**Requested By:**")
        req_name = st.text_input("Req Name", label_visibility="collapsed", placeholder="Signature Over Printed Name")
        req_remarks = st.text_area("Req Remarks", label_visibility="collapsed", placeholder="Remarks:", height=68)

    with c_sig2:
        st.markdown("**Approved By:**")
        app_name = st.text_input("App Name", label_visibility="collapsed", placeholder="Signature Over Printed Name")
        st.caption("*Team Leader/ Co-TL*")

    with c_sig3:
        st.markdown("**Received By:**")
        rec_name = st.text_input("Rec Name", label_visibility="collapsed", placeholder="Signature Over Printed Name")
        st.caption("*Finance Officer*")

    # --- Submit Button ---
    st.markdown("---")
    if st.button("Submit Request", type="primary", use_container_width=True):
        form_data = {
            "header": {
                "date": date,
                "payee": payee,
                "department": department
            },
            "items": edited_df.to_dict(orient="records"),
            "total_amount": total_amount,
            "purpose": purpose,
            "payment_details": {
                "cash": cash,
                "check": check,
                "online": online,
                "bank": bank,
                "account_name": account_name,
                "account_number": account_number
            },
            "remarks": {
                "urgent": urgent,
                "not_urgent": not_urgent,
                "date_needed": date_needed
            },
            "signatures": {
                "requested_by": {
                    "signature": req_name,
                    "remarks": req_remarks
                },
                "approved_by": {
                    "signature": app_name
                },
                "received_by": {
                    "signature": rec_name
                }
            }
        }

        st.json(form_data)
        st.download_button(
            label="Download JSON",
            data=json.dumps(form_data, indent=4),
            file_name="request_for_payment.json",
            mime="application/json"
        )
