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

## Configuration Contracts

The pipeline configuration is divided into four contract layers.

### 1. Runtime Configuration

Runtime configuration defines environment-dependent paths and execution settings required for pipeline execution.

Examples:

- incoming directory
- staging directory
- output directory
- validation directory
- state directory
- logging configuration
- environment flags

Rules:

1. Runtime configuration must define where the pipeline reads and writes runtime artifacts.
2. Runtime configuration must not contain business pricing rules.
3. Runtime configuration must be environment-aware and safe for local development and production execution.
4. Runtime paths must resolve from the project root and must not rely on hardcoded machine-specific absolute paths inside business logic.

### 2. Reference Configuration

Reference configuration defines stable project inputs used by the pipeline as controlled reference artifacts.

Examples:

- base price source
- allowed price groups
- liquidity coefficients
- liquidity category mapping
- dealer list
- email templates

Rules:

1. Reference configuration points to version-controlled reference files.
2. Reference files are not treated as runtime artifacts.
3. Reference configuration must remain explicit and discoverable.
4. Changes to reference configuration must not silently redefine runtime storage policy.

### 3. Export Profile Configuration

Export profile configuration defines how output artifacts may differ by export target.

Examples:

- export naming rules
- sheet composition
- formatting profile
- product selection profile
- future dealer-specific export variants

Rules:

1. Export profile configuration defines output structure, not delivery behavior.
2. Export profile configuration must remain separable from pricing logic.
3. Adding new export profiles must not require rewriting runtime path contracts.
4. This contract is reserved for future profile-based exports and should be prepared but not overimplemented in the contracts-cleanup branch.

### 4. Delivery Profile Configuration

Delivery profile configuration defines how prepared output artifacts are distributed.

Examples:

- recipient groups
- sender identity
- email template selection
- delivery routing
- future per-profile sending rules

Rules:

1. Delivery profile configuration defines sending behavior, not export content.
2. Delivery profile configuration must remain separable from export profile configuration.
3. Delivery-specific settings must not be embedded directly into core pricing logic.
4. This contract is reserved for future delivery profile work and should be documented before implementation.

### Contract Boundary

The contracts-cleanup branch prepares these configuration boundaries without implementing the future business features that depend on them.

In particular, this branch does not yet implement:

- daily base price update automation
- profile-based export generation
- profile-based delivery routing
- separate sender identities by profile

### Derived Reference Artifacts

Some files may be generated or refreshed by the pipeline, while still serving as controlled reference inputs for downstream steps.

Example:

- `data/reference/liquidity_category.xlsx`

Such files are treated as derived reference artifacts.

Rules:

1. They may be updated by the pipeline.
2. They are intentionally stored in reference directories when downstream logic depends on them as stable categorized inputs.
3. They must not be treated as disposable runtime artifacts.
4. Their lifecycle and storage location must be explicitly documented to avoid confusion with pure runtime outputs.