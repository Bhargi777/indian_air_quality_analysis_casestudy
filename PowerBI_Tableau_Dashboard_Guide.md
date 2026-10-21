# Power BI / Tableau dashboard guide

The completed notebook exports these tables when run from this folder:

- `powerbi_city_daily.csv`: one row per city and date, cleaned city-level observations and engineered columns.
- `powerbi_station_daily.csv`: station-day records with AQI.
- `powerbi_city_dimension.csv`: one row per city with state and region.
- `powerbi_station_dimension.csv`: station metadata.
- `powerbi_next_day_predictions.csv`: held-out 2020 observations, predictions, persistence baseline, and residuals.
- `model_evaluation_metrics.csv`: MAE, RMSE, and R² comparison.

## Suggested model relationships

- City daily fact → city dimension on `City` (many-to-one).
- Station daily fact → station dimension on `StationId` (many-to-one).
- Add a calendar table related to each fact table’s `Date`; do not relate the two fact tables directly.

## Suggested report pages

1. **Overview:** median AQI, Poor-or-worse share, trend over time, city/region comparison; slicers for date, region, city, season, and AQI category.
2. **When and where:** monthly/seasonal AQI, city category shares, reporting coverage by city and year.
3. **Station hotspots:** station-level AQI and within-day spread for Delhi, with operator and station count.
4. **Forecast check:** observed vs Linear Regression predictions and residuals; compare MAE, RMSE, R2, and MAPE with persistence. Note that Linear Regression has higher MAE but lower RMSE and higher R2 on the 2020 holdout.

## Measures

```DAX
Days = COUNTROWS(powerbi_city_daily)
Median AQI = MEDIAN(powerbi_city_daily[AQI])
Poor-or-worse days = CALCULATE([Days], powerbi_city_daily[AQI] > 200)
Poor-or-worse share = DIVIDE([Poor-or-worse days], [Days])
```

Show coverage alongside every comparison. Label 2020 as partial (through July 1), use medians/category shares for skewed AQI, and clearly flag Ahmedabad’s unresolved CO anomaly. Results are observational associations, not causal effects.
