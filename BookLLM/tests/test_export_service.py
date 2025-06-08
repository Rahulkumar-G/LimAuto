import sys
import asyncio
from pathlib import Path

import pytest

# Ensure repository root is on the path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from BookLLM.src.models.state import BookState
from BookLLM.src.services.export import ExportService


def test_export_pdf_fallback(tmp_path, monkeypatch):
    state = BookState(
        topic="PDF",
        chapters=["Intro"],
        chapter_map={"Intro": "Some content"},
        metadata={"title": "Test"},
    )
    exporter = ExportService(output_dir=tmp_path)
    monkeypatch.setattr("BookLLM.src.services.export.shutil.which", lambda cmd: None)
    pdf_path = asyncio.run(exporter.export_pdf(state))
    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"
