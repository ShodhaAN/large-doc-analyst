import os
import json
import logging
import numpy as np
import faiss
from pathlib import Path
from typing import List, Dict, Optional
from backend.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FAISSStore:
    """
    Stores embeddings in a FAISS index and searches them.
    Think of this as a smart filing cabinet for your embeddings.
    """

    def __init__(self, index_name: str = "default"):
        """
        Create or load a FAISS index.

        Args:
            index_name: Name for this index (one per document collection)
        """
        self.index_name = index_name
        self.index_path = settings.index_dir / f"{index_name}.index"
        self.metadata_path = settings.index_dir / f"{index_name}.json"

        # This stores the actual embeddings
        self.index = None

        # This stores the text and page info for each embedding
        # FAISS only stores numbers — we need this to get text back
        self.metadata: List[Dict] = []

        # The size of each embedding vector (384 for our model)
        self.dimension = 384

        # Load existing index if it exists
        if self.index_path.exists():
            self.load()
        else:
            self._create_new_index()

    def _create_new_index(self):
        """Create a brand new empty FAISS index"""
        logger.info(f"Creating new FAISS index: {self.index_name}")

        # IndexFlatL2 = search by L2 distance (similarity)
        # Think of it like measuring distance between two points
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []

        logger.info(f"New index created with dimension {self.dimension}")

    def add_embeddings(self, embedded_chunks: List[Dict]):
        """
        Add embedded chunks to the FAISS index.

        Args:
            embedded_chunks: List of dicts with 'embedding' and chunk info
        """
        if not embedded_chunks:
            logger.warning("No embeddings to add!")
            return

        logger.info(f"Adding {len(embedded_chunks)} embeddings to index...")

        # Extract just the numbers (embeddings)
        embeddings = np.array(
            [chunk["embedding"] for chunk in embedded_chunks],
            dtype=np.float32
        )

        # Store the starting position before adding
        start_id = len(self.metadata)

        # Add embeddings to FAISS
        self.index.add(embeddings)

        # Store metadata (text + page info) separately
        for chunk in embedded_chunks:
            self.metadata.append({
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "start_page": chunk["start_page"],
                "end_page": chunk["end_page"],
                "filename": chunk["filename"]
            })

        logger.info(f"Index now has {self.index.ntotal} embeddings total")

        # Save to disk automatically
        self.save()

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find the most similar chunks to a query.

        Args:
            query_embedding: The embedding of the user's question
            top_k: How many results to return

        Returns:
            List of the most relevant chunks with their metadata
        """
        if self.index.ntotal == 0:
            logger.warning("Index is empty! Upload documents first.")
            return []

        # Convert query to numpy array
        query = np.array([query_embedding], dtype=np.float32)

        # Search FAISS for closest matches
        # distances = how similar (lower = more similar)
        # indices = which chunks matched
        distances, indices = self.index.search(query, top_k)

        results = []
        for distance, idx in zip(distances[0], indices[0]):
            # idx = -1 means no result found
            if idx == -1:
                continue

            # Get the metadata for this chunk
            chunk_metadata = self.metadata[idx]

            results.append({
                "chunk_id": chunk_metadata["chunk_id"],
                "text": chunk_metadata["text"],
                "start_page": chunk_metadata["start_page"],
                "end_page": chunk_metadata["end_page"],
                "filename": chunk_metadata["filename"],
                "similarity_score": float(distance)
            })

        logger.info(f"Found {len(results)} results for query")
        return results

    def save(self):
        """Save the FAISS index and metadata to disk"""
        logger.info(f"Saving index to {self.index_path}")

        # Save FAISS index
        faiss.write_index(self.index, str(self.index_path))

        # Save metadata as JSON
        with open(self.metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=2)

        logger.info("Index saved successfully!")

    def load(self):
        """Load an existing FAISS index from disk"""
        logger.info(f"Loading existing index from {self.index_path}")

        # Load FAISS index
        self.index = faiss.read_index(str(self.index_path))

        # Load metadata
        with open(self.metadata_path, "r") as f:
            self.metadata = json.load(f)

        logger.info(f"Loaded index with {self.index.ntotal} embeddings")

    def get_stats(self) -> Dict:
        """Return info about the current index"""
        return {
            "index_name": self.index_name,
            "total_embeddings": self.index.ntotal if self.index else 0,
            "total_chunks": len(self.metadata),
            "dimension": self.dimension
        }


# One shared instance for the whole app
faiss_store = FAISSStore()