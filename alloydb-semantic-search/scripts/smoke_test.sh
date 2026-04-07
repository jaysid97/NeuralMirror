#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8080}"
INGEST_TEXT="${INGEST_TEXT:-AlloyDB and pgvector enable low-latency semantic search.}"
SEARCH_QUERY="${SEARCH_QUERY:-semantic search with vectors}"

echo "[1/2] POST ${BASE_URL}/ingest"
INGEST_RESPONSE=$(curl -sS -X POST "${BASE_URL}/ingest" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"${INGEST_TEXT}\"}")

echo "Ingest response: ${INGEST_RESPONSE}"

echo "[2/2] GET ${BASE_URL}/search?query=..."
SEARCH_RESPONSE=$(curl -sS -G "${BASE_URL}/search" --data-urlencode "query=${SEARCH_QUERY}")

echo "Search response: ${SEARCH_RESPONSE}"
