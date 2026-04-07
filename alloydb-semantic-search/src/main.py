from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db, init_db, shutdown_db
from .embeddings import embed_text, probe_embeddings
from .models import (
    DocumentCreated,
    IngestRequest,
    SearchQuery,
)
from .repository import insert_document, semantic_search


def _run_startup_checks() -> None:
    try:
        db_gen = get_db()
        db = next(db_gen)
        try:
            table_name = db.execute(text("SELECT to_regclass('public.documents')")).scalar_one_or_none()
            if not table_name:
                print("WARNING: Required table public.documents does not exist. Run sql/schema.sql in AlloyDB Studio.")
        finally:
            db_gen.close()
    except Exception as e:
        print(f"WARNING: Could not verify database table: {e}")

    try:
        probe_embeddings()
    except Exception as e:
        print(f"WARNING: Could not probe Vertex AI embeddings: {e}")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    _run_startup_checks()
    yield
    shutdown_db()


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.post("/ingest", response_model=DocumentCreated)
def ingest(payload: IngestRequest, db: Session = Depends(get_db)):
    try:
        embedding = embed_text(payload.text)
        new_id = insert_document(db, payload.text, embedding)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {exc}") from exc
    return {"id": new_id}


@app.get("/search", response_model=list[SearchQuery])
def search_by_text(query: str, db: Session = Depends(get_db)):
    try:
        query_embedding = embed_text(query)
        results = semantic_search(db, query_embedding, 5)
        return [
            {"id": r["id"], "content": r["content"], "score": r["score"]}
            for r in results
        ]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search embedding failed: {exc}") from exc
