import logging
from pathlib import Path
from pypdf import PdfReader
from backend.ingestion.models import PageContent, DocumentContent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_pdf(file_path: str) -> DocumentContent:
    """
    Opens a PDF and extracts text from every page.
    """
    path = Path(file_path)

    # Make sure file exists
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    # Make sure it's a PDF
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Not a PDF file: {file_path}")

    logger.info(f"Opening PDF: {path.name}")

    # Open the PDF
    reader = PdfReader(str(path))
    total_pages = len(reader.pages)

    logger.info(f"Total pages found: {total_pages}")

    pages = []
    full_text_parts = []

    # Loop through every page
    for page_num, page in enumerate(reader.pages, start=1):

        # Extract text from this page
        text = page.extract_text() or ""
        text = text.strip()

        # Store this page
        page_content = PageContent(
            page_number=page_num,
            text=text,
            char_count=len(text)
        )

        pages.append(page_content)
        full_text_parts.append(f"[Page {page_num}]\n{text}")

        logger.info(f"Page {page_num}: {len(text)} characters extracted")

    # Join all pages into one big text
    full_text = "\n\n".join(full_text_parts)

    return DocumentContent(
        filename=path.name,
        total_pages=total_pages,
        pages=pages,
        full_text=full_text
    )