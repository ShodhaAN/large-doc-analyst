import logging
from typing import List
from sentence_transformers import SentenceTransformer
from backend.chunking.chunker import TextChunk
from backend.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Embedder:
    """
    Converts text into embeddings (lists of numbers).
    Uses the Sentence Transformers library.
    """

    def __init__(self):
        logger.info(f"Loading embedding model: {settings.embedding_model}")

        # Load the AI model that converts text to numbers
        # This downloads the model first time (about 90MB)
        self.model = SentenceTransformer(settings.embedding_model)

        # How many numbers per embedding
        self.dimension = self.model.get_embedding_dimension()

        logger.info(f"Model loaded! Embedding dimension: {self.dimension}")

    def embed_text(self, text: str) -> List[float]:
        """
        Convert a single piece of text into a list of numbers.

        Args:
            text: Any string of text

        Returns:
            A list of floating point numbers (the embedding)
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_chunks(self, chunks: List[TextChunk]) -> List[dict]:
        """
        Convert a list of text chunks into embeddings.

        Args:
            chunks: List of TextChunk objects

        Returns:
            List of dicts with chunk info + embedding
        """
        logger.info(f"Embedding {len(chunks)} chunks...")

        # Extract just the text from each chunk
        texts = [chunk.text for chunk in chunks]

        # Generate all embeddings at once (faster than one by one)
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=True
        )

        # Combine chunk info with its embedding
        results = []
        for chunk, embedding in zip(chunks, embeddings):
            results.append({
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "start_page": chunk.start_page,
                "end_page": chunk.end_page,
                "filename": chunk.filename,
                "embedding": embedding.tolist()
            })

        logger.info(f"Successfully embedded {len(results)} chunks!")
        return results


# Create one shared instance
# This way the model loads only once
embedder = Embedder()