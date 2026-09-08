# Security

## Secrets

- Store `OPENAI_API_KEY` and `FLASK_SECRET_KEY` only in `.env` or the deployment platform's secret manager.
- Never put a real credential in source code, tests, logs, screenshots, or issue comments.
- Treat any credential that has appeared in Git history as compromised. Revoke it in the provider dashboard, create a replacement, and update only your local/deployment secret store.

## Reporting a vulnerability

Do not open a public issue containing secrets or exploit details. Contact the repository owner privately with a concise description and reproduction steps.
