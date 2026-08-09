-- IMGW Weather ETL warehouse baseline schema.
-- This file is executed automatically only when the Docker database volume is created.

CREATE SCHEMA layer_bronze;
CREATE SCHEMA layer_silver;
CREATE SCHEMA layer_gold;

-- Bronze preserves the source fields and IMGW measurement statuses.
CREATE TABLE layer_bronze.synop_s_d_imgw (
    nsp bigint,
    post text,
    rok smallint,
    mc smallint,
    dz smallint,
    tmax double precision,
    wtmax smallint,
    tmin double precision,
    wtmin smallint,
    std double precision,
    wstd smallint,
    tmng double precision,
    wtmng smallint,
    smdb double precision,
    wsmdb smallint,
    roop text,
    pksn double precision,
    wpksn smallint,
    rwsn double precision,
    wrwsn smallint,
    usl double precision,
    wusl smallint,
    desz double precision,
    wdesz smallint,
    sneg double precision,
    wsneg smallint,
    disn double precision,
    wdisn smallint,
    grad double precision,
    wgrad smallint,
    mgla double precision,
    wmgla smallint,
    zmgl double precision,
    wzmgl smallint,
    sadz double precision,
    wsadz smallint,
    golo double precision,
    wgolo smallint,
    zmni double precision,
    wzmni smallint,
    zmws double precision,
    wzmws smallint,
    zmet double precision,
    wzmet smallint,
    ff10 double precision,
    wff10 smallint,
    ff15 double precision,
    wff15 smallint,
    brza double precision,
    wbrza smallint,
    rosa double precision,
    wrosa smallint,
    szro double precision,
    wszro smallint,
    dzps smallint,
    wdzps smallint,
    dzbl smallint,
    wdzbl smallint,
    sgr text,
    izd double precision,
    wizd smallint,
    izg double precision,
    wizg smallint,
    aktn double precision,
    waktn smallint
);

CREATE TABLE layer_bronze.synop_s_d_t_imgw (
    nsp bigint,
    post text,
    rok smallint,
    mc smallint,
    dz smallint,
    nos double precision,
    wnos smallint,
    fws double precision,
    wfws smallint,
    temp double precision,
    wtemp smallint,
    cpw double precision,
    wcpw smallint,
    wlgs double precision,
    wwlgs smallint,
    ppps double precision,
    wppps smallint,
    pppm double precision,
    wpppm smallint,
    wodz double precision,
    wwodz smallint,
    wono double precision,
    wwono smallint
);

CREATE DOMAIN layer_silver.measurement_status AS smallint
    CHECK (VALUE IS NULL OR VALUE IN (8, 9));

-- Source station names are aliases because IMGW names change over time.
CREATE TABLE layer_silver.station_alias (
    station_name text NOT NULL,
    station_code bigint NOT NULL,
    location_id text NOT NULL,
    CONSTRAINT station_alias_station_name_uk UNIQUE (station_name)
);

CREATE INDEX station_alias_station_code_idx
    ON layer_silver.station_alias (station_code);

-- Contemporary reporting geography used by Power BI.
CREATE TABLE layer_silver.station_reporting_location (
    location_id text PRIMARY KEY,
    location_name text NOT NULL UNIQUE,
    location_type text NOT NULL,
    voivodeship text NOT NULL,
    source_url text NOT NULL,
    source_as_of date NOT NULL
);

ALTER TABLE layer_silver.station_alias
    ADD CONSTRAINT station_alias_location_fk
    FOREIGN KEY (location_id)
    REFERENCES layer_silver.station_reporting_location (location_id);

-- Official IMGW station history. Validity intervals are inclusive.
CREATE TABLE layer_silver.station_metadata_history (
    station_code bigint NOT NULL,
    official_station_name text,
    valid_from date NOT NULL,
    valid_to date,
    station_type text,
    data_rank text,
    latitude double precision,
    longitude double precision,
    elevation_m double precision,
    metadata_status text NOT NULL,
    source_url text NOT NULL,
    source_retrieved_at date NOT NULL,
    CONSTRAINT station_metadata_history_pk
        PRIMARY KEY (station_code, valid_from),
    CONSTRAINT station_metadata_history_period_ck
        CHECK (valid_to IS NULL OR valid_to >= valid_from),
    CONSTRAINT station_metadata_history_status_ck
        CHECK (metadata_status IN ('official', 'unavailable')),
    CONSTRAINT station_metadata_history_latitude_ck
        CHECK (latitude BETWEEN 48.5 AND 55.5),
    CONSTRAINT station_metadata_history_longitude_ck
        CHECK (longitude BETWEEN 13.5 AND 24.5)
);

