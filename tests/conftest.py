import os
from collections.abc import Iterator

import pytest
from databricks.connect import DatabricksSession
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark() -> Iterator[SparkSession]:
    """One serverless Spark session shared by all tests marked 'spark'."""
    profile = os.environ.get("DATABRICKS_CONFIG_PROFILE", "silica")
    yield DatabricksSession.builder.profile(profile).serverless().getOrCreate()
