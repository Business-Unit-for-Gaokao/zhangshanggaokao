BEGIN;

CREATE SCHEMA IF NOT EXISTS crawler;

CREATE TABLE IF NOT EXISTS crawler.crawl_jobs (
    id BIGSERIAL PRIMARY KEY,
    crawler_name TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'full',
    scope_key TEXT NOT NULL DEFAULT '',
    year TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    last_error TEXT,
    meta_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_crawl_jobs_name_status
    ON crawler.crawl_jobs (crawler_name, status);

CREATE INDEX IF NOT EXISTS idx_crawl_jobs_year
    ON crawler.crawl_jobs (year);

CREATE TABLE IF NOT EXISTS crawler.crawl_progress (
    id BIGSERIAL PRIMARY KEY,
    crawler_name TEXT NOT NULL,
    scope_key TEXT NOT NULL,
    cursor_type TEXT NOT NULL,
    cursor_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (crawler_name, scope_key, cursor_type)
);

CREATE INDEX IF NOT EXISTS idx_crawl_progress_updated_at
    ON crawler.crawl_progress (updated_at);

CREATE TABLE IF NOT EXISTS crawler.raw_documents (
    id BIGSERIAL PRIMARY KEY,
    crawler_name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_key TEXT NOT NULL,
    year TEXT,
    payload JSONB NOT NULL,
    payload_hash TEXT,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (crawler_name, entity_type, entity_key, year)
);

CREATE INDEX IF NOT EXISTS idx_raw_documents_lookup
    ON crawler.raw_documents (crawler_name, entity_type, year);

CREATE INDEX IF NOT EXISTS idx_raw_documents_entity_key
    ON crawler.raw_documents (entity_key);

CREATE INDEX IF NOT EXISTS idx_raw_documents_payload_gin
    ON crawler.raw_documents
    USING GIN (payload);

COMMIT;
