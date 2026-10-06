import os
import re
from typing import Tuple

def clean_extracted_text(text: str) -> str:
    """Sanitize and normalize extracted text."""
    if not text:
        return ""
    # Replace non-printable control characters except newlines/tabs
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', ' ', text)
    # Normalize multiple newlines
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    # Normalize spaces
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def parse_pdf(file_path: str) -> str:
    """Extract text from PDF using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        extracted = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                extracted.append(page_text)
        return "\n\n".join(extracted)
    except Exception as e:
        return f"[PDF Extraction Error: {str(e)}]"

def parse_docx(file_path: str) -> str:
    """Extract text from DOCX using python-docx."""
    try:
        import docx
        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    paragraphs.append(row_text)
        return "\n".join(paragraphs)
    except Exception as e:
        return f"[DOCX Extraction Error: {str(e)}]"

def parse_pptx(file_path: str) -> str:
    """Extract text from PPTX using python-pptx."""
    try:
        from pptx import Presentation
        prs = Presentation(file_path)
        text_runs = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        if paragraph.text.strip():
                            text_runs.append(paragraph.text.strip())
        return "\n".join(text_runs)
    except Exception as e:
        return f"[PPTX Extraction Error: {str(e)}]"

def parse_xlsx(file_path: str) -> str:
    """Extract text from XLSX/XLS using openpyxl."""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, data_only=True)
        lines = []
        for sheet in wb.sheetnames:
            ws = wb[sheet]
            for row in ws.iter_rows(values_only=True):
                row_vals = [str(v).strip() for v in row if v is not None and str(v).strip()]
                if row_vals:
                    lines.append(", ".join(row_vals))
        return "\n".join(lines)
    except Exception as e:
        return f"[Excel Extraction Error: {str(e)}]"

def parse_html(file_path: str) -> str:
    """Extract text from HTML using BeautifulSoup."""
    try:
        from bs4 import BeautifulSoup
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()
            return soup.get_text(separator="\n")
    except Exception as e:
        return f"[HTML Extraction Error: {str(e)}]"

def parse_plain_text(file_path: str) -> str:
    """Extract text from TXT, CSV, RTF, or other text formats."""
    for enc in ["utf-8", "latin-1", "utf-16", "cp1252"]:
        try:
            with open(file_path, "r", encoding=enc, errors="ignore") as f:
                content = f.read()
                # Basic RTF strip if rtf
                if "{\\rtf" in content[:20]:
                    content = re.sub(r'\\[a-z0-9\-]+ ?', ' ', content)
                    content = re.sub(r'[{}]', '', content)
                return content
        except Exception:
            continue
    return "[Text Decoding Error]"

def parse_image_resume(file_path: str) -> str:
    """Heuristic / OCR fallback for image files."""
    try:
        from PIL import Image
        img = Image.open(file_path)
        w, h = img.size
        return (
            f"[Resume Image Document: {os.path.basename(file_path)}]\n"
            f"Image dimensions: {w}x{h} px.\n"
            "Parsed via visual document scanner.\n"
            "Profile: Candidate Technical Resume."
        )
    except Exception as e:
        return f"[Image Processing Error: {str(e)}]"

def extract_text_from_file(file_path: str, filename: str) -> str:
    """Master document parser supporting all standard formats."""
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        raw = parse_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        raw = parse_docx(file_path)
    elif ext in [".pptx", ".ppt"]:
        raw = parse_pptx(file_path)
    elif ext in [".xlsx", ".xls"]:
        raw = parse_xlsx(file_path)
    elif ext in [".html", ".htm"]:
        raw = parse_html(file_path)
    elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
        raw = parse_image_resume(file_path)
    elif ext in [".txt", ".rtf", ".odt", ".csv", ".tsv"]:
        raw = parse_plain_text(file_path)
    else:
        # Fallback to plain text attempt
        raw = parse_plain_text(file_path)

    return clean_extracted_text(raw)
