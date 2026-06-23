# CodeChef Contest MCP Server — Product Requirements Document (PRD)

## 1. Project Overview

### Project Name
CodeChef Contest MCP Server

### Objective
Build a secure, production-grade MCP (Model Context Protocol) server for integrating AI assistants with CodeChef contest workflows.

The MCP server should allow an LLM to:

- Open contests
- Fetch contest problems
- Generate solutions
- Generate strong edge-case tests
- Run solutions in a secure sandbox
- Retry failed solutions
- Submit accepted solutions
- Track verdicts and progress
- Solve problems sequentially (Q1 → Q5)

The system MUST prioritize safety, reliability, and controlled execution.

---

# 2. Core Philosophy

The MCP server MUST:

- NEVER expose unrestricted bash access
- NEVER allow arbitrary shell execution
- NEVER allow unrestricted file system access
- NEVER allow unrestricted network access
- ONLY expose constrained tools

The LLM should interact ONLY through approved MCP tools.

---

# 3. Primary Goals

## Core Goals

- Contest automation
- Secure sandbox execution
- AI-assisted solving loop
- Automated test generation
- Submission verification
- Reliable verdict polling
- Multi-language support

## Safety Goals

- Zero unrestricted shell access
- Container isolation
- Network isolation
- Resource limits
- Timeout protection
- Audit logging

---

# 4. Non-Goals

The system will NOT:

- Provide arbitrary terminal access
- Provide unrestricted Docker access
- Allow external internet access from generated code
- Bypass contest platform rules
- Attempt browser privilege escalation

---

# 5. Functional Requirements

# 5.1 Contest Management

## Requirements

The MCP server must support:

- Open contest
- List contest problems
- Track solved/unsolved problems
- Sequential solving workflow

## Example

open_contest(contest_code="START123")

---

# 5.2 Problem Fetching

## Requirements

Fetch:

- Problem statement
- Constraints
- Input/output format
- Examples
- Time limits
- Memory limits

---

# 5.3 AI Solving Workflow

## Required Workflow

For every problem:

1. Read problem
2. Analyze constraints
3. Generate approach
4. Generate solution
5. Generate edge-case tests
6. Compile solution
7. Run sample tests
8. Run generated tests
9. Detect failures
10. Retry/fix solution
11. Submit ONLY after confidence threshold

---

# 5.4 Automated Test Generation

## Requirements

The system MUST generate:

- Small random tests
- Edge cases
- Boundary cases
- Worst-case inputs
- Adversarial tests

## Example Categories

- Empty/minimum inputs
- Maximum constraints
- Duplicate-heavy inputs
- Sorted/reverse sorted inputs
- Overflow scenarios

---

# 5.5 Confidence Validation

## Requirements

Before submission:

- Solution MUST pass samples
- Solution MUST pass generated tests
- Complexity MUST be validated
- Runtime estimation MUST be acceptable

Submission should occur ONLY if confidence score exceeds threshold.

---

# 5.6 Safe Code Execution

## Requirements

All code execution MUST occur inside isolated containers.

## Mandatory Restrictions

- No internet access
- Read-only runtime
- Limited memory
- Limited CPU
- Limited execution time
- No host filesystem access
- No privileged containers

---

# 5.7 Submission System

## Requirements

The MCP server must:

- Submit solutions
- Poll verdicts
- Detect WA/TLE/MLE/RE
- Trigger retry workflow
- Store submission history

---

# 5.8 Sequential Contest Solving

## Workflow

solve_contest():
    solve Q1
    solve Q2
    solve Q3
    solve Q4
    solve Q5

The system should dynamically decide:

- skip hard problems temporarily
- revisit later
- maximize solved count

---

# 5.9 Retry & Self-Repair System

## Requirements

If solution fails:

1. Analyze failure
2. Inspect failed tests
3. Re-evaluate complexity
4. Patch solution
5. Re-run tests
6. Retry submission

Maximum retry count must be configurable.

---

# 6. MCP Tool Definitions

## Contest Tools

### open_contest
Open a CodeChef contest.

### list_problems
Return all contest problems.

