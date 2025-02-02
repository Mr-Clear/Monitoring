--
-- PostgreSQL database dump
--

-- Dumped from database version 17.2 (Debian 17.2-1.pgdg110+1)
-- Dumped by pg_dump version 17.2 (Debian 17.2-1.pgdg110+1)

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
-- Name: monitoring; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA monitoring;


ALTER SCHEMA monitoring OWNER TO postgres;

--
-- Name: set_value(character varying, character varying, timestamp without time zone, text, text); Type: PROCEDURE; Schema: monitoring; Owner: postgres
--

CREATE PROCEDURE monitoring.set_value(IN host_in character varying, IN key_in character varying, IN time_in timestamp without time zone, IN value_in text, IN extra_in text)
    LANGUAGE plpgsql
    AS $$
	DECLARE
		value_id_var SMALLINT;
		is_valid BOOLEAN := value_in IS NOT NULL;
		time_var TIMESTAMP;
	BEGIN
		IF time_in IS NULL THEN
			time_var = NOW();
		ELSE
			time_var = time_in;
		END IF;

		INSERT INTO monitoring.monitoring.values (host, key) VALUES(host_in, key_in) ON CONFLICT DO NOTHING;
		SELECT id FROM monitoring.monitoring."values" v WHERE host = host_in AND key = key_in INTO value_id_var;

		INSERT INTO monitoring.monitoring.history(value_id, time, value, extra, valid) VALUES (value_id_var, time_var, value_in, extra_in, is_valid);

		INSERT INTO monitoring.monitoring.status(value_id, time, value, extra) VALUES(value_id_var, time_var, value_in, extra_in)
			ON CONFLICT (value_id) DO UPDATE
				SET time = excluded.time, value = excluded.value, extra = excluded.extra;
	END;
$$;


ALTER PROCEDURE monitoring.set_value(IN host_in character varying, IN key_in character varying, IN time_in timestamp without time zone, IN value_in text, IN extra_in text) OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: history; Type: TABLE; Schema: monitoring; Owner: postgres
--

CREATE TABLE monitoring.history (
    id integer NOT NULL,
    value_id smallint NOT NULL,
    "time" timestamp without time zone NOT NULL,
    value text,
    extra text,
    valid boolean DEFAULT true NOT NULL
);


ALTER TABLE monitoring.history OWNER TO postgres;

--
-- Name: status; Type: TABLE; Schema: monitoring; Owner: postgres
--

CREATE TABLE monitoring.status (
    value_id smallint NOT NULL,
    "time" timestamp without time zone NOT NULL,
    value text,
    extra text
);


ALTER TABLE monitoring.status OWNER TO postgres;

--
-- Name: status_id_seq; Type: SEQUENCE; Schema: monitoring; Owner: postgres
--

CREATE SEQUENCE monitoring.status_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE monitoring.status_id_seq OWNER TO postgres;

--
-- Name: status_id_seq; Type: SEQUENCE OWNED BY; Schema: monitoring; Owner: postgres
--

ALTER SEQUENCE monitoring.status_id_seq OWNED BY monitoring.history.id;


--
-- Name: values; Type: TABLE; Schema: monitoring; Owner: postgres
--

CREATE TABLE monitoring."values" (
    id smallint NOT NULL,
    host character varying NOT NULL,
    key character varying NOT NULL
);


ALTER TABLE monitoring."values" OWNER TO postgres;

--
-- Name: values_id_seq; Type: SEQUENCE; Schema: monitoring; Owner: postgres
--

CREATE SEQUENCE monitoring.values_id_seq
    AS smallint
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE monitoring.values_id_seq OWNER TO postgres;

--
-- Name: values_id_seq; Type: SEQUENCE OWNED BY; Schema: monitoring; Owner: postgres
--

ALTER SEQUENCE monitoring.values_id_seq OWNED BY monitoring."values".id;


--
-- Name: history id; Type: DEFAULT; Schema: monitoring; Owner: postgres
--

ALTER TABLE ONLY monitoring.history ALTER COLUMN id SET DEFAULT nextval('monitoring.status_id_seq'::regclass);


--
-- Name: values id; Type: DEFAULT; Schema: monitoring; Owner: postgres
--

ALTER TABLE ONLY monitoring."values" ALTER COLUMN id SET DEFAULT nextval('monitoring.values_id_seq'::regclass);


--
-- Name: status newtable_pk; Type: CONSTRAINT; Schema: monitoring; Owner: postgres
--

ALTER TABLE ONLY monitoring.status
    ADD CONSTRAINT newtable_pk PRIMARY KEY (value_id);


--
-- Name: history status_pk; Type: CONSTRAINT; Schema: monitoring; Owner: postgres
--

ALTER TABLE ONLY monitoring.history
    ADD CONSTRAINT status_pk PRIMARY KEY (id);


--
-- Name: values values_pk; Type: CONSTRAINT; Schema: monitoring; Owner: postgres
--

ALTER TABLE ONLY monitoring."values"
    ADD CONSTRAINT values_pk PRIMARY KEY (id);


--
-- Name: values values_unique; Type: CONSTRAINT; Schema: monitoring; Owner: postgres
--

ALTER TABLE ONLY monitoring."values"
    ADD CONSTRAINT values_unique UNIQUE (host, key);


--
-- Name: status status_values_fk; Type: FK CONSTRAINT; Schema: monitoring; Owner: postgres
--

ALTER TABLE ONLY monitoring.status
    ADD CONSTRAINT status_values_fk FOREIGN KEY (value_id) REFERENCES monitoring."values"(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: history status_values_fk; Type: FK CONSTRAINT; Schema: monitoring; Owner: postgres
--

ALTER TABLE ONLY monitoring.history
    ADD CONSTRAINT status_values_fk FOREIGN KEY (value_id) REFERENCES monitoring."values"(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: SCHEMA monitoring; Type: ACL; Schema: -; Owner: postgres
--

GRANT USAGE ON SCHEMA monitoring TO monitoring;


--
-- Name: PROCEDURE set_value(IN host_in character varying, IN key_in character varying, IN time_in timestamp without time zone, IN value_in text, IN extra_in text); Type: ACL; Schema: monitoring; Owner: postgres
--

GRANT ALL ON PROCEDURE monitoring.set_value(IN host_in character varying, IN key_in character varying, IN time_in timestamp without time zone, IN value_in text, IN extra_in text) TO monitoring;


--
-- Name: TABLE history; Type: ACL; Schema: monitoring; Owner: postgres
--

REVOKE ALL ON TABLE monitoring.history FROM postgres;
GRANT SELECT,INSERT ON TABLE monitoring.history TO monitoring;


--
-- Name: TABLE status; Type: ACL; Schema: monitoring; Owner: postgres
--

GRANT SELECT,INSERT,UPDATE ON TABLE monitoring.status TO monitoring;


--
-- Name: SEQUENCE status_id_seq; Type: ACL; Schema: monitoring; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE monitoring.status_id_seq TO monitoring;


--
-- Name: TABLE "values"; Type: ACL; Schema: monitoring; Owner: postgres
--

GRANT SELECT,INSERT ON TABLE monitoring."values" TO monitoring;


--
-- Name: SEQUENCE values_id_seq; Type: ACL; Schema: monitoring; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE monitoring.values_id_seq TO monitoring;


--
-- PostgreSQL database dump complete
--

