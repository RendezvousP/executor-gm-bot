"""
EXECUTOR - Main Entry Point
"""
from core.orchestrator import Executor
from core.shutdown import ShutdownHandler
import asyncio

async def main():
    print("""
███████╗██╗  ██╗███████╗ ██████╗██╗   ██╗████████╗ ██████╗ ██████╗ 
██╔════╝╚██╗██╔╝██╔════╝██╔════╝██║   ██║╚══██╔══╝██╔═══██╗██╔══██╗
█████╗   ╚███╔╝ █████╗  ██║     ██║   ██║   ██║   ██║   ██║██████╔╝
██╔══╝   ██╔██╗ ██╔══╝  ██║     ██║   ██║   ██║   ██║   ██║██╔══██╗
███████╗██╔╝ ██╗███████╗╚██████╗╚██████╔╝   ██║   ╚██████╔╝██║  ██║
╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝
    
    Antigravity Fleet - Central Orchestrator
    "The will of Lord Vader, executed."
    """)
    
    # Initialize EXECUTOR
    executor = Executor()
    shutdown_handler = ShutdownHandler(executor)
    
    # Run main loop with graceful shutdown support
    try:
        # Create tasks for main loop and shutdown waiter
        main_task = asyncio.create_task(executor.run())
        shutdown_task = asyncio.create_task(shutdown_handler.wait_for_shutdown())
        
        # Wait for either to complete
        done, pending = await asyncio.wait(
            [main_task, shutdown_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
        
    except KeyboardInterrupt:
        pass
    finally:
        await shutdown_handler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
