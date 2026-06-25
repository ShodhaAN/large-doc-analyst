import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.ingestion.pdf_loader import load_pdf
from backend.chunking.chunker import chunk_document
from backend.embeddings.embedder import embedder
from backend.vectorstore.faiss_store import faiss_store
from backend.retrieval.retriever import retriever
from backend.rag.pipeline import rag_pipeline
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
        "message": "Ollama is ready!" if available else "Run 'ollama serve' first!"
    }


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF completely."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed!"
        )

    # Save file
    save_path = settings.upload_dir / file.filename
    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Process pipeline
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
        "message": "PDF processed successfully!"
    }


@router.post("/ask")
async def ask_question(question: str, top_k: int = 5):
    """
    Ask a question about your uploaded documents.
    Uses the full RAG pipeline with Llama 3.
    """
    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty!"
        )

    if not ollama_client.is_available():
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running!"
        )

    result = rag_pipeline.ask(question, top_k=top_k)
    return result


@router.post("/summarize")
async def summarize_document(filename: str):
    """
    Generate a summary of an uploaded document.
    """
    if not ollama_client.is_available():
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running!"
        )

    file_path = settings.upload_dir / filename
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Document '{filename}' not found!"
        )

    result = rag_pipeline.summarize(filename)
    return result


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