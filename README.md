# IMGW Weather ETL

Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej –
Państwowy Instytut Badawczy

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
    -> layer_gold dimensions
    -> layer_gold.fact_weather_daily + layer_gold.fact_weather_station_year
```

## Requirements

- Python 3.11 or newer;
- Docker Desktop with Docker Compose (recommended);
- enough disk space for the complete IMGW archive.

The first full run downloads a large historical dataset and may take considerable time. The
downloaded files are stored under `data/` and are intentionally excluded from Git.

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
ruff check .
pytest
```

The same checks run automatically in GitHub Actions.

## Database notes and current scope

`postgresql_db/00_schema.sql` creates the warehouse schemas, tables, constraints, indexes and
refresh procedures. Bronze preserves the source-shaped IMGW datasets, Silver integrates and
cleans them at station-day grain, and Gold exposes a dimensional model for BI.

The Python pipeline loads the two IMGW SYNOP datasets and three committed reference snapshots:

- `postgresql_db/station_alias.csv` maps historical source names to IMGW station codes and
  project reporting locations;
- `postgresql_db/station_metadata_history.csv` contains versioned official IMGW coordinates,
  elevation and validity periods;
- `postgresql_db/station_reporting_location.csv` contains the contemporary reporting location
  and voivodeship classification used by Power BI.

All three files are validated and loaded into Silver in one database transaction. Gold uses an
SCD Type 2 station dimension and assigns each observation to the metadata version valid on its
observation date. See `docs/station-metadata.md` for provenance and interpretation rules.

Annual Power BI metrics are exposed at station-year grain and are published only when their own
source measure reaches the documented completeness threshold. See `docs/metric-contract.md` for
the exact metric, weighting and incomplete-year rules.

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
