# Silica Soft Sensor

Predicting the silica content of iron ore flotation concentrate before the lab does.

In a flotation plant, the % silica in the concentrate is the key quality metric, but it
comes from laboratory assays that arrive about once an hour, after the material has
already been produced. Operators adjust reagents and air flow based on information that
is already outdated. This project builds a **soft sensor**: a model that estimates
silica from process variables sampled every 20 seconds, giving operators lead time to
correct the process before off-spec concentrate piles up.

The goal is not only a model but a production-grade ML system, from raw data to a
monitored model in production:

- **Data:** bronze/silver/gold Delta tables in Unity Catalog, built from the public
  [Quality Prediction in a Mining Process](https://www.kaggle.com/datasets/edumagalhaes/quality-prediction-in-a-mining-process) dataset
- **Features:** lags, rolling windows and aggregations computed with as-of correctness,
  so the model only sees what was known at each moment
- **Modeling:** ARIMAX baselines vs. scikit-learn and XGBoost, evaluated with
  walk-forward validation and explicit data-leakage tests
- **MLOps:** MLflow tracking and Unity Catalog model registry with Champion/Challenger
  aliases, hourly batch scoring jobs, drift monitoring and a defined retraining trigger
- **Engineering:** Databricks Asset Bundles with `dev` and `prd` targets, and CI/CD on
  GitHub Actions (lint, type checks, tests, bundle validation and deploy)
