import argparse
import pandas as pd
import yaml
import logging
import time
import json
import numpy as np
import sys
import os


def setup_logging(log_file):
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def load_config(config_path):
    if not os.path.exists(config_path):
        raise Exception("Config file not found")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    required_fields = ["seed", "window", "version"]
    for field in required_fields:
        if field not in config:
            raise Exception(f"Missing config field: {field}")

    # Strict validation
    if not isinstance(config["window"], int) or config["window"] <= 0:
        raise Exception("Window must be a positive integer")

    return config


def load_data(input_path):
    if not os.path.exists(input_path):
        raise Exception("Input CSV file not found")

    try:
        with open(input_path, "r") as f:
            lines = f.readlines()

        if len(lines) == 0:
            raise Exception("CSV file is empty")

        header = lines[0].strip().split(",")
        data = [line.strip().split(",") for line in lines[1:]]

        df = pd.DataFrame(data, columns=header)

    except Exception:
        raise Exception("Invalid CSV format")

    if df.empty:
        raise Exception("CSV file is empty")

    # Normalize columns
    df.columns = [col.lower().strip() for col in df.columns]

    if "close" not in df.columns:
        raise Exception("Missing 'close' column in dataset")

    # Convert close to numeric safely
    df["close"] = pd.to_numeric(df["close"], errors="coerce")

    return df


def compute_signals(df, window):
    df["rolling_mean"] = df["close"].rolling(window=window).mean()
    df["signal"] = (df["close"] > df["rolling_mean"]).astype(int)

    # Remove NaN rows
    df = df.dropna().reset_index(drop=True)

    return df


def write_metrics(output_path, data):
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--log-file", required=True)

    args = parser.parse_args()

    setup_logging(args.log_file)

    start_time = time.time()

    try:
        logging.info("Job started")

        # Load config
        config = load_config(args.config)
        seed = config["seed"]
        window = config["window"]
        version = config["version"]

        np.random.seed(seed)

        logging.info(f"Config loaded: {config}")

        # Load data
        df = load_data(args.input)
        logging.info(f"Rows loaded: {len(df)}")

        # Data quality check
        missing_close = int(df["close"].isna().sum())

        # Basic stats
        close_min = float(df["close"].min())
        close_max = float(df["close"].max())
        close_std = float(df["close"].std())

        logging.info("Data quality and stats computed")

        # Process signals
        df = compute_signals(df, window)
        logging.info("Signals computed")

        # Metrics
        rows_processed = len(df)
        signal_rate = float(df["signal"].mean())

        buy_signals = int(df["signal"].sum())
        no_buy_signals = int(rows_processed - buy_signals)

        latency_ms = int((time.time() - start_time) * 1000)

        metrics = {
            "version": version,
            "rows_processed": rows_processed,
            "metric": "signal_rate",
            "value": round(signal_rate, 4),
            "buy_signals": buy_signals,
            "no_buy_signals": no_buy_signals,
            "missing_close_values": missing_close,
            "close_min": round(close_min, 2),
            "close_max": round(close_max, 2),
            "close_std": round(close_std, 2),
            "latency_ms": latency_ms,
            "seed": seed,
            "status": "success",
        }

        logging.info(f"Metrics: {metrics}")
        logging.info("Job completed successfully")

        write_metrics(args.output, metrics)

        print(json.dumps(metrics, indent=2))
        sys.exit(0)

    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)

        error_output = {
            "version": "v1",
            "status": "error",
            "error_message": str(e),
        }

        logging.error(f"Error occurred: {str(e)}")

        write_metrics(args.output, error_output)

        print(json.dumps(error_output, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()