-- One row per IMGW station and observation day.
CREATE TABLE layer_silver.weather_daily (
    station_code bigint NOT NULL,
    station_name text NOT NULL,
    observation_date date NOT NULL,
    max_air_temperature_c double precision,
    max_air_temperature_status layer_silver.measurement_status,
    min_air_temperature_c double precision,
    min_air_temperature_status layer_silver.measurement_status,
    avg_air_temperature_c double precision,
    avg_air_temperature_status layer_silver.measurement_status,
    min_ground_temperature_c double precision,
    min_ground_temperature_status layer_silver.measurement_status,
    precipitation_total_mm double precision,
    precipitation_total_status layer_silver.measurement_status,
    precipitation_type text,
    snow_depth_cm double precision,
    snow_depth_status layer_silver.measurement_status,
    snow_water_equivalent_mm_cm double precision,
    snow_water_equivalent_status layer_silver.measurement_status,
    sunshine_duration_h double precision,
    sunshine_duration_status layer_silver.measurement_status,
    rain_duration_h double precision,
    rain_duration_status layer_silver.measurement_status,
    snowfall_duration_h double precision,
    snowfall_duration_status layer_silver.measurement_status,
    sleet_duration_h double precision,
    sleet_duration_status layer_silver.measurement_status,
    hail_duration_h double precision,
    hail_duration_status layer_silver.measurement_status,
    fog_duration_h double precision,
    fog_duration_status layer_silver.measurement_status,
    mist_duration_h double precision,
    mist_duration_status layer_silver.measurement_status,
    rime_duration_h double precision,
    rime_duration_status layer_silver.measurement_status,
    glaze_duration_h double precision,
    glaze_duration_status layer_silver.measurement_status,
    low_drifting_snow_duration_h double precision,
    low_drifting_snow_status layer_silver.measurement_status,
    high_drifting_snow_duration_h double precision,
    high_drifting_snow_status layer_silver.measurement_status,
    haze_duration_h double precision,
    haze_duration_status layer_silver.measurement_status,
    wind_ge_10_m_s_duration_h double precision,
    wind_ge_10_m_s_status layer_silver.measurement_status,
    wind_gt_15_m_s_duration_h double precision,
    wind_gt_15_m_s_status layer_silver.measurement_status,
    thunderstorm_duration_h double precision,
    thunderstorm_duration_status layer_silver.measurement_status,
    dew_duration_h double precision,
    dew_duration_status layer_silver.measurement_status,
    frost_duration_h double precision,
    frost_duration_status layer_silver.measurement_status,
    snow_cover_occurred_source boolean,
    snow_cover_occurred boolean,
    snow_cover_occurrence_provenance text NOT NULL DEFAULT 'unavailable',
    snow_cover_occurrence_status layer_silver.measurement_status,
    lightning_occurred boolean,
    lightning_occurrence_status layer_silver.measurement_status,
    ground_condition text,
    lower_isotherm_cm double precision,
    lower_isotherm_status layer_silver.measurement_status,
    upper_isotherm_cm double precision,
    upper_isotherm_status layer_silver.measurement_status,
    actinometry_j_cm2 double precision,
    actinometry_status layer_silver.measurement_status,
    avg_cloud_cover_oktas double precision,
    avg_cloud_cover_status layer_silver.measurement_status,
    avg_wind_speed_m_s double precision,
    avg_wind_speed_status layer_silver.measurement_status,
    secondary_avg_air_temperature_c double precision,
    secondary_avg_air_temperature_status layer_silver.measurement_status,
    avg_vapour_pressure_hpa double precision,
    avg_vapour_pressure_status layer_silver.measurement_status,
    avg_relative_humidity_pct double precision,
    avg_relative_humidity_status layer_silver.measurement_status,
    avg_station_pressure_hpa double precision,
    avg_station_pressure_status layer_silver.measurement_status,
    avg_sea_level_pressure_hpa double precision,
    avg_sea_level_pressure_status layer_silver.measurement_status,
    daytime_precipitation_mm double precision,
    daytime_precipitation_status layer_silver.measurement_status,
    nighttime_precipitation_mm double precision,
    nighttime_precipitation_status layer_silver.measurement_status,
    CONSTRAINT weather_daily_pk PRIMARY KEY (station_code, observation_date),
    CONSTRAINT weather_daily_snow_provenance_ck CHECK (
        (
            snow_cover_occurrence_provenance = 'source_occurrence'
            AND snow_cover_occurred_source IS NOT NULL
            AND snow_cover_occurred = snow_cover_occurred_source
        ) OR (
            snow_cover_occurrence_provenance = 'inferred_from_depth'
            AND snow_cover_occurred_source IS NULL
            AND snow_cover_occurred IS NOT NULL
        ) OR (
            snow_cover_occurrence_provenance = 'unavailable'
            AND snow_cover_occurred_source IS NULL
            AND snow_cover_occurred IS NULL
        )
    )
);

CREATE INDEX weather_daily_observation_date_idx
    ON layer_silver.weather_daily (observation_date);

-- Conformed year dimension shared by daily and annual facts.
CREATE TABLE layer_gold.dim_year (
    year smallint PRIMARY KEY,
    expected_days smallint NOT NULL,
    is_leap_year boolean NOT NULL,
    is_complete_year boolean NOT NULL,
    CONSTRAINT dim_year_expected_days_ck CHECK (expected_days IN (365, 366))
);

-- Conformed date dimension for Power BI.
CREATE TABLE layer_gold.dim_date (
    date_key integer PRIMARY KEY,
    full_date date NOT NULL UNIQUE,
    year smallint NOT NULL,
    quarter smallint NOT NULL,
    month smallint NOT NULL,
    month_name text NOT NULL,
    day smallint NOT NULL,
    day_of_year smallint NOT NULL,
    days_in_year smallint NOT NULL,
    is_leap_year boolean NOT NULL,
    CONSTRAINT dim_date_year_fk
        FOREIGN KEY (year) REFERENCES layer_gold.dim_year (year)
);

