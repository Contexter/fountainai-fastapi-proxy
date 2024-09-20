from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the FastAPI App"}

def test_push_logs():
    response = client.get("/logs/push-logs")
    assert response.status_code == 200

def test_get_repo_info():
    response = client.get("/repo/{owner}/{repo}")
    assert response.status_code == 200

# Add more tests as required