### get_problem
Fetch full problem statement.

---

## Solving Tools

### generate_solution
Generate candidate solution.

### generate_tests
Generate adversarial test cases.

### run_solution
Run code inside secure sandbox.

### validate_complexity
Estimate time complexity.

### evaluate_confidence
Calculate submission confidence.

---

## Submission Tools

### submit_solution
Submit code safely.

### get_submission_status
Poll submission verdict.

### retry_solution
Retry after WA/TLE/RE.

---

## Analytics Tools

### get_contest_progress
Return solved/unsolved problems.

### get_submission_history
Return previous submissions.

---

# 7. Non-Functional Requirements

# 7.1 Performance

| Metric | Target |
|---|---|
| Tool latency | < 1s cached |
| Sandbox startup | < 3s |
| Verdict polling | < 2s |

---

# 7.2 Reliability

| Requirement | Target |
|---|---|
| Uptime | 99.5% |
| Retry support | Required |
| Graceful failure | Required |

---

# 7.3 Security

## Mandatory Controls

### Container Isolation
All execution MUST happen in Docker containers.

### No Arbitrary Bash
LLM MUST NOT receive raw shell access.

### Restricted Commands
Only approved operations allowed.

### Network Isolation
Containers MUST run with:
--network=none

### Resource Limits
Enforce:
- memory limits
- CPU limits
- process limits
- execution timeout

### Secret Protection
Cookies/tokens MUST be encrypted.

### Audit Logging
Log:
- submissions
- execution attempts
- failures
- abuse attempts

---

# 8. Safe MCP Design

## Forbidden MCP Tools

The following tools MUST NEVER exist:

- bash()
- terminal()
- exec_shell()
- unrestricted_python()
- docker_run_raw()

---

## Allowed MCP Design

Expose ONLY controlled APIs:

- run_cpp(code, tests)
- run_python(code, tests)
- submit_code(problem_id, code)
- fetch_problem(problem_id)

The MCP layer must sanitize all inputs.

---

# 9. System Architecture

## Components

### MCP Server
Handles:
- tool orchestration
- workflow management

### Browser Automation Service
Handles:
- login
- contest navigation
- submission

### Sandbox Service
Handles:
- secure execution
- isolation

### Retry Engine
Handles:
- iterative repair
- debugging

### Cache Layer
Handles:
- problem cache
- submission cache

### Database Layer
Handles:
- analytics
- execution history

---

# 10. Sandbox Security Requirements

## Docker Restrictions

Required flags:

- --network=none
- --memory=256m
- --cpus=1
- --pids-limit=64
- --read-only
- --cap-drop=ALL

---

## Timeouts

| Action | Timeout |
|---|---|
| Compile | 10s |
| Execution | 5s |
| Stress test | 15s |

---

# 11. Contest Solving Strategy

## Easy Problems

- direct solving
- sample validation
- quick submit

---

## Hard Problems

Before submission:

1. Generate heavy stress tests
2. Generate randomized tests
3. Compare brute force vs optimized solution
4. Run multiple validation rounds
5. Estimate worst-case complexity

Only then submit.

---

# 12. Recommended Tech Stack

| Layer | Technology |
|---|---|
| MCP | FastMCP |
| Backend | FastAPI |
| Automation | Playwright |
| Sandbox | Docker |
| Cache | Redis |
| DB | PostgreSQL |
| Async HTTP | httpx |
| Queue | Celery/RQ |

---

# 13. Deployment Requirements

## Supported Platforms

- Railway
- Fly.io
- AWS
- GCP

---

# 14. Risks

| Risk | Mitigation |
|---|---|
| Platform bans | Rate limiting |
| Infinite loops | Timeout protection |
| Sandbox escape | Container isolation |
| Bad AI solutions | Multi-stage validation |
| Resource abuse | Strict quotas |

---

# 15. Success Metrics

| Metric | Target |
|---|---|
| Accepted submissions | > 80% easy-medium |
| Sandbox failures | < 1% |
| Unsafe execution incidents | 0 |
| Tool success rate | > 98% |
