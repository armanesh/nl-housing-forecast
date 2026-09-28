"""Synthetic generator for a CBS-style regional house price dataset.

Produces monthly rows per region with:
- a long-run upward trend (Dutch house prices have trended up for most of the
  last decade, with a dip around 2022-2023 when mortgage rates rose)
- yearly seasonality (spring/summer are stronger selling months)
- region-level offsets (Amsterdam/Utrecht priced well above Groningen/Limburg)
- two exogenous regressors: mortgage_rate_pct and new_build_permits
- Gaussian noise, so no downstream model fits perfectly (that would be a smell
  in a real portfolio piece)
"""

from __future__ import annotations

import csv
import math
import random
from dataclasses import dataclass
from datetime import date
from pathlib import Path

REGIONS = [
    ("Amsterdam", 1.35),
    ("Utrecht", 1.22),
    ("Rotterdam", 1.05),
    ("Den Haag", 1.10),
    ("Eindhoven", 1.00),
    ("Groningen", 0.78),
    ("Tilburg", 0.85),
    ("Nijmegen", 0.92),
    ("Breda", 0.95),
    ("Maastricht", 0.88),
    ("Arnhem", 0.90),
    ("Almere", 0.93),
]


@dataclass
class GenConfig:
    regions: int = 12
    months: int = 96
    start_year: int = 2017
    start_month: int = 1
    base_price: float = 260_000.0
    monthly_trend: float = 0.0035
    seasonal_amplitude: float = 0.015
    noise_std: float = 0.01
    seed: int = 42


def _month_sequence(start_year: int, start_month: int, n: int):
    year, month = start_year, start_month
    for _ in range(n):
        yield date(year, month, 1)
        month += 1
        if month > 12:
            month = 1
            year += 1


def _mortgage_rate(month_index: int) -> float:
    """A rough shape: low ~2017-2021, rising through 2022-2023, easing after."""
    base = 2.3
    rise_start, rise_end = 60, 78  # months into the series
    if month_index < rise_start:
        return round(base + 0.15 * math.sin(month_index / 11.0), 2)
    if month_index < rise_end:
        progress = (month_index - rise_start) / (rise_end - rise_start)
        return round(base + progress * 2.8, 2)
    return round(base + 2.8 - 0.02 * (month_index - rise_end), 2)


def _permits(month_index: int, region_factor: float, rng: random.Random) -> int:
    seasonal = 1.0 + 0.2 * math.sin((month_index % 12) / 12.0 * 2 * math.pi)
    value = 180 * region_factor * seasonal * rng.uniform(0.85, 1.15)
    return max(5, round(value))


def generate_rows(config: GenConfig):
    rng = random.Random(config.seed)
    regions = REGIONS[: config.regions]
    rows = []
    for region_name, region_factor in regions:
        for month_index, month_date in enumerate(
            _month_sequence(config.start_year, config.start_month, config.months)
        ):
            trend = (1 + config.monthly_trend) ** month_index
            seasonal = 1 + config.seasonal_amplitude * math.sin(
                (month_date.month - 3) / 12.0 * 2 * math.pi
            )
            mortgage = _mortgage_rate(month_index)
            # higher mortgage rate softens price growth, with a lag baked in via
            # the trend shape itself rather than a separate lag term here
            rate_drag = 1 - max(0.0, (mortgage - 3.0)) * 0.01
            noise = rng.gauss(1.0, config.noise_std)
            price = config.base_price * region_factor * trend * seasonal * rate_drag * noise
            permits = _permits(month_index, region_factor, rng)
            rows.append(
                {
                    "region": region_name,
                    "month": month_date.isoformat(),
                    "avg_sale_price_eur": round(price, 2),
                    "mortgage_rate_pct": mortgage,
                    "new_build_permits": permits,
                }
            )
    return rows


def write_csv(rows, out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["region", "month", "avg_sale_price_eur", "mortgage_rate_pct", "new_build_permits"]
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return out_path
