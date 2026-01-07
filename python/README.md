# Python Scripts

## Setup
1. Create a virtual environment: `python -m venv .venv` (optional)
2. Activate it and install dependencies: `pip install -r python/requirements.txt` (installs `boto3`)

## AWS Credentials
- Configure credentials and default region via `aws configure` **or** export env vars `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, optional `AWS_SESSION_TOKEN`, and `AWS_REGION`/`AWS_DEFAULT_REGION`.

## Prune a Glacier Vault
Deletes every archive from a vault (irreversible).

### Available Options

- `--vault-name` (required) - Name of the Glacier vault to prune
- `--region` - AWS region for the Glacier vault (defaults to your AWS config/profile)
- `--dry-run` - List archives without deleting them (safe preview mode)
- `--save-inventory FILE` - Save retrieved inventory to a JSON file for later reuse
- `--load-inventory FILE` - Load inventory from a previously saved JSON file instead of retrieving from AWS
- `--use-job-id JOB_ID` - Resume using an existing inventory-retrieval job ID
- `--poll-seconds SECONDS` - Seconds to wait between job status checks (default: 300)

**Note:** `--load-inventory` and `--use-job-id` are mutually exclusive.

### Usage Examples

#### Basic usage
```bash
# Delete all archives (irreversible!)
python python/scripts/prune_glacier_vault.py --vault-name YOUR_VAULT_NAME --region eu-west-1

# Dry-run to preview what would be deleted
python python/scripts/prune_glacier_vault.py --vault-name YOUR_VAULT_NAME --dry-run
```

#### Recommended workflow: Save and reuse inventory
Since inventory retrieval takes hours, save it during dry-run and reuse for actual deletion:

```bash
# Step 1: Dry-run and save inventory (takes hours)
python python/scripts/prune_glacier_vault.py --vault-name YOUR_VAULT_NAME --dry-run --save-inventory inventory.json

# Step 2: Review the saved inventory, then delete using it (instant start, no waiting)
python python/scripts/prune_glacier_vault.py --vault-name YOUR_VAULT_NAME --load-inventory inventory.json
```

#### Additional inventory examples
```bash
# Save inventory during actual deletion (useful for backup or resuming if interrupted)
python python/scripts/prune_glacier_vault.py --vault-name YOUR_VAULT_NAME --save-inventory inventory.json

# Review a previously saved inventory without making any API calls
python python/scripts/prune_glacier_vault.py --vault-name YOUR_VAULT_NAME --load-inventory inventory.json --dry-run
```

#### Resume with an existing job ID
If you have a job ID from a previous run that's still in progress or completed:

```bash
# Resume waiting for job completion and fetch inventory
python python/scripts/prune_glacier_vault.py --vault-name YOUR_VAULT_NAME --use-job-id YOUR_JOB_ID --region eu-west-1

# Resume and save the inventory for later use
python python/scripts/prune_glacier_vault.py --vault-name YOUR_VAULT_NAME --use-job-id YOUR_JOB_ID --save-inventory inventory.json
```
