#!/bin/bash

# This script adds PYTHONPATH configuration to the GitHub Actions workflow
# to fix the 'ModuleNotFoundError' by ensuring the app directory is in the Python path.

# Function to check if GitHub Actions workflow file exists
check_workflow_file() {
    if [ ! -f "../.github/workflows/test.yml" ]; then
        echo "Error: GitHub Actions workflow file not found."
        exit 1
    fi
}

# Function to add PYTHONPATH configuration to the workflow file if not already added
add_pythonpath_to_workflow() {
    workflow_file="../.github/workflows/test.yml"

    # Check if PYTHONPATH is already set
    if grep -q "export PYTHONPATH" "$workflow_file"; then
        echo "PYTHONPATH is already configured in the workflow file."
    else
        # Add PYTHONPATH setup before running tests
        echo "Adding PYTHONPATH configuration to the workflow file..."
        # Safely append the export command before the "Run Tests" section
        sed -i '' '/- name: Run Tests/i \
        - name: Set PYTHONPATH\n      run: export PYTHONPATH=$PYTHONPATH:$(pwd)\n' "$workflow_file"
        
        echo "PYTHONPATH configuration added successfully."
    fi
}

# Function to commit and push changes
commit_and_push_changes() {
    # Navigate to the project root where .git/ is located
    cd ..

    # Stage the workflow file changes
    git add .github/workflows/test.yml

    # Commit the changes if any were staged
    if git diff-index --quiet HEAD --; then
        echo "No changes to commit."
    else
        commit_message="Add PYTHONPATH configuration to GitHub Actions workflow to fix ModuleNotFoundError"
        echo "Committing the changes with message: '$commit_message'"
        git commit -m "$commit_message"
    fi

    # Push the changes to the test-deployment-branch
    branch_name="test-deployment-branch"
    echo "Pushing changes to the $branch_name..."
    git push origin "$branch_name"

    echo "Fix applied and changes have been pushed to the $branch_name."

    # Return to the fixes/ directory after committing and pushing
    cd fixes
}

# Main script execution starts here

# Step 1: Check if the workflow file exists
check_workflow_file

# Step 2: Add PYTHONPATH configuration to the GitHub Actions workflow
add_pythonpath_to_workflow

# Step 3: Commit and push changes
commit_and_push_changes
