--
-- PostgreSQL database dump
--

-- Dumped from database version 17.6 (Debian 17.6-1.pgdg11+1)
-- Dumped by pg_dump version 17.5 (Debian 17.5-1.pgdg110+1)

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

		SELECT id FROM monitoring.monitoring.value_definition v WHERE host = host_in AND key = key_in INTO value_id_var;
		IF value_id_var IS NULL THEN
			INSERT INTO monitoring.monitoring.value_definition (host, key) VALUES(host_in, key_in) ON CONFLICT DO NOTHING RETURNING id INTO value_id_var;
		END IF;

		INSERT INTO monitoring.monitoring.history(value_id, time, value, extra, valid) VALUES (value_id_var, time_var, value_in, extra_in, is_valid);

		INSERT INTO monitoring.monitoring.current_values(value_id, time, value, extra) VALUES(value_id_var, time_var, value_in, extra_in)
			ON CONFLICT (value_id) DO UPDATE
				SET time = excluded.time, value = excluded.value, extra = excluded.extra;
	END;
$$;


ALTER PROCEDURE monitoring.set_value(IN host_in character varying, IN key_in character varying, IN time_in timestamp without time zone, IN value_in text, IN extra_in text) OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: checks; Type: TABLE; Schema: monitoring; Owner: postgres
--

CREATE TABLE monitoring.checks (
    id smallint NOT NULL,
    value_id smallint NOT NULL,
    "check" character varying NOT NULL,
    arguments character varying,
    patience interval NOT NULL,
    fail_message text,
    repeat interval NOT NULL
);


ALTER TABLE monitoring.checks OWNER TO postgres;

--
-- Name: checks_id_seq; Type: SEQUENCE; Schema: monitoring; Owner: postgres
--

CREATE SEQUENCE monitoring.checks_id_seq
    AS smallint
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE monitoring.checks_id_seq OWNER TO postgres;

--
-- Name: checks_id_seq; Type: SEQUENCE OWNED BY; Schema: monitoring; Owner: postgres
--

ALTER SEQUENCE monitoring.checks_id_seq OWNED BY monitoring.checks.id;


--
-- Name: checks_status; Type: TABLE; Schema: monitoring; Owner: postgres
--

CREATE TABLE monitoring.checks_status (
    check_id smallint NOT NULL,
    last_check timestamp without time zone NOT NULL,
    is_good boolean,
    status_since timestamp without time zone NOT NULL,
    message text,
    last_mail timestamp without time zone
);


ALTER TABLE monitoring.checks_status OWNER TO postgres;

--
-- Name: current_values; Type: TABLE; Schema: monitoring; Owner: postgres
--

CREATE TABLE monitoring.current_values (
    value_id smallint NOT NULL,
    "time" timestamp without time zone NOT NULL,
    value text,
    extra text
);


ALTER TABLE monitoring.current_values OWNER TO postgres;

--
-- Name: value_definition; Type: TABLE; Schema: monitoring; Owner: postgres
--

CREATE TABLE monitoring.value_definition (
    id smallint NOT NULL,
    host character varying NOT NULL,
    key character varying NOT NULL
);


ALTER TABLE monitoring.value_definition OWNER TO postgres;

--
-- Name: checks_overview; Type: VIEW; Schema: monitoring; Owner: postgres
--

CREATE VIEW monitoring.checks_overview AS
 SELECT c.id AS check_id,
    vd.id AS value_id,
    vd.host,
    vd.key,
    cv.value,
    cv.extra,
    cv."time" AS value_time,
    (now() - (cv."time")::timestamp with time zone) AS value_age,
    c."check",
    c.arguments,
    c.patience,
    c.fail_message,
    c.repeat,
    cs.is_good,
    cs.status_since,
    cs.message,
    cs.last_check,
    cs.last_mail
   FROM (monitoring.value_definition vd
     LEFT JOIN monitoring.current_values cv ON ((cv.value_id = vd.id))),
    (monitoring.checks c
     LEFT JOIN monitoring.checks_status cs ON ((cs.check_id = c.id)))
  WHERE (c.value_id = vd.id)
  ORDER BY vd.host, vd.key;


ALTER VIEW monitoring.checks_overview OWNER TO postgres;

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

ALTER SEQUENCE monitoring.values_id_seq OWNED BY monitoring.value_definition.id;


--
-- Name: values_overview; Type: VIEW; Schema: monitoring; Owner: postgres
--

CREATE VIEW monitoring.values_overview AS
 SELECT v.id,
    v.host,
    v.key,
    s."time",
    (now() - (s."time")::timestamp with time zone) AS age,
    s.value,
    s.extra,
    (s.value IS NOT NULL) AS is_valid
   FROM monitoring.value_definition v,
    monitoring.current_values s
  WHERE (v.id = s.value_id)
  ORDER BY v.host, v.key;


ALTER VIEW monitoring.values_overview OWNER TO postgres;

--
-- Name: checks id; Type: DEFAULT; Schema: monitoring; Owner: postgres
--

ALTER TABLE ONLY monitoring.checks ALTER COLUMN id SET DEFAULT nextval('monitoring.checks_id_seq'::regclass);


