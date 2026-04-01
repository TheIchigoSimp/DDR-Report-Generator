# DDR Report Generation System — Implementation Plan

## Goal

Build a full-stack AI pipeline that accepts two PDF documents (Inspection Report + Thermal Report), extracts their content, analyzes them via Groq LLM, and generates a professional Detailed Diagnostic Report (DDR) as a downloadable PDF.

---

## Architecture Overview

```mermaid
graph LR
    A[React UI] -->|Upload 2 PDFs| B[FastAPI Backend]
    B --> C[extractor.py]
    C -->|Text + Images| D[llm_analyzer.py]
    D -->|Structured JSON| E[image_matcher.py]
    E -->|Observations + Images| F[report_builder.py]
    F -->|DDR PDF| B
    B -->|Download Link| A
```

**Flow:**
1. User uploads Inspection PDF + Thermal PDF via React UI
2. FastAPI receives files, saves temporarily
3. `extractor.py` extracts text and images from both PDFs
4. `llm_analyzer.py` sends both texts to Groq (llama-3.3-70b-versatile) → gets structured JSON
5. `image_matcher.py` matches extracted images to observations via keyword hints
6. `report_builder.py` generates a professional PDF using ReportLab
7. PDF is returned to the React UI for download

---

## User Review Required

> [!IMPORTANT]
> **Backend Framework**: The spec mentions a React frontend but doesn't specify a backend API framework. I'll use **FastAPI** to serve the React app and handle file uploads/processing. This is the lightest-weight option that supports async and file uploads cleanly.

> [!IMPORTANT]
> **React Setup**: I'll use **Vite + React** for the frontend (fast, minimal config). The UI will be a single-page app with file uploaders, a generate button, progress indicator, and download button.

> [!NOTE]
> **Groq Model**: Using `llama-3.3-70b-versatile` as specified. The system prompt will enforce JSON-only output with strict rules about not inventing facts.

---

## Proposed Changes

### Project Structure

```
c:\Ichigo\Code\Python\UrbanRoof\
├── backend/
│   ├── main.py                 # FastAPI app — routes, file handling, orchestration
│   ├── extractor.py            # PDF text + image extraction (PyMuPDF)
│   ├── llm_analyzer.py         # Groq API call + JSON parsing
│   ├── image_matcher.py        # Match images to observations by keyword
│   ├── report_builder.py       # ReportLab PDF generation
│   ├── requirements.txt        # Python dependencies
│   └── .env                    # GROQ_API_KEY (gitignored)
├── frontend/                   # Vite + React app
│   ├── src/
│   │   ├── App.jsx             # Main app component
│   │   ├── App.css             # Styles
│   │   ├── main.jsx            # Entry point
│   │   └── index.css           # Global styles
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

---

### Backend — Python Modules

#### [NEW] [main.py](file:///c:/Ichigo/Code/Python/UrbanRoof/backend/main.py)

FastAPI application with:
- `POST /api/generate-ddr` — accepts two PDF files, orchestrates the pipeline, returns DDR PDF
- `GET /api/download/{filename}` — serves generated PDFs for download
- `GET /api/status` — health check
- CORS middleware for React dev server
- Temp file cleanup after response

#### [NEW] [extractor.py](file:///c:/Ichigo/Code/Python/UrbanRoof/backend/extractor.py)

`extract_pdf_content(pdf_path: str) -> dict` using PyMuPDF:
- Extract text page-by-page with `--- Page N ---` markers
- Extract all embedded images with page number, index, raw bytes, extension
- Save images to `./extracted_images/{inspection|thermal}/`
- Handles PDFs with no images or no text gracefully

#### [NEW] [llm_analyzer.py](file:///c:/Ichigo/Code/Python/UrbanRoof/backend/llm_analyzer.py)

`generate_ddr_structure(inspection_text: str, thermal_text: str) -> dict`:
- System prompt enforcing JSON-only output with the exact schema
- Rules: no invented facts, "Not Available" for missing info, conflict flagging, no jargon
- User message with both texts clearly labeled
- JSON parsing with fallback (strip markdown fences if model adds them)
- Retry logic (up to 2 retries on parse failure)

#### [NEW] [image_matcher.py](file:///c:/Ichigo/Code/Python/UrbanRoof/backend/image_matcher.py)

`match_images_to_sections(observations: list, inspection_images: list, thermal_images: list) -> list`:
- For each observation, check `image_hint` field
- Keyword match against image filenames and page context
- Thermal hints → thermal images, inspection hints → inspection images
- Returns observations with added `image_path` field (or `None`)

#### [NEW] [report_builder.py](file:///c:/Ichigo/Code/Python/UrbanRoof/backend/report_builder.py)

`build_pdf_report(ddr_data: dict, output_path: str)` using ReportLab:
- **Cover/Header** — Title, date, AI-generated disclaimer
- **Property Issue Summary** — paragraph
- **Area-wise Observations** — subheadings with observation text + matched images (or grey "Image Not Available")
- **Probable Root Cause** — paragraph
- **Severity Assessment** — colored badge (Red/Orange/Yellow/Green) + reasoning
- **Recommended Actions** — numbered list
- **Additional Notes** — paragraph
- **Missing or Unclear Information** — bulleted list
- Professional styling: Helvetica, bold headers, proper spacing, page numbers in footer
- Images sized max ~400px wide with captions

#### [NEW] [requirements.txt](file:///c:/Ichigo/Code/Python/UrbanRoof/backend/requirements.txt)

```
fastapi
uvicorn[standard]
python-multipart
groq
PyMuPDF
reportlab
Pillow
python-dotenv
```

---

### Frontend — React (Vite)

#### [NEW] [App.jsx](file:///c:/Ichigo/Code/Python/UrbanRoof/frontend/src/App.jsx)

Single-page app with:
- Two file upload zones (drag & drop + click) with PDF validation
- "Generate DDR" button (disabled until both files uploaded)
- Progress spinner with status messages ("Extracting PDFs...", "Analyzing with AI...", "Building report...")
- Success state with download button
- Error handling with clear user-facing messages
- Modern dark-themed UI with glassmorphism, smooth animations

#### [NEW] [App.css](file:///c:/Ichigo/Code/Python/UrbanRoof/frontend/src/App.css)

Premium design:
- Dark gradient background
- Glassmorphic card containers
- Animated upload zones with hover effects
- Pulsing progress indicator
- Color-coded status messages
- Responsive layout

---

## Open Questions

> [!IMPORTANT]
> 1. **Groq API Key**: Do you already have a `GROQ_API_KEY` ready, or do I need to include instructions for obtaining one?

> [!NOTE]  
> 2. **Sample PDFs**: Do you have sample Inspection and Thermal report PDFs to test with, or should I include test instructions for any generic PDFs?

---

## Verification Plan

### Automated Tests
1. `pip install -r requirements.txt` — verify all dependencies install
2. `npm install && npm run build` — verify React app builds
3. Start backend: `uvicorn main:app --reload` — verify server starts
4. Start frontend: `npm run dev` — verify React dev server starts

### Manual Verification
1. Open React UI in browser
2. Upload two sample PDFs
3. Click "Generate DDR"
4. Verify progress states display correctly
5. Download generated PDF and verify:
   - All sections present
   - Images embedded (or "Image Not Available" shown)
   - Professional styling
   - Page numbers in footer
6. Test error cases: upload non-PDF, upload only one file, upload empty PDF
