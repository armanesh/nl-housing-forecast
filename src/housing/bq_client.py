"""Thin wrapper around google-cloud-bigquery.

Kept separate from cli.py so it's the only module that imports the real
BigQuery SDK, and so tests can monkeypatch `get_client` without pulling in
network code.
"""

from __future__ import annotations

from pathlib import Path

from housing.config import Settings


def get_client(settings: Settings):
    from google.cloud import bigquery

    return bigquery.Client(project=settings.project, location=settings.location)


def ensure_datasets(settings: Settings) -> None:
    from google.api_core.exceptions import NotFound
    from google.cloud import bigquery

    client = get_client(settings)
    for dataset_id in (settings.dataset_raw, settings.dataset_features, settings.dataset_models):
        ref = bigquery.DatasetReference(settings.project, dataset_id)
        try:
            client.get_dataset(ref)
        except NotFound:
            dataset = bigquery.Dataset(ref)
            dataset.location = settings.location
            client.create_dataset(dataset, exists_ok=True)


def run_ddl(sql: str, settings: Settings) -> None:
    client = get_client(settings)
    job = client.query(sql)
    job.result()


def load_csv(csv_path: str | Path, settings: Settings) -> None:
    from google.cloud import bigquery

    client = get_client(settings)
    table_id = f"{settings.project}.{settings.dataset_raw}.{settings.raw_table}"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=False,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        schema=[
            bigquery.SchemaField("region", "STRING"),
            bigquery.SchemaField("month", "DATE"),
            bigquery.SchemaField("avg_sale_price_eur", "FLOAT64"),
            bigquery.SchemaField("mortgage_rate_pct", "FLOAT64"),
            bigquery.SchemaField("new_build_permits", "INT64"),
        ],
    )
    with open(csv_path, "rb") as fh:
        job = client.load_table_from_file(fh, table_id, job_config=job_config)
    job.result()


def query_to_dataframe(sql: str, settings: Settings):
    client = get_client(settings)
    return client.query(sql).to_dataframe()
