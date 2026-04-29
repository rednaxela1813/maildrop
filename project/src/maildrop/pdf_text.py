from __future__ import annotations

from io import BytesIO


def extract_pdf_text(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""

    try:
        reader = PdfReader(BytesIO(content))
    except Exception:
        return ""

    page_texts: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text:
            page_texts.append(text)

    return "\n".join(page_texts)
