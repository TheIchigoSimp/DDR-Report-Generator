import os
import uuid
import shutil
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from extractor import extract_pdf_content
from llm_analyzer import generate_ddr_structure
from image_matcher import match_images_to_sections
from report_builder import build_pdf_report

app = FastAPI(title="DDR Report Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "temp_uploads"
OUTPUT_DIR = "generated_reports"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/api/status")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/api/generate-ddr")
async def generate_ddr(
    inspection_pdf: UploadFile = File(...),
    thermal_pdf: UploadFile = File(...)
):
    for f in [inspection_pdf, thermal_pdf]:
        if not f.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"'{f.filename}' is not a PDF file.")
    
    job_id = str(uuid.uuid4())[:8]
    job_dir = os.path.join(UPLOAD_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    try:
        inspection_path = os.path.join(job_dir, "inspection.pdf")
        thermal_path = os.path.join(job_dir, "thermal.pdf")
        
        with open(inspection_path, "wb") as f:
            content = await inspection_pdf.read()
            f.write(content)
        
        with open(thermal_path, "wb") as f:
            content = await thermal_pdf.read()
            f.write(content)
        print(f"[main] Job {job_id}: PDFs saved")

        inspection_data = extract_pdf_content(inspection_path, "inspection")
        thermal_data = extract_pdf_content(thermal_path, "thermal")
        if not inspection_data["text"] and not thermal_data["text"]:
            raise HTTPException(status_code=400, detail="Both PDFs appear to be empty or unreadable.")
        print(f"[main] Job {job_id}: Extraction complete")

        ddr_structure = generate_ddr_structure(
            inspection_data["text"],
            thermal_data["text"]
        )
        
        if "error" in ddr_structure:
            raise HTTPException(status_code=500, detail="LLM analysis failed. Please try again.")
        print(f"[main] Job {job_id}: LLM analysis complete")

        ddr_structure["observations"] = match_images_to_sections(
            ddr_structure.get("observations", []),
            inspection_data["images"],
            thermal_data["images"]
        )
        print(f"[main] Job {job_id}: Image matching complete")

        output_filename = f"DDR_Report_{job_id}.pdf"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        build_pdf_report(ddr_structure, output_path)
        print(f"[main] Job {job_id}: PDF generated at {output_path}")
        
        return {
            "success": True,
            "job_id": job_id,
            "filename": output_filename,
            "download_url": f"/api/download/{output_filename}"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[main] Job {job_id}: Error — {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(job_dir):
            shutil.rmtree(job_dir, ignore_errors=True)
            
@app.get("/api/download/{filename}")
def download_report(filename: str):
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report not found.")
    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename=filename
    )
    
from fastapi.staticfiles import StaticFiles
import pathlib

frontend_dist = pathlib.Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)