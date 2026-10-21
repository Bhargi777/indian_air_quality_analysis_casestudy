# Air Quality Analysis and AQI Dashboard

An air quality case study using Indian city and monitoring-station data. The project includes Jupyter notebooks for preprocessing, exploratory analysis, statistical tests, and next-day AQI regression, plus a Streamlit dashboard backed by SQLite for interactive exploration and visualization.

**Live dashboard:** [Indian Air Quality Dashboard](https://indianairquality-team-12.streamlit.app/)

## What is included

- `Air_Quality_Complete_Case_Study.ipynb` - complete analysis, hypothesis tests, Linear Regression model, evaluation, and export steps.
- `Air_Quality_Preprocessing_EDA.ipynb` and `Air_Quality_Part2_Analysis_Questions.ipynb` - supporting preprocessing/EDA and question-based analysis notebooks.
- `dashboard/` - Streamlit application, SQLite loading code, and app-specific instructions.
- `Case_Study_Report.md` - written case-study summary.
- `PowerBI_Tableau_Dashboard_Guide.md` - instructions and data handoff for Power BI or Tableau.
- `city_day.csv`, `station_day.csv`, `stations.csv` - source datasets used by the notebooks and dashboard.
- `*_clean.csv` and `powerbi_*.csv` - processed and dashboard-ready data exports.
- `model_evaluation_metrics.csv` - holdout performance for Linear Regression and the persistence baseline.

## Model summary

The notebook predicts next-day AQI with **Linear Regression**, using chronological training, validation, and holdout periods. On the 2020 holdout, Linear Regression achieved MAE 22.36, RMSE 37.36, R-squared 0.801, and MAPE 22.62%. The persistence baseline achieved MAE 19.35, RMSE 41.14, R-squared 0.758, and MAPE 15.74%. The model therefore has mixed performance: better RMSE and R-squared, but worse MAE and MAPE than persistence.

## Run the dashboard

Requires Python 3.10 or newer. In PowerShell, from the project root:

```powershell
cd dashboard
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Open the local address printed by Streamlit (usually `http://localhost:8501`). On first launch, the app loads available CSV data into a local SQLite database under `dashboard/data/`. That database is generated locally and excluded from Git.

See [dashboard/README.md](dashboard/README.md) for dashboard pages, data-source selection, and configuration details.

## Run the notebook

Open `Air_Quality_Complete_Case_Study.ipynb` in JupyterLab, Jupyter Notebook, or VS Code with a Python environment that has the packages imported by the notebook. Run the notebook from the project root so its relative CSV paths resolve. Run all cells to reproduce the model evaluation and exported CSV files.

## Data portability

Keep the three source CSV files and the notebook/dashboard files together in the project folder. The cleaned and `powerbi_*.csv` files are included because they support the analysis and Power BI/Tableau handoff. The dashboard can fall back to the source CSVs if prepared exports are unavailable.

## Repository name suggestion

**`air-quality-aqi-analysis-dashboard`**

It describes the analysis, AQI model, and interactive dashboard while remaining readable in a repository URL.
