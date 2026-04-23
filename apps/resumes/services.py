import io
import docx
import pdfplumber
from django.core.files.storage import default_storage


def parse_pdf(file_content: bytes) -> str:
    text = ''
    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + '\n'
    return text


def parse_docx(file_content: bytes) -> str:
    doc = docx.Document(io.BytesIO(file_content))
    text = ''
    for para in doc.paragraphs:
        text += para.text + '\n'
    return text


def parse_resume(file, filename: str) -> str:
    content = file.read()
    ext = filename.lower().split('.')[-1]

    if ext == 'pdf':
        return parse_pdf(content)
    elif ext in ['docx', 'doc']:
        return parse_docx(content)
    else:
        return content.decode('utf-8', errors='ignore')


def get_file_bytes(file):
    file.seek(0)
    return file.read()


def save_file(user_id: str, filename: str, content: bytes) -> str:
    path = f"resumes/{user_id}/{filename}"
    default_storage.save(path, io.BytesIO(content))
    return path


def count_words(text: str) -> int:
    return len(text.split())