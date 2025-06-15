import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from ..models.state import BookState
from ..utils.case_study_formatter import CaseStudyFormatter
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
        """Export book as professional PDF with headers, footers, and page numbers"""
        md_path = await self.export_markdown(state)
        pdf_path = md_path.with_suffix(".pdf")
        latex_template_path = self._create_professional_latex_template(state)

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
                        "--template", str(latex_template_path),
                        "--toc",
                        "--toc-depth=3",
                        "--highlight-style=tango",
                        "--variable", "geometry:margin=1in",
                        "--variable", "geometry:top=1.5in",
                        "--variable", "geometry:bottom=1.5in",
                        "--variable", f"title:{state.metadata.get('title', 'Professional Book')}",
                        "--variable", f"subtitle:{state.metadata.get('subtitle', '')}",
                        "--variable", f"author:{state.metadata.get('author', 'Expert Author')}",
                        "--variable", f"date:{datetime.now().strftime('%Y')}",
                        "--variable", "book-title:" + state.metadata.get('title', 'Professional Book'),
                        "--variable", "footer-text:" + state.metadata.get('title', 'Professional Book'),
                        "--variable", "documentclass:book",
                        "--variable", "classoption:openright",
                        "--variable", "fontsize:11pt",
                        "--variable", "linestretch:1.2",
                        "--top-level-division=chapter",
                        "--number-sections",
                        "--listings",
                    ],
                    check=True,
                )
                return pdf_path
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Professional PDF export failed: {e}")
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
                sections.append(CaseStudyFormatter.format(case))

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
    
    def _create_professional_latex_template(self, state: BookState) -> Path:
        """Create professional LaTeX template with headers/footers and page numbers"""
        template_path = self.output_dir / "professional_book_template.latex"
        
        book_title = state.metadata.get('title', 'Professional Book')
        
        latex_template = rf"""
\documentclass[$if(fontsize)$$fontsize$,$endif$$if(lang)$$babel-lang$,$endif$$if(papersize)$$papersize$paper,$endif$$for(classoption)$$classoption$$sep$,$endfor$]{{$documentclass-default.latex$}}

% Professional book packages
\usepackage{{lmodern}}
\usepackage{{amsmath,amsfonts,amssymb}}
\usepackage{{ifxetex,ifluatex}}
\usepackage{{fixltx2e}} % provides \textsubscript
\ifnum 0\ifxetex 1\fi\ifluatex 1\fi=0 % if pdftex
  \usepackage[T1]{{fontenc}}
  \usepackage[utf8]{{inputenc}}
\else % if luatex or xelatex
  \ifxetex
    \usepackage{{mathspec}}
  \else
    \usepackage{{fontspec}}
  \fi
  \defaultfontfeatures{{Ligatures=TeX,Scale=MatchLowercase}}
\fi

% Professional page layout
\usepackage{{geometry}}
\geometry{{
  left=1.25in,
  right=1.25in,
  top=1.5in,
  bottom=1.5in,
  headheight=0.5in,
  headsep=0.3in,
  footskip=0.5in
}}

% Headers and footers
\usepackage{{fancyhdr}}
\pagestyle{{fancy}}
\fancyhf{{}} % Clear all header and footer fields

% Header configuration
\fancyhead[LE]{{\textit{{\leftmark}}}} % Even pages: chapter title
\fancyhead[RO]{{\textit{{\rightmark}}}} % Odd pages: section title

% Footer configuration - Book title and page number
\fancyfoot[LE]{{\textit{{{book_title}}} \hfill \thepage}} % Even pages
\fancyfoot[RO]{{\thepage \hfill \textit{{{book_title}}}}} % Odd pages

% Chapter pages style
\fancypagestyle{{plain}}{{
  \fancyhf{{}}
  \fancyfoot[C]{{\textit{{{book_title}}} \hfill \thepage}}
  \renewcommand{{\headrulewidth}}{{0pt}}
  \renewcommand{{\footrulewidth}}{{0.4pt}}
}}

% Header/footer line thickness
\renewcommand{{\headrulewidth}}{{0.4pt}}
\renewcommand{{\footrulewidth}}{{0.4pt}}

% Professional typography
\usepackage{{microtype}}
\usepackage{{setspace}}
\setstretch{{1.15}}

% Enhanced chapter formatting
\usepackage{{titlesec}}
\titleformat{{\chapter}}[display]
  {{\normalfont\huge\bfseries}}
  {{\chaptertitlename\ \thechapter}}
  {{20pt}}
  {{\Huge}}
\titlespacing*{{\chapter}}{{0pt}}{{50pt}}{{40pt}}

% Professional table of contents
\usepackage{{tocloft}}
\renewcommand{{\cftchapfont}}{{\bfseries}}
\renewcommand{{\cfttoctitlefont}}{{\huge\bfseries}}
\setlength{{\cftbeforetoctitleskip}}{{50pt}}
\setlength{{\cftaftertoctitleskip}}{{40pt}}

% Code highlighting
\usepackage{{listings}}
\usepackage{{xcolor}}
\lstset{{
  backgroundcolor=\color{{gray!10}},
  basicstyle=\ttfamily\footnotesize,
  breakatwhitespace=false,
  breaklines=true,
  captionpos=b,
  commentstyle=\color{{green!60!black}},
  escapeinside={{\\%*}}{{*)}},
  extendedchars=true,
  frame=single,
  keepspaces=true,
  keywordstyle=\color{{blue}},
  language=Python,
  morekeywords={{*,...}},
  numbers=left,
  numbersep=5pt,
  numberstyle=\tiny\color{{gray}},
  rulecolor=\color{{black}},
  showspaces=false,
  showstringspaces=false,
  showtabs=false,
  stepnumber=1,
  stringstyle=\color{{red!80!black}},
  tabsize=2,
  title=\lstname
}}

% Professional hyperlinks
\usepackage{{hyperref}}
\hypersetup{{
  colorlinks=true,
  linkcolor=blue!50!black,
  urlcolor=blue!50!black,
  citecolor=blue!50!black,
  pdftitle={{{book_title}}},
  pdfauthor={{$author-meta$}},
  pdfsubject={{Professional Technical Book}},
  pdfkeywords={{Technical, Professional, Book}},
  bookmarksnumbered=true,
  bookmarksopen=true
}}

% Title page formatting
\title{{$title$}}
\author{{$author$}}
\date{{$date$}}

\begin{{document}}

% Professional title page
\begin{{titlepage}}
\centering
\vspace*{{2cm}}
{{\Huge\bfseries $title$ \par}}
\vspace{{1cm}}
$if(subtitle)$
{{\LARGE $subtitle$ \par}}
\vspace{{1.5cm}}
$endif$
{{\Large\itshape $author$ \par}}
\vfill
{{\large Professional Publishing \par}}
{{\large $date$ \par}}
\end{{titlepage}}

% Copyright page
\newpage
\thispagestyle{{empty}}
\vspace*{{\fill}}
\begin{{flushleft}}
\textcopyright\ $date$\ $author$\\

All rights reserved. No part of this publication may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the author.\\

First Edition: $date$\\

ISBN: 978-0-000-00000-0 (Paperback)\\
ISBN: 978-0-000-00000-0 (eBook)\\

Published by Professional Publishing\\
www.professionalpublishing.com\\

Printed in the United States of America
\end{{flushleft}}
\vspace*{{\fill}}

% Table of contents
\newpage
\tableofcontents
\newpage

% Main content
$body$

\end{{document}}
"""
        
        template_path.write_text(latex_template)
        return template_path
