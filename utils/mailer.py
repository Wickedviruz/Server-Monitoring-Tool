import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.logger import log_message
from utils.config import config

# Hämta e-postkonfiguration från din config-fil
SENDER_EMAIL = config.get('email', 'SENDER_EMAIL')
RECEIVER_EMAILS = [email.strip() for email in config.get('email', 'RECEIVER_EMAILS').split(',')]
SMTP_SERVER = config.get('email', 'SMTP_SERVER')
SMTP_PORT = config.getint('email', 'SMTP_PORT')
SMTP_USER = config.get('email', 'SMTP_USER')
SMTP_PASSWORD = config.get('email', 'SMTP_PASSWORD')

# Funktion för att skapa e-postmeddelandet
def create_email_message(subject, body):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = ', '.join(RECEIVER_EMAILS)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    return msg

# Funktion för att skicka e-post
def send_email(subject, body):
    msg = create_email_message(subject, body)
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAILS, text)
        server.quit()
        log_message("info", f"Email sent successfully: {subject}")
    except Exception as e:
        log_message("error", f"Failed to send email: {e}")

# En funktion för att skicka varningar
def send_alert(resource_name, message):
    subject = f"Warning: High {resource_name} usage"
    body = f"Alert: {message}"
    send_email(subject, body)
    log_message("warning", f"{resource_name} alert: {message}")
