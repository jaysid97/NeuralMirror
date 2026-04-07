from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import settings


def _to_pgvector_literal(values: Sequence[float]) -> str:
    return "[" + ",".join(str(v) for v in values) + "]"


def _validate_dim(values: Sequence[float]) -> None:
    if len(values) != settings.vector_dim:
        raise ValueError(
            f"Embedding length {len(values)} does not match VECTOR_DIM={settings.vector_dim}"
        )


def insert_document(db: Session, content: str, embedding: Sequence[float]) -> int:
    _validate_dim(embedding)
    embedding_lit = _to_pgvector_literal(embedding)

    query = text(
        """
        INSERT INTO documents (content, embedding)
        VALUES (:content, CAST(:embedding AS vector))
        RETURNING id
        """
    )

    row = db.execute(
        query,
        {
            "content": content,
            "embedding": embedding_lit,
        },
    ).fetchone()

    if row is None:
        raise RuntimeError("Insert failed")

    db.commit()
    return int(row[0])


def semantic_search(db: Session, query_embedding: Sequence[float], k: int) -> list[dict]:
    _validate_dim(query_embedding)
    query_lit = _to_pgvector_literal(query_embedding)

    query = text(
        """
        SELECT
            id,
            content,
            1 - (embedding <=> CAST(:query_embedding AS vector)) AS score
        FROM documents
        ORDER BY embedding <=> CAST(:query_embedding AS vector)
        LIMIT :k
        """
    )

    rows = db.execute(query, {"query_embedding": query_lit, "k": k}).fetchall()

    return [
        {
            "id": int(r.id),
            "content": r.content,
            "score": float(r.score),
        }
        for r in rows
    ]
