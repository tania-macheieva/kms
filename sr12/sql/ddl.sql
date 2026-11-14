-- Зіркова схема СР12: оцінювання RAG-відповідей (ЛР11 + СР11). СУБД: DuckDB 2.x
-- Зерно: один рядок = ОДНЕ тестове питання, виконане в ОДНОМУ прогоні (run).
CREATE SCHEMA IF NOT EXISTS dwh;

CREATE TABLE dwh.dim_date (               -- календар; роль у факті: дата прогону
  date_key     INTEGER PRIMARY KEY,       -- YYYYMMDD
  full_date    DATE NOT NULL UNIQUE,
  year_num     SMALLINT NOT NULL,
  quarter_num  TINYINT  NOT NULL CHECK (quarter_num BETWEEN 1 AND 4),
  month_num    TINYINT  NOT NULL CHECK (month_num BETWEEN 1 AND 12),
  month_name   VARCHAR  NOT NULL,
  iso_week     TINYINT  NOT NULL,         -- окрема гілка (тиждень не вкладається в місяць)
  day_of_month TINYINT  NOT NULL,
  is_weekend   BOOLEAN  NOT NULL
);

CREATE TABLE dwh.dim_run (                -- прогін = набір + конфігурація (незмінний, SCD 0)
  run_key         SMALLINT PRIMARY KEY,
  run_label       VARCHAR NOT NULL UNIQUE,   -- A, B, SR11
  suite           VARCHAR NOT NULL,          -- lab11 | sr11
  reranker_on     BOOLEAN NOT NULL,
  top_k           SMALLINT NOT NULL CHECK (top_k > 0),
  generator_model VARCHAR NOT NULL
);

CREATE TABLE dwh.dim_role (               -- SCD 1 (довідник)
  role_key  SMALLINT PRIMARY KEY,
  role_code VARCHAR NOT NULL UNIQUE
);

CREATE TABLE dwh.dim_outcome (            -- junk-вимір: пара (очікуваний, фактичний статус)
  outcome_key     SMALLINT PRIMARY KEY,
  expected_status VARCHAR NOT NULL CHECK (expected_status IN ('ANSWER','NO_ANSWER','CONFLICT')),
  actual_status   VARCHAR NOT NULL CHECK (actual_status   IN ('ANSWER','NO_ANSWER','CONFLICT')),
  is_match        BOOLEAN GENERATED ALWAYS AS (expected_status = actual_status) VIRTUAL,
  UNIQUE (expected_status, actual_status)
);

-- SCD 2 «append-only»: зберігаємо лише valid_from; valid_to та is_current обчислює view.
-- (Так немає прапорців, що можуть суперечити один одному: дві «поточні» версії, перекриття періодів.)
CREATE TABLE dwh.dim_test (
  test_key       INTEGER PRIMARY KEY,       -- сурогат ВЕРСІЇ
  suite          VARCHAR NOT NULL,
  test_id        VARCHAR NOT NULL,          -- природний ключ разом із suite
  category_group VARCHAR NOT NULL CHECK (category_group IN ('answerable','no_answer','conflict','unsafe')),
  category       VARCHAR NOT NULL,
  subtype        VARCHAR NOT NULL,
  language_code  VARCHAR NOT NULL CHECK (language_code IN ('en','uk')),
  valid_from     DATE NOT NULL,
  UNIQUE (suite, test_id, valid_from)
);
CREATE VIEW dwh.v_dim_test AS
SELECT t.*,
       COALESCE(LEAD(valid_from) OVER (PARTITION BY suite, test_id ORDER BY valid_from), DATE '9999-12-31') AS valid_to,
       LEAD(valid_from) OVER (PARTITION BY suite, test_id ORDER BY valid_from) IS NULL AS is_current
FROM dwh.dim_test t;

CREATE TABLE dwh.fact_rag_answer (
  run_key      SMALLINT NOT NULL REFERENCES dwh.dim_run(run_key),
  test_key     INTEGER  NOT NULL REFERENCES dwh.dim_test(test_key),
  date_key     INTEGER  NOT NULL REFERENCES dwh.dim_date(date_key),   -- дата прогону
  role_key     SMALLINT NOT NULL REFERENCES dwh.dim_role(role_key),   -- роль — атрибут запуску, не частина зерна
  outcome_key  SMALLINT NOT NULL REFERENCES dwh.dim_outcome(outcome_key),
  -- адитивні міри
  in_tokens        INTEGER NOT NULL CHECK (in_tokens  >= 0),
  out_tokens       INTEGER NOT NULL CHECK (out_tokens >= 0),
  retrieve_ms      DOUBLE  NOT NULL CHECK (retrieve_ms >= 0),
  graph_ms         DOUBLE  NOT NULL CHECK (graph_ms >= 0),
  n_cited          SMALLINT NOT NULL CHECK (n_cited >= 0),
  n_invalid        SMALLINT NOT NULL CHECK (n_invalid >= 0),
  uncited_sent     SMALLINT NOT NULL CHECK (uncited_sent >= 0),
  claims_total     SMALLINT NOT NULL CHECK (claims_total >= 0),
  claims_supported SMALLINT NOT NULL CHECK (claims_supported >= 0),
  gold_total       SMALLINT NOT NULL CHECK (gold_total >= 0),
  gold_hit         SMALLINT NOT NULL CHECK (gold_hit >= 0),
  PRIMARY KEY (run_key, test_key),                                  -- ЗЕРНО
  CHECK (n_invalid <= n_cited), CHECK (claims_supported <= claims_total), CHECK (gold_hit <= gold_total)
);
-- Частки (accuracy, faithfulness, context recall) НЕ зберігаються: рахуються як SUM/SUM.
