"""
EXECUTOR - Task Queue System
SQLite-based task queue with WAL for resilience.
"""
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from enum import Enum
import asyncio

logger = logging.getLogger("EXECUTOR.TaskQueue")

class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

class TaskQueue:
    """
    SQLite-based task queue with Write-Ahead Logging (WAL).
    Supports persistence across power outages.
    """
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
        self._init_database()
        
        logger.info(f"📋 Task Queue initialized at {db_path}")
    
    def _init_database(self):
        """Initialize SQLite database with WAL mode."""
        self.conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False  # Allow multi-threaded access
        )
        self.conn.row_factory = sqlite3.Row  # Return dict-like rows
        
        # Enable WAL mode for better concurrency and crash recovery
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        
        # Create tasks table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                priority INTEGER DEFAULT 1,
                status TEXT DEFAULT 'pending',
                assigned_to TEXT,
                payload TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                started_at TEXT,
                completed_at TEXT,
                error TEXT
            )
        """)
        
        # Create index for faster queries
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_status_priority 
            ON tasks(status, priority DESC, created_at)
        """)
        
        self.conn.commit()
        logger.debug("Database initialized with WAL mode")
    
    def add_task(
        self,
        name: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        assigned_to: Optional[str] = None,
        payload: Optional[Dict] = None
    ) -> int:
        """
        Add a new task to the queue.
        
        Returns:
            Task ID
        """
        cursor = self.conn.execute("""
            INSERT INTO tasks (name, description, priority, assigned_to, payload)
            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            description,
            priority.value,
            assigned_to,
            json.dumps(payload) if payload else None
        ))
        
        self.conn.commit()
        task_id = cursor.lastrowid
        
        logger.info(f"➕ Task added: #{task_id} - {name}")
        return task_id
    
    def get_next_task(self, assigned_to: Optional[str] = None) -> Optional[Dict]:
        """
        Get next pending task based on priority.
        
        Args:
            assigned_to: Filter by assigned agent (optional)
        
        Returns:
            Task dict or None if no tasks
        """
        query = """
            SELECT * FROM tasks
            WHERE status = 'pending'
        """
        params = []
        
        if assigned_to:
            query += " AND assigned_to = ?"
            params.append(assigned_to)
        
        query += " ORDER BY priority DESC, created_at ASC LIMIT 1"
        
        row = self.conn.execute(query, params).fetchone()
        
        if row:
            task = dict(row)
            if task.get("payload"):
                task["payload"] = json.loads(task["payload"])
            return task
        return None
    
    def start_task(self, task_id: int):
        """Mark task as in progress."""
        self.conn.execute("""
            UPDATE tasks
            SET status = 'in_progress',
                started_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (task_id,))
        self.conn.commit()
        
        logger.info(f"▶️ Task started: #{task_id}")
    
    def complete_task(self, task_id: int):
        """Mark task as completed."""
        self.conn.execute("""
            UPDATE tasks
            SET status = 'completed',
                completed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (task_id,))
        self.conn.commit()
        
        logger.info(f"✅ Task completed: #{task_id}")
    
    def fail_task(self, task_id: int, error: str):
        """Mark task as failed."""
        self.conn.execute("""
            UPDATE tasks
            SET status = 'failed',
                error = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (error, task_id))
        self.conn.commit()
        
        logger.error(f"❌ Task failed: #{task_id} - {error}")
    
    def get_task_status(self, task_id: int) -> Optional[str]:
        """Get current status of a task."""
        row = self.conn.execute(
            "SELECT status FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()
        
        return row["status"] if row else None
    
    def get_pending_count(self) -> int:
        """Get number of pending tasks."""
        row = self.conn.execute(
            "SELECT COUNT(*) as count FROM tasks WHERE status = 'pending'"
        ).fetchone()
        return row["count"]
    
    def get_all_tasks(self, status: Optional[TaskStatus] = None) -> List[Dict]:
        """Get all tasks, optionally filtered by status."""
        if status:
            rows = self.conn.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC",
                (status.value,)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC"
            ).fetchall()
        
        tasks = []
        for row in rows:
            task = dict(row)
            if task.get("payload"):
                task["payload"] = json.loads(task["payload"])
            tasks.append(task)
        
        return tasks
    
    def cleanup_old_tasks(self, days: int = 30):
        """Delete completed tasks older than N days."""
        self.conn.execute("""
            DELETE FROM tasks
            WHERE status IN ('completed', 'failed')
            AND datetime(completed_at) < datetime('now', '-' || ? || ' days')
        """, (days,))
        
        deleted = self.conn.total_changes
        self.conn.commit()
        
        logger.info(f"🗑️ Cleaned up {deleted} old tasks")
        return deleted
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.debug("Database connection closed")

    async def execute_with_timeout(
        self,
        task_id: int,
        executor_func,
        timeout: int = 300
    ):
        """
        Execute a task with timeout protection.
        
        Args:
            task_id: ID of task being executed
            executor_func: Async function to execute
            timeout: Timeout in seconds (default: 300)
            
        Returns:
            Result of executor_func
            
        Raises:
            asyncio.TimeoutError: If task takes too long
        """
        logger.info(f"⏱️ Task {task_id} execution started (timeout: {timeout}s)")
        
        try:
            return await asyncio.wait_for(executor_func(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"🕐 Task {task_id} TIMED OUT after {timeout}s")
            self.fail_task(task_id, f"Execution timed out ({timeout}s)")
            raise