--
-- Name: history id; Type: DEFAULT; Schema: monitoring; Owner: postgres
--

ALTER TABLE ONLY monitoring.history ALTER COLUMN id SET DEFAULT nextval('monitoring.status_id_seq'::regclass);


--
-- Name: value_definition id; Type: DEFAULT; Schema: monitoring; Owner: postgres
--

ALTER TABLE ONLY monitoring.value_definition ALTER COLUMN id SET DEFAULT nextval('monitoring.values_id_seq'::regclass);


--
-- Name: checks checks_pk; Type: CONSTRAINT; Schema: monitoring; Owner: postgres
--

ALTER TABLE ONLY monitoring.checks
    ADD CONSTRAINT checks_pk PRIMARY KEY (id);


--
-- Name: checks_status checks_status_pk; Type: CONSTRAINT; Schema: monitoring; Owner: postgres
--

ALTER TABLE ONLY monitoring.checks_status
    ADD CONSTRAINT checks_status_pk PRIMARY KEY (check_id);


--
-- Name: current_values newtable_pk; Type: CONSTRAINT; Schema: monitoring; Owner: postgres
--

ALTER TABLE ONLY monitoring.current_values
    ADD CONSTRAINT newtable_pk PRIMARY KEY (value_id);


--
-- Name: history status_pk; Type: CONSTRAINT; Schema: monitoring; Owner: postgres
--

ALTER TABLE ONLY monitoring.history
    ADD CONSTRAINT status_pk PRIMARY KEY (id);


--
-- Name: value_definition values_pk; Type: CONSTRAINT; Schema: monitoring; Owner: postgres
--

ALTER TABLE ONLY monitoring.value_definition
    ADD CONSTRAINT values_pk PRIMARY KEY (id);


--
-- Name: value_definition values_unique; Type: CONSTRAINT; Schema: monitoring; Owner: postgres
--

ALTER TABLE ONLY monitoring.value_definition
    ADD CONSTRAINT values_unique UNIQUE (host, key);


--
-- Name: checks checks_value_definition_fk; Type: FK CONSTRAINT; Schema: monitoring; Owner: postgres
--

ALTER TABLE ONLY monitoring.checks
    ADD CONSTRAINT checks_value_definition_fk FOREIGN KEY (value_id) REFERENCES monitoring.value_definition(id);


--
-- Name: current_values status_values_fk; Type: FK CONSTRAINT; Schema: monitoring; Owner: postgres
--

ALTER TABLE ONLY monitoring.current_values
    ADD CONSTRAINT status_values_fk FOREIGN KEY (value_id) REFERENCES monitoring.value_definition(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: history status_values_fk; Type: FK CONSTRAINT; Schema: monitoring; Owner: postgres
--

ALTER TABLE ONLY monitoring.history
    ADD CONSTRAINT status_values_fk FOREIGN KEY (value_id) REFERENCES monitoring.value_definition(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: SCHEMA monitoring; Type: ACL; Schema: -; Owner: postgres
--

GRANT USAGE ON SCHEMA monitoring TO monitoring;


--
-- Name: PROCEDURE set_value(IN host_in character varying, IN key_in character varying, IN time_in timestamp without time zone, IN value_in text, IN extra_in text); Type: ACL; Schema: monitoring; Owner: postgres
--

GRANT ALL ON PROCEDURE monitoring.set_value(IN host_in character varying, IN key_in character varying, IN time_in timestamp without time zone, IN value_in text, IN extra_in text) TO monitoring;


--
-- Name: TABLE checks; Type: ACL; Schema: monitoring; Owner: postgres
--

GRANT SELECT ON TABLE monitoring.checks TO monitoring;


--
-- Name: TABLE checks_status; Type: ACL; Schema: monitoring; Owner: postgres
--

GRANT SELECT,INSERT,UPDATE ON TABLE monitoring.checks_status TO monitoring;


--
-- Name: TABLE current_values; Type: ACL; Schema: monitoring; Owner: postgres
--

GRANT SELECT,INSERT,UPDATE ON TABLE monitoring.current_values TO monitoring;


--
-- Name: TABLE value_definition; Type: ACL; Schema: monitoring; Owner: postgres
--

GRANT SELECT,INSERT ON TABLE monitoring.value_definition TO monitoring;


--
-- Name: TABLE checks_overview; Type: ACL; Schema: monitoring; Owner: postgres
--

GRANT SELECT ON TABLE monitoring.checks_overview TO monitoring;


--
-- Name: TABLE history; Type: ACL; Schema: monitoring; Owner: postgres
--

REVOKE ALL ON TABLE monitoring.history FROM postgres;
GRANT SELECT,INSERT ON TABLE monitoring.history TO monitoring;


--
-- Name: SEQUENCE status_id_seq; Type: ACL; Schema: monitoring; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE monitoring.status_id_seq TO monitoring;


--
-- Name: SEQUENCE values_id_seq; Type: ACL; Schema: monitoring; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE monitoring.values_id_seq TO monitoring;


--
-- Name: TABLE values_overview; Type: ACL; Schema: monitoring; Owner: postgres
--

GRANT SELECT ON TABLE monitoring.values_overview TO monitoring;


--
-- PostgreSQL database dump complete
--

