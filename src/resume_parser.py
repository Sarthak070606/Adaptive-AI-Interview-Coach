"""Resume PDF parser using PyMuPDF."""
from pathlib import Path
import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF resume."""
    try:
        doc = fitz.open(pdf_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text("text"))
        doc.close()
        return "\n".join(text_parts).strip()
    except Exception as e:
        raise RuntimeError(f"Failed to read PDF: {e}")
