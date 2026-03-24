import argparse
import csv
import logging
from datetime import datetime
from pathlib import Path

from configs.settings import (
    OUTPUT_DIR,
    REFERENCE_DIR,
    STATE_DIR,
)
from pricing_engine.infrastructure.mailer import send_mail

logger = logging.getLogger(__name__)

EMAIL_LIST = REFERENCE_DIR / "dealers.csv"
TEMPLATE_FILE = REFERENCE_DIR / "email_templates" / "dealer.txt"
SENT_HISTORY = STATE_DIR / "sent_history.csv"


# ---------------------------------------------------------
# Get latest price file
# ---------------------------------------------------------

def get_latest_price_file() -> Path:
    files = list(OUTPUT_DIR.glob("Лига-М_запчасти_*.xlsx"))

    if not files:
        raise FileNotFoundError(
            f"No price files found in output folder: {OUTPUT_DIR}"
        )

    return max(files, key=lambda f: f.stat().st_mtime)


# ---------------------------------------------------------
# Load recipients
# ---------------------------------------------------------

def load_recipients() -> list[str]:

    if not EMAIL_LIST.exists():
        raise FileNotFoundError(
            f"Dealers email list not found: {EMAIL_LIST}"
        )

    recipients = []

    with open(EMAIL_LIST, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            email = (row.get("email") or "").strip()
            if email:
                recipients.append(email)

    return recipients


# ---------------------------------------------------------
# Load template
# ---------------------------------------------------------

def load_template() -> str:

    if not TEMPLATE_FILE.exists():
        raise FileNotFoundError(
            f"Email template not found: {TEMPLATE_FILE}"
        )

    return TEMPLATE_FILE.read_text(encoding="utf-8")


# ---------------------------------------------------------
# Sent history
# ---------------------------------------------------------

def already_sent_today(file_name: str) -> bool:

    if not SENT_HISTORY.exists():
        return False

    today = datetime.today().date()

    with open(SENT_HISTORY, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if (
                row["file_name"] == file_name and
                datetime.fromisoformat(row["sent_at"]).date() == today
            ):
                return True

    return False


def save_sent_record(file_name: str):

    STATE_DIR.mkdir(parents=True, exist_ok=True)

    file_exists = SENT_HISTORY.exists()

    with open(SENT_HISTORY, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["file_name", "sent_at"]
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "file_name": file_name,
            "sent_at": datetime.now().isoformat()
        })


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logger.info("START → email_delivery")

    try:
        recipients = load_recipients()
        logger.info(f"Recipients found: {len(recipients)}")

        if not recipients:
            logger.warning("No recipients found.")
            return

        price_file = get_latest_price_file()
        logger.info(f"Using file: {price_file.name}")

        if already_sent_today(price_file.name):
            logger.warning("File already sent today. Aborting.")
            return

        body = load_template()

    except Exception as e:
        logger.error(f"Initialization error: {e}")
        raise

    subject = "Оригинальные запчасти из Южной Кореи — прайс-лист Лига-М"

    success = 0
    failed = 0

    for email in recipients:
        try:
            if args.dry_run:
                logger.info(f"[DRY RUN] Would send to: {email}")
            else:
                send_mail(
                    to=email,
                    subject=subject,
                    body=body,
                    attachments=[price_file]
                )
                success += 1
                logger.info(f"Sent to: {email}")

        except Exception as e:
            failed += 1
            logger.error(f"ERROR sending to {email}: {e}")

    if not args.dry_run:
        save_sent_record(price_file.name)

    logger.info(f"Send finished. Success: {success}, Failed: {failed}")
    logger.info("DONE → email_delivery")


if __name__ == "__main__":
    main()