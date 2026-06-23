import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.ingestion.pdf_loader import load_pdf
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
    Upload a PDF file and extract its text.
    """
    # Only allow PDF files
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed!"
        )

    # Save the file to disk
    save_path = settings.upload_dir / file.filename

    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)

    logger.info(f"Saved file: {save_path}")

    # Extract text from the PDF
    document = load_pdf(str(save_path))

    # Send back a summary
    return {
        "filename": document.filename,
        "total_pages": document.total_pages,
        "total_characters": document.total_chars,
        "preview": document.pages[0].text[:300] if document.pages else "",
        "message": "PDF uploaded and processed successfully!"
    }


@router.get("/documents/{filename}/page/{page_number}")
async def get_page(filename: str, page_number: int):
    """
    Get text from a specific page of a document.
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
            detail=f"Page {page_number} doesn't exist. This document has {document.total_pages} pages."
        )

    page = document.pages[page_number - 1]

    return {
        "filename": filename,
        "page_number": page_number,
        "total_pages": document.total_pages,
        "text": page.text,
        "char_count": page.char_count
    }