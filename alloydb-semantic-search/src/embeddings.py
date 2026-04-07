import vertexai
from vertexai.language_models import TextEmbeddingModel

from .config import settings


_model: TextEmbeddingModel | None = None


def _get_model() -> TextEmbeddingModel:
    global _model
    if _model is None:
        vertexai.init(project=settings.gcp_project_id, location=settings.gcp_region)
        _model = TextEmbeddingModel.from_pretrained(settings.embedding_model)
    return _model


def embed_text(text: str) -> list[float]:
    model = _get_model()
    # text-embedding-004 supports configurable output dimensionality.
    try:
        embedding = model.get_embeddings([text], output_dimensionality=settings.vector_dim)[0]
    except TypeError:
        embedding = model.get_embeddings([text])[0]
    return list(embedding.values)


def probe_embeddings() -> None:
    # A tiny request verifies auth, model access, and endpoint reachability at startup.
    vector = embed_text("startup probe")
    if len(vector) != settings.vector_dim:
        raise RuntimeError(
            f"Embedding dimension mismatch: expected {settings.vector_dim}, got {len(vector)}"
        )
