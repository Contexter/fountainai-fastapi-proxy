# tests/test_app.py
# Pytest file for testing FastAPI routes using TestClient.

import pytest
from fastapi.testclient import TestClient
from app.main import app  # Import the FastAPI app

client = TestClient(app)

# Test the repo metadata route
def test_repo_metadata():
    response = client.get("/repo/owner/repo")
    assert response.status_code == 200
    assert "forks" in response.json()  # Example response check

def test_commit_history():
    response = client.get("/repo/owner/repo/commits")
    assert response.status_code == 200

def test_repo_branches():
    response = client.get("/repo/owner/repo/branches")
    assert response.status_code == 200

def test_traffic_views():
    response = client.get("/traffic/repo/owner/repo/views")
    assert response.status_code == 200

def test_traffic_clones():
    response = client.get("/traffic/repo/owner/repo/clones")
    assert response.status_code == 200

def test_push_logs():
    response = client.get("/logs/push")
    assert response.status_code == 200
    assert response.json() == {"message": "Logs have been successfully committed and pushed to GitHub."}
