import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from ..models.state import BookState
from ..utils.logger import get_logger
from ..utils.style_guide import StyleGuideEnforcer


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
            content = StyleGuideEnforcer.enforce(content)
            output_path.write_text(content)
            return output_path
        except Exception as e:
            raise RuntimeError(f"Markdown export failed: {e}")

    async def export_pdf(self, state: BookState) -> Path:
        """Export book as PDF using pandoc or fallback to FPDF"""
        md_path = await self.export_markdown(state)
        pdf_path = md_path.with_suffix(".pdf")

        pandoc_available = shutil.which("pandoc") and shutil.which("xelatex")

        if pandoc_available:
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
        else:
            # Simple fallback PDF generation using FPDF
            try:
                from fpdf import FPDF

                pdf = FPDF()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.add_page()
                pdf.set_font("Helvetica", size=12)

                width = pdf.w - 2 * pdf.l_margin
                for line in md_path.read_text().splitlines():
                    if line.startswith("# "):
                        pdf.set_font("Helvetica", "B", 16)
                        pdf.multi_cell(width, 10, line[2:])
                        pdf.set_font("Helvetica", size=12)
                    elif line.startswith("## "):
                        pdf.set_font("Helvetica", "B", 14)
                        pdf.multi_cell(width, 10, line[3:])
                        pdf.set_font("Helvetica", size=12)
                    else:
                        pdf.multi_cell(width, 10, line)

                pdf.output(str(pdf_path))
                return pdf_path
            except Exception as e:
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
        if state.title_page:
            sections.append(state.title_page)
        elif state.metadata.get("title"):
            title_line = f"# {state.metadata['title']}"
            if state.metadata.get("subtitle"):
                title_line += f"\n\n## {state.metadata['subtitle']}"
            sections.append(title_line)

        if state.preface:
            sections.append(f"## Preface\n\n{state.preface}")

        # Main content
        for i, chapter_title in enumerate(state.chapters, 1):
            content = state.chapter_map.get(chapter_title, "")
            sections.append(f"## Chapter {i}: {chapter_title}\n\n{content}")
            case = state.case_studies.get(chapter_title)
            if case:
                sections.append(f"### Case Study\n\n{case}")

            questions = state.check_questions.get(chapter_title)
            if questions:
                sections.append("### Check Your Understanding")
                for q in questions:
                    sections.append(f"- {q}")

            template = state.templates.get(chapter_title)
            if template:
                sections.append(f"### Template\n\n{template}")

        # Back matter
        if state.glossary:
            sections.append("## Glossary\n")
            for term, definition in state.glossary.items():
                sections.append(f"**{term}**: {definition}\n")

        if state.bibliography:
            sections.append(f"## Bibliography\n\n{state.bibliography}")

        if state.acknowledgments:
            sections.append(f"## Acknowledgments\n\n{state.acknowledgments}")

        if state.about_the_author:
            sections.append(f"## About the Author\n\n{state.about_the_author}")

        if state.index_terms:
            sections.append("## Index\n")
            for term in state.index_terms:
                sections.append(f"- {term}")

        return "\n\n".join(sections)
