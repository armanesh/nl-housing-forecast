-- Per-region ARIMA_PLUS baseline. time_series_id_col lets one CREATE MODEL
-- statement fit an independent ARIMA per region, which BigQuery ML
-- parallelises for you.
CREATE OR REPLACE MODEL {model_ref}
OPTIONS (
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'month',
  time_series_data_col = 'avg_sale_price_eur',
  time_series_id_col = 'region',
  auto_arima = TRUE,
  data_frequency = 'MONTHLY',
  decompose_time_series = TRUE,
  holiday_region = 'NL'
) AS
SELECT
  region,
  month,
  avg_sale_price_eur
FROM {features_ref};
