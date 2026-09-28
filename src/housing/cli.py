"""Command-line entry point: `housing <command> [options]`.

Every command that touches BigQuery supports --dry-run, which renders and
prints the SQL it would execute instead of running it. This is what makes the
pipeline reviewable and testable without a GCP project.
"""

from __future__ import annotations

import argparse
import sys

from housing.config import load_settings
from housing.data_gen import GenConfig, generate_rows, write_csv
from housing.sql_templates import render


def _print_sql(sql: str) -> None:
    print("-- DRY RUN: the following SQL would be executed --\n")
    print(sql.strip())
    print()


def cmd_generate_sample(args: argparse.Namespace) -> int:
    config = GenConfig(regions=args.regions, months=args.months, seed=args.seed)
    rows = generate_rows(config)
    out_path = write_csv(rows, args.out)
    print(f"Wrote {len(rows)} rows for {args.regions} regions to {out_path}")
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    settings = load_settings()
    raw_ddl = render("schema/create_raw_table.sql", settings)
    features_ddl = render("schema/create_features_table.sql", settings)
    if args.dry_run:
        _print_sql(raw_ddl)
        _print_sql(features_ddl)
        return 0
    from housing.bq_client import ensure_datasets, run_ddl

    ensure_datasets(settings)
    run_ddl(raw_ddl, settings)
    run_ddl(features_ddl, settings)
    print("Datasets and tables ready.")
    return 0


def cmd_load(args: argparse.Namespace) -> int:
    settings = load_settings()
    if args.dry_run:
        print(f"DRY RUN: would load {args.source} into {settings.raw_ref}")
        return 0
    from housing.bq_client import load_csv

    load_csv(args.source, settings)
    print(f"Loaded {args.source} into {settings.raw_ref}")
    return 0


def cmd_build_features(args: argparse.Namespace) -> int:
    settings = load_settings()
    sql = render("features/build_features.sql", settings, lookback_months=str(args.lookback))
    if args.dry_run:
        _print_sql(sql)
        return 0
    from housing.bq_client import run_ddl

    run_ddl(sql, settings)
    print(f"Feature table refreshed: {settings.features_ref}")
    return 0


MODEL_FILES = {
    "arima": ("models/create_arima_model.sql", "nl_housing_arima"),
    "boosted-tree": ("models/create_boosted_tree_model.sql", "nl_housing_boosted_tree"),
}


def cmd_train(args: argparse.Namespace) -> int:
    settings = load_settings()
    if args.model not in MODEL_FILES:
        print(f"Unknown model '{args.model}'. Choose from: {', '.join(MODEL_FILES)}", file=sys.stderr)
        return 1
    sql_file, model_name = MODEL_FILES[args.model]
    sql = render(sql_file, settings, model_ref=settings.model_ref(model_name))
    if args.dry_run:
        _print_sql(sql)
        return 0
    from housing.bq_client import run_ddl

    run_ddl(sql, settings)
    print(f"Trained model {settings.model_ref(model_name)}")
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    settings = load_settings()
    sql = render(
        "queries/evaluate_models.sql",
        settings,
        arima_ref=settings.model_ref("nl_housing_arima"),
        boosted_tree_ref=settings.model_ref("nl_housing_boosted_tree"),
    )
    if args.dry_run:
        _print_sql(sql)
        return 0
    from housing.bq_client import query_to_dataframe

    df = query_to_dataframe(sql, settings)
    print(df.to_string(index=False))
    return 0


def cmd_predict(args: argparse.Namespace) -> int:
    settings = load_settings()
    model_name = "nl_housing_arima" if args.model == "arima" else "nl_housing_boosted_tree"
    template = (
        "queries/forecast_arima.sql" if args.model == "arima" else "queries/forecast_boosted_tree.sql"
    )
    sql = render(
        template,
        settings,
        model_ref=settings.model_ref(model_name),
        horizon=str(args.horizon),
    )
    if args.dry_run:
        _print_sql(sql)
        return 0
    from housing.bq_client import query_to_dataframe

    df = query_to_dataframe(sql, settings)
    if args.out:
        df.to_csv(args.out, index=False)
        print(f"Wrote forecast to {args.out}")
    else:
        print(df.to_string(index=False))
    return 0


def cmd_register(args: argparse.Namespace) -> int:
    settings = load_settings()
    model_name = "nl_housing_boosted_tree" if args.model == "boosted-tree" else "nl_housing_arima"
    from housing.vertex_registry import export_model_sql

    sql = export_model_sql(model_name, args.gcs_uri, settings)
    if args.dry_run:
        _print_sql(sql)
        print(f"DRY RUN: would then call aiplatform.Model.upload(display_name={args.display_name!r}, "
              f"artifact_uri={args.gcs_uri!r})")
        return 0
    from housing.vertex_registry import export_model, register_in_vertex

    export_model(model_name, args.gcs_uri, settings)
    model = register_in_vertex(args.display_name, args.gcs_uri, settings)
    print(f"Registered Vertex AI model: {model.resource_name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="housing", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("generate-sample", help="Generate a synthetic CBS-style CSV")
    p.add_argument("--out", default="data/sample/regional_price_index.csv")
    p.add_argument("--regions", type=int, default=12)
    p.add_argument("--months", type=int, default=96)
    p.add_argument("--seed", type=int, default=42)
    p.set_defaults(func=cmd_generate_sample)

    p = sub.add_parser("init", help="Create BigQuery datasets and tables")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("load", help="Load a CSV into the raw BigQuery table")
    p.add_argument("--source", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_load)

    p = sub.add_parser("build-features", help="Run the feature engineering SQL")
    p.add_argument("--lookback", type=int, default=12, help="Months of lag features to build")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_build_features)

    p = sub.add_parser("train", help="Train a BigQuery ML model")
    p.add_argument("--model", choices=list(MODEL_FILES), required=True)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_train)

    p = sub.add_parser("evaluate", help="Run ML.EVALUATE for both models side by side")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_evaluate)

    p = sub.add_parser("predict", help="Forecast future prices with a trained model")
    p.add_argument("--model", choices=["arima", "boosted-tree"], default="arima")
    p.add_argument("--horizon", type=int, default=6, help="Months ahead to forecast")
    p.add_argument("--out", default=None, help="Optional CSV path to write results to")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_predict)

    p = sub.add_parser("register", help="Export a model to Vertex AI Model Registry")
    p.add_argument("--model", choices=["arima", "boosted-tree"], default="boosted-tree")
    p.add_argument("--gcs-uri", default="gs://CHANGE-ME-bucket/nl-housing-forecast/boosted-tree/")
    p.add_argument("--display-name", default="nl-housing-boosted-tree")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_register)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
