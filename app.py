import streamlit as st
import pandas as pd
import main
import io

st.set_page_config(page_title="WhatsApp & Email Automation", page_icon="🟢")

st.title("🟢 Omni-Channel Bulk Sender")
st.markdown("""
Upload your Excel file and send WhatsApp messages and/or Emails automatically.
**Note:** Use responsibly. Do not spam.
""")

# File Uploader
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:
    # Load Data
    try:
        df = pd.read_excel(uploaded_file)
        if 'Status' not in df.columns:
            df['Status'] = 'Pending'
        if 'Email_Status' not in df.columns:
            df['Email_Status'] = 'Pending'
        
        st.subheader("Data Preview")
        st.dataframe(df)
        
        # Stats
        total = len(df)
        wa_sent = len(df[df['Status'] == 'Sent'])
        email_sent = len(df.get('Email_Status', pd.Series(['Pending']*total)) == 'Sent')
        
        col_s1, col_s2 = st.columns(2)
        col_s1.metric("WA Sent", wa_sent, delta=f"Total: {total}")
        col_s2.metric("Emails Sent", email_sent, delta=f"Total: {total}")
        
        # Column Mapping
        st.subheader("Map Columns")
        col_map1, col_map2, col_map3 = st.columns(3)
        
        # Try to auto-detect columns
        all_columns = df.columns.tolist()
        default_name_index = 0
        default_phone_index = 0
        default_email_index = 0
        
        for i, col in enumerate(all_columns):
            if "name" in col.lower(): default_name_index = i
            if "mobile" in col.lower() or "phone" in col.lower() or "contact" in col.lower(): default_phone_index = i
            if "email" in col.lower() or "mail" in col.lower(): default_email_index = i

        with col_map1:
            name_col = st.selectbox("Select Name Column", all_columns, index=default_name_index)
        with col_map2:
            phone_col = st.selectbox("Select Phone Column", all_columns, index=default_phone_index)
        with col_map3:
            email_col = st.selectbox("Select Email Column", all_columns, index=default_email_index)

        # Channel Selection
        st.subheader("Select Channels")
        chk_c1, chk_c2 = st.columns(2)
        with chk_c1:
            enable_wa = st.checkbox("Send WhatsApp", value=True)
        with chk_c2:
            enable_email = st.checkbox("Send Email", value=False)

        st.subheader("Message Configuration")
        
        tab1, tab2 = st.tabs(["💬 WhatsApp", "📧 Email"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                custom_msg = st.text_area("WA Default Message", value="Hello {Name}, Join our community!")
                st.caption("Use {Name} as placeholder.")
            with col2:
                custom_link = st.text_input("WA Community Link", value="")
                st.caption("Appended to every WA message.")

        with tab2:
            email_subject = st.text_input("Email Subject", value="Hello from Us!")
            email_body = st.text_area("Email Body", value="Hi {Name},\n\nWe would love to connect with you.")
            
            with st.expander("⚙️ Email SMTP Configuration"):
                e_server = st.text_input("SMTP Server", value="smtp.gmail.com")
                e_port = st.number_input("SMTP Port", value=465)
                e_user = st.text_input("Sender Email", placeholder="your_email@gmail.com")
                e_pass = st.text_input("App Password", type="password", help="Use App Password for Gmail, not login password.")
                
                smtp_settings = {
                    "server": e_server,
                    "port": int(e_port),
                    "sender_email": e_user,
                    "password": e_pass
                }

        # Safety Settings
        if enable_wa:
            with st.expander("🛡️ WhatsApp Safety Settings (Anti-Ban)", expanded=False):
                st.warning("Recommended: Keep delays higher to avoid ban.")
                s_col1, s_col2 = st.columns(2)
                with s_col1:
                    min_d = st.number_input("Min Delay (sec)", min_value=5, value=10)
                    batch_size = st.number_input("Batch Size (Pause after X msgs)", min_value=0, value=50, help="0 to disable")
                with s_col2:
                    max_d = st.number_input("Max Delay (sec)", min_value=10, value=20)
                    batch_pause = st.number_input("Batch Pause Duration (sec)", min_value=0, value=300, help="Time to wait after batch finishes")
        else:
            min_d, max_d, batch_size, batch_pause = 0, 0, 0, 0

        if st.button("🚀 Start Automation"):
            if enable_email and not (e_user and e_pass):
                st.error("Please provide Email Credentials.")
            else:
                status_text = st.empty()
                progress_bar = st.progress(0)
                log_area = st.empty()
                logs = []
                
                processed_count = 0
                # Approximate total operations
                total_ops = 0
                if enable_wa: total_ops += (total - wa_sent)
                if enable_email: total_ops += (total - email_sent)
                if total_ops == 0: total_ops = 1
                
                current_op = 0

                # Run Automation
                for event_type, msg, data, type_source in main.process_messages(
                    df, name_col, phone_col, email_col=email_col,
                    enable_wa=enable_wa, enable_email=enable_email,
                    custom_message=custom_msg, custom_link=custom_link,
                    email_subject=email_subject, email_body=email_body, smtp_settings=smtp_settings,
                    min_delay=min_d, max_delay=max_d,
                    batch_size=batch_size, batch_pause=batch_pause
                ):
                    if event_type == "init":
                        status_text.info(msg)
                    elif event_type == "login":
                        status_text.warning(msg)
                    elif event_type == "progress":
                        status_text.text(msg)
                    elif event_type == "update":
                        logs.append(f"[{type_source.upper()}] {msg}")
                        log_area.text("\n".join(logs[-10:])) # Show last 10 logs
                        
                        # Update DataFrame
                        idx, col_name, status_val = data
                        df.at[idx, col_name] = status_val
                        
                        current_op += 1
                        progress = min(current_op / total_ops, 1.0)
                        progress_bar.progress(progress)
                        
                    elif event_type == "error":
                        st.error(msg)
                    elif event_type == "done":
                        st.success(msg)
                        status_text.empty()
                
                # Show updated dataframe
                st.session_state['df_result'] = df
            
    except Exception as e:
        st.error(f"Error reading file: {e}")

# Download Section
if 'df_result' in st.session_state:
    st.subheader("🎉 Result")
    st.dataframe(st.session_state['df_result'])
    
    # Convert DF to Excel for download
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        st.session_state['df_result'].to_excel(writer, index=False)
    
    st.download_button(
        label="📥 Download Updated Excel",
        data=output.getvalue(),
        file_name="updated_status.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
