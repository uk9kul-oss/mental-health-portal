from __future__ import annotations

import io
import random
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from clean_data import DISORDER_COLUMNS, load_and_clean_data


DATA_FILE = Path("1- mental-illnesses-prevalence.csv")

NEWS_ITEMS = [
    {
        "title": "World Health Organization - Mental health",
        "url": "https://www.who.int/health-topics/mental-health",
    },
    {
        "title": "NIMH - Mental Health Information",
        "url": "https://www.nimh.nih.gov/health",
    },
    {
        "title": "CDC - Mental Health",
        "url": "https://www.cdc.gov/mentalhealth/index.htm",
    },
]

AWARENESS_POINTS = [
    "Mental health conditions are common and treatable.",
    "Early support often improves long-term outcomes.",
    "Regular sleep, movement, and social support can reduce stress burden.",
    "Seeking professional help is a strength, not a weakness.",
    "Community stigma reduction improves care access and recovery.",
]

FOOD_FOR_THOUGHT = [
    "If your organization tracked stress like a business KPI, what would change?",
    "How do socioeconomic factors amplify mental health inequities?",
    "What would prevention-first mental healthcare look like in schools?",
    "Can digital tools improve access without reducing human connection?",
    "How can workplaces make mental wellbeing measurable and actionable?",
]

DEFAULT_THEME = {
    "plotly_template": "plotly_dark",
    "accent": "#d61f60",
    "background": "linear-gradient(135deg, #141226 0%, #1c1a33 45%, #221a2f 100%)",
    "card_bg": "#222038",
    "text": "#f1f1f4",
    "muted_text": "#b7b5c6",
    "visual_palette": ["#d61f60", "#ff6fa8", "#f45a7f", "#ff9dc1", "#b64878", "#e2577a"],
    "heatmap_scale": [
        [0.0, "#1f1c31"],
        [0.5, "#4a2748"],
        [1.0, "#d61f60"],
    ],
}


@st.cache_data
def get_clean_data(file_path: str) -> pd.DataFrame:
    return load_and_clean_data(file_path)


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="report")
    return output.getvalue()


def to_pdf_bytes(title: str, summary_rows: list[tuple[str, str]], table_df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, 760, title)

    c.setFont("Helvetica", 10)
    y = 735
    for key, value in summary_rows:
        c.drawString(40, y, f"{key}: {value}")
        y -= 16

    y -= 8
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Data preview")
    y -= 16

    c.setFont("Helvetica", 8)
    preview = table_df.head(15).copy()
    headers = " | ".join(preview.columns.astype(str).tolist())
    c.drawString(40, y, headers[:120])
    y -= 12
    for _, row in preview.iterrows():
        line = " | ".join(row.astype(str).tolist())
        c.drawString(40, y, line[:120])
        y -= 12
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 8)
            y = 760

    c.save()
    buffer.seek(0)
    return buffer.read()


