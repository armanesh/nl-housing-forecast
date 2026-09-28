-- Empty shell for the feature table; build_features.sql fills it via
-- CREATE OR REPLACE TABLE ... AS SELECT, so this DDL only needs to exist for
-- `housing init` to have something idempotent to run before any data has
-- been loaded yet.
CREATE TABLE IF NOT EXISTS {features_ref} (
  region STRING,
  month DATE,
  avg_sale_price_eur FLOAT64,
  price_lag_1 FLOAT64,
  price_lag_3 FLOAT64,
  price_lag_12 FLOAT64,
  price_rolling_mean_3 FLOAT64,
  price_rolling_mean_12 FLOAT64,
  yoy_growth_pct FLOAT64,
  mortgage_rate_pct FLOAT64,
  new_build_permits INT64,
  month_of_year INT64
)
PARTITION BY month
CLUSTER BY region
OPTIONS (
  description = 'Feature table for BigQuery ML training: lags, rolling stats, seasonality'
);
