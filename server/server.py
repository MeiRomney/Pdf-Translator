from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

import fitz  # PyMuPDF
from googletrans import Translator
from docx import Document
from docx.shared import Pt
import pytesseract
from PIL import Image

import io
import time
import re
import os

app = FastAPI()

# CORS - Allow your Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:5500",
        "http://localhost:5173",
        "https://*.vercel.app",
        "https://pdf-translator-five.vercel.app",
        "https://pdf-translator-mei-romneys-projects.vercel.app",
        "https://pdf-translator-khm-en.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "PDF Translator API",
        "status": "active",
        "endpoints": {
            "translate": "/translate (POST)"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

def clean_text_for_xml(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)
    return text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")


def extract_text_from_pdf_ocr(pdf_bytes: bytes, lang: str = 'khm') -> str:
    """Extract text from PDF using OCR (for Khmer PDFs with font issues)"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    
    for page_num, page in enumerate(doc):
        print(f"OCR processing page {page_num + 1}/{len(doc)}...")
        
        # Convert page to image
        # Increase resolution for better OCR (300 DPI)
        mat = fitz.Matrix(300/72, 300/72)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Perform OCR
        # lang='khm' for Khmer, 'eng' for English
        page_text = pytesseract.image_to_string(img, lang=lang)
        page_text = clean_text_for_xml(page_text)
        text += page_text + "\n\n"
    
    doc.close()
    return text.strip()


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes in memory (standard method)"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        page_text = page.get_text()
        page_text = clean_text_for_xml(page_text)
        text += page_text + "\n\n"
    doc.close()
    return text.strip()


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text using googletrans"""
    translator = Translator()
    
    # Split into smaller chunks (googletrans has 15k char limit per request)
    max_chunk = 4500
    paragraphs = text.split("\n")
    chunks = []
    current = ""

    for p in paragraphs:
        if len(current) + len(p) > max_chunk and current:
            chunks.append(current)
            current = p + "\n"
        else:
            current += p + "\n"

    if current:
        chunks.append(current)

    translated_chunks = []

    for i, chunk in enumerate(chunks):
        chunk = clean_text_for_xml(chunk)
        if not chunk.strip():
            translated_chunks.append(chunk)
            continue
            
        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Translating chunk {i + 1}/{len(chunks)} (attempt {attempt + 1})...")
                result = translator.translate(chunk, src=source_lang, dest=target_lang)
                translated_chunks.append(clean_text_for_xml(result.text))
                print(f"✓ Chunk {i + 1}/{len(chunks)} translated successfully")
                time.sleep(0.5)  # Rate limiting
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Retry {attempt + 1}/{max_retries} for chunk {i + 1}: {str(e)}")
                    time.sleep(2)
                else:
                    print(f"Failed to translate chunk {i + 1}: {str(e)}")
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Translation failed on chunk {i + 1}: {str(e)}"
                    )

    return "\n".join(translated_chunks)


def create_docx(text: str) -> io.BytesIO:
    """Create DOCX document in memory and return BytesIO"""
    doc = Document()
    doc.add_heading("Translated Document", level=1)

    text = clean_text_for_xml(text)

    for line in text.split("\n"):
        line = line.strip()
        if line:
            try:
                p = doc.add_paragraph(line)
                for run in p.runs:
                    run.font.size = Pt(12)
            except Exception as e:
                print(f"DOCX error: {e}")

    docx_io = io.BytesIO()
    doc.save(docx_io)
    docx_io.seek(0)
    return docx_io

def create_doc(text: str) -> io.BytesIO:
    """Create DOC document (Word 97-2003 format) - using DOCX library"""
    doc = Document()
    doc.add_heading("Translated Document", level=1)

    text = clean_text_for_xml(text)

    for line in text.split("\n"):
        line = line.strip()
        if line:
            try:
                p = doc.add_paragraph(line)
                for run in p.runs:
                    run.font.size = Pt(12)
            except Exception as e:
                print(f"Doc error: {e}")

    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return doc_io

def create_txt(text: str) -> io.BytesIO:
    """Create plain text file in memory and return BytesIO"""
    text = clean_text_for_xml(text)

    content = "TRANSLATED DOCUMENT\n"
    content += "=" * 50 + "\n\n"
    content += text

    txt_io = io.BytesIO()
    txt_io.write(content.encode('utf-8'))
    txt_io.seek(0)
    return txt_io
    

@app.post("/translate")
async def translate_pdf(
    file: UploadFile = File(...),
    direction: str = Form(...),
    format: str = Form("docx")
):
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        pdf_bytes = await file.read()
        
        print(f"DEBUG: Received direction = '{direction}'")
        
        # Determine if we need OCR based on direction
        if direction == "km-en":
            # Use OCR for Khmer PDFs (better handling of Khmer fonts)
            print("Extracting text using OCR (Khmer)...")
            text = extract_text_from_pdf_ocr(pdf_bytes, lang='khm')
            src, tgt = "km", "en"  # googletrans uses 'km' for Khmer
        else:  # en-km
            # Use standard extraction for English PDFs
            print("Extracting text (standard)...")
            text = extract_text_from_pdf(pdf_bytes)
            src, tgt = "en", "km"
        
        print(f"DEBUG: Source = '{src}', Target = '{tgt}'")

        if not text or len(text) < 10:
            raise HTTPException(status_code=400, detail="Failed to extract text from PDF")

        print(f"Translating {src} → {tgt}")
        translated_text = translate_text(text, src, tgt)

        print(f"Creating {format.upper()} file...")
        if format == "docx":
            file_io = create_docx(translated_text)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = "translated.docx"
        elif format == "doc":
            file_io = create_doc(translated_text)
            media_type = "application/msword"
            filename = "translated.doc"
        else:
            file_io = create_txt(translated_text)
            media_type = "text/plain"
            filename = "translated.txt"

        print("Translation complete!")

        return StreamingResponse(
            file_io,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)