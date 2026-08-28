"""Simple, presentation-ready employee analytics dashboard."""

from pathlib import Path

import pandas as pd
import streamlit as st

from src.charts import (
    department_headcount_chart,
    department_salary_chart,
    hiring_trend_chart,
    salary_by_gender_chart,
)
from src.data import clean_employee_data, filter_employees, read_employee_source


st.set_page_config(
    page_title="Employee analytics",
    page_icon=":material/groups:",
    layout="wide",
)

PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "data" / "employee.csv"
FILTER_KEYS = ["year_filter", "gender_filter", "department_filter", "region_filter", "salary_filter"]
PLOTLY_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "responsive": True,
}


@st.cache_data(show_spinner="Preparing employee data...")
def load_data(source_path: str) -> tuple[pd.DataFrame, dict]:
    """Load and clean the fixed project dataset once per app session."""

    raw_df = read_employee_source(source_path)
    return clean_employee_data(raw_df)


def reset_filters() -> None:
    """Clear only dashboard filter state."""

    for key in FILTER_KEYS:
        st.session_state.pop(key, None)


try:
    employees, quality = load_data(str(DATA_PATH))
except (FileNotFoundError, ValueError) as exc:
    st.error(str(exc), icon=":material/error:")
    st.stop()


with st.sidebar:
    st.header(":material/filter_list: Filters")
    st.caption("All filters update the four charts together.")
    st.button(
        "Reset filters",
        icon=":material/restart_alt:",
        type="tertiary",
        on_click=reset_filters,
        width="stretch",
    )

    min_year = int(employees["start_year"].min())
    max_year = int(employees["start_year"].max())
    year_range = st.slider(
        "Start year",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        key="year_filter",
    )

    gender_options = sorted(employees["gender"].unique().tolist())
    selected_genders = st.pills(
        "Gender",
        options=gender_options,
        default=gender_options,
        selection_mode="multi",
        key="gender_filter",
    )

    selected_departments = st.multiselect(
        "Department",
        options=sorted(employees["department"].unique()),
        placeholder="All departments",
        key="department_filter",
    )

    region_options = sorted(employees["region_id"].unique().tolist())
    selected_regions = st.multiselect(
        "Region",
        options=region_options,
        format_func=lambda region_id: f"Region {region_id}",
        placeholder="All regions",
        key="region_filter",
    )

    source_min_salary = int(employees["salary"].min())
    source_max_salary = int(employees["salary"].max())
    min_salary = (source_min_salary // 1_000) * 1_000
    max_salary = ((source_max_salary + 999) // 1_000) * 1_000
    salary_range = st.slider(
        "Salary range",
        min_value=min_salary,
        max_value=max_salary,
        value=(min_salary, max_salary),
        step=1_000,
        key="salary_filter",
    )

    st.caption("Data source: bundled employee dataset · 1,000 records")


filtered = filter_employees(
    employees,
    year_range=year_range,
    genders=list(selected_genders or []),
    departments=list(selected_departments),
    regions=list(selected_regions),
    salary_range=salary_range,
)

st.title(":material/groups: Employee analytics dashboard")
st.caption(
    "A focused view of workforce size, salary distribution, and hiring history. "
    "Results are descriptive and should not be interpreted as causal HR conclusions."
)

if filtered.empty:
    st.warning(
        "No employees match this filter combination. Reset or widen the filters.",
        icon=":material/filter_alt_off:",
    )
    st.stop()

employee_delta = len(filtered) - len(employees)
average_salary = filtered["salary"].mean()
salary_delta = average_salary - employees["salary"].mean()

kpi_columns = st.columns(4)
kpi_columns[0].metric(
    "Employees",
    f"{len(filtered):,}",
    delta=f"{employee_delta:+,} vs all data",
    delta_color="off",
    border=True,
)
kpi_columns[1].metric(
    "Average salary",
    f"{average_salary / 1_000:,.1f}K",
    delta=f"{salary_delta / 1_000:+,.1f}K vs all data",
    delta_color="off",
    border=True,
)
kpi_columns[2].metric(
    "Median salary",
    f"{filtered['salary'].median() / 1_000:,.1f}K",
    border=True,
)
kpi_columns[3].metric(
    "Departments",
    f"{filtered['department'].nunique():,}",
    border=True,
)

row_one = st.columns(2)
with row_one[0].container(border=True):
    st.subheader("Largest departments")
    st.plotly_chart(
        department_headcount_chart(filtered),
        width="stretch",
        config=PLOTLY_CONFIG,
    )

with row_one[1].container(border=True):
    st.subheader("Department salary vs overall average")
    st.plotly_chart(
        department_salary_chart(filtered),
        width="stretch",
        config=PLOTLY_CONFIG,
    )

row_two = st.columns(2)
with row_two[0].container(border=True):
    st.subheader("Salary distribution by gender")
    st.plotly_chart(
        salary_by_gender_chart(filtered),
        width="stretch",
        config=PLOTLY_CONFIG,
    )

with row_two[1].container(border=True):
    st.subheader("Employee starts by year")
    st.plotly_chart(
        hiring_trend_chart(filtered),
        width="stretch",
        config=PLOTLY_CONFIG,
    )

with st.expander("Data quality and filtered records", icon=":material/table_chart:"):
    st.caption(
        f"Automated cleaning kept {quality['clean_rows']:,} of {quality['original_rows']:,} rows, "
        f"removed {quality['rows_removed']:,}, standardized "
        f"{quality['standardized_departments']:,} department labels, and found "
        f"{quality['salary_outliers_iqr']:,} IQR salary outliers. Emails are excluded from this view."
    )
    display_columns = [
        "id",
        "gender",
        "department",
        "start_date",
        "salary",
        "job_title",
        "region",
    ]
    st.dataframe(
        filtered[display_columns],
        hide_index=True,
        width="stretch",
        height=320,
        column_config={
            "id": st.column_config.NumberColumn("Employee ID", format="%d"),
            "gender": "Gender",
            "department": "Department",
            "start_date": st.column_config.DateColumn("Start date", format="YYYY-MM-DD"),
            "salary": st.column_config.NumberColumn("Salary", format="%.0f"),
            "job_title": "Job title",
            "region": "Region",
        },
    )
