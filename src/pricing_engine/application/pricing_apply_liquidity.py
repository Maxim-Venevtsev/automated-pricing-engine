import logging
import pandas as pd

from configs.settings import (
    STAGING_DIR,
    LIQUIDITY_CATEGORY_FILE,
    LIQUIDITY_COEF_FILE,
)

logger = logging.getLogger(__name__)

INPUT_FILE = STAGING_DIR / "corrected_price_4.xlsx"
OUTPUT_FILE = STAGING_DIR / "corrected_price_45.xlsx"


# ---------------------------------------------------------
# Load corrected price
# ---------------------------------------------------------

def load_corrected_price() -> pd.DataFrame:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"{INPUT_FILE} not found")

    df = pd.read_excel(INPUT_FILE)

    required = {"article", "price", "price_group"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in input file: {missing}")

    df["article"] = df["article"].astype(str).str.strip()
    return df.copy()


# ---------------------------------------------------------
# Load liquidity category (from reference export)
# ---------------------------------------------------------

def load_liquidity_category() -> pd.DataFrame:
    """
    Expected columns:
      - article
      - liquidity_category (preferred) or category
    """
    if not LIQUIDITY_CATEGORY_FILE.exists():
        logger.warning("liquidity_category.xlsx not found → using empty mapping")
        return pd.DataFrame(columns=["article", "liquidity_category"])

    df = pd.read_excel(LIQUIDITY_CATEGORY_FILE)

    if "article" not in df.columns:
        logger.warning("liquidity_category.xlsx missing 'article' → using empty mapping")
        return pd.DataFrame(columns=["article", "liquidity_category"])

    if "liquidity_category" not in df.columns and "category" in df.columns:
        df = df.rename(columns={"category": "liquidity_category"})

    if "liquidity_category" not in df.columns:
        logger.warning("liquidity_category.xlsx missing category column → using empty mapping")
        return pd.DataFrame(columns=["article", "liquidity_category"])

    out = df[["article", "liquidity_category"]].copy()
    out["article"] = out["article"].astype(str).str.strip()
    out["liquidity_category"] = out["liquidity_category"].astype(str).str.strip().str.lower()

    return out


# ---------------------------------------------------------
# Load liquidity coefficients
# ---------------------------------------------------------

def load_liquidity_coef_map() -> dict:
    """
    Expected columns:
      - liquidity_category (preferred) or category
      - coef
    Returns: { "high": 1.0, "low": 0.97, ... }
    """
    if not LIQUIDITY_COEF_FILE.exists():
        logger.warning("liquidity_coef.xlsx not found → all coef = 1.0")
        return {}

    logger.info(f"Using liquidity coef file: {LIQUIDITY_COEF_FILE.name}")

    df = pd.read_excel(LIQUIDITY_COEF_FILE)

    if "liquidity_category" in df.columns:
        category_col = "liquidity_category"
    elif "category" in df.columns:
        category_col = "category"
    else:
        logger.warning("liquidity_coef.xlsx missing category column → all coef = 1.0")
        return {}

    if "coef" not in df.columns:
        logger.warning("liquidity_coef.xlsx missing 'coef' column → all coef = 1.0")
        return {}

    tmp = df[[category_col, "coef"]].dropna().copy()
    tmp[category_col] = tmp[category_col].astype(str).str.strip().str.lower()
    tmp["coef"] = pd.to_numeric(tmp["coef"], errors="coerce")

    tmp = tmp.dropna(subset=["coef"])

    return tmp.set_index(category_col)["coef"].to_dict()


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    logger.info("START → pricing_apply_liquidity")

    df = load_corrected_price()
    liquidity_df = load_liquidity_category()
    coef_map = load_liquidity_coef_map()

    df = df.merge(liquidity_df, on="article", how="left")

    # Normalize category
    df["liquidity_category"] = (
        df["liquidity_category"]
        .fillna("unknown")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # Apply coefficients
    df["liquidity_coef"] = (
        df["liquidity_category"]
        .map(coef_map)
        .fillna(1.0)
        .astype(float)
    )

# ---------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------

    logger.info("Liquidity categories detected:")
    logger.info(df["liquidity_category"].value_counts().to_string())

    logger.info("Liquidity coefficients applied:")
    logger.info(df["liquidity_coef"].value_counts().to_string())

    logger.info("Category → coef mapping sample:")
    logger.info(
    df[["liquidity_category", "liquidity_coef"]]
    .drop_duplicates()
    .sort_values("liquidity_category")
    .to_string(index=False)
    )

    logger.info(f"Total rows: {len(df)}")
    logger.info(f"Coef map size: {len(coef_map)}")

    # Keep nice order for downstream
    preferred_order = [
        "price_group",
        "article",
        "name",
        "stock",
        "unit",
        "price",
        "liquidity_category",
        "liquidity_coef",
    ]
    remaining = [c for c in df.columns if c not in preferred_order]
    df = df[[c for c in preferred_order if c in df.columns] + remaining]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(OUTPUT_FILE, index=False)

    logger.info(f"Saved: {OUTPUT_FILE.name}")
    logger.info("DONE → pricing_apply_liquidity")


if __name__ == "__main__":
    main()