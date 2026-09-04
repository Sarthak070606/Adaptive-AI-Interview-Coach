
from fastapi import FastAPI

app = FastAPI(title="Adaptive AI Interview Coach API")

@app.get("/")
def root():
    return {"message": "Adaptive AI Interview Coach API is running"}
