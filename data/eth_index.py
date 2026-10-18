"""Build an index for the ETH leaf-image dataset."""

from __future__ import annotations

import hashlib
import warnings
from pathlib import Path
from typing import Optional

import pandas as pd

DEFAULT_DATA_ROOT = Path("datasets/eth")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _select_leaf_rds(root: Path) -> Path:
    """Find one data_leaf.rds without concatenating copies."""
    candidates = [
        root / "processed" / "res" / "dataset_2023" / "data_leaf.rds",
        root / "processed" / "res" / "dataset_2024" / "data_leaf.rds",
    ]
    existing = [path for path in candidates if path.is_file()]
    if not existing:
        raise FileNotFoundError(
            "Không tìm thấy data_leaf.rds. Cần có file tại một trong các vị trí: "
            "datasets/eth/processed/res/dataset_2023/data_leaf.rds hoặc "
            "datasets/eth/processed/res/dataset_2024/data_leaf.rds."
        )

    if len(existing) > 1 and _sha256(existing[0]) != _sha256(existing[1]):
        warnings.warn(
            "Hai file data_leaf.rds trong dataset_2023 và dataset_2024 khác nhau. "
            "Để tránh đếm trùng, hiện chỉ đọc bản dataset_2023; cần kiểm tra nguồn "
            "dữ liệu trước khi gộp hai bản.",
            RuntimeWarning,
            stacklevel=2,
        )
    return existing[0]


def _read_leaf_table(root: Path) -> pd.DataFrame:
    rds_path = _select_leaf_rds(root)
    try:
        import pyreadr
    except ImportError as exc:
        raise ImportError(
            "Để Python đọc file .rds, hãy mở Terminal trong VS Code (không phải R Console) "
            "và chạy: python -m pip install pyreadr"
        ) from exc

    result = pyreadr.read_r(str(rds_path))
    if not result:
        raise ValueError(f"Không đọc được bảng dữ liệu từ {rds_path}")
    table = next(iter(result.values()))
    if not isinstance(table, pd.DataFrame):
        raise TypeError(f"Nội dung {rds_path} không phải bảng data.frame/tibble")
    return table.copy()


def _parse_naive_datetime(values: pd.Series) -> pd.Series:
    """Parse mixed date/timestamp values into naive datetimes."""
    text = values.astype("string").str.strip()
    text = text.str.replace(r"\s+UTC$", "", regex=True)
    text = text.str.replace(r"(?:\+00:00|Z)$", "", regex=True)

    date_only = text.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)
    parsed = pd.Series(pd.NaT, index=values.index, dtype="datetime64[ns]")
    timed = ~date_only & text.notna()
    if timed.any():
        parsed.loc[timed] = pd.to_datetime(text.loc[timed], errors="coerce")
    if date_only.any():
        parsed.loc[date_only] = pd.to_datetime(
            text.loc[date_only], format="%Y-%m-%d", errors="coerce"
        )
    return parsed


def _make_image_path(root: Path, leaf_uid: object, file_id: object) -> object:
    """Map a file ID to its aligned JPG path."""
    if pd.isna(leaf_uid) or pd.isna(file_id):
        return pd.NA

    leaf_folder = str(leaf_uid).strip()
    file_name = Path(str(file_id).strip()).name
    stem = Path(file_name).stem
    if not stem:
        return pd.NA

    # Filename mapping was verified on the inspected sample.
    image_name = f"{stem}.JPG"
    path = root / "processed" / "reg" / leaf_folder / "crop" / image_name
    return path.as_posix()


def _make_mask_path(root: Path, leaf_uid: object, file_id: object) -> object:
    """Map an observation to its aligned piecewise PNG mask."""
    if pd.isna(leaf_uid) or pd.isna(file_id):
        return pd.NA

    leaf_folder = str(leaf_uid).strip()
    file_name = Path(str(file_id).strip()).name
    mask_name = f"{Path(file_name).stem}.png"
    path = (
        root / "processed" / "reg" / leaf_folder
        / "mask_aligned" / "piecewise" / mask_name
    )
    return path.as_posix()


