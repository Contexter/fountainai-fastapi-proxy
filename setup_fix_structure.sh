#!/bin/bash

# Create the fixes directory if it doesn't exist
if [ ! -d "fixes" ]; then
    echo "Creating fixes directory..."
    mkdir fixes
else
    echo "fixes directory already exists."
fi

# Create the fix script to add __init__.py in the app directory
fix_script="fixes/fix_01_add_init_py.sh"

# Write the fix script that creates the __init__.py file
cat <<EOL > $fix_script
#!/bin/bash

# This script adds the missing __init__.py file to the app directory to fix the module import issue.

# Check if the app directory exists
if [ ! -d "app" ]; then
  echo "Error: 'app' directory does not exist. Please ensure you're in the correct project directory."
  exit 1
fi

# Create the __init__.py file in the app directory if it doesn't exist
if [ ! -f "app/__init__.py" ]; then
  echo "Creating __init__.py in the app directory..."
  touch app/__init__.py
  echo "# This file makes the 'app' directory a Python module" > app/__init__.py
else
  echo "__init__.py already exists in the app directory."
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
  echo "Error: No git repository found. Please ensure you're in the correct project directory."
  exit 1
fi

# Add the __init__.py file to the staging area
git add app/__init__.py

# Commit the changes
commit_message="Add missing __init__.py to app directory to fix module import in tests"
echo "Committing the changes with message: '\$commit_message'"
git commit -m "\$commit_message"

# Push the changes to the test-deployment-branch
branch_name="test-deployment-branch"
echo "Pushing changes to the \$branch_name..."
git push origin "\$branch_name"

echo "Fix applied and changes have been pushed to the \$branch_name."
EOL

# Make the script executable
chmod +x $fix_script

echo "Fix script created at: $fix_script"

# Reminder: Add comment to the main.py file to ensure developers follow the plan

main_file="app/main.py"
if [ -f "$main_file" ]; then
    # Add a reminder comment at the beginning of main.py if it doesn't already exist
    if ! grep -q "Reminder: Follow repository plan" "$main_file"; then
        echo "Adding reminder comment to $main_file..."
        sed -i '1i\
# Reminder: Follow the repository plan. Ensure all fixes and patches are handled via the fixes/ directory. Use proper commit messages and track all changes using fix scripts.\
' "$main_file"
    else
        echo "Reminder comment already exists in $main_file."
    fi
else
    echo "Error: $main_file does not exist. Please ensure you're in the correct project directory."
fi

echo "Repository structure updated. Fix script added and reminder comment inserted."
