import os

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")

# Primary Parquet path
PROCESSED_DATA_PATH = os.path.join(DATA_DIR, "asia_flood_dashboard_data.parquet")
FALLBACK_DATA_PATH = os.path.join(DATA_DIR, "asia_flood_dashboard_data.parquet")

# Candidate paths list for resilient dataset auto-detection
DATASET_CANDIDATE_PATHS = [
    os.path.join(PROCESSED_DATA_DIR, "asia_flood_dashboard_data.parquet"),
    os.path.join(DATA_DIR, "asia_flood_dashboard_data.parquet"),
    os.path.join(BASE_DIR, "asia_flood_dashboard_data.parquet"),
    os.path.join(PROCESSED_DATA_DIR, "asia_flood_dashboard_data.csv"),
    os.path.join(DATA_DIR, "asia_flood_dashboard_data.csv"),
    os.path.join(BASE_DIR, "asia_flood_dashboard_data.csv"),
]

# Candidate paths list for trained ML model pipeline auto-detection
MODEL_CANDIDATE_PATHS = [
    os.path.join(BASE_DIR, "models", "flood_early_warning_pipeline.joblib"),
    os.path.join(PROCESSED_DATA_DIR, "flood_early_warning_pipeline.joblib"),
    os.path.join(DATA_DIR, "flood_early_warning_pipeline.joblib"),
    os.path.join(BASE_DIR, "flood_early_warning_pipeline.joblib"),
]

MODEL_PATH = MODEL_CANDIDATE_PATHS[0]
FALLBACK_MODEL_PATH = MODEL_CANDIDATE_PATHS[2]

# Candidate paths list for alert configuration auto-detection
ALERT_CONFIG_CANDIDATE_PATHS = [
    os.path.join(PROCESSED_DATA_DIR, "alert_config.json"),
    os.path.join(DATA_DIR, "alert_config.json"),
    os.path.join(BASE_DIR, "alert_config.json"),
]

ALERT_CONFIG_PATH = ALERT_CONFIG_CANDIDATE_PATHS[0]

# Color palette mapping for severity levels
SEVERITY_COLORS = {
    "Normal (Green)": "#10B981",    # Emerald Green
    "Warning (Yellow)": "#F59E0B",   # Amber Gold
    "Severe (Orange)": "#F97316",    # Warm Orange
    "Critical (Red)": "#EF4444"      # Crimson Red
}

SEVERITY_BG_LIGHT = {
    "Normal (Green)": "#D1FAE5",
    "Warning (Yellow)": "#FEF3C7",
    "Severe (Orange)": "#FFEDD5",
    "Critical (Red)": "#FEE2E2"
}

# Color palette mapping for river basins
BASIN_COLORS = {
    "Mekong Basin": "#1E40AF",          # Deep Blue
    "Chao Phraya Basin": "#0D9488",     # Deep Teal
    "Ganges-Brahmaputra": "#D97706",    # Amber / Ochre
    "Yangtze River": "#4F46E5",         # Indigo
    "Indus River": "#059669",           # Emerald
    "Irrawaddy Basin": "#9333EA",       # Purple
    "Red River Basin": "#DC2626"        # Ruby Red
}

# Basins list
BASINS = [
    "Mekong Basin",
    "Chao Phraya Basin",
    "Ganges-Brahmaputra",
    "Yangtze River",
    "Indus River",
    "Irrawaddy Basin",
    "Red River Basin"
]

# Baseline historical metrics for delta comparisons
HISTORICAL_BASELINES = {
    "rainfall_mm": 48.5,
    "river_level_m": 6.80,
    "soil_moisture_percent": 65.2,
    "flood_risk_score": 0.38
}
