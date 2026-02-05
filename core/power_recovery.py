"""
EXECUTOR - Power Recovery Module
Handles system recovery after power outage.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger("EXECUTOR.PowerRecovery")

class PowerRecovery:
    """
    Power Recovery Protocol.
    
    When system restarts after power outage:
    1. Check all agents' status
    2. Read last checkpoint from each agent
    3. Resume from last known good state
    4. Report status to User via Telegram + Discord
    """
    
    def __init__(self, state_dir: Path, fleet_registry: Dict):
        self.state_dir = state_dir
        self.fleet_registry = fleet_registry
        self.last_state_file = state_dir / "last_state.json"
        
        logger.info("⚡ Power Recovery module initialized")
    
    def save_checkpoint(self, agent_id: str, step: int, status: str, data: Optional[Dict] = None):
        """
        Save checkpoint for an agent.
        Called periodically to enable recovery.
        """
        checkpoint_file = self.state_dir / f"{agent_id}_checkpoint.json"
        
        checkpoint = {
            "agent_id": agent_id,
            "step": step,
            "status": status,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        }
        
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"💾 Checkpoint saved for {agent_id} at step {step}")
    
    def load_checkpoint(self, agent_id: str) -> Optional[Dict]:
        """Load last checkpoint for an agent."""
        checkpoint_file = self.state_dir / f"{agent_id}_checkpoint.json"
        
        if checkpoint_file.exists():
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def detect_interruption(self) -> bool:
        """
        Detect if system was interrupted (power outage).
        Returns True if recovery is needed.
        """
        if not self.last_state_file.exists():
            return False
        
        with open(self.last_state_file, 'r', encoding='utf-8') as f:
            last_state = json.load(f)
        
        return last_state.get("status") == "running"
    
    def mark_running(self):
        """Mark system as running (called on startup)."""
        state = {
            "status": "running",
            "started_at": datetime.now().isoformat()
        }
        with open(self.last_state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    
    def mark_shutdown(self):
        """Mark system as cleanly shutdown."""
        state = {
            "status": "stopped",
            "stopped_at": datetime.now().isoformat()
        }
        with open(self.last_state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    
    async def recover(self) -> Dict:
        """
        Perform full system recovery.
        
        Returns:
            Recovery report with agent statuses and actions needed.
        """
        logger.info("🔄 POWER RECOVERY: Starting system scan...")
        
        report = {
            "recovery_started": datetime.now().isoformat(),
            "agents": [],
            "actions_needed": [],
            "summary": ""
        }
        
        agents_online = 0
        agents_offline = 0
        agents_resuming = 0
        
        for agent in self.fleet_registry.get("agents", []):
            agent_id = agent.get("id")
            agent_name = agent.get("name")
            
            # Check agent status
            is_online = await self._ping_agent(agent)
            
            # Load checkpoint
            checkpoint = self.load_checkpoint(agent_id)
            
            agent_status = {
                "id": agent_id,
                "name": agent_name,
                "online": is_online,
                "last_checkpoint": checkpoint
            }
            
            if is_online:
                if checkpoint and checkpoint.get("status") == "in_progress":
                    agent_status["action"] = "resume"
                    agent_status["resume_from_step"] = checkpoint.get("step")
                    agents_resuming += 1
                    report["actions_needed"].append(
                        f"Resume {agent_name} from step {checkpoint.get('step')}"
                    )
                else:
                    agent_status["action"] = "idle"
                agents_online += 1
            else:
                agent_status["action"] = "restart_required"
                agents_offline += 1
                report["actions_needed"].append(
                    f"⚠️ Agent {agent_name} is OFFLINE - restart required"
                )
            
            report["agents"].append(agent_status)
        
        # Summary
        report["summary"] = (
            f"Online: {agents_online}, Offline: {agents_offline}, "
            f"Resuming: {agents_resuming}"
        )
        report["recovery_completed"] = datetime.now().isoformat()
        
        logger.info(f"🔄 Recovery complete: {report['summary']}")
        
        return report
    
    async def _ping_agent(self, agent: Dict) -> bool:
        """
        Ping an agent to check if it's online.
        
        TODO: Implement actual ping via MCP/HTTP based on agent type.
        """
        # For now, assume all agents are online (placeholder)
        return True
    
    def format_recovery_report(self, report: Dict) -> str:
        """Format recovery report for notification."""
        lines = [
            "## 🔄 HỆ THỐNG KHỞI ĐỘNG LẠI",
            "",
            f"**Thời gian bắt đầu**: {report['recovery_started']}",
            f"**Tổng kết**: {report['summary']}",
            "",
            "### Trạng Thái Agents",
            "",
            "| Agent | Online | Action | Last Step |",
            "|-------|--------|--------|-----------|",
        ]
        
        for agent in report["agents"]:
            online_emoji = "✅" if agent["online"] else "❌"
            last_step = agent.get("resume_from_step", "-")
            lines.append(
                f"| {agent['name']} | {online_emoji} | {agent['action']} | {last_step} |"
            )
        
        if report["actions_needed"]:
            lines.append("")
            lines.append("### ⚠️ Hành Động Cần Thiết")
            for action in report["actions_needed"]:
                lines.append(f"- {action}")
        
        return "\n".join(lines)
