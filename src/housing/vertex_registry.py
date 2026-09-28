"""Export a trained BigQuery ML model to Vertex AI Model Registry.

BigQuery ML models can be exported to Cloud Storage in a format Vertex AI can
serve (TensorFlow SavedModel for DNN/boosted-tree models trained with
TRANSFORM, or a portable format via `EXPORT MODEL`). This module wraps the two
steps: EXPORT MODEL to GCS, then Vertex AI Model.upload pointing at that GCS
path. It is deliberately optional -- `housing register` is the only command
that touches this module, so the rest of the pipeline works without the
aiplatform SDK installed.
"""

from __future__ import annotations

from housing.config import Settings


def export_model_sql(model_name: str, gcs_uri: str, settings: Settings) -> str:
    model_ref = settings.model_ref(model_name)
    return f"EXPORT MODEL {model_ref}\nOPTIONS (URI = '{gcs_uri}')"


def export_model(model_name: str, gcs_uri: str, settings: Settings) -> None:
    from housing.bq_client import run_ddl

    run_ddl(export_model_sql(model_name, gcs_uri, settings), settings)


def register_in_vertex(
    display_name: str,
    gcs_uri: str,
    settings: Settings,
    serving_container_image_uri: str = (
        "europe-docker.pkg.dev/vertex-ai/prediction/tf2-cpu.2-15:latest"
    ),
):
    """Upload the exported model artifact to Vertex AI Model Registry.

    Returns the created `google.cloud.aiplatform.Model` instance. Import of the
    aiplatform SDK is local to this function so the rest of the package stays
    importable without it installed.
    """
    from google.cloud import aiplatform

    aiplatform.init(project=settings.project, location=_vertex_region(settings.location))
    model = aiplatform.Model.upload(
        display_name=display_name,
        artifact_uri=gcs_uri,
        serving_container_image_uri=serving_container_image_uri,
    )
    return model


def _vertex_region(bq_location: str) -> str:
    """Map a BigQuery location (often 'EU' or 'US') to a concrete Vertex AI region."""
    mapping = {
        "EU": "europe-west4",
        "US": "us-central1",
    }
    return mapping.get(bq_location.upper(), "europe-west4")
