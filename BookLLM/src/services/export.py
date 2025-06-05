import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from ..models.state import BookState
from ..utils.logger import get_logger


class ExportService:
    """Service for exporting book content in various formats"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.logger = get_logger(__name__)
        self.supported_formats = {
            "markdown": self.export_markdown,
            "pdf": self.export_pdf,
            "epub": self.export_epub,
            "html": self.export_html,
            "docx": self.export_docx,
        }

    async def export(
        self, state: BookState, formats: List[str] = None
    ) -> Dict[str, Path]:
        """Export book in multiple formats"""
        if formats is None:
            formats = ["markdown", "pdf"]

        results = {}
        for fmt in formats:
            if fmt not in self.supported_formats:
                self.logger.warning(f"Unsupported format: {fmt}")
                continue

            try:
                output_path = await self.supported_formats[fmt](state)
                results[fmt] = output_path
                self.logger.info(f"Successfully exported to {fmt}: {output_path}")
            except Exception as e:
                self.logger.error(f"Failed to export to {fmt}: {e}")

        return results

    async def export_markdown(self, state: BookState) -> Path:
        """Export book content as Markdown"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"book_{timestamp}.md"

        try:
            content = self._compile_content(state)
            output_path.write_text(content)
            return output_path
        except Exception as e:
            raise RuntimeError(f"Markdown export failed: {e}")

    async def export_pdf(self, state: BookState) -> Path:
        """Export book as PDF using pandoc"""
        md_path = await self.export_markdown(state)
        pdf_path = md_path.with_suffix(".pdf")

        try:
            subprocess.run(
                [
                    "pandoc",
                    str(md_path),
                    "-o",
                    str(pdf_path),
                    "--pdf-engine=xelatex",
                    "--toc",
                    "--toc-depth=3",
                    "--highlight-style=tango",
                    "--variable",
                    "geometry:margin=1in",
                    "--variable",
                    f"title:{state.metadata.get('title', 'Untitled')}",
                    "--top-level-division=chapter",
                ],
                check=True,
            )
            return pdf_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"PDF export failed: {e}")

    async def export_epub(self, state: BookState) -> Path:
        """Export book as EPUB"""
        md_path = await self.export_markdown(state)
        epub_path = md_path.with_suffix(".epub")

        try:
            subprocess.run(
                [
                    "pandoc",
                    str(md_path),
                    "-o",
                    str(epub_path),
                    "--toc",
                    "--toc-depth=3",
                    "--epub-metadata=metadata.yaml",
                    (
                        "--epub-cover-image=" + str(state.cover_image)
                        if state.cover_image
                        else ""
                    ),
                ],
                check=True,
            )
            return epub_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"EPUB export failed: {e}")

    async def export_html(self, state: BookState) -> Path:
        """Export book as HTML"""
        md_path = await self.export_markdown(state)
        html_path = md_path.with_suffix(".html")

        try:
            subprocess.run(
                [
                    "pandoc",
                    str(md_path),
                    "-o",
                    str(html_path),
                    "--standalone",
                    "--toc",
                    "--toc-depth=3",
                    "--css=style.css",
                    "--mathjax",
                    "--highlight-style=tango",
                ],
                check=True,
            )
            return html_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"HTML export failed: {e}")

    async def export_docx(self, state: BookState) -> Path:
        """Export book as DOCX"""
        md_path = await self.export_markdown(state)
        docx_path = md_path.with_suffix(".docx")

        try:
            subprocess.run(
                [
                    "pandoc",
                    str(md_path),
                    "-o",
                    str(docx_path),
                    "--toc",
                    "--toc-depth=3",
                    "--reference-doc=template.docx",
                ],
                check=True,
            )
            return docx_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"DOCX export failed: {e}")

    def _compile_content(self, state: BookState) -> str:
        """Compile book content into a single markdown string"""
        sections = []

        # Front matter
        if state.metadata.get("title"):
            sections.append(f"# {state.metadata['title']}\n")

        if state.preface:
            sections.append(f"## Preface\n\n{state.preface}")

        # Main content
        for i, chapter_title in enumerate(state.chapters, 1):
            content = state.chapter_map.get(chapter_title, "")
            sections.append(f"## Chapter {i}: {chapter_title}\n\n{content}")

        # Back matter
        if state.glossary:
            sections.append("## Glossary\n")
            for term, definition in state.glossary.items():
                sections.append(f"**{term}**: {definition}\n")

        if state.bibliography:
            sections.append(f"## Bibliography\n\n{state.bibliography}")

        return "\n\n".join(sections)