-- Stable reporting geography shared by daily and annual BI metrics.
CREATE TABLE layer_gold.dim_reporting_location (
    location_key bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    location_id text NOT NULL UNIQUE,
    location_name text NOT NULL,
    location_type text NOT NULL,
    voivodeship text NOT NULL
);

-- Stable station entity: one row per physical IMGW station series.
CREATE TABLE layer_gold.dim_station (
    station_key bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    station_code bigint NOT NULL UNIQUE,
    station_name text NOT NULL,
    location_key bigint NOT NULL,
    CONSTRAINT dim_station_location_fk
        FOREIGN KEY (location_key)
        REFERENCES layer_gold.dim_reporting_location (location_key)
);

-- SCD Type 2: one row per station metadata validity period.
CREATE TABLE layer_gold.dim_station_version (
    station_version_key bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    station_key bigint NOT NULL,
    station_code bigint NOT NULL,
    official_station_name text,
    valid_from date NOT NULL,
    valid_to date,
    is_current boolean NOT NULL,
    station_type text,
    data_rank text,
    latitude double precision,
    longitude double precision,
    elevation_m double precision,
    metadata_status text NOT NULL,
    CONSTRAINT dim_station_version_uk UNIQUE (station_key, valid_from),
    CONSTRAINT dim_station_period_ck
        CHECK (valid_to IS NULL OR valid_to >= valid_from),
    CONSTRAINT dim_station_version_station_fk
        FOREIGN KEY (station_key) REFERENCES layer_gold.dim_station (station_key),
    CONSTRAINT dim_station_version_code_uk UNIQUE (station_code, valid_from)
);

-- One row per station and observation day. Descriptive attributes live in dimensions.
CREATE TABLE layer_gold.fact_weather_daily (
    date_key integer NOT NULL,
    station_key bigint NOT NULL,
    station_version_key bigint NOT NULL,
    max_air_temperature_c double precision,
    min_air_temperature_c double precision,
    avg_air_temperature_c double precision,
    min_ground_temperature_c double precision,
    precipitation_total_mm double precision,
    precipitation_type text,
    snow_depth_cm double precision,
    snow_water_equivalent_mm_cm double precision,
    sunshine_duration_h double precision,
    rain_duration_h double precision,
    snowfall_duration_h double precision,
    sleet_duration_h double precision,
    hail_duration_h double precision,
    fog_duration_h double precision,
    mist_duration_h double precision,
    rime_duration_h double precision,
    glaze_duration_h double precision,
    low_drifting_snow_duration_h double precision,
    high_drifting_snow_duration_h double precision,
    haze_duration_h double precision,
    wind_ge_10_m_s_duration_h double precision,
    wind_gt_15_m_s_duration_h double precision,
    thunderstorm_duration_h double precision,
    dew_duration_h double precision,
    frost_duration_h double precision,
    snow_cover_occurred_source boolean,
    snow_cover_occurred boolean,
    snow_cover_occurrence_provenance text NOT NULL DEFAULT 'unavailable',
    lightning_occurred boolean,
    ground_condition text,
    lower_isotherm_cm double precision,
    upper_isotherm_cm double precision,
    actinometry_j_cm2 double precision,
    avg_cloud_cover_oktas double precision,
    avg_wind_speed_m_s double precision,
    avg_vapour_pressure_hpa double precision,
    avg_relative_humidity_pct double precision,
    avg_station_pressure_hpa double precision,
    avg_sea_level_pressure_hpa double precision,
    daytime_precipitation_mm double precision,
    nighttime_precipitation_mm double precision,
    CONSTRAINT fact_weather_daily_pk PRIMARY KEY (date_key, station_key),
    CONSTRAINT fact_weather_daily_date_fk
        FOREIGN KEY (date_key) REFERENCES layer_gold.dim_date (date_key),
    CONSTRAINT fact_weather_daily_station_fk
        FOREIGN KEY (station_key) REFERENCES layer_gold.dim_station (station_key),
    CONSTRAINT fact_weather_daily_station_version_fk
        FOREIGN KEY (station_version_key)
        REFERENCES layer_gold.dim_station_version (station_version_key),
    CONSTRAINT fact_weather_daily_snow_provenance_ck CHECK (
        (
            snow_cover_occurrence_provenance = 'source_occurrence'
            AND snow_cover_occurred_source IS NOT NULL
            AND snow_cover_occurred = snow_cover_occurred_source
        ) OR (
            snow_cover_occurrence_provenance = 'inferred_from_depth'
            AND snow_cover_occurred_source IS NULL
            AND snow_cover_occurred IS NOT NULL
        ) OR (
            snow_cover_occurrence_provenance = 'unavailable'
            AND snow_cover_occurred_source IS NULL
            AND snow_cover_occurred IS NULL
        )
    )
);

CREATE INDEX fact_weather_daily_station_date_idx
    ON layer_gold.fact_weather_daily (station_key, date_key);

