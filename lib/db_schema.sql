-- Drop table

-- DROP TABLE monitoring.checks;

CREATE TABLE monitoring.checks (
	id smallserial NOT NULL,
	value_id int2 NOT NULL,
	"check" varchar NOT NULL,
	arguments varchar NULL,
	patience interval NOT NULL,
	fail_message text NULL,
	repeat interval NOT NULL,
	CONSTRAINT checks_pk PRIMARY KEY (id),
	CONSTRAINT checks_value_definition_fk FOREIGN KEY (value_id) REFERENCES monitoring.value_definition(id)
);

-- Permissions

ALTER TABLE monitoring.checks OWNER TO postgres;
GRANT ALL ON TABLE monitoring.checks TO postgres;

-- Drop table

-- DROP TABLE monitoring.checks_status;

CREATE TABLE monitoring.checks_status (
	check_id int2 NOT NULL,
	last_check timestamp NOT NULL,
	is_good bool NULL,
	status_since timestamp NOT NULL,
	message text NULL,
	last_mail timestamp NULL,
	CONSTRAINT checks_status_pk PRIMARY KEY (check_id)
);

-- Permissions

ALTER TABLE monitoring.checks_status OWNER TO postgres;
GRANT ALL ON TABLE monitoring.checks_status TO postgres;
GRANT INSERT, SELECT, UPDATE ON TABLE monitoring.checks_status TO monitoring;

-- Drop table

-- DROP TABLE monitoring.current_values;

CREATE TABLE monitoring.current_values (
	value_id int2 NOT NULL,
	"time" timestamp NOT NULL,
	value text NULL,
	extra text NULL,
	CONSTRAINT newtable_pk PRIMARY KEY (value_id),
	CONSTRAINT status_values_fk FOREIGN KEY (value_id) REFERENCES monitoring.value_definition(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Permissions

ALTER TABLE monitoring.current_values OWNER TO postgres;
GRANT ALL ON TABLE monitoring.current_values TO postgres;
GRANT INSERT, SELECT, UPDATE ON TABLE monitoring.current_values TO monitoring;

-- Drop table

-- DROP TABLE monitoring.history;

CREATE TABLE monitoring.history (
	id int4 DEFAULT nextval('monitoring.status_id_seq'::regclass) NOT NULL,
	value_id int2 NOT NULL,
	"time" timestamp NOT NULL,
	value text NULL,
	extra text NULL,
	"valid" bool DEFAULT true NOT NULL,
	CONSTRAINT status_pk PRIMARY KEY (id),
	CONSTRAINT status_values_fk FOREIGN KEY (value_id) REFERENCES monitoring.value_definition(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Permissions

ALTER TABLE monitoring.history OWNER TO postgres;
GRANT INSERT, SELECT ON TABLE monitoring.history TO monitoring;

-- Drop table

-- DROP TABLE monitoring.value_definition;

CREATE TABLE monitoring.value_definition (
	id int2 DEFAULT nextval('monitoring.values_id_seq'::regclass) NOT NULL,
	host varchar NOT NULL,
	"key" varchar NOT NULL,
	CONSTRAINT values_pk PRIMARY KEY (id),
	CONSTRAINT values_unique UNIQUE (host, key)
);

-- Permissions

ALTER TABLE monitoring.value_definition OWNER TO postgres;
GRANT ALL ON TABLE monitoring.value_definition TO postgres;
GRANT INSERT, SELECT ON TABLE monitoring.value_definition TO monitoring;

CREATE OR REPLACE VIEW monitoring.checks_overview
AS SELECT c.id,
    vd.host,
    vd.key,
    cv.value,
    cv.extra,
    cv."time" AS value_time,
    now() - cv."time"::timestamp with time zone AS value_age,
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
   FROM monitoring.value_definition vd
     LEFT JOIN monitoring.current_values cv ON cv.value_id = vd.id,
    monitoring.checks c
     LEFT JOIN monitoring.checks_status cs ON cs.check_id = c.id
  WHERE c.value_id = vd.id;

-- Permissions

ALTER TABLE monitoring.checks_overview OWNER TO postgres;
GRANT ALL ON TABLE monitoring.checks_overview TO postgres;
GRANT SELECT ON TABLE monitoring.checks_overview TO monitoring;

CREATE OR REPLACE VIEW monitoring.values_overview
AS SELECT v.id,
    v.host,
    v.key,
    s."time",
    now() - s."time"::timestamp with time zone AS age,
    s.value,
    s.extra,
    s.value IS NOT NULL AS is_valid
   FROM monitoring.value_definition v,
    monitoring.current_values s
  WHERE v.id = s.value_id
  ORDER BY v.host, v.key;

-- Permissions

ALTER TABLE monitoring.values_overview OWNER TO postgres;
GRANT ALL ON TABLE monitoring.values_overview TO postgres;
GRANT SELECT ON TABLE monitoring.values_overview TO monitoring;

-- DROP PROCEDURE monitoring.set_value(varchar, varchar, timestamp, text, text);

CREATE OR REPLACE PROCEDURE monitoring.set_value(IN host_in character varying, IN key_in character varying, IN time_in timestamp without time zone, IN value_in text, IN extra_in text)
 LANGUAGE plpgsql
AS $procedure$
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
$procedure$
;

-- Permissions

ALTER PROCEDURE monitoring.set_value(varchar, varchar, timestamp, text, text) OWNER TO postgres;
GRANT ALL ON PROCEDURE monitoring.set_value(varchar, varchar, timestamp, text, text) TO public;
GRANT ALL ON PROCEDURE monitoring.set_value(varchar, varchar, timestamp, text, text) TO postgres;
GRANT ALL ON PROCEDURE monitoring.set_value(varchar, varchar, timestamp, text, text) TO monitoring;