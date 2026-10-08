# SECURITY.md

Security policy for the project.

## Threat model in one line

The agent reads code and secrets-adjacent context, calls an LLM provider, and posts
comments — so the risks are **leakage**, **supply chain**, and **unintended write access**.

## Secrets

- Never commit secrets. `.env` is git-ignored; it is mounted or injected at runtime.
- Secrets live only in env vars (`SPECIFICATION.md §2`) and the CI/CD secret store.
- No secret may appear in a report, a prompt, a trace, or a log line.
- Rotate `LLM_API_KEY` and `LANGSMITH_API_KEY` on any suspected exposure; treat provider
  logs as if the key were visible there.

## What the agent may see

| Access | Allowed | Never |
|---|---|---|
| Repo contents | Working tree of the reviewed change | Unrelated repositories |
| Diff | The change under review | Credentials, `.env`, key material (scrub before ingest) |
| Write | PR comments, CI status | Merge, force-push, branch deletion, secret stores |
| Network | LLM provider, LangSmith | Arbitrary URLs from repo content |

## Prompt injection

Reviewed code and repo docs are untrusted input.

- Retrieved chunks (`codebase_docs`, `past_reviews`) are treated as data, never as
  instructions.
- The agent has no tools that mutate the repository — review is read-only
  (`PRINCIPLES.md §3`).
- Findings that instruct a reader are phrased as suggestions, not commands
  (`CONVERSATION.md`).

## Build and supply chain

- Pin base images and dependency versions; review dependency changes like code.
- One image, built by CI, signed/tagged by git SHA (`DEPLOYMENTS.md`).
- No `COPY` of `.env`, keys, or local ChromaDB volumes into the image.
- Run as non-root; read-only root filesystem where the runtime allows it.

## Data handling in traces and memory

- LangSmith traces contain prompts and node outputs → assume they are sensitive; project
  access is restricted to the team.
- ChromaDB collections embed repo docs; `CHROMA_PATH` lives on a volume, not in the repo.
- Redact obvious secrets before ingestion; scrub patterns (`AKIA…`, `-----BEGIN … KEY-----`,
  `ghp_…`) at ingest time.

## Reporting a vulnerability

1. Report privately to the maintainers — do not open a public issue.
2. Include: affected version/image tag, reproduction, impact.
3. We acknowledge within 72 hours and ship a fix before disclosing details.

## Compliance checklist (every release)

- [ ] No secrets in repo or image layers
- [ ] Traces contain no credentials
- [ ] Agent cannot write to the repository
- [ ] Exit codes and error paths leak no key material (`TROUBLESHOOTING.md`)
- [ ] Dependencies reviewed

## Related

- Privacy of reviewed code → `PRIVACY.md`
- Human ownership of keys and merge → `HUMAN.md`
