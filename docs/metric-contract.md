# BI metric contract

## Purpose and reporting grain

This contract defines the analytical meaning of the annual weather metrics exposed to Power BI.
It prevents incomplete source coverage, implicit weighting and ambiguous threshold definitions
from changing a result silently.

`layer_gold.fact_weather_station_year` has exactly one row per:

```text
station_key + calendar_year
```

`station_key` identifies one stable physical IMGW series and does not change when its name or
metadata changes. Reporting geography is supplied by
`layer_gold.dim_reporting_location`, whose grain is one stable project reporting location.
Historical metadata versions are stored separately in `layer_gold.dim_station_version` and are
used only by the daily fact. This keeps a station-year complete when a version starts or ends
during the year and retains partial first or final station-years for quality monitoring.
`layer_gold.dim_year` provides the conformed one-side relationship to both annual rows and daily
dates.

## Completeness

The expected denominator is 365 or 366 calendar days. A year is complete only when the warehouse
contains observations through 31 December of that year. The latest partial year remains visible
for quality monitoring but none of its annual metrics are reportable.

Completeness is evaluated independently for:

- daily mean air temperature;
- daily maximum air temperature;
- daily minimum air temperature;
- daily precipitation total;
- snow-cover occurrence status.

A metric is reportable when the year is complete and at least 95% of its expected daily values
are non-null. A row count cannot substitute for measure-specific completeness.

`precipitation_observed_days` counts days with a known precipitation total, including
explicit dry days normalized to `0 mm`. It does not mean the number of rainy days.

`snow_cover_observed_days` counts days where snow-cover occurrence is analytically known. A
known `false` is an observed day without snow and is part of coverage; `NULL` means the occurrence
cannot be established. The analytical value uses this precedence:

1. valid source occurrence (`0` or `1`);
2. positive valid snow depth as `true`;
3. zero valid depth or depth status `9` as `false`;
4. otherwise `NULL`.

Occurrence status `8` is never inferred from depth. Daily rows retain
`snow_cover_occurred_source` and `snow_cover_occurrence_provenance` so an inferred value is never
presented as a direct source observation.

Annual metric columns are set to `NULL` when their contract is not met. This makes an incomplete
annual result unavailable by default instead of relying on a hidden report filter.

Power BI coverage measures are weighted by the expected station-day denominator:

```text
coverage = sum(observed measure days) / sum(expected days)
```

The temperature reporting rate uses complete station-years as its denominator. A partial current
year is therefore visible for coverage monitoring without being classified as a reporting
failure.

## Metric definitions

| Metric | Station-year formula | Eligibility |
| --- | --- | --- |
| Annual average air temperature | arithmetic mean of valid daily mean temperatures | mean-temperature coverage |
| Annual maximum air temperature | maximum of valid daily maximum temperatures | maximum-temperature coverage |
| Annual minimum air temperature | minimum of valid daily minimum temperatures | minimum-temperature coverage |
| Annual precipitation total | sum of valid daily precipitation totals | precipitation coverage |
| Hot days | count of days with maximum temperature `>= 30°C` | maximum-temperature coverage |
| Very hot days | count of days with maximum temperature `>= 35°C` | maximum-temperature coverage |
| Cold nights | count of days with minimum temperature `<= -20°C` | minimum-temperature coverage |
| Very cold nights | count of days with minimum temperature `<= -25°C` | minimum-temperature coverage |
| Snow-cover days | count of days where analytical snow-cover occurrence is true | snow-cover occurrence coverage |

Temperature comparisons are inclusive. Cold metrics intentionally use daily minimum temperature;
using daily maximum temperature would describe a different and much rarer phenomenon.

## Aggregation rules

Regional and national annual temperature and precipitation metrics use equal station weighting:

1. calculate the eligible annual metric for each station;
2. exclude `NULL` station-year results;
3. calculate the arithmetic mean of the remaining station results.

Power BI must therefore use `AVERAGE` over the annual fact columns. It must not average daily
rows directly and must not weight a station by the number of available daily observations.

Annual precipitation must not be split by the daily `precipitation_type` attribute. A daily
classification has no unique annual category and would fragment the station-year total.

## Time-series rules

Full-year trends use reportable annual values only. The incomplete latest year is excluded.
If a YTD comparison is added later, it must be a separate metric that compares identical
calendar-day ranges and is labelled as YTD.

A trailing 10-year average includes the selected year and the preceding nine years. It is
reported only when all ten annual values exist in the current reporting context.

Annual record labels mean:

- hottest day: maximum of `annual_max_air_temperature_c`;
- coldest night: minimum of `annual_min_air_temperature_c`.

## Power BI usage

The annual trend, annual precipitation and annual threshold visuals should use
`fact_weather_station_year`. Daily exploration may use `fact_weather_daily`.
The legacy global filter based on more than 360 observation rows must not be used.

The final distributable report will be a data-free Power BI template with parameterized
PostgreSQL server, port and database values. Credentials must be supplied by each user and must
never be stored in the repository.
