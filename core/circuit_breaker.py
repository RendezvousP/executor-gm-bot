"""
EXECUTOR - Circuit Breaker Pattern
Prevents repeated calls to failing services.
"""
import logging
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, Callable, Any

logger = logging.getLogger("EXECUTOR.CircuitBreaker")

class CircuitState(Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject immediately
    HALF_OPEN = "half_open" # Testing recovery

class CircuitBreakerOpenError(Exception):
    """Raised when circuit is OPEN."""
    pass

class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,  # seconds
        success_threshold: int = 2
    ):
        """
        Args:
            failure_threshold: Failures before opening circuit
            timeout: Seconds to wait before HALF_OPEN
            success_threshold: Successes needed to close from HALF_OPEN
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        
        # State tracking per service
        self.failures: Dict[str, int] = {}
        self.successes: Dict[str, int] = {}
        self.state: Dict[str, CircuitState] = {}
        self.opened_at: Dict[str, datetime] = {}
    
    def call(
        self,
        service_name: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Raises:
            CircuitBreakerOpenError: If circuit is OPEN
        """
        current_state = self.state.get(service_name, CircuitState.CLOSED)
        
        # Check if OPEN
        if current_state == CircuitState.OPEN:
            elapsed = datetime.now() - self.opened_at[service_name]
            
            if elapsed > timedelta(seconds=self.timeout):
                # Try HALF_OPEN
                logger.info(f"🔌 {service_name} circuit: OPEN → HALF_OPEN (testing)")
                self.state[service_name] = CircuitState.HALF_OPEN
            else:
                remaining = self.timeout - int(elapsed.total_seconds())
                raise CircuitBreakerOpenError(
                    f"{service_name} circuit is OPEN. "
                    f"Wait {remaining}s before retry."
                )
        
        # Try execution
        try:
            result = func(*args, **kwargs)
            self._on_success(service_name)
            return result
            
        except Exception as e:
            self._on_failure(service_name)
            raise
    
    def _on_success(self, service_name: str):
        """Handle successful call."""
        current_state = self.state.get(service_name, CircuitState.CLOSED)
        
        if current_state == CircuitState.HALF_OPEN:
            self.successes[service_name] = self.successes.get(service_name, 0) + 1
            
            if self.successes[service_name] >= self.success_threshold:
                logger.info(f"✅ {service_name} circuit: HALF_OPEN → CLOSED")
                self.state[service_name] = CircuitState.CLOSED
                self.failures[service_name] = 0
                self.successes[service_name] = 0
        else:
            # Reset failure count on success
            self.failures[service_name] = 0
    
    def _on_failure(self, service_name: str):
        """Handle failed call."""
        self.failures[service_name] = self.failures.get(service_name, 0) + 1
        
        if self.failures[service_name] >= self.failure_threshold:
            # Only log transition once
            if self.state.get(service_name) != CircuitState.OPEN:
                logger.error(
                    f"🔌 {service_name} circuit: CLOSED → OPEN "
                    f"(failures: {self.failures[service_name]})"
                )
            
            self.state[service_name] = CircuitState.OPEN
            self.opened_at[service_name] = datetime.now()
            self.successes[service_name] = 0
