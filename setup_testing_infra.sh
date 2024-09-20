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

echo "Setting up testing infrastructure for FastAPI project..."

# Ensure correct directory structure for GitHub workflows
echo "Ensuring GitHub Actions workflow directory exists..."
mkdir -p "$TEST_WORKFLOW_DIR"

# Create the GitHub Actions workflow to run tests
echo "Creating GitHub Actions test workflow..."
cat > "$TEST_WORKFLOW_FILE" << 'EOL'
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
        mkdir -p test-results
        pytest tests/ | tee test-results/test_log.txt
    
    - name: Upload test results
      uses: actions/upload-artifact@v2
      with:
        name: test-logs
        path: test-results/test_log.txt
EOL

# The rest of the script follows as before
