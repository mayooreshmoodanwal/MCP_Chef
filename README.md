# CodeChef Contest MCP Server

An AI-powered competitive programming assistant implementing the Model Context Protocol (MCP). This server allows AI agents (like Claude Desktop or Cursor) to participate in CodeChef contests: fetching problems, generating/testing solutions in a secure sandbox, managing retry states, submitting answers, and tracking contest progress.

---

## 🚀 Features

* **Contest Management**: Open contests, retrieve problem lists, and track solved vs. remaining problems.
* **Browser Automation**: Playwright-based logins, problem-statement scraping, submission uploads, and verdict polling.
* **Secure Sandbox**: Docker-isolated compilation and execution (supports C++, Python, Java, Go, Rust) with no internet access, limited CPU/memory, and execution timeouts.
* **Validation & Retry**: Custom edge-case generator, confidence evaluator, and self-repair engine to analyze verdicts and repair failing solutions iteratively.

---

## 📂 Project Structure

```text
MCP_Chef/
│
├── app/
│   ├── browser/       # Playwright-based browser automation (login, submit, poll)
│   ├── models/        # SQLAlchemy database schema (SQLite)
│   ├── retry_engine/  # Diagnosis & self-repair pipeline
│   ├── sandbox/       # Secure Docker runner configuration & language setup
│   ├── solver/        # Sequential contest solver state (Q1 → Q5)
│   ├── tools/         # Exposed MCP tool decorators
│   ├── utils/         # Structured logger and cache layer
│   ├── main.py        # Streamable HTTP ASGI app
│   └── mcp_server.py  # FastMCP server instantiation
│
├── tests/             # Automated test suite
├── Dockerfile         # Multi-stage container definition
├── docker-compose.yml # Compose configuration (App, Redis)
├── run_server.py      # Unified server CLI entrypoint (STDIO & HTTP)
└── .env               # Local configuration file (not tracked in Git)
```

---

## 🛠️ Local Setup

### Prerequisites
* Python 3.10+
* Docker (Required for sandbox execution)
* Node.js (Optional, for `localtunnel` testing)

### Step 1: Install Dependencies
Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### Step 2: Configure Environment
Copy the example environment file and add your CodeChef credentials:
```bash
cp .env.example .env
```
Open [.env](file:///Users/ayushkumarsingh/Downloads/MCP_Chef/.env) and set your CodeChef username and password.

### Step 3: Run Tests
Verify your local installation:
```bash
python -m pytest tests/ -v
```

---

## 💻 Running the Server

### 1. STDIO Transport (For Claude Desktop)
To run the server locally over Standard Input/Output:
```bash
python run_server.py
```
Add the configuration to your Claude Desktop config (e.g., `~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "codechef": {
      "command": "/Users/ayushkumarsingh/Downloads/MCP_Chef/venv/bin/python",
      "args": ["/Users/ayushkumarsingh/Downloads/MCP_Chef/run_server.py"]
    }
  }
}
```

### 2. HTTP Transport (For Cursor/Web Clients)
To run the server over HTTP/SSE:
```bash
python run_server.py --http --port 8000
```
Then configure your client to connect to:
`http://localhost:8000/mcp`

---

## ☁️ Deployment

We have configured deployment setups for both container and VM platforms:

* **Render (Free Tier)**: For a quick deployment that does not require a card, see the [Render Deployment Guide](file:///Users/ayushkumarsingh/Downloads/MCP_Chef/render_deployment.md).
* **Fly.io (VM with Sandbox)**: For running with the secure Docker sandbox enabled, see the [Fly.io Deployment Guide](file:///Users/ayushkumarsingh/Downloads/MCP_Chef/fly_io_deployment.md).
