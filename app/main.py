from fastapi import FastAPI
from app.routers import logs, repo, traffic

app = FastAPI(
    title="FountainAI FastAPI Proxy",
    description="A FastAPI-based proxy to interact with GitHub's repository, traffic, and logging features.",
    version="1.0.0",
    contact={
        "name": "FountainAI Support",
        "url": "https://fountainai.example.com",
        "email": "support@fountainai.example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Include routers
app.include_router(logs.router)
app.include_router(repo.router)
app.include_router(traffic.router)

@app.get("/", summary="Root endpoint")
def read_root():
    """
    Root endpoint for the FountainAI FastAPI Proxy.
    
    Returns a welcome message.
    """
    return {"message": "Welcome to the FastAPI App"}
