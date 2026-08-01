"""
utils/resume_parser.py
──────────────────────
Parses resume content from uploaded PDF or TXT files.
Uses PyPDF2 for PDF extraction and standard text handling for .txt files.
Sanitizes output to remove PII beyond candidate name before downstream use.
"""

import re
import io
from typing import Optional

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract plain text from PDF bytes using PyPDF2.
    Returns extracted text or an error message string.
    """
    if not PYPDF2_AVAILABLE:
        return "⚠️ PyPDF2 not installed. Please run: pip install PyPDF2"

    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages_text = []
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text.strip())
        extracted = "\n\n".join(pages_text)
        return clean_text(extracted) if extracted else "⚠️ No readable text found in PDF."
    except Exception as e:
        return f"⚠️ Could not parse PDF: {str(e)}"


def extract_text_from_txt(file_bytes: bytes) -> str:
    """
    Decode and return plain text from a .txt file.
    Tries UTF-8, falls back to Latin-1.
    """
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1", errors="replace")
    return clean_text(text)


def clean_text(text: str) -> str:
    """
    Basic text cleaning:
    - Collapse excessive blank lines
    - Strip trailing whitespace per line
    - Remove non-printable characters
    """
    # Remove non-printable characters (except newlines and tabs)
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]", " ", text)
    # Strip trailing whitespace per line
    lines = [line.rstrip() for line in text.split("\n")]
    # Collapse 3+ consecutive blank lines into 2
    cleaned_lines = []
    blank_count = 0
    for line in lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count <= 2:
                cleaned_lines.append(line)
        else:
            blank_count = 0
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def extract_candidate_name(resume_text: str) -> str:
    """
    Heuristic to extract candidate name from the first few lines of a resume.
    Returns 'Unknown Candidate' if name cannot be determined.
    """
    lines = [l.strip() for l in resume_text.split("\n") if l.strip()]
    for line in lines[:5]:
        # Skip lines that look like headings, emails, phones, or addresses
        if any(c in line for c in ["@", "+91", "github", "linkedin", "http", "www", "📧", "📞", "📍"]):
            continue
        # Skip lines with common resume section keywords
        skip_keywords = [
            "resume", "cv", "curriculum", "vitae", "profile", "summary",
            "developer", "engineer", "analyst", "scientist", "manager"
        ]
        if any(kw in line.lower() for kw in skip_keywords) and len(line.split()) > 3:
            continue
        # A name is usually 2-4 words, all mostly alphabetic
        words = line.split()
        if 2 <= len(words) <= 4 and all(re.match(r"^[A-Za-z'\-]+$", w) for w in words):
            return line.title()
    return "Unknown Candidate"


def parse_uploaded_file(uploaded_file) -> tuple[str, str]:
    """
    Parse a Streamlit UploadedFile object.
    Returns: (resume_text, candidate_name)
    """
    file_bytes = uploaded_file.read()
    file_name  = uploaded_file.name.lower()

    if file_name.endswith(".pdf"):
        resume_text = extract_text_from_pdf(file_bytes)
    elif file_name.endswith(".txt"):
        resume_text = extract_text_from_txt(file_bytes)
    else:
        resume_text = "⚠️ Unsupported file format. Please upload a PDF or TXT file."

    candidate_name = extract_candidate_name(resume_text)
    return resume_text, candidate_name


def truncate_for_api(text: str, max_chars: int = 6000) -> str:
    """
    Truncate resume text to fit within API token limits.
    Preserves content from start and end of document.
    """
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + "\n\n[... content truncated for API limit ...]\n\n" + text[-half:]
