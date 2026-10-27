--
-- PostgreSQL database dump
--

\restrict Kig7npPXE9hd9YoTZG3gG4NU6OeaUzG5POJ2vHLIG8cvsPtGShMPtgN0rMEI4DB

-- Dumped from database version 16.14
-- Dumped by pg_dump version 16.14

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: yellow_taxi_trips; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.yellow_taxi_trips (
    "VendorID" integer,
    tpep_pickup_datetime timestamp without time zone,
    tpep_dropoff_datetime timestamp without time zone,
    passenger_count double precision,
    trip_distance double precision,
    "RatecodeID" double precision,
    store_and_fwd_flag text,
    "PULocationID" integer,
    "DOLocationID" integer,
    payment_type bigint,
    fare_amount double precision,
    extra double precision,
    mta_tax double precision,
    tip_amount double precision,
    tolls_amount double precision,
    improvement_surcharge double precision,
    total_amount double precision,
    congestion_surcharge double precision,
    "Airport_fee" double precision,
    cbd_congestion_fee double precision,
    trip_duration_minutes double precision,
    pickup_hour integer,
    trip_id bigint NOT NULL
);


--
-- Name: yellow_taxi_trips_trip_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.yellow_taxi_trips ALTER COLUMN trip_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.yellow_taxi_trips_trip_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: yellow_taxi_trips yellow_taxi_trips_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.yellow_taxi_trips
    ADD CONSTRAINT yellow_taxi_trips_pkey PRIMARY KEY (trip_id);


--
-- PostgreSQL database dump complete
--

\unrestrict Kig7npPXE9hd9YoTZG3gG4NU6OeaUzG5POJ2vHLIG8cvsPtGShMPtgN0rMEI4DB

