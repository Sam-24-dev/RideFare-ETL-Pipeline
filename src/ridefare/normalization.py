"""Normalization helpers for dataframe ingestion."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping

import polars as pl


def normalize_column_name(name: str) -> str:
    """Normalize a raw column header into lowercase snake_case."""

    normalized = re.sub(r"[^0-9a-zA-Z]+", "_", name.strip())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized.lower()


def normalize_column_names(frame: pl.DataFrame) -> pl.DataFrame:
    """Return a dataframe with normalized column headers."""

    rename_map = {column: normalize_column_name(column) for column in frame.columns}
    return frame.rename(rename_map)


def select_columns(frame: pl.DataFrame, ordered_columns: Iterable[str]) -> pl.DataFrame:
    """Select columns in a stable order."""

    return frame.select(list(ordered_columns))


def cast_columns(frame: pl.DataFrame, column_types: Mapping[str, pl.DataType]) -> pl.DataFrame:
    """Cast known columns with non-strict conversion so bad values become nulls."""

    expressions = [
        pl.col(column).cast(dtype, strict=False).alias(column)
        for column, dtype in column_types.items()
    ]
    return frame.with_columns(expressions)
