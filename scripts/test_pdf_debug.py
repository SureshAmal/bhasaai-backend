import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from fpdf import FPDF
from app.services.pdf_service import PDFService
from app.models.question_paper import QuestionPaper, Question
from uuid import uuid4
from datetime import datetime

def test_generation():
    print(f"CWD: {os.getcwd()}")
    
    # Check font file explicitly
    font_path = "assets/fonts/NotoSansGujarati-Regular.ttf"
    if os.path.exists(font_path):
        print(f"Font found at {font_path}, size: {os.path.getsize(font_path)}")
    else:
        print(f"ERROR: Font NOT found at {font_path}")
        # Try finding it
        for root, dirs, files in os.walk("."):
            if "NotoSansGujarati-Regular.ttf" in files:
                print(f"Found font at: {os.path.join(root, 'NotoSansGujarati-Regular.ttf')}")

    # Create dummy paper
    paper = QuestionPaper(
        id=str(uuid4()),
        user_id=str(uuid4()),
        title="Test Paper Gujarati",
        subject="Maths",
        total_marks=100,
        grade_level="10",
        language="gu",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        status="generated",
        difficulty_distribution={},
        question_type_distribution={},
    )
    
    q1 = Question(
        id=str(uuid4()),
        paper_id=paper.id,
        question_number=1,
        question_text="English Text Mixed with Gujarati: ગુજરાતી ટેક્સ્ટ",
        marks=1.0,
        question_type="short_answer"
    )
    paper.questions = [q1]

    print("\nAttempting to generate PDF...")
    try:
        service = PDFService()
        pdf_bytes = service.generate_question_paper(paper)
        print(f"Success! Generated {len(pdf_bytes)} bytes.")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_generation()
