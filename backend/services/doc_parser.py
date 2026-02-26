import os
import PyPDF2
from docx import Document
from typing import List

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    text = ""
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
    return text

def extract_text_from_docx(file_path: str) -> str:
    """从 Word 文档中提取文字，支持普通段落、表格、文本框"""
    text = ""
    try:
        doc = Document(file_path)

        # 1. 提取普通段落（包括各级标题）
        for para in doc.paragraphs:
            if para.text.strip():
                text += para.text + "\n"

        # 2. 提取表格中的文字
        for table in doc.tables:
            for row in table.rows:
                row_texts = []
                for cell in row.cells:
                    if cell.text.strip():
                        row_texts.append(cell.text.strip())
                if row_texts:
                    text += " | ".join(row_texts) + "\n"

        # 3. 如果还是空的，尝试从 XML 中全量提取文字（针对文本框等特殊结构）
        if not text.strip():
            from lxml import etree
            ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
            xml_bytes = doc.element.xml.encode('utf-8')
            root = etree.fromstring(xml_bytes)
            all_texts = root.iter(f'{{{ns}}}t')
            text = "\n".join(t.text for t in all_texts if t.text and t.text.strip())


    except Exception as e:
        print(f"Error reading DOCX {file_path}: {e}")
    return text


def clean_text(text: str) -> str:
    """清洗文本，去除零宽字符等不可见特殊字符"""
    # 去除各类零宽字符、控制字符等
    import re
    text = re.sub(r'[\u200b\u200c\u200d\ufeff\u00a0]', ' ', text)
    # 去除多余空行
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()

def parse_document(file_path: str) -> str:
    """Parse document based on its extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif ext in [".doc", ".docx"]:
        text = extract_text_from_docx(file_path)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        raise ValueError(f"Unsupported document format: {ext}")
    return clean_text(text)

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into smaller chunks for vectorization."""
    # A simple character-based chunking; in production, token-based is better
    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(start + chunk_size, text_length)
        
        # If not at the end, try to find a natural break (like a newline or period)
        if end < text_length:
            # Look back for a period or newline within the last 50 characters
            lookback = text[end-50:end]
            if "\n" in lookback:
                end = end - 50 + lookback.rfind("\n") + 1
            elif "。" in lookback:
                end = end - 50 + lookback.rfind("。") + 1
            elif "." in lookback:
                end = end - 50 + lookback.rfind(".") + 1
                
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break
            
        next_start = end - overlap
        if next_start <= start:
            next_start = start + 10 # Force advance if overlap causes infinite loop
        start = next_start
        
    return chunks
