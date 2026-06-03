from fastapi import FastAPI
from pydantic import BaseModel
from algorithms.kmp import kmp_steps

app = FastAPI()

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