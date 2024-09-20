# app/main.py
# Main entry point for the FastAPI app, now modularized with routers.

from fastapi import FastAPI
from routers import repo, traffic, logs

app = FastAPI(
    title="FountainAI GitHub Proxy API",
    description="A modular API to interact with GitHub repositories, enabling operations like metadata retrieval, traffic statistics, and log handling.",
    version="1.0.0"
)

# Include routers
app.include_router(repo.router)
app.include_router(traffic.router)
app.include_router(logs.router)

# Additional routers can be included as needed
