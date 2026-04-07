-- Keep VECTOR dimension in sync with VECTOR_DIM from your .env file.
CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(768) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Cosine similarity index (tune lists based on corpus size).
CREATE INDEX IF NOT EXISTS idx_documents_embedding_ivfflat
ON documents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
