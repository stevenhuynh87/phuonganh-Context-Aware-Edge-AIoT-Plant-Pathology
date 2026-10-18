# ETH Dataset Audit — S01

**Project:** Context-Aware Edge AIoT Plant Pathology: Fusing Morphological Vision with Microclimatic Environmental Dynamics
**Audit snapshot:** 2026-10-18
**Status:** Plan B in use; data/code checks partly verified; K2 pathogen-count condition unresolved; K3 not met on the current local machine.

## 1. Scope and download decision

The full ETH dataset was **not** downloaded locally. The local `datasets/eth/` directory contains 39 files totalling approximately **0.187 GB** at the time of measurement. The C: drive had approximately **2.23 GB free** in the latest check. Online inventory previously observed in the ETH repository showed approximately 223.9 GB under `raw/`, 88.4 GB under `processed/reg/`, and 63.3 GB under `processed/ts/` (remote folder-size listings, not local usage).

**Plan B:** retain metadata CSVs and RDS tables, and use one selectively available aligned image/mask sample for smoke testing. Do not attempt a full raw-data download or regenerate the entire processing pipeline on this machine without more storage and an appropriate compute environment.

## 2. Locally inspected data

### Metadata CSVs

- `meta/experimental_design.csv`: 544 rows × 16 columns; includes `plot_UID`, `treatment`, `genotype_name`, `harvest_year`, `fungicide_treatment`, and `inoculation_treatment`. It has treatment/genotype/year metadata but no direct pathogen-label column.
- `meta/heading_date.csv`: 336 rows × 2 columns; 336 unique `plot_UID`; 19 missing heading-date values in the earlier inspection.
- `meta/weather_covariates.csv`: 12,073 rows × 3 columns. The loader uses 11,570 timestamped hourly records and excludes 503 date-only summary rows. No missing values were observed in hourly `T` or `RH`. Timestamp range observed: 2022-11-08 15:00 to 2024-07-19 14:00. The timezone for the weather timestamps is not explicitly established by the CSV.

### RDS tables

- `data_leaf.rds`: 11,768 rows × 25 variables; 1,029 unique `leaf_UID`; 11,768 unique `file_id` values. The index uses `leaf_UID` as `sequence_id`.
- `data_lesions.rds`: 209,892 rows × 39 variables; 1,024 unique `leaf_UID`, 60,207 unique `lesion_UID`, and 9,741 unique `file_id` values. Many lesion morphology/density fields are missing for some rows. No direct categorical pathogen/disease-label column was found in the inspected schema.
- The 2023 and 2024 copies of the leaf and lesion RDS files were previously compared in R and `identical(...)` returned `TRUE`; this establishes that the loaded R objects match, but should not be described as a byte-level comparison unless file hashes were compared. Do not concatenate these copies without evidence that they are distinct data partitions.

## 3. Index and local image/mask verification

Latest command:

```powershell
python -m data.eth_index
```

Observed result:

- Index shape: **11,768 rows × 26 columns**.
- Unique sequences: **1,029**.
- Unique indexed image paths / `file_id` rows: **11,768**. These are index references, **not** evidence that 11,768 image files are physically present locally.
- Local aligned JPGs found by index: **14 / 11,768**.
- Local piecewise masks found by index: **14 / 11,768**.

For sample `ESWW0070020_1`, 14 crop JPGs and 14 PNG masks were present; all 14 basenames matched, with no unmatched files on either side in this sample. First inspected image size: 8192 × 2048; first inspected mask size: 4999 × 791.

Latest test command:

```powershell
python -m pytest -q
```

Result: **4 passed in 4.25s**.

## 4. Author toolkit smoke test and full pipeline feasibility

Author repository: <https://github.com/and-jonas/sympathique-wheat>

A read-only `LeafDataset` smoke test using the author’s `DatasetTools/LeafImageSeries.py` was run on the sample `ESWW0070020_1`:

- Images loaded: 14.
- Masks loaded: 14/14.
- Result: `TOOLKIT_SMOKE=PASS`, exit code 0.

