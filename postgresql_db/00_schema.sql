--
-- PostgreSQL database dump
--

\restrict FZPrCSd43e0UJY5wVp7m56saHmz2hdBcinNGBxCUzsqx2jmodeZAKWb1PFo7CHo

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: layer_bronze; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA layer_bronze;


ALTER SCHEMA layer_bronze OWNER TO postgres;

--
-- Name: layer_gold; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA layer_gold;


ALTER SCHEMA layer_gold OWNER TO postgres;

--
-- Name: layer_silver; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA layer_silver;


ALTER SCHEMA layer_silver OWNER TO postgres;

--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


--
-- Name: refresh_etl(); Type: PROCEDURE; Schema: layer_bronze; Owner: postgres
--

CREATE PROCEDURE layer_bronze.refresh_etl()
    LANGUAGE plpgsql
    AS $$
BEGIN

	CALL layer_silver.refresh();
	CALL layer_gold.refresh();
	
END;
$$;


ALTER PROCEDURE layer_bronze.refresh_etl() OWNER TO postgres;

--
-- Name: refresh(); Type: PROCEDURE; Schema: layer_gold; Owner: postgres
--

CREATE PROCEDURE layer_gold.refresh()
    LANGUAGE plpgsql
    AS $$
BEGIN

	-- CREATE GOLDEN SOURCE TABLE
	DROP TABLE IF EXISTS layer_gold.synop_data_gold;
	CREATE TABLE layer_gold.synop_data_gold
	AS 
	SELECT * FROM layer_gold.daily_synop_data;

END;
$$;


ALTER PROCEDURE layer_gold.refresh() OWNER TO postgres;

--
-- Name: refresh(); Type: PROCEDURE; Schema: layer_silver; Owner: postgres
--

CREATE PROCEDURE layer_silver.refresh()
    LANGUAGE plpgsql
    AS $$
BEGIN

	-- REFRESH TABLE WITH CITIES
    TRUNCATE TABLE layer_silver.geography_city;
    INSERT INTO layer_silver.geography_city
    SELECT *
    FROM layer_bronze.geography
    WHERE name_type = 'urzędowa'
      AND place_category = 'miejscowość'
      AND place_type = 'miasto';
	---------------------------------------------

	-- CREATE TABLE FOR SYNOP DATA ANALYSIS
	TRUNCATE TABLE layer_silver.synop_daily;
	INSERT INTO layer_silver.synop_daily
	SELECT
		nsp as station_code,
		TRIM(post) as station_name,
		rok as year,
		mc as month,
		dz as day,
		tmax as max_daily_t,
		tmin as min_daily_t,
		std as avg_daily_t,
		smdb as daily_precip,
		roop as precip_type,
		pksn as snow_deph_cm,
		desz as time_of_rain_h,
		sneg as time_if_snow_h,
		disn as time_of_sleet_h,
		dzps as snow_cover_occur
	FROM layer_bronze.synop_s_d_imgw;
	--

END;
$$;


ALTER PROCEDURE layer_silver.refresh() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: geography; Type: TABLE; Schema: layer_bronze; Owner: postgres
--

CREATE TABLE layer_bronze.geography (
    id text,
    name text,
    name_type text,
    place_category text,
    place_type text,
    voivodeship text,
    county text,
    municipality text,
    geographical_coordinates public.geography(Point,4326)
);


ALTER TABLE layer_bronze.geography OWNER TO postgres;

--
-- Name: synop_s_d_imgw; Type: TABLE; Schema: layer_bronze; Owner: postgres
--

