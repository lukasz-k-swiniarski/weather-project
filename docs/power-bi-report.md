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
- `Station` is the versioned station dimension;
- `Reporting Location` contains the reporting geography, including voivodeships;
- `Daily Weather` has one row per station and observation date;
- `Station Year Weather` has one row per station version and year;
- `Metrics` contains explicit DAX measures used by visuals.

Relationships are single-direction, one-to-many relationships from dimensions to
facts. Surrogate keys remain hidden from report authors.

Annual measures consume the quality-gated annual fact. A value that does not satisfy
the warehouse completeness contract remains blank instead of being presented as a
complete annual result.

## Report pages

- **Weather Overview** — annual mean temperature and ten-year moving average,
  filterable by year and voivodeship.
- **Temperature and Snow Extremes** — annual high and low temperature series.
- **Data Quality** — annual temperature and precipitation coverage.

The geographic map is intentionally deferred until the final package.

## Distribution

The PBIP committed to this repository is the canonical, data-free source. Local
Power BI caches are ignored, so a recipient must provide connection parameters and
local PostgreSQL credentials before refreshing data.

An optional `.pbit` template can be exported from Power BI Desktop when a single-file
distribution artifact is preferred. It is not the version-controlled source of the
report.
