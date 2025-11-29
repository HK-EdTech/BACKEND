from fastapi import FastAPI

app = FastAPI(
    title="My Awesome API",
    description="Deployed with GitHub Actions + EC2 + Docker",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
def health():
    return {"status": "healthy"}