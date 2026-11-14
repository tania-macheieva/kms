## (а) Зерно факту

Один рядок фактів це результат оцінювання одного тестового запиту в одному прогоні для однієї ролі користувача, зі знімком версії тесту на момент прогону.

## (б) Таблиці

**Факт:** `fact_evaluation_result`
- Ключі: `run_key`, `run_date_key`, `config_key`, `test_case_key`, `role_key`, `expected_status_key`, `actual_status_key`
- Міри: `is_status_match`, `input_tokens`, `output_tokens`, `retrieval_time_ms`, `gold_evidence_total`, `gold_evidence_in_context`, `context_recall`, `citation_count`, `invalid_citation_count`, `uncited_sentence_count`, `claim_count`, `supported_claim_count`

**Виміри:**

| Таблиця | Ключ | Ключові атрибути |
|---|---|---|
| `dim_run` | `run_key` (NK `run_name`) | `run_name` (A, B, SR11). Повторний прогін з тією самою назвою отримує нову назву, напр. A2. |
| `dim_config` | `config_key` (NK = комбінація атрибутів) | `reranker_enabled`, `top_k`, `graph_enabled`, `prompt_version`, `generator_model` |
| `dim_date` | `date_key` (YYYYMMDD) | дата, рік, квартал, місяць, ISO-тиждень. Роль: дата прогону. |
| `dim_test_case` | `test_case_key` (суррогатний, NK `test_case_id`) | `category`, `subtype`, `language_code` (en/uk), `valid_from`, `valid_to`, `is_current` |
| `dim_role` | `role_key` | `role_code` (reader, analyst, clinician) |
| `dim_status` | `status_key` | `status_code` (ANSWER, NO_ANSWER, CONFLICT, BLOCKED, MALFORMED), `status_group`. Роль: очікуваний і фактичний статус. |

Очікуваний статус зберігається у факті як знімок на момент прогону, а не в `dim_test_case`. Так історія прогонів не змінюється, якщо тест згодом виправили.

## (в) Адитивність мір

| Міра | Тип | Як агрегувати |
|---|---|---|
| `is_status_match` (0/1) | адитивна | SUM дає кількість збігів; частка = SUM / COUNT |
| `input_tokens`, `output_tokens` | адитивна | SUM; середнє = SUM / COUNT |
| `retrieval_time_ms` | адитивна | SUM; середнє = SUM / COUNT |
| `gold_evidence_total`, `gold_evidence_in_context` | адитивна | SUM |
| `context_recall` | неадитивна | SUM(in_context) / SUM(total) лише по рядках з total NOT NULL, а не AVG |
| `citation_count`, `invalid_citation_count`, `uncited_sentence_count` | адитивна | SUM |
| `claim_count`, `supported_claim_count` | адитивна | SUM |
| Вірність (похідна, не зберігається) | неадитивна | SUM(supported) / SUM(claim) |

Напівадитивних мір немає, бо немає балансів чи знімків стану.

## (г) Ієрархії

- **Тест:** category → subtype → test_case_id. Мова (`language_code`) є окремим атрибутом, а не рівнем ієрархії.
- **Статус:** status_group (ОБРОБЛЕНО: ANSWER, NO_ANSWER, CONFLICT; ВІДХИЛЕНО: BLOCKED, MALFORMED) → status_code.
- **Конфігурація:** generator_model → prompt_version → (top_k, reranker_enabled, graph_enabled).
- **Час:** рік → квартал → місяць → дата.
- **Прогін і роль:** плоскі.

## (д) Тип SCD

| Таблиця | Тип | Обґрунтування |
|---|---|---|
| `dim_run` | Type 0 | Прогін незмінний після завершення. |
| `dim_config` | Type 0 | Нова конфігурація це новий рядок, старі не змінюються. |
| `dim_date` | Type 0 | Календар незмінний. |
| `dim_test_case` | Type 2 | Категорію, підтип або мову тесту можуть виправити, і історія має бути точною на дату прогону. |
| `dim_role` | Type 1 | Довідник з рідкими змінами. |
| `dim_status` | Type 0 | Фіксовані коди. |

## (е) DDL для DuckDB