This verifies that the toolkit loader can read the sample images and masks. It does **not** verify the entire alignment, detection, segmentation, or lesion-tracking pipeline.

A recursive search under the cloned repository found no `.ipynb` notebook. The repository README lists the code workflow in `01_detect.py` through `06_track.py`; its model download link is marked TODO.

The end-to-end pipeline was **not run** because required inputs are missing in the cloned toolkit folder and local machine:

- `01_detect.py` expects `raw/2023`, `raw/2024`, and `models/best.pt`; the raw folders and model file were not present. The test environment also lacks `ultralytics`.
- `02_crop.py` and `03_align_img.py` depend on raw images and generated labels/outputs.
- `04_predict.py` imports the `leaf` package (`leaf-toolkit`), which is not installed in the smoke-test environment; the required `processed/` input tree was not present in the toolkit clone.
- `05_align_msk.py` requires segmentation/detection predictions and registration outputs.
- `06_track.py` expects aligned masks, registered result images, and keypoints under an `Output/` structure that was not present in the toolkit clone.

Do not install the full environment or run these scripts over a full dataset on this machine until storage and model/input availability are resolved. The smoke test is the completed toolkit check for S01; the full pipeline is **blocked**, not passed.

## 5. Sequence-count discrepancy

The paper reports **1,032 image sequences and 12,520 RGB images**. Current local derived counts are **1,029 unique `leaf_UID` sequences** and 11,768 rows/unique `file_id` values in the leaf RDS index. Remote directory inventories previously observed 1,029 folders under `processed/ts/` and 1,031 under `processed/reg/`.

These counts do not match and have not been reconciled. Keep the observed counts as-is; do not hard-code the published total into code or tests. A full reconciliation would require comparing sequence/file identifiers against an authoritative manifest or obtaining clarification from the data authors.

## 6. Symptom markers, treatments, and pathogen-label limitation

The index currently leaves `severity` and `pathogens` missing intentionally because an authoritative sequence-level label mapping has not been verified.

At the observation level (11,768 leaf rows), `n_pycn` and `n_rust` had no missing values; positive observations were 8,988 and 9,996 respectively. Aggregated to 1,029 sequences using the maximum marker value per sequence:

- `n_pycn > 0`: 1,022 sequences.
- `n_rust > 0`: 1,022 sequences.
- Both markers positive: 1,021 sequences.
- Neither marker positive: 6 sequences (derived from these counts).

These are **symptom-marker indicators**, not validated pathogen labels. The lesion RDS schema contains features such as `n_pycn`, `pycn_density_lesion`, and `rust_density_lesion`, but no direct categorical pathogen field.

After joining one row per sequence to `experimental_design.csv`, treatment groups were:

| Local `inoculation_treatment` value | Sequences | Pycn marker positive | Rust marker positive |
|---|---:|---:|---:|
| `Inoculation` | 258 | 257 | 257 |
| `Inoculation1` | 584 | 578 | 578 |
| `No_Inoculation` | 187 | 187 | 187 |
| **Total** | **1,029** | **1,022** | **1,022** |

The local CSV treatment labels are not themselves pathogen diagnoses. The paper describes the experimental design in terms of combinations of inoculation and fungicide treatment and also reports natural infection and mixed infections. Therefore, the K2 requirement of at least 100 sequences **per pathogen** cannot yet be certified from these treatment and marker counts.

A grouped summary by overall / season / genotype was exported locally to `docs/sequence_counts_by_group.csv`. Its disease columns are marker counts, not pathogen-class counts. Sequence totals by season are 385 (2023) and 644 (2024), summing to 1,029. Do not present the marker columns as authoritative disease classes.

## 7. Weather-coverage estimate (provisional)

A script compared hourly timestamps within each sequence’s first-to-last observation window against the hourly weather records. The calculation was repeated under two assumptions: (A) weather timestamps are UTC; (B) weather timestamps are `Europe/Zurich` local time converted to UTC.

Both assumptions returned the same observed figures:

