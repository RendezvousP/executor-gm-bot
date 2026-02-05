"""
EXECUTOR - MCP Server Entry Point
Run this to start EXECUTOR as an MCP server.
"""
from mcp.server import mcp, init_mcp_server
from core.orchestrator import Executor
import asyncio
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EXECUTOR.MCP")

async def main():
    logger.info("🚀 Starting EXECUTOR MCP Server...")
    
    try:
        # Initialize EXECUTOR
        executor = Executor()
    except Exception as e:
        logger.error(f"❌ Failed to initialize EXECUTOR: {e}")
        logger.error("   Please check your configuration files and try again.")
        sys.exit(1)
    
    # Initialize MCP server with EXECUTOR instance
    init_mcp_server(executor)
    
    logger.info("✅ EXECUTOR MCP Server ready")
    logger.info("   Tools available:")
    logger.info("   - submit_task")
    logger.info("   - get_task_status")
    logger.info("   - get_fleet_status")
    logger.info("   - add_api_key")
    logger.info("   - select_model")
    logger.info("   - escalate_decision")
    logger.info("   - get_pending_tasks_count")
    logger.info("   - list_pending_tasks")
    
    try:
        # Run MCP server
        await mcp.run()
    except KeyboardInterrupt:
        logger.info("🛑 MCP Server stopped by user")
    except Exception as e:
        logger.error(f"❌ MCP Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
