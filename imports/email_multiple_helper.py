from datetime import datetime, timezone
import time
import os
import sys
import smtplib
import ssl
from email.message import EmailMessage
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import getpass

username = getpass.getuser()
max_retries = 10  #reiterations
retry_delay = 1  #seconds
WATCHED_FOLDER = f'/home/{username}/vivacity/ruby/reports'
EMAIL_SENDER = "SEND_EMAIL@GMAIL.COM"                                   # This email sends the report
recipients = ["RECEIVE_EMAIL@GMAIL.COM", "RECEIVE_EMAIL@GMAIL.COM"]     # These emails receive the report
EMAIL_PASSWORD = 'ENTER_APP_PASSWORD_HERE'                              # This is the app password for the SENDER email (different from regular account password)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

email_sent = False


# Email sending function
def send_email_with_attachment(file_path):
            msg = EmailMessage()
            msg["Subject"] = "New Report Generated"
            msg["From"] = EMAIL_SENDER
            msg["To"] = ", ".join(recipients)
            msg.set_content(f"A new report has been generated. See attached: {os.path.basename(file_path)}")

            with open(file_path, "rb") as f:
                msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=os.path.basename(file_path))

            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)
            print(f"{datetime.now(timezone.utc)} : Email sent with attachment : {file_path}\n\n\n\n\n")



# Watchdog event handler (checks for new reports)
class PDFHandler(FileSystemEventHandler):
    def on_created(self, event):
        global email_sent
        if email_sent:
            return

        if event.src_path.endswith(".pdf"):
            print(f"{datetime.now(timezone.utc)} : Detected PDF: {event.src_path}\n")
            time.sleep(3)  # Wait to ensure file is fully written

            send_email_with_attachment(event.src_path)
            email_sent = True
            sys.exit(0) # Exits to the finally block for cleanup
