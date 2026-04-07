# AlloyDB AI Semantic Search

A production-oriented FastAPI service for semantic search on Google Cloud. The application generates embeddings with Vertex AI (`text-embedding-004`), stores vectors in AlloyDB (`pgvector`), and serves low-latency search endpoints from Cloud Run.

## Features

- FastAPI API with two core endpoints:
  - `POST /ingest` to embed and store text in AlloyDB
  - `GET /search` to embed a query and return top 5 cosine-similar matches
- AlloyDB connection via `google-cloud-alloydb-connector` and `pg8000`
- Vector search using `pgvector` cosine distance operator (`<=>`)
- Startup health checks that validate:
  - `documents` table availability
  - Vertex AI embedding model connectivity/auth
- Containerized runtime with Python 3.11 and Uvicorn on port `8080`

## Architecture (Cloud Run + AlloyDB + Vertex AI)

1. Client sends text to FastAPI on Cloud Run.
2. App calls Vertex AI model `text-embedding-004` to generate a 768-dim embedding.
3. App inserts content + embedding into AlloyDB (`documents` table).
4. For search, app embeds query text and runs cosine similarity in AlloyDB using `<=>`.
5. Top 5 matches are returned as JSON.

### High-level components

- **Cloud Run**: stateless API container host
- **Vertex AI**: managed text embedding generation
- **AlloyDB + pgvector**: vector storage and ANN/exact similarity search

## Setup Instructions

### 1) Prerequisites

- Python 3.11+
- Google Cloud SDK (`gcloud`)
- Access to:
  - A GCP project
  - Vertex AI API
  - AlloyDB cluster/instance with network access from Cloud Run

### 2) Clone and install dependencies

```bash
cd alloydb-semantic-search
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3) Configure environment variables

Create `.env` from `.env.template` and fill all values:

```bash
cp .env.template .env
```

Required values include:

- `GCP_PROJECT_ID`
- `GCP_REGION`
- `EMBEDDING_MODEL` (default: `text-embedding-004`)
- `VECTOR_DIM` (default: `768`)
- `ALLOYDB_INSTANCE_URI`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`

### 4) Database initialization (required)

AlloyDB cannot store vectors until pgvector is enabled and the `documents` table exists.

Use AlloyDB Studio:

1. Open Google Cloud Console, then go to AlloyDB.
2. Open AlloyDB Studio.
3. Select your target database.
4. Open and paste the content of `sql/schema.sql`.
5. Run the script.

This step enables vector support and creates the `documents` table.

Optional: if you want ScaNN indexing for faster similarity search at scale, run `sql/003_alloydb_documents_scann.sql` after `sql/schema.sql`.

### 5) Run locally

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8080
```

Smoke test:

```bash
bash scripts/smoke_test.sh
```

## Deploy Guide (gcloud run deploy)

### 1) Set deployment variables

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export SERVICE_NAME="alloydb-ai-semantic-search"
export IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"
```

### 2) Build and push container image

```bash
gcloud builds submit --tag "${IMAGE}" .
```

### 3) Deploy to Cloud Run

```bash
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars APP_ENV=prod,GCP_PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION},EMBEDDING_MODEL=text-embedding-004,VECTOR_DIM=768,USE_ALLOYDB_CONNECTOR=true,ALLOYDB_INSTANCE_URI=projects/${PROJECT_ID}/locations/${REGION}/clusters/YOUR_CLUSTER/instances/YOUR_INSTANCE,DB_USER=YOUR_DB_USER,DB_PASSWORD=YOUR_DB_PASSWORD,DB_NAME=YOUR_DB_NAME
```

### 4) Verify deployment

```bash
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --format='value(status.url)')
curl -X POST "${SERVICE_URL}/ingest" -H "Content-Type: application/json" -d '{"text":"AlloyDB and Vertex AI power semantic search."}'
curl -G "${SERVICE_URL}/search" --data-urlencode "query=semantic search with vectors"
```

## API Summary

- `POST /ingest`
  - Request body:
    ```json
    { "text": "Your document text" }
    ```
  - Response body:
    ```json
    { "id": 123 }
    ```

- `GET /search?query=your+text`
  - Response body:
    ```json
    [
      { "id": 123, "content": "...", "score": 0.92 }
    ]
    ```

## Notes for Production

- Use Secret Manager instead of plain `DB_PASSWORD` environment variables.
- Restrict unauthenticated access unless a public API is explicitly required.
- Tune vector index/search settings to match corpus size and latency targets.
- Set Cloud Run min instances and CPU/memory based on embedding throughput requirements.