- Expected sequence-hours: **337,822**.
- Covered sequence-hours: **323,582**.
- Overall coverage: **95.78%**.
- Sequences evaluated: **1,025**.
- Evaluated sequences with coverage ≥90%: **1,025 / 1,025**.
- Median per-sequence coverage: **95.78%**; minimum: **94.87%**.
- Two weather timestamps were excluded as ambiguous/nonexistent when parsing the Europe/Zurich local-time assumption.
- Four of the 1,029 sequences were not included in the hourly-window calculation because they did not yield a valid interval under the script’s minimum-span rule; row-level causes have not yet been reconciled.

This is a useful **provisional estimate** that exceeds the 90% threshold under both tested assumptions. However, the source CSV does not establish the weather timezone, and the exact relationship between weather rows and the study’s intended “sequence time” denominator has not been confirmed with the authors. Do not mark the entire K2 gate as passed solely on this estimate.

## 8. Hardware and storage feasibility (K3)

Latest Windows-reported graphics adapters:

- AMD Radeon R5 M420: 2 GB reported memory.
- Intel HD Graphics 620: 1 GB reported memory.

These are values reported by Windows, not a specialist VRAM benchmark; nevertheless, neither reported adapter meets the roadmap’s ≥8 GB VRAM condition. The C: drive had approximately 2.23 GB free in the latest check. K3 is **not met on the current machine** for full-dataset processing. Small CPU-based metadata/index tasks and the one-sequence loader smoke test have succeeded.

## 9. S01 gate status

| Gate / requirement | Status | Evidence / open issue |
|---|---|---|
| `build_index()` and `count_sequences()` | Partial / sample-level verified | Index runs with 11,768 rows and 1,029 sequences; only 14 local JPGs/masks exist. |
| `load_station()` | Implemented and tested | 11,570 hourly rows loaded; `T`/`RH` complete in hourly subset; weather timezone unresolved. |
| Author toolkit reader on one sample | Pass | 14 images and 14 masks loaded; `TOOLKIT_SMOKE=PASS`. |
| Author’s full processing pipeline | Blocked | No raw image tree, trained `models/best.pt`, `leaf-toolkit`, predictions, or full expected `Output/` tree. |
| K1 — ETH data + reader usable | Partial under Plan B | Metadata/RDS and sample loader work; full dataset was not downloaded. |
| K2 — weather coverage ≥90% | Provisional pass for computed coverage only | 95.78% under two timezone assumptions; timezone/denominator require confirmation. |
| K2 — ≥100 sequences per pathogen | Unverified / blocked | No authoritative sequence-level pathogen mapping was found in inspected metadata/RDS. Treatment groups and symptom markers are not equivalent to pathogen labels. |
| K3 — ≥8 GB GPU VRAM and sufficient storage | Not met locally | Windows reports 1–2 GB on listed adapters; C: has ~2.23 GB free. |
| Literature Matrix ≥15 entries | Count check passed | Workbook has 15 article entries by the local count command; bibliographic details and reading notes still need source-level validation. |
| Published-vs-local sequence/image counts | Unresolved | 1,032 / 12,520 published versus 1,029 sequence IDs / 11,768 leaf-index rows locally. |

## 10. Recommended next actions

1. Keep Plan B; do not download all raw or processing outputs onto the current C: drive.
2. Preserve `docs/sequence_counts_by_group.csv`; label its pycn/rust columns as symptom markers, not pathogen classes.
3. Seek the authoritative disease-occurrence/label mapping and weather timestamp timezone from the paper’s supplementary materials, dataset manifest, or authors.
4. If full pipeline reproduction is required, use a machine with adequate storage and compatible dependencies, and obtain the official model checkpoint and original raw-image/label inputs first.
5. Keep K1 partial, K2 partially verified, and K3 not met until the outstanding evidence is available.

## References

- Dataset paper: Anderegg & McDonald (2026), *High-Resolution Leaf Image Sequences with Geometric Alignment for Dynamic Phenotyping of Foliar Diseases*, Scientific Data 13, 247. https://doi.org/10.1038/s41597-026-06567-y
- Author toolkit repository: https://github.com/and-jonas/sympathique-wheat
