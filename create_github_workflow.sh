#!/bin/bash

# Function to check if the script is being run from the correct directory
check_directory() {
    if [ ! -d ".git" ]; then
        echo "This script must be run from the root of a Git repository."
        exit 1
    fi
}

# Function to create the .github/workflows directory if it doesn't exist
create_workflow_directory() {
    local workflow_dir=".github/workflows"
    
    if [ ! -d "$workflow_dir" ]; then
        mkdir -p "$workflow_dir"
        echo "Created workflow directory: $workflow_dir"
    else
        echo "Workflow directory already exists: $workflow_dir"
    fi
}

# Function to create the GitHub Actions workflow file
create_github_workflow() {
    local workflow_file=".github/workflows/deploy.yml"
    
    # Check if the workflow file already exists
    if [ ! -f "$workflow_file" ]; then
        echo "Creating GitHub Actions workflow: $workflow_file"
        cat <<EOL > "$workflow_file"
name: Deploy to Lightsail

on:
  push:
    branches:
      - main  # Trigger when changes are pushed to the main branch
  workflow_dispatch:  # Allow manual trigger from the GitHub Actions tab

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout repository
      uses: actions/checkout@v2

    - name: Pull repo changes and restart FastAPI and NGINX on Lightsail
      run: |
        ssh -o StrictHostKeyChecking=no ubuntu@\${{ secrets.LIGHTSAIL_SERVER_IP }} << EOF
          cd ~/fountainai-fastapi-proxy
          git pull origin main
          sudo systemctl restart fastapi
          sudo systemctl restart nginx
          sudo systemctl status fastapi
          sudo systemctl status nginx
        EOF
EOL
    else
        echo "Workflow file already exists: $workflow_file"
    fi
}

# Ensure the script runs from the project root (where .git exists)
check_directory

# Ensure the script is idempotent by checking if workflow file already exists
create_workflow_directory
create_github_workflow
