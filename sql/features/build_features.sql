-- Rebuilds the feature table from the raw table: per-region lags, rolling
-- means, year-over-year growth, and a plain month-of-year seasonality column
-- (BOOSTED_TREE_REGRESSOR handles a categorical INT64 fine; no need to
-- one-hot encode it ourselves, BQML's TRANSFORM/ML.FEATURE does that).
--
-- {lookback_months} controls how far back the lag/rolling windows look, so a
-- shorter history in --dry-run demos still produces a valid (if noisier) plan.

CREATE OR REPLACE TABLE {features_ref} AS
WITH base AS (
  SELECT
    region,
    month,
    avg_sale_price_eur,
    mortgage_rate_pct,
    new_build_permits
  FROM {raw_ref}
),
windowed AS (
  SELECT
    region,
    month,
    avg_sale_price_eur,
    mortgage_rate_pct,
    new_build_permits,
    LAG(avg_sale_price_eur, 1) OVER w AS price_lag_1,
    LAG(avg_sale_price_eur, 3) OVER w AS price_lag_3,
    LAG(avg_sale_price_eur, 12) OVER w AS price_lag_12,
    AVG(avg_sale_price_eur) OVER (
      PARTITION BY region ORDER BY UNIX_DATE(month)
      ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS price_rolling_mean_3,
    AVG(avg_sale_price_eur) OVER (
      PARTITION BY region ORDER BY UNIX_DATE(month)
      ROWS BETWEEN {lookback_months} PRECEDING AND CURRENT ROW
    ) AS price_rolling_mean_12
  FROM base
  WINDOW w AS (PARTITION BY region ORDER BY UNIX_DATE(month))
)
SELECT
  region,
  month,
  avg_sale_price_eur,
  price_lag_1,
  price_lag_3,
  price_lag_12,
  price_rolling_mean_3,
  price_rolling_mean_12,
  SAFE_DIVIDE(avg_sale_price_eur - price_lag_12, price_lag_12) * 100 AS yoy_growth_pct,
  mortgage_rate_pct,
  new_build_permits,
  EXTRACT(MONTH FROM month) AS month_of_year
FROM windowed
ORDER BY region, month;
