# uvicorn app.main:app --reload
from fastapi import FastAPI

app = FastAPI(title="공고그대로 API", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}
