# IMGW Weather ETL

Python ETL pipeline that downloads public daily meteorological data from
[IMGW](https://danepubliczne.imgw.pl/), parses the source CSV files and loads them into a
PostgreSQL warehouse organized into Bronze, Silver and Gold layers.

## Architecture

```text
IMGW website
    -> crawler and downloader
    -> local ZIP/CSV staging (ignored by Git)
    -> Pandas parsing
    -> PostgreSQL layer_bronze
versioned station reference data
    -> SQL procedures
    -> layer_silver.weather_daily
    -> layer_gold conformed date, year, stable-station, station-version and reporting-location dimensions
    -> layer_gold.fact_weather_daily + layer_gold.fact_weather_station_year
```

## Requirements

- Python 3.11 or newer;
- Docker Desktop with Docker Compose (recommended);
- enough disk space for the complete IMGW archive.

The first full run downloads a large historical dataset and may take considerable time. The
downloaded files are stored under `data/` and are intentionally excluded from Git.
As a practical reference, one full Windows/Docker Desktop test took about 64 minutes, peaked at
approximately 3.1 GB of Python process memory, created about 438 MB of extracted files and produced
a PostgreSQL database of approximately 1.9 GB. Actual results depend on hardware, network speed and
the current size of the IMGW archive.
Validated downloads and completed extractions are reused on later runs. A corrupt or incomplete
cache is rebuilt automatically, and any required archive failure stops publication of a new
Bronze snapshot.

## Quick start

1. Clone the repository and enter its directory.
2. Create the local environment file:

   ```bash
   cp .env.example .env
   ```

   On Windows PowerShell use `Copy-Item .env.example .env`.

3. Change `DB_PASSWORD` in `.env`.
4. Start PostgreSQL:

   ```bash
   docker compose up -d
   ```

5. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   # Linux/macOS: source .venv/bin/activate
   # Windows PowerShell: .venv\Scripts\Activate.ps1
   ```

6. Install the application dependencies and run the pipeline:

   ```bash
   python -m pip install -r requirements.txt
   python -m etl_process.run
   ```

## Configuration

| Variable | Purpose | Example |
| --- | --- | --- |
| `DB_HOST` | PostgreSQL host visible from Python | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_NAME` | Database name | `weather_db` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Local database password | set your own value |
| `DB_SCHEMA` | ETL target schema | `layer_bronze` |

Dataset URLs, encodings and filename prefixes are defined in
`etl_process/config_dataset_synop_1*.yaml`.

## Tests and code quality

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m pytest
```

The same checks run automatically in GitHub Actions.

## Power BI

The version-controlled Power BI Project is available at `powerbi/WeatherReport.pbip`.
It connects only to curated Gold-layer tables and uses configurable PostgreSQL server,
port and database parameters. See [docs/power-bi-report.md](docs/power-bi-report.md)
for the semantic-model contract and refresh instructions.

## Database notes and current scope

`postgresql_db/00_schema.sql` creates the warehouse schemas, tables, constraints, indexes and
refresh procedures. Bronze preserves the source-shaped IMGW datasets, Silver integrates,
standardizes and quality-checks them at station-day grain, and Gold exposes a dimensional model
for BI.

The Python pipeline loads the two IMGW SYNOP datasets and three committed reference snapshots:

- `postgresql_db/station_alias.csv` maps historical source names to IMGW station codes and
  project reporting locations;
- `postgresql_db/station_metadata_history.csv` contains versioned official IMGW coordinates,
  elevation and validity periods;
- `postgresql_db/station_reporting_location.csv` contains the contemporary reporting location
  and voivodeship classification used by Power BI. This is a manually maintained,
  project-specific reporting mapping, not an official administrative register.

All three files are validated and loaded into Silver in one database transaction. Gold uses an
SCD Type 2 station dimension and assigns each observation to the metadata version valid on its
observation date. See `docs/station-metadata.md` for provenance and interpretation rules.

Annual Power BI metrics are exposed at station-year grain and are published only when their own
source measure reaches the documented completeness threshold. See `docs/metric-contract.md` for
the exact metric, weighting and incomplete-year rules.

## Data attribution and reuse

This project uses public daily SYNOP observations and station metadata provided by the
Institute of Meteorology and Water Management – National Research Institute (IMGW-PIB).
The daily archive is downloaded from the official
[IMGW-PIB public data portal](https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/dobowe/synop/),
and station metadata comes from the public IMGW-PIB climate metadata service.

The following source and processing statements are provided in accordance with the
[IMGW-PIB data access regulations](https://danepubliczne.imgw.pl/docs/regulamin_udostepniania_danych.pdf):

> Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej –
> Państwowy Instytut Badawczy.

> Dane Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu
> Badawczego zostały przetworzone.

The project downloads, validates, transforms, maps and aggregates the source data. The resulting
warehouse tables, analytical metrics and Power BI visualizations are an independent analytical
work. They are not official IMGW-PIB products, forecasts, warnings or operational weather
communications.

The complete raw IMGW-PIB archive is not committed to this repository. It is downloaded from the
official source during pipeline execution and stored in the Git-ignored `data/` directory. Small,
version-controlled reference snapshots are included to make station metadata and the project's
reporting classifications reproducible and auditable.

Source data may be corrected, supplemented or unverified at the time of publication. Results
therefore depend on the source version available when the pipeline is executed. Missing analytical
values mean that the relevant data-quality and completeness contract was not met; they must not be
interpreted automatically as zero or as the absence of a meteorological phenomenon.

Any future use of the source data remains subject to the current terms specified by IMGW-PIB.
Publishing this repository does not grant additional rights to IMGW-PIB data. Any license selected
for the original project source code applies to that code only and does not replace or override the
data provider's terms.

## License

The original source code in this repository is licensed under the
[PolyForm Noncommercial License 1.0.0](LICENSE). It may be used, studied, modified and distributed
for permitted noncommercial purposes under the conditions of that license. Commercial use requires
separate permission from the copyright holder.

PolyForm Noncommercial is a source-available license, not an Open Source Initiative-approved open
source license. It applies only to the original project source code. It does not apply to IMGW-PIB
data or other third-party materials, which remain subject to their providers' respective terms.

## Security

- `.env`, downloaded data, logs, virtual environments and IDE settings are ignored by Git;
- `.env.example` contains placeholders only;
- database credentials are read from environment variables and are not logged;
- never commit a real `.env` file or production credentials.

## Resetting the local database

This removes the Docker database volume and recreates the schema on the next start:

```bash
docker compose down -v
docker compose up -d
```

Do not use this command for a database containing data you need to keep.
