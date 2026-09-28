-- ML.FORECAST natively produces a per-region forecast with confidence
-- intervals for ARIMA_PLUS models; {horizon} is the number of months ahead.
SELECT
  region,
  forecast_timestamp AS month,
  forecast_value AS forecast_avg_sale_price_eur,
  prediction_interval_lower_bound,
  prediction_interval_upper_bound
FROM ML.FORECAST(MODEL {model_ref}, STRUCT({horizon} AS horizon, 0.9 AS confidence_level))
ORDER BY region, month;
