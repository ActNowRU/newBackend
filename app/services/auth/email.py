from settings import SMTP_HOST, SMTP_PORT, SMTP_SENDER, SMTP_PASSWORD

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(subject, text, receiver) -> None:
    msg = MIMEMultipart()
    msg["From"] = SMTP_SENDER
    msg["To"] = receiver
    msg["Subject"] = subject

    msg.attach(MIMEText(text, "html"))
    server = smtplib.SMTP_SSL(host=SMTP_HOST, port=SMTP_PORT)
    server.login(SMTP_SENDER, SMTP_PASSWORD)
    server.sendmail(SMTP_SENDER, receiver, msg.as_string())
    server.close()
