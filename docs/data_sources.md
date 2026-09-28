# Data sources

This project is modeled on two CBS (Statistics Netherlands) StatLine datasets:

- **Bestaande koopwoningen; verkoopprijzen** (existing owner-occupied dwellings,
  sale prices), published monthly, broken down by region and property type.
- **Regionale kerncijfers / huizenprijsindex** (regional house price index),
  which underlies the Kadaster/CBS house price index used in most Dutch market
  reporting.

Both are queryable via the free CBS OData v4 API, for example:

```
https://opendata.cbs.nl/ODataApi/odata/83625NED/TypedDataSet
```

(dataset ID `83625NED` is the "Bestaande koopwoningen" table as of this
writing; CBS renumbers tables occasionally, so search
https://opendata.cbs.nl for the current ID if this one 404s).

Mortgage rate data can be sourced from De Nederlandsche Bank (DNB) statistics,
and new-build permit counts from CBS's `Verleende bouwvergunningen` table.

## Why this repo uses a synthetic generator instead of calling the API directly

Three reasons:

1. It keeps the repo runnable with zero network access and zero setup, which
   matters for a portfolio project someone might clone and run in one sitting.
2. It keeps the CI pipeline fast and independent of an external API's
   uptime or schema changes.
3. It lets the pipeline logic (lags, rolling windows, model comparison) be
   demonstrated against data with known, designed-in properties (trend,
   seasonality, a rate-driven slowdown), which makes it easier to sanity-check
   that the feature engineering and forecasts behave as expected.

Swapping in real CBS data only requires writing a small loader that calls the
OData endpoint and reshapes it into the same five columns
(`region, month, avg_sale_price_eur, mortgage_rate_pct, new_build_permits`)
that `housing load` expects, then pointing `--source` at that CSV.
