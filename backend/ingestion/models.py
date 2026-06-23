from dataclasses import dataclass, field
from typing import List


@dataclass
class PageContent:
    """Represents one single page from a PDF"""
    page_number: int        # Which page (1, 2, 3...)
    text: str               # The actual text on that page
    char_count: int         # How many characters on this page


@dataclass
class DocumentContent:
    """Represents the entire PDF document"""
    filename: str                           # e.g. "contract.pdf"
    total_pages: int                        # Total number of pages
    pages: List[PageContent] = field(default_factory=list)  # All pages
    full_text: str = ""                     # All text joined together

    @property
    def total_chars(self) -> int:
        """Total characters in the whole document"""
        return sum(page.char_count for page in self.pages)