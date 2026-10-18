import pandas as pd
import pytest

from data.eth_index import build_index, count_sequences
from data.weather import load_station


@pytest.fixture(scope="module")
def index_df():
    """Build the index once from the real local ETH dataset for this test module."""
    return build_index()


def test_build_index(index_df):
    """The real index should be non-empty and expose the required schema."""
    assert not index_df.empty

    expected_cols = [
        "leaf_id",
        "sequence_id",
        "plot",
        "genotype",
        "season",
        "date_time",
        "image_path",
        "mask_path",
        "severity",
        "pathogens",
    ]
    for col in expected_cols:
        assert col in index_df.columns, f"Missing required column: {col}"

    assert index_df["leaf_id"].notna().any()
    assert index_df["sequence_id"].notna().any()
    assert index_df["date_time"].notna().any()

    # Image paths are derived from the real file_id. The raw JPGs may not yet
    # be downloaded locally, so do not require image_exists to be True.
    image_paths = index_df["image_path"].dropna().astype(str)
    assert not image_paths.empty
    assert image_paths.str.endswith(".JPG").all()


def test_count_sequences_counts_unique_ids_and_paths():
    """Test count semantics on a small controlled example, not hard-coded dataset totals."""
    sample = pd.DataFrame(
        {
            "sequence_id": ["leaf_A", "leaf_A", "leaf_B", None],
            "image_path": ["a.JPG", "a.JPG", "b.JPG", pd.NA],
        }
    )

    counts = count_sequences(sample)

    assert counts["total_sequences"] == 2
    assert counts["total_images"] == 2


def test_count_sequences_matches_real_index(index_df):
    """Reported counts should reflect the index currently built from the dataset."""
    counts = count_sequences(index_df)

    assert counts["total_sequences"] == index_df["sequence_id"].nunique(dropna=True)
    assert counts["total_images"] == index_df["image_path"].dropna().nunique()


def test_load_station():
    """Weather loader should read the downloaded metadata CSV and standardize columns."""
    df_weather = load_station()

    assert not df_weather.empty
    assert list(df_weather.columns) == ["timestamp", "T", "RH"]
    assert df_weather["timestamp"].notna().all()
    assert pd.api.types.is_datetime64_any_dtype(df_weather["timestamp"])
    assert pd.api.types.is_numeric_dtype(df_weather["T"])
    assert pd.api.types.is_numeric_dtype(df_weather["RH"])
