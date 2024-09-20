#!/bin/bash

# Ensure we're in a git repository
if [ ! -d ".git" ]; then
  echo "Error: Not a git repository. Please ensure you're in the root of your project."
  exit 1
fi

echo "Preparing to refactor FastAPI project with OpenAPI optimizations..."

# Clean old branches
echo "Cleaning up old branches..."
git branch -D refactor-fastapi 2>/dev/null
git push origin --delete refactor-fastapi 2>/dev/null
echo "Old branches cleaned."

# Switch to main and pull latest
echo "Switching to main branch and pulling latest code..."
git checkout main
git pull origin main
echo "Main branch updated."

# Create a new branch for refactoring
echo "Creating new branch 'refactor-fastapi'..."
git checkout -b refactor-fastapi

# Ensure correct project structure
echo "Ensuring modular structure for the FastAPI app..."
mkdir -p app/routers app/services app/utils tests

# Add __init__.py files to ensure Python treats these as modules
touch app/__init__.py app/routers/__init__.py app/services/__init__.py app/utils/__init__.py tests/__init__.py

# Step 1: Move existing main.py logic to the new modular structure
if [ ! -f app/main.py ]; then
  echo "Moving 'main.py' to 'app/main.py'..."
  mv main.py app/main.py
fi

# Step 2: Create modularized routers (logs, repo, traffic) while keeping OpenAPI integration intact

# logs.py
echo "Creating 'logs.py' router with OpenAPI optimizations..."
cat > app/routers/logs.py <<EOL
from fastapi import APIRouter
from app.services.github_service import push_logs_to_github

router = APIRouter(
    prefix="/logs",
    tags=["Logs"],
    responses={404: {"description": "Not found"}},
)

@router.get("/push-logs", summary="Push logs to GitHub")
async def push_logs():
    """
    Push application logs to the configured GitHub repository.
    
    This endpoint triggers log collection and pushes them to GitHub for auditing.
    """
    return push_logs_to_github()
EOL

# repo.py
echo "Creating 'repo.py' router with OpenAPI optimizations..."
cat > app/routers/repo.py <<EOL
from fastapi import APIRouter
from app.services.github_service import (
    get_file_lines,
    get_repo_info,
    list_repo_contents,
    get_commit_history,
    list_pull_requests,
    list_issues,
    list_branches,
)

router = APIRouter(
    prefix="/repo",
    tags=["Repository"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{owner}/{repo}/file/{path:path}/lines", summary="Retrieve file lines from repo")
async def get_file(owner: str, repo: str, path: str):
    """
    Retrieve specific lines from a file within a repository.
    
    - **owner**: The repository owner.
    - **repo**: The repository name.
    - **path**: The file path in the repository.
    """
    return get_file_lines(owner, repo, path)

@router.get("/{owner}/{repo}", summary="Get repository info")
async def get_repository(owner: str, repo: str):
    """
    Fetch detailed information about a repository.
    """
    return get_repo_info(owner, repo)

@router.get("/{owner}/{repo}/contents", summary="List repository contents")
async def get_contents(owner: str, repo: str):
    """
    List all files and directories in the repository.
    """
    return list_repo_contents(owner, repo)

@router.get("/{owner}/{repo}/commits", summary="Get repository commit history")
async def get_commits(owner: str, repo: str):
    """
    Fetch the commit history of the repository.
    """
    return get_commit_history(owner, repo)

@router.get("/{owner}/{repo}/pulls", summary="List pull requests")
async def get_pull_requests(owner: str, repo: str):
    """
    Retrieve the list of pull requests for the repository.
    """
    return list_pull_requests(owner, repo)

@router.get("/{owner}/{repo}/issues", summary="List repository issues")
async def get_issues(owner: str, repo: str):
    """
    Retrieve the list of issues for the repository.
    """
    return list_issues(owner, repo)

@router.get("/{owner}/{repo}/branches", summary="List branches")
async def get_branches(owner: str, repo: str):
    """
    List all branches in the repository.
    """
    return list_branches(owner, repo)
EOL

# traffic.py
echo "Creating 'traffic.py' router with OpenAPI optimizations..."
cat > app/routers/traffic.py <<EOL
from fastapi import APIRouter
from app.services.github_service import get_traffic_views, get_traffic_clones

router = APIRouter(
    prefix="/traffic",
    tags=["Traffic"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{owner}/{repo}/views", summary="Get traffic views")
async def get_views(owner: str, repo: str):
    """
    Get the number of views for a repository over a specific time period.
    """
    return get_traffic_views(owner, repo)

@router.get("/{owner}/{repo}/clones", summary="Get traffic clones")
async def get_clones(owner: str, repo: str):
    """
    Get the number of times the repository has been cloned.
    """
    return get_traffic_clones(owner, repo)
EOL

# Step 3: Update main.py
echo "Updating 'app/main.py' to include routers and OpenAPI configuration..."
cat > app/main.py <<EOL
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
EOL

# Step 4: Update tests/test_app.py to ensure coverage for new endpoints
echo "Updating 'tests/test_app.py' with tests for modular routers..."
cat > tests/test_app.py <<EOL
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
EOL

# Step 5: Commit changes
echo "Committing changes..."
git add .
git commit -m "Refactored FastAPI app with OpenAPI optimizations and modular structure."

# Step 6: Push the refactor-fastapi branch to remote
echo "Pushing refactored branch to remote repository..."
git push origin refactor-fastapi

echo "Refactoring complete! The branch 'refactor-fastapi' has been pushed."
