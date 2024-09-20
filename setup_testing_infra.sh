#!/bin/bash

# Check if we're in a git repository
if [ ! -d ".git" ]; then
  echo "Error: Not a git repository. Please ensure you're in the root of your project."
  exit 1
fi

# Define constants for directories and files
TEST_WORKFLOW_DIR=".github/workflows"
TEST_WORKFLOW_FILE="$TEST_WORKFLOW_DIR/test.yml"
TEST_DIR="tests"
REQUIREMENTS_FILE="requirements.txt"
TEST_LOG_DIR="test-results"
GITHUB_ACTIONS_WORKFLOW="test.yml"

echo "Setting up testing infrastructure for FastAPI project..."

# Ensure correct directory structure for GitHub workflows
echo "Ensuring GitHub Actions workflow directory exists..."
mkdir -p "$TEST_WORKFLOW_DIR"

# Create the GitHub Actions workflow to run tests
echo "Creating GitHub Actions test workflow..."
cat > "$TEST_WORKFLOW_FILE" <<EOL
name: Run FastAPI Tests

on:
  push:
    branches:
      - refactor-fastapi
  pull_request:
    branches:
      - refactor-fastapi

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version: ['3.9', '3.10']

    steps:
    - name: Checkout code
      uses: actions/checkout@v2

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run pytest and save output to logs
      run: |
        mkdir -p $TEST_LOG_DIR
        pytest tests/ | tee $TEST_LOG_DIR/test_log.txt
    
    - name: Upload test results
      uses: actions/upload-artifact@v2
      with:
        name: test-logs
        path: $TEST_LOG_DIR/test_log.txt
EOL

# Create the test directory and a sample test
echo "Ensuring test directory exists..."
mkdir -p "$TEST_DIR"

# Create a basic test file
echo "Creating a basic test for FastAPI app..."
cat > "$TEST_DIR/test_app.py" <<EOL
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the FastAPI App"}

# Add more tests for your routes and services here
EOL

# Ensure the requirements.txt file exists with necessary dependencies
echo "Ensuring requirements.txt exists and contains required dependencies..."
if [ ! -f "$REQUIREMENTS_FILE" ]; then
  cat > "$REQUIREMENTS_FILE" <<EOL
fastapi
pytest
httpx
uvicorn
EOL
else
  # Add missing dependencies if necessary
  if ! grep -q 'fastapi' "$REQUIREMENTS_FILE"; then echo "fastapi" >> "$REQUIREMENTS_FILE"; fi
  if ! grep -q 'pytest' "$REQUIREMENTS_FILE"; then echo "pytest" >> "$REQUIREMENTS_FILE"; fi
  if ! grep -q 'httpx' "$REQUIREMENTS_FILE"; then echo "httpx" >> "$REQUIREMENTS_FILE"; fi
  if ! grep -q 'uvicorn' "$REQUIREMENTS_FILE"; then echo "uvicorn" >> "$REQUIREMENTS_FILE"; fi
fi

# Commit and push the changes to the refactor-fastapi branch
echo "Committing and pushing the test infrastructure to the refactor-fastapi branch..."
git add .
git commit -m "Added testing infrastructure for FastAPI app with GitHub Actions workflow"
git push origin refactor-fastapi

echo "Test infrastructure setup complete. You can now check the GitHub Actions workflows for test results."
