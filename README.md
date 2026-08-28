# Employee analytics dashboard

A focused Streamlit project that turns a 1,000-row employee workbook into a
simple but information-rich dashboard. It has global filters, four KPI cards,
and exactly four figures arranged in a 2×2 layout.

## What the dashboard answers

1. Which departments contain the most employees?
2. Which departments have the highest and lowest average salaries?
3. How does the salary distribution differ by gender?
4. How have employee start dates changed over time?

## Libraries and why they are used

- **Pandas:** reads, cleans, filters, groups, and summarizes the employee data.
- **NumPy:** creates reproducible salary bands during data preparation.
- **Plotly:** powers all four interactive charts, hover details, zoom, and export tools.
- **Streamlit:** provides the filters, KPI cards, layout, and deployable web app.
- **OpenPyXL:** supports reading an Excel workbook during local development.

## Project structure

```text
employee-analytics-dashboard/
├── data/
│   └── employee.csv           # De-identified deployment snapshot
├── reports/
│   └── employee-storytelling-ar.md
├── src/
│   ├── charts.py
│   └── data.py
├── tests/
├── .streamlit/config.toml
├── requirements.txt
└── streamlit_app.py
```

## Run locally

Open a terminal inside this project folder, then run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

If you see `Could not open requirements file`, the terminal is in the wrong
folder. Move to the folder containing `requirements.txt` first:

```powershell
Set-Location "C:\path\to\employee-analytics-dashboard"
python -m pip install -r requirements.txt
```

## Deploy on Streamlit Community Cloud

Push this folder to GitHub, create a Streamlit Community Cloud app, and set the
main file path to `streamlit_app.py`. The data snapshot is bundled, so the app
does not need an upload step.

## Data handling

Cleaning is deterministic and documented in `src/data.py`: column names are
normalized, text is trimmed, types are validated, duplicate keys are removed,
invalid required records are excluded, and the misspelled department label
`Jewelery` is standardized to `Jewelry`. The bundled GitHub-ready snapshot
excludes `last_name` and `email` because neither field is needed for analysis.
The supplied original workbook stays outside the repository.

This dataset supports descriptive analysis only. It does not contain employee
level, prior experience, performance, termination status, bonuses, or named
locations, so it cannot prove pay fairness, retention, or causal relationships.
