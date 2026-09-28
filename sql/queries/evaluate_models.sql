-- Side-by-side comparison of the two model families using ML.EVALUATE.
-- ARIMA_PLUS's evaluation columns differ from a regressor's, so this UNIONs
-- the metrics both expose in common (mean_absolute_error / mean_squared_error)
-- rather than forcing one schema on both.
SELECT
  'arima_plus' AS model_name,
  mean_absolute_error,
  mean_squared_error
FROM ML.EVALUATE(MODEL {arima_ref})

UNION ALL

SELECT
  'boosted_tree_regressor' AS model_name,
  mean_absolute_error,
  mean_squared_error
FROM ML.EVALUATE(MODEL {boosted_tree_ref});
