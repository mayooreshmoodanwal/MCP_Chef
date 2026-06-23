# Deploying CodeChef MCP Server to Render (Free Tier)

Render offers a fully-featured free tier for Web Services that does not require a credit card/payment method to get started. By deploying the CodeChef MCP server to Render, you will have a public HTTPS URL that you can connect to Cursor, Claude, or other AI agents.

> [!NOTE]
> **Ephemeral Disk**: On Render's free tier, the container filesystem is ephemeral. This means your SQLite database (`codechef_mcp.db`) and session cookies (`cookies/codechef_cookies.json`) will reset whenever the service restarts (usually once a day).
> The server is designed to handle this automatically: if cookies are cleared, it will execute a fresh login using the `CODECHEF_USERNAME` and `CODECHEF_PASSWORD` environment variables.

---

## 1. Preparing the Codebase

Render will build and run the application using the existing [Dockerfile](file:///Users/ayushkumarsingh/Downloads/MCP_Chef/Dockerfile). Since we are not using the Docker-in-Docker sandbox execution on Render, the default `Dockerfile` is ready to go.

Make sure the following files are pushed to your Git repository (GitHub/GitLab):
* `app/` (all application source code)
* `run_server.py`
* `requirements.txt`
* `Dockerfile`

---

## 2. Step-by-Step Render Deployment

### Step 1: Sign up and connect GitHub
1. Go to [Render](https://render.com/) and create a free account.
2. In the Render Dashboard, click the **New +** button in the top right and select **Web Service**.
3. Connect your GitHub or GitLab account and select your repository containing the MCP server.

### Step 2: Configure Web Service Details
On the configuration page, set the following fields:
* **Name**: `codechef-mcp` (or any name you prefer)
* **Region**: Choose the region closest to you (e.g., `Singapore (Southeast Asia)` or `Oregon (US West)`)
* **Branch**: `main` (or your active development branch)
* **Runtime**: `Docker` (Render will automatically detect this and build using your `Dockerfile`)
* **Instance Type**: Select **Free**

### Step 3: Add Environment Variables
Scroll down, click **Advanced**, then select **Add Environment Variable** to add the config keys:

| Key | Value | Description |
| :--- | :--- | :--- |
| `CODECHEF_USERNAME` | `your_username` | Your CodeChef username |
| `CODECHEF_PASSWORD` | `your_password` | Your CodeChef password |
| `PORT` | `8000` | The internal port (matches port in `Dockerfile`) |
| `DATABASE_URL` | `sqlite+aiosqlite:///./codechef_mcp.db` | Local SQLite path |

### Step 4: Deploy
Click **Create Web Service** at the bottom of the page. 

Render will begin pulling the repository, building the Docker image (installing Chromium and Playwright), and starting the server. Once the build completes, the status will change to **Live**.

---

## 3. Connecting to Client Applications

Render will assign you a public URL (e.g., `https://codechef-mcp.onrender.com`).

### Connecting to Cursor
1. In Cursor, open **Settings** (Gear icon) → **Features** → **MCP**.
2. Click **+ Add New MCP Server**.
3. Configure the fields:
   * **Name**: `codechef-mcp`
   * **Type**: `sse`
   * **URL**: `https://your-app-name.onrender.com/mcp` (ensure you append `/mcp`)
4. Click **Save**.

### Connecting to Claude Desktop (Web Mode)
Because Render web services are publicly accessible over HTTPS, you can connect them to browser-based client extensions or tools that support SSE connections.
