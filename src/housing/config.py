"""Central configuration, read from environment variables.

Every value has a sane default so the package can be imported and its SQL
templates rendered (in --dry-run mode) without any environment set up at all.
This is what lets the test suite and CI run with zero GCP credentials.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    project: str
    location: str
    dataset_raw: str
    dataset_features: str
    dataset_models: str
    raw_table: str = "regional_price_index"
    features_table: str = "monthly_features"

    @property
    def raw_ref(self) -> str:
        return f"`{self.project}.{self.dataset_raw}.{self.raw_table}`"

    @property
    def features_ref(self) -> str:
        return f"`{self.project}.{self.dataset_features}.{self.features_table}`"

    def model_ref(self, model_name: str) -> str:
        return f"`{self.project}.{self.dataset_models}.{model_name}`"


def load_settings() -> Settings:
    return Settings(
        project=os.environ.get("GOOGLE_CLOUD_PROJECT", "demo-project"),
        location=os.environ.get("BQ_LOCATION", "EU"),
        dataset_raw=os.environ.get("BQ_DATASET_RAW", "housing_raw"),
        dataset_features=os.environ.get("BQ_DATASET_FEATURES", "housing_features"),
        dataset_models=os.environ.get("BQ_DATASET_MODELS", "housing_models"),
    )
