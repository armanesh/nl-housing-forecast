# NL Housing Forecast

Forecasting Dutch residential housing prices with **BigQuery ML** and, optionally,
**Vertex AI** for registry, batch prediction, and monitoring. Built as a portfolio
project: it uses CBS (Statistics Netherlands) style regional house price index data,
but ships with a synthetic data generator so the whole pipeline runs end to end
without any external credentials.

## Why this project

Most "housing price prediction" repos on GitHub are a single notebook with a
`RandomForestRegressor` on the Ames or California dataset. This one instead shows
the skills that come up in a GCP-based data/AI role:

- Designing a BigQuery schema and partitioned/clustered tables for a time series
- Feature engineering entirely in SQL (lags, rolling averages, seasonality flags)
- Training and evaluating two BigQuery ML model families on the same data:
  - `ARIMA_PLUS` for a classical, per-region time series baseline
  - `BOOSTED_TREE_REGRESSOR` for a features-based model that can use exogenous
    regressors (interest rate, mortgage rate, new-build permits)
- Exporting a trained BigQuery ML model to **Vertex AI Model Registry** and running
  batch predictions from there
- A thin Python CLI that wraps the whole workflow (`load`, `build-features`,
  `train`, `evaluate`, `predict`, `register`) so it is runnable, not just readable
- Tests for the parts that don't need a live GCP project (SQL templating, feature
  logic, CLI argument handling), plus a CI workflow that runs them on every push

## Architecture

```
Raw CSV (CBS-style regional price index, monthly)
        │  bq load
        ▼
housing_raw.regional_price_index          (BigQuery, partitioned by month)
        │  sql/features/build_features.sql
        ▼
housing_features.monthly_features          (lags, rolling stats, seasonality)
        │                       │
        ▼                       ▼
 ARIMA_PLUS model        BOOSTED_TREE_REGRESSOR model
 (per-region time         (features + exogenous regressors)
  series baseline)
        │                       │
        └───────────┬───────────┘
                     ▼
        sql/queries/evaluate_models.sql (ML.EVALUATE side by side)
                     │
                     ▼
        Vertex AI Model Registry (optional, via `housing register`)
                     │
                     ▼
        Batch prediction job → forecast written back to BigQuery
```

## Repo layout

```
src/housing/          Python package: CLI + BigQuery/Vertex AI clients + data gen
sql/schema/           DDL for raw and feature tables
sql/features/         Feature engineering SQL (parameterised, run via the CLI)
sql/models/           CREATE MODEL statements for ARIMA_PLUS and boosted trees
sql/queries/          Evaluation and forecast-retrieval queries
scripts/              One-shot shell scripts that chain the CLI + bq commands
data/sample/          Small synthetic CSV so `make demo` works with zero setup
tests/                Unit tests that don't require a live GCP project
notebooks/            One exploratory notebook (EDA + result plots)
.github/workflows/    CI: lint + tests on push/PR
```

## Quickstart (no GCP account needed)

The synthetic data path lets you inspect the whole pipeline logic locally:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# generate a synthetic dataset shaped like CBS regional price data
housing generate-sample --out data/sample/regional_price_index.csv --regions 12 --months 96

# see the SQL each step would run against BigQuery, without executing it
housing build-features --dry-run
housing train --model arima --dry-run
housing train --model boosted-tree --dry-run

pytest
```

## Running it for real against BigQuery

```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
export BQ_DATASET_RAW=housing_raw
export BQ_DATASET_FEATURES=housing_features
export BQ_DATASET_MODELS=housing_models
export BQ_LOCATION=EU   # CBS data lives in the EU; keep datasets in the same region

# 1. create datasets + tables
housing init

# 2. load CSV (your own export, or the generated sample) into BigQuery
housing load --source data/sample/regional_price_index.csv

# 3. build the feature table with SQL (lags, rolling means, month dummies)
housing build-features

# 4. train both model families
housing train --model arima
housing train --model boosted-tree

# 5. compare them with ML.EVALUATE
housing evaluate

# 6. forecast the next 6 months per region
housing predict --horizon 6 --out data/forecast.csv

# 7. optional: push the boosted-tree model to Vertex AI Model Registry
housing register --model boosted-tree --display-name nl-housing-boosted-tree
```

Or run the whole thing with `make demo` (dry-run) or `make pipeline` (live, needs
`GOOGLE_CLOUD_PROJECT` set and `gcloud auth application-default login` done).

## Data source

The real data source this project is built around is CBS StatLine's "Bestaande
koopwoningen; verkoopprijzen" (existing owner-occupied dwellings; sale prices)
and the regional house price index, both published monthly and freely available
via the CBS OData API (see `docs/data_sources.md`). `housing generate-sample`
produces a CSV with the same columns and realistic seasonality/trend/noise so the
rest of the pipeline can be developed and tested without hitting that API.

## Notes on design choices

- **Why two model families instead of one:** it is the more honest way to show
  BigQuery ML competence. `ARIMA_PLUS` is the right default for a pure time
  series with no useful exogenous signal; boosted trees earn their place once you
  add mortgage rate / permits data. Evaluating both side by side with the same
  `ML.EVALUATE` query is the point, not picking a "winner" up front.
- **Why SQL-first feature engineering:** in a BigQuery ML workflow the features
  should live next to the data, not get pulled into pandas and pushed back. The
  Python layer here orchestrates and parameterises SQL; it does not reimplement
  feature logic in pandas.
- **Why the CLI has a `--dry-run` on every command:** so the whole pipeline is
  reviewable (and testable in CI) without a GCP project or billing account.

## License

MIT, see `LICENSE`.
