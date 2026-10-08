# PROJECT.md

All details about the project.

## Name

Autonomous Code Review Agent

## Summary

An autonomous, multi-agent code review system that reads a pull request / diff, retrieves
relevant project context from a vector store, runs specialized review agents over the change,
and posts a structured, actionable review comment.

## Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Agent orchestration | LangGraph |
| Design style | Multi-agent (supervisor + specialists) |
| Vector memory | ChromaDB |
| Observability / tracing | LangSmith |
| Packaging & runtime | Docker / Docker Compose |

## Goals

1. Reduce review latency from hours to minutes.
2. Catch bugs, security issues, style violations and missing tests automatically.
3. Learn project conventions from the repository itself (retrieval, not hard-coded rules).
4. Keep a human in the loop for final approval.

## Non-goals

- Auto-merging code without human approval.
- Replacing human reviewers for design-level discussions.
- Supporting every language on day one (Python first).

## Key entry points

- `index.py` — application entry point.
- `ARCHITECTURE.md` — how the pieces fit together.
- `SPECIFICATION.md` — precise technical behavior.
- `REQUIREMENTS.md` — what the system must do.

## Status

Early development (skeleton). See `CHANGELOG.md` and `ROADMAP.md`.
