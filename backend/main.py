from fastapi import FastAPI
from pydantic import BaseModel
from algorithms.kmp import kmp_steps
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