from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import fitz  # PyMuPDF
from googletrans import Translator
from docx import Document
from docx.shared import Pt

import os
import io
import time
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT_DIR = os.path.join(BASE_DIR, "client")

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

translator = Translator()

app.mount("/static", StaticFiles(directory=CLIENT_DIR), name="static")

@app.get("/")
async def read_index():
    with open(os.path.join(CLIENT_DIR, "index.html"), "r", encoding="utf-8") as f:
        content = f.read()
    return StreamingResponse(io.StringIO(content), media_type="text/html")

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
            result = translator.translate(chunk, src=source_lang, dest=target_lang)
            translated_chunks.append(clean_text_for_xml(result.text))
            print(f"Translated chunk {i + 1}/{len(chunks)}")
            time.sleep(0.5)
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

    # Save to BytesIO instead of file
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
        # Read PDF into memory
        pdf_bytes = await file.read()
        
        print("Extracting text...")
        text = extract_text_from_pdf(pdf_bytes)

        if not text or len(text) < 10:
            raise Exception("Failed to extract text from PDF")

        src, tgt = ("en", "km") if direction == "en-km" else ("km", "en")

        print(f"Translating {src} → {tgt}")
        translated_text = translate_text(text, src, tgt)

        print("Creating DOCX...")
        docx_io = create_docx(translated_text)

        print("Translation complete!")

        # Stream the file directly to client
        return StreamingResponse(
            docx_io,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": "attachment; filename=translated.docx"
            }
        )

    except Exception as e:
        print("Error:", e)
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)