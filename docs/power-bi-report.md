# Power BI report

The version-controlled report is stored as a Power BI Project in
`powerbi/WeatherReport.pbip`. The project contains only report and semantic-model
definitions. Power BI local caches and user-specific settings are excluded from Git.

## Connection parameters

The semantic model uses three required Power Query parameters:

| Parameter | Default | Purpose |
| --- | --- | --- |
| `DatabaseServer` | `localhost` | PostgreSQL host |
| `DatabasePort` | `5432` | PostgreSQL port published by Docker Compose |
| `DatabaseName` | `weather_db` | Warehouse database |

Open the PBIP file, change these parameters if necessary, provide PostgreSQL
credentials locally, and refresh the model. Credentials are never stored in the
repository.

## Semantic model

The model imports only curated Gold-layer tables:

- `Year` and `Date` are conformed calendar dimensions;
- `Station` contains one stable row per IMGW station series;
- `Reporting Location` contains the reporting geography, including voivodeships;
- `Daily Weather` has one row per station and observation date;
- `Station Year Weather` has one row per stable station and year;
- `Metrics` contains explicit DAX measures used by visuals.

Relationships are single-direction, one-to-many relationships from dimensions to
facts. Surrogate keys remain hidden from report authors.

Annual measures consume the quality-gated annual fact. A value that does not satisfy
the warehouse completeness contract remains blank instead of being presented as a
complete annual result.

## Report page

The user-facing report is intentionally a single 1280x720 page named **Main**. It restores the
original portfolio layout while binding every visual to the curated dimensional model:

- voivodeship cards, year range and location-type slicers;
- annual mean temperature and ten-year moving-average trend;
- annual precipitation per station;
- a voivodeship/location/year temperature matrix;
- annual hot-day, cold-night and snow-cover summaries.

The original precipitation-type selector was not retained semantically because a daily
precipitation classification cannot uniquely classify a station-year total. Its compact visual
slot now filters the stable `location_type` dimension. This preserves the one-page composition
without publishing a misleading split of the annual precipitation metric.

Quality and reportability measures remain available in the semantic model and enforce blank
annual values below the warehouse threshold. A geographic map remains outside the current scope.

## Distribution

The PBIP committed to this repository is the canonical, data-free source. Local
Power BI caches are ignored, so a recipient must provide connection parameters and
local PostgreSQL credentials before refreshing data.

An optional `.pbit` template can be exported from Power BI Desktop when a single-file
distribution artifact is preferred. It is not the version-controlled source of the
report.
