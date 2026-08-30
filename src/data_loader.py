import os
import json
import joblib
import pandas as pd
import streamlit as st
from src.config import (
    PROCESSED_DATA_PATH,
    FALLBACK_DATA_PATH,
    ALERT_CONFIG_PATH,
    MODEL_PATH,
    FALLBACK_MODEL_PATH,
    HISTORICAL_BASELINES
)

@st.cache_data(ttl=3600)
def load_dataset():
    """Load the hydro-meteorological 25-year dataset."""
    path = PROCESSED_DATA_PATH if os.path.exists(PROCESSED_DATA_PATH) else FALLBACK_DATA_PATH
    if not os.path.exists(path):
        st.error(f"Dataset not found at {path}. Please run `python scripts/generate_data_and_model.py` first.")
        return pd.DataFrame()
    
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df

@st.cache_resource
def load_model():
    """Load trained Scikit-learn flood early warning pipeline model."""
    path = MODEL_PATH if os.path.exists(MODEL_PATH) else FALLBACK_MODEL_PATH
    if not os.path.exists(path):
        st.error(f"Model file not found at {path}.")
        return None
    try:
        model = joblib.load(path)
        return model
    except Exception as e:
        st.error(f"Failed to load joblib model: {e}")
        return None

@st.cache_data
def load_alert_config():
    """Load alert thresholds and severity configuration."""
    if os.path.exists(ALERT_CONFIG_PATH):
        with open(ALERT_CONFIG_PATH, "r") as f:
            return json.load(f)
    return {
        "model_name": "Logistic Regression",
        "optimal_threshold": 0.70,
        "alert_levels": {
            "Normal (Green)": [0.0, 0.46],
            "Warning (Yellow)": [0.46, 0.70],
            "Severe (Orange)": [0.70, 0.92],
            "Critical (Red)": [0.92, 1.0]
        }
    }

def filter_dataset(df, basin=None, country=None, station=None, start_date=None, end_date=None):
    """Filter dataframe by basin, country, station, and date range."""
    if df.empty:
        return df

    filtered = df.copy()

    if basin and basin != "All Basins / Countries" and basin != "ลุ่มน้ำ/ประเทศ ทั้งหมด":
        filtered = filtered[filtered["basin"] == basin]

    if country and country != "All Basins / Countries" and country != "ลุ่มน้ำ/ประเทศ ทั้งหมด":
        filtered = filtered[filtered["country"] == country]

    if station and station != "All Stations" and station != "สถานี ทั้งหมด":
        filtered = filtered[filtered["station_name"] == station]

    if start_date:
        filtered = filtered[filtered["date"] >= pd.to_datetime(start_date)]

    if end_date:
        filtered = filtered[filtered["date"] <= pd.to_datetime(end_date)]

    return filtered

def compute_kpis(df):
    """Compute executive summary KPI metrics and delta percentages vs baseline."""
    if df.empty:
        return {
            "total_stations": 0,
            "critical_alerts": 0,
            "avg_rainfall": 0.0,
            "rainfall_delta": 0.0,
            "avg_river_level": 0.0,
            "river_delta": 0.0,
            "mean_risk_score": 0.0,
            "risk_delta": 0.0
        }

    latest_date = df["date"].max()
    # Focus latest status on the most recent sampled time slice
    latest_df = df[df["date"] == latest_date]

    total_stations = latest_df["station_id"].nunique()
    critical_alerts = latest_df[latest_df["severity_level"].isin(["Severe (Orange)", "Critical (Red)"])]["station_id"].nunique()

    avg_rainfall = round(df["rainfall_mm"].mean(), 1)
    avg_river_level = round(df["river_level_m"].mean(), 2)
    mean_risk_score = round(df["flood_risk_score"].mean(), 3)

    rainfall_delta = round(((avg_rainfall - HISTORICAL_BASELINES["rainfall_mm"]) / HISTORICAL_BASELINES["rainfall_mm"]) * 100, 1)
    river_delta = round(((avg_river_level - HISTORICAL_BASELINES["river_level_m"]) / HISTORICAL_BASELINES["river_level_m"]) * 100, 1)
    risk_delta = round(((mean_risk_score - HISTORICAL_BASELINES["flood_risk_score"]) / HISTORICAL_BASELINES["flood_risk_score"]) * 100, 1)

    return {
        "total_stations": total_stations,
        "critical_alerts": critical_alerts,
        "avg_rainfall": avg_rainfall,
        "rainfall_delta": rainfall_delta,
        "avg_river_level": avg_river_level,
        "river_delta": river_delta,
        "mean_risk_score": mean_risk_score,
        "risk_delta": risk_delta
    }

def get_cascading_options(df: pd.DataFrame, country: str = None, basin: str = None, all_label: str = "All Basins / Countries", all_stations_label: str = "All Stations"):
    """
    Compute dependent/cascading filter choices for Country, Basin, and Station.
    When a specific country (e.g. "Thailand") is selected, dynamically narrow down available Basins and Stations.
    """
    if df.empty:
        return [all_label], [all_label], [all_stations_label]

    # All available countries
    all_countries = [all_label] + sorted(df["country"].dropna().unique().tolist())

    # If country selected, filter basins
    if country and country != all_label:
        country_df = df[df["country"] == country]
        available_basins = [all_label] + sorted(country_df["basin"].dropna().unique().tolist())
    else:
        country_df = df
        available_basins = [all_label] + sorted(df["basin"].dropna().unique().tolist())

    # If basin selected as well, filter stations
    if basin and basin != all_label:
        station_df = country_df[country_df["basin"] == basin]
    else:
        station_df = country_df

    available_stations = [all_stations_label] + sorted(station_df["station_name"].dropna().unique().tolist())

    return all_countries, available_basins, available_stations

def calculate_map_bounds(df: pd.DataFrame):
    """
    Calculate centroid (mean_lat, mean_lon) and optimal zoom level for dynamic map auto-centering.
    """
    if df.empty:
        return 20.0, 98.0, 3.8

    min_lat, max_lat = float(df["latitude"].min()), float(df["latitude"].max())
    min_lon, max_lon = float(df["longitude"].min()), float(df["longitude"].max())

    mean_lat = (min_lat + max_lat) / 2.0
    mean_lon = (min_lon + max_lon) / 2.0

    lat_span = abs(max_lat - min_lat)
    lon_span = abs(max_lon - min_lon)
    max_span = max(lat_span, lon_span)

    if max_span < 0.01:
        zoom = 9.5
    elif max_span < 1.0:
        zoom = 7.5
    elif max_span < 3.0:
        zoom = 6.2
    elif max_span < 7.0:
        zoom = 5.2
    elif max_span < 15.0:
        zoom = 4.2
    else:
        zoom = 3.8

    return round(mean_lat, 4), round(mean_lon, 4), zoom

