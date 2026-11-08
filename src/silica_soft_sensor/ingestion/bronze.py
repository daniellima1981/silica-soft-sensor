"""Bronze layer: the flotation CSV stored as Delta with values untouched."""

from datetime import UTC, datetime

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

from silica_soft_sensor.ingestion.columns import (
    BRONZE_COLUMNS,
    SOURCE_TO_BRONZE,
    check_source_header,
)

SOURCE_DATE_FORMAT = "yyyy-MM-dd HH:mm:ss"
METADATA_COLUMNS = ("_row_id", "_source_file", "_ingested_at")


def read_source_csv(spark: SparkSession, path: str) -> DataFrame:
    """Read the source CSV with every column as string, plus the file path."""
    df = spark.read.option("header", True).option("inferSchema", False).csv(path)
    check_source_header(df.columns)
    return df.withColumn("_source_file", F.col("_metadata.file_path"))


def add_row_id(df: DataFrame) -> DataFrame:
    """Add _row_id = 0..n-1 following the order of the rows in the file."""
    window = Window.orderBy("_mono_id")
    return (
        df.withColumn("_mono_id", F.monotonically_increasing_id())
        .withColumn("_row_id", (F.row_number().over(window) - 1).cast("long"))
        .drop("_mono_id")
    )


def to_bronze(df: DataFrame, ingested_at: datetime) -> DataFrame:
    """Rename to normalized names, add ingestion time and fix the column order."""
    return (
        df.withColumnsRenamed(SOURCE_TO_BRONZE)
        .withColumn("_ingested_at", F.lit(ingested_at))
        .select("_row_id", *BRONZE_COLUMNS, "_source_file", "_ingested_at")
    )


def validate_bronze(bronze: DataFrame, expected_rows: int | None = None) -> None:
    """Fail if the row count, the date format or the file order is not as expected."""
    rows = bronze.count()
    if expected_rows is not None and rows != expected_rows:
        raise ValueError(f"Expected {expected_rows} rows, got {rows}.")

    checked = bronze.select(
        "_row_id", F.try_to_timestamp("date", F.lit(SOURCE_DATE_FORMAT)).alias("ts")
    ).withColumn("prev_ts", F.lag("ts").over(Window.orderBy("_row_id")))

    unparsed = checked.where(F.col("ts").isNull()).count()
    if unparsed:
        raise ValueError(f"{unparsed} rows have a date that does not parse.")

    out_of_order = checked.where(F.col("ts") < F.col("prev_ts")).count()
    if out_of_order:
        raise ValueError(f"{out_of_order} rows break the chronological file order.")


def write_bronze(bronze: DataFrame, table: str) -> None:
    """Full reload: the source is a static file, so overwrite is idempotent."""
    (
        bronze.write.mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(table)
    )


def run(
    spark: SparkSession,
    source_path: str,
    table: str,
    expected_rows: int | None = None,
) -> None:
    """Read, number, normalize, validate and write the bronze table."""
    raw = add_row_id(read_source_csv(spark, source_path))
    bronze = to_bronze(raw, ingested_at=datetime.now(UTC))
    validate_bronze(bronze, expected_rows)
    write_bronze(bronze, table)
