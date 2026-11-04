from sentence_transformers import SentenceTransformer


class EmbeddingClient:
    """Generate text embeddings using a local Sentence Transformer model."""

    MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"     #вынести

    def __init__(self) -> None:
        self._model = SentenceTransformer(self.MODEL_NAME)

    def create_embedding(self, text: str) -> list[float]:
        """Convert text into a 384-dimensional embedding vector."""
        embedding = self._model.encode(text)

        return embedding.tolist()


embedding_client = EmbeddingClient()
