# Automated Pricing Engine --- Project Passport

## Overview

Automated pipeline for processing supplier price lists, applying pricing
rules, calculating liquidity-based adjustments, generating formatted
dealer price lists, and delivering them via email.

The system is designed as a modular ETL + pricing pipeline with optional
database ingestion and liquidity analytics.

------------------------------------------------------------------------

# 1. High-Level Architecture

Email attachment (supplier price) ↓ Download incoming XLS ↓ Data
cleaning / normalization ↓ (Optional) Database ingestion ↓ Liquidity
recalculation ↓ Liquidity coefficient pricing ↓ Core pricing logic ↓
Registry update (NEW items) ↓ Output dataset generation ↓ Excel
formatting ↓ Email delivery to dealers

------------------------------------------------------------------------

# 2. Repository Structure

automated-pricing-engine │ ├── analytics/ ├── configs/ │ ├── settings.py
│ └── constants.py │ ├── data/ │ ├── incoming/ │ ├── staging/ │ ├──
output/ │ ├── reference/ │ ├── state/ │ └── validation/ │ ├── docs/ ├──
logs/ ├── scripts/ │ ├── src/pricing_engine/ │ ├── pipelines/ │ ├──
application/ │ ├── infrastructure/ │ └── domain/ │ └── tests/

------------------------------------------------------------------------

# 3. Pipeline Entry Point

Run pipeline:

python -m pricing_engine.pipelines.full_pipeline

Optional flags:

--with-ingestion --historical

------------------------------------------------------------------------

# 4. Data Contracts

After ingestion_step1_clean:

price_group article name stock unit price

After pricing_apply_liquidity:

-   liquidity_category
-   liquidity_coef

After export_build:

-   flag
-   liquidity_category

------------------------------------------------------------------------

# 5. Pipeline Stages

STAGE 1 --- INGESTION

1.  ingestion_email.py\
2.  ingestion_step1_clean.py\
3.  ingestion_step2_validate.py\
4.  ingestion_step3_filter.py\
5.  ingestion_step4_normalize.py

STAGE 2 --- DATABASE & LIQUIDITY

1.  ingestion_snapshot.py\
2.  liquidity_recalculation.py\
3.  liquidity_export.py

STAGE 3 --- PRICING

1.  pricing_apply_liquidity.py\
2.  pricing_core.py\
3.  registry_update.py

STAGE 4 --- OUTPUT

1.  export_build.py\
2.  export_format.py

STAGE 5 --- DELIVERY

email_delivery.py

------------------------------------------------------------------------

# 6. Reference Files

dealers.csv --- dealer email list\
liquidity_coef.xlsx --- liquidity coefficients\
liquidity_category.xlsx --- calculated liquidity\
allowed_price_groups.xlsx --- allowed groups\
dealer.txt --- email template

------------------------------------------------------------------------

# 7. State Files

data/state/items_presence_registry.csv

Columns:

article\
first_seen\
last_seen\
is_active

------------------------------------------------------------------------

# 8. Key Business Rules

NEW item:

days_since_first_seen ≤ NEW_DAYS

Special Offer:

liquidity_category ∈ {dead, low} AND flag != New!

Hyundai Sheet:

price_group == HYUNDAI/KIA

------------------------------------------------------------------------

# 9. Performance Bottlenecks

1.  Multiple Excel read/write operations\
2.  pandas → DB → pandas round trips\
3.  CSV registries\
4.  Liquidity recalculation scans

------------------------------------------------------------------------

# 10. Optimization Roadmap

Phase 1 --- Safe Refactor

remove intermediate Excel files\
unify dataframe pipeline

Phase 2 --- DB Optimization

SQLAlchemy\
connection pooling

Phase 3 --- Scaling

dealer‑specific pricing\
caching liquidity

------------------------------------------------------------------------

# 11. Testing

Recommended tests:

ingestion validation\
pricing rules\
registry logic\
export filters

------------------------------------------------------------------------

# 12. Requirements

Python 3.10+\
pandas\
openpyxl\
MySQL connector

Environment variables via `.env`.
