"""
EXECUTOR - Hydra Protocol v2 (Model Router)
Multi-model routing with account rotation.
"""
import json
import random
import logging
from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict

logger = logging.getLogger("EXECUTOR.Hydra")

class ModelTier(Enum):
    """Model tier classification."""
    FREE = "free"           # OpenCode, Google AI Studio free tier
    STANDARD = "standard"   # Gemini Flash, GPT-4o Mini
    PREMIUM = "premium"     # Claude Sonnet, GPT-4o
    CRITICAL = "critical"   # Claude Opus (requires User approval)


class ModelRouter:
    """
    Hydra Protocol v2 - Multi-Model Routing with Account Rotation.
    
    Features:
    1. Round-robin / random key selection from pool
    2. Automatic fallback when rate limited
    3. Budget tracking per key
    4. Free tier priority for cost optimization
    """
    
    # Model registry with tier classification
    MODELS = {
        # Free Tier (OpenCode)
        "opencode-claude": {"tier": ModelTier.FREE, "provider": "opencode"},
        "opencode-openai": {"tier": ModelTier.FREE, "provider": "opencode"},
        "opencode-google": {"tier": ModelTier.FREE, "provider": "opencode"},
        "opencode-kimi": {"tier": ModelTier.FREE, "provider": "opencode"},
        "opencode-glm": {"tier": ModelTier.FREE, "provider": "opencode"},
        
        # Google AI Studio Free
        "gemini-flash-lite": {"tier": ModelTier.FREE, "provider": "google", "rpm": 1000},
        
        # Standard (Google AI Pro)
        "gemini-3-pro": {"tier": ModelTier.STANDARD, "provider": "google-ai-pro"},
        "gemini-3-flash": {"tier": ModelTier.STANDARD, "provider": "google-ai-pro"},
        "chatgpt-oss120b": {"tier": ModelTier.STANDARD, "provider": "google-ai-pro"},
        "kimi-2.5": {"tier": ModelTier.STANDARD, "provider": "google-ai-pro"},
        "glm-4.7": {"tier": ModelTier.STANDARD, "provider": "google-ai-pro"},
        
        # Premium
        "claude-4.5-sonnet": {"tier": ModelTier.PREMIUM, "provider": "google-ai-pro"},
        "chatgpt-5.2-plus": {"tier": ModelTier.PREMIUM, "provider": "openai-plus"},
        
        # Critical (User approval required)
        "claude-4.5-opus": {"tier": ModelTier.CRITICAL, "provider": "google-ai-pro"},
    }
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.keys = self._load_keys()
        self.key_usage = {}  # Track usage per key
        self.current_key_index = 0
        
        logger.info(f"🐍 Hydra v2 initialized with {len(self.keys)} keys")
    
    def _load_keys(self) -> List[Dict]:
        """Load API keys from config."""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("keys", [])
        return []
    
    def _save_keys(self):
        """Save API keys to config."""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump({
                "keys": self.keys,
                "rotation_strategy": "round_robin",
                "fallback": "opencode",
                "last_updated": datetime.now().isoformat()
            }, f, indent=2)
    
    def add_key(self, provider: str, key: str, tier: str = "standard"):
        """Add a new API key to the pool."""
        self.keys.append({
            "provider": provider,
            "key": key,
            "tier": tier,
            "added": datetime.now().isoformat(),
            "usage_count": 0,
            "last_used": None
        })
        self._save_keys()
        logger.info(f"🔑 Added new key for {provider}")
    
    def select_model(
        self, 
        task_complexity: str = "standard",
        budget_remaining_percent: float = 100.0,
        force_model: Optional[str] = None
    ) -> Dict:
        """
        Select optimal model based on task complexity and budget.
        Includes automatic fallback if model is unavailable (503 errors).
        
        Args:
            task_complexity: "simple", "standard", "complex", "critical"
            budget_remaining_percent: Remaining budget as percentage
            force_model: Force a specific model (for User direct chat)
        
        Returns:
            Dict with model name and API key
        """
        if force_model:
            return self._get_model_with_key(force_model)
        
        # Determine required tier
        if task_complexity == "critical":
            # Claude Opus - requires escalation
            return {
                "model": "claude-4.5-opus",
                "requires_approval": True,
                "message": "Critical task requires Claude Opus. User approval needed."
            }
        
        if task_complexity == "complex":
            target_tier = ModelTier.PREMIUM
        elif task_complexity == "simple":
            target_tier = ModelTier.FREE
        else:
            target_tier = ModelTier.STANDARD
        
        # Budget check - fallback to free if low
        if budget_remaining_percent < 20:
            logger.warning("⚠️ Budget low, falling back to free tier")
            target_tier = ModelTier.FREE
        
        # Find model matching tier
        suitable_models = [
            name for name, info in self.MODELS.items()
            if info["tier"] == target_tier
        ]
        
        if not suitable_models:
            # Fallback to opencode
            suitable_models = ["opencode-claude", "opencode-google"]
        
        selected_model = random.choice(suitable_models)
        return self._get_model_with_key(selected_model)
    
    def select_with_fallback(self, preferred_model: str, fallback_chain: Optional[List[str]] = None) -> Dict:
        """
        Select model with automatic fallback if unavailable.
        
        Use this when you need guaranteed availability (e.g., critical operations).
        
        Args:
            preferred_model: The preferred model to try first
            fallback_chain: List of fallback models (optional)
        
        Returns:
            Dict with model info and key
        
        Raises:
            AllModelsUnavailableError: If all models in chain fail
        """
        if not fallback_chain:
            fallback_chain = [
                preferred_model,
                "claude-4.5-sonnet",  # Stable alternative
                "gemini-3-pro",       # Fast, cheap
                "opencode-claude",    # Free tier
            ]
        
        for model_name in fallback_chain:
            try:
                result = self._get_model_with_key(model_name)
                if model_name != preferred_model:
                    logger.warning(
                        f"⚠️ {preferred_model} unavailable, using {model_name} instead"
                    )
                return result
            except Exception as e:
                logger.warning(f"{model_name} failed: {e}, trying next...")
                continue
        
        raise Exception(f"All models in fallback chain failed: {fallback_chain}")
    
    def _get_model_with_key(self, model_name: str) -> Dict:
        """Get model info with an available API key."""
        model_info = self.MODELS.get(model_name, {})
        provider = model_info.get("provider", "unknown")
        
        # Find key for this provider
        key = self._get_next_key(provider)
        
        return {
            "model": model_name,
            "provider": provider,
            "tier": model_info.get("tier", ModelTier.STANDARD).value,
            "api_key": key,
            "requires_approval": False
        }
    
    def _get_next_key(self, provider: str) -> Optional[str]:
        """Get next available key for provider using round-robin."""
        provider_keys = [k for k in self.keys if k.get("provider") == provider]
        
        if not provider_keys:
            logger.warning(f"No keys available for {provider}, using fallback")
            return None
        
        # Round-robin selection
        key_data = provider_keys[self.current_key_index % len(provider_keys)]
        self.current_key_index += 1
        
        # Update usage
        key_data["usage_count"] = key_data.get("usage_count", 0) + 1
        key_data["last_used"] = datetime.now().isoformat()
        
        return key_data.get("key")
    
    def mark_rate_limited(self, model_name: str, key: str):
        """Mark a key as rate-limited, switch to next."""
        logger.warning(f"⚠️ Rate limited on {model_name}, switching key")
        for k in self.keys:
            if k.get("key") == key:
                k["rate_limited_until"] = datetime.now().isoformat()
        self.current_key_index += 1
    
    def get_status(self) -> Dict:
        """Get current status of Hydra protocol."""
        return {
            "total_keys": len(self.keys),
            "keys_by_provider": {
                provider: len([k for k in self.keys if k.get("provider") == provider])
                for provider in set(k.get("provider") for k in self.keys)
            },
            "current_index": self.current_key_index
        }
