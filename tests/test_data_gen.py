from housing.data_gen import GenConfig, generate_rows


def test_generate_rows_shape():
    config = GenConfig(regions=3, months=24)
    rows = generate_rows(config)
    assert len(rows) == 3 * 24

    regions = {row["region"] for row in rows}
    assert len(regions) == 3


def test_generate_rows_is_deterministic_with_seed():
    config = GenConfig(regions=2, months=12, seed=7)
    rows_a = generate_rows(config)
    rows_b = generate_rows(config)
    assert rows_a == rows_b


def test_prices_and_permits_are_positive():
    rows = generate_rows(GenConfig(regions=4, months=36))
    for row in rows:
        assert row["avg_sale_price_eur"] > 0
        assert row["new_build_permits"] > 0
        assert 0 < row["mortgage_rate_pct"] < 15


def test_months_are_sequential_per_region():
    rows = generate_rows(GenConfig(regions=1, months=6, start_year=2020, start_month=11))
    months = [row["month"] for row in rows]
    assert months == [
        "2020-11-01",
        "2020-12-01",
        "2021-01-01",
        "2021-02-01",
        "2021-03-01",
        "2021-04-01",
    ]


def test_write_csv_round_trip(tmp_path):
    import csv

    from housing.data_gen import write_csv

    rows = generate_rows(GenConfig(regions=2, months=5))
    out_path = write_csv(rows, tmp_path / "sample.csv")

    with out_path.open(newline="", encoding="utf-8") as fh:
        reader = list(csv.DictReader(fh))

    assert len(reader) == len(rows)
    assert set(reader[0].keys()) == {
        "region",
        "month",
        "avg_sale_price_eur",
        "mortgage_rate_pct",
        "new_build_permits",
    }
