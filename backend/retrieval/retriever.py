import logging
from typing import List, Dict
from backend.embeddings.embedder import embedder
from backend.vectorstore.faiss_store import faiss_store
from backend.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Retriever:
    """
    Retrieves the most relevant document chunks for a query.
    
    This is the bridge between the user's question 
    and the vector database.
    """

    def __init__(self):
        self.embedder = embedder
        self.store = faiss_store
        logger.info("Retriever initialized!")

    def retrieve(
        self,
        query: str,
        top_k: int = None
    ) -> List[Dict]:
        """
        Find the most relevant chunks for a question.

        Args:
            query: The user's question in plain English
            top_k: How many chunks to return

        Returns:
            List of relevant chunks with text and page numbers
        """
        if top_k is None:
            top_k = settings.top_k_results

        logger.info(f"Retrieving chunks for: '{query}'")

        # Step 1 — Convert question to numbers
        query_embedding = self.embedder.embed_text(query)

        # Step 2 — Search FAISS for closest chunks
        raw_results = self.store.search(
            query_embedding,
            top_k=top_k
        )

        # Step 3 — Format results nicely
        formatted = []
        for rank, result in enumerate(raw_results, start=1):
            formatted.append({
                "rank": rank,
                "text": result["text"],
                "page": result["start_page"],
                "filename": result["filename"],
                "score": round(result["similarity_score"], 4)
            })

            logger.info(
                f"Result {rank}: page {result['start_page']} "
                f"from {result['filename']} "
                f"(score: {result['similarity_score']:.4f})"
            )

        logger.info(f"Retrieved {len(formatted)} chunks")
        return formatted

    def retrieve_with_context(
        self,
        query: str,
        top_k: int = None
    ) -> Dict:
        """
        Retrieve chunks AND format them as context for the LLM.
        
        This is what we'll pass to Llama 3 in Phase 7.

        Returns:
            Dict with chunks AND a formatted context string
        """
        chunks = self.retrieve(query, top_k=top_k)

        if not chunks:
            return {
                "query": query,
                "chunks": [],
                "context": "No relevant information found.",
                "sources": []
            }

        # Build a formatted context string for the LLM
        context_parts = []
        sources = []

        for chunk in chunks:
            context_parts.append(
                f"[Source: {chunk['filename']}, "
                f"Page {chunk['page']}]\n{chunk['text']}"
            )
            sources.append({
                "filename": chunk["filename"],
                "page": chunk["page"]
            })

        context = "\n\n---\n\n".join(context_parts)

        return {
            "query": query,
            "chunks": chunks,
            "context": context,
            "sources": sources
        }


# One shared instance
retriever = Retriever()