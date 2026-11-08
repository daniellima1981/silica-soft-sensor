from datetime import datetime

import pytest
from pyspark.sql import DataFrame, SparkSession

from silica_soft_sensor.ingestion.silver import to_typed, value_columns

pytestmark = pytest.mark.spark

BRONZE_SCHEMA = (
    "date string, starch_flow string, ore_pulp_ph string, "
    "_row_id long, _source_file string, _ingested_at timestamp"
)


def _bronze(spark: SparkSession, rows: list[tuple[object, ...]]) -> DataFrame:
    return spark.createDataFrame(rows, BRONZE_SCHEMA)


def test_value_columns_excludes_date_and_metadata(spark: SparkSession) -> None:
    df = _bronze(spark, [])
    assert value_columns(df) == ["starch_flow", "ore_pulp_ph"]


def test_to_typed_parses_decimal_comma_and_timestamp(spark: SparkSession) -> None:
    df = _bronze(
        spark,
        [("2017-03-10 01:00:00", "3019,53", "10,0802", 0, "f.csv", datetime.now())],
    )
    row = to_typed(df).first()
    assert row is not None
    assert row["ts"] == datetime(2017, 3, 10, 1, 0, 0)
    assert row["starch_flow"] == pytest.approx(3019.53)
    assert row["ore_pulp_ph"] == pytest.approx(10.0802)
    assert row["_row_id"] == 0


def test_to_typed_turns_invalid_number_into_null(spark: SparkSession) -> None:
    df = _bronze(
        spark,
        [("2017-03-10 01:00:00", "abc", "10,0", 0, "f.csv", datetime.now())],
    )
    row = to_typed(df).first()
    assert row is not None
    assert row["starch_flow"] is None


def test_to_typed_drops_bronze_only_metadata(spark: SparkSession) -> None:
    df = _bronze(spark, [])
    assert to_typed(df).columns == ["_row_id", "ts", "starch_flow", "ore_pulp_ph"]
