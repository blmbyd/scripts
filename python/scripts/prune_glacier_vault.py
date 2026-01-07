"""Delete all archives from an Amazon Glacier vault.

This script initiates an inventory-retrieval job, waits for completion,
reads the inventory, and deletes every archive listed. Be aware that
inventory retrieval can take hours.
"""
import argparse
import json
import logging
import sys
import time
from typing import Dict, List

import boto3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Delete all archives from a Glacier vault")
    parser.add_argument("--vault-name", required=True, help="Name of the Glacier vault")
    parser.add_argument(
        "--region",
        help="AWS region for the Glacier client (defaults to your AWS config/profile)",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=300,
        help="Seconds to wait between job status checks (default: 300)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List archives without deleting them",
    )
    parser.add_argument(
        "--save-inventory",
        help="Save inventory to this file path after retrieval",
    )
    parser.add_argument(
        "--load-inventory",
        help="Load inventory from this file instead of retrieving from AWS",
    )
    parser.add_argument(
        "--use-job-id",
        help="Use an existing inventory-retrieval job ID instead of starting a new one",
    )
    
    args = parser.parse_args()
    
    # Validate mutually exclusive options
    if args.load_inventory and args.use_job_id:
        parser.error("--load-inventory and --use-job-id are mutually exclusive")
    
    return args


def start_inventory_job(client, vault_name: str) -> str:
    response = client.initiate_job(
        vaultName=vault_name,
        jobParameters={"Type": "inventory-retrieval", "Format": "JSON"},
    )
    return response["jobId"]


def wait_for_job(client, vault_name: str, job_id: str, poll_seconds: int) -> None:
    logging.info("Waiting for inventory job %s to complete (this can take hours)...", job_id)
    poll_count = 0
    while True:
        job = client.describe_job(vaultName=vault_name, jobId=job_id)
        status = job.get("StatusCode")
        if status == "InProgress":
            poll_count += 1
            logging.info("Still waiting... (poll #%d, next check in %d seconds)", poll_count, poll_seconds)
            time.sleep(poll_seconds)
            continue
        if status == "Succeeded":
            return
        raise RuntimeError(f"Inventory job failed with status: {status}")


def fetch_inventory(client, vault_name: str, job_id: str) -> Dict:
    logging.info("Downloading inventory for vault %s...", vault_name)
    output = client.get_job_output(vaultName=vault_name, jobId=job_id)
    body = output["body"].read()
    return json.loads(body)


def save_inventory_to_file(inventory: Dict, file_path: str) -> None:
    logging.info("Saving inventory to %s...", file_path)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2)
    logging.info("Inventory saved successfully.")


def load_inventory_from_file(file_path: str) -> Dict:
    logging.info("Loading inventory from %s...", file_path)
    with open(file_path, encoding="utf-8") as f:
        inventory = json.load(f)
    logging.info("Inventory loaded successfully.")
    return inventory


def delete_archives(client, vault_name: str, archives: List[Dict], dry_run: bool) -> int:
    total = len(archives)
    logging.info("Found %d archives to delete", total)
    if dry_run:
        logging.info("Dry-run enabled; no archives will be deleted.")
    deleted = 0
    for index, archive in enumerate(archives, start=1):
        archive_id = archive.get("ArchiveId")
        try:
            if dry_run:
                logging.info("Would delete %s (%d/%d)", archive_id, index, total)
                continue

            client.delete_archive(vaultName=vault_name, archiveId=archive_id)
            deleted += 1
            logging.info("Deleted %s (%d/%d)", archive_id, index, total)
        except Exception as exc:  # noqa: BLE001
            logging.error("Failed to delete %s: %s", archive_id, exc)
    return deleted


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)

    session = boto3.session.Session(region_name=args.region)
    client = session.client("glacier")

    try:
        if args.dry_run:
            logging.info("Dry-run mode: no archives will be deleted.")
        
        # Load or retrieve inventory
        if args.load_inventory:
            inventory = load_inventory_from_file(args.load_inventory)
        elif args.use_job_id:
            logging.info("Using existing inventory-retrieval job: %s", args.use_job_id)
            wait_for_job(client, args.vault_name, args.use_job_id, poll_seconds=args.poll_seconds)
            inventory = fetch_inventory(client, args.vault_name, args.use_job_id)
            
            # Save inventory if requested
            if args.save_inventory:
                save_inventory_to_file(inventory, args.save_inventory)
        else:
            job_id = start_inventory_job(client, args.vault_name)
            logging.info("Started inventory-retrieval job: %s", job_id)
            wait_for_job(client, args.vault_name, job_id, poll_seconds=args.poll_seconds)
            inventory = fetch_inventory(client, args.vault_name, job_id)
            
            # Save inventory if requested
            if args.save_inventory:
                save_inventory_to_file(inventory, args.save_inventory)
        
        archives = inventory.get("ArchiveList", [])
        deleted = delete_archives(client, args.vault_name, archives, dry_run=args.dry_run)
        if args.dry_run:
            logging.info("Dry-run complete. Would delete %d archives.", len(archives))
        else:
            logging.info("Finished. Deleted %d of %d archives.", deleted, len(archives))
    except KeyboardInterrupt:
        logging.warning("Interrupted by user; exiting.")
        return 1
    except Exception as exc:  # noqa: BLE001
        logging.error("Error: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
