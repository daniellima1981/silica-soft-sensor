import re

import pytest

from silica_soft_sensor.ingestion.columns import (
    BRONZE_COLUMNS,
    SOURCE_COLUMNS,
    check_source_header,
)


def test_layout_has_24_columns() -> None:
    assert len(SOURCE_COLUMNS) == 24
    assert len(BRONZE_COLUMNS) == 24


def test_bronze_names_are_unique_snake_case() -> None:
    assert len(set(BRONZE_COLUMNS)) == len(BRONZE_COLUMNS)
    assert all(re.fullmatch(r"[a-z][a-z0-9_]*", c) for c in BRONZE_COLUMNS)


def test_expected_header_passes() -> None:
    check_source_header(list(SOURCE_COLUMNS))


def test_missing_column_fails() -> None:
    with pytest.raises(ValueError, match="missing"):
        check_source_header(list(SOURCE_COLUMNS[:-1]))


def test_reordered_header_fails() -> None:
    reordered = [SOURCE_COLUMNS[1], SOURCE_COLUMNS[0], *SOURCE_COLUMNS[2:]]
    with pytest.raises(ValueError, match="order changed"):
        check_source_header(reordered)
