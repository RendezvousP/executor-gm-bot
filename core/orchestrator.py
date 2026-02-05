"""
EXECUTOR - The General Manager
Core Orchestrator for Antigravity Fleet
"""
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime

from .notifications import NotificationSystem
from .task_queue import TaskQueue, TaskPriority, TaskStatus
from .power_recovery import PowerRecovery
from .model_router import ModelRouter
from .skill_injector import SkillInjector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("EXECUTOR")

# Paths
BASE_DIR = Path(__file__).parent.parent  # Go up from core/ to executor/
CONFIG_DIR = BASE_DIR / "config"
STATE_DIR = BASE_DIR / "state"
SKILLS_DIR = BASE_DIR / "skills" / "cache"  # Updated: use local cache

class Executor:
    """
    The Central Orchestrator - Named after Vader's Flagship.
    
    Responsibilities:
    1. Fleet Coordination - Assign tasks to agents
    2. Skill Inheritance - Inject skills to child agents
    3. Model Routing - Hydra v2 protocol
    4. Power Recovery - Resume after outage
    5. Escalation - Ask User for critical decisions
    """
    
    def __init__(self):
        # Ensure directories exist
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        # CRITICAL: Validate configs before proceeding
        from .config_validator import validate_or_exit
        validate_or_exit(CONFIG_DIR)
        
        # Load configs
        self.fleet_registry = self._load_config("fleet_registry.json")
        self.hydra_config = self._load_config("hydra_keys.json")
        
        # Initialize subsystems
        self.notifications = NotificationSystem(CONFIG_DIR / "notification.json")
        self.task_queue = TaskQueue(STATE_DIR / "task_queue.db")
        self.power_recovery = PowerRecovery(STATE_DIR, self.fleet_registry)
        self.model_router = ModelRouter(CONFIG_DIR / "hydra_keys.json")
        self.skill_injector = SkillInjector(SKILLS_DIR, BASE_DIR / "rules")
        
        # MCP clients (connect to external MCP servers)
        from mcp.client import MCPClientManager
        self.mcp_clients = MCPClientManager(CONFIG_DIR / "mcp_clients.json")
        
        # State
        self.current_step = self._load_state("current_step.json")
        
        # MCP server instance (will be set if running as MCP server)
        self.mcp_server = None
        
        logger.info("🛡️ EXECUTOR initialized")
        logger.info(f"   Fleet agents: {len(self.fleet_registry.get('agents', []))}")
        logger.info(f"   Pending tasks: {self.task_queue.get_pending_count()}")
    
    def _load_config(self, filename: str) -> dict:
        """Load configuration file."""
        config_path = CONFIG_DIR / filename
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_config(self, filename: str, data: dict):
        """Save configuration file."""
        config_path = CONFIG_DIR / filename
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load_state(self, filename: str) -> dict:
        """Load state file."""
        state_path = STATE_DIR / filename
        if state_path.exists():
            with open(state_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"step": 0, "status": "idle", "last_updated": None}
    
    def _save_state(self, filename: str, data: dict):
        """Save state file."""
        state_path = STATE_DIR / filename
        data["last_updated"] = datetime.now().isoformat()
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    async def power_recovery_check(self):
        """
        Called after power outage / system restart.
        Scans all agents, checks their status, and reports to User.
        """
        logger.info("🔄 POWER RECOVERY: Scanning fleet status...")
        
        # Use PowerRecovery module
        report = await self.power_recovery.recover()
        
        # Send notification via NotificationSystem
        await self.notifications.send_recovery_report(report)
        
        return report
    
    async def _ping_agent(self, agent: dict) -> str:
        """Ping an agent to check if it's online."""
        # TODO: Implement actual ping via MCP/HTTP
        # For now, return online (no agents deployed yet)
        return "online"
    
    def _format_recovery_report(self, report: dict) -> str:
        """Format recovery report for notification."""
        lines = [
            f"**Thời gian**: {report['timestamp']}",
            "",
            "**Trạng thái Agents**:",
        ]
        
        for agent in report["agents"]:
            status_emoji = "✅" if agent["status"] == "online" else "❌"
            lines.append(f"- {status_emoji} {agent['name']}: {agent['status']}")
        
        if report["action_required"]:
            lines.append("")
            lines.append("**⚠️ Cần xử lý**:")
            for action in report["action_required"]:
                lines.append(f"- {action}")
        
        return "\n".join(lines)
    
    async def ask_user_multi_account(self) -> bool:
        """
        REQUIRED: Ask User if they have multi-account available.
        Must be called before starting any new project.
        """
        await self.notifications.send(
            title="🤖 EXECUTOR: CẦN XÁC NHẬN",
            message="""**Câu hỏi cho User**:
1. Ông có multi-account API keys không?
2. Nếu có, xin cung cấp danh sách keys.
3. Vẫn sử dụng OpenCode hay nguồn khác cho free tier?

Xin trả lời để con tiếp tục.""",
            priority="critical"
        )
        # In real implementation, this would wait for User response
        return True
    
    async def run(self):
        """Main execution loop."""
        logger.info("🚀 EXECUTOR starting...")
        
        # Check if this is a recovery from power outage
        if self.current_step.get("status") == "interrupted":
            await self.power_recovery_check()
        
        # Main loop
        while True:
            # TODO: Implement task queue processing
            await asyncio.sleep(60)  # Heartbeat


# Entry point
if __name__ == "__main__":
    executor = Executor()
    asyncio.run(executor.run())
