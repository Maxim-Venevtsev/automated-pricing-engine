import imaplib
import email
import logging
from email.header import decode_header
from pathlib import Path

from configs.settings import (
    IMAP_SERVER,
    IMAP_PORT,
    IMAP_EMAIL,
    IMAP_PASSWORD,
    INCOMING_DIR,
)

logger = logging.getLogger(__name__)

# По-хорошему позже вынесем в settings
SENDER_FILTER = "zakaz@liga-m.pro"
FILENAME_KEYWORD = "Лига-М"


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def decode_filename(value):
    if not value:
        return None

    parts = decode_header(value)
    filename = ""

    for part, enc in parts:
        if isinstance(part, bytes):
            filename += part.decode(enc or "utf-8", errors="ignore")
        else:
            filename += part

    return filename


# ---------------------------------------------------------
# Core logic
# ---------------------------------------------------------

def download_attachment():
    """
    Connect to IMAP and download the latest matching attachment.
    """

    if not IMAP_SERVER or not IMAP_EMAIL or not IMAP_PASSWORD:
        raise ValueError("IMAP configuration is incomplete. Check .env file.")

    logger.info("Connecting to IMAP server...")

    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)

    try:
        mail.login(IMAP_EMAIL, IMAP_PASSWORD)
        mail.select("INBOX")

        logger.info(f"Searching emails from {SENDER_FILTER}...")
        result, data = mail.search(None, f'FROM "{SENDER_FILTER}"')

        if result != "OK" or not data or not data[0]:
            logger.info("No matching emails found.")
            return None

        latest_id = data[0].split()[-1]
        result, msg_data = mail.fetch(latest_id, "(RFC822)")

        if result != "OK":
            logger.warning("Failed to fetch email.")
            return None

        msg = email.message_from_bytes(msg_data[0][1])
        logger.info("Email found. Checking attachments...")

        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue

            if part.get("Content-Disposition") is None:
                continue

            filename = decode_filename(part.get_filename())

            if not filename or FILENAME_KEYWORD not in filename:
                continue

            INCOMING_DIR.mkdir(parents=True, exist_ok=True)
            filepath = INCOMING_DIR / filename

            with open(filepath, "wb") as f:
                f.write(part.get_payload(decode=True))

            logger.info(f"Attachment saved to: {filepath}")
            return filepath

        logger.info("No suitable attachment found.")
        return None

    except Exception as e:
        logger.error(f"Error during email ingestion: {e}")
        raise

    finally:
        try:
            mail.logout()
        except Exception:
            pass


# ---------------------------------------------------------
# CLI entry
# ---------------------------------------------------------

def main():
    download_attachment()


if __name__ == "__main__":
    main()