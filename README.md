# DDR Report Generator

AI-powered Detailed Diagnostic Report generator for building inspections.

## How It Works

1. Upload an **Inspection Report PDF** and a **Thermal Report PDF**
2. The system extracts text and images from both documents
3. Groq AI (llama-3.3-70b-versatile) analyzes both reports
4. Images are matched to observations automatically
5. A professional DDR PDF is generated for download

## Tech Stack

- **Frontend**: React + Vite
- **Backend**: FastAPI + Python
- **AI**: Groq (llama-3.3-70b-versatile)
- **PDF Processing**: PyMuPDF (extraction) + ReportLab (generation)

## Setup

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
# Add your GROQ_API_KEY to .env
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

### 🎉 You're done!

The entire DDR pipeline is built and running. You can now:
1. Open `http://localhost:5173`
2. Upload your two sample PDFs
3. Click **Generate DDR Report**
4. Download the AI-generated professional report
