# MLOps Trading Signal Pipeline

> A production-grade batch pipeline for financial time-series processing and automated signal generation — built with reproducibility, observability, and deployment readiness at its core.

## What It Does

This pipeline ingests raw OHLCV financial data and transforms it into actionable trading signals using a rolling mean strategy:

- Computes a **configurable rolling mean** over closing prices
- Emits a **binary signal** — `1` (buy) when price exceeds the mean, `0` otherwise
- Produces **structured JSON metrics** and detailed logs on every run

## Dataset

The pipeline expects a CSV with standard OHLCV columns. Only `close` is consumed — it represents the final market price for each time step.
```
timestamp | open | high | low | close | volume
```

## Core Principles

| Principle | Implementation |
|---|---|
| **Reproducibility** | Config-driven execution with fixed random seed |
| **Observability** | Structured metrics + timestamped run logs |
| **Reliability** | Metrics emitted on both success *and* failure |
| **Portability** | Fully containerized via Docker |

## Pipeline Architecture
```
config.yaml ──► [1] Load & Validate Config
                        │
data.csv ───────► [2] Ingest & Validate Data
                        │
                [3] Feature Engineering
                   rolling_mean(close, window)
                        │
                [4] Signal Generation
                   signal = 1 if close > rolling_mean
                        │
                [5] Compute Metrics + Write Logs
                        │
                metrics.json + run.log
```

### Stage Breakdown

**1 · Configuration** — Reads `config.yaml`, validates required fields (`seed`, `window`, `version`), and sets the random seed for deterministic execution.

**2 · Ingestion & Validation** — Parses CSV with malformed-file tolerance, normalizes column names, validates the `close` column, and safely coerces values to numeric.

**3 · Feature Engineering** — Computes a rolling mean over a configurable window. Initial NaN rows from the warm-up period are cleanly handled.

**4 · Signal Generation** — Applies the core rule per row:
```python
signal = 1 if close > rolling_mean else 0
```

**5 · Metrics & Logging** — Aggregates runtime statistics and writes to `metrics.json`. Full execution trace written to `run.log`.

## Quickstart

**Run locally:**
```bash
pip install -r requirements.txt
python run.py \
  --input data.csv \
  --config config.yaml \
  --output metrics.json \
  --log-file run.log
```

**Run with Docker:**
```bash
docker build -t mlops-task .
docker run --rm mlops-task
```

## Metrics Reference

| Metric | Description |
|---|---|
| `rows_processed` | Valid rows after rolling window warm-up |
| `signal_rate` | Fraction of rows with a positive (buy) signal |
| `buy_signals` | Count of rows where `signal = 1` |
| `no_buy_signals` | Count of rows where `signal = 0` |
| `missing_close_values` | Null/unparseable close prices — data quality indicator |
| `close_min / max / std` | Statistical summary of the input price series |
| `latency_ms` | End-to-end wall-clock execution time |

## Output Schema

### Success
```json
{
  "version": "v1",
  "status": "success",
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
  "seed": 42
}
```

### Failure
```json
{
  "version": "v1",
  "status": "error",
  "error_message": "Description of failure"
}
```

## Design Decisions

**Fail-safe metrics** — `metrics.json` is always written, even when the pipeline errors. Downstream monitors never face a missing file.

**Strict config validation** — Required fields are checked at startup. Misconfigured runs fail fast with clear messages rather than silently producing bad output.

**Separation of concerns** — Config loading, ingestion, feature engineering, signal generation, and metrics are fully decoupled modules. Each is independently testable.

**Robust CSV parsing** — Malformed rows are handled gracefully. Column names are normalized to prevent casing mismatches.

**Deterministic execution** — A fixed seed guarantees identical outputs across runs given the same inputs and config — essential for debugging and auditing.

## Enhancements Beyond Requirements

- Signal distribution breakdown (`buy_signals` vs `no_buy_signals`)
- Input data quality tracking via `missing_close_values`
- Full statistical summary of the price series (`min`, `max`, `std`)
- Strict config validation with actionable error messages
- Structured logging with job start/end timestamps for full traceability

## Conclusion

This project demonstrates that even a focused, single-signal pipeline can be engineered to production standards. By embedding MLOps best practices — deterministic execution, structured observability, fail-safe outputs, and containerized deployment — from the ground up, the system is not just functional but genuinely operatable.

The architecture is intentionally lean yet extensible. The same scaffold that powers this rolling mean strategy can accommodate more complex models, additional signal types, or real-time streaming with minimal structural change. Every design choice — from config validation to error-time metrics — reflects the reality that **pipelines fail in production, and the ones that survive are the ones built to handle it gracefully**.

This is what separates a script from a system.