```sql
CREATE SCHEMA IF NOT EXISTS dwh;

-- ===== Виміри =====
CREATE TABLE dwh.dim_date (
    date_key      INTEGER PRIMARY KEY,               -- YYYYMMDD
    full_date     DATE NOT NULL UNIQUE,
    year_num      SMALLINT NOT NULL,
    quarter_num   TINYINT NOT NULL CHECK (quarter_num BETWEEN 1 AND 4),
    month_num     TINYINT NOT NULL CHECK (month_num BETWEEN 1 AND 12),
    month_name    VARCHAR(20) NOT NULL,
    iso_week      TINYINT NOT NULL,
    day_of_month  TINYINT NOT NULL,
    is_weekend    BOOLEAN NOT NULL
);

CREATE TABLE dwh.dim_run (
    run_key       INTEGER PRIMARY KEY,
    run_name      VARCHAR(30) NOT NULL UNIQUE          -- A, B, SR11, ...
);

CREATE TABLE dwh.dim_config (
    config_key       INTEGER PRIMARY KEY,
    reranker_enabled BOOLEAN NOT NULL,
    top_k            SMALLINT NOT NULL CHECK (top_k > 0),
    graph_enabled    BOOLEAN NOT NULL,
    prompt_version   VARCHAR(50) NOT NULL,
    generator_model  VARCHAR(100) NOT NULL,
    UNIQUE (reranker_enabled, top_k, graph_enabled, prompt_version, generator_model)
);

-- SCD Type 2
CREATE TABLE dwh.dim_test_case (
    test_case_key  INTEGER PRIMARY KEY,               -- суррогатний ключ версії
    test_case_id   VARCHAR(50) NOT NULL,              -- природний ключ
    category       VARCHAR(40) NOT NULL,              -- answerable, no_answer, conflict, injection, ...
    subtype        VARCHAR(60),
    language_code  VARCHAR(5) NOT NULL CHECK (language_code IN ('en', 'uk')),
    valid_from     DATE NOT NULL,
    valid_to       DATE NOT NULL DEFAULT DATE '9999-12-31',
    is_current     BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (test_case_id, valid_from)
);

CREATE TABLE dwh.dim_role (
    role_key   SMALLINT PRIMARY KEY,
    role_code  VARCHAR(20) NOT NULL UNIQUE
               CHECK (role_code IN ('reader', 'analyst', 'clinician'))
);

CREATE TABLE dwh.dim_status (
    status_key    SMALLINT PRIMARY KEY,
    status_code   VARCHAR(20) NOT NULL UNIQUE
                  CHECK (status_code IN ('ANSWER', 'NO_ANSWER', 'CONFLICT', 'BLOCKED', 'MALFORMED')),
    status_group  VARCHAR(20) NOT NULL
                  CHECK (status_group IN ('PROCESSED', 'REJECTED'))
);

-- ===== Факт =====
CREATE SEQUENCE dwh.seq_fact_eval START 1;

CREATE TABLE dwh.fact_evaluation_result (
    evaluation_result_key   BIGINT PRIMARY KEY DEFAULT nextval('dwh.seq_fact_eval'),

    -- зовнішні ключі
    run_key                 INTEGER  NOT NULL REFERENCES dwh.dim_run(run_key),
    run_date_key            INTEGER  NOT NULL REFERENCES dwh.dim_date(date_key),
    config_key              INTEGER  NOT NULL REFERENCES dwh.dim_config(config_key),
    test_case_key           INTEGER  NOT NULL REFERENCES dwh.dim_test_case(test_case_key),
    role_key                SMALLINT NOT NULL REFERENCES dwh.dim_role(role_key),
    expected_status_key     SMALLINT NOT NULL REFERENCES dwh.dim_status(status_key),
    actual_status_key       SMALLINT NOT NULL REFERENCES dwh.dim_status(status_key),

    -- статус (адитивна ознака 0/1; рівна 1, коли expected_status_key = actual_status_key)
    is_status_match         TINYINT  NOT NULL CHECK (is_status_match IN (0, 1)),

    -- ресурси та час (адитивні)
    input_tokens            INTEGER  NOT NULL CHECK (input_tokens >= 0),
    output_tokens           INTEGER  NOT NULL CHECK (output_tokens >= 0),
    retrieval_time_ms       DOUBLE   NOT NULL CHECK (retrieval_time_ms >= 0),

    -- повнота контексту: адитивні компоненти + неадитивна частка (NULL, якщо немає золотих доказів)
    gold_evidence_total     SMALLINT CHECK (gold_evidence_total >= 0),
    gold_evidence_in_context SMALLINT CHECK (gold_evidence_in_context >= 0),
    context_recall          DOUBLE   CHECK (context_recall BETWEEN 0 AND 1),
    CHECK (gold_evidence_in_context <= gold_evidence_total),

    -- цитати і вірність (адитивні)
    citation_count          SMALLINT NOT NULL CHECK (citation_count >= 0),
    invalid_citation_count  SMALLINT NOT NULL CHECK (invalid_citation_count >= 0),
    uncited_sentence_count  SMALLINT NOT NULL CHECK (uncited_sentence_count >= 0),
    claim_count             SMALLINT NOT NULL CHECK (claim_count >= 0),
    supported_claim_count   SMALLINT NOT NULL CHECK (supported_claim_count >= 0),
    CHECK (invalid_citation_count <= citation_count),
    CHECK (supported_claim_count <= claim_count),

    -- зерно: один запит, один прогін, одна роль
    UNIQUE (run_key, test_case_key, role_key)
);
```

## Примітки

- Узгодженість `is_status_match` з парою статусів DDL не перевіряє, бо для цього потрібен крос-табличний чек. Це треба забезпечити при завантаженні ETL.
- Факт append-only, тому FK не заважають.
- У DuckDB оновлення рядка, на який посилається FK, може відхилятися. Закриття попередньої версії в `dim_test_case` (`is_current = FALSE`, `valid_to`) тому краще робити через вставку нової версії плюс перебудову таблиці або без FK на `dim_test_case`.
- Відповіді на бізнес-питання: питання 1 це SUM(is_status_match)/COUNT по `category` і `run`. Питання 2 це SUM(retrieval_time_ms)/COUNT і SUM(input_tokens)/COUNT по `role` і `reranker_enabled`. Питання 3 це SUM(in_context)/SUM(total) по `category` і `language_code`. Питання 4 це вірність і SUM(invalid_citation_count) по `run`. Питання 5 це COUNT рядків з `is_status_match = 0` по парі `expected_status` × `actual_status` і `role`.