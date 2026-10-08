# PRIVACY.md

What data the agent touches and where it goes.

## Data map

| Data | Collected | Leaves the machine | Retention |
|---|---|---|---|
| Diff / changed code | yes | to LLM provider; to LangSmith in traces | per CI artifact policy |
| Repo docs & conventions | yes | embedded locally in ChromaDB | until re-ingested / volume deleted |
| Past findings | yes | local ChromaDB | until pruned |
| Traces (prompts + outputs) | when tracing on | LangSmith project | provider retention setting |
| API keys | env only | to provider as auth | rotation policy |
| Human PR comments / waivers | on feedback | local `past_reviews` | until pruned |
| Personal data | not intentionally collected | — | — |

## Principles

1. **Minimum necessary.** Only the reviewed change and the context needed for it are sent
   to the model.
2. **Local by default.** ChromaDB stays on the operator's volume; tracing is opt-in except
   in prod where it is mandated for auditability (`OPERATIONS.md`).
3. **No training on your code.** Provider-side data handling is configured to the
   no-training/zero-retention option where the provider offers it; verify per provider.
4. **No secrets in data.** Scrub patterns before ingestion and before tracing
   (`SECURITY.md`).

## What is sent to the LLM provider

- The diff hunks under review.
- Up to 8 retrieved context chunks (`SPECIFICATION.md §4`).
- The specialist prompt and its version tag.

Not sent: full repository history, unrelated files, keys, `.env`.

## Third parties

| Party | Purpose | Data |
|---|---|---|
| LLM provider | Inference | diff + context + prompts |
| LangSmith | Tracing / eval | full run traces when key is set |
| Git provider | PR comments | findings report only |

## Retention and deletion

- Traces: governed by LangSmith project retention; delete the project to purge.
- ChromaDB: delete `CHROMA_PATH` to remove all embedded content.
- CI artifacts: follow pipeline retention; reports contain file paths and finding text.

## Your obligations (operator)

- Confirm your organisation may send the reviewed code to the chosen provider.
- Restrict access to the LangSmith project and the `CHROMA_PATH` volume.
- Keep `.env` out of the repository (`SECURITY.md`).

## Related

- Access boundaries → `SECURITY.md`
- What traces contain → `OPERATIONS.md`
