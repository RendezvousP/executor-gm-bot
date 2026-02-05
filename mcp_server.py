"""
EXECUTOR - MCP Server Entry Point
Run this to start EXECUTOR as an MCP server.
"""
from mcp.server import mcp, init_mcp_server
from core.orchestrator import Executor
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EXECUTOR.MCP")

async def main():
    logger.info("🚀 Starting EXECUTOR MCP Server...")
    
    # Initialize EXECUTOR
    executor = Executor()
    
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
    
    # Run MCP server
    await mcp.run()

if __name__ == "__main__":
    asyncio.run(main())
