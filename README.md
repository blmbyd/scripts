# Scripts Repository

A collection of utility scripts organized by programming language, designed for automation and infrastructure management tasks.

## Repository Structure

```
.
├── python/          # Python scripts and utilities
├── powershell/      # PowerShell scripts and utilities
├── node/            # Node.js scripts and utilities (placeholder)
├── docs/            # Documentation and conventions
└── output/          # Output directory for generated files
```

## Quick Start

### Python Scripts
Python scripts are located in `python/scripts/` with shared utilities in `python/lib/`.

**Setup:**
```bash
# Optional: Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r python/requirements.txt
```

**Available Scripts:**
- `prune_glacier_vault.py` - Deletes all archives from an AWS Glacier vault

See [python/README.md](python/README.md) for detailed documentation.

### PowerShell Scripts
PowerShell scripts are located in `powershell/scripts/`.

**Linting:**
```powershell
Invoke-ScriptAnalyzer -Path powershell -Settings powershell/PSScriptAnalyzerSettings.psd1
```

See [powershell/README.md](powershell/README.md) for more information.

### Node.js Scripts
Node.js scripts will be located in `node/scripts/`. Currently a placeholder for future tools.

**Setup:**
```bash
cd node && npm install
```

See [node/README.md](node/README.md) for more information.

## Conventions

This repository follows specific conventions for structure, naming, and development practices. Please review [docs/CONVENTIONS.md](docs/CONVENTIONS.md) before contributing.

**Key conventions:**
- Scripts are organized in language-specific folders (python/, powershell/, node/) with `scripts/` subdirectories
- Use kebab-case for script filenames
- Keep secrets in `.env` files (not committed to version control)
- Add dry-run flags for destructive operations
- Place shared modules in `lib/` folders

## Output Directory

The `output/` directory is used for storing generated files, logs, and artifacts. All files in this directory are git-ignored except for the `.gitignore` file itself.

## Contributing

When adding new scripts:
1. Place them in the appropriate language folder's `scripts/` subdirectory (e.g., python/scripts/)
2. Update the language-specific README with documentation
3. Include usage examples and command-line options
4. Add tests where applicable
5. Follow the naming and structure conventions

## License

See repository license for details.
