# Repository Guidelines

## Project Overview
This repository automates YouTube Shorts discovery for a topic, enriches results with transcripts and Russian translations, and writes the output to Google Sheets. The desktop UI collects search parameters (topic, language, region, date range) and triggers the pipeline.

## Project Structure & Module Organization
- `app/`: desktop UI (PySide6) and user workflows.
- `pipeline/`: search, filtering, transcription, translation, and export logic.
- `services/`: API clients (YouTube Data API, LLM query expansion, Speech-to-Text, Translation, Sheets).
- `storage/`: SQLite models, migrations, and cache utilities.
- `tests/`: unit and integration tests.
- `scripts/`: helper scripts (auth setup, local runs).

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: create and activate a virtualenv.
- `pip install -r requirements.txt`: install dependencies.
- `python -m app`: run the desktop UI locally.
- `python -m pipeline.run --topic "..."`: headless pipeline run.
- `pytest`: run all tests.

## Coding Style & Naming Conventions
- Indentation: 4 spaces, no tabs.
- Use `ruff` for linting and `black` for formatting.
- Module names: `snake_case`; classes: `PascalCase`; functions/vars: `snake_case`.
- Keep API wrappers thin; place retry logic in `services/`.

## Testing Guidelines
- Framework: `pytest`.
- Test files: `tests/test_*.py`.
- Cover query expansion, Shorts filtering, and Sheets writing with fixtures.
- Run `pytest -k pipeline` for focused pipeline tests.

## Commit & Pull Request Guidelines
- Commits: imperative, short subject (e.g., "Add Shorts filter").
- PRs: include a clear description, linked issue (if any), and screenshots for UI changes.
- Note API keys used for local testing (never commit secrets).

## Configuration & Secrets
- Use a `.env` file for API keys and OAuth tokens.
- Required keys: YouTube Data API, LLM provider, Speech-to-Text, Translation, Google Sheets.
- Never commit `client_secret.json` or token files.

## Architecture Notes
- Only Shorts are kept: `contentDetails.duration` must **not** contain `M` (e.g., `PT45S`).
- Default search parameters: `region=US`, date range last 90 days.
- If fewer than 100 unique Shorts are found, generate additional query variants and repeat.
