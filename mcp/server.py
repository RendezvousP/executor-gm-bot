"""
EXECUTOR - MCP Server
Exposes EXECUTOR functionality as MCP tools.
"""
from fastmcp import FastMCP
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("EXECUTOR.MCP.Server")

# Will be set by main
executor_instance = None

mcp = FastMCP("EXECUTOR GM BOT")

def init_mcp_server(executor):
    """Initialize MCP server with EXECUTOR instance."""
    global executor_instance
    executor_instance = executor
    logger.info("🔌 MCP Server initialized")


@mcp.tool()
async def submit_task(
    name: str,
    description: str,
    priority: str = "normal",
    assigned_to: Optional[str] = None
) -> dict:
    """
    Submit a new task to EXECUTOR's queue.
    
    Args:
        name: Task name/title
        description: Detailed task description
        priority: Task priority (low, normal, high, critical)
        assigned_to: Optional agent ID to assign task to
    
    Returns:
        Task ID and status
    """
    if not executor_instance:
        return {"error": "EXECUTOR not initialized"}
    
    # Map priority string to enum
    from core.task_queue import TaskPriority
    priority_map = {
        "low": TaskPriority.LOW,
        "normal": TaskPriority.NORMAL,
        "high": TaskPriority.HIGH,
        "critical": TaskPriority.CRITICAL
    }
    
    task_priority = priority_map.get(priority, TaskPriority.NORMAL)
    
    # Add to queue
    task_id = executor_instance.task_queue.add_task(
        name=name,
        description=description,
        priority=task_priority,
        assigned_to=assigned_to
    )
    
    logger.info(f"📨 Task submitted: {name} (ID: {task_id})")
    
    return {
        "task_id": task_id,
        "name": name,
        "priority": priority,
        "status": "pending"
    }


@mcp.tool()
async def get_task_status(task_id: int) -> dict:
    """
    Get status of a task.
    
    Args:
        task_id: Task ID to query
    
    Returns:
        Task details with current status
    """
    if not executor_instance:
        return {"error": "EXECUTOR not initialized"}
    
    task = executor_instance.task_queue.get_task(task_id)
    
    if not task:
        return {"error": f"Task {task_id} not found"}
    
    return task


@mcp.tool()
async def get_fleet_status() -> dict:
    """
    Get health status of all agents in the fleet.
    
    Returns:
        List of agents with online/offline status
    """
    if not executor_instance:
        return {"error": "EXECUTOR not initialized"}
    
    agents = executor_instance.fleet_registry.get("agents", [])
    
    return {
        "total_agents": len(agents),
        "agents": agents,
        "timestamp": executor_instance.power_recovery.get_timestamp()
    }


@mcp.tool()
async def add_api_key(
    provider: str,
    key: str,
    tier: str = "standard"
) -> dict:
    """
    Add API key to Hydra v2 pool.
    
    Args:
        provider: Provider name (e.g., google-ai-pro, openai)
        key: API key
        tier: Key tier (free, standard, premium, critical)
    
    Returns:
        Confirmation with total key count
    """
    if not executor_instance:
        return {"error": "EXECUTOR not initialized"}
    
    # Add key to model router
    executor_instance.model_router.add_key(provider, key, tier)
    
    logger.info(f"🔑 Added API key for {provider} (tier: {tier})")
    
    total_keys = len(executor_instance.hydra_config.get("keys", []))
    
    return {
        "success": True,
        "provider": provider,
        "tier": tier,
        "total_keys": total_keys
    }


@mcp.tool()
async def select_model(
    task_complexity: str = "standard",
    force_model: Optional[str] = None
) -> dict:
    """
    Get recommended model for a task.
    
    Args:
        task_complexity: Task complexity (simple, standard, complex, critical)
        force_model: Force specific model (optional)
    
    Returns:
        Model name and API key
    """
    if not executor_instance:
        return {"error": "EXECUTOR not initialized"}
    
    model_info = executor_instance.model_router.select_model(
        task_complexity=task_complexity,
        force_model=force_model
    )
    
    return model_info


@mcp.tool()
async def escalate_decision(
    issue: str,
    options: list[str]
) -> str:
    """
    Escalate decision to User via notifications.
    
    Args:
        issue: Description of the issue requiring decision
        options: List of available options
    
    Returns:
        Note that user will be notified (actual response requires manual implementation)
    """
    if not executor_instance:
        return "ERROR: EXECUTOR not initialized"
    
    # Format options
    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
    
    message = f"""🚨 **DECISION REQUIRED**

**Issue:** {issue}

**Options:**
{options_text}

Please respond with your choice."""
    
    await executor_instance.notifications.send(
        title="🚨 ESCALATION",
        message=message,
        priority="critical"
    )
    
    logger.warning(f"⚠️ Escalated to User: {issue}")
    
    return f"User notified. Awaiting decision on: {issue}"


@mcp.tool()
async def get_pending_tasks_count() -> int:
    """
    Get count of pending tasks in queue.
    
    Returns:
        Number of pending tasks
    """
    if not executor_instance:
        return 0
    
    return executor_instance.task_queue.get_pending_count()


@mcp.tool()
async def list_pending_tasks(limit: int = 10) -> dict:
    """
    List pending tasks in queue.
    
    Args:
        limit: Maximum number of tasks to return
    
    Returns:
        List of pending tasks
    """
    if not executor_instance:
        return {"error": "EXECUTOR not initialized"}
    
    tasks = executor_instance.task_queue.get_pending_tasks(limit)
    
    return {
        "count": len(tasks),
        "tasks": tasks
    }
