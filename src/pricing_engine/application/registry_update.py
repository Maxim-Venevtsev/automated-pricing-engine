import logging
import pandas as pd
from datetime import datetime

from configs.settings import STAGING_DIR, STATE_DIR
from configs.constants import NEW_DAYS, RESTART_THRESHOLD_DAYS

logger = logging.getLogger(__name__)

INPUT_FILE = STAGING_DIR / "corrected_price_5.xlsx"
REGISTRY_FILE = STATE_DIR / "items_presence_registry.csv"


def main():

    logger.info("START → registry_update")

    today = pd.Timestamp(datetime.today().date())

    df_current = pd.read_excel(INPUT_FILE)
    df_current["article"] = df_current["article"].astype(str)

    current_articles = set(df_current["article"].unique())

    if REGISTRY_FILE.exists():
        registry = pd.read_csv(REGISTRY_FILE)
        registry["article"] = registry["article"].astype(str)
        registry["first_seen"] = pd.to_datetime(registry["first_seen"])
        registry["last_seen"] = pd.to_datetime(registry["last_seen"])
    else:
        registry = pd.DataFrame(
            columns=["article", "first_seen", "last_seen", "is_active"]
        )

    registry_articles = set(registry["article"].unique())

    updated_rows = []

    for article in current_articles:

        if article not in registry_articles:

            updated_rows.append({
                "article": article,
                "first_seen": today,
                "last_seen": today,
                "is_active": 1
            })

        else:
            row = registry.loc[registry["article"] == article].iloc[0]

            if row["is_active"] == 1:

                updated_rows.append({
                    "article": article,
                    "first_seen": row["first_seen"],
                    "last_seen": today,
                    "is_active": 1
                })

            else:
                days_absent = (today - row["last_seen"]).days

                if days_absent >= RESTART_THRESHOLD_DAYS:
                    updated_rows.append({
                        "article": article,
                        "first_seen": today,
                        "last_seen": today,
                        "is_active": 1
                    })
                else:
                    updated_rows.append({
                        "article": article,
                        "first_seen": row["first_seen"],
                        "last_seen": today,
                        "is_active": 1
                    })

    # deactivate missing
    missing_articles = registry_articles - current_articles

    for article in missing_articles:
        row = registry.loc[registry["article"] == article].iloc[0]
        updated_rows.append({
            "article": article,
            "first_seen": row["first_seen"],
            "last_seen": row["last_seen"],
            "is_active": 0
        })

    registry_updated = pd.DataFrame(updated_rows)

    registry_updated.to_csv(REGISTRY_FILE, index=False)

    logger.info("Registry updated successfully")
    logger.info("DONE → registry_update")


if __name__ == "__main__":
    main()