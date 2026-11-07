# ADR 0001 — Problem definition

- **Status:** Accepted
- **Date:** 2026-11-07
- **Stage:** 1.6 — Problem definition (closes Stage 1, Data understanding)
- **Evidence:** [`notebooks/01_eda.ipynb`](../../notebooks/01_eda.ipynb)

## Context

The goal of this project is a soft sensor that predicts the silica content (`% Silica Concentrate`)
of an iron ore flotation concentrate before the laboratory result is available, so that operators
have time to correct reagent dosage and air flow.

The data is the public Kaggle dataset *Quality Prediction in a Mining Process*:

- Period: 2017-03-10 01:00 to 2017-09-09 23:00; 737,453 rows × 24 columns.
- Process variables are sampled every 20 s, but the file only carries an hourly timestamp
  (180 rows per hour). Laboratory assays of the concentrate are hourly.
- There is one data gap of 318 h (2017-03-16 06:00 to 2017-03-29 11:00).

The exploratory analysis (Stage 1) surfaced the facts that drive the decisions below:

- **Interpolated target:** 310 hours of `% Silica Concentrate` are a linear ramp towards the next
  hour's value, i.e. they contain information from the future.
- **Repeated lab results:** in several periods the same lab value is repeated for many consecutive
  hours (up to 28–74 h in three periods), which indicates a frozen value, not a real assay.
- **Regime changes** (starch in May, air in April/August, pH at the end of August) make random
  splits misleading; only chronological validation is meaningful.
- **Weak individual inputs** (|ρ| ≤ 0.21, hourly Spearman) and a **closed control loop**: amine
  dosage responds to silica (peak ρ = 0.33 against silica 3 h earlier).
- **Target autocorrelation** is 0.69 at 1 h, 0.49 at 3 h, 0.29 at 6 h and ~0.15 from 12 h on,
  so the last known lab value is a strong baseline at short gaps.
- `% Iron Concentrate` comes from the same lab sample as the target (ρ = −0.74) and cannot be
  used as a feature at lag 0.

## Decisions

### D1 — Valid labels

The target is the hourly lab silica, restricted to valid hours. Two groups of hours are excluded
as training and evaluation targets:

- the 310 interpolated hours (future leakage);
- 361 hours whose lab result is repeated for ≥ 4 consecutive hours (26 blocks).

This leaves **3,426 valid labels**. Excluded hours are kept in the silver layer with quality flags
rather than deleted, so the decision can be audited and revisited.

### D2 — Laboratory latency

The lab result for hour *t* is assumed to become available at **t + L, with L = 2 h**. The data
does not identify the real latency (timestamps mark the sampling hour, not the release time), so
L is a **configurable assumption**. The sensitivity of the results to L is shown by evaluating
every model as a function of the gap `L + h` (see D5).

### D3 — Forecast horizon

At decision time *t* the model predicts the silica of hour *t + h*, using process data up to *t*
and lab results up to *t − L* only.

- Evaluated horizons: **h ∈ {0, 1, 2, 4}**.
- Headline horizon: **h = 2**, which gives the operation a gap of `L + h` = **4 h** of
  anticipation relative to the lab result.

### D4 — Metric

- **Primary:** MAE in percentage points (pp) — directly interpretable by the operation and robust
  to the occasional large lab error.
- **Secondary:** RMSE, to expose large errors.
- **Skill score**, computed on exactly the same hours as the model:

  skill = 1 − MAE_model / min(MAE_persistence, MAE_expanding_mean)

  A model must beat the best of the naive baselines, not just one of them.

### D5 — Baselines and success criterion

Baselines, both respecting the latency L:

- **Persistence:** the last lab value available at *t* (hour *t − L*).
- **Expanding mean:** the mean of all lab values available at *t*.
- ARIMAX is added as a statistical baseline in Stage 4.

Measured baseline MAE (pp) by gap = L + h:

| gap (h)        | 1     | 2     | 3     | 4     | 5     | 6     | 8     |
|----------------|-------|-------|-------|-------|-------|-------|-------|
| Persistence    | 0.547 | 0.670 | 0.756 | 0.837 | 0.902 | 0.940 | 1.010 |
| Expanding mean | 0.838 | 0.839 | 0.840 | 0.840 | 0.840 | 0.840 | 0.839 |

**Success criterion:** skill ≥ 0.10 at h = 2 (gap 4 h) in walk-forward validation. At gap 4 the
best baseline is persistence (0.837 pp), so this means **MAE ≤ ~0.75 pp**.

## Consequences

- Validation is **walk-forward with chronological splits**; random K-fold is not used.
- Every feature must be **as-of correct**: at time *t*, lab values are only usable up to *t − L*,
  and `% Iron Concentrate` follows the same rule as the target.
- Rolling windows and lags must not cross the 318 h data gap.
- The silver layer must carry quality flags (interpolated target, repeated lab result, ramps and
  frozen sensors) so that D1 can be applied in the gold layer.
- `L` and the list of horizons live in configuration, not in code. Changing `L` changes the gap and
  therefore the baselines; results must always be reported together with the `L` used.
- Results are reported for all horizons; h = 2 is the headline number in the README.

## Alternatives considered

- **Keep interpolated labels:** rejected — they leak the next hour's value into the target.
- **Keep repeated lab results:** rejected — they are frozen values, not assays, and would inflate
  the persistence baseline and the model's apparent accuracy.
- **Fixed L = 0 (no latency):** rejected — it overstates the value of persistence-like features
  and does not reflect how the lab works.
- **RMSE as primary metric:** rejected — less interpretable for the operation and dominated by a
  few large errors.

## References

- Kadlec, P., Gabrys, B. & Strandt, S. (2009). Data-driven soft sensors in the process industry.
- Fortuna, L. et al. (2007). *Soft Sensors for Monitoring and Control of Industrial Processes*.
- Tashman, L. J. (2000). Out-of-sample tests of forecasting accuracy: an analysis and review.
- Hyndman, R. J. & Koehler, A. B. (2006). Another look at measures of forecast accuracy.
- Hyndman, R. J. & Athanasopoulos, G. *Forecasting: Principles and Practice* (3rd ed.).
- Kaufman, S., Rosset, S. & Perlich, C. (2012). Leakage in data mining: formulation, detection,
  and avoidance.