def build_index(root: str | Path = DEFAULT_DATA_ROOT) -> pd.DataFrame:
    """Build one index row per leaf observation from real RDS metadata.

    Disease labels remain missing until verified; damage_ratio is not disease severity.
    """
    data_root = Path(root)
    leaf = _read_leaf_table(data_root)

    required_leaf_columns = {"plot_UID", "leaf_UID", "timestamp", "file_id"}
    missing_leaf = required_leaf_columns - set(leaf.columns)
    if missing_leaf:
        raise ValueError(
            f"data_leaf.rds thiếu cột bắt buộc: {sorted(missing_leaf)}. "
            "Kiểm tra đúng file data_leaf.rds đã chọn."
        )

    design_path = data_root / "meta" / "experimental_design.csv"
    if not design_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy metadata: {design_path}")
    design = pd.read_csv(design_path)
    if "plot_UID" not in design.columns:
        raise ValueError("experimental_design.csv thiếu cột plot_UID")
    if design["plot_UID"].duplicated().any():
        raise ValueError("experimental_design.csv có plot_UID trùng; chưa thể ghép an toàn")

    meta_cols = [
        col
        for col in ["plot_UID", "plot", "genotype_name", "harvest_year", "Year"]
        if col in design.columns
    ]
    index = leaf.merge(
        design[meta_cols],
        on="plot_UID",
        how="left",
        validate="many_to_one",
        suffixes=("", "_design"),
    )

    heading_path = data_root / "meta" / "heading_date.csv"
    if heading_path.is_file():
        heading = pd.read_csv(heading_path)
        if {"plot_UID", "hd"}.issubset(heading.columns):
            if heading["plot_UID"].duplicated().any():
                raise ValueError("heading_date.csv có plot_UID trùng; chưa thể ghép an toàn")
            index = index.merge(
                heading[["plot_UID", "hd"]].rename(columns={"hd": "heading_date"}),
                on="plot_UID",
                how="left",
                validate="many_to_one",
            )
            index["heading_date"] = pd.to_datetime(index["heading_date"], errors="coerce")

    # The timestamps shown in the R table are explicitly UTC.
    parsed_time = _parse_naive_datetime(index["timestamp"])
    index["date_time"] = parsed_time.dt.tz_localize("UTC")

    index["leaf_id"] = index["leaf_UID"].astype("string")
    index["sequence_id"] = index["leaf_UID"].astype("string")
    index["genotype"] = (
        index["genotype_name"].astype("string")
        if "genotype_name" in index.columns
        else pd.Series(pd.NA, index=index.index, dtype="string")
    )

    if "harvest_year" in index.columns:
        season = index["harvest_year"]
    elif "Year" in index.columns:
        season = index["Year"]
    else:
        season = pd.Series(pd.NA, index=index.index)
    season_numeric = pd.to_numeric(season, errors="coerce")
    season_text = season_numeric.astype("Int64").astype("string")
    season_text = season_text.where(season_numeric.notna(), season.astype("string"))
    year_fallback = index["date_time"].dt.year.astype("Int64").astype("string")
    index["season"] = season_text.fillna(year_fallback)

    index["image_path"] = [
        _make_image_path(data_root, leaf_uid, file_id)
        for leaf_uid, file_id in zip(index["leaf_UID"], index["file_id"])
    ]
    index["image_exists"] = index["image_path"].map(
        lambda value: bool(Path(str(value)).is_file()) if pd.notna(value) else False
    )

    # Verified on 14 local image/mask pairs only; the full dataset is not yet checked.
    index["mask_path"] = [
        _make_mask_path(data_root, leaf_uid, file_id)
        for leaf_uid, file_id in zip(index["leaf_UID"], index["file_id"])
    ]
    index["mask_exists"] = index["mask_path"].map(
        lambda value: bool(Path(str(value)).is_file()) if pd.notna(value) else False
    )

    # Keep disease labels unfilled until an authoritative label mapping is verified.
    index["severity"] = pd.Series(pd.NA, index=index.index, dtype="Float64")
    index["pathogens"] = pd.Series(pd.NA, index=index.index, dtype="string")

    if {"la_damaged", "la_tot"}.issubset(index.columns):
        damaged = pd.to_numeric(index["la_damaged"], errors="coerce")
        total = pd.to_numeric(index["la_tot"], errors="coerce")
        index["damage_ratio"] = (damaged / total).where(total > 0)
    else:
        index["damage_ratio"] = pd.Series(float("nan"), index=index.index)

    # Select the index fields and real measurements used for auditing.
    leading = [
        "leaf_id", "sequence_id", "plot_UID", "plot", "genotype", "season",
        "date_time", "file_id", "image_path", "image_exists", "mask_path",
        "mask_exists", "severity", "pathogens", "heading_date", "damage_ratio",
    ]
    measurement_cols = [
        "leaf_nr", "la_tot", "la_damaged", "la_healthy", "la_insect",
        "n_lesion", "n_pycn", "n_rust", "pycn_density", "rust_density",
    ]
    output_cols = [col for col in leading + measurement_cols if col in index.columns]
    output = index[output_cols].copy()
    output = output.sort_values(["sequence_id", "date_time"], na_position="last").reset_index(drop=True)
    return output


