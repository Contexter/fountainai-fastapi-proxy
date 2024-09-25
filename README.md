
### **Comprehensive Guide: Building FastAPI Proxies the FountainAI Way**

#### **Table of Contents**:
1. [Introduction](#introduction)
2. [Project Structure for FastAPI Proxy](#project-structure-for-fastapi-proxy)
3. [Modular Route Design](#modular-route-design)
4. [Service Layer for External API Interaction](#service-layer-for-external-api-interaction)
5. [OpenAPI Documentation](#openapi-documentation)
6. [Error Handling](#error-handling)
7. [Dockerization of the FastAPI Proxy](#dockerization-of-the-fastapi-proxy)
8. [FountainAI Shell Scripting for Proxy Automation](#fountainai-shell-scripting-for-proxy-automation)
9. [Deploying with GitHub Actions](#deploying-with-github-actions)
10. [Using GitHub Container Registry with GitHub CLI](#using-github-container-registry-with-github-cli)
11. [Testing and Maintenance](#testing-and-maintenance)
12. [Conclusion](#conclusion)
13. [Appendix: GHCR Workflow Focused GPT Prompt](#appendix-ghcr-workflow-focused-gpt-prompt)

---

### **1. Introduction**

In this guide, we’ll walk through the steps of building a **FastAPI proxy** following **FountainAI’s best practices** for **modularity**, **Dockerization**, and **automation**. FastAPI is a great choice for proxy services because it’s fast, easy to use, and automatically generates OpenAPI documentation. By leveraging the **FountainAI way** of shell scripting, we’ll automate key parts of deployment, ensuring consistent, idempotent operations.

Additionally, we will use **GitHub Container Registry (GHCR)** for storing Docker images and administer the registry using the **GitHub CLI (gh)** for managing permissions, pushing/pulling images, and versioning.

---

### **2. Project Structure for FastAPI Proxy**

A well-organized project structure is essential for maintainability, scalability, and composability. Following the **FountainAI philosophy**, we’ll split the project into **small, manageable components**.

---

### **3. Modular Route Design**

Following **FountainAI’s composability principles**, we keep routes modular, meaning each API domain (e.g., **GitHub Issues**, **Pull Requests**) gets its own route file. This approach avoids bloating a single route file and allows each part of the proxy to grow independently.

---

### **4. Service Layer for External API Interaction**

The service layer handles the actual interaction with external APIs (e.g., GitHub’s REST or GraphQL APIs). This separation of concerns ensures that routes are only responsible for handling HTTP requests/responses, while the service layer deals with business logic.

---

### **5. OpenAPI Documentation**

FastAPI automatically generates **OpenAPI documentation** for each route. However, following **FountainAI norms**, we ensure that every route has a:
- **Custom `operation_id`** (e.g., `list_github_issues`).
- **Short, clear `summary`** (one-liner describing the route).
- **Concise `description`** (maximum of 300 characters).

This ensures the API documentation is both **informative** and **concise**.

---

### **6. Error Handling**

All errors should be handled consistently, providing clear error messages and appropriate HTTP status codes. Use FastAPI’s `HTTPException` for error handling.

---

### **7. Dockerization of the FastAPI Proxy**

By Dockerizing the FastAPI proxy, we ensure portability and ease of deployment across environments. Here is an example **Dockerfile** to build the FastAPI proxy:

```Dockerfile
# Use the official Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY . .

# Expose the FastAPI default port
EXPOSE 8000

# Start the FastAPI app with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### **8. FountainAI Shell Scripting for Proxy Automation**

Following **Chapter 7 of the FountainAI Book**, we’ll use **modular shell scripts** for automating repetitive tasks like building Docker images and running containers.

#### **Example Script: `fountainai_docker_deploy.sh`**

```bash
#!/bin/bash
# A FountainAI-style script for Docker deployment of FastAPI proxy

# Exit on error
set -e

# Function to build Docker image
build_docker_image() {
    echo "Building Docker image..."
    docker build -t fastapi-proxy .
}

# Function to run Docker container
run_docker_container() {
    local container_name="fastapi-proxy"
    if [ "$(docker ps -q -f name=$container_name)" ]; then
        echo "Container $container_name is already running."
    else
        echo "Running Docker container..."
        docker run -d -p 8000:8000 --name $container_name fastapi-proxy
    fi
}

# Main deployment function
deploy() {
    build_docker_image
    run_docker_container
    echo "Deployment complete!"
}

# Execute the deploy function
deploy
```

---

### **9. Deploying with GitHub Actions**

Automate the deployment process using **GitHub Actions**. This can trigger the `fountainai_docker_deploy.sh` script whenever changes are pushed to the main branch.

#### **GitHub Actions Workflow**:

```yaml
name: Deploy FastAPI Proxy

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v2

      - name: Build and Deploy
        run: ./scripts/fountainai_docker_deploy.sh
```

---

### **10. Using GitHub Container Registry with GitHub CLI**

We will store Docker images in **GitHub Container Registry (GHCR)**, and use **GitHub CLI (gh)** to administer the registry and manage permissions, tags, and image versions.

#### **Pushing an Image to GHCR**
1. Authenticate with GHCR using GitHub CLI:
   ```bash
   echo $GHCR_PAT | docker login ghcr.io -u USERNAME --password-stdin
   ```

2. Tag the image:
   ```bash
   docker tag fastapi-proxy ghcr.io/USERNAME/fastapi-proxy:latest
   ```

3. Push the image:
   ```bash
   docker push ghcr.io/USERNAME/fastapi-proxy:latest
   ```

#### **Managing GHCR with GitHub CLI**
Using **`gh`**, you can manage container images and versions.

- **List Container Images**:
  ```bash
  gh api /user/packages/container
  ```

- **View Container Versions**:
  ```bash
  gh api /user/packages/container/fastapi-proxy/versions
  ```

- **Delete a Container Version**:
  ```bash
  gh api --method DELETE /user/packages/container/fastapi-proxy/versions/VERSION_ID
  ```

---

### **11. Testing and Maintenance**

Testing should focus on:
- **Unit tests** for the service layer, mocking external API calls.
- **Integration tests** for the routes using FastAPI’s `TestClient`.

Ensure tests are run in the CI pipeline to maintain system integrity.

---

### **12. Conclusion**

By leveraging **FastAPI’s speed** and **OpenAPI capabilities**, combined with **FountainAI’s scripting and automation principles**, and storing Docker images in **GitHub Container Registry**, we’ve created a **modular**, **Dockerized**, and **automated proxy** system. This approach ensures **consistency**, **portability**, and **scalability** for API proxy development, making it easy to manage and deploy in real-world environments.

---

### **13. Appendix: GHCR Workflow Focused GPT Prompt**

Here’s a **GHCR workflow-focused prompt** that you can use to guide a GPT-powered assistant through the process of managing Docker images with GitHub Container Registry (GHCR).

**Prompt Title:**  
"Guide me through the full GitHub Container Registry (GHCR) workflow for Docker image management."

**Prompt Text:**  
"Please provide a detailed guide for managing Docker images with GitHub Container Registry (GHCR). The guide should cover the following steps:

1. **Setting up GHCR:**  
   - How to authenticate with GHCR using Docker CLI and GitHub CLI.
   - How to create a Personal Access Token (PAT) for GHCR and set up authentication.

2. **Building and Tagging Docker Images:**  
   - Instructions for building a Docker image from a project.
   - How to tag the image for GHCR with the correct format.

3. **Pushing Docker Images to GHCR:**  
   - The correct steps to push a tagged Docker image to GHCR.
   - How to handle multiple image versions and tags.

4. **Pulling Images from GHCR:**  
   - How to pull images from GHCR for use on other machines or in deployment.

5. **Managing Images and Versions in GHCR:**  
   - Using GitHub CLI (gh) to list container images and view versions.
   - How to delete specific image versions or update permissions for GHCR repositories.
   -

 How to automate GHCR workflows with GitHub Actions to build, tag, and push Docker images during CI/CD.

6. **Security and Permissions in GHCR:**  
   - How to configure permissions for accessing private images in GHCR.
   - Recommendations for securing access to images and managing permissions using GitHub Teams or Organizations.

Please format the guide with code examples and practical instructions, with clear explanations for each step. Emphasize using GitHub CLI (gh) for image management, along with Docker CLI."
