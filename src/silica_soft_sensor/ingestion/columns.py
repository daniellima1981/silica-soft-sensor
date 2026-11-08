"""Mapping between the source CSV header and normalized bronze column names."""

from collections.abc import Sequence
from typing import Final

_FLOTATION_COLUMNS = range(1, 8)

SOURCE_TO_BRONZE: Final[dict[str, str]] = {
    "date": "date",
    "% Iron Feed": "pct_iron_feed",
    "% Silica Feed": "pct_silica_feed",
    "Starch Flow": "starch_flow",
    "Amina Flow": "amine_flow",
    "Ore Pulp Flow": "ore_pulp_flow",
    "Ore Pulp pH": "ore_pulp_ph",
    "Ore Pulp Density": "ore_pulp_density",
    **{
        f"Flotation Column {i:02d} Air Flow": f"air_flow_col_{i:02d}"
        for i in _FLOTATION_COLUMNS
    },
    **{
        f"Flotation Column {i:02d} Level": f"level_col_{i:02d}"
        for i in _FLOTATION_COLUMNS
    },
    "% Iron Concentrate": "pct_iron_concentrate",
    "% Silica Concentrate": "pct_silica_concentrate",
}

SOURCE_COLUMNS: Final[tuple[str, ...]] = tuple(SOURCE_TO_BRONZE)
BRONZE_COLUMNS: Final[tuple[str, ...]] = tuple(SOURCE_TO_BRONZE.values())


def check_source_header(header: Sequence[str]) -> None:
    """Raise ValueError if the CSV header differs from the expected source layout."""
    if tuple(header) == SOURCE_COLUMNS:
        return
    missing = [c for c in SOURCE_COLUMNS if c not in header]
    unexpected = [c for c in header if c not in SOURCE_TO_BRONZE]
    raise ValueError(
        "Unexpected source header "
        f"(missing: {missing}; unexpected: {unexpected}; "
        "if both are empty, the column order changed)."
    )
