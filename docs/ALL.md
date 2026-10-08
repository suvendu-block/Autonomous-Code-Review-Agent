# ALL.md

All about the project (overview).

## What it is

The **Autonomous Code Review Agent** is an AI system that reviews code changes without a human
initiating each step. Given a repository and a diff, it plans its review, delegates to
specialized agents, gathers evidence, and returns a single consolidated review.

## Why it exists

Code review is the highest-leverage quality gate in software, but it is slow and inconsistent.
This project automates the mechanical 80% (style, correctness smells, security, test coverage)
so humans can focus on design and intent.

## How it works (one paragraph)

A **supervisor agent** in LangGraph decomposes the review into tasks. Specialist agents —
`context_retriever` (ChromaDB), `bug_hunter`, `security_auditor`, `style_linter`,
`test_gap_analyzer`, `summarizer` — run as graph nodes, each with its own prompt and tools.
LangSmith traces every node execution. The final node emits a markdown review with severity
labels and suggested patches.

## Design in one line

**Multi-agent + retrieval-augmented review + full tracing + containerized delivery.**

## Components

| Component | Purpose |
|---|---|
| Supervisor | Plans and routes the review workflow |
| Specialist agents | Perform focused review passes |
| ChromaDB store | Project conventions, past reviews, docs as embeddings |
| LangSmith | Tracing, evaluation, prompt versioning |
| Docker image | Reproducible runtime for local and CI use |

## Docs map

- Vision → `VISION.md`, `MILESTONES.md`
- Planning → `ROADMAP.md`, `BACKLOGS.md`, `TASKS.md`, `STEPS.md`
- Design → `ARCHITECTURE.md`, `SPECIFICATION.md`, `PRINCIPLES.md`, `DECISIONS.md`
- Process → `CONTRIBUTION.md`, `HUMAN.md`, `CONVERSATION.md`
- Operations → `DEPLOYMENTS.md`, `OPERATIONS.md`, `TESTING.md`, `TROUBLESHOOTING.md`
- Policy → `SECURITY.md`, `PRIVACY.md`
- Meta → `FILES.md`, `CHANGELOG.md`

## Read this first

1. `VISION.md`
2. `ARCHITECTURE.md`
3. `STEPS.md`