def apply_theme(theme: dict[str, str]) -> None:
    st.markdown(
        f"""
        <style>
            .stApp {{
                background: {theme["background"]};
                color: {theme["text"]};
                background-attachment: fixed;
            }}
            .stApp::before {{
                content: "";
                position: fixed;
                inset: 0;
                pointer-events: none;
                background:
                    radial-gradient(circle at 10% 20%, {theme["accent"]}26 0%, transparent 36%),
                    radial-gradient(circle at 85% 15%, {theme["accent"]}1A 0%, transparent 30%),
                    radial-gradient(circle at 80% 85%, #ffffff66 0%, transparent 32%);
                z-index: 0;
            }}
            .main .block-container {{
                position: relative;
                z-index: 1;
                background: rgba(18, 16, 30, 0.88);
                border: 1px solid {theme["accent"]}3A;
                border-radius: 18px;
                padding: 1.2rem 1.2rem 1rem 1.2rem;
                box-shadow: 0 18px 36px rgba(0, 0, 0, 0.32);
            }}
            .portal-card {{
                padding: 12px;
                border-radius: 12px;
                border: 1px solid {theme["accent"]}55;
                background: {theme["card_bg"]};
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.28);
            }}
            h1, h2, h3, p, label {{
                color: {theme["text"]};
            }}
            [data-testid="stSidebar"] {{
                background: rgba(18, 16, 30, 0.92);
                border-right: 1px solid {theme["accent"]}33;
            }}
            [data-testid="stSidebar"] * {{
                color: {theme["text"]};
            }}
            [data-baseweb="tab-list"] button {{
                color: {theme["text"]} !important;
                font-weight: 700 !important;
            }}
            [data-testid="stAlert"] {{
                color: {theme["text"]} !important;
            }}
            [data-testid="stAlert"] * {{
                color: {theme["text"]} !important;
            }}
            [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{
                color: {theme["text"]};
            }}
            [data-testid="stCaption"] {{
                color: {theme["muted_text"]};
            }}
            .stButton>button, .stDownloadButton>button {{
                border: 1px solid {theme["accent"]}88;
                border-radius: 10px;
                background: rgba(34, 32, 56, 0.9);
                color: {theme["text"]};
                font-weight: 600;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def style_figure(fig, theme: dict[str, str]):
    fig.update_layout(
        template=theme["plotly_template"],
        font=dict(color=theme["text"]),
        title_font=dict(color=theme["text"], size=20),
        legend_font=dict(color=theme["text"]),
        plot_bgcolor="#ffffff",
        paper_bgcolor=theme["card_bg"],
    )
    return fig


def chart_jpeg_bytes(df: pd.DataFrame, country: str, metric: str, accent: str) -> bytes:
    chart_df = df[df["Entity"] == country][["Year", metric]].sort_values("Year")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(chart_df["Year"], chart_df[metric], color=accent, linewidth=2)
    ax.set_title(f"{country}: {metric.title()} trend")
    ax.set_xlabel("Year")
    ax.set_ylabel("Share of population")
    ax.grid(True, alpha=0.25)
    img_buffer = io.BytesIO()
    plt.tight_layout()
    fig.savefig(img_buffer, format="jpeg", dpi=150)
    plt.close(fig)
    img_buffer.seek(0)
    return img_buffer.read()


def build_prediction(country_df: pd.DataFrame, metric: str, horizon: int) -> pd.DataFrame:
    model_df = country_df[["Year", metric]].dropna().copy()
    x = model_df[["Year"]].to_numpy()
    y = model_df[metric].to_numpy()

    lr = LinearRegression()
    lr.fit(x, y)

    max_year = int(model_df["Year"].max())
    future_years = list(range(max_year + 1, max_year + horizon + 1))
    prediction = lr.predict(pd.Series(future_years).to_numpy().reshape(-1, 1))
    return pd.DataFrame({"Year": future_years, f"{metric}_predicted": prediction})


def build_ts_forecast(country_df: pd.DataFrame, metric: str, horizon: int) -> pd.DataFrame:
    ts = country_df[["Year", metric]].dropna().sort_values("Year")
    values = ts[metric].to_numpy()
    max_year = int(ts["Year"].max())

    if len(values) < 3:
        # Fallback forecast when not enough points for a stable TS fit.
        forecast = [float(values[-1])] * horizon
    else:
        model = ExponentialSmoothing(values, trend="add", seasonal=None, initialization_method="estimated")
        fit = model.fit(optimized=True)
        forecast = fit.forecast(horizon)
    years = list(range(max_year + 1, max_year + horizon + 1))

    return pd.DataFrame({"Year": years, f"{metric}_ts_forecast": forecast})


def main() -> None:
    st.set_page_config(page_title="Mental Health Portal", layout="wide")
    st.title("Mental Health Data Portal")
    st.caption("Dashboard, prediction, time-series analysis, and report export")

    if not DATA_FILE.exists():
        st.error(f"Data file not found: {DATA_FILE}")
        return

    df = get_clean_data(str(DATA_FILE))
    apply_theme(DEFAULT_THEME)

    countries = sorted(df["Entity"].unique().tolist())
    metrics = DISORDER_COLUMNS + ["total_burden"]

    st.sidebar.header("Filters")
    selected_country = st.sidebar.selectbox("Country", countries)
    selected_metric = st.sidebar.selectbox("Metric", metrics, index=1)
    year_min = int(df["Year"].min())
    year_max = int(df["Year"].max())
    forecast_end_year = 2030
    horizon_years = max(1, forecast_end_year - year_max)
    year_range = st.sidebar.slider("Year range", year_min, year_max, (year_min, year_max))

    filtered = df[
        (df["Entity"] == selected_country)
        & (df["Year"] >= year_range[0])
        & (df["Year"] <= year_range[1])
    ].copy()

    if filtered.empty:
        st.warning("No data found for the selected filters. Adjust country or year range.")
        return

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Dashboard", "Prediction", "Time Series", "Insights Hub", "Stress Calculator"]
    )

    with tab1:
        col1, col2, col3 = st.columns(3)
        latest = filtered.sort_values("Year").tail(1)
        if not latest.empty:
            col1.metric("Latest year", int(latest["Year"].iloc[0]))
            col2.metric(f"{selected_metric} (%)", f"{latest[selected_metric].iloc[0]:.3f}")
            col3.metric("Total burden (%)", f"{latest['total_burden'].iloc[0]:.3f}")

        fig = px.line(
            filtered,
            x="Year",
            y=selected_metric,
            title=f"{selected_country}: {selected_metric.title()} over time",
            markers=True,
        )
        fig = style_figure(fig, DEFAULT_THEME)
        fig.update_traces(line=dict(color=DEFAULT_THEME["accent"], width=3))
        st.plotly_chart(fig, use_container_width=True)

        v1, v2 = st.columns(2)
        with v1:
            st.markdown("<div class='portal-card'>", unsafe_allow_html=True)
            all_metric_trend = px.line(
                filtered,
                x="Year",
                y=DISORDER_COLUMNS,
                title="All disorders trend",
                color_discrete_sequence=DEFAULT_THEME["visual_palette"],
            )
            all_metric_trend = style_figure(all_metric_trend, DEFAULT_THEME)
            st.plotly_chart(all_metric_trend, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with v2:
            latest_row = filtered.sort_values("Year").tail(1)
            if not latest_row.empty:
                pie_df = latest_row[DISORDER_COLUMNS].T.reset_index()
                pie_df.columns = ["Disorder", "Value"]
                st.markdown("<div class='portal-card'>", unsafe_allow_html=True)
                donut = px.pie(
                    pie_df,
                    names="Disorder",
                    values="Value",
                    hole=0.45,
                    title=f"{int(latest_row['Year'].iloc[0])} composition",
                    color_discrete_sequence=DEFAULT_THEME["visual_palette"],
                )
                donut = style_figure(donut, DEFAULT_THEME)
                st.plotly_chart(donut, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

        heatmap_data = filtered.set_index("Year")[DISORDER_COLUMNS]
        heatmap_fig = px.imshow(
            heatmap_data.T,
            aspect="auto",
            color_continuous_scale=DEFAULT_THEME["heatmap_scale"],
            title="Disorder intensity heatmap by year",
            labels={"x": "Year", "y": "Disorder", "color": "Share (%)"},
        )
        heatmap_fig = style_figure(heatmap_fig, DEFAULT_THEME)
        st.plotly_chart(heatmap_fig, use_container_width=True)

        st.subheader("Cleaned data preview")
        st.dataframe(filtered, use_container_width=True)

    with tab2:
        st.subheader("Linear Regression Prediction")
        horizon = horizon_years
        st.caption(f"Forecasting through {forecast_end_year}.")

        pred_df = build_prediction(filtered, selected_metric, horizon)
        merged = filtered[["Year", selected_metric]].merge(pred_df, on="Year", how="outer")

        fig_pred = px.line(
            merged,
            x="Year",
            y=[selected_metric, f"{selected_metric}_predicted"],
            markers=True,
            color_discrete_sequence=[DEFAULT_THEME["accent"], DEFAULT_THEME["visual_palette"][1]],
        )
        fig_pred = style_figure(fig_pred, DEFAULT_THEME)
        st.plotly_chart(fig_pred, use_container_width=True)
        st.dataframe(pred_df, use_container_width=True)

    with tab3:
        st.subheader("Time Series Analysis")
        filtered["rolling_3y"] = filtered[selected_metric].rolling(3, min_periods=1).mean()
        filtered["yoy_change_pct"] = filtered[selected_metric].pct_change() * 100

        ts_horizon = horizon_years
        st.caption(f"Forecasting through {forecast_end_year}.")
        ts_forecast = build_ts_forecast(filtered, selected_metric, ts_horizon)
        combined = filtered[["Year", selected_metric, "rolling_3y"]].merge(ts_forecast, on="Year", how="outer")

        fig_ts = px.line(
            combined,
            x="Year",
            y=[selected_metric, "rolling_3y", f"{selected_metric}_ts_forecast"],
            markers=True,
            title="Historical trend + rolling mean + forecast",
            color_discrete_sequence=[
                DEFAULT_THEME["accent"],
                DEFAULT_THEME["visual_palette"][2],
                DEFAULT_THEME["visual_palette"][1],
            ],
        )
        fig_ts = style_figure(fig_ts, DEFAULT_THEME)
        st.plotly_chart(fig_ts, use_container_width=True)

        st.subheader("Year-over-year change (%)")
        st.dataframe(filtered[["Year", selected_metric, "yoy_change_pct"]], use_container_width=True)

    with tab4:
        st.subheader("News")
        for item in NEWS_ITEMS:
            st.markdown(f"- [{item['title']}]({item['url']})")

        st.subheader("Awareness")
        for point in AWARENESS_POINTS:
            st.write(f"- {point}")

        st.subheader("Food for Thought")
        st.info(random.choice(FOOD_FOR_THOUGHT))
        if st.button("New thought"):
            st.success(random.choice(FOOD_FOR_THOUGHT))

    with tab5:
        st.subheader("Mental Stress Calculator")
        st.caption("Quick self-check. This is not a medical diagnosis.")

        c1, c2 = st.columns(2)
        with c1:
            stress_level = st.slider("Perceived stress level (last 7 days)", 0, 10, 5)
            sleep_quality = st.slider("Sleep quality", 0, 10, 6)
            energy_level = st.slider("Energy level", 0, 10, 6)
        with c2:
            mood_level = st.slider("Mood stability", 0, 10, 6)
            workload_pressure = st.slider("Work/school pressure", 0, 10, 5)

        # Higher stress/pressure increases score; higher wellbeing buffers reduce it.
        score = (
            stress_level * 20
            + workload_pressure * 18
            + (10 - sleep_quality) * 16
            + (10 - energy_level) * 14
            + (10 - mood_level) * 12
        )

        score = max(0, min(100, round(score / 8)))
        st.metric("Stress score (0-100)", score)

        if score >= 70:
            st.error("High stress indicated. Consider reaching out to a professional or trusted person.")
            st.markdown(
                "- Suggestions: pause non-urgent tasks, sleep and hydration first, try a short walk, "
                "and reach out to someone you trust today."
            )
        elif score >= 40:
            st.warning("Moderate stress indicated. Try rest, routine, and support to lower strain.")
            st.markdown(
                "- Suggestions: plan one small break, reduce multitasking, do 10 minutes of breathing, "
                "and aim for consistent sleep."
            )
        else:
            st.success("Low stress indicated. Keep up the healthy habits.")
            st.markdown(
                "- Suggestions: keep your routine, add a brief daily activity you enjoy, "
                "and check in with yourself weekly."
            )

        st.info(
            "If you feel overwhelmed or unsafe, seek help from local emergency services or a licensed professional."
        )

    st.divider()
    st.subheader("Export Reports")

    report_df = filtered.copy()
    csv_bytes = report_df.to_csv(index=False).encode("utf-8")
    excel_bytes = to_excel_bytes(report_df)
    pdf_bytes = to_pdf_bytes(
        title="Mental Health Report",
        summary_rows=[
            ("Country", selected_country),
            ("Metric", selected_metric),
            ("Year range", f"{year_range[0]} - {year_range[1]}"),
            ("Rows", str(len(report_df))),
        ],
        table_df=report_df,
    )
    jpeg_bytes = chart_jpeg_bytes(df, selected_country, selected_metric, DEFAULT_THEME["accent"])

    e1, e2, e3, e4 = st.columns(4)
    e1.download_button(
        "Download CSV",
        data=csv_bytes,
        file_name=f"{selected_country}_{selected_metric}_report.csv",
        mime="text/csv",
    )
    e2.download_button(
        "Download Excel",
        data=excel_bytes,
        file_name=f"{selected_country}_{selected_metric}_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    e3.download_button(
        "Download PDF",
        data=pdf_bytes,
        file_name=f"{selected_country}_{selected_metric}_report.pdf",
        mime="application/pdf",
    )
    e4.download_button(
        "Download image.jpeg",
        data=jpeg_bytes,
        file_name="image.jpeg",
        mime="image/jpeg",
    )


if __name__ == "__main__":
    main()
