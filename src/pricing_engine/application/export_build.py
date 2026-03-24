import logging
import pandas as pd
from datetime import datetime

from configs.settings import (
    STAGING_DIR,
    STATE_DIR,
    REFERENCE_DIR,
)

logger = logging.getLogger(__name__)

INPUT_FILE = STAGING_DIR / "corrected_price_5.xlsx"
OUTPUT_FILE = STAGING_DIR / "corrected_price_6.xlsx"

REGISTRY_FILE = STATE_DIR / "items_presence_registry.csv"
ALLOWED_GROUPS_FILE = REFERENCE_DIR / "allowed_price_groups.xlsx"

NEW_DAYS = 14


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

def load_input():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"{INPUT_FILE} not found")

    df = pd.read_excel(INPUT_FILE)

    required = {
        "price_group",
        "article",
        "name",
        "stock",
        "unit",
        "price",
    }

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df["article"] = df["article"].astype(str)
    return df.copy()


# ---------------------------------------------------------
# Allowed price groups
# ---------------------------------------------------------

def load_allowed_groups() -> set[str]:
    """
    Reads allowed_price_groups.xlsx and returns a set of allowed group names.
    Be tolerant to column naming:
      - 'price_group' (preferred)
      - 'group'
      - 'allowed_group'
      - or first column if unknown
    """
    if not ALLOWED_GROUPS_FILE.exists():
        raise FileNotFoundError(f"{ALLOWED_GROUPS_FILE} not found")

    df = pd.read_excel(ALLOWED_GROUPS_FILE)

    if df.empty:
        logger.warning("allowed_price_groups.xlsx is empty → no filtering applied")
        return set()

    preferred_cols = ["price_group", "group", "allowed_group", "allowed_price_group"]
    col = None
    for c in preferred_cols:
        if c in df.columns:
            col = c
            break

    if col is None:
        # fallback to first column
        col = df.columns[0]
        logger.warning(
            f"allowed_price_groups.xlsx: unknown column names; using first column '{col}'"
        )

    allowed = (
        df[col]
        .dropna()
        .astype(str)
        .str.strip()
    )

    allowed_set = set([x for x in allowed.tolist() if x])

    if not allowed_set:
        logger.warning("allowed_price_groups.xlsx produced empty allowed set → no filtering applied")

    return allowed_set


# ---------------------------------------------------------
# Load registry
# ---------------------------------------------------------

def load_registry():

    if not REGISTRY_FILE.exists():
        logger.warning("Registry file not found → NEW flag disabled")
        return None

    registry = pd.read_csv(REGISTRY_FILE)

    registry["article"] = registry["article"].astype(str)
    registry["first_seen"] = pd.to_datetime(registry["first_seen"], errors="coerce")

    return registry


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    logger.info("START → export_build")

    df = load_input()

    rows_before = len(df)
    logger.info(f"Rows before filter: {rows_before}")

    # ---------------------------------------------------------
    # Filter: allowed price groups (business whitelist)
    # ---------------------------------------------------------
    allowed_groups = load_allowed_groups()
    if allowed_groups:
        before = len(df)
        df = df[df["price_group"].astype(str).str.strip().isin(allowed_groups)]
        after = len(df)
        logger.info(f"Allowed groups filter applied: {before} → {after}")
    else:
        logger.info("Allowed groups filter skipped (empty allowed set)")

    # ---------------------------------------------------------
    # Remove zero/negative stock
    # ---------------------------------------------------------
    df["stock"] = pd.to_numeric(df["stock"], errors="coerce").fillna(0)
    df = df[df["stock"] > 0]

    rows_after = len(df)
    logger.info(f"Rows after stock filter: {rows_after}")

    # ---------------------------------------------------------
    # Merge registry + NEW flag
    # ---------------------------------------------------------
    registry = load_registry()

    if registry is not None:
        df = df.merge(
            registry[["article", "first_seen"]],
            on="article",
            how="left"
        )

        today = pd.Timestamp.today().normalize()

        # If first_seen missing → treat as not new (will be set by registry_update on next runs)
        df["days_since_first_seen"] = (today - df["first_seen"]).dt.days

        df["flag"] = ""
        df.loc[df["days_since_first_seen"].notna() & (df["days_since_first_seen"] <= NEW_DAYS), "flag"] = "New!"

        new_items = int((df["flag"] == "New!").sum())
        logger.info(f"New items flagged (visual): {new_items}")
    else:
        df["flag"] = ""

    # ---------------------------------------------------------
    # Select final columns
    # ---------------------------------------------------------
    columns = [
        "price_group",
        "article",
        "name",
        "stock",
        "unit",
        "price",
        "flag",
    ]

    # liquidity_category сохраняем если есть (для спецпредложения)
    if "liquidity_category" in df.columns:
        columns.append("liquidity_category")

    df = df[columns]

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        df.to_excel(OUTPUT_FILE, index=False)
        logger.info(f"Saved technical file: {OUTPUT_FILE.name}")
    except Exception as e:
        logger.error(f"Failed to save export file: {e}")
        raise

    logger.info("DONE → export_build")


if __name__ == "__main__":
    main()