# Station metadata

## Sources and ownership

Historical station metadata comes from the public IMGW-PIB climate metadata portal:

```text
https://klimat.imgw.pl/json/stacje.json
```

The committed UTF-8 snapshot contains only station codes used by this project. It preserves the
official station name, validity period, station type, data rank, latitude, longitude and
elevation. `source_url` and `source_retrieved_at` make the snapshot auditable and reproducible.

The upstream payload contains mixed Windows-1250 and UTF-8 strings. The update script decodes
each field and writes one consistent UTF-8 CSV. One IMGW record represents a year-only boundary
(`1956`). The snapshot normalizes this boundary to a 1956-01-01 start and a 1955-12-31 end so
inclusive validity periods do not overlap.

The official history does not cover every calendar day for every project station. The snapshot
therefore inserts explicit `metadata_status=unavailable` periods between official records and
after a closed final record. These rows deliberately leave the official name, coordinates and
elevation empty. They preserve fact coverage without presenting inferred geography as official
data. Reporting location and voivodeship remain available from the separate project contract.

Run the following command to review a newer source snapshot:

```bash
python scripts/update_station_metadata.py
```

Changes to a snapshot must be reviewed like code because IMGW states that its metadata is
updated and may be supplemented when new historical information becomes available.

## Reporting geography

`station_reporting_location.csv` is a project-owned reporting contract. It consolidates station
aliases into stable locations and assigns each location to one of Poland's 16 contemporary
voivodeships. The assignments are reviewed against the current GUS TERYT register. `source_url`
and `source_as_of` preserve the administrative classification provenance:

```text
https://eteryt.stat.gov.pl/eTeryt/rejestr_teryt/teryt_rejestr.aspx
```

This classification answers the current BI question, "Which voivodeship is this reporting
location in?" It must not be interpreted as a reconstruction of administrative boundaries for
the historical observation date.

## Dimensional behavior

`layer_gold.dim_station` uses SCD Type 2 grain:

```text
station_code + valid_from
```

The daily fact joins a station version when:

```text
observation_date >= valid_from
AND (valid_to IS NULL OR observation_date <= valid_to)
```

The refresh fails unless every fact row matches exactly one version. This prevents silent gaps
and ambiguous assignments.
