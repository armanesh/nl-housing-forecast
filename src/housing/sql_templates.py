"""Loads .sql files from the sql/ directory and renders them with settings.

Templates use plain Python str.format placeholders (e.g. {raw_ref}) rather than
a templating engine, since BigQuery SQL and Jinja-style braces for STRUCT/ARRAY
literals collide. Keeping this to str.format with doubled braces where needed
is intentional simplicity, not an oversight.
"""

from __future__ import annotations

from pathlib import Path

from housing.config import Settings

SQL_ROOT = Path(__file__).resolve().parents[2] / "sql"


def _read(relative_path: str) -> str:
    path = SQL_ROOT / relative_path
    if not path.exists():
        raise FileNotFoundError(f"SQL template not found: {path}")
    return path.read_text(encoding="utf-8")


def render(relative_path: str, settings: Settings, **extra: str) -> str:
    """Read a SQL template and substitute {raw_ref}, {features_ref}, model refs, etc."""
    template = _read(relative_path)
    context = {
        "project": settings.project,
        "location": settings.location,
        "dataset_raw": settings.dataset_raw,
        "dataset_features": settings.dataset_features,
        "dataset_models": settings.dataset_models,
        "raw_ref": settings.raw_ref,
        "features_ref": settings.features_ref,
        "raw_table": settings.raw_table,
        "features_table": settings.features_table,
    }
    context.update(extra)
    return template.format(**context)
