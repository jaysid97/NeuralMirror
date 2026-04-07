-- AlloyDB semantic search setup
-- Enables required extensions and creates a ScaNN index for cosine similarity.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS google_ml_integration;

CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(768) NOT NULL
);

DO $$
DECLARE
    scann_am TEXT;
BEGIN
    SELECT amname
    INTO scann_am
    FROM pg_am
    WHERE amname IN ('scann', 'alloydb_scann')
    ORDER BY CASE amname WHEN 'scann' THEN 1 ELSE 2 END
    LIMIT 1;

    IF scann_am IS NULL THEN
        RAISE EXCEPTION 'No ScaNN access method found. Ensure google_ml_integration is enabled and supported in this AlloyDB instance.';
    END IF;

    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS idx_documents_embedding_scann ON documents USING %I (embedding vector_cosine_ops)',
        scann_am
    );
END
$$;
