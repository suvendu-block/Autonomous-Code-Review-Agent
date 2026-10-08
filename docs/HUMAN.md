# HUMAN.md

Where humans sit in the loop.

## Principle

The agent proposes, the human disposes. No auto-merge, ever (`PRINCIPLES.md §3`).

## Roles

| Role | Owns | Does not own |
|---|---|---|
| Author | The change; responding to findings | Final merge approval |
| Reviewer (human) | Design, intent, trade-offs | Mechanical style/security passes |
| Review agent | Evidence-gathering, consistency, coverage of the mechanical 80% | Merge decisions |
| Maintainer | Waivers, policy, severity thresholds | — |

## Interaction points

1. **Before the run** — human triggers review (CLI, CI, or webhook). The agent never
   self-initiates on a repository it wasn't pointed at.
2. **During the run** — no intervention. Runs are observable in LangSmith; if a run is
   wrong, it is re-run, not patched live.
3. **After the run** — human reads the report, dismisses or acts on each finding, and
   approves the merge.

## What the human must still do

- Judge design and intent, which retrieval cannot supply.
- Decide on waivers: a `blocker` may be accepted only with a written reason in the PR.
- Approve changes to severity thresholds, prompts and eval datasets.
- Own the merge button.

## What the human must never delegate

- Secrets handling and access control (`SECURITY.md`).
- Triage of exit `2` infrastructure failures (`TROUBLESHOOTING.md`).
- Acceptance of a run that produced no report (`PRINCIPLES.md §1`).

## Escalation

| Signal | Meaning | Human action |
|---|---|---|
| Exit `0` | No blocker/major | Skim and merge |
| Exit `1` | Findings present | Address or waive with reason |
| Exit `2` | Run failed | Investigate via `TROUBLESHOOTING.md`, re-run |
| No output | Bug | Treat as incident (`PRINCIPLES.md §1`) |

## Feedback loop

Human review comments on merged PRs are the raw material for the `past_reviews` collection
and for eval dataset growth (`BACKLOGS.md` → Ideas inbox). The agent learns from what humans
wrote, not from what it assumed.
