# CodeChef Contest MCP Server — Complete Build Guide

# 1. Create Project

```bash
mkdir codechef-mcp
cd codechef-mcp
```

---

# 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

---

# 3. Install Dependencies

```bash
pip install fastapi uvicorn playwright httpx docker redis psycopg2-binary
pip install mcp python-dotenv sqlalchemy
```

---

# 4. Recommended Folder Structure

```text
codechef-mcp/
│
├── app/
│   ├── auth/
│   ├── browser/
│   ├── sandbox/
│   ├── solver/
│   ├── validator/
│   ├── retry_engine/
│   ├── tools/
│   ├── models/
│   ├── utils/
│   ├── main.py
│   └── mcp_server.py
│
├── docker/
├── tests/
├── requirements.txt
├── docker-compose.yml
└── .env
```

---

# 5. Create MCP Server

## app/mcp_server.py

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("codechef-mcp")
```

---

# 6. Create Main Entry

## app/main.py

```python
from app.mcp_server import mcp

app = mcp.streamable_http_app()
```

Run:

```bash
uvicorn app.main:app --reload
```

---

# 7. Browser Automation Setup

Install Playwright:

```bash
playwright install
```

---

# 8. Login Automation

## app/browser/login.py

```python
from playwright.async_api import async_playwright

async def login():
    pass
```

Store cookies securely.

NEVER hardcode credentials.

---

# 9. Contest Navigation Tool

## app/tools/contest.py

```python
from app.mcp_server import mcp

@mcp.tool()
async def open_contest(contest_code: str):
    return {
        "status": "opened",
        "contest": contest_code
    }
```

---

# 10. Problem Fetch Tool

```python
@mcp.tool()
async def get_problem(problem_code: str):
    pass
```

Fetch:

- statement
- examples
- constraints
- limits

---

# 11. AI Solving Pipeline

## Required Pipeline

```text
fetch problem
    ↓
analyze constraints
    ↓
generate approach
    ↓
generate solution
    ↓
generate tests
    ↓
compile
    ↓
run samples
    ↓
run stress tests
    ↓
validate complexity
    ↓
submit
```

---

# 12. IMPORTANT SECURITY RULE

NEVER expose:

```python
subprocess.run(user_input)
```

NEVER expose raw shell execution tools.

The LLM must ONLY access constrained MCP tools.

---

# 13. Safe Sandbox Design

## app/sandbox/runner.py

```python
import subprocess
import tempfile

def run_cpp(code_path):

    cmd = [
        "docker",
        "run",
        "--rm",
        "--network=none",
        "--memory=256m",
        "--cpus=1",
        "--read-only",
        "--cap-drop=ALL",
        "--pids-limit=64",
        "gcc:13",
    ]

    subprocess.run(
        cmd,
        timeout=5
    )
```

---

# 14. Add Timeout Protection

```python
subprocess.run(
    cmd,
    timeout=5
)
```

---

# 15. Multi-Language Support

Support:

- C++
- Python
- Java
- Go
- Rust

Each language gets isolated runtime images.

---

# 16. Build Test Generator

## app/validator/test_generator.py

```python
def generate_edge_cases():

    return [
        "minimum_input",
        "maximum_input",
        "duplicate_values",
        "sorted_case",
        "reverse_sorted"
    ]
```

---

# 17. Stress Testing System

## Strategy

For harder problems:

1. Generate random tests
2. Generate brute force solution
3. Compare outputs
4. Detect mismatches

---

# 18. Confidence Evaluator

## app/validator/confidence.py

```python
def evaluate_confidence():

    score = 0

    # sample pass
    # stress pass
    # complexity pass

    return score
```

Submit ONLY if confidence exceeds threshold.

---

# 19. Submission Tool

## app/tools/submission.py

```python
@mcp.tool()
async def submit_solution(
    problem_code: str,
    language: str,
    code: str
):
    pass
```

---

# 20. Verdict Polling

## Workflow

```text
submit
   ↓
submission_id
   ↓
poll
   ↓
AC / WA / TLE / RE
```

---

# 21. Retry Engine

## app/retry_engine/retry.py

```python
def retry_solution():

    # analyze verdict
    # inspect failing logic
    # regenerate patch
    pass
```

---

# 22. Sequential Contest Solver

## app/solver/contest_solver.py

```python
async def solve_contest():

    problems = [
        "Q1",
        "Q2",
        "Q3",
        "Q4",
        "Q5"
    ]

    for problem in problems:

        # solve
        # validate
        # submit
        pass
```

---

# 23. Smart Strategy Engine

The agent should:

- prioritize easy problems
- skip temporarily if stuck
- revisit later
- maximize accepted count

---

# 24. Add Redis Cache

```python
import redis

redis_client = redis.Redis(
    host="localhost",
    port=6379
)
```

---

# 25. Add PostgreSQL

Docker:

```bash
docker run \
-e POSTGRES_PASSWORD=password \
-p 5432:5432 postgres
```

---

# 26. SQLAlchemy Setup

```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql://postgres:password@localhost/postgres"
)
```

---

# 27. Logging System

## Requirements

Log:

- submissions
- retries
- failures
- runtime
- sandbox usage

---

# 28. Add Rate Limiting

Recommended:

- slowapi
- nginx rate limiting

Prevent platform bans.

---

# 29. Add Monitoring

Recommended:

- Prometheus
- Grafana

Track:

- execution time
- sandbox failures
- AC rate
- retry counts

---

# 30. Docker Compose

## docker-compose.yml

```yaml
version: '3.9'

services:

  api:
    build: .
    ports:
      - "8000:8000"

  redis:
    image: redis

  postgres:
    image: postgres
```

---

# 31. MCP Integration

## Claude Desktop

```json
{
  "mcpServers": {
    "codechef": {
      "command": "python",
      "args": ["run_server.py"]
    }
  }
}
```

---

# 32. Cursor Integration

```json
{
  "mcpServers": {
    "codechef-mcp": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

---

# 33. Secure Tool Design

## GOOD

```python
run_cpp(code, tests)
```

## BAD

```python
run_terminal(command)
```

The MCP must NEVER expose unrestricted execution.

---

# 34. Production Security Checklist

## MUST HAVE

- container isolation
- timeout protection
- no network containers
- encrypted secrets
- read-only runtime
- dropped Linux capabilities
- audit logging
- resource quotas

---

# 35. Recommended Build Order

## Phase 1

- MCP server
- contest fetch
- problem fetch

## Phase 2

- secure sandbox
- code execution

## Phase 3

- automated testing
- stress testing

## Phase 4

- submission system
- retry engine

## Phase 5

- sequential contest solving
- optimization engine

## Phase 6

- monitoring
- scaling
- production deployment

---

# 36. Final Architecture

```text
LLM
 │
 ▼
MCP Server
 │
 ├──────────────┐
 ▼              ▼
Playwright   Redis Cache
 │
 ▼
Contest Pages
 │
 ▼
Sandbox Runner
 │
 ▼
Validation Engine
 │
 ▼
Submission Engine
 │
 ▼
Verdict Poller
```

---

# 37. Recommended Future Enhancements

- multi-agent solving
- brute-force verifier generation
- solution explanation engine
- adaptive retry system
- distributed stress testing
- local offline contest mode
