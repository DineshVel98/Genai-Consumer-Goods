import os
from docx import Document


def read_docx(file_path: str) -> Document:
    """
    Reads a .docx file and returns the Document object itself.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    doc = Document(file_path)
    return doc