import logging
from typing import List, Dict, Optional
from backend.embeddings.embedder import embedder
from backend.vectorstore.faiss_store import faiss_store
from backend.retrieval.retriever import retriever
from backend.llm.ollama_client import ollama_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    The complete RAG pipeline in one clean class.
    
    RAG = Retrieval Augmented Generation
    
    What it does:
    1. Takes a user question
    2. Finds relevant document chunks
    3. Sends chunks + question to Llama 3
    4. Returns a proper answer with sources
    """

    def __init__(self):
        self.embedder = embedder
        self.store = faiss_store
        self.retriever = retriever
        self.llm = ollama_client
        logger.info("RAG Pipeline initialized!")

    def ask(
        self,
        question: str,
        top_k: int = 5,
        temperature: float = 0.3
    ) -> Dict:
        """
        Ask a question and get an answer from your documents.

        Args:
            question: The user's question in plain English
            top_k: How many chunks to retrieve
            temperature: How creative Llama 3 should be

        Returns:
            Dict with answer, sources, and metadata
        """
        logger.info(f"Processing question: '{question}'")

        # Step 1 — Retrieve relevant chunks
        retrieved = self.retriever.retrieve_with_context(
            question,
            top_k=top_k
        )

        # Step 2 — Handle empty results
        if not retrieved["chunks"]:
            return {
                "question": question,
                "answer": "I couldn't find relevant information in the uploaded documents. Please make sure you have uploaded documents first.",
                "sources": [],
                "chunks_used": 0,
                "confidence": "low"
            }

        # Step 3 — Build a smart prompt
        prompt = self._build_prompt(question, retrieved["context"])

        # Step 4 — Get answer from Llama 3
        answer = self.llm.generate(
            prompt,
            temperature=temperature
        )

        # Step 5 — Extract unique sources
        unique_sources = self._get_unique_sources(retrieved["sources"])

        logger.info(f"Answer generated with {len(unique_sources)} sources")

        return {
            "question": question,
            "answer": answer,
            "sources": unique_sources,
            "chunks_used": len(retrieved["chunks"]),
            "confidence": "high" if len(retrieved["chunks"]) >= 3 else "medium"
        }

    def summarize(self, filename: str) -> Dict:
        """
        Generate a summary of an entire document.

        Args:
            filename: Name of the uploaded PDF to summarize

        Returns:
            Dict with summary and key points
        """
        logger.info(f"Summarizing document: {filename}")

        # Search for chunks from this specific file
        query_embedding = self.embedder.embed_text(
            "main topics overview summary key points"
        )

        all_results = self.store.search(
            query_embedding,
            top_k=10
        )

        # Filter to only this document
        doc_chunks = [
            r for r in all_results
            if r["filename"] == filename
        ]

        if not doc_chunks:
            return {
                "filename": filename,
                "summary": "Document not found. Please upload it first.",
                "key_points": []
            }

        # Build context from chunks
        context = "\n\n".join([
            f"[Page {c['start_page']}]: {c['text']}"
            for c in doc_chunks
        ])

        # Build summarization prompt
        prompt = f"""You are a document analyst. 
Read the following content from a document and provide:
1. A clear 3-4 sentence summary
2. 5 key points as bullet points
3. The main topic of the document

DOCUMENT CONTENT:
{context}

Provide a structured response with:
SUMMARY:
[Your summary here]

KEY POINTS:
- [Point 1]
- [Point 2]
- [Point 3]
- [Point 4]
- [Point 5]

MAIN TOPIC:
[Main topic here]"""

        summary = self.llm.generate(prompt, temperature=0.3)

        return {
            "filename": filename,
            "summary": summary,
            "chunks_analyzed": len(doc_chunks)
        }

    def _build_prompt(self, question: str, context: str) -> str:
        """
        Build a well-structured prompt for Llama 3.
        Good prompts = better answers!
        """
        return f"""You are an expert document analyst assistant.
Your job is to answer questions based ONLY on the provided document context.

RULES:
1. Only use information from the provided context
2. Always mention page numbers when available
3. If the answer is not in the context, say "I don't have enough information"
4. Be concise and clear
5. Use bullet points for lists

CONTEXT FROM DOCUMENTS:
{context}

QUESTION: {question}

ANSWER:"""

    def _get_unique_sources(self, sources: List[Dict]) -> List[Dict]:
        """Remove duplicate sources"""
        seen = set()
        unique = []
        for source in sources:
            key = f"{source['filename']}_page_{source['page']}"
            if key not in seen:
                seen.add(key)
                unique.append(source)
        return unique


# One shared instance
rag_pipeline = RAGPipeline()