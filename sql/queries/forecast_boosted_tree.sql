-- Unlike ARIMA_PLUS, a BOOSTED_TREE_REGRESSOR has no built-in notion of
-- "the future": ML.PREDICT needs a row of features for every month you want a
-- prediction for. This query builds those future rows by carrying the most
-- recent known price forward as a stand-in for the lag features, and holding
-- mortgage_rate_pct / new_build_permits at their latest observed value.
--
-- That is a simplification worth calling out explicitly: a production version
-- would instead join in a real forecast/plan for mortgage rates and permits,
-- and update the lag features iteratively month by month using the model's
-- own prior predictions. Doing that recursively in pure SQL is possible but
-- adds real complexity for a portfolio project, so it's left as a documented
-- next step (see README) rather than pretending this is more than a
-- reasonable naive baseline.

WITH latest_per_region AS (
  SELECT
    region,
    ARRAY_AGG(STRUCT(month, avg_sale_price_eur, mortgage_rate_pct, new_build_permits)
              ORDER BY month DESC LIMIT 1)[OFFSET(0)] AS latest
  FROM {features_ref}
  GROUP BY region
),
future_months AS (
  SELECT
    region,
    DATE_ADD(latest.month, INTERVAL offset MONTH) AS month,
    latest.avg_sale_price_eur AS carried_price,
    latest.mortgage_rate_pct AS mortgage_rate_pct,
    latest.new_build_permits AS new_build_permits
  FROM latest_per_region,
       UNNEST(GENERATE_ARRAY(1, {horizon})) AS offset
)
SELECT
  region,
  month,
  predicted_avg_sale_price_eur
FROM ML.PREDICT(
  MODEL {model_ref},
  (
    SELECT
      region,
      month,
      carried_price AS price_lag_1,
      carried_price AS price_lag_3,
      carried_price AS price_lag_12,
      carried_price AS price_rolling_mean_3,
      carried_price AS price_rolling_mean_12,
      mortgage_rate_pct,
      new_build_permits,
      EXTRACT(MONTH FROM month) AS month_of_year
    FROM future_months
  )
)
ORDER BY region, month;
