import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from configs.settings import (
    STAGING_DIR,
    BASE_PRICE_FILE,
    VALIDATION_DIR,
)
from pricing_engine.infrastructure.mailer import send_mail

logger = logging.getLogger(__name__)

INPUT_FILE = STAGING_DIR / "corrected_price_5.xlsx"

OUTPUT_FILE = (
    VALIDATION_DIR /
    f"missing_base_price_{datetime.today().strftime('%Y_%m_%d')}.xlsx"
)

# Кому отправлять уведомление
NOTIFY_EMAIL = "m.venevtsev@liga-m.pro"


# ---------------------------------------------------------
# Main logic
# ---------------------------------------------------------

def main():

    logger.info("START → validation_missing_base_price")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    if not BASE_PRICE_FILE.exists():
        raise FileNotFoundError(f"Base price file not found: {BASE_PRICE_FILE}")

    try:
        df = pd.read_excel(INPUT_FILE)
        base_df = pd.read_excel(BASE_PRICE_FILE)
    except Exception as e:
        logger.error(f"Error loading files: {e}")
        raise

    required_cols_input = {"price_group", "article"}
    required_cols_base = {"article"}

    if not required_cols_input.issubset(df.columns):
        raise ValueError("corrected_price_5.xlsx missing required columns")

    if not required_cols_base.issubset(base_df.columns):
        raise ValueError("base_price.xlsx missing required columns")

    df["article"] = df["article"].astype(str).str.strip()
    base_df["article"] = base_df["article"].astype(str).str.strip()

    missing = df[~df["article"].isin(base_df["article"])][
        ["price_group", "article"]
    ].drop_duplicates()

    if missing.empty:
        logger.info("No missing base_price positions found.")
        logger.info("DONE → validation_missing_base_price")
        return

    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    try:
        missing.to_excel(OUTPUT_FILE, index=False)
    except Exception as e:
        logger.error(f"Failed to save missing_base_price file: {e}")
        raise

    logger.info(f"Missing positions found: {len(missing)}")
    logger.info(f"File saved: {OUTPUT_FILE.name}")

    # ---------------------------------------------------------
    # Send notification
    # ---------------------------------------------------------

    try:
        send_mail(
            to=NOTIFY_EMAIL,
            subject="Отсутствуют позиции в base_price.xlsx",
            body=(
                "Обнаружены позиции, отсутствующие в base_price.xlsx.\n\n"
                "См. вложенный файл."
            ),
            attachments=[OUTPUT_FILE]
        )

        logger.info("Notification email sent.")

    except Exception as e:
        logger.error(f"Error sending notification email: {e}")
        # не падаем — pricing pipeline должен продолжить работу

    logger.info("DONE → validation_missing_base_price")


if __name__ == "__main__":
    main()