# EXECUTOR - The General Manager

```
███████╗██╗  ██╗███████╗ ██████╗██╗   ██╗████████╗ ██████╗ ██████╗ 
██╔════╝╚██╗██╔╝██╔════╝██╔════╝██║   ██║╚══██╔══╝██╔═══██╗██╔══██╗
█████╗   ╚███╔╝ █████╗  ██║     ██║   ██║   ██║   ██║   ██║██████╔╝
██╔══╝   ██╔██╗ ██╔══╝  ██║     ██║   ██║   ██║   ██║   ██║██╔══██╗
███████╗██╔╝ ██╗███████╗╚██████╗╚██████╔╝   ██║   ╚██████╔╝██║  ██║
╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝
```

> **Named after Darth Vader's flagship - The Super Star Destroyer "Executor"**  
> **Type**: Multi-Agent Orchestration System  
> **Version**: 1.0.0  
> **License**: MIT

---

## Overview

EXECUTOR is a **General Manager Bot** for orchestrating multi-agent systems.  
It coordinates agents, manages skills, routes AI models, and handles task distribution.

*"The Executor does not ask for permission. It executes the will of Lord Vader."*

## Responsibilities

1. **Fleet Coordination**: Assign tasks to all Agents
2. **Skill Inheritance**: Inject appropriate skills to child agents
3. **Model Routing**: Select optimal models (Hydra Protocol v2)
4. **Power Recovery**: Scan and report system status after outage
5. **Escalation**: Ask User when critical decisions needed
6. **MCP Server**: Expose EXECUTOR functionality to external systems
7. **MCP Client**: Connect to external MCP servers (optional)

## Project Structure

```
executor/
├── config/
│   ├── hydra_keys.json      # API key pool (encrypted)
│   ├── fleet_registry.json  # Registered agents
│   └── notification.json    # Telegram + Discord config
├── core/
│   ├── orchestrator.py      # Main brain
│   ├── skill_injector.py    # Skill inheritance engine
│   ├── model_router.py      # Hydra v2 routing
│   └── power_recovery.py    # Resume logic
├── agents/                  # Agent connectors
│   ├── network_agent.py
│   ├── proxmox_agent.py
│   └── deep_search_agent.py
├── state/
│   ├── current_step.json
│   ├── task_queue.db
│   └── logs/
├── skills/cache/            # Bundled skills (11 included)
└── main.py                  # Entry point
```

## Quick Start

### Run EXECUTOR (Standard Mode)

```bash
cd /path/to/executor
python main.py
```

### Run as MCP Server

```bash
python mcp_server.py
```

This exposes 8 MCP tools:
- `submit_task` - Submit new task to queue
- `get_task_status` - Get task status
- `get_fleet_status` - Health check all agents
- `add_api_key` - Add key to Hydra pool
- `select_model` - Get recommended model
- `escalate_decision` - Escalate to User
- `get_pending_tasks_count` - Count pending tasks
- `list_pending_tasks` - List pending tasks

## Dependencies

- Python 3.13+
- FastMCP
- SQLite
- python-telegram-bot
- discord.py
- proxmoxer
- routeros_api

## Configuration

See `config/` directory for:
- `hydra_keys.json` - API keys (Hydra v2)
- `fleet_registry.json` - Fleet registry
- `notification.json` - Notification channels (Telegram + Discord)
- `mcp_clients.json` - External MCP servers to connect to

### MCP Client Configuration

To connect EXECUTOR to external MCP servers (optional feature):

1. Edit `config/mcp_clients.json`
2. Set `"enabled": true` for the servers you want
3. Restart EXECUTOR

Example:
```json
{
  "clients": [
    {
      "name": "external_server",
      "url": "http://localhost:5000/mcp",
      "enabled": false
    }
  ]
}
```

> **Note**: MCP clients are **optional**. EXECUTOR works standalone without external servers.

## Hardware Requirements

### Minimum
- **CPU**: 4 cores (Intel i5 / AMD Ryzen 5)
- **RAM**: 8 GB
- **Storage**: 10 GB SSD
- **OS**: Windows 10+, Linux, macOS
- **Network**: Internet connection for AI APIs

### Recommended
- **CPU**: 8 cores (Intel i7 / AMD Ryzen 7)
- **RAM**: 16 GB
- **Storage**: 50 GB SSD
- **OS**: Windows 11 / Ubuntu 22.04+
- **Network**: Stable broadband (100+ Mbps)

### For Production (Managing 10+ Agents)
- **CPU**: 12+ cores (Intel i9 / AMD Ryzen 9 / Xeon)
- **RAM**: 32 GB
- **Storage**: 100 GB NVMe SSD
- **Network**: Gigabit Ethernet / Fiber

---

*"Execute Order 66."* - Not this kind of execute, though. 🤖
