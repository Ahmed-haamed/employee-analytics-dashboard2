"""A lightweight Streamlit smoke test."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "streamlit_app.py"


def test_dashboard_runs_without_exceptions() -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()

    assert not app.exception
    assert len(app.title) == 1
    assert len(app.metric) == 4

