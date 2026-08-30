import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from plotly.subplots import make_subplots
from src.config import BASIN_COLORS, SEVERITY_COLORS
from src.i18n import get_text
from src.data_loader import calculate_map_bounds

def render_map_view(df: pd.DataFrame, lang: str):
    """Render interactive Plotly geospatial early warning map with Plotly 5/6 dual compatibility."""
    st.subheader(get_text(lang, "map_title"))

    if df.empty:
        st.info("No monitoring station data available for current selection.")
        return

    # Focus map on the latest status per station
    latest_df = df.sort_values("date").groupby("station_id", as_index=False).last()

    # Create marker size metric proportional to river level & risk score
    latest_df["marker_size"] = (latest_df["river_level_m"] * 2.2 + latest_df["flood_risk_score"] * 16).clip(lower=8, upper=30)

    # Hover text styling with high-contrast HTML formatting
    latest_df["hover_info"] = (
        "<b style='font-size:14px; color:#0F172A;'>" + latest_df["station_name"] + "</b><br>" +
        "<span style='color:#334155;'>" + get_text(lang, "hover_basin") + ": <b>" + latest_df["basin"] + "</b></span><br>" +
        "<span style='color:#334155;'>" + get_text(lang, "hover_country") + ": <b>" + latest_df["country"] + "</b></span><br>" +
        "<hr style='margin:4px 0; border-color:#CBD5E1;'/>" +
        "<span style='color:#0F172A;'>" + get_text(lang, "hover_risk") + ": <b style='color:#1E3A8A;'>" + (latest_df["flood_risk_score"] * 100).round(1).astype(str) + "%</b></span><br>" +
        "<span style='color:#334155;'>" + get_text(lang, "hover_severity") + ": <b>" + latest_df.get("severity_level", latest_df.get("alert_level", "Normal")).astype(str) + "</b></span><br>" +
        "<span style='color:#334155;'>" + get_text(lang, "hover_rainfall") + ": <b>" + latest_df["rainfall_mm"].astype(str) + " mm</b></span><br>" +
        "<span style='color:#334155;'>" + get_text(lang, "hover_river") + ": <b>" + latest_df["river_level_m"].astype(str) + " m</b></span><br>" +
        "<span style='color:#334155;'>" + get_text(lang, "hover_soil") + ": <b>" + latest_df["soil_moisture_percent"].astype(str) + " %</b></span><br>" +
        "<span style='color:#64748B; font-size:11px;'>" + get_text(lang, "hover_date") + ": " + latest_df["date"].dt.strftime("%Y-%m-%d") + "</span>"
    )

    # Dynamic auto-centering & bounding box zoom calculation
    center_lat, center_lon, map_zoom = calculate_map_bounds(latest_df)

    # Plotly 5.x / 6.x Dual Compatibility Map rendering
    if hasattr(px, "scatter_map"):
        fig = px.scatter_map(
            latest_df,
            lat="latitude",
            lon="longitude",
            color="basin",
            size="marker_size",
            color_discrete_map=BASIN_COLORS,
            hover_name="station_name",
            hover_data={"hover_info": True, "latitude": False, "longitude": False, "marker_size": False, "basin": False},
            zoom=map_zoom,
            center={"lat": center_lat, "lon": center_lon},
            map_style="carto-positron",
            height=580
        )
    else:
        fig = px.scatter_mapbox(
            latest_df,
            lat="latitude",
            lon="longitude",
            color="basin",
            size="marker_size",
            color_discrete_map=BASIN_COLORS,
            hover_name="station_name",
            hover_data={"hover_info": True, "latitude": False, "longitude": False, "marker_size": False, "basin": False},
            zoom=map_zoom,
            center={"lat": center_lat, "lon": center_lon},
            mapbox_style="carto-positron",
            height=580
        )

    fig.update_traces(
        hovertemplate="%{customdata[0]}<extra></extra>",
        marker=dict(opacity=0.92)
    )

    fig.update_layout(
        margin={"r": 0, "t": 10, "l": 0, "b": 0},
        hoverlabel=dict(
            bgcolor="rgba(255, 255, 255, 0.96)",
            font_size=12,
            font_family="Inter, system-ui, sans-serif",
            font_color="#0F172A",
            bordercolor="#CBD5E1"
        ),
        legend=dict(
            title=dict(text=get_text(lang, "map_legend"), font=dict(color="#0F172A", size=12, family="Inter, sans-serif")),
            orientation="h",
            yanchor="bottom",
            y=0.02,
            xanchor="left",
            x=0.02,
            bgcolor="rgba(255, 255, 255, 0.95)",
            bordercolor="#CBD5E1",
            borderwidth=1,
            font=dict(color="#0F172A", size=11)
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------------
    # DRILL-DOWN STATION INSPECTOR & DETAIL VIEW
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader(get_text(lang, "station_inspector_title"))

    station_options = sorted(latest_df["station_name"].unique().tolist())
    selected_station = st.selectbox(
        get_text(lang, "select_station_inspect"),
        options=station_options,
        index=0
    )

    if selected_station:
        station_ts = df[df["station_name"] == selected_station].sort_values("date")
        latest_row = station_ts.iloc[-1]

        # Station Metadata & Metrics
        st_name = latest_row["station_name"]
        st_id = latest_row["station_id"]
        basin_name = latest_row["basin"]
        country_name = latest_row["country"]
        lat_val = float(latest_row["latitude"])
        lon_val = float(latest_row["longitude"])

        gauge_m = float(latest_row["river_level_m"])
        rain_mm = float(latest_row["rainfall_mm"])
        soil_pct = float(latest_row["soil_moisture_percent"])
        temp_c = float(latest_row.get("temperature_c", latest_row.get("temperature_celsius", 28.5)))

        risk_score = float(latest_row["flood_risk_score"])
        prob_pct = round(risk_score * 100, 1)
        severity = str(latest_row.get("severity_level", latest_row.get("alert_level", "Normal")))

        # Badging colors
        if risk_score < 0.46:
            badge_bg, badge_txt = "#D1FAE5", "#065F46"
        elif risk_score < 0.70:
            badge_bg, badge_txt = "#FEF3C7", "#92400E"
        elif risk_score < 0.92:
            badge_bg, badge_txt = "#FFEDD5", "#9A3412"
        else:
            badge_bg, badge_txt = "#FEE2E2", "#991B1B"

        # Contextual explanation logic
        if len(station_ts) > 1:
            prev_gauge = float(station_ts.iloc[-2]["river_level_m"])
            surge_24h = gauge_m - prev_gauge
        else:
            surge_24h = 0.0

        if soil_pct > 75 and rain_mm > 70:
            driver_text = f"Severe soil saturation ({soil_pct:.1f}%) combined with high 24h rainfall ({rain_mm:.1f} mm) is suppressing infiltration, accelerating surface runoff surge into {basin_name}."
        elif gauge_m > 7.5:
            driver_text = f"River gauge level ({gauge_m:.2f} m) has breached baseline operating thresholds, experiencing a 24h surge rate of +{surge_24h:.2f} m."
        elif rain_mm > 90:
            driver_text = f"Intense localized precipitation ({rain_mm:.1f} mm/24h) is the primary risk driver for {st_name}."
        else:
            driver_text = f"Hydrological parameters are operating within baseline limits. Soil saturation is at {soil_pct:.1f}% with stable gauge readings."

        # Inspector Layout Cards
        col_meta, col_diag = st.columns([1, 1])

        with col_meta:
            st.markdown(
                f"""
                <div class="station-inspector-card">
                    <div class="station-inspector-header">
                        <div>
                            <div class="station-title">{st_name} ({st_id})</div>
                            <div class="station-subtitle">{basin_name} | {country_name} | Coordinates: {lat_val:.4f}°N, {lon_val:.4f}°E</div>
                        </div>
                        <span class="badge" style="background-color: {badge_bg}; color: {badge_txt}; font-size: 0.85rem; padding: 6px 12px;">
                            {severity}
                        </span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 16px;">
                        <div class="metric-pill">
                            <div class="metric-pill-title">{get_text(lang, 'chart_river_axis')}</div>
                            <div class="metric-pill-val">{gauge_m:.2f} m</div>
                        </div>
                        <div class="metric-pill">
                            <div class="metric-pill-title">{get_text(lang, 'chart_rainfall_axis')}</div>
                            <div class="metric-pill-val">{rain_mm:.1f} mm</div>
                        </div>
                        <div class="metric-pill">
                            <div class="metric-pill-title">{get_text(lang, 'hover_soil')}</div>
                            <div class="metric-pill-val">{soil_pct:.1f} %</div>
                        </div>
                        <div class="metric-pill">
                            <div class="metric-pill-title">Temperature</div>
                            <div class="metric-pill-val">{temp_c:.1f} °C</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col_diag:
            st.markdown(
                f"""
                <div class="station-inspector-card">
                    <div style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: #64748B; margin-bottom: 6px;">
                        {get_text(lang, 'predictive_assessment')}
                    </div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: #0F172A; margin-bottom: 8px;">
                        {prob_pct}% <span style="font-size: 0.9rem; font-weight: 500; color: #475569;">({get_text(lang, 'action_threshold_label')}: 70.0%)</span>
                    </div>
                    <div style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; color: #64748B; margin-top: 14px; margin-bottom: 6px;">
                        {get_text(lang, 'driver_explanation')}
                    </div>
                    <div style="font-size: 0.95rem; color: #1E293B; line-height: 1.5; font-weight: 400; background: #F8FAFC; border-left: 4px solid #2563EB; padding: 12px; border-radius: 4px;">
                        {driver_text}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # High-resolution time-series trend line for selected station
        st.markdown(f"#### {get_text(lang, 'historical_forecast_trend')}: {st_name}")
        
        recent_ts = station_ts.tail(90)

        trend_fig = make_subplots(specs=[[{"secondary_y": True}]])

        trend_fig.add_trace(
            go.Bar(
                x=recent_ts["date"],
                y=recent_ts["rainfall_mm"],
                name=get_text(lang, "chart_rainfall_axis"),
                marker_color="rgba(37, 99, 235, 0.45)",
                hovertemplate="%{x|%Y-%m-%d}<br>Rainfall: %{y:.1f} mm<extra></extra>"
            ),
            secondary_y=False
        )

        trend_fig.add_trace(
            go.Scatter(
                x=recent_ts["date"],
                y=recent_ts["river_level_m"],
                name=get_text(lang, "chart_river_axis"),
                mode="lines+markers",
                line=dict(color="#DC2626", width=2.5),
                marker=dict(size=4),
                hovertemplate="%{x|%Y-%m-%d}<br>River Gauge: %{y:.2f} m<extra></extra>"
            ),
            secondary_y=True
        )

        # Warning threshold line on gauge axis
        trend_fig.add_hline(
            y=8.0,
            line_dash="dash",
            line_color="#F97316",
            annotation_text="Severe Gauge Warning (8.0 m)",
            annotation_position="top left",
            secondary_y=True
        )

        trend_fig.update_xaxes(title_text="Date Window", showgrid=True, gridcolor="#E2E8F0")
        trend_fig.update_yaxes(title_text=get_text(lang, "chart_rainfall_axis"), secondary_y=False, showgrid=True, gridcolor="#E2E8F0")
        trend_fig.update_yaxes(title_text=get_text(lang, "chart_river_axis"), secondary_y=True, showgrid=False)

        trend_fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#0F172A")),
            height=380,
            margin=dict(l=20, r=20, t=30, b=20),
            hovermode="x unified",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )

        st.plotly_chart(trend_fig, use_container_width=True)
