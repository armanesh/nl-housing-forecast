import pytest

from housing.config import Settings
from housing.sql_templates import render


@pytest.fixture
def settings():
    return Settings(
        project="test-project",
        location="EU",
        dataset_raw="housing_raw",
        dataset_features="housing_features",
        dataset_models="housing_models",
    )


def test_render_create_raw_table(settings):
    sql = render("schema/create_raw_table.sql", settings)
    assert "test-project.housing_raw.regional_price_index" in sql
    assert "PARTITION BY month" in sql


def test_render_build_features_substitutes_lookback(settings):
    sql = render("features/build_features.sql", settings, lookback_months="6")
    assert "6 PRECEDING" in sql
    assert "test-project.housing_raw.regional_price_index" in sql
    assert "test-project.housing_features.monthly_features" in sql


def test_render_create_arima_model(settings):
    sql = render(
        "models/create_arima_model.sql",
        settings,
        model_ref=settings.model_ref("nl_housing_arima"),
    )
    assert "test-project.housing_models.nl_housing_arima" in sql
    assert "ARIMA_PLUS" in sql


def test_render_create_boosted_tree_model(settings):
    sql = render(
        "models/create_boosted_tree_model.sql",
        settings,
        model_ref=settings.model_ref("nl_housing_boosted_tree"),
    )
    assert "BOOSTED_TREE_REGRESSOR" in sql
    assert "price_lag_12 IS NOT NULL" in sql


def test_render_evaluate_models(settings):
    sql = render(
        "queries/evaluate_models.sql",
        settings,
        arima_ref=settings.model_ref("nl_housing_arima"),
        boosted_tree_ref=settings.model_ref("nl_housing_boosted_tree"),
    )
    assert "nl_housing_arima" in sql
    assert "nl_housing_boosted_tree" in sql
    assert sql.count("ML.EVALUATE(MODEL") == 2


def test_render_forecast_arima(settings):
    sql = render(
        "queries/forecast_arima.sql",
        settings,
        model_ref=settings.model_ref("nl_housing_arima"),
        horizon="6",
    )
    assert "6 AS horizon" in sql


def test_render_forecast_boosted_tree(settings):
    sql = render(
        "queries/forecast_boosted_tree.sql",
        settings,
        model_ref=settings.model_ref("nl_housing_boosted_tree"),
        horizon="3",
    )
    assert "GENERATE_ARRAY(1, 3)" in sql


def test_render_missing_template_raises(settings):
    with pytest.raises(FileNotFoundError):
        render("does/not/exist.sql", settings)
