"""Configuration loading and AWS session utilities."""
from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3
import yaml
from botocore.credentials import ReadOnlyCredentials
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError


class AWSConfig(BaseModel):
    profile: Optional[str] = Field(default=None, description="AWS profile name")
    role_arn: Optional[str] = Field(default=None, description="Role ARN to assume")
    region: str = Field(default="us-east-1", description="AWS region")


class VaultConfig(BaseModel):
    name: str
    retention_days: int = Field(gt=0)


class GlacierConfig(BaseModel):
    vaults: List[VaultConfig]
    inventory_file: Optional[Path] = Field(default=None, description="Path to Glacier inventory JSON")


class DeleteConfig(BaseModel):
    dry_run: bool = True


class LoggingConfig(BaseModel):
    level: str = "INFO"


class AppConfig(BaseModel):
    aws: AWSConfig
    glacier: GlacierConfig
    delete: DeleteConfig = DeleteConfig()
    logging: LoggingConfig = LoggingConfig()


DEFAULT_CONFIG_PATH = Path("common/config/config.yml")
DEFAULT_ENV_PATH = Path(".env")


def _ensure_nested(data: Dict[str, Any], key: str) -> Dict[str, Any]:
    if key not in data or not isinstance(data[key], dict):
        data[key] = {}
    return data[key]


def _apply_env_overrides(data: Dict[str, Any]) -> Dict[str, Any]:
    aws = _ensure_nested(data, "aws")
    glacier = _ensure_nested(data, "glacier")
    delete_cfg = _ensure_nested(data, "delete")
    logging_cfg = _ensure_nested(data, "logging")

    # AWS
    if os.getenv("AWS_PROFILE"):
        aws["profile"] = os.getenv("AWS_PROFILE")
    if os.getenv("AWS_ROLE_ARN"):
        aws["role_arn"] = os.getenv("AWS_ROLE_ARN")
    if os.getenv("AWS_REGION"):
        aws["region"] = os.getenv("AWS_REGION")

    # Glacier vault overrides
    vaults_env = os.getenv("GLACIER_VAULTS")
    retention_env = os.getenv("GLACIER_RETENTION_DAYS")
    if vaults_env:
        names = [v.strip() for v in vaults_env.split(",") if v.strip()]
        retention_val = int(retention_env) if retention_env else None
        glacier["vaults"] = [
            {"name": name, "retention_days": retention_val or 365}
            for name in names
        ]
    elif retention_env:
        # apply retention to existing vaults
        try:
            retention_val = int(retention_env)
            if "vaults" in glacier and isinstance(glacier["vaults"], list):
                glacier["vaults"] = [
                    {**v, "retention_days": retention_val} for v in glacier["vaults"]
                ]
        except ValueError:
            raise ValueError("GLACIER_RETENTION_DAYS must be an integer")

    if os.getenv("GLACIER_INVENTORY_FILE"):
        glacier["inventory_file"] = os.getenv("GLACIER_INVENTORY_FILE")

    if os.getenv("GLACIER_DRY_RUN"):
        delete_cfg["dry_run"] = os.getenv("GLACIER_DRY_RUN").lower() != "false"

    if os.getenv("LOG_LEVEL"):
        logging_cfg["level"] = os.getenv("LOG_LEVEL")

    return data


def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    """Load config from YAML, overlay .env/env vars, and validate."""
    load_dotenv(DEFAULT_ENV_PATH, override=False)

    data: Dict[str, Any] = {}
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f) or {}
            if not isinstance(yaml_data, dict):
                raise ValueError("Config YAML must define a mapping at the root")
            data.update(yaml_data)

    data = _apply_env_overrides(data)

    try:
        return AppConfig.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid configuration: {exc}") from exc


def assume_role_session(base_session: boto3.Session, role_arn: str, region: str) -> boto3.Session:
    sts = base_session.client("sts", region_name=region)
    resp = sts.assume_role(RoleArn=role_arn, RoleSessionName="glacier-prune")
    creds = resp["Credentials"]
    return boto3.Session(
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
        region_name=region,
    )


def build_boto3_session(cfg: AWSConfig) -> boto3.Session:
    base = (
        boto3.Session(profile_name=cfg.profile, region_name=cfg.region)
        if cfg.profile
        else boto3.Session(region_name=cfg.region)
    )
    if cfg.role_arn:
        return assume_role_session(base, cfg.role_arn, cfg.region)
    return base
