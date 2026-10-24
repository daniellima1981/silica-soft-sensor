from importlib.metadata import version

from silica_soft_sensor import __version__


def test_version_matches_package_metadata() -> None:
    assert __version__ == version("silica-soft-sensor")
