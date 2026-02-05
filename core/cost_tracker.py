"""
EXECUTOR - Cost Tracking
Monitor and limit API costs per task.
"""
import logging
from typing import Dict

logger = logging.getLogger("EXECUTOR.CostTracker")

# Pricing per 1M tokens (estimated/generic)
# Real implementation would load from config or live API
MODEL_PRICING = {
    "claude-4.5-opus": {"input": 15.0, "output": 75.0},
    "claude-4.5-sonnet": {"input": 3.0, "output": 15.0},
    "gemini-pro": {"input": 0.5, "output": 1.5},
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "opencode": {"input": 0.0, "output": 0.0},  # Free
}

class CostLimitExceeded(Exception):
    """Raised when cost limit exceeded."""
    pass

class CostTracker:
    """Track and limit API costs."""
    
    def __init__(self, limit_per_task: float = 10.0):
        self.limit_per_task = limit_per_task
        self.task_costs: Dict[str, float] = {} # task_id (str) -> cost
        
    def add_cost(
        self,
        task_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Add cost for API call.
        
        Returns:
            Total cost for task so far
        
        Raises:
            CostLimitExceeded: If budget exceeded
        """
        pricing = MODEL_PRICING.get(model, {"input": 0, "output": 0})
        
        cost = (
            (input_tokens / 1_000_000) * pricing["input"] +
            (output_tokens / 1_000_000) * pricing["output"]
        )
        
        # Add to task total (make sure task_id is string key)
        t_id = str(task_id)
        self.task_costs[t_id] = self.task_costs.get(t_id, 0.0) + cost
        
        # Check limit
        if self.task_costs[t_id] > self.limit_per_task:
            raise CostLimitExceeded(
                f"Task {t_id} exceeded budget: "
                f"${self.task_costs[t_id]:.2f} > ${self.limit_per_task}"
            )
        
        # Log significant costs (> $0.01)
        if cost > 0.01:
            logger.info(
                f"💰 Task {t_id}: +${cost:.4f} "
                f"(total: ${self.task_costs[t_id]:.2f})"
            )
        
        return self.task_costs[t_id]
    
    def get_cost(self, task_id: str) -> float:
        """Get total cost for task."""
        return self.task_costs.get(str(task_id), 0.0)
