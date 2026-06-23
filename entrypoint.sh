#!/bin/sh

# Create folder for dockerd logs and docker storage
mkdir -p /workspace/data/docker-daemon
mkdir -p /var/log

# Start dockerd in the background
echo "[Fly-Dind] Starting Docker daemon..."
dockerd --data-root /workspace/data/docker-daemon > /var/log/dockerd.log 2>&1 &

# Wait for Docker to boot up
echo "[Fly-Dind] Waiting for Docker daemon to initialize..."
until docker info >/dev/null 2>&1; do
  sleep 1
done
echo "[Fly-Dind] Docker daemon is ready."

# Pre-pull sandbox images in the background (speeds up first solution run)
echo "[Fly-Dind] Pre-pulling sandbox runtimes..."
docker pull gcc:13 &
docker pull python:3.12-slim &

# Start the Python MCP server in the foreground
echo "[Fly-Dind] Starting CodeChef MCP Server..."
exec python run_server.py --http --host 0.0.0.0 --port 8000 --no-reload
