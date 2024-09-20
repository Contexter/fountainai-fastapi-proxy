#!/bin/bash

# Comprehensive shell script to refactor an existing FastAPI app into a modular structure,
# set up tests using Pytest, and configure GitHub Actions for automated testing.

# Function to create a new branch using GitHub CLI
create_test_branch() {
    echo "Creating test deployment branch..."
    
    # Check if gh (GitHub CLI) is installed
    if ! command -v gh &> /dev/null; then
        echo "Error: gh (GitHub CLI) is not installed. Please install it and try again."
        exit 1
    fi

    # Create the branch using gh
    git checkout -b test-deployment-branch
    git push origin test-deployment-branch
    echo "Test deployment branch created and pushed to GitHub."
}

# Function to create the new directory structure
create_directories() {
    echo "Creating necessary directories..."
    if [ ! -d "app/routers" ]; then
        mkdir -p app/routers
    fi
    if [ ! -d "app/services" ]; then
        mkdir -p app/services
    fi
    if [ ! -d "app/utils" ]; then
        mkdir -p app/utils
    fi
    if [ ! -d "tests" ]; then
        mkdir -p tests
    fi
    echo "Directories created: app/routers, app/services, app/utils, tests."
}

# Function to create the router files with modular route logic
create_router_files() {
    echo "Creating router files with modular logic..."

    # Repo router
    cat <<EOL > app/routers/repo.py
# app/routers/repo.py
# Router file handling repository-related operations (commits, branches, metadata).

from fastapi import APIRouter, HTTPException, Path
from services.github_service import github_request

router = APIRouter(
    prefix="/repo",
    tags=["repository"],
    responses={404: {"description": "Not found"}}
)

@router.get("/{owner}/{repo}/file/{path:path}/lines", summary="Retrieve file content by line range",
            description="Get a specific range of lines from a large file in the repository.")
def get_lines_by_range(owner: str, repo: str, path: str, start_line: int = 0, end_line: int = None):
    # Placeholder for logic
    pass

@router.get("/{owner}/{repo}", summary="Retrieve repository metadata",
            description="Retrieve metadata about the repository, including stars, forks, watchers, and more.")
def get_repo_info(owner: str = Path(..., description="GitHub username or organization"),
                  repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}"
    return github_request(endpoint)

@router.get("/{owner}/{repo}/commits", summary="Retrieve commit history",
            description="Get a list of commits in the repository.")
def get_commit_history(owner: str = Path(..., description="GitHub username or organization"),
                       repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/commits"
    return github_request(endpoint)

@router.get("/{owner}/{repo}/branches", summary="List repository branches",
            description="Retrieve a list of branches in the repository.")
def list_branches(owner: str = Path(..., description="GitHub username or organization"),
                  repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/branches"
    return github_request(endpoint)
EOL

    # Traffic router
    cat <<EOL > app/routers/traffic.py
# app/routers/traffic.py
# Router file handling traffic-related operations (views and clones).

from fastapi import APIRouter, Path
from services.github_service import github_request

router = APIRouter(
    prefix="/traffic",
    tags=["traffic"],
    responses={404: {"description": "Not found"}}
)

@router.get("/repo/{owner}/{repo}/views", summary="Retrieve repository traffic views",
            description="Get the number of views for the repository over a specified time period.")
def get_repo_traffic_views(owner: str = Path(..., description="GitHub username or organization"),
                           repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/traffic/views"
    return github_request(endpoint)

@router.get("/repo/{owner}/{repo}/clones", summary="Retrieve repository traffic clones",
            description="Get the number of times the repository has been cloned over a specified time period.")
def get_repo_traffic_clones(owner: str = Path(..., description="GitHub username or organization"),
                            repo: str = Path(..., description="Repository name")):
    endpoint = f"repos/{owner}/{repo}/traffic/clones"
    return github_request(endpoint)
EOL

    # Logs router
    cat <<EOL > app/routers/logs.py
# app/routers/logs.py
# Router file handling log-related operations (committing and pushing logs to GitHub).

from fastapi import APIRouter, HTTPException
from services.logging_service import commit_and_push_logs

router = APIRouter(
    prefix="/logs",
    tags=["logs"],
    responses={404: {"description": "Not found"}}
)

@router.get("/push", summary="Push logs to GitHub",
            description="Triggers a log commit and pushes it to GitHub.")
async def push_logs():
    try:
        message = commit_and_push_logs()
        return {"message": message}
    except HTTPException as e:
        return {"error": e.detail}
EOL

    echo "Router files created successfully."
}

# Function to create service files (GitHub service and logging service)
create_service_files() {
    echo "Creating service files..."

    # GitHub service
    cat <<EOL > app/services/github_service.py
# app/services/github_service.py
# Service file for handling GitHub API interactions.

import requests
import logging
from fastapi import HTTPException

GITHUB_API_URL = "https://api.github.com"

def github_request(endpoint: str, params=None, headers=None):
    url = f"\${GITHUB_API_URL}/\${endpoint}"
    if headers is None:
        headers = {"Accept": "application/vnd.github.v3+json"}
    
    logging.info(f"Making GitHub API request to: {url}")
    response = requests.get(url, headers=headers, params=params)

    if response.status_code not in [200, 206]:
        logging.error(f"GitHub API error: {response.status_code}, {response.text}")
        raise HTTPException(status_code=response.status_code, detail=response.json())

    return response.json()
EOL

    # Logging service
    cat <<EOL > app/services/logging_service.py
# app/services/logging_service.py
# Service file for committing and pushing logs to GitHub.

import os
from datetime import datetime
from fastapi import HTTPException

def commit_and_push_logs():
    try:
        repo_path = os.getcwd()
        if not os.path.exists(os.path.join(repo_path, '.git')):
            raise Exception("Current directory is not a Git repository.")

        commit_message = f"Log update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        os.system('git add app.log')
        os.system(f'git commit -m "\${commit_message}"')
        os.system('git push origin main')

        return "Logs have been successfully committed and pushed to GitHub."
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error committing logs: {str(e)}")
EOL

    echo "Service files created successfully."
}

# Function to create utility files (e.g., file processing)
create_utility_files() {
    echo "Creating utility files..."

    # File utility for processing chunks
    cat <<EOL > app/utils/file_utils.py
# app/utils/file_utils.py
# Utility file for processing file content in chunks.

def process_chunk(chunk, carry_over):
    content = carry_over + chunk.decode("utf-8")
    lines = content.splitlines(keepends=True)

    if not content.endswith("\\n"):
        carry_over = lines.pop()
    else:
        carry_over = ""

    return lines, carry_over
EOL

    echo "Utility files created successfully."
}

# Function to create the main.py file with router imports
refactor_main_py() {
    echo "Refactoring main.py..."

    # Refactor main.py to include routers
    cat <<EOL > app/main.py
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
EOL

    echo "main.py refactored successfully."
}

# Function to create test files using pytest and HTTPX
create_test_files() {
    echo "Creating test files..."

    # Create test_app.py file for route testing
    cat <<EOL > tests/test_app.py
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
EOL

    echo "Test files created successfully."
}

# Function to create a GitHub Actions workflow file
create_github_action() {
    echo "Creating GitHub Actions workflow for automated testing..."

    # Create the GitHub Actions workflow file
    mkdir -p .github/workflows
    cat <<EOL > .github/workflows/test.yml
# .github/workflows/test.yml
# GitHub Actions workflow to run tests on refactored app.

name: Run Tests on Refactored App

# Run the workflow on push to the test-deployment-branch
on:
  push:
    branches:
      - test-deployment-branch

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout the code
      uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.x'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install fastapi pytest httpx uvicorn

    - name: Run tests
      run: |
        pytest tests/
EOL

    echo "GitHub Actions workflow created successfully."
}

# Execute all the functions to set up and refactor the app
create_test_branch
create_directories
create_router_files
create_service_files
create_utility_files
refactor_main_py
create_test_files
create_github_action

echo "Refactoring and setup complete! Push changes to GitHub and monitor test results."
