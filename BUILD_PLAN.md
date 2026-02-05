# EXECUTOR GM BOT - COMPLETE BUILD PLAN v1.0

> **Date**: 2026-02-05  
> **Goal**: Finish EXECUTOR before GitHub push  
> **Scope**: MCP Server + Config Validation + Graceful Shutdown

---

## 📋 CURRENT STATUS

### ✅ Already Built

- Core Orchestrator (`orchestrator.py`)
- Model Router with Hydra v2 (`model_router.py`)
- Skill Injector (`skill_injector.py`)
- Power Recovery (`power_recovery.py`)
- Notifications (Telegram + Discord) (`notifications.py`)
- Task Queue with WAL (`task_queue.py`)
- Documentation (README, ARCHITECTURE, CONTRIBUTING)

### ⏳ Missing (CRITICAL)

1. **MCP Server** - External comms interface
2. **MCP Client** - Connect to external MCP servers (optional)
3. **Config Validation** - Prevent startup with bad config
4. **Graceful Shutdown** - Save state on SIGTERM

---

## 🎯 PART 1: MCP SERVER (EXECUTOR AS SERVER)

### Purpose

Allow external systems to interact with EXECUTOR:
- User commands via MCP client (Claude Desktop, etc.)
- Child agents submit tasks
- External automation tools

### MCP Tools to Expose

```python
# File: mcp/server.py

@mcp.tool()
async def submit_task(
    name: str,
    description: str,
    priority: str = "normal",  # low, normal, high, critical
    assigned_to: str | None = None
) -> dict:
    """Submit a new task to EXECUTOR's queue."""
    pass

@mcp.tool()
async def get_task_status(task_id: int) -> dict:
    """Get status of a task."""
    pass

@mcp.tool()
async def get_fleet_status() -> dict:
    """Get health status of all agents."""
    pass

@mcp.tool()
async def add_api_key(
    provider: str,
    key: str,
    tier: str = "standard"
) -> dict:
    """Add API key to Hydra v2 pool."""
    pass

@mcp.tool()
async def escalate_decision(
    issue: str,
    options: list[str]
) -> str:
    """Escalate decision to User."""
    pass

@mcp.tool()
async def select_model(
    task_complexity: str = "standard",
    force_model: str | None = None
) -> dict:
    """Get recommended model for a task."""
    pass
```

---

## 🔌 PART 2: MCP CLIENT (EXECUTOR AS CLIENT)

EXECUTOR connects TO other MCP servers (optional):
- **External skill servers** (if exposed as MCP)
- **Third-party services** (if available)

---

## ✅ PART 3: CONFIG VALIDATION (Pydantic)

Validate configs on startup to prevent runtime errors.

---

## 🛑 PART 4: GRACEFUL SHUTDOWN

Handle SIGTERM/SIGINT to save state before exit.

---

## 📦 IMPLEMENTATION ORDER

1. Config Validation (30 min)
2. Graceful Shutdown (20 min)
3. MCP Server (45 min)
4. MCP Client (30 min)
5. Testing (15 min)
6. Documentation (20 min)

**Total**: ~2.5 hours

---

**Ready to execute** ✅
