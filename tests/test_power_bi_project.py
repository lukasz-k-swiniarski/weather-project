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
    assert "SUM('Station Year Weather'[snow_cover_observed_days])" in metrics
    assert "[Snow Reportable Station-Years], [Complete Station-Years]" in metrics
    assert "DISTINCTCOUNT(Station[station_key])" in metrics
    assert "\n\tisHidden\n" in daily_fact
    assert "\n\tisHidden\n" in annual_fact


def test_power_bi_report_pages_and_references_are_valid():
    pages = json.loads((REPORT_DIR / "pages" / "pages.json").read_text(encoding="utf-8"))
    assert pages["pageOrder"] == ["abef0bd58f60f0782d15"]

    display_names = []
    for page_name in pages["pageOrder"]:
        page_dir = REPORT_DIR / "pages" / page_name
        page = json.loads((page_dir / "page.json").read_text(encoding="utf-8"))
        display_names.append(page["displayName"])
        for visual_path in page_dir.glob("visuals/*/visual.json"):
            json.loads(visual_path.read_text(encoding="utf-8"))

    assert display_names == ["Main"]

    versioned_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in POWER_BI_DIR.rglob("*")
        if path.is_file() and ".pbi" not in path.parts
    )
    assert "polish_clities_synop_data" not in versioned_text
    assert "station_year_observstion_count" not in versioned_text
    assert "Celcius" not in versioned_text
    assert "Temperature (°C)" in versioned_text


def test_power_bi_uses_the_approved_one_page_layout_with_curated_fields():
    page_dir = REPORT_DIR / "pages" / "abef0bd58f60f0782d15"
    expected_visuals = {
        "d0f261a68ae24d609197": ("advancedSlicerVisual", 0, 12.53731343283582),
        "84d7a44ee36d4f30aad3": ("slicer", 1112.5581395348838, 20.465116279069768),
        "f2c53bd691794c57b0ea": ("slicer", 0, 102.08955223880596),
        "ffa450ba029403da5ecb": ("tableEx", 714.6268656716418, 114.6268656716418),
        "8cc6add46832a25cb09e": ("lineChart", 8.059701492537313, 208.65671641791045),
        "8894aa968cc07290e215": ("pivotTable", 714.6268656716418, 307.16417910447763),
        "27c19083e5b435a2ff9e": ("columnChart", 8.041237113402062, 507.21649484536084),
        "d4566e4d36994561748a": ("textbox", 714.6268656716418, 672.5373134328358),
    }

    actual = {}
    for visual_path in page_dir.glob("visuals/*/visual.json"):
        visual = json.loads(visual_path.read_text(encoding="utf-8"))
        actual[visual_path.parent.name] = (
            visual["visual"].get("visualType"),
            visual["position"]["x"],
            visual["position"]["y"],
        )

    assert actual == expected_visuals

    report_text = "\n".join(
        path.read_text(encoding="utf-8") for path in page_dir.rglob("*.json")
    )
    assert "polish_clities_synop_data" not in report_text
    assert "DateTable" not in report_text
    assert "station_year_observstion_count" not in report_text
    assert "Metrics.Annual Average Precipitation per Station" in report_text
    assert "Reporting Location.location_type" in report_text
    assert "Metrics.Average Snow Cover Days" in report_text

    year_table = (MODEL_DIR / "tables" / "Year.tmdl").read_text(encoding="utf-8")
    assert "column 'Time Range'" in year_table
