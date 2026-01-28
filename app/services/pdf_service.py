"""
BhashaAI Backend - PDF Service

Service for generating PDF documents for:
- Question Papers
- Worksheets
- Learning Materials

This service uses fpdf2 for Unicode support (essential for Gujarati)
and custom layout handling.
"""

import io
import os
from datetime import datetime
from typing import Optional

from fpdf import FPDF

from app.models.question_paper import QuestionPaper, Question


class PDFService:
    """
    Service for generating formatted PDF documents.
    """

    FONT_DIR = "assets/fonts"
    FONT_DIR = "assets/fonts"
    REGULAR_FONT = "NotoSans-Regular.ttf"  # Main font (English/Latin)
    BOLD_FONT = "NotoSans-Bold.ttf"
    GUJARATI_REGULAR = "NotoSansGujarati-Regular.ttf"  # Fallback for Gujarati
    GUJARATI_BOLD = "NotoSansGujarati-Bold.ttf"

    def __init__(self):
        """Initialize PDF service configuration."""
        self.font_path_regular = os.path.join(self.FONT_DIR, self.REGULAR_FONT)
        self.font_path_bold = os.path.join(self.FONT_DIR, self.BOLD_FONT)
        self.font_gu_regular = os.path.join(self.FONT_DIR, self.GUJARATI_REGULAR)
        self.font_gu_bold = os.path.join(self.FONT_DIR, self.GUJARATI_BOLD)

        # Verify main fonts
        if not os.path.exists(self.font_path_regular):
            raise FileNotFoundError(
                "English font not found. Please download NotoSans-Regular.ttf"
            )

    def generate_question_paper(self, paper: QuestionPaper) -> bytes:
        """
        Generate a PDF for a question paper.

        Args:
            paper: The QuestionPaper model with questions

        Returns:
            bytes: PDF file content
        """
        pdf = FPDF()
        pdf.add_page()

        # Add fonts
        pdf.add_font("NotoSans", style="", fname=self.font_path_regular)
        pdf.add_font("NotoSans", style="B", fname=self.font_path_bold)

        # Add Gujarati fonts (for fallback)
        pdf.add_font("NotoSansGujarati", style="", fname=self.font_gu_regular)
        if os.path.exists(self.font_gu_bold):
            pdf.add_font("NotoSansGujarati", style="B", fname=self.font_gu_bold)

        # Configure fallbacks: When NotoSans doesn't have a char (like Gujarati), use NotoSansGujarati
        pdf.set_fallback_fonts(["NotoSansGujarati"])

        # Set default font immediately (Using the English one as base)
        pdf.set_font("NotoSans", size=12)

        # --- HEADER ---
        self._add_header(pdf, paper)

        # --- INSTRUCTIONS ---
        if paper.instructions:
            self._add_instructions(pdf, paper.instructions)

        # --- QUESTIONS ---
        self._add_questions(pdf, paper.questions)

        # Output directly to bytes
        return bytes(pdf.output())

    def _add_header(self, pdf: FPDF, paper: QuestionPaper):
        """Add standard exam header."""
        # Institution / Logo placeholder
        if paper.institution and paper.institution.name:
            pdf.set_font("NotoSans", style="B", size=18)
            pdf.cell(
                0, 10, paper.institution.name, align="C", new_x="LMARGIN", new_y="NEXT"
            )

        # Exam Name
        pdf.set_font("NotoSans", style="B", size=16)
        pdf.cell(0, 10, paper.title, align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(5)

        # Details Line (Subject | Date | Time | Marks)
        pdf.set_font("NotoSans", size=10)

        # # Left side: Subject & grade
        # pdf.cell(90, 6, f"Subject: {paper.subject} | Grade: {paper.grade_level or 'N/A'}", align="L")

        # Right side: Marks & Time
        right_text = f"Marks: {paper.total_marks}"
        if paper.duration_minutes:
            right_text += f" | Time: {paper.duration_minutes} mins"

        pdf.cell(0, 6, right_text, align="R", new_x="LMARGIN", new_y="NEXT")

        # Date
        date_str = paper.created_at.strftime("%d-%m-%Y")
        pdf.cell(90, 6, f"Date: {date_str}", align="L", new_x="LMARGIN", new_y="NEXT")

        # Separator line
        pdf.line(pdf.get_x(), pdf.get_y() + 2, 190, pdf.get_y() + 2)
        pdf.ln(5)

    def _add_instructions(self, pdf: FPDF, instructions: str):
        """Add exam instructions section."""
        pdf.set_font("NotoSans", style="B", size=11)
        pdf.cell(0, 8, "Instructions:", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("NotoSans", size=10)
        pdf.multi_cell(0, 6, instructions)
        pdf.ln(5)

    def _add_questions(self, pdf: FPDF, questions: list[Question]):
        """Add list of questions."""
        pdf.set_font("NotoSans", size=11)

        for q in questions:
            # Question number and text
            # Use multi_cell for wrapping text
            # Backup current Y position
            start_y = pdf.get_y()

            # Print Q number
            pdf.cell(10, 6, f"{q.question_number}.", align="R")

            # Print marks on the right
            pdf.set_x(170)
            pdf.cell(20, 6, f"[{q.marks}]", align="R")

            # Bring cursor back for the question text
            pdf.set_xy(25, start_y)

            # Print question text (wrapped) - 145mm width to avoid marks overlap
            pdf.multi_cell(145, 6, q.question_text)

            # Options for MCQ
            if q.question_type == "mcq" and q.options:
                pdf.set_x(30)
                options_str = ""
                for idx, opt in enumerate(q.options):
                    options_str += f"({chr(65 + idx)}) {opt}    "
                pdf.multi_cell(140, 6, options_str)

            # Formatting space
            pdf.ln(4)
