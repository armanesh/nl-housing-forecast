#!/usr/bin/env bash
# Runs the whole pipeline in --dry-run mode: no GCP project needed.
# Shows exactly what SQL would run against BigQuery at each step.
set -euo pipefail
cd "$(dirname "$0")/.."

housing generate-sample --out data/sample/regional_price_index.csv --regions 12 --months 96
housing init --dry-run
housing load --source data/sample/regional_price_index.csv --dry-run
housing build-features --dry-run
housing train --model arima --dry-run
housing train --model boosted-tree --dry-run
housing evaluate --dry-run
housing predict --model arima --horizon 6 --dry-run
housing predict --model boosted-tree --horizon 6 --dry-run
housing register --model boosted-tree --dry-run
