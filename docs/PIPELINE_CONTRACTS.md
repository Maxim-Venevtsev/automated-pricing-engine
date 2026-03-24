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

## Runtime Directory Contracts

The pipeline uses the following runtime directories:

- `data/incoming/`
- `data/staging/`
- `data/output/`
- `data/validation/`
- `data/state/`

### Contract

These directories are required for pipeline execution, but their contents are environment-specific runtime artifacts and must not be committed to Git.

The repository keeps these directories only through placeholder files:

- `data/incoming/.gitkeep`
- `data/staging/.gitkeep`
- `data/output/.gitkeep`
- `data/validation/.gitkeep`
- `data/state/.gitkeep`

### Rules

1. The directories must always exist in the project structure.
2. Only `.gitkeep` is allowed in Git inside these directories.
3. Production files generated or consumed by the pipeline must remain local and untracked.
4. Cleanup and refactoring tasks must preserve these directories and their `.gitkeep` files.
5. Any pipeline step that writes runtime artifacts must write them only into the designated runtime directories.

### Examples of disallowed files in Git

- `data/incoming/*.xls`
- `data/incoming/*.xlsx`
- `data/staging/*.xlsx`
- `data/output/*.xlsx`
- `data/validation/*`
- `data/state/*`

### Reference Data Exception

Files stored in `data/reference/` are treated separately.  
They are not runtime artifacts and may be version-controlled when they are required for reproducible pipeline behavior.

### Git Enforcement

This contract is enforced through:
- `.gitignore`
- `.gitkeep` placeholders
- `pre-commit` hook checks