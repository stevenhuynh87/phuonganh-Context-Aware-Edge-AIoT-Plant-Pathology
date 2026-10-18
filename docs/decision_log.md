# Decision Log & Experiment Tracking

## [2026-10-05] Project Initialization and Sprint 1 Environment
- **Hypothesis:** The repository structure and documentation need to be standardized to support S01 implementation.
- **Experiment:** Initialize and inspect the `data/`, `docs/`, and `tests/` directories, along with project management files.
- **Result:** The repository has a structure that supports code development, testing, and documentation.
- **Action:** Keep.

## [2026-10-06] Reading and Extraction of Group 1 (A1, A2)
- **Hypothesis:** A1 and A2 provide foundational information about the ETH dataset and the relationship between weather and lesion development.
- **Experiment:** Read and extract information from the two papers into `docs/literature_matrix.xlsx`.
- **Result:** The initial information extraction for A1 and A2 was completed, according to the project records.
- **Action:** Keep.

## [2026-10-07] Inspection of ETH Metadata Structure
- **Hypothesis:** The metadata can be read and used to build an index before processing the entire image dataset.
- **Experiment:** Inspect the RDS files and the structure of the leaf/lesion metadata using R.
- **Result:** Recorded 11,768 rows of leaf metadata, 1,029 sequences, and 209,892 rows of lesion metadata.
- **Action:** Continue using the actual metadata; do not generate synthetic data (Keep).

## [2026-10-08] Metadata Consistency Check
- **Hypothesis:** The metadata copies need to be compared to avoid duplicate counting or incorrect data joins.
- **Experiment:** Compare leaf IDs, lesion IDs, and the 2023/2024 copies of `data_leaf.rds`.
- **Result:** There were 1,024 leaf IDs in the lesion metadata; 5 leaf IDs had no corresponding lesion records. The two `data_leaf.rds` copies were recorded as identical.
- **Action:** Do not concatenate the two RDS copies; retain the discrepancy for further verification (Keep).

## [2026-10-09] ETH Index Construction Using Python
- **Hypothesis:** An index can be created from the actual metadata to support subsequent processing steps.
- **Experiment:** Develop `data/eth_index.py` to read the metadata and build a DataFrame.
- **Result:** The index was recorded as having a size of 11,768 × 26, with 1,029 sequences.
- **Action:** Keep the module; continue verifying image paths, mask paths, and labels (Keep).

## [2026-10-10] Weather Data Inspection
- **Hypothesis:** Weather data can provide time-dependent environmental variables for each sequence.
- **Experiment:** Inspect `meta/weather_covariates.csv` and the timestamp data.
- **Result:** Recorded 12,073 rows, including 11,570 hourly records and 503 daily aggregate rows; the date range was from 2022-11-08 to 2024-07-19.
- **Action:** Keep the data; verify the time zone and how rows containing only dates are handled (Keep).

## [2026-10-11] Preliminary Weather Coverage Assessment
- **Hypothesis:** Weather data may achieve the 90% coverage threshold specified in the roadmap.
- **Experiment:** Assess coverage across eligible sequences based on the recorded analysis.
- **Result:** Preliminary coverage was 95.78% across 1,025 sequences; 4 sequences could not be assessed due to missing suitable timestamps.
- **Action:** Do not conclude that K2 has passed yet; continue checking the denominator, timestamps, and label conditions (Keep).

## [2026-10-12] Scientific Database Review
- **Hypothesis:** The scope of research related to leaf diseases, multimodal fusion, and microclimate needs to be assessed preliminarily.
- **Query:** `("plant disease" OR "foliar pathology") AND ("multimodal" OR "microclimate" OR "sensor fusion") AND ("deep learning" OR "time series")`
- **Experiment:** Run the query on IEEE Xplore, Google Scholar, and Semantic Scholar.
- **Result:**
  - IEEE Xplore: 107 results.
  - Google Scholar: approximately 10,700 results.
  - Semantic Scholar: 72 results.
- **Action:** Keep the search strategy; continue screening for relevant papers (Keep).

