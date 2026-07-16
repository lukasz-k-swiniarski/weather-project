# IMGW Weather ETL

Python ETL pipeline that downloads public daily meteorological data from
[IMGW](https://danepubliczne.imgw.pl/), parses the source CSV files and loads them into a
PostgreSQL/PostGIS warehouse organized into Bronze, Silver and Gold layers.

## What this project demonstrates

- recursive discovery and idempotent downloading of public datasets;
- ZIP extraction and schema-driven CSV parsing;
- configuration through YAML and environment variables;
- batch loading with Pandas and SQLAlchemy;
- PostgreSQL procedures and Bronze/Silver/Gold data modelling;
- automated tests, linting and CI.

## Architecture

```text
IMGW website
    -> crawler and downloader
    -> local ZIP/CSV staging (ignored by Git)
    -> Pandas parsing
    -> PostgreSQL layer_bronze
station mapping CSV
    -> validation and transactional load to layer_silver.synop_location_mapp
    -> SQL procedures
    -> layer_silver
    -> layer_gold
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
4. Start PostgreSQL/PostGIS:

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

`postgresql_db/00_schema.sql` creates the warehouse schemas, tables, views and refresh
procedures. The Docker image includes PostGIS, which is required by the geography columns.

The Python pipeline loads the two IMGW SYNOP datasets and the committed
`postgresql_db/synop_location_mapp.csv` reference snapshot. At the beginning of every run, the
mapping file is fully validated and replaces the contents of
`layer_silver.synop_location_mapp` in a single database transaction. The warehouse refresh
procedure runs only after the mapping and weather datasets have been loaded successfully.

The mapping intentionally allows multiple station names for one station code and nullable city
identifiers for locations such as mountain stations. The loader rejects missing station names,
location types and station codes.

The separate `layer_bronze.geography` reference dataset is not yet loaded by this repository.
City names from the station mapping are therefore available, but administrative divisions and
PostGIS coordinates require the geography table to be populated separately.

### Station mapping data provenance

`postgresql_db/synop_location_mapp.csv` is a project-specific reference mapping created by the
project author. It combines IMGW meteorological station data with locality information matched
against the Polish **Państwowy Rejestr Nazw Geograficznych (PRNG)**. It is not an unchanged
official dataset published by either IMGW or GUGiK.

Column provenance:

- `station_name` and `station_code` come from public IMGW SYNOP meteorological datasets;
- `location_name` is the locality name matched by the project author using PRNG data;
- `id` is the PRNG identifier of the matched locality;
- `location` is the PRNG locality type used in the mapping, for example `miasto` (town/city) or
  `wieś` (village).

The PRNG data used for this mapping was downloaded on 2026-04-26 from the official
[Geoportal PRNG map](https://mapy.geoportal.gov.pl/imap/Imgp_2.html?locale=pl&gui=new&sessionID=5836773).
Original source providers are **Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut
Badawczy (IMGW-PIB)** for station data and **Główny Urząd Geodezji i Kartografii (GUGiK)** for
PRNG locality data.

The source records were processed and matched by the project author. IMGW-PIB and GUGiK are not
responsible for the correctness, completeness, quality or currency of this derived mapping. PRNG
reuse is subject to the
[GUGiK public-sector information reuse conditions](https://www.gov.pl/web/gugik/ponowne-wykorzystanie-informacji-sektora-publicznego).

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
