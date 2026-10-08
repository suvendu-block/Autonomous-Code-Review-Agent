# VISION.md

Vision.

## Statement

Every pull request gets a rigorous, instant, project-aware review — so humans only spend
attention on design and intent.

## Future state

1. A PR opens → within minutes a review appears with severity-ranked findings, evidence and
   suggested patches.
2. The agent knows the repository's conventions because it retrieves them, not because someone
   wrote rules.
3. Every run is traced, reproducible and auditable in LangSmith.
4. Humans approve merges; the agent never merges on its own.

## Why now

LLM agents are good enough at mechanical review (style, security smells, obvious bugs, test
gaps) to remove the slowest 80% of review latency, but only if they are orchestrated,
grounded in project context and observable.

## Boundaries

- Assist, do not decide. Human keeps final approval.
- Depth over breadth. Python first, other languages later.
- Evidence over vibes. Every finding points at a file and line.

## Success looks like

- Review latency: hours → minutes.
- Blocker and major issues caught before a human looks.
- Zero unexplained runs: report or explicit error, never silence.
