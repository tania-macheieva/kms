-- Star schema for the variant-calling process (DuckDB). Run: python3 etl/load.py  (executes this file)
-- Grain of fact_variant_call: ONE called variant (call_id) of one sample, in one gene, by one pipeline version, on one date.
-- Grain of fact_pipeline_day: ONE pipeline version in effect on ONE calendar day (periodic snapshot).

CREATE TABLE dim_date (
    date_key     INTEGER PRIMARY KEY,          -- yyyymmdd
    full_date    DATE NOT NULL UNIQUE,
    year         SMALLINT NOT NULL, quarter SMALLINT NOT NULL, month SMALLINT NOT NULL, month_name VARCHAR NOT NULL,
    iso_week     SMALLINT NOT NULL, day_of_week SMALLINT NOT NULL, is_weekend BOOLEAN NOT NULL
);

-- Taxonomy as a dimension: every concept of the Lab-5 SKOS taxonomy; IRI is the conformed business key.
-- Role-playing: fact_variant_call references it three times (variant type, origin, clinical significance); dim_pipeline twice.
CREATE TABLE dim_taxon (
    taxon_key    INTEGER PRIMARY KEY,
    iri          VARCHAR NOT NULL UNIQUE,      -- http://example.org/knowledge-hub/biomed/C023
    notation     VARCHAR NOT NULL UNIQUE,      -- C023
    label        VARCHAR NOT NULL, label_uk VARCHAR,
    level        SMALLINT NOT NULL,            -- 0 = root
    parent_key   INTEGER REFERENCES dim_taxon(taxon_key),
    top_label    VARCHAR,                      -- ancestor at level 1 (e.g. 'Genetic variation')
    facet_label  VARCHAR,                      -- ancestor at level 2 (e.g. 'genetic variant', 'Variant by origin')
    path         VARCHAR NOT NULL,             -- root > ... > label
    is_leaf      BOOLEAN NOT NULL
);

CREATE TABLE dim_sample (                      -- SCD type 1 (corrections overwrite)
    sample_key   INTEGER PRIMARY KEY, sample_code VARCHAR NOT NULL UNIQUE,
    cohort       VARCHAR NOT NULL, tissue VARCHAR NOT NULL, platform VARCHAR NOT NULL, batch VARCHAR NOT NULL, qc_status VARCHAR NOT NULL
);

CREATE TABLE dim_gene (                        -- SCD type 1; hierarchy gene -> chromosome
    gene_key     INTEGER PRIMARY KEY, gene_symbol VARCHAR NOT NULL UNIQUE, chromosome VARCHAR NOT NULL
);

CREATE TABLE dim_pipeline (                    -- SCD type 2: new row on every tool-version change
    pipeline_key INTEGER PRIMARY KEY,
    family       VARCHAR NOT NULL, tool VARCHAR NOT NULL, version VARCHAR NOT NULL,
    valid_from   DATE NOT NULL, valid_to DATE NOT NULL, is_current BOOLEAN NOT NULL,
    caller_taxon_key INTEGER NOT NULL REFERENCES dim_taxon(taxon_key),        -- 'variant calling' (C060)
    filter_taxon_key INTEGER NOT NULL REFERENCES dim_taxon(taxon_key),        -- 'hard filtering' / 'variant quality score recalibration'
    CHECK (valid_from <= valid_to)
);

CREATE TABLE fact_variant_call (
    call_id          INTEGER PRIMARY KEY,                                       -- degenerate dimension
    date_key         INTEGER NOT NULL REFERENCES dim_date(date_key),
    sample_key       INTEGER NOT NULL REFERENCES dim_sample(sample_key),
    gene_key         INTEGER NOT NULL REFERENCES dim_gene(gene_key),
    pipeline_key     INTEGER NOT NULL REFERENCES dim_pipeline(pipeline_key),
    variant_type_key INTEGER NOT NULL REFERENCES dim_taxon(taxon_key),
    origin_key       INTEGER NOT NULL REFERENCES dim_taxon(taxon_key),
    significance_key INTEGER NOT NULL REFERENCES dim_taxon(taxon_key),
    call_count       INTEGER NOT NULL DEFAULT 1 CHECK (call_count = 1),         -- additive
    is_pass          INTEGER NOT NULL CHECK (is_pass IN (0, 1)),                -- additive (count of passed calls)
    review_minutes   DOUBLE  NOT NULL CHECK (review_minutes >= 0),             -- additive
    read_depth       INTEGER NOT NULL CHECK (read_depth BETWEEN 1 AND 1000),    -- non-additive (average)
    qual             DOUBLE  NOT NULL CHECK (qual BETWEEN 0 AND 255),           -- non-additive (average / percentile)
    alt_fraction     DOUBLE  NOT NULL CHECK (alt_fraction BETWEEN 0 AND 1)      -- non-additive (average)
);

CREATE TABLE fact_pipeline_day (
    date_key      INTEGER NOT NULL REFERENCES dim_date(date_key),
    pipeline_key  INTEGER NOT NULL REFERENCES dim_pipeline(pipeline_key),
    runs_started  INTEGER NOT NULL CHECK (runs_started >= 0),                   -- additive
    cpu_hours     DOUBLE  NOT NULL CHECK (cpu_hours >= 0),                      -- additive
    queue_backlog DOUBLE  NOT NULL CHECK (queue_backlog >= 0),                  -- semi-additive: sum over pipelines, NOT over time (use last/avg)
    PRIMARY KEY (date_key, pipeline_key)
);

