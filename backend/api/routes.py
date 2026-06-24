import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.ingestion.pdf_loader import load_pdf
from backend.chunking.chunker import chunk_document
from backend.embeddings.embedder import embedder
from backend.vectorstore.faiss_store import faiss_store
from backend.retrieval.retriever import retriever
from backend.llm.ollama_client import ollama_client
from backend.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/ping")
async def ping():
    return {"message": "pong"}


@router.get("/ollama/status")
async def ollama_status():
    """Check if Ollama is running"""
    available = ollama_client.is_available()
    return {
        "ollama_running": available,
        "model": settings.ollama_model,
        "message": "Ollama is ready!" if available else "Ollama is not running. Run 'ollama serve' in terminal."
    }


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF and process it completely."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed!"
        )

    save_path = settings.upload_dir / file.filename
    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)

    document = load_pdf(str(save_path))
    chunks = chunk_document(
        document,
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap
    )
    embedded_chunks = embedder.embed_chunks(chunks)
    faiss_store.add_embeddings(embedded_chunks)
    stats = faiss_store.get_stats()

    return {
        "filename": document.filename,
        "total_pages": document.total_pages,
        "total_chunks": len(chunks),
        "embeddings_stored": stats["total_embeddings"],
        "message": "PDF processed and stored successfully!"
    }


@router.post("/ask")
async def ask_question(query: str, top_k: int = 5):
    """
    Ask a question about your uploaded documents.
    Uses RAG: retrieves relevant chunks then asks Llama 3.
    """
    if not query:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty!"
        )

    # Check Ollama is running
    if not ollama_client.is_available():
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running! Open a terminal and run: ollama serve"
        )

    # Step 1 — Find relevant chunks
    retrieved = retriever.retrieve_with_context(query, top_k=top_k)

    if not retrieved["chunks"]:
        return {
            "question": query,
            "answer": "I couldn't find relevant information. Please upload documents first.",
            "sources": []
        }

    # Step 2 — Build prompt for Llama 3
    prompt = f"""You are a helpful document analyst assistant.
Use the following context from uploaded documents to answer the question.
Be specific and mention page numbers when relevant.
If the answer is not in the context, say "I don't have enough information to answer this."

CONTEXT:
{retrieved['context']}

QUESTION: {query}

ANSWER:"""

    # Step 3 — Get answer from Llama 3
    answer = ollama_client.generate(prompt)

    return {
        "question": query,
        "answer": answer,
        "sources": retrieved["sources"],
        "chunks_used": len(retrieved["chunks"])
    }


@router.get("/search")
async def search(query: str, top_k: int = 5):
    """Search documents using natural language."""
    if not query:
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty!"
        )

    result = retriever.retrieve_with_context(query, top_k=top_k)

    return {
        "query": result["query"],
        "total_results": len(result["chunks"]),
        "sources": result["sources"],
        "chunks": result["chunks"]
    }


@router.get("/stats")
async def get_stats():
    """Get vector store statistics."""
    return faiss_store.get_stats()


@router.get("/documents/{filename}/page/{page_number}")
async def get_page(filename: str, page_number: int):
    """Get text from a specific page."""
    file_path = settings.upload_dir / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Document '{filename}' not found"
        )

    document = load_pdf(str(file_path))

    if page_number < 1 or page_number > document.total_pages:
        raise HTTPException(
            status_code=400,
            detail=f"Page {page_number} doesn't exist."
        )

    page = document.pages[page_number - 1]

    return {
        "filename": filename,
        "page_number": page_number,
        "total_pages": document.total_pages,
        "text": page.text,
        "char_count": page.char_count
    }