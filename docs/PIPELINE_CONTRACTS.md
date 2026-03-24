# Pipeline Data Contracts

## ingestion_step1_clean → output

Columns:

price_group article name stock unit price

Description: Normalized raw supplier price list columns.

------------------------------------------------------------------------

## ingestion_step4_normalize → output

price_group article name stock unit price

Rules:

HYUNDAI → HYUNDAI/KIA string normalization numeric cleaning

------------------------------------------------------------------------

## pricing_apply_liquidity → output

price_group article name stock unit price liquidity_category
liquidity_coef

Description: Liquidity category attached from DB/export.

------------------------------------------------------------------------

## pricing_core → output

price_group article name stock unit price liquidity_category flag

Description: Final calculated price + flags.

------------------------------------------------------------------------

## export_build → output

price_group article name stock unit price flag liquidity_category

Description: Filtered dataset for export.

------------------------------------------------------------------------

## export_format → final Excel

Columns displayed:

Ценовая группа Артикул Номенклатура Остаток Ед. Цена (с НДС) flag
