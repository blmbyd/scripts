# Repository Conventions

- **Structure**: language-specific roots (`python/`, `powershell/`, `node/`).
- **Secrets**: Keep secrets in `.env` (not committed).
- **Logging/Outputs**: CLI tools log to stdout/stderr. Redirect to files when running in automation.
- **Testing**: Add smoke tests or unit tests per language before automation. Use dry-run flags before destructive actions.
- **Naming**: Scripts live under each language's `scripts/` folder. Use kebab-case for script filenames; keep modules in `lib/`.
