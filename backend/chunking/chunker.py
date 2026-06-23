import logging
from dataclasses import dataclass
from typing import List
from backend.ingestion.models import DocumentContent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """Represents one chunk of text from a document"""
    chunk_id: int          # Unique ID for this chunk (0, 1, 2...)
    text: str              # The actual text content
    start_page: int        # Which page this chunk starts on
    end_page: int          # Which page this chunk ends on
    filename: str          # Which document this came from
    char_count: int        # How many characters in this chunk


def chunk_document(
    document: DocumentContent,
    chunk_size: int = 500,
    overlap: int = 50
) -> List[TextChunk]:
    """
    Splits a document into overlapping chunks.

    Args:
        document: The full document loaded by pdf_loader
        chunk_size: How many characters per chunk
        overlap: How many characters to share between chunks

    Returns:
        A list of TextChunk objects
    """
    logger.info(f"Chunking document: {document.filename}")
    logger.info(f"Chunk size: {chunk_size}, Overlap: {overlap}")

    chunks = []
    chunk_id = 0

    # Process each page separately
    # This way we always know which page a chunk came from
    for page in document.pages:

        text = page.text
        page_num = page.page_number

        # Skip empty pages
        if not text.strip():
            logger.info(f"Page {page_num}: empty, skipping")
            continue

        # Split this page's text into chunks
        start = 0

        while start < len(text):
            # Calculate end position
            end = start + chunk_size

            # Get the chunk text
            chunk_text = text[start:end].strip()

            # Skip empty chunks
            if not chunk_text:
                break

            # Create the chunk object
            chunk = TextChunk(
                chunk_id=chunk_id,
                text=chunk_text,
                start_page=page_num,
                end_page=page_num,
                filename=document.filename,
                char_count=len(chunk_text)
            )

            chunks.append(chunk)
            chunk_id += 1

            # Move forward by (chunk_size - overlap)
            # This creates the overlapping effect
            step = chunk_size - overlap
            start += step

    logger.info(f"Created {len(chunks)} chunks from {document.filename}")
    return chunks


def get_chunks_for_page(
    chunks: List[TextChunk],
    page_number: int
) -> List[TextChunk]:
    """
    Get all chunks that belong to a specific page.

    Args:
        chunks: All chunks from the document
        page_number: Which page you want chunks for

    Returns:
        List of chunks from that page
    """
    return [
        chunk for chunk in chunks
        if chunk.start_page <= page_number <= chunk.end_page
    ]