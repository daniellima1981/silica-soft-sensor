# ADR 0002 — Silver layer contract

- **Status:** Accepted
- **Date:** 2026-11-08
- **Related:** ADR 0001 (problem definition)

## Context

The bronze table `bronze_flotation` is a faithful, all-text copy of the Kaggle
CSV (737,453 rows, one row per ~20 s reading, but timestamps only at the full
hour). The EDA (`notebooks/01_eda.ipynb`) found several data-quality issues
that must be made explicit before feature engineering:

- 1,171 duplicated rows, all consecutive (frozen readings, not re-ingestion);
- a total freeze on 2017-07-11 06:00–10:00 and partial freezes per sensor group;
- 639 linear ramps in the inputs (~2.8 % of values), matching data blackouts;
- values piling up near operating limits (density, level 03, pH);
- lab results interpolated (310 h) or repeated for ≥ 4 consecutive hours (361 h).

Process inputs (one row per reading) and lab results (one value per hour,
repeated across the hour's rows) have different grains and different origins.

## Decision

1. **Two tables, one per grain.**
   - `silver_process`: one row per bronze row. Typed process and feed inputs,
     row-level quality flags.
   - `silver_lab_hourly`: one row per hour. `pct_iron_concentrate`,
     `pct_silica_concentrate`, lab quality flags and `is_valid_label`
     (the 3,426 valid labels defined in ADR 0001).
   The gold layer joins them on the hour.

2. **Flag, never drop.** Consecutive duplicates are kept and marked with
   `is_row_repeat` (row identical to the previous one in every variable).
   No bronze row is lost; exclusion rules belong to the gold layer.

3. **Per-variable flags as arrays.** `ramp_vars`, `frozen_vars` and
   `near_limit_vars` are `array<string>` holding the names of the affected
   variables in that row; `is_all_frozen` flags a whole-row freeze.
   To keep the table understandable for readers outside the project:
   - every array column carries a Unity Catalog column comment describing
     the rule;
   - the allowed values are the column-name constants in
     `ingestion/columns.py`, and `validate_silver` fails on any unknown name;
   - a view `silver_quality_summary` explodes the arrays into a long format
     (`variable`, `flag_type`, `n_rows`, `pct_rows`, `first_ts`, `last_ts`)
     and is the entry point for data-quality reporting in the README.

4. **No synthetic 20 s timestamps.** `ts` stays at the full hour.
   The order within the hour is kept in `seq_in_hour` (0..n−1 by `_row_id`).
   The data does not support a fixed 20 s spacing (not every hour has 180 rows).

5. **Rule parameters in configuration.** Minimum ramp length, minimum freeze
   duration, the lab-repetition threshold (≥ 4 h) and the near-limit
   thresholds live in a `SilverConfig` dataclass with documented defaults,
   not in the transformation code. Metadata columns: `_row_id` (lineage to
   bronze) and `_processed_at` (UTC).

## Alternatives considered

- **One boolean column per variable and flag type** (~45 columns): fully
  self-describing schema and easy aggregation, but a very wide table where
  the data columns get lost and "any issue in this row?" needs a long `OR`.
- **A separate long table of flags as the primary store** (`_row_id`,
  `variable`, `flag_type`): the most normalized option, but every feature
  read would need a join. The summary view gives the same long-format
  reading without that cost.
- **Dropping duplicates in silver:** changes rows-per-hour counts and hides
  the freeze episodes.

## Consequences

- Silver keeps full traceability to bronze through `_row_id`.
- Feature engineering (Stage 3) turns the flag arrays into per-variable masks
  (`array_contains`), and pandas consumers must explode or convert the arrays.
- Data-quality figures in the README come from `silver_quality_summary`,
  not from ad-hoc queries.
- Changing a rule threshold only requires a config change and a silver rebuild.
