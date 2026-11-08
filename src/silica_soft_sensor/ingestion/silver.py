"""Silver layer: typed, quality-flagged process and lab tables (see ADR 0002)."""

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as F

DATE_COL = "date"
TS_COL = "ts"
TS_FORMAT = "yyyy-MM-dd HH:mm:ss"
ROW_ID_COL = "_row_id"
BRONZE_METADATA = (ROW_ID_COL, "_source_file", "_ingested_at")


def value_columns(df: DataFrame) -> list[str]:
    """Return the measurement columns (everything but the date and metadata)."""
    return [c for c in df.columns if c != DATE_COL and c not in BRONZE_METADATA]


def parse_decimal_comma(col_name: str) -> Column:
    """Parse a decimal-comma string ("3019,53") into a double; invalid -> null."""
    return (
        F.regexp_replace(F.col(col_name), ",", ".").try_cast("double").alias(col_name)
    )


def to_typed(bronze: DataFrame) -> DataFrame:
    """Convert the all-text bronze table into typed columns.

    The source timestamp is plant wall-clock time with no time zone, so it is
    stored as TIMESTAMP_NTZ to avoid any shift by the session time zone.
    """
    return bronze.select(
        F.col(ROW_ID_COL),
        F.to_timestamp_ntz(F.col(DATE_COL), F.lit(TS_FORMAT)).alias(TS_COL),
        *[parse_decimal_comma(c) for c in value_columns(bronze)],
    )
