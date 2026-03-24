import ssl
import smtplib
import logging
from email.message import EmailMessage
from pathlib import Path

from configs.settings import (
    SMTP_SERVER,
    SMTP_PORT,
    SMTP_EMAIL,
    SMTP_PASSWORD,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Public mail function
# ---------------------------------------------------------

def send_mail(
    to,
    subject,
    body,
    attachments=None
):
    """
    Send email with optional attachments.
    """

    if not SMTP_SERVER or not SMTP_EMAIL or not SMTP_PASSWORD:
        raise ValueError("SMTP configuration is incomplete. Check .env file.")

    if isinstance(to, str):
        to = [to]

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = ", ".join(to)

    msg.set_content(body)

    # Attach files
    if attachments:
        for file_path in attachments:
            path = Path(file_path)

            if not path.exists():
                logger.warning(f"Attachment not found: {path}")
                continue

            with open(path, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="application",
                    subtype="octet-stream",
                    filename=path.name
                )

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email successfully sent to: {to}")

    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        raise