-- One row per stable station and calendar year.
-- Annual metrics are NULL unless their own source measure meets the reporting contract.
CREATE TABLE layer_gold.fact_weather_station_year (
    station_key bigint NOT NULL,
    year smallint NOT NULL,
    expected_days smallint NOT NULL,
    observation_days smallint NOT NULL,
    avg_temperature_days smallint NOT NULL,
    max_temperature_days smallint NOT NULL,
    min_temperature_days smallint NOT NULL,
    precipitation_observed_days smallint NOT NULL,
    snow_cover_observed_days smallint NOT NULL,
    avg_temperature_coverage numeric(6, 5) NOT NULL,
    max_temperature_coverage numeric(6, 5) NOT NULL,
    min_temperature_coverage numeric(6, 5) NOT NULL,
    precipitation_coverage numeric(6, 5) NOT NULL,
    snow_cover_coverage numeric(6, 5) NOT NULL,
    is_complete_year boolean NOT NULL,
    is_avg_temperature_reportable boolean NOT NULL,
    is_max_temperature_reportable boolean NOT NULL,
    is_min_temperature_reportable boolean NOT NULL,
    is_precipitation_reportable boolean NOT NULL,
    is_snow_cover_reportable boolean NOT NULL,
    annual_avg_air_temperature_c double precision,
    annual_max_air_temperature_c double precision,
    annual_min_air_temperature_c double precision,
    annual_precipitation_total_mm double precision,
    hot_days_ge_30_c smallint,
    very_hot_days_ge_35_c smallint,
    cold_nights_le_minus_20_c smallint,
    very_cold_nights_le_minus_25_c smallint,
    snow_cover_days smallint,
    CONSTRAINT fact_weather_station_year_pk PRIMARY KEY (station_key, year),
    CONSTRAINT fact_weather_station_year_station_fk
        FOREIGN KEY (station_key) REFERENCES layer_gold.dim_station (station_key),
    CONSTRAINT fact_weather_station_year_year_fk
        FOREIGN KEY (year) REFERENCES layer_gold.dim_year (year),
    CONSTRAINT fact_weather_station_year_expected_days_ck
        CHECK (expected_days IN (365, 366)),
    CONSTRAINT fact_weather_station_year_day_counts_ck CHECK (
        observation_days BETWEEN 0 AND expected_days
        AND avg_temperature_days BETWEEN 0 AND expected_days
        AND max_temperature_days BETWEEN 0 AND expected_days
        AND min_temperature_days BETWEEN 0 AND expected_days
        AND precipitation_observed_days BETWEEN 0 AND expected_days
        AND snow_cover_observed_days BETWEEN 0 AND expected_days
    ),
    CONSTRAINT fact_weather_station_year_coverage_ck CHECK (
        avg_temperature_coverage BETWEEN 0 AND 1
        AND max_temperature_coverage BETWEEN 0 AND 1
        AND min_temperature_coverage BETWEEN 0 AND 1
        AND precipitation_coverage BETWEEN 0 AND 1
        AND snow_cover_coverage BETWEEN 0 AND 1
    )
);

CREATE INDEX fact_weather_station_year_year_idx
    ON layer_gold.fact_weather_station_year (year);

