import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3

from db import DB_PATH, PROJECT_DIR, POLLUTANTS, initialize_database, read_table, row_counts

st.set_page_config(page_title="Indian Air Quality Explorer", page_icon="🌫️", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.7rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {background: #f4f7fb; padding: 0.8rem 1rem; border-radius: 0.55rem;}
</style>
""", unsafe_allow_html=True)

st.title("Indian Air Quality Explorer")
st.caption("Interactive city and monitoring-station analysis | Data: 2015 to July 1, 2020")

@st.cache_data(show_spinner="Loading data from SQLite...")
def table(name, database_path, database_signature):
    return read_table(name)

try:
    source_info = initialize_database()
    db_signature = DB_PATH.stat().st_mtime_ns
    city_data = table("city_daily", str(DB_PATH), db_signature)
    station_data = table("station_daily", str(DB_PATH), db_signature)
except Exception as exc:
    st.error(f"Could not prepare the dashboard data: {exc}")
    st.markdown("""
    Place the three original files beside the notebook, then restart the app:
    `city_day.csv`, `station_day.csv`, and `stations.csv`.
    The app can also use the notebook's cleaned CSV exports when they are present.
    """)
    st.stop()

city_data["Date"] = pd.to_datetime(city_data["Date"], errors="coerce")
station_data["Date"] = pd.to_datetime(station_data["Date"], errors="coerce")
city_data["AQI"] = pd.to_numeric(city_data["AQI"], errors="coerce")
station_data["AQI"] = pd.to_numeric(station_data["AQI"], errors="coerce")

with st.sidebar:
    st.header("Explore")
    page = st.radio("Dashboard page", ["Overview", "Map & comparison", "City & season", "Pollutants", "Stations", "Data explorer", "ML predictions", "Model performance"], index=0)
    st.divider()
    st.caption("Data is stored locally in SQLite.")
    st.caption(f"City source: {source_info['city_source'].name}")
    st.caption(f"Station source: {source_info['station_source'].name}")
    if source_info["reloaded"]:
        st.success("SQLite database created or refreshed from CSV sources.")


def date_filter(frame, key):
    frame = frame.dropna(subset=["Date", "AQI"])
    if frame.empty:
        return frame
    first = frame["Date"].min().date()
    last = frame["Date"].max().date()
    dates = st.sidebar.date_input("Date range", value=(first, last), min_value=first, max_value=last, key=key)
    if isinstance(dates, (tuple, list)) and len(dates) == 2:
        start, end = dates
    else:
        start = end = dates
    return frame[frame["Date"].dt.date.between(start, end)]


def city_filters(frame, key_prefix="city"):
    regions = sorted(frame["Region"].dropna().astype(str).unique()) if "Region" in frame else []
    selected_regions = st.sidebar.multiselect("Region", regions, default=regions, key=f"{key_prefix}_regions")
    filtered = frame[frame["Region"].astype(str).isin(selected_regions)] if regions else frame
    cities = sorted(filtered["City"].dropna().astype(str).unique()) if "City" in filtered else []
    selected_cities = st.sidebar.multiselect("City", cities, default=cities, key=f"{key_prefix}_cities")
    filtered = filtered[filtered["City"].astype(str).isin(selected_cities)] if cities else filtered
    if "Season" in filtered:
        seasons = [s for s in ["Winter", "Summer", "Monsoon", "Post-Monsoon"] if s in set(filtered["Season"].dropna())]
        selected_seasons = st.sidebar.multiselect("Season", seasons, default=seasons, key=f"{key_prefix}_seasons")
        filtered = filtered[filtered["Season"].isin(selected_seasons)]
    buckets = [b for b in ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"] if b in set(filtered["AQI_Bucket"].dropna().astype(str))]
    if buckets:
        selected_buckets = st.sidebar.multiselect("AQI category", buckets, default=buckets, key=f"{key_prefix}_buckets")
        filtered = filtered[filtered["AQI_Bucket"].astype(str).isin(selected_buckets)]
    return filtered


def kpis(frame):
    if frame.empty:
        st.warning("No records match the current filters.")
        return
    poor_share = (frame["AQI"] > 200).mean() * 100
    a, b, c, d = st.columns(4)
    a.metric("Median AQI", f"{frame['AQI'].median():.0f}")
    b.metric("Mean AQI", f"{frame['AQI'].mean():.1f}")
    c.metric("Poor-or-worse days", f"{poor_share:.1f}%")
    d.metric("Cities", f"{frame['City'].nunique():,}")


def no_rows():
    st.info("No data matches the selected filters. Widen the date range or remove a filter.")


def download_csv(frame, filename, label="Download filtered CSV"):
    st.download_button(label, frame.to_csv(index=False).encode("utf-8"), filename, "text/csv")


CITY_COORDS = {
    "Ahmedabad": (23.0225,72.5714), "Amaravati": (16.5062,80.6480), "Amritsar": (31.6340,74.8723),
    "Bengaluru": (12.9716,77.5946), "Bhopal": (23.2599,77.4126), "Chandigarh": (30.7333,76.7794),
    "Chennai": (13.0827,80.2707), "Coimbatore": (11.0168,76.9558), "Delhi": (28.6139,77.2090),
    "Ernakulam": (9.9816,76.2999), "Gurugram": (28.4595,77.0266), "Guwahati": (26.1445,91.7362),
    "Hyderabad": (17.3850,78.4867), "Jaipur": (26.9124,75.7873), "Jorapokhar": (23.7167,86.4167),
    "Kochi": (9.9312,76.2673), "Kolkata": (22.5726,88.3639), "Lucknow": (26.8467,80.9462),
    "Mumbai": (19.0760,72.8777), "Patna": (25.5941,85.1376), "Shillong": (25.5788,91.8933),
    "Talcher": (20.9500,85.2167), "Thiruvananthapuram": (8.5241,76.9366), "Visakhapatnam": (17.6868,83.2185),
    "Aizawl": (23.7271,92.7176), "Brajrajnagar": (21.8167,83.9167),
}
PREDICTION_PATH = PROJECT_DIR / "powerbi_next_day_predictions.csv"
METRICS_PATH = PROJECT_DIR / "model_evaluation_metrics.csv"


@st.cache_resource(show_spinner="Training the notebook's time-split Linear Regression...")
def get_notebook_model():
    from sklearn.compose import ColumnTransformer
    from sklearn.linear_model import LinearRegression
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    source = PROJECT_DIR / "city_day.csv"
    raw = pd.read_csv(source, parse_dates=["Date"], low_memory=False).sort_values(["City", "Date"])
    lag_cols = ["AQI"] + [c for c in POLLUTANTS if c in raw.columns and c not in ("Xylene", "NOx")]
    previous = raw[["City", "Date"] + lag_cols].copy()
    previous["Date"] += pd.Timedelta(days=1)
    previous = previous.rename(columns={c: "prev_" + c for c in lag_cols})
    target = raw[["City", "Date", "AQI"]].dropna(subset=["AQI"]).rename(columns={"AQI": "target_AQI"})
    data = target.merge(previous, on=["City", "Date"], how="left").dropna(subset=["prev_AQI"])
    data["Month"] = data["Date"].dt.month.astype(str)
    data["Season"] = data["Date"].dt.month.map({
        12: "Winter", 1: "Winter", 2: "Winter",
        3: "Summer", 4: "Summer", 5: "Summer",
        6: "Monsoon", 7: "Monsoon", 8: "Monsoon", 9: "Monsoon",
        10: "Post-Monsoon", 11: "Post-Monsoon",
    })
    train = data[data["Date"] < "2020-01-01"]
    numeric = ["prev_" + c for c in lag_cols]
    # 2019 validation selected this compact set; NOx is excluded as redundant with NO/NO2.
    numeric = ["prev_AQI", "prev_PM2.5", "prev_PM10", "prev_NO2", "prev_CO"]
    categorical = ["City", "Month"]
    preprocess = ColumnTransformer([
        ("numeric", make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler()), numeric),
        ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical),
    ])
    model = make_pipeline(preprocess, LinearRegression())
    model.fit(train[numeric + categorical], train["target_AQI"])
    data["Month"] = data["Month"].astype(str)
    return model, data, numeric + categorical


if page == "Overview":
    with st.sidebar:
        city_data = date_filter(city_data, "overview_dates")
        city_data = city_filters(city_data, "overview")
        exclude_ahmedabad = st.checkbox("Exclude Ahmedabad from this view", value=False)
    if exclude_ahmedabad:
        city_data = city_data[city_data["City"] != "Ahmedabad"]
    kpis(city_data)
    if city_data.empty:
        no_rows()
    else:
        st.warning("Coverage is uneven across cities and years. Ahmedabad has an unresolved CO/AQI anomaly; use the sidebar to compare results without it.")
        daily = city_data.groupby("Date", as_index=False).agg(Median_AQI=("AQI", "median"), Reporting_Cities=("City", "nunique"))
        fig = px.line(daily, x="Date", y="Median_AQI", hover_data=["Reporting_Cities"], title="Daily median AQI among cities reporting that day")
        fig.update_layout(yaxis_title="Median AQI", xaxis_title="Date")
        st.plotly_chart(fig, use_container_width=True)
        left, right = st.columns(2)
        bucket_order = ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]
        counts = city_data["AQI_Bucket"].astype(str).value_counts().reindex(bucket_order, fill_value=0).rename_axis("AQI_Bucket").reset_index(name="Days")
        left.plotly_chart(px.bar(counts, x="AQI_Bucket", y="Days", title="Days by AQI category", color="AQI_Bucket"), use_container_width=True)
        coverage = city_data.groupby(["Year", "City"], as_index=False).size().rename(columns={"size": "Days"})
        right.plotly_chart(px.density_heatmap(coverage, x="Year", y="City", z="Days", histfunc="sum", title="Reporting coverage by city and year", color_continuous_scale="Blues"), use_container_width=True)
        st.caption("The trend summarizes the cities reporting on each date; the set of reporting cities changes over time.")

elif page == "Map & comparison":
    with st.sidebar:
        city_data = date_filter(city_data, "map_dates")
        city_data = city_filters(city_data, "map")
    if city_data.empty:
        no_rows()
    else:
        city_summary = city_data.groupby("City", as_index=False).agg(Median_AQI=("AQI", "median"), Mean_AQI=("AQI", "mean"), Days=("AQI", "size"))
        city_summary["Latitude"] = city_summary["City"].map(lambda c: CITY_COORDS.get(c, (None,None))[0])
        city_summary["Longitude"] = city_summary["City"].map(lambda c: CITY_COORDS.get(c, (None,None))[1])
        mapped = city_summary.dropna(subset=["Latitude", "Longitude"])
        st.subheader("City AQI map")
        if mapped.empty:
            st.info("No selected cities have map coordinates in the dashboard reference list.")
        else:
            st.plotly_chart(px.scatter_geo(mapped, lat="Latitude", lon="Longitude", size="Days", color="Median_AQI", hover_name="City", hover_data=["Mean_AQI", "Days"], color_continuous_scale="RdYlGn_r", projection="natural earth", scope="asia", title="Median AQI by city (selected period)"), use_container_width=True)
        cities = sorted(city_data["City"].dropna().unique())
        chosen = st.multiselect("Compare city trends", cities, default=cities[:min(4,len(cities))], key="compare_cities")
        compare = city_data[city_data["City"].isin(chosen)].groupby(["Date", "City"], as_index=False)["AQI"].median()
        if not compare.empty:
            st.plotly_chart(px.line(compare, x="Date", y="AQI", color="City", title="Side-by-side city AQI trends"), use_container_width=True)
        download_csv(city_data, "filtered_city_readings.csv")

elif page == "City & season":
    with st.sidebar:
        city_data = date_filter(city_data, "city_dates")
        city_data = city_filters(city_data, "city")
    kpis(city_data)
    if city_data.empty:
        no_rows()
    else:
        city_summary = city_data.groupby(["City", "Region"], as_index=False).agg(Median_AQI=("AQI", "median"), Mean_AQI=("AQI", "mean"), Days=("AQI", "count"))
        city_summary = city_summary.sort_values("Median_AQI", ascending=False)
        fig = px.bar(city_summary.head(20).sort_values("Median_AQI"), x="Median_AQI", y="City", color="Region", hover_data=["Mean_AQI", "Days"], orientation="h", title="Cities with highest median AQI in the selected period")
        st.plotly_chart(fig, use_container_width=True)
        season_order = ["Winter", "Summer", "Monsoon", "Post-Monsoon"]
        seasonal = city_data.groupby(["Season", "City"], as_index=False).agg(Median_AQI=("AQI", "median"), Days=("AQI", "count"))
        fig = px.box(seasonal, x="Season", y="Median_AQI", points="all", category_orders={"Season": season_order}, hover_data=["City", "Days"], title="City-level AQI medians by season")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(city_summary, use_container_width=True, hide_index=True)
        st.caption("City-level seasonal medians are shown so cities with longer records do not dominate the seasonal comparison.")

elif page == "Pollutants":
    with st.sidebar:
        city_data = date_filter(city_data, "pollutant_dates")
        city_data = city_filters(city_data, "pollutant")
    available = [name for name in POLLUTANTS if name in city_data.columns]
    if city_data.empty:
        no_rows()
    elif not available:
        st.warning("No pollutant measurements are available in the selected city data source.")
    else:
        pollutant = st.selectbox("Pollutant", available, index=available.index("PM2.5") if "PM2.5" in available else 0)
        statistic = st.radio("Summary", ["Median", "Mean"], horizontal=True)
        agg = "median" if statistic == "Median" else "mean"
        summary = city_data.groupby("Season", as_index=False)[pollutant].agg(agg).rename(columns={pollutant: "Concentration"})
        fig = px.bar(summary, x="Season", y="Concentration", title=f"{statistic} {pollutant} concentration by season")
        st.plotly_chart(fig, use_container_width=True)
        numeric_cols = [col for col in available + ["AQI"] if col in city_data.columns]
        corr = city_data[numeric_cols].apply(pd.to_numeric, errors="coerce").corr()
        heat = px.imshow(corr, text_auto=".2f", zmin=-1, zmax=1, color_continuous_scale="RdBu_r", title="Pollutant and AQI correlation (selected records)")
        st.plotly_chart(heat, use_container_width=True)
        st.caption("Correlation describes association. It does not establish that a pollutant caused the AQI pattern.")

elif page == "Stations":
    station_data = station_data.dropna(subset=["AQI", "Date"])
    with st.sidebar:
        station_data = date_filter(station_data, "station_dates")
        state_values = sorted(station_data["State"].dropna().astype(str).unique()) if "State" in station_data else []
        selected_states = st.multiselect("State", state_values, default=state_values, key="station_states")
        if state_values:
            station_data = station_data[station_data["State"].astype(str).isin(selected_states)]
        city_values = sorted(station_data["City"].dropna().astype(str).unique()) if "City" in station_data else []
        preferred = ["Delhi"] if "Delhi" in city_values else city_values[:1]
        selected_station_cities = st.multiselect("City", city_values, default=preferred, key="station_cities")
        if city_values:
            station_data = station_data[station_data["City"].astype(str).isin(selected_station_cities)]
        station_buckets = sorted(station_data["AQI_Bucket"].dropna().astype(str).unique()) if "AQI_Bucket" in station_data else []
        selected_buckets = st.multiselect("AQI severity", station_buckets, default=station_buckets, key="station_buckets")
        if station_buckets:
            station_data = station_data[station_data["AQI_Bucket"].astype(str).isin(selected_buckets)]
    if station_data.empty:
        no_rows()
    elif "StationName" not in station_data.columns:
        st.warning("Station names are unavailable. Keep stations.csv beside the raw station-day file and reload the app.")
    else:
        station_key = "StationName" if "StationName" in station_data else "StationId"
        selected_stations = st.multiselect("Monitoring station", sorted(station_data[station_key].dropna().astype(str).unique()), key="station_names")
        if selected_stations:
            station_data = station_data[station_data[station_key].astype(str).isin(selected_stations)]
        station_summary = station_data.groupby([station_key, "City"], as_index=False).agg(Median_AQI=("AQI", "median"), Mean_AQI=("AQI", "mean"), Days=("AQI", "count"))
        station_summary = station_summary[station_summary["Days"] >= 30].sort_values("Median_AQI", ascending=False)
        fig = px.bar(station_summary.head(20).sort_values("Median_AQI"), x="Median_AQI", y=station_key, color="City", orientation="h", hover_data=["Mean_AQI", "Days"], title="Stations with highest median AQI (at least 30 observations)")
        st.plotly_chart(fig, use_container_width=True)
        daily_range = station_data.groupby("Date")["AQI"].agg(lambda x: x.max()-x.min()).rename("Station AQI range").reset_index()
        st.plotly_chart(px.line(daily_range, x="Date", y="Station AQI range", title="Within-day AQI spread across selected stations"), use_container_width=True)
        st.dataframe(station_summary, use_container_width=True, hide_index=True)
        download_csv(station_data, "filtered_station_readings.csv")
        st.caption("Station coverage and operating agencies differ; station differences may reflect both location and measurement practices.")

elif page == "Data explorer":
    table_name = st.selectbox("SQLite table", ["city_daily", "station_daily"])
    # Perform filtering, sorting, and pagination in SQLite; never interpolate user-entered SQL.
    with sqlite3.connect(DB_PATH) as conn:
        columns = [r[1] for r in conn.execute(f'PRAGMA table_info("{table_name}")')]
        searchable = [c for c in ["City", "State", "StationName", "StationId", "AQI_Bucket"] if c in columns]
        col1, col2, col3 = st.columns(3)
        search = col1.text_input("Search city/station/category")
        category_options = []
        if "AQI_Bucket" in columns:
            category_options = [r[0] for r in conn.execute(f'SELECT DISTINCT AQI_Bucket FROM "{table_name}" WHERE AQI_Bucket IS NOT NULL ORDER BY AQI_Bucket')]
        category = col2.multiselect("AQI severity", category_options, default=category_options)
        sort_col = col3.selectbox("Sort by", [c for c in ["Date", "AQI", "City", "StationName"] if c in columns], index=0)
        sort_dir = st.radio("Order", ["Newest / largest first", "Oldest / smallest first"], horizontal=True)
        page_size = st.selectbox("Rows per page", [25, 50, 100, 250], index=1)
        page_number = st.number_input("Page", min_value=1, value=1, step=1)
        where, params = [], []
        if search and searchable:
            where.append("(" + " OR ".join(f'CAST("{c}" AS TEXT) LIKE ?' for c in searchable) + ")")
            params.extend([f"%{search}%"] * len(searchable))
        if category and "AQI_Bucket" in columns:
            where.append("AQI_Bucket IN (" + ",".join("?" for _ in category) + ")")
            params.extend(category)
        clause = " WHERE " + " AND ".join(where) if where else ""
        direction = "DESC" if sort_dir.startswith("Newest") else "ASC"
        total = conn.execute(f'SELECT COUNT(*) FROM "{table_name}"{clause}', params).fetchone()[0]
        query = f'SELECT * FROM "{table_name}"{clause} ORDER BY "{sort_col}" {direction} LIMIT ? OFFSET ?'
        view = pd.read_sql_query(query, conn, params=params + [int(page_size), (int(page_number)-1)*int(page_size)])
        exported = pd.read_sql_query(f'SELECT * FROM "{table_name}"{clause} ORDER BY "{sort_col}" {direction}', conn, params=params)
    st.caption(f"{total:,} matching rows · showing page {int(page_number)} · source: SQLite")
    st.dataframe(view, use_container_width=True, hide_index=True)
    download_csv(exported, f"{table_name}_filtered.csv", "Download all filtered rows")

elif page == "ML predictions":
    prediction_path = PREDICTION_PATH
    metrics_path = METRICS_PATH
    if not prediction_path.exists():
        st.info("Forecast outputs are not present yet. Run the completed notebook to generate the model evaluation CSVs.")
    else:
        forecast = pd.read_csv(prediction_path, parse_dates=["Date"])
        with st.sidebar:
            forecast_cities = sorted(forecast["City"].dropna().unique())
            selected_forecast_cities = st.multiselect("City", forecast_cities, default=forecast_cities, key="forecast_cities")
        forecast = forecast[forecast["City"].isin(selected_forecast_cities)]
        st.info("These are saved predictions from the notebook's 2020 time-ordered holdout. Each row was scored only when the previous-day AQI input existed; actual AQI is shown for retrospective evaluation, not as a future forecast.")
        if forecast.empty:
            no_rows()
        else:
            st.subheader("Run the trained model on a selected holdout day")
            city_choice = st.selectbox("City with eligible next-day inputs", sorted(forecast["City"].unique()), key="model_city")
            city_rows = forecast[forecast["City"] == city_choice]
            date_choice = st.selectbox("Prediction target date", sorted(city_rows["Date"].dt.date.unique()), key="model_date")
            if st.button("Run Linear Regression prediction"):
                try:
                    fitted_model, model_rows, feature_cols = get_notebook_model()
                    selected = model_rows[(model_rows["City"] == city_choice) & (model_rows["Date"].dt.date == date_choice)]
                    if selected.empty or selected["prev_AQI"].isna().all():
                        st.warning("Required previous-day AQI input is missing for this city/date, so no prediction was produced.")
                    else:
                        row = selected.iloc[[0]]
                        predicted = float(fitted_model.predict(row[feature_cols])[0])
                        actual = float(row["target_AQI"].iloc[0])
                        saved = city_rows[city_rows["Date"].dt.date == date_choice].iloc[0]
                        p1,p2,p3 = st.columns(3)
                        p1.metric("Model prediction", f"{predicted:.1f}")
                        p2.metric("Recorded AQI", f"{actual:.1f}")
                        p3.metric("Absolute error", f"{abs(actual-predicted):.1f}")
                        st.caption(f"Inputs from {row['Date'].iloc[0].date() - pd.Timedelta(days=1)} were used for the next-day target. Saved notebook prediction: {saved['Prediction']:.1f}. This selected target is in the historical 2020 holdout.")
                except Exception as exc:
                    st.error(f"Could not run the notebook model: {exc}. Keep city_day.csv beside the notebook and install dashboard/requirements.txt.")
            fig = px.scatter(forecast, x="target_AQI", y="Prediction", color="City", opacity=0.55, hover_data=["Date", "Persistence", "Residual"], title="Observed vs predicted next-day AQI")
            maximum = max(float(forecast["target_AQI"].max()), float(forecast["Prediction"].max()))
            fig.add_shape(type="line", x0=0, y0=0, x1=maximum, y1=maximum, line=dict(dash="dash", color="black"))
            fig.update_layout(xaxis_title="Observed next-day AQI", yaxis_title="Linear Regression prediction")
            st.plotly_chart(fig, use_container_width=True)
            st.plotly_chart(px.histogram(forecast, x="Residual", nbins=50, title="Prediction residuals (observed - predicted)"), use_container_width=True)
            history = forecast.sort_values("Date")
            city_history = st.selectbox("Prediction history city", sorted(history["City"].unique()), key="history_city")
            selected_history = history[history["City"] == city_history]
            st.plotly_chart(px.line(selected_history, x="Date", y=[c for c in ["target_AQI", "Prediction", "Persistence"] if c in selected_history], title=f"Actual and predicted AQI history · {city_history}"), use_container_width=True)
            download_csv(forecast, "prediction_history.csv")
            st.caption("The Linear Regression has higher MAE than persistence but lower RMSE and higher R² in this holdout. Errors are larger for Ahmedabad and extreme AQI values. This is a retrospective proof of concept, not a live forecast.")

elif page == "Model performance":
    metrics_path = METRICS_PATH
    prediction_path = PREDICTION_PATH
    if not metrics_path.exists() or not prediction_path.exists():
        st.info("Run the completed notebook to generate the model evaluation outputs.")
    else:
        metrics = pd.read_csv(metrics_path)
        predictions = pd.read_csv(prediction_path, parse_dates=["Date"])
        a,b = st.columns(2)
        for col,(_,row) in zip([a,b],metrics.iterrows()):
            col.metric(str(row["Model"]), f"MAE {row['MAE']:.2f}", f"RMSE {row['RMSE']:.2f} · R² {row['R2']:.3f}", help=f"MAPE: {row['MAPE (%)']:.2f}%")
        st.plotly_chart(px.bar(metrics.melt(id_vars="Model", value_vars=["MAE","RMSE"], var_name="Metric", value_name="AQI error"), x="Model", y="AQI error", color="Metric", barmode="group", title="Linear Regression compared with persistence baseline"), use_container_width=True)
        predictions["AQI band"] = pd.cut(predictions["target_AQI"], [0,50,100,200,300,400,500,1000,2500], include_lowest=True)
        per_city = predictions.groupby("City", as_index=False).agg(MAE=("Residual",lambda x:x.abs().mean()), Days=("Residual","size")).sort_values("MAE",ascending=False)
        per_band = predictions.groupby("AQI band", observed=False).agg(MAE=("Residual",lambda x:x.abs().mean()), Days=("Residual","size")).reset_index()
        # Plotly cannot JSON-encode pandas Interval objects; use readable string labels.
        per_band["AQI band"] = per_band["AQI band"].astype(str)
        left,right = st.columns(2)
        left.plotly_chart(px.bar(per_city.head(12), x="MAE", y="City", orientation="h", hover_data=["Days"], title="Holdout MAE by city (largest 12)"), use_container_width=True)
        right.plotly_chart(px.bar(per_band.dropna(subset=["MAE"]), x="AQI band", y="MAE", hover_data=["Days"], title="Holdout MAE by actual AQI severity"), use_container_width=True)
        st.markdown("**Why Linear Regression?** The faculty requires a linear or logistic regressor; AQI is continuous, so Linear Regression is the appropriate choice. A 2019 chronological validation comparison selected lagged AQI, PM2.5, PM10, NO2 and CO with City and Month. NOx is excluded because it overlaps with NO and NO2. The seasonal test supports retaining time-of-year information; Month already represents that information, so a separate Season category is redundant in this linear design. The lockdown test does not justify a lockdown flag, and Diwali cannot be evaluated in the 2020 holdout. P-values are not model inputs. On the final 2020 holdout, this model has higher MAE than persistence, but lower RMSE and higher R². It meets the course model requirement, though the MAE result means it should not be presented as uniformly better than the baseline.")
        download_csv(predictions, "model_holdout_predictions.csv")

city_rows, station_rows = row_counts()
st.sidebar.caption(f"SQLite rows: {city_rows:,} city-days | {station_rows:,} station-days")
