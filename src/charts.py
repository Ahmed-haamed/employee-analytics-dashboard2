"""Chart builders for the four dashboard figures."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


BLUE = "#0078D4"
GREEN = "#107C10"
ORANGE = "#D83B01"
PURPLE = "#8764B8"
GRID = "#E8E8E8"
CHART_HEIGHT = 360


def _style_plotly(fig: go.Figure) -> go.Figure:
    """Apply one consistent, compact style to interactive charts."""

    fig.update_layout(
        template="plotly_white",
        height=CHART_HEIGHT,
        margin=dict(l=8, r=32, t=10, b=8),
        font=dict(size=13, color="#1A1A1A"),
        hoverlabel=dict(bgcolor="white"),
        showlegend=False,
    )
    fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=False)
    fig.update_yaxes(showgrid=False, title=None)
    return fig


def department_headcount_chart(df: pd.DataFrame) -> go.Figure:
    """Return an interactive top-10 department headcount bar chart."""

    summary = (
        df.groupby("department", as_index=False)
        .agg(employees=("id", "nunique"))
        .nlargest(10, "employees")
        .sort_values("employees")
    )
    fig = px.bar(
        summary,
        x="employees",
        y="department",
        orientation="h",
        text="employees",
        color_discrete_sequence=[BLUE],
        labels={"employees": "Employees", "department": "Department"},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(title="Employees", rangemode="tozero")
    return _style_plotly(fig)


def department_salary_chart(df: pd.DataFrame) -> go.Figure:
    """Return top and bottom departments as differences from filtered average."""

    filtered_average = float(df["salary"].mean())
    department_summary = df.groupby("department", as_index=False).agg(
        average_salary=("salary", "mean")
    )
    department_summary["difference"] = (
        department_summary["average_salary"] - filtered_average
    )
    top_five = department_summary.nlargest(5, "difference")
    bottom_five = department_summary.nsmallest(5, "difference")
    summary = (
        pd.concat([bottom_five, top_five], ignore_index=True)
        .drop_duplicates(subset="department")
        .sort_values("difference")
    )
    summary["direction"] = summary["difference"].ge(0).map(
        {True: "Above average", False: "Below average"}
    )
    summary["label"] = summary["difference"].map(
        lambda value: f"{value / 1000:+.1f}K"
    )

    fig = px.bar(
        summary,
        x="difference",
        y="department",
        orientation="h",
        text="label",
        color="direction",
        color_discrete_map={"Above average": BLUE, "Below average": ORANGE},
        category_orders={"direction": ["Below average", "Above average"]},
        custom_data=["average_salary"],
        labels={
            "difference": "Difference from filtered average",
            "department": "Department",
        },
    )
    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{y}</b><br>Average salary: %{customdata[0]:,.0f}"
            "<br>Difference: %{x:+,.0f}<extra></extra>"
        ),
    )
    fig.add_vline(
        x=0,
        line_dash="dash",
        line_color="#737373",
        annotation_text=f"Filtered average {filtered_average / 1000:.1f}K",
        annotation_position="top",
    )
    fig.update_xaxes(title="Difference from filtered average", tickformat="~s")
    fig = _style_plotly(fig)
    fig.update_layout(
        showlegend=True,
        margin=dict(l=8, r=32, t=40, b=8),
        legend=dict(
            title=None,
            orientation="h",
            yanchor="bottom",
            y=1.0,
            xanchor="right",
            x=1.0,
        ),
    )
    return fig


def salary_by_gender_chart(df: pd.DataFrame) -> go.Figure:
    """Return an interactive violin with embedded box plots and employee points."""

    preferred_order = ["Female", "Male"]
    order = [item for item in preferred_order if item in df["gender"].unique()]
    order += [item for item in df["gender"].unique() if item not in order]

    fig = px.violin(
        df,
        x="gender",
        y="salary",
        color="gender",
        box=True,
        points="all",
        category_orders={"gender": order},
        color_discrete_map={"Female": PURPLE, "Male": BLUE},
        hover_data={
            "id": True,
            "department": True,
            "job_title": True,
            "start_year": True,
            "salary": ":,.0f",
        },
        labels={"gender": "Gender", "salary": "Salary"},
    )
    fig.update_traces(
        meanline_visible=True,
        jitter=0.18,
        marker=dict(size=3, opacity=0.35),
        spanmode="hard",
    )
    fig = _style_plotly(fig)
    fig.update_layout(violinmode="group", showlegend=False)
    fig.update_xaxes(title=None)
    fig.update_yaxes(title="Salary", tickformat="~s", rangemode="tozero")
    return fig


def hiring_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Return interactive yearly starts and a three-year moving average."""

    counts = df.groupby("start_year").size().sort_index()
    all_years = pd.Index(range(int(counts.index.min()), int(counts.index.max()) + 1))
    counts = counts.reindex(all_years, fill_value=0)
    moving_average = counts.rolling(3, center=True, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=counts.index,
            y=counts.values,
            name="Employee starts",
            marker=dict(color="#A9D2F3", line=dict(color=BLUE, width=0.8)),
            hovertemplate="Year %{x}<br>Employee starts: %{y}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=moving_average.index,
            y=moving_average.values,
            name="3-year moving average",
            mode="lines+markers",
            line=dict(color=ORANGE, width=2.5),
            marker=dict(size=6),
            hovertemplate="Year %{x}<br>3-year average: %{y:.1f}<extra></extra>",
        )
    )
    fig = _style_plotly(fig)
    fig.update_layout(
        showlegend=True,
        hovermode="x unified",
        margin=dict(l=8, r=20, t=40, b=8),
        legend=dict(
            title=None,
            orientation="h",
            yanchor="bottom",
            y=1.0,
            xanchor="left",
            x=0.0,
        ),
    )
    fig.update_xaxes(title=None, dtick=1)
    fig.update_yaxes(title="Employee starts", rangemode="tozero")
    return fig
