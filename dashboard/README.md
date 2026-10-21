# Interactive Air Quality Dashboard

This is the case study's interactive visualization app. Streamlit renders the dashboard; SQLite stores the city-day and station-day tables. The first launch imports the available CSV files into `data/air_quality.sqlite`. When a source CSV changes, the app refreshes the database automatically.

## Dashboard pages

- **Overview:** AQI summary metrics, city rankings, daily trend, reporting coverage, and category counts.
- **Map & comparison:** city-level map, AQI severity filtering, and side-by-side city trends.
- **City & season:** city rankings, seasonal comparisons, and a filtered summary table.
- **Pollutants:** pollutant levels by season and an interactive correlation heatmap.
- **Stations:** state/city/severity filters, monitoring-station drill-down, AQI rankings, and within-day spread.
- **Data explorer:** parameterized SQLite search, severity filter, sorting, pagination, and filtered CSV export.
- **ML predictions:** invoke the notebook's Linear Regression pipeline on eligible 2020 holdout records, show actual AQI and prediction history, and export results. It uses the 2019 validation-selected compact lag feature set with City and Month. Missing previous-day AQI inputs block scoring.
- **Model performance:** Linear Regression vs persistence baseline with MAE, RMSE, R² and city/severity error breakdowns.

Use the sidebar to filter by date, city, region, season, AQI category, or state. Ahmedabad can be excluded from the overview for sensitivity comparisons.

## Run on this computer

In PowerShell, from the `dashboard` folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Streamlit prints a local URL (usually `http://localhost:8501`) to open in a browser.

## Run on another computer

Copy the `dashboard` folder and the three original CSV files into the project folder:

- `city_day.csv`
- `station_day.csv`
- `stations.csv`

The notebook's cleaned exports are optional. The app prefers `powerbi_city_daily.csv` and `powerbi_station_daily.csv` when present, then falls back to `city_day_clean.csv` / `station_day_clean.csv`, then to the original files. If only raw station data is available, `stations.csv` is used to attach names, cities, and states.

Install the requirements and run the same commands. The SQLite database is created locally on first launch and is ignored by Git; there is no separate database file to download.

## Backend and data flow

`app.py` is the Streamlit UI. `db.py` handles CSV discovery, basic field preparation, SQLite database creation/refresh, and table reads. The app uses SQLite tables `city_daily` and `station_daily`, plus `app_metadata` to detect changed source files. `sql/schema.sql` documents the metadata table; analytical tables are inferred from the notebook CSV columns so the app can also load raw source exports.

Set `AIR_QUALITY_DATA_DIR` to point to a different folder containing the source CSVs. Set `AIR_QUALITY_DB_PATH` to choose another SQLite database location.

## Notes

The app is for interactive exploration. Coverage varies across cities and years, Ahmedabad has an unresolved CO/AQI anomaly, and the observations are not causal evidence. Historical holdout results are loaded from the notebook's `powerbi_next_day_predictions.csv` and `model_evaluation_metrics.csv`. The prediction page fits the same time-split Linear Regression configuration as the notebook and runs it only on historical holdout dates with available prior-day inputs; it does not claim to forecast beyond the dataset. In this holdout, Linear Regression has higher MAE and MAPE than persistence, but lower RMSE and higher R², so its performance is mixed.
