# IMGW daily SYNOP source data contract

## Purpose

This document defines the source contract used by the ETL pipeline for public daily SYNOP
files published by IMGW-PIB. The versioned column lists in
`etl_process/config_dataset_synop_1_schema.yaml` are the executable source of truth used by
the parser. The remote IMGW header files are documentation references and are not required
at runtime.

Contract version: `2026-01-29`.

Source directory:
<https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/dobowe/synop/>

## Shared grain

Both datasets represent one weather station on one observation day. Their natural key is:

```text
nsp + rok + mc + dz
```

`nsp` is the station code. `post` is a descriptive station name and is not part of the key,
because names can change while a station code remains the same.

The `s_d` dataset is the primary daily dataset. Keys from `s_d_t` must be a subset of keys
from `s_d`. A missing `s_d_t` row does not invalidate an otherwise valid `s_d` observation.

## Status columns

Most measurements have an adjacent status column whose name starts with `w`. IMGW defines:

- `8` — measurement missing;
- `9` — phenomenon absent;
- blank — no status value supplied.

The status columns must be retained in Bronze. Rules deciding whether a measurement is
analytically usable belong in Silver and must not be implemented by silently discarding
status information during ingestion.

## Dataset `s_d`

Expected columns: 65.

Official format:
<https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/dobowe/synop/s_d_format.txt>

| Value | Status | IMGW definition | Unit or domain |
|---|---|---|---|
| `nsp` | — | Station code | identifier |
| `post` | — | Station name | text |
| `rok`, `mc`, `dz` | — | Observation year, month and day | calendar components |
| `tmax` | `wtmax` | Maximum daily air temperature | °C |
| `tmin` | `wtmin` | Minimum daily air temperature | °C |
| `std` | `wstd` | Mean daily air temperature | °C |
| `tmng` | `wtmng` | Minimum daily ground-level temperature | °C |
| `smdb` | `wsmdb` | Daily precipitation total | mm |
| `roop` | — | Precipitation type | `S`, `W` or blank |
| `pksn` | `wpksn` | Snow-cover depth | cm |
| `rwsn` | `wrwsn` | Snow water equivalent | mm/cm |
| `usl` | `wusl` | Sunshine duration | hours |
| `desz` | `wdesz` | Rain duration | hours |
| `sneg` | `wsneg` | Snowfall duration | hours |
| `disn` | `wdisn` | Sleet duration | hours |
| `grad` | `wgrad` | Hail duration | hours |
| `mgla` | `wmgla` | Fog duration | hours |
| `zmgl` | `wzmgl` | Mist duration | hours |
| `sadz` | `wsadz` | Rime duration | hours |
| `golo` | `wgolo` | Glaze duration | hours |
| `zmni` | `wzmni` | Low drifting-snow duration | hours |
| `zmws` | `wzmws` | High drifting-snow duration | hours |
| `zmet` | `wzmet` | Haze duration | hours |
| `ff10` | `wff10` | Wind at least 10 m/s duration | hours |
| `ff15` | `wff15` | Wind above 15 m/s duration | hours |
| `brza` | `wbrza` | Thunderstorm duration | hours |
| `rosa` | `wrosa` | Dew duration | hours |
| `szro` | `wszro` | Frost duration | hours |
| `dzps` | `wdzps` | Snow-cover occurrence | `0` or `1` |
| `dzbl` | `wdzbl` | Lightning occurrence | `0` or `1` |
| `sgr` | — | Ground condition | `Z` or `R` |
| `izd` | `wizd` | Lower isotherm | cm |
| `izg` | `wizg` | Upper isotherm | cm |
| `aktn` | `waktn` | Actinometry | J/cm² |

## Dataset `s_d_t`

Expected columns: 23.

Official format:
<https://danepubliczne.imgw.pl/data/dane_pomiarowo_obserwacyjne/dane_meteorologiczne/dobowe/synop/s_d_t_format.txt>

| Value | Status | IMGW definition | Unit |
|---|---|---|---|
| `nsp` | — | Station code | identifier |
| `post` | — | Station name | text |
| `rok`, `mc`, `dz` | — | Observation year, month and day | calendar components |
| `nos` | `wnos` | Mean daily total cloud cover | oktas |
| `fws` | `wfws` | Mean daily wind speed | m/s |
| `temp` | `wtemp` | Mean daily air temperature | °C |
| `cpw` | `wcpw` | Mean daily water-vapour pressure | hPa |
| `wlgs` | `wwlgs` | Mean daily relative humidity | % |
| `ppps` | `wppps` | Mean daily station-level pressure | hPa |
| `pppm` | `wpppm` | Mean daily sea-level pressure | hPa |
| `wodz` | `wwodz` | Daytime precipitation total | mm |
| `wono` | `wwono` | Night-time precipitation total | mm |

## Ingestion validation

Before any database load, the parser enforces:

- presence of every required dataset;
- non-empty source files;
- the exact versioned column count;
- complete grain columns;
- valid calendar dates;
- uniqueness of the natural key within each dataset;
- subset integrity between `s_d_t` and `s_d`.

Differences in coverage where `s_d` has more keys than `s_d_t` are logged as a warning.
This is expected for periods where the secondary dataset is not yet available.
