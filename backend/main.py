import json
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from algorithms.kmp import kmp_steps, kmp_contains
from fastapi.middleware.cors import CORSMiddleware
import subprocess
from fastapi.responses import FileResponse
from pathlib import Path
from PIL import Image
import uuid

IMAGE_DIR = Path("static/images")
CONVERTED_DIR = Path("static/converted")
CONVERTED_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_OUTPUTS = {"png", "jpg", "jpeg", "webp", "ico", "pdf"}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://interactive-algorithm-visualizer-im.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class KMPRequest(BaseModel):
    text: str
    pattern: str

class OpenFileRequest(BaseModel):
    filepath: str

class ConvertImageRequest(BaseModel):
    filename: str
    output_format: str

@app.get("/")
def root():
    return {"message": "Algorithm Visualizer API is running"}

@app.post("/kmp")
def run_kmp(request: KMPRequest):
    return {
        "steps": kmp_steps(request.text, request.pattern)
    }

app.mount("/images", StaticFiles(directory="static/images"), name="images")

@app.get("/preview/{filename}")
def preview_image(filename: str):
    file_path = Path("static/images") / filename

    return FileResponse(
        file_path,
        media_type="image/webp" if filename.lower().endswith(".webp") else None,
        filename=filename,
        content_disposition_type="inline"
    )

@app.get("/search")
def search_images(q: str):
    with open("data/images.json", "r", encoding="utf-8") as file:
        images = json.load(file)

    results = []

    for image in images:
        searchable_text = " ".join([
            image["filename"],
            " ".join(image["tags"]),
            image["description"]
        ])

        if kmp_contains(searchable_text, q):
            results.append(image)

    return {
        "query": q,
        "count": len(results),
        "results": results
    }

@app.post("/open-file")
def open_file(request: OpenFileRequest):

    subprocess.run(
        ["explorer", f"/select,{request.filepath}"]
    )

    return {"status": "success"}

@app.post("/convert-image")
def convert_image(request: ConvertImageRequest):
    output_format = request.output_format.lower()

    if output_format not in SUPPORTED_OUTPUTS:
        return {"error": "Unsupported output format"}

    input_path = IMAGE_DIR / request.filename

    if not input_path.exists():
        return {"error": "File does not exist"}

    image = Image.open(input_path)

    # Convert transparency safely for JPG/PDF
    if output_format in {"jpg", "jpeg", "pdf"}:
        image = image.convert("RGB")

    output_filename = f"{input_path.stem}_{uuid.uuid4().hex[:8]}.{output_format}"
    output_path = CONVERTED_DIR / output_filename

    save_format = output_format.upper()

    if output_format == "jpg":
        save_format = "JPEG"

    image.save(output_path, save_format)

    return {
        "status": "success",
        "filename": output_filename,
        "download_url": f"/converted/{output_filename}"
    }

app.mount("/converted", StaticFiles(directory="static/converted"), name="converted")