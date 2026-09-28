#!/usr/bin/env bash
# Runs the whole pipeline for real against BigQuery. Requires
# GOOGLE_CLOUD_PROJECT to be set and `gcloud auth application-default login`
# (or a service account key) to already be configured.
set -euo pipefail
cd "$(dirname "$0")/.."

: "${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT before running this script}"

if [ ! -f data/sample/regional_price_index.csv ]; then
  housing generate-sample --out data/sample/regional_price_index.csv --regions 12 --months 96
fi

housing init
housing load --source data/sample/regional_price_index.csv
housing build-features
housing train --model arima
housing train --model boosted-tree
housing evaluate
housing predict --model arima --horizon 6 --out data/forecast_arima.csv
housing predict --model boosted-tree --horizon 6 --out data/forecast_boosted_tree.csv

echo "Done. Forecasts written to data/forecast_arima.csv and data/forecast_boosted_tree.csv"
echo "To push the boosted-tree model to Vertex AI Model Registry, run:"
echo "  housing register --model boosted-tree --gcs-uri gs://<your-bucket>/nl-housing-forecast/boosted-tree/"
