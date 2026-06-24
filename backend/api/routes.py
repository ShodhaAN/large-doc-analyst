import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.ingestion.pdf_loader import load_pdf
from backend.chunking.chunker import chunk_document
from backend.embeddings.embedder import embedder
from backend.vectorstore.faiss_store import faiss_store
from backend.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/ping")
async def ping():
    return {"message": "pong"}


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF — extract, chunk, embed and store in FAISS.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed!"
        )

    # Step 1 — Save file
    save_path = settings.upload_dir / file.filename
    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Step 2 — Extract text
    document = load_pdf(str(save_path))

    # Step 3 — Chunk it
    chunks = chunk_document(
        document,
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap
    )

    # Step 4 — Generate embeddings
    embedded_chunks = embedder.embed_chunks(chunks)

    # Step 5 — Store in FAISS
    faiss_store.add_embeddings(embedded_chunks)

    # Get index stats
    stats = faiss_store.get_stats()

    return {
        "filename": document.filename,
        "total_pages": document.total_pages,
        "total_chunks": len(chunks),
        "embeddings_stored": stats["total_embeddings"],
        "message": "PDF processed and stored in vector database!"
    }


@router.get("/search")
async def search(query: str, top_k: int = 5):
    """
    Search for relevant chunks using a text query.
    """
    if not query:
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty!"
        )

    # Convert question to embedding
    query_embedding = embedder.embed_text(query)

    # Search FAISS
    results = faiss_store.search(query_embedding, top_k=top_k)

    if not results:
        return {
            "query": query,
            "results": [],
            "message": "No results found. Upload documents first!"
        }

    return {
        "query": query,
        "total_results": len(results),
        "results": results
    }


@router.get("/stats")
async def get_stats():
    """
    Get stats about the vector store.
    """
    return faiss_store.get_stats()


@router.get("/documents/{filename}/page/{page_number}")
async def get_page(filename: str, page_number: int):
    """
    Get text from a specific page.
    """
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