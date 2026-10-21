# Air Quality Case Study - Replacement Model Slide Content

Use this content for the air-quality case-study presentation's model slide. The Desktop `pptcontent.md` currently open in the editor is for a different project (CLAUSENT legal contract analysis), so this file is prepared separately instead of overwriting that unrelated content.

## Slide: Next-Day AQI Prediction with Linear Regression

**Goal:** Predict each city's AQI for the next calendar day using information available from the previous day.

**Required model:** Linear Regression. AQI is a continuous numeric target, so Linear Regression fits the task. Logistic Regression would be for classifying AQI categories and would discard the exact AQI value.

**Inputs:** Yesterday's AQI, PM2.5, PM10, NO2, and CO; city and target month. Numeric inputs are imputed and standardized; city and month are one-hot encoded. NOx is omitted because it overlaps with NO and NO2; Xylene is omitted because it is heavily missing.

**How the analysis informed the model:** The within-city test found winter AQI higher than monsoon AQI, so calendar month remains a predictor. Adding a separate Season field did not improve validation because season is determined by month. The lockdown comparison was not significant, so no lockdown flag is used. The Diwali result is based on nine city summaries, and the 2020 holdout ends before Diwali, so a Diwali flag cannot be evaluated fairly. P-values are not fed into the model.

**Evaluation:** Train before 2020, select the compact predictor set on 2019 validation, and evaluate on the untouched 2020 holdout.

| Model | MAE (AQI points) | RMSE (AQI points) | R2 | MAPE |
|---|---:|---:|---:|---:|
| Persistence (tomorrow = today) | 19.35 | 41.14 | 0.758 | 15.74% |
| Linear Regression | 22.36 | 37.36 | 0.801 | 22.62% |

**Conclusion:** Linear Regression meets the course requirement. It has lower RMSE and higher R2 than persistence, but higher MAE and MAPE. It is not uniformly better than the simple baseline; present it as a course-compliant model with mixed holdout performance.

### Speaker note

The hypothesis tests informed the choice of calendar features, but their p-values are not model inputs. Because month already identifies the season, a separate season variable was redundant. We did not include lockdown or Diwali flags: the lockdown comparison was not statistically significant, and the 2020 test period contains no Diwali event dates. The model's higher MAE means its typical absolute prediction error is worse than persistence, even though RMSE and R2 are better.
