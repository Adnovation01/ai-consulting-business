import os
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import time
import random
from datetime import datetime

load_dotenv()

def send_gmail_outreach(to_email, subject, body_text):
    """
    Sends a single email using Gmail SMTP.
    """
    smtp_server = "smtp.gmail.com"
    smtp_port = 465
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_PASS")
    sender_name = os.getenv("YOUR_NAME", "Pranshu Mishra")
    bcc_email = os.getenv("BCC_EMAIL")

    if not email_user or not email_pass or "your_password" in email_pass:
        return False, "Gmail credentials not configured in .env"

    try:
        msg = MIMEMultipart()
        msg['From'] = f"{sender_name} <{email_user}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        if bcc_email:
            msg['Bcc'] = bcc_email

        # HTML formatting for spacing and bullets
        html_body = body_text.replace("\n", "<br>")
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(email_user, email_pass)
            server.send_message(msg)
        return True, "SENT"
    except Exception as e:
        return False, str(e)

def process_outreach_from_excel(excel_file="Dentist_Industry_Master.xlsx"):
    """
    The main logic to sync with the Excel file.
    """
    if not os.path.exists(excel_file):
        print(f"Error: {excel_file} not found.")
        return

    try:
        # Load the Master CRM sheet
        df = pd.read_excel(excel_file, sheet_name='CRM_SYNC')
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return

    # Filter for things marked 'SEND'
    targets = df[df['Action'] == 'SEND']
    
    if targets.empty:
        print("No leads marked as 'SEND'. Update the 'Action' column in Excel to begin.")
        return

    print(f"🚀 Found {len(targets)} leads marked for sending via Gmail...")

    for index, row in targets.iterrows():
        lead_name = row['Lead Name']
        to_email = row['Email']
        subject = row['Draft Subject']
        body = row['Draft Body']
        
        print(f"📧 Sending to {lead_name}...", end="", flush=True)
        
        success, status_msg = send_gmail_outreach(to_email, subject, body)
        
        if success:
            print(" ✅")
            df.at[index, 'Action'] = "COMPLETED"
            df.at[index, 'Status'] = "SENT"
            df.at[index, 'Sent At'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            print(f" ❌ ({status_msg})")
            df.at[index, 'Status'] = f"Error: {status_msg}"

        # Delay to avoid Gmail spam filters
        time.sleep(random.uniform(2, 5))

    # Save back to Excel
    try:
        with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name='CRM_SYNC', index=False)
        print(f"\n✅ All updates saved to {excel_file}")
    except Exception as e:
        print(f"Error saving to Excel: {e} (Is the file open in Excel? Close it!)")

if __name__ == "__main__":
    process_outreach_from_excel()
