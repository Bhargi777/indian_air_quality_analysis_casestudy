# Air Quality in Indian Cities — Case Study Report

## Problem and objective

This case study analyzes daily AQI and pollutant measurements from Indian cities between 2015 and July 1, 2020. It examines data quality, pollution patterns across cities, seasons and stations, evidence for selected comparisons, and the feasibility of next-day AQI prediction.

## Data and preprocessing

The analysis uses `city_day.csv` (29,531 city-day records), `station_day.csv` (108,035 station-day records), and `stations.csv` (230 station metadata rows). The city-day file is the main analytical table. Dates are parsed, duplicates and suspicious values are checked, rows without AQI are removed, Xylene is dropped because about 61% of values are missing and many cities do not measure it, and remaining pollutant gaps are filled with city-month medians followed by month medians. AQI-missing rows are dropped rather than inventing target values. Outliers are retained and flagged for sensitivity analysis.

The cleaned city dataset has 24,850 rows. Coverage varies by city and year; 2020 ends on July 1. Ahmedabad’s exceptionally high CO and AQI are treated as an unresolved anomaly and are separated in key comparisons. Imputed pollutant readings are compared with real readings when interpreting correlations.

## Analysis questions

The complete notebook now has 19 questions; the Diwali event-window analysis and its city-level test are combined under Q10. It keeps the other notebook’s case-specific analyses, replaces its generic sampling simulation with a raw-data anomaly audit, and changes city uncertainty intervals to a calendar-month block bootstrap because daily AQI values are serially dependent. The questions cover:

- Dataset scope, distributions, city levels and variability.
- Missingness, unusual values, cleaning decisions, and imputation effects.
- Approximate pollutant contributions, particle composition, and correlated predictors.
- Seasonal and yearly comparisons, lockdown and Diwali event windows.
- Serial dependence, uncertainty in city risk, and station-level hot spots.
- Statistical evidence, two additional paired comparisons, the regression decision, forecast diagnostics, and BI reporting.

Each question is answered with analysis, a visualization, and an interpretation or decision in `Air_Quality_Complete_Case_Study.ipynb`.

## Statistical evidence

All formal tests use city-level paired summaries so the many autocorrelated daily readings are not treated as independent replicates. We use t-tests and apply the Holm correction across the three selected tests; decisions use family-wise alpha = 0.05.

- **Winter vs monsoon:** A two-sided paired t-test across 22 eligible cities gives a mean winter-minus-monsoon city-median difference of 102.4 AQI points (95% CI 65.3 to 139.6), t(21) = 5.736, raw p = 1.08e-5, Holm-adjusted p = 3.23e-5. This supports a seasonal association in the observed cities. 
- **Lockdown-period A/B-style comparison:** For 18 cities with sufficient observations, median year-over-year AQI change is -21.6% in Jan-Mar and -33.0% in Apr-Jun. A two-sided one-sample t-test on each city's incremental change gives a mean of -9.7 percentage points, t(17) = -1.425, raw and Holm-adjusted p = 0.172, 95% CI -23.9 to 4.6. Eleven of 18 cities have a larger percentage drop in Apr-Jun. The result is not significant at alpha = 0.05 and is not a causal estimate. The 95% CI includes zero.
- **Diwali event window (Q10):** A one-sided one-sample t-test on nine city-level median changes (day +1 vs days -3 to -1) gives a mean increase of 74.1 index points, t(8) = 2.330, raw p = 0.0241, Holm-adjusted p = 0.0481; the median city increase is 53.9 points. This supports an event-timed association, not proof that fireworks caused the increase. The small number of cities warrants caution.

**Additional paired comparisons (Q16-Q17):** For 25 cities, weekend mean AQI is 129.0 and weekday mean AQI is 131.0; the mean city-level difference (weekend minus weekday) is -2.0 points (95% CI -3.1 to -0.9), t(24) = -3.625, raw p = 0.00135. For 24 cities, the mean winter-minus-summer difference in city median AQI is 67.2 points (95% CI 41.1 to 93.2), t(23) = 5.337, raw p = 2.03e-5. These two added comparisons are exploratory; their raw p-values are not included in the Holm adjustment for the three primary tests. The weekend difference is small in size despite its low p-value.

The city-risk calendar-month block bootstrap gives uncertainty intervals; it is an estimation method, not a hypothesis test.

## Regression model and justification

The course requires a linear or logistic regressor. AQI is continuous, so the selected model is **Linear Regression**; Logistic Regression would be for predicting AQI categories. The model predicts AQI from the previous day's AQI, PM2.5, PM10, NO2, and CO, plus city and target month. The lag inputs make the prediction available from prior-day information. Xylene is excluded for missingness, and NOx is excluded because it overlaps with NO and NO2. Numeric values are imputed and standardized in a training-fitted pipeline; city and month are one-hot encoded.

The hypothesis tests inform feature decisions but are not model inputs. The significant within-city winter/monsoon result supports retaining month in the model. A separate Season field is determined by Month and gave no improvement in linear validation, so it is omitted as redundant. The lockdown comparison was not significant, so no lockdown flag is used. The Diwali result is based on nine city summaries, and the 2020 holdout ends before Diwali, so a Diwali feature cannot be fairly evaluated here.

A chronological 2019 validation period selected the compact pollutant set over all available lagged pollutants (MAE 29.804 vs 30.240). We then evaluated once on the 2020 holdout.

| Model | MAE | RMSE | R2 | MAPE (%) |
|---|---:|---:|---:|---:|
| Persistence | 19.348 | 41.138 | 0.758 | 15.74 |
| Linear Regression | 22.363 | 37.359 | 0.801 | 22.62 |

Linear Regression has lower RMSE and higher R2 than persistence, but its MAE is higher; it does not outperform the baseline on typical absolute error. Its MAPE is 22.62%, versus 15.74% for persistence. Include this mixed result rather than claiming the model is uniformly better. Large errors remain for Ahmedabad and extreme AQI values. The 2020 holdout is short and contains unusual observations, so this is a course-compliant prototype, not a deployment forecast.

## Main conclusions and limitations

AQI varies strongly by city and season. Particle pollution is closely related to AQI, but the relationship is sensitive to Ahmedabad and pollutant imputation. The dataset contains 543 city-day AQI values above 500 and a maximum of 2,049; these are retained and flagged because the data alone does not establish whether they are reporting or measurement errors. Station records reveal sizable within-city differences. Daily readings are dependent, coverage is unbalanced, and the observations do not establish causal effects. Interpret correlations and the lockdown/Diwali results as associations.

## BI handoff

The notebook generates city-day and station-day fact tables, dimensions, held-out next-day predictions, and model metrics. `PowerBI_Tableau_Dashboard_Guide.md` describes relationships, measures, suggested pages, and caveats. A native PBIX/TWB file is not included because Power BI Desktop/Tableau is unavailable in this environment.

## Data source

Central Pollution Control Board air-quality data as distributed in the Kaggle “Air Quality Data in India” dataset, as described in the source notebook. Verify the exact dataset URL and access date before final submission.
