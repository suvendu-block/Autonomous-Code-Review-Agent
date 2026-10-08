# CONVERSATION.md

How the agent and humans talk to each other.

## Channels

| Channel | Direction | Content |
|---|---|---|
| PR comment | Agent → human | Findings table + details (`SPECIFICATION.md §6`) |
| `review_report.json` | Agent → machine | Same findings, structured |
| Exit code | Agent → CI | `0` clean · `1` findings · `2` failure |
| LangSmith trace | Agent → operator | Per-node evidence for a run |
| CLI stderr | Agent → developer | Explicit errors, never silence |

## Message rules

1. **One run, one comment.** Re-runs edit or replace the previous comment; no thread spam.
2. **Evidence first.** Every finding carries `file`, `line` where known, `detail`, and an
   explicit `confidence`.
3. **Severity is a label, not an opinion.** `blocker | major | minor | info` — defined in
   `SPECIFICATION.md §3`.
4. **No prose without a pointer.** Findings link to code; the summary links to the trace.
5. **Failures are stated.** A node that errored says so in the report's error section.

## Report anatomy

```markdown
## 🤖 Autonomous Review — <n> findings
<summary line: what changed, what matters most>

| # | Severity | File | Issue |
|---|----------|------|-------|
| 1 | blocker  | security/api.py:42 | SQL string built from user input |

### Details
1. **[blocker] security/api.py:42** — …
   _Suggestion:_ …

### Run
model · trace · duration · errors (if any)
```

## Tone

- Neutral and specific; no blame, no hedging.
- Prefer "parameterize this query" over "this code is bad".
- Confidence below `0.5` is phrased as a question, not a verdict.

## Human replies

- A PR comment that replies to a finding with `wontfix: <reason>` records a waiver; waivers
  are candidates for `past_reviews` embeddings so the same non-issue is not re-reported.
- Design discussion stays in the PR — the agent does not participate in it (`HUMAN.md`).

## Never say

- "Looks good to me." — the agent does not approve.
- Anything when the run failed — it errors instead (`PRINCIPLES.md §1`).
- Findings without file and line for changed code.
