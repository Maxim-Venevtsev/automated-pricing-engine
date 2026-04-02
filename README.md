# 🚀 Automated Pricing Engine

Production-grade data pipeline for automated pricing in wholesale automotive parts.

This project processes supplier price lists, applies pricing logic (including liquidity-based adjustments), generates dealer-ready Excel outputs, and delivers them automatically via email. 
It handles evolving supplier formats with backward compatibility.

---

## ✨ Key Features

* 📥 **Automated ingestion**

  * fetch supplier Excel files via email
  * normalize and clean raw data
  * supports multiple supplier file formats (legacy + updated structure)
  * automatic header detection and column mapping

* 🔄 **Multi-stage data transformation**

  * structured ETL pipeline using pandas
  * consistent normalization of articles, names, and price groups

* 💰 **Pricing engine**

  * liquidity-based pricing adjustments
  * business rule–driven price calculation
  * support for “new item” logic

* 📊 **Output generation**

  * formatted Excel files for dealers
  * multiple output layers (build + format)

* 📤 **Automated delivery**

  * email distribution to dealer network
  * delivery safeguards (anti-duplicate logic)

---

## 🧠 Architecture

The project follows a modular architecture inspired by production data systems:

```text
src/pricing_engine/
│
├── pipelines/        # orchestration layer
├── application/      # business logic (ETL, pricing, export)
├── infrastructure/   # external systems (email, DB)
└── domain/           # data models (future extension)
```

### Key design principles:

* separation of concerns
* explicit data contracts between pipeline stages
* isolation of runtime and reference data
* reproducible pipeline execution

---

## 📂 Project Structure

```text
automated-pricing-engine/
│
├── configs/          # settings & constants
├── data/
│   ├── incoming/     # raw inputs (runtime)
│   ├── staging/      # intermediate files (runtime)
│   ├── output/       # final exports (runtime)
│   ├── reference/    # controlled reference data
│   └── state/        # pipeline state
│
├── docs/             # architecture & contracts
├── logs/             # runtime logs
├── src/              # core pipeline code
└── tests/            # (planned)
```

---

## ⚙️ Configuration Model

The system uses a layered configuration approach:

* **settings.py** → environment & paths
* **constants.py** → business rules
* `.env` → secrets (not tracked in Git)

---

## 🔐 Data & Git Policy

Runtime data is **never committed to Git**.

Ignored directories:

* `data/incoming/`
* `data/staging/`
* `data/output/`
* `data/state/`

Structure is preserved via `.gitkeep`.

Sensitive data is protected via:

* `.env` exclusion
* pre-commit checks

---

## ▶️ Running the Pipeline

```bash
python -m pricing_engine.pipelines.full_pipeline --with-ingestion
```

Optional flags:

```bash
--with-ingestion
--historical
```

---

## 📊 Pipeline Stages

1. **Ingestion**
2. **Validation & Normalization**
3. **Liquidity & Pricing**
4. **Export**
5. **Delivery**

---

## 🧪 Current Status

✅ Production-ready pipeline (contracts-cleanup stage completed)
🔜 Next steps:

* base price versioning (snapshots + diff logic)
* analytics layer (Power BI + MySQL)
* dealer-specific pricing profiles

---

## 🧭 Roadmap

* daily base price update pipeline
* pricing analytics & dashboards
* elasticity analysis
* marketplace integration

---

## 📌 Repository

👉 https://github.com/Maxim-Venevtsev/automated-pricing-engine

---

## 🤝 Feedback

Open to feedback, ideas, and discussions.