CREATE TABLE layer_bronze.synop_s_d_imgw (
    nsp bigint,
    post text,
    rok bigint,
    mc bigint,
    dz bigint,
    tmax double precision,
    wtmax double precision,
    tmin double precision,
    wtmin double precision,
    std double precision,
    wstd double precision,
    tmng double precision,
    wtmng double precision,
    smdb double precision,
    wsmdb double precision,
    roop text,
    pksn double precision,
    wpksn double precision,
    rwsn double precision,
    wrwsn double precision,
    usl double precision,
    wusl double precision,
    desz double precision,
    wdesz double precision,
    sneg double precision,
    wsneg double precision,
    disn double precision,
    wdisn double precision,
    grad double precision,
    wgrad double precision,
    mgla double precision,
    wmgla double precision,
    zmgl double precision,
    wzmgl double precision,
    sadz double precision,
    wsadz double precision,
    golo double precision,
    wgolo double precision,
    zmni double precision,
    wzmni double precision,
    zmws double precision,
    wzmws double precision,
    zmet double precision,
    wzmet double precision,
    ff10 double precision,
    wff10 double precision,
    ff15 double precision,
    wff15 double precision,
    brza double precision,
    wbrza double precision,
    rosa double precision,
    wrosa double precision,
    szro double precision,
    wszro double precision,
    dzps double precision,
    wdzps double precision,
    dzbl double precision,
    wdzbl double precision,
    sgr text,
    izd double precision,
    wizd double precision,
    izg double precision,
    wizg double precision,
    aktn double precision,
    waktn double precision
);


ALTER TABLE layer_bronze.synop_s_d_imgw OWNER TO postgres;

--
-- Name: synop_s_d_t_imgw; Type: TABLE; Schema: layer_bronze; Owner: postgres
--

CREATE TABLE layer_bronze.synop_s_d_t_imgw (
    nsp bigint,
    post text,
    rok bigint,
    mc bigint,
    dz bigint,
    nos double precision,
    wnos double precision,
    fws double precision,
    wfws double precision,
    temp double precision,
    wtemp double precision,
    cpw double precision,
    wcpw double precision,
    wlgs double precision,
    wwlgs double precision,
    ppps double precision,
    wppps double precision,
    pppm double precision,
    wpppm double precision,
    wodz double precision,
    wwodz double precision,
    wono double precision,
    wwono double precision
);


ALTER TABLE layer_bronze.synop_s_d_t_imgw OWNER TO postgres;

--
-- Name: geography_city; Type: TABLE; Schema: layer_silver; Owner: postgres
--

CREATE TABLE layer_silver.geography_city (
    id text,
    name text,
    name_type text,
    place_category text,
    place_type text,
    voivodeship text,
    county text,
    municipality text,
    geographical_coordinates public.geography(Point,4326)
);


ALTER TABLE layer_silver.geography_city OWNER TO postgres;

--
-- Name: synop_daily; Type: TABLE; Schema: layer_silver; Owner: postgres
--

CREATE TABLE layer_silver.synop_daily (
    station_code bigint,
    station_name text,
    year bigint,
    month bigint,
    day bigint,
    max_daily_t double precision,
    min_daily_t double precision,
    avg_daily_t double precision,
    daily_precip double precision,
    precip_type text,
    snow_deph_cm double precision,
    time_of_rain_h double precision,
    time_if_snow_h double precision,
    time_of_sleet_h double precision,
    snow_cover_occur double precision
);


ALTER TABLE layer_silver.synop_daily OWNER TO postgres;

--
-- Name: synop_location_mapp; Type: TABLE; Schema: layer_silver; Owner: postgres
--

CREATE TABLE layer_silver.synop_location_mapp (
    station_name text,
    location text,
    location_name text,
    id text,
    station_code bigint
);


ALTER TABLE layer_silver.synop_location_mapp OWNER TO postgres;

--
-- Name: synop_station_mapp_1; Type: VIEW; Schema: layer_gold; Owner: postgres
--

CREATE VIEW layer_gold.synop_station_mapp_1 AS
 WITH synop_city AS (
         SELECT DISTINCT synop_location_mapp.station_name,
            synop_location_mapp.location_name AS city,
            synop_location_mapp.id AS city_id
           FROM layer_silver.synop_location_mapp
          WHERE (synop_location_mapp.location = 'miasto'::text)
        ), synop_daily AS (
         SELECT DISTINCT synop_daily.station_name
           FROM layer_silver.synop_daily
        ), city_mapp_1 AS (
         SELECT c.station_name,
            c.city,
            c.city_id
           FROM (synop_daily s
             LEFT JOIN synop_city c ON ((s.station_name = c.station_name)))
          WHERE (c.city_id IS NOT NULL)
        ), city_mapp_2 AS (
         SELECT c.station_name,
            c.city,
            c.city_id,
            g.voivodeship,
            g.county,
            g.municipality,
            g.geographical_coordinates
           FROM (city_mapp_1 c
             LEFT JOIN layer_silver.geography_city g ON ((c.city_id = g.id)))
        )
 SELECT station_name,
    city,
    city_id,
    voivodeship,
    county,
    municipality,
    geographical_coordinates
   FROM city_mapp_2;


