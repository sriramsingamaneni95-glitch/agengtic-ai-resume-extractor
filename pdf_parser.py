"""
Tool: extract raw text from a PDF resume (Point 2).
Requires: pip install pymupdf
"""
def parse_pdf(path: str) -> str:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("Run: pip install pymupdf")

    text_parts = []
    with fitz.open(path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts).strip()