CREATE PROCEDURE layer_silver.refresh()
LANGUAGE plpgsql
AS $$
BEGIN
    TRUNCATE TABLE layer_silver.weather_daily;

    INSERT INTO layer_silver.weather_daily (
        station_code, station_name, observation_date,
        max_air_temperature_c, max_air_temperature_status,
        min_air_temperature_c, min_air_temperature_status,
        avg_air_temperature_c, avg_air_temperature_status,
        min_ground_temperature_c, min_ground_temperature_status,
        precipitation_total_mm, precipitation_total_status, precipitation_type,
        snow_depth_cm, snow_depth_status,
        snow_water_equivalent_mm_cm, snow_water_equivalent_status,
        sunshine_duration_h, sunshine_duration_status,
        rain_duration_h, rain_duration_status,
        snowfall_duration_h, snowfall_duration_status,
        sleet_duration_h, sleet_duration_status,
        hail_duration_h, hail_duration_status,
        fog_duration_h, fog_duration_status,
        mist_duration_h, mist_duration_status,
        rime_duration_h, rime_duration_status,
        glaze_duration_h, glaze_duration_status,
        low_drifting_snow_duration_h, low_drifting_snow_status,
        high_drifting_snow_duration_h, high_drifting_snow_status,
        haze_duration_h, haze_duration_status,
        wind_ge_10_m_s_duration_h, wind_ge_10_m_s_status,
        wind_gt_15_m_s_duration_h, wind_gt_15_m_s_status,
        thunderstorm_duration_h, thunderstorm_duration_status,
        dew_duration_h, dew_duration_status,
        frost_duration_h, frost_duration_status,
        snow_cover_occurred_source, snow_cover_occurred,
        snow_cover_occurrence_provenance, snow_cover_occurrence_status,
        lightning_occurred, lightning_occurrence_status,
        ground_condition,
        lower_isotherm_cm, lower_isotherm_status,
        upper_isotherm_cm, upper_isotherm_status,
        actinometry_j_cm2, actinometry_status,
        avg_cloud_cover_oktas, avg_cloud_cover_status,
        avg_wind_speed_m_s, avg_wind_speed_status,
        secondary_avg_air_temperature_c, secondary_avg_air_temperature_status,
        avg_vapour_pressure_hpa, avg_vapour_pressure_status,
        avg_relative_humidity_pct, avg_relative_humidity_status,
        avg_station_pressure_hpa, avg_station_pressure_status,
        avg_sea_level_pressure_hpa, avg_sea_level_pressure_status,
        daytime_precipitation_mm, daytime_precipitation_status,
        nighttime_precipitation_mm, nighttime_precipitation_status
    )
    SELECT
        source.nsp,
        trim(source.post),
        make_date(source.rok, source.mc, source.dz),
        CASE WHEN source.wtmax = 8 THEN NULL ELSE source.tmax END, source.wtmax,
        CASE WHEN source.wtmin = 8 THEN NULL ELSE source.tmin END, source.wtmin,
        CASE WHEN source.wstd = 8 THEN NULL ELSE source.std END, source.wstd,
        CASE WHEN source.wtmng = 8 THEN NULL ELSE source.tmng END, source.wtmng,
        CASE
            WHEN source.wsmdb = 8 THEN NULL
            WHEN source.wsmdb = 9 THEN 0
            ELSE source.smdb
        END,
        source.wsmdb,
        nullif(trim(source.roop), ''),
        CASE WHEN source.wpksn = 8 THEN NULL ELSE source.pksn END, source.wpksn,
        CASE WHEN source.wrwsn = 8 THEN NULL ELSE source.rwsn END, source.wrwsn,
        CASE WHEN source.wusl = 8 THEN NULL ELSE source.usl END, source.wusl,
        CASE WHEN source.wdesz = 8 THEN NULL ELSE source.desz END, source.wdesz,
        CASE WHEN source.wsneg = 8 THEN NULL ELSE source.sneg END, source.wsneg,
        CASE WHEN source.wdisn = 8 THEN NULL ELSE source.disn END, source.wdisn,
        CASE WHEN source.wgrad = 8 THEN NULL ELSE source.grad END, source.wgrad,
        CASE WHEN source.wmgla = 8 THEN NULL ELSE source.mgla END, source.wmgla,
        CASE WHEN source.wzmgl = 8 THEN NULL ELSE source.zmgl END, source.wzmgl,
        CASE WHEN source.wsadz = 8 THEN NULL ELSE source.sadz END, source.wsadz,
        CASE WHEN source.wgolo = 8 THEN NULL ELSE source.golo END, source.wgolo,
        CASE WHEN source.wzmni = 8 THEN NULL ELSE source.zmni END, source.wzmni,
        CASE WHEN source.wzmws = 8 THEN NULL ELSE source.zmws END, source.wzmws,
        CASE WHEN source.wzmet = 8 THEN NULL ELSE source.zmet END, source.wzmet,
        CASE WHEN source.wff10 = 8 THEN NULL ELSE source.ff10 END, source.wff10,
        CASE WHEN source.wff15 = 8 THEN NULL ELSE source.ff15 END, source.wff15,
        CASE WHEN source.wbrza = 8 THEN NULL ELSE source.brza END, source.wbrza,
        CASE WHEN source.wrosa = 8 THEN NULL ELSE source.rosa END, source.wrosa,
        CASE WHEN source.wszro = 8 THEN NULL ELSE source.szro END, source.wszro,
        CASE
            WHEN source.wdzps = 8 OR source.dzps NOT IN (0, 1) THEN NULL
            ELSE source.dzps = 1
        END,
        CASE
            WHEN source.wdzps IS DISTINCT FROM 8 AND source.dzps IN (0, 1)
                THEN source.dzps = 1
            WHEN source.wdzps = 8 THEN NULL
            WHEN source.wpksn = 8 THEN NULL
            WHEN source.pksn > 0 THEN true
            WHEN source.pksn = 0 OR source.wpksn = 9 THEN false
            ELSE NULL
        END,
        CASE
            WHEN source.wdzps IS DISTINCT FROM 8 AND source.dzps IN (0, 1)
                THEN 'source_occurrence'
            WHEN source.wdzps = 8 THEN 'unavailable'
            WHEN source.wpksn = 8 THEN 'unavailable'
            WHEN source.pksn >= 0 OR source.wpksn = 9
                THEN 'inferred_from_depth'
            ELSE 'unavailable'
        END,
        source.wdzps,
        CASE
            WHEN source.wdzbl = 8 OR source.dzbl NOT IN (0, 1) THEN NULL
            ELSE source.dzbl = 1
        END,
        source.wdzbl,
        nullif(trim(source.sgr), ''),
        CASE WHEN source.wizd = 8 THEN NULL ELSE source.izd END, source.wizd,
        CASE WHEN source.wizg = 8 THEN NULL ELSE source.izg END, source.wizg,
        CASE WHEN source.waktn = 8 THEN NULL ELSE source.aktn END, source.waktn,
        CASE WHEN secondary.wnos = 8 THEN NULL ELSE secondary.nos END, secondary.wnos,
        CASE WHEN secondary.wfws = 8 THEN NULL ELSE secondary.fws END, secondary.wfws,
        CASE WHEN secondary.wtemp = 8 THEN NULL ELSE secondary.temp END, secondary.wtemp,
        CASE WHEN secondary.wcpw = 8 THEN NULL ELSE secondary.cpw END, secondary.wcpw,
        CASE WHEN secondary.wwlgs = 8 THEN NULL ELSE secondary.wlgs END, secondary.wwlgs,
        CASE WHEN secondary.wppps = 8 THEN NULL ELSE secondary.ppps END, secondary.wppps,
        CASE WHEN secondary.wpppm = 8 THEN NULL ELSE secondary.pppm END, secondary.wpppm,
        CASE WHEN secondary.wwodz = 8 THEN NULL ELSE secondary.wodz END, secondary.wwodz,
        CASE WHEN secondary.wwono = 8 THEN NULL ELSE secondary.wono END, secondary.wwono
    FROM layer_bronze.synop_s_d_imgw AS source
    LEFT JOIN layer_bronze.synop_s_d_t_imgw AS secondary
        ON secondary.nsp = source.nsp
       AND secondary.rok = source.rok
       AND secondary.mc = source.mc
       AND secondary.dz = source.dz;
