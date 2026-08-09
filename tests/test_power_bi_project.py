import json
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
POWER_BI_DIR = PROJECT_DIR / "powerbi"
MODEL_DIR = POWER_BI_DIR / "WeatherReport.SemanticModel" / "definition"
REPORT_DIR = POWER_BI_DIR / "WeatherReport.Report" / "definition"


def test_power_bi_project_uses_parameterized_gold_sources():
    expressions = (MODEL_DIR / "expressions.tmdl").read_text(encoding="utf-8")
    model_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((MODEL_DIR / "tables").glob("*.tmdl"))
    )

    assert 'expression DatabaseServer = "localhost"' in expressions
    assert "expression DatabasePort = 5432" in expressions
    assert 'expression DatabaseName = "weather_db"' in expressions
    assert "DatabaseServer & \":\" & Text.From(DatabasePort)" in model_text
    assert "layer_gold." in model_text
    assert "layer_bronze." not in model_text
    assert "layer_silver." not in model_text


def test_power_bi_model_has_conformed_dimensions_and_facts():
    model = (MODEL_DIR / "model.tmdl").read_text(encoding="utf-8")
    relationships = (MODEL_DIR / "relationships.tmdl").read_text(encoding="utf-8")

    for table in (
        "Year",
        "Date",
        "'Reporting Location'",
        "Station",
        "'Daily Weather'",
        "'Station Year Weather'",
        "Metrics",
    ):
        assert f"ref table {table}" in model

    assert "daily_to_date" in relationships
    assert "daily_to_station" in relationships
    assert "station_to_location" in relationships
    assert "annual_to_year" in relationships
    assert "annual_to_station" in relationships
    assert "annual_to_location" not in relationships

    station = (MODEL_DIR / "tables" / "Station.tmdl").read_text(encoding="utf-8")
    daily = (MODEL_DIR / "tables" / "Daily Weather.tmdl").read_text(
        encoding="utf-8"
    )
    assert "station_version_key" in daily
    assert "valid_from" not in station
    assert "FROM layer_gold.dim_station" in station


def test_power_bi_metrics_use_explicit_quality_aware_definitions():
    metrics = (MODEL_DIR / "tables" / "Metrics.tmdl").read_text(encoding="utf-8")
    daily_fact = (MODEL_DIR / "tables" / "Daily Weather.tmdl").read_text(
        encoding="utf-8"
    )
    annual_fact = (MODEL_DIR / "tables" / "Station Year Weather.tmdl").read_text(
        encoding="utf-8"
    )

    assert (
        "DIVIDE([Temperature Reportable Station-Years], [Complete Station-Years])"
        in metrics
    )
    assert "SUM('Station Year Weather'[avg_temperature_days])" in metrics
    assert "SUM('Station Year Weather'[precipitation_observed_days])" in metrics
    assert "DISTINCTCOUNT(Station[station_key])" in metrics
    assert "\n\tisHidden\n" in daily_fact
    assert "\n\tisHidden\n" in annual_fact


def test_power_bi_report_pages_and_references_are_valid():
    pages = json.loads((REPORT_DIR / "pages" / "pages.json").read_text(encoding="utf-8"))
    assert pages["pageOrder"] == [
        "abef0bd58f60f0782d15",
        "temperature-extremes",
        "data-quality",
    ]

    display_names = []
    for page_name in pages["pageOrder"]:
        page_dir = REPORT_DIR / "pages" / page_name
        page = json.loads((page_dir / "page.json").read_text(encoding="utf-8"))
        display_names.append(page["displayName"])
        for visual_path in page_dir.glob("visuals/*/visual.json"):
            json.loads(visual_path.read_text(encoding="utf-8"))

    assert display_names == [
        "Weather Overview",
        "Temperature and Snow Extremes",
        "Data Quality",
    ]

    versioned_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in POWER_BI_DIR.rglob("*")
        if path.is_file() and ".pbi" not in path.parts
    )
    assert "polish_clities_synop_data" not in versioned_text
    assert "station_year_observstion_count" not in versioned_text
    assert "Celcius" not in versioned_text
    assert "Temperature (°C)" in versioned_text
    assert "Coverage (%)" in versioned_text
