# MLOps Trading Signal Pipeline

A minimal, production-style MLOps batch pipeline for processing financial time-series data and generating trading signals.

---

## Overview

Given OHLCV financial data, this pipeline:

1. Computes a **rolling mean** on closing prices
2. Generates a **binary trading signal** — `1` if price is above the rolling mean (buy), `0` otherwise
3. Outputs structured metrics and logs for monitoring

**Core MLOps principles applied:**
- **Reproducibility** — configuration-driven with fixed seed control
- **Observability** — structured metrics and detailed logs
- **Deployment readiness** — fully Dockerized

---

## Dataset

The pipeline expects time-series financial data with the following columns:

| Column | Description |
|---|---|
| `timestamp` | Time of record |
| `open`, `high`, `low`, `close` | Price information |
| `volume` | Trading activity |

> Only the `close` price is used — it represents the final market value for each time step.

---

## Pipeline Workflow

### 1. Configuration Loading
- Reads parameters from `config.yaml`
- Validates required fields: `seed`, `window`, `version`
- Ensures deterministic execution via fixed seed

### 2. Data Ingestion & Validation
- Reads input CSV with robust malformed-file handling
- Normalizes column names
- Validates presence of `close` column
- Safely converts values to numeric

### 3. Feature Engineering
- Computes rolling mean over a configurable window
- Handles initial NaN values from rolling computation

### 4. Signal Generation
```python
signal = 1 if close > rolling_mean else 0
```

### 5. Metrics Computation

| Metric | Description |
|---|---|
| `rows_processed` | Valid rows after rolling computation |
| `signal_rate` | Proportion of positive signals |
| `buy_signals` / `no_buy_signals` | Signal distribution |
| `missing_close_values` | Data quality indicator |
| `close_min` / `close_max` / `close_std` | Statistical summary of input |
| `latency_ms` | Total execution time |

### 6. Logging
Writes detailed logs to `run.log`, including job timestamps, config details, data loading status, processing steps, metrics summary, and any errors.

---

## Output

### Success — `metrics.json`
```json
{
  "version": "v1",
  "rows_processed": 9996,
  "metric": "signal_rate",
  "value": 0.4991,
  "buy_signals": 4989,
  "no_buy_signals": 5007,
  "missing_close_values": 0,
  "close_min": 41939.28,
  "close_max": 50949.16,
  "close_std": 2410.69,
  "latency_ms": 66,
  "seed": 42,
  "status": "success"
}
```

### Failure — `metrics.json`
```json
{
  "version": "v1",
  "status": "error",
  "error_message": "Description of failure"
}
```

> Metrics are always generated — in both success and failure scenarios.

---

## Running the Project

### Local
```bash
pip install -r requirements.txt
python run.py --input data.csv --config config.yaml --output metrics.json --log-file run.log
```

### Docker
```bash
docker build -t mlops-task .
docker run --rm mlops-task
```

---

## Design Decisions

- **Deterministic runs** — fixed random seed ensures reproducibility
- **Robust CSV handling** — pipeline recovers gracefully from malformed inputs
- **Separation of concerns** — config, ingestion, processing, and metrics are fully decoupled
- **Fail-safe design** — metrics are emitted even on pipeline failure
- **Structured outputs** — JSON metrics are ready for downstream consumption

---

## Enhancements Beyond Requirements

- Signal distribution metrics (`buy` vs `no-buy` counts)
- Data quality tracking (`missing_close_values`)
- Statistical summary of input data (`min`, `max`, `std`)
- Strict configuration validation with clear error messages
- Enhanced structured logging for full observability
