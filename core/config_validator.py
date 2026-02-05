"""
EXECUTOR - Config Validation
Validates all configuration files on startup using Pydantic.
"""
from pydantic import BaseModel, Field, field_validator
from pathlib import Path
import json
import logging
from typing import Optional

logger = logging.getLogger("EXECUTOR.ConfigValidator")

class TelegramConfig(BaseModel):
    """Telegram notification configuration."""
    enabled: bool
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    
    @field_validator('bot_token')
    @classmethod
    def validate_bot_token(cls, v, info):
        if info.data.get('enabled') and not v:
            raise ValueError("bot_token required when Telegram enabled")
        if v and v == "PLACEHOLDER_TELEGRAM_BOT_TOKEN":
            raise ValueError("Please replace PLACEHOLDER_TELEGRAM_BOT_TOKEN with real token")
        return v
    
    @field_validator('chat_id')
    @classmethod
    def validate_chat_id(cls, v, info):
        if info.data.get('enabled') and not v:
            raise ValueError("chat_id required when Telegram enabled")
        return v


class DiscordConfig(BaseModel):
    """Discord notification configuration."""
    enabled: bool
    webhook_url: Optional[str] = None
    
    @field_validator('webhook_url')
    @classmethod
    def validate_webhook(cls, v, info):
        if info.data.get('enabled') and not v:
            raise ValueError("webhook_url required when Discord enabled")
        if v and v == "PLACEHOLDER_DISCORD_WEBHOOK_URL":
            raise ValueError("Please replace PLACEHOLDER_DISCORD_WEBHOOK_URL with real URL")
        return v


class NotificationConfig(BaseModel):
    """Complete notification configuration."""
    telegram: TelegramConfig
    discord: DiscordConfig


class HydraKey(BaseModel):
    """Single API key in Hydra pool."""
    provider: str = Field(..., pattern="^[a-z0-9-]+$")
    key: str = Field(..., min_length=10)
    tier: str = Field(default="standard", pattern="^(free|standard|premium|critical)$")
    usage_count: int = Field(default=0, ge=0)
    last_used: Optional[str] = None
    rate_limited_until: Optional[str] = None


class HydraConfig(BaseModel):
    """Hydra v2 multi-account configuration."""
    keys: list[HydraKey]
    rotation_strategy: str = Field(default="round_robin", pattern="^(round_robin|random)$")
    fallback: str = Field(default="opencode")
    last_updated: Optional[str] = None


class FleetAgent(BaseModel):
    """Single fleet agent registration."""
    id: str = Field(..., pattern="^[a-z0-9-]+$")
    name: str
    type: str = Field(..., pattern="^(infrastructure|project)$")
    status: str = Field(default="online", pattern="^(online|offline|error)$")
    last_step: Optional[str] = None


class FleetRegistry(BaseModel):
    """Fleet agent registry."""
    agents: list[FleetAgent] = Field(default_factory=list)


class MCPClient(BaseModel):
    """External MCP client connection."""
    name: str
    url: str
    enabled: bool = False
    description: Optional[str] = None


class MCPClientsConfig(BaseModel):
    """MCP clients configuration."""
    clients: list[MCPClient] = Field(default_factory=list)


def validate_all_configs(config_dir: Path) -> dict[str, str]:
    """
    Validate all configuration files.
    
    Args:
        config_dir: Directory containing config files
    
    Returns:
        Dict of {filename: error_message}, empty if all valid
    """
    errors = {}
    
    # Validate notification.json
    notification_path = config_dir / "notification.json"
    if notification_path.exists():
        try:
            with open(notification_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            NotificationConfig(**data)
            logger.debug("✅ notification.json valid")
        except Exception as e:
            errors["notification.json"] = str(e)
            logger.error(f"❌ notification.json: {e}")
    else:
        logger.warning("⚠️ notification.json not found (optional)")
    
    # Validate hydra_keys.json
    hydra_path = config_dir / "hydra_keys.json"
    if hydra_path.exists():
        try:
            with open(hydra_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            HydraConfig(**data)
            logger.debug("✅ hydra_keys.json valid")
        except Exception as e:
            errors["hydra_keys.json"] = str(e)
            logger.error(f"❌ hydra_keys.json: {e}")
    else:
        logger.warning("⚠️ hydra_keys.json not found (will use defaults)")
    
    # Validate fleet_registry.json
    fleet_path = config_dir / "fleet_registry.json"
    if fleet_path.exists():
        try:
            with open(fleet_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            FleetRegistry(**data)
            logger.debug("✅ fleet_registry.json valid")
        except Exception as e:
            errors["fleet_registry.json"] = str(e)
            logger.error(f"❌ fleet_registry.json: {e}")
    else:
        logger.warning("⚠️ fleet_registry.json not found (optional)")
    
    # Validate mcp_clients.json
    mcp_path = config_dir / "mcp_clients.json"
    if mcp_path.exists():
        try:
            with open(mcp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            MCPClientsConfig(**data)
            logger.debug("✅ mcp_clients.json valid")
        except Exception as e:
            errors["mcp_clients.json"] = str(e)
            logger.error(f"❌ mcp_clients.json: {e}")
    else:
        logger.warning("⚠️ mcp_clients.json not found (optional)")
    
    return errors


def validate_or_exit(config_dir: Path):
    """
    Validate configs and exit if any errors.
    
    This should be called early in EXECUTOR startup.
    """
    logger.info("🔍 Validating configuration files...")
    
    errors = validate_all_configs(config_dir)
    
    if errors:
        logger.error("❌ Configuration validation FAILED:")
        for file, error in errors.items():
            logger.error(f"   📄 {file}:")
            logger.error(f"      {error}")
        
        logger.error("")
        logger.error("💡 Fix the errors above and restart EXECUTOR.")
        raise SystemExit(1)
    
    logger.info("✅ All configurations valid")
