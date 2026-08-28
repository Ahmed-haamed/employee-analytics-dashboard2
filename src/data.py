"""Load, clean, validate, and filter the employee dataset."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = {
    "id",
    "gender",
    "department",
    "start_date",
    "salary",
    "job_title",
    "region_id",
}

TEXT_COLUMNS = ["gender", "department", "job_title"]
OPTIONAL_PERSONAL_COLUMNS = ["last_name", "email"]
DEPARTMENT_RENAMES = {"Jewelery": "Jewelry"}
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def read_employee_source(source_path: str | Path) -> pd.DataFrame:
    """Read a de-identified CSV snapshot or a local Excel workbook.

    The deployed project uses CSV. Excel remains supported when a local workbook
    is supplied during development.
    """

    source_path = Path(source_path)
    if source_path.suffix.lower() == ".csv" and source_path.exists():
        return pd.read_csv(source_path)
    if source_path.suffix.lower() in {".xlsx", ".xls"} and source_path.exists():
        return pd.read_excel(source_path, sheet_name="employee")

    raise FileNotFoundError(f"Employee data was not found at {source_path}")


def clean_employee_data(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Apply reproducible cleaning rules and return a quality report."""

    df = raw_df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
    )

    missing_columns = REQUIRED_COLUMNS.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {missing}")

    original_rows = len(df)
    missing_cells_before = int(df[list(REQUIRED_COLUMNS)].isna().sum().sum())
    exact_duplicates = int(df.duplicated().sum())

    available_text_columns = [
        column for column in TEXT_COLUMNS + OPTIONAL_PERSONAL_COLUMNS if column in df.columns
    ]
    for column in available_text_columns:
        df[column] = df[column].astype("string").str.strip()
        df[column] = df[column].replace("", pd.NA)

    if "email" in df.columns:
        df["email"] = df["email"].str.lower()
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df["salary"] = pd.to_numeric(df["salary"], errors="coerce")
    df["region_id"] = pd.to_numeric(df["region_id"], errors="coerce")

    if "email" in df.columns:
        invalid_email = ~df["email"].str.fullmatch(EMAIL_PATTERN, na=False)
    else:
        invalid_email = pd.Series(False, index=df.index)
    invalid_date = df["start_date"].isna()
    invalid_salary = df["salary"].isna() | (df["salary"] <= 0)
    invalid_id = df["id"].isna()
    invalid_region = df["region_id"].isna() | (df["region_id"] <= 0)
    missing_text = df[TEXT_COLUMNS].isna().any(axis=1)

    invalid_rows = (
        invalid_email
        | invalid_date
        | invalid_salary
        | invalid_id
        | invalid_region
        | missing_text
    )
    invalid_rows_removed = int(invalid_rows.sum())
    df = df.loc[~invalid_rows].copy()

    df = df.drop_duplicates()
    duplicate_ids_removed = int(df.duplicated(subset="id").sum())
    df = df.drop_duplicates(subset="id", keep="first")
    if "email" in df.columns:
        duplicate_emails_removed = int(df.duplicated(subset="email").sum())
        df = df.drop_duplicates(subset="email", keep="first")
    else:
        duplicate_emails_removed = 0

    standardized_departments = int(df["department"].isin(DEPARTMENT_RENAMES).sum())
    df["department"] = df["department"].replace(DEPARTMENT_RENAMES)

    df["id"] = df["id"].astype(int)
    df["region_id"] = df["region_id"].astype(int)
    df["salary"] = df["salary"].astype(float)
    df["start_year"] = df["start_date"].dt.year.astype(int)
    df["region"] = "Region " + df["region_id"].astype(str)

    df["salary_band"] = pd.cut(
        df["salary"],
        bins=[-np.inf, 60_000, 90_000, 120_000, np.inf],
        labels=["Under 60K", "60K–89K", "90K–119K", "120K+"],
        right=False,
    )

    q1, q3 = df["salary"].quantile([0.25, 0.75])
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    salary_outliers = int(
        ((df["salary"] < lower_bound) | (df["salary"] > upper_bound)).sum()
    )

    df = df.sort_values("id").reset_index(drop=True)

    quality_report: dict[str, Any] = {
        "original_rows": original_rows,
        "clean_rows": len(df),
        "rows_removed": original_rows - len(df),
        "missing_cells_before": missing_cells_before,
        "exact_duplicates_found": exact_duplicates,
        "invalid_rows_removed": invalid_rows_removed,
        "duplicate_ids_removed": duplicate_ids_removed,
        "duplicate_emails_removed": duplicate_emails_removed,
        "standardized_departments": standardized_departments,
        "salary_outliers_iqr": salary_outliers,
        "salary_lower_bound": float(lower_bound),
        "salary_upper_bound": float(upper_bound),
    }
    return df, quality_report


def filter_employees(
    df: pd.DataFrame,
    year_range: tuple[int, int],
    genders: list[str] | None = None,
    departments: list[str] | None = None,
    regions: list[int] | None = None,
    salary_range: tuple[float, float] | None = None,
) -> pd.DataFrame:
    """Apply all dashboard filters with one Boolean mask."""

    mask = df["start_year"].between(year_range[0], year_range[1])

    if genders:
        mask &= df["gender"].isin(genders)
    if departments:
        mask &= df["department"].isin(departments)
    if regions:
        mask &= df["region_id"].isin(regions)
    if salary_range:
        mask &= df["salary"].between(salary_range[0], salary_range[1])

    return df.loc[mask].copy()
