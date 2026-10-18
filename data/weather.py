"""Load hourly weather covariates from ETH metadata."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = PROJECT_ROOT / "datasets" / "eth"
WEATHER_FILENAME = "weather_covariates.csv"


def _find_weather_csv(root: str | Path | None) -> Path:
    """Resolve the weather CSV from a dataset root, project root, or file path."""
    if root is None:
        candidates = [DEFAULT_DATA_ROOT / "meta" / WEATHER_FILENAME]
    else:
        root_path = Path(root).expanduser()
        if not root_path.is_absolute():
            root_path = (Path.cwd() / root_path).resolve()

        if root_path.is_file():
            candidates = [root_path]
        else:
            candidates = [
                root_path / "meta" / WEATHER_FILENAME,  # datasets/eth
                root_path / "datasets" / "eth" / "meta" / WEATHER_FILENAME,  # project root
                root_path / WEATHER_FILENAME,  # meta directory
            ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    checked = "\n".join(f"  - {path}" for path in candidates)
    raise FileNotFoundError(
        f"Không tìm thấy {WEATHER_FILENAME}. Đã kiểm tra:\n{checked}\n"
        "Hãy đặt file tại datasets/eth/meta/weather_covariates.csv."
    )


def load_station(root: str | Path | None = None) -> pd.DataFrame:
    """Load hourly weather data as timestamp, T, and RH.

    Timestamps remain timezone-naive because the CSV does not specify a timezone.
    """
    weather_csv = _find_weather_csv(root)
    weather = pd.read_csv(weather_csv)

    required = {"timestamp", "mean_tmp", "mean_rh"}
    missing = required - set(weather.columns)
    if missing:
        raise ValueError(
            f"{weather_csv} thiếu cột bắt buộc: {sorted(missing)}. "
            f"Các cột hiện có: {list(weather.columns)}"
        )

    # Exclude date-only daily summaries from the hourly weather data.
    timestamp_text = weather["timestamp"].astype("string").str.strip()
    has_time = timestamp_text.str.fullmatch(
        r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}", na=False
    )
    weather = weather.loc[has_time].copy()

    weather = weather.rename(columns={"mean_tmp": "T", "mean_rh": "RH"})
    weather["timestamp"] = pd.to_datetime(
        weather["timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce"
    )
    weather["T"] = pd.to_numeric(weather["T"], errors="coerce")
    weather["RH"] = pd.to_numeric(weather["RH"], errors="coerce")
    weather = weather.dropna(subset=["timestamp"])

    weather = weather[["timestamp", "T", "RH"]]
    weather = weather.sort_values("timestamp").reset_index(drop=True)
    return weather


if __name__ == "__main__":
    df = load_station()
    print("--- ETH WEATHER DATA ---")
    print(f"Path: {DEFAULT_DATA_ROOT / 'meta' / WEATHER_FILENAME}")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"Timestamp range: {df['timestamp'].min()} -> {df['timestamp'].max()}")
    print(f"Missing T: {int(df['T'].isna().sum())}")
    print(f"Missing RH: {int(df['RH'].isna().sum())}")
    print("Note: daily-summary rows without an hourly timestamp are excluded.")
