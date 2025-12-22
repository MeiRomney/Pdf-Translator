from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

import fitz  # PyMuPDF
from deep_translator import GoogleTranslator
from docx import Document
from docx.shared import Pt

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
        "https://*.vercel.app",  # All Vercel preview deployments
        "https://pdf-translator-five.vercel.app",  # Replace with your actual Vercel URL
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


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes in memory"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        page_text = page.get_text()
        page_text = clean_text_for_xml(page_text)
        text += page_text + "\n\n"
    doc.close()
    return text.strip()


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text using deep-translator"""
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
        try:
            chunk = clean_text_for_xml(chunk)
            if chunk.strip():  # Only translate non-empty chunks
                translator = GoogleTranslator(source=source_lang, target=target_lang)
                result = translator.translate(chunk)
                translated_chunks.append(clean_text_for_xml(result))
                print(f"Translated chunk {i + 1}/{len(chunks)}")
                time.sleep(0.5)  # Rate limiting
            else:
                translated_chunks.append(chunk)
        except Exception as e:
            print(f"Translation error on chunk {i}: {e}")
            translated_chunks.append(chunk)

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

@app.post("/translate")
async def translate_pdf(
    file: UploadFile = File(...),
    direction: str = Form(...)
):
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Read PDF into memory
        pdf_bytes = await file.read()
        
        print("Extracting text...")
        text = extract_text_from_pdf(pdf_bytes)

        if not text or len(text) < 10:
            raise HTTPException(status_code=400, detail="Failed to extract text from PDF")

        # Map language codes for deep-translator
        # deep-translator uses 'km' for Khmer and 'en' for English
        src, tgt = ("en", "km") if direction == "en-km" else ("km", "en")

        print(f"Translating {src} → {tgt}")
        translated_text = translate_text(text, src, tgt)

        print("Creating DOCX...")
        docx_io = create_docx(translated_text)

        print("Translation complete!")

        return StreamingResponse(
            docx_io,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": "attachment; filename=translated.docx"
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