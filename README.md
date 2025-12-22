# 📄 PDF Translator

A web application that translates PDF documents between English and Khmer.
The project consists of a FastAPI backend and a static frontend (HTML/CSS/JS).

Live site: https://pdf-translator-mei-romneys-projects.vercel.app/

---

## Features

- Upload a PDF document and select translation direction:
  - English → Khmer
  - Khmer → English
- Uses Deep Translator (Google Translate API) for translation.
- Generates and downloads the translated document as a DOCX file.
- Drag-and-drop PDF support.
- Works locally and can be deployed to Render (backend) + Vercel (frontend).

---

## Project Structure
```
pdf-translator/
├─ server/                  # FastAPI backend
│  ├─ server.py             # Main backend script
│  └─ requirements.txt
├─ client/                  # Frontend
│  ├─ index.html
│  ├─ style.css
│  └─ script.js
└─ README.md
```
---

## Tech Stack

- Backend: Python 3.11+, FastAPI, PyMuPDF, deep-translator, python-docx
- Frontend: HTML, CSS, Vanilla JavaScript
- Deployment: Render (backend), Vercel (frontend)

---

## Local Setup
1. Clone the repository
```
git clone https://github.com/your-username/pdf-translator.git
cd pdf-translator
```
2. Setup Backend (FastAPI)
```
cd server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

3. Run Backend
```
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

Your API will be available at: http://localhost:8000 <br/>
Health check: http://localhost:8000/health <br/>
Translate endpoint: POST http://localhost:8000/translate <br/>

4. Run Frontend

Open <mark>client/index.html</mark> in your browser (or use a live server plugin like VSCode Live Server). </br>
<b>Note:</b> Make sure the API_URL in script.js points to your backend URL:
```
const API_URL = "http://localhost:8000";
```

---

## CORS Configuration

The backend allows cross-origin requests from your frontend:
```
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5500",
        "https://*.vercel.app",
        "https://pdf-translator-mei-romneys-projects.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Deployment
### Backend (Render)

1. Push your backend (server) to a repository.
2. Connect Render and select Python service.
3. Use uvicorn server:app --host 0.0.0.0 --port $PORT as the start command.
4. Set the Python runtime version in runtime.txt (e.g., python-3.11.6).

### Frontend (Vercel)

1. Push your client folder to a repository or monorepo.
2. Deploy the frontend on Vercel.
3. Update API_URL in script.js to point to your deployed backend:
```
const API_URL = "https://your-backend-service.onrender.com";
```

---

## Usage

Open the [live site](https://pdf-translator-mei-romneys-projects.vercel.app/)

1. Upload a PDF file.
2. Select the translation direction.
3. Click Translate PDF.
4. Wait for processing.
5. Download the translated DOCX file.

---

## Troubleshooting

- CORS errors: Make sure the frontend origin is allowed in FastAPI middleware.
- Translation issues: Large PDFs may take several minutes; consider splitting large files.
- Dependencies: Ensure Python 3.11+ is used; use pip install -r requirements.txt.

---

## Dependencies

- fastapi
- uvicorn
- PyMuPDF (fitz)
- deep-translator
- python-docx
- CORS middleware (fastapi.middleware.cors)
- standard Python libraries (io, re, time, os)

--

## Contact

For questions or support, reach out to:
📧 <a>mei.romney987@gmail.com</a>