ALTER VIEW layer_gold.synop_station_mapp_1 OWNER TO postgres;

--
-- Name: daily_synop_data; Type: VIEW; Schema: layer_gold; Owner: postgres
--

CREATE VIEW layer_gold.daily_synop_data AS
 WITH synop_daily AS (
         SELECT synop_daily.station_code,
            synop_daily.station_name,
            synop_daily.year,
            synop_daily.month,
            synop_daily.day,
            synop_daily.max_daily_t,
            synop_daily.min_daily_t,
            synop_daily.avg_daily_t,
            synop_daily.daily_precip,
            synop_daily.precip_type,
            synop_daily.snow_deph_cm,
            synop_daily.time_of_rain_h,
            synop_daily.time_if_snow_h,
            synop_daily.time_of_sleet_h,
            synop_daily.snow_cover_occur
           FROM layer_silver.synop_daily
        ), mapp AS (
         SELECT synop_station_mapp_1.station_name,
            synop_station_mapp_1.city,
            synop_station_mapp_1.city_id,
            synop_station_mapp_1.voivodeship,
            synop_station_mapp_1.county,
            synop_station_mapp_1.municipality,
            synop_station_mapp_1.geographical_coordinates
           FROM layer_gold.synop_station_mapp_1
        ), synop_mapped AS (
         SELECT main.station_code,
            main.station_name,
            main.year,
            main.month,
            main.day,
            main.max_daily_t,
            main.min_daily_t,
            main.avg_daily_t,
            main.daily_precip,
            main.precip_type,
            main.snow_deph_cm,
            main.time_of_rain_h,
            main.time_if_snow_h,
            main.time_of_sleet_h,
            main.snow_cover_occur,
            mapp.city,
            mapp.city_id,
            mapp.voivodeship,
            mapp.county,
            mapp.municipality,
            mapp.geographical_coordinates
           FROM (synop_daily main
             LEFT JOIN mapp ON ((main.station_name = mapp.station_name)))
        )
 SELECT station_code,
    station_name,
    year,
    month,
    day,
    max_daily_t,
    min_daily_t,
    avg_daily_t,
    daily_precip,
    precip_type,
    snow_deph_cm,
    time_of_rain_h,
    time_if_snow_h,
    time_of_sleet_h,
    snow_cover_occur,
    city,
    city_id,
    voivodeship,
    county,
    municipality,
    geographical_coordinates
   FROM synop_mapped;


ALTER VIEW layer_gold.daily_synop_data OWNER TO postgres;

--
-- Name: synop_data_gold; Type: TABLE; Schema: layer_gold; Owner: postgres
--

CREATE TABLE layer_gold.synop_data_gold (
    station_code bigint,
    station_name text,
    year bigint,
    month bigint,
    day bigint,
    max_daily_t double precision,
    min_daily_t double precision,
    avg_daily_t double precision,
    daily_precip double precision,
    precip_type text,
    snow_deph_cm double precision,
    time_of_rain_h double precision,
    time_if_snow_h double precision,
    time_of_sleet_h double precision,
    snow_cover_occur double precision,
    city text,
    city_id text,
    voivodeship text,
    county text,
    municipality text,
    geographical_coordinates public.geography(Point,4326)
);


ALTER TABLE layer_gold.synop_data_gold OWNER TO postgres;

--
-- PostgreSQL database dump complete
--

\unrestrict FZPrCSd43e0UJY5wVp7m56saHmz2hdBcinNGBxCUzsqx2jmodeZAKWb1PFo7CHo
