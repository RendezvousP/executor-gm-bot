"""
EXECUTOR - Notification System
Sends notifications via Telegram and Discord simultaneously.
"""
import logging
import asyncio
from pathlib import Path
from typing import Optional
import json

logger = logging.getLogger("EXECUTOR.Notifications")

class NotificationSystem:
    """
    Dual-channel notification system.
    Sends messages to both Telegram and Discord simultaneously.
    """
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Import telegram/discord libs only if needed
        self.telegram_bot = None
        self.discord_webhook = None
        
        self._init_telegram()
        self._init_discord()
        
        logger.info("📢 Notification system initialized")
        logger.info(f"   Telegram: {'ON' if self.config.get('telegram', {}).get('enabled') else 'OFF'}")
        logger.info(f"   Discord: {'ON' if self.config.get('discord', {}).get('enabled') else 'OFF'}")
    
    def _load_config(self) -> dict:
        """Load notification config."""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _init_telegram(self):
        """Initialize Telegram bot if enabled."""
        tg_config = self.config.get("telegram", {})
        if not tg_config.get("enabled"):
            return
        
        try:
            from telegram import Bot
            bot_token = tg_config.get("bot_token")
            if bot_token and bot_token != "PLACEHOLDER_TELEGRAM_BOT_TOKEN":
                self.telegram_bot = Bot(token=bot_token)
                logger.info("✅ Telegram bot initialized")
            else:
                logger.warning("⚠️ Telegram enabled but no valid token")
        except ImportError:
            logger.error("❌ python-telegram-bot not installed. Run: pip install python-telegram-bot")
        except Exception as e:
            logger.error(f"❌ Telegram init failed: {e}")
    
    def _init_discord(self):
        """Initialize Discord webhook if enabled."""
        dc_config = self.config.get("discord", {})
        if not dc_config.get("enabled"):
            return
        
        webhook_url = dc_config.get("webhook_url")
        if webhook_url and webhook_url != "PLACEHOLDER_DISCORD_WEBHOOK_URL":
            self.discord_webhook = webhook_url
            logger.info("✅ Discord webhook initialized")
        else:
            logger.warning("⚠️ Discord enabled but no valid webhook URL")
    
    async def send(self, title: str, message: str, priority: str = "info"):
        """
        Send notification to all enabled channels.
        
        Args:
            title: Notification title
            message: Notification body (supports Markdown)
            priority: "info", "warning", "critical"
        """
        # Add emoji based on priority
        emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "🚨"
        }.get(priority, "📢")
        
        full_message = f"{emoji} **{title}**\n\n{message}"
        
        # Send to both channels concurrently
        tasks = []
        if self.telegram_bot:
            tasks.append(self._send_telegram(full_message))
        if self.discord_webhook:
            tasks.append(self._send_discord(full_message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            logger.warning("No notification channels configured")
    
    async def _send_telegram(self, message: str):
        """Send to Telegram."""
        try:
            chat_id = self.config.get("telegram", {}).get("chat_id")
            if not chat_id:
                logger.error("Telegram chat_id not configured")
                return
            
            await self.telegram_bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown"
            )
            logger.debug("✅ Sent to Telegram")
        except Exception as e:
            logger.error(f"❌ Telegram send failed: {e}")
    
    async def _send_discord(self, message: str):
        """Send to Discord via webhook."""
        try:
            import httpx
            
            payload = {
                "content": message,
                "username": "EXECUTOR GM BOT"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.discord_webhook,
                    json=payload,
                    timeout=10
                )
                response.raise_for_status()
            
            logger.debug("✅ Sent to Discord")
        except ImportError:
            logger.error("❌ httpx not installed. Run: pip install httpx")
        except Exception as e:
            logger.error(f"❌ Discord send failed: {e}")
    
    async def send_recovery_report(self, report: dict):
        """Send power recovery report."""
        await self.send(
            title="🔄 HỆ THỐNG KHỞI ĐỘNG LẠI",
            message=self._format_recovery_report(report),
            priority="warning"
        )
    
    async def send_escalation(self, issue: str, options: list):
        """Send escalation to User for decision."""
        message_parts = [
            f"**Vấn đề**: {issue}",
            "",
            "**Lựa chọn**:"
        ]
        for i, option in enumerate(options, 1):
            message_parts.append(f"{i}. {option}")
        
        await self.send(
            title="🤖 EXECUTOR CẦN QUYẾT ĐỊNH",
            message="\n".join(message_parts),
            priority="critical"
        )
    
    def _format_recovery_report(self, report: dict) -> str:
        """Format recovery report for notification."""
        lines = [
            f"**Thời gian**: {report.get('recovery_started', 'N/A')}",
            f"**Tổng kết**: {report.get('summary', 'N/A')}",
            "",
            "**Agents**:"
        ]
        
        for agent in report.get("agents", []):
            status_emoji = "✅" if agent.get("online") else "❌"
            lines.append(f"• {status_emoji} {agent.get('name')}: {agent.get('action')}")
        
        if report.get("actions_needed"):
            lines.append("")
            lines.append("**⚠️ Cần xử lý**:")
            for action in report["actions_needed"]:
                lines.append(f"• {action}")
        
        return "\n".join(lines)
