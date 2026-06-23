# Deploying CodeChef MCP Server to Fly.io (with Sandbox Enabled)

Fly.io runs applications inside independent microVMs (Firecracker). Because it uses actual virtual machines rather than shared container hosts, it is possible to run a Docker daemon (`dockerd`) inside your app's VM. This allows the CodeChef MCP server's **sandbox execution tool** to run C++ and Python solutions in isolated containers on the cloud.

This guide details the complete configuration and deployment steps.

---

## 1. How Docker-in-Docker works on Fly.io

To run the sandbox runner, the Fly.io VM needs:
1. The Docker daemon (`dockerd`) running in the background.
2. The CodeChef MCP API running in the foreground.
3. Language runner Docker images (e.g., `gcc:13`, `python:3.12-slim`) pre-cached or pulled dynamically inside the VM.

---

## 2. Configuration Files

To support this setup, we need a custom entrypoint script, an updated `Dockerfile`, and a `fly.toml` configuration.

### A. The Startup Script: `entrypoint.sh`
Create a file named `entrypoint.sh` in the project root to start the Docker daemon, wait for it to initialize, pre-pull the required sandbox images, and then start the Uvicorn server:

```bash
#!/bin/sh

# Start dockerd in the background
echo "[Fly-Dind] Starting Docker daemon..."
dockerd --data-root /workspace/data/docker-daemon > /var/log/dockerd.log 2>&1 &

# Wait for Docker to boot up
echo "[Fly-Dind] Waiting for Docker daemon to initialize..."
until docker info >/dev/null 2>&1; do
  sleep 1
done
echo "[Fly-Dind] Docker daemon is ready."

# Pre-pull sandbox images (speeds up first execution)
echo "[Fly-Dind] Pre-pulling sandbox runtimes..."
docker pull gcc:13 &
docker pull python:3.12-slim &

# Start the Python MCP server
echo "[Fly-Dind] Starting CodeChef MCP Server..."
exec python run_server.py --http --host 0.0.0.0 --port 8000 --no-reload
```

---

### B. Updated `Dockerfile`
Your `Dockerfile` must install both `dockerd` (Docker engine) and the standard Python dependencies:

```dockerfile
FROM python:3.11-slim

# Install system dependencies, Docker daemon, iptables, and CA certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    lsb-release \
    ca-certificates \
    iptables \
    procps \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update && apt-get install -y --no-install-recommends \
    docker-ce \
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
COPY entrypoint.sh .

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Expose HTTP port
EXPOSE 8000

# Set entrypoint to run dockerd and the application
ENTRYPOINT ["./entrypoint.sh"]
```

---

### C. Fly.io Config: `fly.toml`
Create a `fly.toml` file in the root directory. Notice that we mount a persistent volume `mcp_data` to `/workspace/data` so that:
* Your database logs and cookies persist across restarts.
* The Docker daemon's storage is cached on disk (preventing pulling `gcc:13` on every deployment).

```toml
app = "your-codechef-mcp"
primary_region = "lax"

[build]
  dockerfile = "Dockerfile"

[[mounts]]
  source = "mcp_data"
  destination = "/workspace/data"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 1

[env]
  HOST = "0.0.0.0"
  PORT = "8000"
  DATABASE_URL = "sqlite+aiosqlite:////workspace/data/codechef_mcp.db"
```

---

## 3. Step-by-Step Deployment Instructions

### Step 1: Install Fly CLI and Authenticate
Install the command-line tool on your local machine and sign in:
```bash
# macOS
brew install superfly/tap/flyctl

# Linux
curl -L https://fly.io/install.sh | sh

# Login
fly auth login
```

### Step 2: Initialize Fly.io Application
Generate the application configuration. Fly will prompt you to choose a unique application name (replace `your-codechef-mcp` with your choice) and preferred deployment region:
```bash
fly launch --no-deploy
```

### Step 3: Provision Persistent Storage
Create the persistent volume specified in the `[[mounts]]` section of `fly.toml` in your chosen region (e.g., `lax`):
```bash
fly volumes create mcp_data --region lax --size 2
```
*Note: A volume size of 2GB is recommended to store both the SQLite database, persistent cookies, and cached Docker runtime layers.*

### Step 4: Configure Secure Credentials
Inject your CodeChef credentials as encrypted secrets:
```bash
fly secrets set CODECHEF_USERNAME="your_username" CODECHEF_PASSWORD="your_password"
```

### Step 5: Deploy to Fly.io
Deploy the stack to the cloud:
```bash
fly deploy
```

---

## 4. Connecting Client Applications

Once the deployment completes, your server will be running on HTTPS. You can connect it to Cursor or Claude Desktop.

### Connecting to Cursor
1. Go to **Settings** → **Features** → **MCP**.
2. Click **+ Add New MCP Server**.
3. Name: `codechef-mcp`
4. Type: `sse`
5. URL: `https://your-codechef-mcp.fly.dev/mcp`
