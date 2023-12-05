import os
import smtplib
import ssl
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


@dataclass(frozen=True, order=True)
class Attachment:
    content: bytes
    maintype: str
    subtype: str
    filename: str


def send_mail(
    subject,
    content,
    content_type="plain",
    attachment: Attachment = None,
    recipients=None,
    catch_errors=False,
):
    print(f"Sending mail with subject {subject}")

    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
    PRIVATE_EMAIL_ADDRESS = os.getenv("PRIVATE_EMAIL_ADDRESS")
    API_KEY = os.getenv("EMAIL_API_KEY")

    to = recipients or PRIVATE_EMAIL_ADDRESS
    me = f"Emil Djupvik <{EMAIL_ADDRESS}>"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = me
    msg["To"] = to
    msg["X-Priority"] = "1"

    msg.attach(MIMEText(content, content_type))

    context = ssl.create_default_context()

    if attachment is not None:
        msg.add_attachment(
            attachment.content,
            maintype=attachment.maintype,
            subtype=attachment.subtype,
            filename=attachment.filename,
        )

    try:
        with smtplib.SMTP_SSL("smtp.sendgrid.net", 465, context=context) as smtp:
            smtp.login("apikey", API_KEY)

            smtp.sendmail(me, to, msg.as_string())
            print(f"Sent mail with subject {subject} to {to}")
    except smtplib.SMTPException as e:
        if catch_errors:
            print(f"Could not send mail: {e}")
        else:
            raise e
