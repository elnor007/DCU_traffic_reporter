# This is an emergency emailing script, which is only sent out if any of the scripts exceed their maximum error handling retries.

import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail account credentials (sender)
GMAIL_USER = "SENDER@GMAIL.COM"                                      # CHANGE
GMAIL_PASS = 'INSERT_APP_PASSWORD_HERE'                              # CHANGE   

# Email recipients (example)
recipients = ["EXAMPLE_EMAIL@GMAIL.COM", "EXAMPLE_EMAIL@GMAIL.COM"]  # CHANGE   
subject = "Unresolved Error - DCU Traffic Reporter"
body = """
Empty
"""



def send_email():
    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, recipients, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server.quit()



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 script.py [email|upload]")
        sys.exit(1)

    error_script = sys.argv[1].lower()

    body = f"""
    Hello, 

    this email has been sent to inform you that an error could not be resolved inside the {error_script} script within
    the DCU Traffic Reporter. Check the log files contained within ~/vivacity/log_files for more information about 
    the error.
    """

    send_email()
  
