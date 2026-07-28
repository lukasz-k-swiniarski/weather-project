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
station mapping CSV
    -> SQL procedures
    -> layer_silver.weather_daily
    -> layer_gold.dim_date + layer_gold.dim_station
    -> layer_gold.fact_weather_daily
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

The Python pipeline loads the two IMGW SYNOP datasets and the committed
`postgresql_db/synop_location_mapp.csv` reference snapshot. At the beginning of every run, the
mapping file is fully validated and replaces the contents of
`layer_silver.synop_location_mapp` in a single database transaction. The warehouse refresh
procedure runs only after the mapping and weather datasets have been loaded successfully.

The station mapping is a manually maintained, project-specific lookup intended only to support
this application's data-processing workflow. Its `id` values are internal identifiers
with no meaning outside this project, and its location names and types are project-defined labels,
not an authoritative geographic register. The mapping may associate multiple station names with
one location, while the loader enforces complete values and a one-to-one relationship between
each `location_name` and `id`.

Administrative divisions and geographic coordinates are enriched in a separate workflow. The
Gold station dimension is prepared for these attributes but does not invent or infer missing
geographic values.

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