END;
$$;

CREATE PROCEDURE layer_gold.refresh()
LANGUAGE plpgsql
AS $$
DECLARE
    first_date date;
    last_date date;
BEGIN
    SELECT min(observation_date), max(observation_date)
    INTO first_date, last_date
    FROM layer_silver.weather_daily;

    IF first_date IS NULL OR last_date IS NULL THEN
        RAISE EXCEPTION 'Cannot refresh Gold from an empty Silver weather table';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM layer_silver.weather_daily AS weather
        LEFT JOIN layer_silver.station_alias AS alias
            ON alias.station_code = weather.station_code
        WHERE alias.station_code IS NULL
    ) THEN
        RAISE EXCEPTION 'Cannot refresh Gold: station alias mapping is incomplete';
    END IF;

    IF EXISTS (
        SELECT alias.station_code
        FROM layer_silver.station_alias AS alias
        GROUP BY alias.station_code
        HAVING count(DISTINCT alias.location_id) > 1
    ) THEN
        RAISE EXCEPTION 'Cannot refresh Gold: a station code maps to multiple locations';
    END IF;

    IF EXISTS (
        SELECT weather.station_code, weather.observation_date
        FROM layer_silver.weather_daily AS weather
        LEFT JOIN layer_silver.station_metadata_history AS metadata
            ON metadata.station_code = weather.station_code
           AND weather.observation_date >= metadata.valid_from
           AND (
                metadata.valid_to IS NULL
                OR weather.observation_date <= metadata.valid_to
           )
        GROUP BY weather.station_code, weather.observation_date
        HAVING count(metadata.station_code) <> 1
    ) THEN
        RAISE EXCEPTION
            'Cannot refresh Gold: every observation must match exactly one station metadata period';
    END IF;

    TRUNCATE TABLE
        layer_gold.fact_weather_station_year,
        layer_gold.fact_weather_daily,
        layer_gold.dim_date,
        layer_gold.dim_station_version,
        layer_gold.dim_station,
        layer_gold.dim_reporting_location,
        layer_gold.dim_year
    RESTART IDENTITY;

    INSERT INTO layer_gold.dim_year (
        year, expected_days, is_leap_year, is_complete_year
    )
    SELECT
        calendar_year::smallint,
        (
            make_date(calendar_year + 1, 1, 1)
            - make_date(calendar_year, 1, 1)
        )::smallint,
        (
            make_date(calendar_year + 1, 1, 1)
            - make_date(calendar_year, 1, 1)
        ) = 366,
        make_date(calendar_year + 1, 1, 1) - 1 <= last_date
    FROM generate_series(
        extract(year FROM first_date)::integer,
        extract(year FROM last_date)::integer
    ) AS years(calendar_year);

    INSERT INTO layer_gold.dim_date (
        date_key, full_date, year, quarter, month, month_name, day,
        day_of_year, days_in_year, is_leap_year
    )
    SELECT
        to_char(calendar_date, 'YYYYMMDD')::integer,
        calendar_date,
        extract(year FROM calendar_date)::smallint,
        extract(quarter FROM calendar_date)::smallint,
        extract(month FROM calendar_date)::smallint,
        CASE extract(month FROM calendar_date)::smallint
            WHEN 1 THEN 'January' WHEN 2 THEN 'February' WHEN 3 THEN 'March'
            WHEN 4 THEN 'April' WHEN 5 THEN 'May' WHEN 6 THEN 'June'
            WHEN 7 THEN 'July' WHEN 8 THEN 'August' WHEN 9 THEN 'September'
            WHEN 10 THEN 'October' WHEN 11 THEN 'November' WHEN 12 THEN 'December'
        END,
        extract(day FROM calendar_date)::smallint,
        extract(doy FROM calendar_date)::smallint,
        (
            make_date(extract(year FROM calendar_date)::integer + 1, 1, 1)
            - make_date(extract(year FROM calendar_date)::integer, 1, 1)
        )::smallint,
        (
            make_date(extract(year FROM calendar_date)::integer + 1, 1, 1)
            - make_date(extract(year FROM calendar_date)::integer, 1, 1)
        ) = 366
    FROM generate_series(first_date, last_date, interval '1 day') AS dates(calendar_date);

    INSERT INTO layer_gold.dim_reporting_location (
        location_id, location_name, location_type, voivodeship
    )
    SELECT
        location_id,
        location_name,
        location_type,
        voivodeship
    FROM layer_silver.station_reporting_location
    ORDER BY location_id;

    INSERT INTO layer_gold.dim_station (
        station_code, station_name, location_key
    )
    SELECT
        code_location.station_code,
        code_location.station_name,
        location.location_key
    FROM (
        SELECT
            alias.station_code,
            min(alias.location_id) AS location_id,
            min(alias.station_name) AS station_name
        FROM layer_silver.station_alias AS alias
        GROUP BY alias.station_code
    ) AS code_location
    JOIN layer_gold.dim_reporting_location AS location
        ON location.location_id = code_location.location_id
    ORDER BY code_location.station_code;

    INSERT INTO layer_gold.dim_station_version (
        station_key, station_code, official_station_name,
        valid_from, valid_to, is_current, station_type, data_rank,
        latitude, longitude, elevation_m, metadata_status
    )
    SELECT
        station.station_key,
        metadata.station_code,
        metadata.official_station_name,
        metadata.valid_from,
        metadata.valid_to,
        metadata.valid_to IS NULL,
        metadata.station_type,
        metadata.data_rank,
        metadata.latitude,
        metadata.longitude,
        metadata.elevation_m,
        metadata.metadata_status
    FROM layer_silver.station_metadata_history AS metadata
    JOIN layer_gold.dim_station AS station
        ON station.station_code = metadata.station_code
    ORDER BY metadata.station_code, metadata.valid_from;

    INSERT INTO layer_gold.fact_weather_daily (
        date_key, station_key, station_version_key,
        max_air_temperature_c, min_air_temperature_c, avg_air_temperature_c,
        min_ground_temperature_c, precipitation_total_mm, precipitation_type,
        snow_depth_cm, snow_water_equivalent_mm_cm, sunshine_duration_h,
        rain_duration_h, snowfall_duration_h, sleet_duration_h, hail_duration_h,
        fog_duration_h, mist_duration_h, rime_duration_h, glaze_duration_h,
        low_drifting_snow_duration_h, high_drifting_snow_duration_h, haze_duration_h,
        wind_ge_10_m_s_duration_h, wind_gt_15_m_s_duration_h,
        thunderstorm_duration_h, dew_duration_h, frost_duration_h,
        snow_cover_occurred_source, snow_cover_occurred,
        snow_cover_occurrence_provenance, lightning_occurred, ground_condition,
        lower_isotherm_cm, upper_isotherm_cm, actinometry_j_cm2,
        avg_cloud_cover_oktas, avg_wind_speed_m_s, avg_vapour_pressure_hpa,
        avg_relative_humidity_pct, avg_station_pressure_hpa,
        avg_sea_level_pressure_hpa, daytime_precipitation_mm,
        nighttime_precipitation_mm
    )
    SELECT
        date_dimension.date_key,
        station.station_key,
        station_version.station_version_key,
        weather.max_air_temperature_c,
        weather.min_air_temperature_c,
        weather.avg_air_temperature_c,
        weather.min_ground_temperature_c,
        weather.precipitation_total_mm,
        weather.precipitation_type,
        weather.snow_depth_cm,
        weather.snow_water_equivalent_mm_cm,
        weather.sunshine_duration_h,
        weather.rain_duration_h,
        weather.snowfall_duration_h,
        weather.sleet_duration_h,
        weather.hail_duration_h,
        weather.fog_duration_h,
        weather.mist_duration_h,
        weather.rime_duration_h,
        weather.glaze_duration_h,
        weather.low_drifting_snow_duration_h,
        weather.high_drifting_snow_duration_h,
        weather.haze_duration_h,
        weather.wind_ge_10_m_s_duration_h,
        weather.wind_gt_15_m_s_duration_h,
        weather.thunderstorm_duration_h,
        weather.dew_duration_h,
        weather.frost_duration_h,
        weather.snow_cover_occurred_source,
        weather.snow_cover_occurred,
        weather.snow_cover_occurrence_provenance,
        weather.lightning_occurred,
        weather.ground_condition,
        weather.lower_isotherm_cm,
        weather.upper_isotherm_cm,
        weather.actinometry_j_cm2,
        weather.avg_cloud_cover_oktas,
        weather.avg_wind_speed_m_s,
        weather.avg_vapour_pressure_hpa,
        weather.avg_relative_humidity_pct,
        weather.avg_station_pressure_hpa,
        weather.avg_sea_level_pressure_hpa,
        weather.daytime_precipitation_mm,
        weather.nighttime_precipitation_mm
    FROM layer_silver.weather_daily AS weather
    JOIN layer_gold.dim_date AS date_dimension
        ON date_dimension.full_date = weather.observation_date
    JOIN layer_gold.dim_station AS station
        ON station.station_code = weather.station_code
    JOIN layer_gold.dim_station_version AS station_version
        ON station_version.station_key = station.station_key
       AND weather.observation_date >= station_version.valid_from
       AND (
            station_version.valid_to IS NULL
            OR weather.observation_date <= station_version.valid_to
       );

    INSERT INTO layer_gold.fact_weather_station_year (
        station_key, year, expected_days, observation_days,
        avg_temperature_days, max_temperature_days, min_temperature_days,
        precipitation_observed_days, snow_cover_observed_days,
        avg_temperature_coverage, max_temperature_coverage,
        min_temperature_coverage, precipitation_coverage, snow_cover_coverage,
        is_complete_year,
        is_avg_temperature_reportable, is_max_temperature_reportable,
        is_min_temperature_reportable, is_precipitation_reportable,
        is_snow_cover_reportable,
        annual_avg_air_temperature_c, annual_max_air_temperature_c,
        annual_min_air_temperature_c, annual_precipitation_total_mm,
        hot_days_ge_30_c, very_hot_days_ge_35_c,
        cold_nights_le_minus_20_c, very_cold_nights_le_minus_25_c,
        snow_cover_days
    )
    WITH station_year AS (
        SELECT
            weather.station_code,
            extract(year FROM weather.observation_date)::smallint AS year,
            (
                make_date(extract(year FROM weather.observation_date)::integer + 1, 1, 1)
                - make_date(extract(year FROM weather.observation_date)::integer, 1, 1)
            )::smallint AS expected_days,
            count(*)::smallint AS observation_days,
            count(weather.avg_air_temperature_c)::smallint AS avg_temperature_days,
            count(weather.max_air_temperature_c)::smallint AS max_temperature_days,
            count(weather.min_air_temperature_c)::smallint AS min_temperature_days,
            count(weather.precipitation_total_mm)::smallint
                AS precipitation_observed_days,
            count(weather.snow_cover_occurred)::smallint AS snow_cover_observed_days,
            avg(weather.avg_air_temperature_c) AS raw_avg_air_temperature_c,
            max(weather.max_air_temperature_c) AS raw_max_air_temperature_c,
            min(weather.min_air_temperature_c) AS raw_min_air_temperature_c,
            sum(weather.precipitation_total_mm) AS raw_precipitation_total_mm,
            count(*) FILTER (
                WHERE weather.max_air_temperature_c >= 30
            )::smallint AS raw_hot_days_ge_30_c,
            count(*) FILTER (
                WHERE weather.max_air_temperature_c >= 35
            )::smallint AS raw_very_hot_days_ge_35_c,
            count(*) FILTER (
                WHERE weather.min_air_temperature_c <= -20
            )::smallint AS raw_cold_nights_le_minus_20_c,
            count(*) FILTER (
                WHERE weather.min_air_temperature_c <= -25
            )::smallint AS raw_very_cold_nights_le_minus_25_c,
            count(*) FILTER (
                WHERE weather.snow_cover_occurred
            )::smallint AS raw_snow_cover_days
        FROM layer_silver.weather_daily AS weather
        GROUP BY weather.station_code, extract(year FROM weather.observation_date)
    ),
    quality AS (
        SELECT
            station_year.*,
            station_year.avg_temperature_days::numeric
                / station_year.expected_days AS avg_temperature_coverage,
            station_year.max_temperature_days::numeric
                / station_year.expected_days AS max_temperature_coverage,
            station_year.min_temperature_days::numeric
                / station_year.expected_days AS min_temperature_coverage,
            station_year.precipitation_observed_days::numeric
                / station_year.expected_days AS precipitation_coverage,
            station_year.snow_cover_observed_days::numeric
                / station_year.expected_days AS snow_cover_coverage,
            make_date(station_year.year + 1, 1, 1) - 1 <= last_date AS is_complete_year
        FROM station_year
    )
    SELECT
        station.station_key,
        quality.year,
        quality.expected_days,
        quality.observation_days,
        quality.avg_temperature_days,
        quality.max_temperature_days,
        quality.min_temperature_days,
        quality.precipitation_observed_days,
        quality.snow_cover_observed_days,
        quality.avg_temperature_coverage,
        quality.max_temperature_coverage,
        quality.min_temperature_coverage,
        quality.precipitation_coverage,
        quality.snow_cover_coverage,
        quality.is_complete_year,
        quality.is_complete_year AND quality.avg_temperature_coverage >= 0.95,
        quality.is_complete_year AND quality.max_temperature_coverage >= 0.95,
        quality.is_complete_year AND quality.min_temperature_coverage >= 0.95,
        quality.is_complete_year AND quality.precipitation_coverage >= 0.95,
        quality.is_complete_year AND quality.snow_cover_coverage >= 0.95,
        CASE
            WHEN quality.is_complete_year AND quality.avg_temperature_coverage >= 0.95
            THEN quality.raw_avg_air_temperature_c
        END,
        CASE
            WHEN quality.is_complete_year AND quality.max_temperature_coverage >= 0.95
            THEN quality.raw_max_air_temperature_c
        END,
        CASE
            WHEN quality.is_complete_year AND quality.min_temperature_coverage >= 0.95
            THEN quality.raw_min_air_temperature_c
        END,
        CASE
            WHEN quality.is_complete_year AND quality.precipitation_coverage >= 0.95
            THEN quality.raw_precipitation_total_mm
        END,
        CASE
            WHEN quality.is_complete_year AND quality.max_temperature_coverage >= 0.95
            THEN quality.raw_hot_days_ge_30_c
        END,
        CASE
            WHEN quality.is_complete_year AND quality.max_temperature_coverage >= 0.95
            THEN quality.raw_very_hot_days_ge_35_c
        END,
        CASE
            WHEN quality.is_complete_year AND quality.min_temperature_coverage >= 0.95
            THEN quality.raw_cold_nights_le_minus_20_c
        END,
        CASE
            WHEN quality.is_complete_year AND quality.min_temperature_coverage >= 0.95
            THEN quality.raw_very_cold_nights_le_minus_25_c
        END,
        CASE
            WHEN quality.is_complete_year AND quality.snow_cover_coverage >= 0.95
            THEN quality.raw_snow_cover_days
        END
    FROM quality
    JOIN layer_gold.dim_station AS station
        ON station.station_code = quality.station_code;
END;
$$;

CREATE PROCEDURE layer_bronze.refresh_etl()
LANGUAGE plpgsql
AS $$
BEGIN
    CALL layer_silver.refresh();
    CALL layer_gold.refresh();
END;
$$;