def count_sequences(index: pd.DataFrame) -> dict:
    """Count actual unique leaf sequences and unique image paths; never hard-code totals."""
    required = {"sequence_id", "image_path"}
    missing = required - set(index.columns)
    if missing:
        raise ValueError(f"Index thiếu cột bắt buộc: {sorted(missing)}")
    return {
        "total_sequences": int(index["sequence_id"].nunique(dropna=True)),
        "total_images": int(index["image_path"].dropna().nunique()),
    }


def audit_eth_dataset(
    data_dir: str | Path = DEFAULT_DATA_ROOT,
    min_weather_coverage_pct: Optional[float] = None,
    min_sequences: int = 100,
) -> dict:
    """Report counts and weather timestamp coverage.

    K2 pass/fail requires an explicitly supplied coverage threshold.
    """
    data_root = Path(data_dir)
    index = build_index(data_root)
    counts = count_sequences(index)

    weather_path = data_root / "meta" / "weather_covariates.csv"
    coverage_pct: Optional[float] = None
    if weather_path.is_file() and not index.empty:
        weather = pd.read_csv(weather_path)
        if "timestamp" not in weather.columns:
            raise ValueError("weather_covariates.csv thiếu cột timestamp")
        weather_times = _parse_naive_datetime(weather["timestamp"]).dropna()
        observation_times = pd.to_datetime(index["date_time"], errors="coerce", utc=True)
        observation_times = observation_times.dt.tz_convert(None)
        observation_hours = observation_times.dt.floor("h")
        weather_hours = set(weather_times.dt.floor("h"))
        valid_obs = observation_hours.notna()
        if valid_obs.any():
            covered = observation_hours.loc[valid_obs].isin(weather_hours)
            coverage_pct = round(float(covered.mean() * 100), 2)

    return {
        "total_sequences": counts["total_sequences"],
        "total_images": counts["total_images"],
        "weather_coverage_pct": coverage_pct,
        "k2_weather_met": (
            None
            if coverage_pct is None or min_weather_coverage_pct is None
            else coverage_pct >= min_weather_coverage_pct
        ),
        "k2_sequences_met": counts["total_sequences"] >= min_sequences,
    }


if __name__ == "__main__":
    data = build_index()
    counts = count_sequences(data)
    print("--- ETH DATASET INDEX ---")
    print(f"Index shape: {data.shape}")
    print(f"Columns: {list(data.columns)}")
    print(f"Counts: {counts}")
    print(f"Local aligned JPGs found: {int(data['image_exists'].sum())} / {len(data)}")
    print(f"Local piecewise masks found: {int(data['mask_exists'].sum())} / {len(data)}")
    print("Note: severity and pathogens are left missing until authoritative labels are verified.")
