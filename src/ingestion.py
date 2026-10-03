import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file with page markers."""
    doc = fitz.open(pdf_path)
    text = ""
    for page_num, page in enumerate(doc):
        text += f"\n=== PAGE {page_num + 1} ===\n"
        text += page.get_text()
    doc.close()
    return text
