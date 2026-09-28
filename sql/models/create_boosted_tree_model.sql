-- Feature-based alternative to the ARIMA baseline: gradient-boosted trees
-- over lags, rolling stats, seasonality, and the exogenous regressors
-- (mortgage rate, permits) that ARIMA_PLUS can't use directly. Rows with
-- NULL lag features (the first 12 months of each region's history) are
-- dropped, since BQML can't train on NULL labels/features for this model type.
CREATE OR REPLACE MODEL {model_ref}
OPTIONS (
  model_type = 'BOOSTED_TREE_REGRESSOR',
  input_label_cols = ['avg_sale_price_eur'],
  max_iterations = 50,
  learn_rate = 0.1,
  subsample = 0.85,
  early_stop = TRUE,
  data_split_method = 'SEQ',
  data_split_col = 'month',
  data_split_eval_fraction = 0.2
) AS
SELECT
  avg_sale_price_eur,
  price_lag_1,
  price_lag_3,
  price_lag_12,
  price_rolling_mean_3,
  price_rolling_mean_12,
  mortgage_rate_pct,
  new_build_permits,
  month_of_year,
  region
FROM {features_ref}
WHERE price_lag_12 IS NOT NULL;
