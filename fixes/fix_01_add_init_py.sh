#!/bin/bash

# Shell script to add the missing __init__.py file to the app directory and commit/push changes.
# This script follows modular design principles, idempotency, and proper commenting.

# Function to check if the app directory exists
check_app_directory() {
    if [ ! -d "../app" ]; then
        echo "Error: 'app' directory does not exist. Please ensure you're in the correct project directory."
        exit 1
    fi
}

# Function to add __init__.py to the app directory if it doesn't already exist (idempotent)
add_init_py() {
    if [ ! -f "../app/__init__.py" ]; then
        echo "Creating __init__.py in the app directory..."
        echo "# This file makes the 'app' directory a Python module" > ../app/__init__.py
        echo "__init__.py created successfully."
    else
        echo "__init__.py already exists in the app directory."
    fi
}

# Function to check if git is initialized in the parent directory
check_git_repository() {
    if [ ! -d "../.git" ]; then
        echo "Error: No git repository found in the parent directory. Please ensure you're in the correct project directory."
        exit 1
    fi
}

# Function to commit and push changes to the test-deployment-branch
commit_and_push_changes() {
    # Navigate to the parent directory where the .git/ folder is located
    cd ..

    # Stage the __init__.py file
    git add app/__init__.py
    
    # Commit the changes
    commit_message="Add missing __init__.py to app directory to fix module import in tests"
    echo "Committing the changes with message: '$commit_message'"
    git commit -m "$commit_message"
    
    # Push the changes to the test-deployment-branch
    branch_name="test-deployment-branch"
    echo "Pushing changes to the $branch_name..."
    git push origin "$branch_name"

    echo "Fix applied and changes have been pushed to the $branch_name."

    # Return back to the fixes/ directory after committing and pushing
    cd fixes
}

# Main script execution starts here

# Step 1: Check if the app directory exists
check_app_directory

# Step 2: Add __init__.py to the app directory (idempotent)
add_init_py

# Step 3: Check if git is initialized in the parent directory
check_git_repository

# Step 4: Commit and push changes
commit_and_push_changes
