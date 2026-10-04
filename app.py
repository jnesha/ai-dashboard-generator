import streamlit as st
import pandas as pd
import plotly.express as px
from data_profiler import profile_dataframe
from ai_analyzer import get_chart_recommendations, answer_question
from report_builder import build_pdf_report

st.set_page_config(page_title="AI Dashboard Generator", layout="wide")

def render_kpi(df: pd.DataFrame, kpi: dict):
    col = kpi.get("column")
    agg = kpi.get("agg", "count")
    label = kpi.get("label", col)

    if col not in df.columns:
        return None

    try:
        if agg == "sum":
            value = df[col].sum()
        elif agg == "mean":
            value = df[col].mean()
        elif agg == "count":
            value = len(df)
        elif agg == "max":
            value = df[col].max()
        elif agg == "min":
            value = df[col].min()
        else:
            return None

        if isinstance(value, float):
            value = round(value, 2)
        return label, f"{value:,}" if isinstance(value, (int, float)) else str(value)

    except Exception:
        return None

def render_dashboard_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Renders filter controls inline (not in the sidebar), only for columns
    that are genuinely low-cardinality categories — not names, IDs, or dates,
    which are near-unique per row and make bad filters."""
    filterable_cols = [
        col for col in df.columns
        if not pd.api.types.is_numeric_dtype(df[col])
        and df[col].nunique() <= 15
        and df[col].nunique() < len(df) * 0.5
    ]

    filtered_df = df.copy()
    if not filterable_cols:
        return filtered_df

    with st.expander("🔍 Filter dashboard", expanded=False):
        cols = st.columns(min(len(filterable_cols), 3))
        for i, col in enumerate(filterable_cols):
            options = sorted(df[col].dropna().unique().tolist())
            with cols[i % len(cols)]:
                selected = st.multiselect(col, options, default=options, key=f"filter_{col}")
            if selected:
                filtered_df = filtered_df[filtered_df[col].isin(selected)]

    return filtered_df

def build_chart_figure(df: pd.DataFrame, chart: dict):
    """Builds the Plotly figure for a chart spec, or returns None if it
    can't be built. Separated from rendering so the same figure can be
    both displayed on-screen and exported as an image for the PDF report."""
    chart_type = chart.get("type")
    x = chart.get("x")
    y = chart.get("y")
    title = chart.get("title", "")

    if x not in df.columns:
        return None

    try:
        if chart_type == "bar":
            if y and y in df.columns:
                fig = px.bar(df, x=x, y=y, title=title)
            else:
                counts = df[x].value_counts().reset_index()
                counts.columns = [x, "count"]
                fig = px.bar(counts, x=x, y="count", title=title)
        elif chart_type == "line":
            fig = px.line(df, x=x, y=y, title=title)
        elif chart_type == "scatter":
            fig = px.scatter(df, x=x, y=y, title=title)
        elif chart_type == "histogram":
            fig = px.histogram(df, x=x, title=title)
        else:
            return None
        return fig
    except Exception:
        return None

st.title("AI-Powered Dashboard Generator")
st.caption(
    "Upload any CSV. Claude profiles your data, decides what's worth "
    "visualizing, and the dashboard builds itself."
)

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

df_full = None
load_error = None

if uploaded_file is not None:
    try:
        df_full = pd.read_csv(uploaded_file)
    except Exception as e:
        load_error = f"Couldn't read this file as a CSV: {e}"

if load_error:
    st.error(
        f"{load_error}\n\nMake sure the file is a valid CSV (comma-separated, "
        "UTF-8 encoded). Try opening it in Excel/Numbers and re-saving as CSV "
        "if you're unsure."
    )

if df_full is not None:
    st.success(f"Loaded {len(df_full):,} rows, {len(df_full.columns)} columns")

    with st.expander("Preview raw data"):
        st.dataframe(df_full.head(20))

    focus = st.text_input(
        "What should the dashboard focus on? (optional)",
        placeholder="e.g. revenue by region, customer satisfaction drivers...",
    )

    if st.button("Generate Dashboard", type="primary"):
        profile = profile_dataframe(df_full)
        with st.spinner("Asking Claude what's worth visualizing..."):
            result = get_chart_recommendations(profile, focus=focus)
            st.session_state["recommendations"] = result if result is not None else "failed"

    recommendations = st.session_state.get("recommendations")

    if recommendations is None:
        pass
    elif recommendations == "failed":
        st.error(
            "Couldn't get AI recommendations. Check that ANTHROPIC_API_KEY "
            "is set (see README for setup)."
        )
    else:
        st.subheader("Key Insights")
        st.write(recommendations.get("summary", "No summary returned."))

        st.subheader("Dashboard")
        df = render_dashboard_filters(df_full)
        if len(df) < len(df_full):
            st.caption(f"Showing {len(df):,} of {len(df_full):,} rows after filters")

        kpis = recommendations.get("kpis", [])
        kpi_results = []
        if kpis:
            kpi_cols = st.columns(len(kpis))
            for i, kpi in enumerate(kpis):
                result = render_kpi(df, kpi)
                if result:
                    label, value = result
                    kpi_results.append((label, value))
                    with kpi_cols[i]:
                        st.metric(label, value)

        charts = recommendations.get("charts", [])
        chart_images = []
        if not charts:
            st.info("No chart recommendations returned.")
        else:
            cols = st.columns(2)
            for i, chart in enumerate(charts):
                fig = build_chart_figure(df, chart)
                with cols[i % 2]:
                    if fig is None:
                        st.warning(f"Skipped chart '{chart.get('title', '')}'")
                        continue
                    st.plotly_chart(fig, use_container_width=True)
                try:
                    png_bytes = fig.to_image(format="png", width=700, height=420, scale=2)
                    chart_images.append((chart.get("title", "Untitled chart"), png_bytes))
                except Exception as e:
                    st.caption(f"(Couldn't export '{chart.get('title', '')}' to PDF: {e})")

        pdf_bytes = build_pdf_report(
            summary=recommendations.get("summary", ""),
            kpi_results=kpi_results,
            chart_images=chart_images,
            rows_shown=len(df),
            rows_total=len(df_full),
        )
        st.download_button(
            "📥 Download Report (PDF)",
            data=pdf_bytes,
            file_name="dashboard_report.pdf",
            mime="application/pdf",
        )

        st.divider()
        st.subheader("Ask a question about this data")
        question = st.text_input(
            "e.g. \"Which region has the highest average order value?\"",
            key="user_question",
        )
        if st.button("Ask") and question:
            with st.spinner("Thinking..."):
                current_profile = profile_dataframe(df)
                answer = answer_question(current_profile, question)
            st.info(answer)

else:
    st.info("Upload a CSV above to get started.")