"""Tests for employee cleaning, filtering, and core analysis values."""

from pathlib import Path

import pandas as pd

from src.data import clean_employee_data, filter_employees, read_employee_source


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_DIR / "data" / "employee.csv"


def cleaned_data() -> tuple[pd.DataFrame, dict]:
    raw = read_employee_source(DATA_PATH)
    return clean_employee_data(raw)


def test_cleaning_preserves_valid_rows_and_keys() -> None:
    df, quality = cleaned_data()

    assert len(df) == 1_000
    assert quality["rows_removed"] == 0
    assert quality["missing_cells_before"] == 0
    assert df["id"].is_unique
    assert not df.isna().any().any()


def test_derived_fields_and_standardization() -> None:
    df, quality = cleaned_data()

    assert quality["standardized_departments"] == 46
    assert "Jewelery" not in set(df["department"])
    assert "Jewelry" in set(df["department"])
    assert df["start_year"].between(2000, 2014).all()
    assert (df["salary"] > 0).all()
    assert df["salary_band"].notna().all()


def test_combined_filters_reconcile() -> None:
    df, _ = cleaned_data()
    result = filter_employees(
        df,
        year_range=(2005, 2010),
        genders=["Female"],
        departments=["Outdoors", "Tools"],
        regions=[1, 2],
        salary_range=(60_000, 120_000),
    )

    assert result["start_year"].between(2005, 2010).all()
    assert set(result["gender"]) <= {"Female"}
    assert set(result["department"]) <= {"Outdoors", "Tools"}
    assert set(result["region_id"]) <= {1, 2}
    assert result["salary"].between(60_000, 120_000).all()
