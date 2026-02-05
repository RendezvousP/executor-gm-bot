"""
EXECUTOR - Skill Injector
Injects appropriate skills to child agents based on their role.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger("EXECUTOR.SkillInjector")

class SkillInjector:
    """
    Skill Inheritance Engine.
    
    EXECUTOR (GM BOT) inherits ALL skills.
    Child agents receive a subset based on their role.
    """
    
    # Role to skills mapping
    ROLE_SKILLS = {
        "pm_agent": [
            "openspec",
            "writing-plans",
            "pricing-strategy",
            "marketing-ideas",
            "brainstorming",
        ],
        "architect_agent": [
            "mcp-builder",
            "mermaid-diagrams",
            "supabase-postgres-best-practices",
            "next-best-practices",
            "writing-plans",
        ],
        "coder_agent": [
            "vercel-react-best-practices",
            "next-best-practices",
            "vue-best-practices",
            "test-driven-development",
            "systematic-debugging",
            "commit-work",
        ],
        "qa_agent": [
            "qa-test-planner",
            "webapp-testing",
            "systematic-debugging",
        ],
        "network_agent": [
            "systematic-debugging",
            # mikrotik_architect is custom, loaded separately
        ],
        "proxmox_agent": [
            "mcp-builder",
            "systematic-debugging",
        ],
        "deep_search_agent": [
            "brainstorming",
            "writing-clearly-and-concisely",
        ],
    }
    
    # Core rules that ALL agents must follow
    CORE_RULES = [
        "CORE_PROTOCOL.md",
    ]
    
    # Additional rules per role
    ROLE_RULES = {
        "pm_agent": ["metagpt-sop"],
        "architect_agent": ["metagpt-sop"],
        "coder_agent": ["metagpt-sop"],
        "qa_agent": [],
        "network_agent": [],
        "proxmox_agent": [],
        "deep_search_agent": [],
    }
    
    def __init__(self, skills_dir: Path, rules_dir: Path):
        self.skills_dir = skills_dir
        self.rules_dir = rules_dir
        self.available_skills = self._scan_skills()
        
        logger.info(f"💉 Skill Injector initialized with {len(self.available_skills)} skills")
    
    def _scan_skills(self) -> List[str]:
        """Scan available skills in skills directory."""
        skills = []
        if self.skills_dir.exists():
            for skill_dir in self.skills_dir.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    skills.append(skill_dir.name)
        return skills
    
    def get_skills_for_role(self, role: str) -> List[str]:
        """Get list of skills for a given role."""
        required_skills = self.ROLE_SKILLS.get(role, [])
        
        # Filter to only available skills
        available = [s for s in required_skills if s in self.available_skills]
        missing = [s for s in required_skills if s not in self.available_skills]
        
        if missing:
            logger.warning(f"⚠️ Missing skills for {role}: {missing}")
        
        return available
    
    def get_rules_for_role(self, role: str) -> List[str]:
        """Get list of rules for a given role."""
        rules = self.CORE_RULES.copy()
        rules.extend(self.ROLE_RULES.get(role, []))
        return rules
    
    def load_skill_content(self, skill_name: str) -> Optional[str]:
        """Load content of a skill file."""
        skill_path = self.skills_dir / skill_name / "SKILL.md"
        if skill_path.exists():
            with open(skill_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def load_rule_content(self, rule_name: str) -> Optional[str]:
        """Load content of a rule file."""
        rule_path = self.rules_dir / rule_name
        if rule_path.exists():
            with open(rule_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def generate_system_prompt(self, role: str, project_context: str = "") -> str:
        """
        Generate complete system prompt for an agent.
        
        Includes:
        1. Role-specific skills
        2. Core rules (CORE_PROTOCOL)
        3. Role-specific rules
        4. Project context
        """
        prompt_parts = []
        
        # Header
        prompt_parts.append(f"# AGENT ROLE: {role.upper()}")
        prompt_parts.append("")
        
        # Core Rules
        prompt_parts.append("## CORE RULES (MANDATORY)")
        for rule in self.CORE_RULES:
            content = self.load_rule_content(rule)
            if content:
                prompt_parts.append(content)
        prompt_parts.append("")
        
        # Role-specific rules
        role_rules = self.ROLE_RULES.get(role, [])
        if role_rules:
            prompt_parts.append("## ROLE-SPECIFIC RULES")
            for rule in role_rules:
                content = self.load_skill_content(rule)  # Skills can also be rules
                if content:
                    prompt_parts.append(f"### {rule}")
                    prompt_parts.append(content)
        prompt_parts.append("")
        
        # Skills
        prompt_parts.append("## SKILLS")
        for skill in self.get_skills_for_role(role):
            content = self.load_skill_content(skill)
            if content:
                prompt_parts.append(f"### {skill}")
                # Only include the first 500 chars to avoid token bloat
                prompt_parts.append(content[:500] + "..." if len(content) > 500 else content)
        prompt_parts.append("")
        
        # Project context
        if project_context:
            prompt_parts.append("## PROJECT CONTEXT")
            prompt_parts.append(project_context)
        
        return "\n".join(prompt_parts)
    
    def inject_to_agent(self, agent_config: Dict, role: str, project_context: str = "") -> Dict:
        """
        Inject skills and rules into agent configuration.
        
        Returns updated agent config with system_prompt.
        """
        system_prompt = self.generate_system_prompt(role, project_context)
        
        agent_config["system_prompt"] = system_prompt
        agent_config["skills"] = self.get_skills_for_role(role)
        agent_config["rules"] = self.get_rules_for_role(role)
        agent_config["role"] = role
        
        logger.info(f"💉 Injected {len(agent_config['skills'])} skills into {role}")
        
        return agent_config
