-- Raw monthly regional house price data, as loaded from CBS-style CSV exports.
CREATE TABLE IF NOT EXISTS {raw_ref} (
  region STRING NOT NULL OPTIONS (description = 'CBS region / municipality name'),
  month DATE NOT NULL OPTIONS (description = 'First day of the month this row reports'),
  avg_sale_price_eur FLOAT64 OPTIONS (description = 'Average sale price in EUR for existing owner-occupied dwellings'),
  mortgage_rate_pct FLOAT64 OPTIONS (description = 'Average 10-year fixed mortgage rate, percent'),
  new_build_permits INT64 OPTIONS (description = 'New-build permits issued in the region that month')
)
PARTITION BY month
CLUSTER BY region
OPTIONS (
  description = 'Raw ingested regional house price index, one row per region per month'
);
