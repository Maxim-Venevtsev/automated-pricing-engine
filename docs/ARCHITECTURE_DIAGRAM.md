# Pipeline Architecture

                    EMAIL (supplier)
                          │
                          ▼
                ingestion_email.py
                          │
                          ▼
                ingestion_step1_clean
                          │
                          ▼
                ingestion_step2_validate
                          │
                          ▼
                ingestion_step3_filter
                          │
                          ▼
                ingestion_step4_normalize
                          │
                          ▼
                 corrected_price_4.xlsx
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
     ingestion_snapshot            pricing_apply_liquidity
            │                           │
            ▼                           ▼
     liquidity_recalculation        pricing_core
            │                           │
            ▼                           ▼
     liquidity_export             registry_update
            │                           │
            └─────────────┬─────────────┘
                          ▼
                     export_build
                          │
                          ▼
                     export_format
                          │
                          ▼
                     email_delivery
                          │
                          ▼
                     Dealers receive price list

------------------------------------------------------------------------

# System Layers

## Pipelines

Orchestration layer.

    pipelines/full_pipeline.py

Responsible for running stages.

------------------------------------------------------------------------

## Application Layer

Business logic:

pricing\
ingestion\
export\
liquidity

------------------------------------------------------------------------

## Infrastructure Layer

External systems:

email\
database\
file system