## [2026-10-13] Data Pipeline Development and Testing
- **Hypothesis:** The pipeline must be able to generate an index from the actual metadata without using synthetic fallback data.
- **Experiment:** Complete and inspect the indexing module and related data-reading components.
- **Result:** The repository contains `data/eth_index.py` and `data/weather.py`; previous test results were recorded as 4 tests passed.
- **Action:** Keep the existing code; rerun the tests before finalizing the repository (Keep).

## [2026-10-14] Inventory and Resource Constraint Assessment
- **Hypothesis:** Storage capacity and GPU resources may limit the ability to process the entire ETH dataset.
- **Experiment:** Compare the dataset inventory information and machine specifications recorded in the audit.
- **Result:** The audit recorded approximately 0.187 GB of local ETH data, approximately 2.23 GB of free space on the C: drive at the time of inspection, and GPUs that did not meet the 8 GB VRAM threshold.
- **Action:** Keep the metadata-based and small-sample processing approach; do not download the entire dataset onto a drive with insufficient space (Keep).

## [2026-10-15] Literature Matrix Review
- **Hypothesis:** The Literature Matrix needs to meet the minimum scope for S01 and clearly distinguish verified information from information that remains incomplete.
- **Experiment:** Review the workbook and the information fields of the collected research papers.
- **Result:** The Literature Review scope was kept at 15 papers for S01; there was no evidence confirming that the full text of every paper had been verified.
- **Action:** Keep the 15-paper scope; do not treat information from abstracts as findings verified against the full text (Keep).

## [2026-10-16] Review of S01 Deliverables
- **Hypothesis:** The audit documents, sequence statistics, and decision log need to be consistent with the code results.
- **Experiment:** Inspect `docs/dataset_audit.md`, `docs/sequence_counts_by_group.csv`, and `docs/decision_log.md`.
- **Result:** The files were recorded as present in the repository; the CSV still needed to be compared against the results of the current code execution before finalization.
- **Action:** Keep the deliverables; verify consistency before committing (Keep).

## [2026-10-17] Feasibility Gate Assessment
- **Hypothesis:** S01 can only be confirmed as complete when sufficient evidence is available for each gate.
- **Experiment:** Compare the metadata, weather coverage, disease labels, and hardware results against the K1–K3 criteria.
- **Result:** K1 was not fully confirmed due to insufficient evidence covering all images/masks; K2 could not yet be concluded to have passed; K3 had not been met on the recorded machine configuration.
- **Action:** Keep the blockers documented in the audit; do not mark all of K1-K3 as PASS (Keep).

## [2026-10-18] SYMPATHIQUE Smoke Test
- **Hypothesis:** A small sample of images and masks can be used to test the toolkit's data-loading capability.
- **Experiment:** Run a smoke test using 14 JPG images and 14 PNG masks, as recorded in the handover.
- **Result:** The handover recorded that the sample was successfully loaded through `LeafDataset`; the full pipeline had not been verified on the entire ETH dataset.
- **Action:** Keep the smoke-test result; document the limitations and missing dependencies (Keep).

## [2026-10-18] S01 Final Review and Closeout Decision

- **Hypothesis:** S01 can be closed only when its deliverables have been reviewed and the feasibility gates have sufficient supporting evidence or an explicitly accepted fallback plan.
- **Experiment:** Review the ETH metadata and index, weather analysis, Literature Matrix, SYMPATHIQUE smoke test, test results, dataset audit, sequence statistics, repository status, and Definition of Done checklist.
- **Result:** The core implementation and preliminary validation activities were completed, but S01 did not meet all closeout requirements. K1 remained partially verified because the local dataset counts differed from the published counts and only a small subset of image/mask paths was locally resolved. K2 remained unverified because authoritative weather-timezone information and disease labels were unresolved. K3 was not achieved on the previously recorded hardware configuration, and the fallback plan required explicit confirmation. The SYMPATHIQUE test verified sample loading only, not the full end-to-end pipeline.
- **Action:** Record S01 as `PARTIALLY COMPLETE / BLOCKED`. Preserve the verified results, document the unresolved items, and complete the required validation and repository checks before declaring S01 fully closed. Do not mark K1–K3 as PASS without sufficient evidence or an explicitly accepted alternative where permitted by the roadmap.
