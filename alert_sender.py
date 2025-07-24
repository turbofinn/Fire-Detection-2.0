# In alert_sender.py
import os
import sqlite3
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# --- Store your keys securely as environment variables ---
# For Twilio
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

# For SendGrid
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
SENDER_EMAIL = "your_verified_sender@example.com" # Must be a verified sender in SendGrid

def send_sms_alert(phone_number, location):
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        print("Twilio credentials not set.")
        return
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message_body = f"FIRE ALERT: A fire has been detected at {location}. Please take immediate action."
        client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        print(f"SMS alert sent to {phone_number}")
    except Exception as e:
        print(f"Failed to send SMS: {e}")

def send_email_alert(email_address, location):
    if not all([SENDGRID_API_KEY, SENDER_EMAIL]):
        print("SendGrid credentials not set.")
        return
    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=email_address,
        subject=f"🔥 CRITICAL FIRE ALERT: {location}",
        html_content=f"<h1>Fire Alert</h1><p>A fire has been detected at <strong>{location}</strong> at {QDateTime.currentDateTime().toString()}.</p><p>Please initiate safety protocols immediately.</p>"
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        print(f"Email alert sent to {email_address}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def trigger_all_alerts(location):
    """Fetches all users and sends them SMS and email alerts."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Fetch all users from the database
    cursor.execute("SELECT phone_number, email FROM users")
    users = cursor.fetchall()
    conn.close()
    
    print(f"Found {len(users)} users to alert.")
    for phone, email in users:
        if phone:
            send_sms_alert(phone, location)
        if email:
            send_email_alert(email, location)