import json
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from algorithms.kmp import kmp_steps, kmp_contains
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class KMPRequest(BaseModel):
    text: str
    pattern: str

@app.get("/")
def root():
    return {"message": "Algorithm Visualizer API is running"}

@app.post("/kmp")
def run_kmp(request: KMPRequest):
    return {
        "steps": kmp_steps(request.text, request.pattern)
    }

app.mount("/images", StaticFiles(directory="static/images"), name="images")

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