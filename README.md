# API Integration Lab

Concise guide and quick-start for this Guardian analysis pipeline.

## What this repo does

- Fetches articles from the Guardian API for a given date.
- Sends articles to an LLM client for analysis.
- Writes per-day analysis files as JSONL to `outputs/`.

Code is grouped under `src/`:

- `src/api_client/` — Guardian HTTP client and error mapping.
- `src/llm_client/` — abstract LLM client and provider implementations.
- `src/orchestrator/` — pipeline orchestration (fetch → analyze → save).
- `src/cli/` — small CLI wrappers to run the pipeline.

## Quick start

1. Create a virtualenv and install deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Set the Guardian API key (use your shell or a `.env` file):

```bash
export GUARDIAN_API_KEY="your-key-here"
# or put GUARDIAN_API_KEY in a .env file for local testing
```

3. Run the pipeline for yesterday (CLI):

```bash
python -m src.cli.run_analysis
```

4. Run for a specific date:

```bash
python3 -m src.cli.run_analysis --date 2025-12-06
```

Output files are written to `outputs/guardian_analysis_YYYY-MM-DD.jsonl`.

## Important environment & config

- `GUARDIAN_API_KEY` (required): API key used by the `BaseClient`.
- `src/config.py` centralises runtime defaults (page-size, output dir, analyze limit, retry/backoff constants).
- `src/api_client/config.py` holds API-specific constants (base URL, default timeout).
- Use `--verbose` in CLI/debug runs to enable DEBUG logging (code reads logging flags).

## Debugging tips

- If VS Code tries to run `.vscode/launch.json` as a script, check your launch configuration and set `program` to the target Python file (or use `${file}`).
- Secrets are redacted in logs: `BaseClient` now redacts common secret keys (e.g. `api-key`) before logging.
- The HTTP client implements retries with exponential backoff, jitter and honors `Retry-After` when present. If you see 429/5xx repeatedly increase `DEFAULT_MAX_RETRIES` or contact the API provider.
- Failures from LLM calls are persisted to a separate failures file so you can resume or re-run problematic items (see `outputs/*_failures.jsonl`).

---
