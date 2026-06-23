# Dockerfile for CodeChef MCP Server
FROM python:3.11-slim

# Install system dependencies, including curl and docker-cli
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    lsb-release \
    ca-certificates \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update && apt-get install -y --no-install-recommends \
    docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy requirements file and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and chromium browser dependencies
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application source code
COPY app/ app/
COPY run_server.py .
COPY .env.example .env

# Expose port 8000 for the HTTP transport mode
EXPOSE 8000

# Set entrypoint
CMD ["python", "run_server.py", "--http"]
