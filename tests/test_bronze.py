from datetime import datetime

import pytest
from pyspark.sql import DataFrame, SparkSession

from silica_soft_sensor.ingestion.bronze import add_row_id, to_bronze, validate_bronze
from silica_soft_sensor.ingestion.columns import BRONZE_COLUMNS, SOURCE_COLUMNS

pytestmark = pytest.mark.spark

ORDERED_DATES = ["2017-03-10 01:00:00", "2017-03-10 01:00:00", "2017-03-10 02:00:00"]


def _bronze_df(spark: SparkSession, dates: list[str]) -> DataFrame:
    """Source-shaped rows (all strings, comma decimals) run through the bronze steps."""
    rows = [(d, *["1,0"] * (len(SOURCE_COLUMNS) - 1), "file.csv") for d in dates]
    source = spark.createDataFrame(rows, schema=[*SOURCE_COLUMNS, "_source_file"])
    return to_bronze(add_row_id(source), ingested_at=datetime(2026, 11, 7))


def test_row_id_is_sequential_from_zero(spark: SparkSession) -> None:
    rows = _bronze_df(spark, ORDERED_DATES).orderBy("_row_id").collect()
    assert [r["_row_id"] for r in rows] == [0, 1, 2]


def test_bronze_column_order(spark: SparkSession) -> None:
    expected = ["_row_id", *BRONZE_COLUMNS, "_source_file", "_ingested_at"]
    assert _bronze_df(spark, ORDERED_DATES).columns == expected


def test_values_are_kept_as_strings(spark: SparkSession) -> None:
    row = _bronze_df(spark, ORDERED_DATES).first()
    assert row is not None
    assert row["pct_silica_concentrate"] == "1,0"


def test_validate_accepts_ordered_file(spark: SparkSession) -> None:
    validate_bronze(_bronze_df(spark, ORDERED_DATES), expected_rows=3)


def test_validate_rejects_wrong_row_count(spark: SparkSession) -> None:
    with pytest.raises(ValueError, match="Expected 4 rows"):
        validate_bronze(_bronze_df(spark, ORDERED_DATES), expected_rows=4)


def test_validate_rejects_out_of_order_file(spark: SparkSession) -> None:
    dates = ["2017-03-10 02:00:00", "2017-03-10 01:00:00"]
    with pytest.raises(ValueError, match="chronological"):
        validate_bronze(_bronze_df(spark, dates))


def test_validate_rejects_unparsable_date(spark: SparkSession) -> None:
    with pytest.raises(ValueError, match="does not parse"):
        validate_bronze(_bronze_df(spark, ["10/03/2017 01:00"]))
