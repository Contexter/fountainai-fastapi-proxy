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

# Function to create or overwrite the GitHub Actions workflow file
create_github_workflow() {
    local workflow_file=".github/workflows/deploy.yml"
    
    # Check if the workflow file already exists
    if [ -f "$workflow_file" ]; then
        # Ask for confirmation to overwrite the file
        read -p "The workflow file $workflow_file already exists. Do you want to overwrite it? (y/n): " confirm
        if [[ "$confirm" != "y" ]]; then
            echo "Skipping workflow creation."
            return
        fi
    fi
    
    # Create or overwrite the workflow file
    echo "Creating (or overwriting) GitHub Actions workflow: $workflow_file"
    cat <<EOL > "$workflow_file"
name: Manual Deployment

on:
  workflow_dispatch:  # Allow manual trigger from the GitHub Actions tab

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - name: Check if actor is repository owner
      run: |
        if [[ "\${{ github.actor }}" != "\${{ github.repository_owner }}" ]]; then
          echo "You are not authorized to run this workflow."
          exit 1
        fi
      # This step runs only if the person triggering is the repository owner

    - name: Checkout code
      uses: actions/checkout@v2

    - name: Deploy to Lightsail
      run: |
        ssh -o StrictHostKeyChecking=no ubuntu@\${{ secrets.LIGHTSAIL_SERVER_IP }} << EOF
          cd ~/fountainai-fastapi-proxy
          git pull origin main
          sudo systemctl restart fastapi
          sudo systemctl restart nginx
        EOF
EOL
    echo "Workflow created (or overwritten): $workflow_file"
}

# Ensure the script runs from the project root (where .git exists)
check_directory

# Ensure the script is idempotent by checking if workflow file already exists
create_workflow_directory
create_github_workflow
