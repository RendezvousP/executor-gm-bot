"""
EXECUTOR - Graceful Shutdown Handler
Handles SIGTERM/SIGINT to save state before exit.
"""
import signal
import sys
import logging
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .orchestrator import Executor

logger = logging.getLogger("EXECUTOR.Shutdown")

class ShutdownHandler:
    """Handle graceful shutdown on SIGTERM/SIGINT."""
    
    def __init__(self, executor: "Executor"):
        self.executor = executor
        self.shutdown_event = asyncio.Event()
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.info("🛑 Shutdown handler registered (SIGTERM, SIGINT)")
    
    def _signal_handler(self, signum, frame):
        """Called when signal received."""
        signal_name = signal.Signals(signum).name
        logger.warning(f"⚠️ Received {signal_name}, initiating graceful shutdown...")
        
        # Set shutdown event (breaks main loop)
        self.shutdown_event.set()
    
    async def shutdown(self):
        """Perform graceful shutdown."""
        logger.info("🛑 Shutting down EXECUTOR...")
        
        try:
            # 1. Mark shutdown in power recovery
            self.executor.power_recovery.mark_shutdown()
            logger.info("   ✅ Power recovery state saved")
        except Exception as e:
            logger.error(f"   ❌ Power recovery save failed: {e}")
        
        try:
            # 2. Close task queue
            self.executor.task_queue.close()
            logger.info("   ✅ Task queue closed")
        except Exception as e:
            logger.error(f"   ❌ Task queue close failed: {e}")
        
        try:
            # 3. Stop MCP server (if running)
            if hasattr(self.executor, 'mcp_server') and self.executor.mcp_server:
                await self.executor.mcp_server.stop()
                logger.info("   ✅ MCP server stopped")
        except Exception as e:
            logger.error(f"   ❌ MCP server stop failed: {e}")
        
        logger.info("🛑 Shutdown complete. Goodbye!")
    
    def is_shutdown_requested(self) -> bool:
        """Check if shutdown was requested."""
        return self.shutdown_event.is_set()
    
    async def wait_for_shutdown(self):
        """Wait for shutdown signal."""
        await self.shutdown_event.wait()
