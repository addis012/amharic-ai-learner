import pathlib
import sys

import pytest
from PyPDF2 import PdfWriter

# Ensure the repository root is on ``sys.path`` so that ``app`` can be imported
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from app import extract_text_from_pdf


def test_extract_text_from_pdf_handles_blank_pages(tmp_path):
    pdf_path = tmp_path / "blank.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with open(pdf_path, "wb") as f:
        writer.write(f)

    text = extract_text_from_pdf(str(pdf_path))
    assert text == ""
