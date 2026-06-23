import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.ingestion.pdf_loader import load_pdf
from backend.chunking.chunker import chunk_document
from backend.embeddings.embedder import embedder
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
    Upload a PDF, extract text, chunk it, and generate embeddings.
    """
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

    # Extract text
    document = load_pdf(str(save_path))

    # Chunk it
    chunks = chunk_document(
        document,
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap
    )

    # Generate embeddings
    embedded_chunks = embedder.embed_chunks(chunks)

    # Show sample embedding (first 5 numbers only)
    sample_embedding = embedded_chunks[0]["embedding"][:5] if embedded_chunks else []

    return {
        "filename": document.filename,
        "total_pages": document.total_pages,
        "total_chunks": len(chunks),
        "embedding_dimension": len(embedded_chunks[0]["embedding"]) if embedded_chunks else 0,
        "sample_embedding_preview": sample_embedding,
        "message": "PDF processed and embeddings generated successfully!"
    }


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
            detail=f"Page {page_number} doesn't exist. Document has {document.total_pages} pages."
        )

    page = document.pages[page_number - 1]

    return {
        "filename": filename,
        "page_number": page_number,
        "total_pages": document.total_pages,
        "text": page.text,
        "char_count": page.char_count
    }