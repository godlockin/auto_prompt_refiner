"""
Circuit Breaker Pattern Implementation.

Prevents cascading failures by:
- Tracking failure counts
- Implementing half-open state for recovery
- Configurable thresholds and timeouts

States:
- CLOSED: Normal operation
- OPEN: Failing, rejecting requests
- HALF_OPEN: Testing recovery
"""
import time
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Any, TypeVar, Generic
from functools import wraps
from threading import Lock

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: float = 60.0
    half_open_max_calls: int = 3


@dataclass
class CircuitMetrics:
    """Circuit breaker metrics."""
    state: CircuitState = CircuitState.CLOSED
    failures: int = 0
    successes: int = 0
    total_calls: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    last_state_change: float = field(default_factory=time.time)
    consecutive_failures: int = 0
    consecutive_successes: int = 0


class CircuitBreakerError(Exception):
    """Circuit breaker is open."""
    def __init__(self, message: str = "Circuit breaker is open"):
        super().__init__(message)


class CircuitBreaker:
    """
    Circuit Breaker implementation.

    Prevents cascading failures by:
    1. Counting failures and successes
    2. Opening circuit after threshold failures
    3. Testing recovery in half-open state
    4. Resetting after success threshold
    """

    def __init__(self, name: str, config: CircuitConfig = None):
        self.name = name
        self.config = config or CircuitConfig()
        self._state = CircuitState.CLOSED
        self._metrics = CircuitMetrics()
        self._lock = Lock()
        self._last_opened_time = 0.0

    @property
    def state(self) -> CircuitState:
        """Get current state, checking timeout if open."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_opened_time >= self.config.timeout_seconds:
                    self._transition_to(CircuitState.HALF_OPEN)
                    return CircuitState.HALF_OPEN
            return self._state

    @property
    def metrics(self) -> CircuitMetrics:
        """Get current metrics."""
        with self._lock:
            return CircuitMetrics(
                state=self._state,
                failures=self._metrics.failures,
                successes=self._metrics.successes,
                total_calls=self._metrics.total_calls,
                last_failure_time=self._metrics.last_failure_time,
                last_success_time=self._metrics.last_success_time,
                last_state_change=self._metrics.last_state_change,
                consecutive_failures=self._metrics.consecutive_failures,
                consecutive_successes=self._metrics.consecutive_successes,
            )

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state."""
        old_state = self._state
        self._state = new_state
        self._metrics.last_state_change = time.time()

        if new_state == CircuitState.OPEN:
            self._last_opened_time = time.time()
            self._metrics.consecutive_failures = 0
            self._metrics.consecutive_successes = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._metrics.successes = 0
            self._metrics.failures = 0
            self._metrics.consecutive_failures = 0
            self._metrics.consecutive_successes = 0
        elif new_state == CircuitState.CLOSED:
            self._metrics.failures = 0
            self._metrics.successes = 0
            self._metrics.consecutive_failures = 0
            self._metrics.consecutive_successes = 0

        logger.info(
            f"Circuit [{self.name}]: {old_state.value} -> {new_state.value}"
        )

    def record_success(self) -> None:
        """Record a successful call."""
        with self._lock:
            self._metrics.total_calls += 1
            self._metrics.successes += 1
            self._metrics.consecutive_successes += 1
            self._metrics.consecutive_failures = 0
            self._metrics.last_success_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                if self._metrics.consecutive_successes >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)

    def record_failure(self) -> None:
        """Record a failed call."""
        with self._lock:
            self._metrics.total_calls += 1
            self._metrics.failures += 1
            self._metrics.consecutive_failures += 1
            self._metrics.consecutive_successes = 0
            self._metrics.last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                if self._metrics.consecutive_failures >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)

    def can_execute(self) -> bool:
        """Check if a call can be executed."""
        return self.state != CircuitState.OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
            Any exception from the function
        """
        # Check state BEFORE execution
        current_state = self.state
        if current_state == CircuitState.OPEN:
            raise CircuitBreakerError(
                f"Circuit [{self.name}] is open. Cannot execute {func.__name__}"
            )

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            # After recording failure, check if circuit transitioned to OPEN
            if self.state == CircuitState.OPEN:
                raise CircuitBreakerError(
                    f"Circuit [{self.name}] is now open after failure"
                )
            raise

    def __repr__(self) -> str:
        metrics = self.metrics
        return (
            f"CircuitBreaker(name={self.name}, "
            f"state={self._state.value}, "
            f"failures={metrics.failures}, "
            f"successes={metrics.successes})"
        )


def circuit_breaker(
    name: str,
    config: CircuitConfig = None,
    circuit_breaker: CircuitBreaker = None
):
    """
    Decorator to apply circuit breaker to a function.

    Args:
        name: Circuit breaker name
        config: Circuit configuration
        circuit_breaker: Existing circuit breaker instance

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        breaker = circuit_breaker or CircuitBreaker(name, config)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)

        # Store breaker on function for access
        wrapper.circuit_breaker = breaker
        async_wrapper.circuit_breaker = breaker

        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper

    return decorator


# Try-import asyncio for decorator
try:
    import asyncio
except ImportError:
    asyncio = None


class CircuitManager:
    """
    Manager for multiple circuit breakers.

    Provides:
    - Centralized circuit state tracking
    - Group-level operations
    - Health checks
    """

    def __init__(self):
        self._circuits: dict[str, CircuitBreaker] = {}
        self._lock = Lock()

    def get_or_create(
        self,
        name: str,
        config: CircuitConfig = None
    ) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        with self._lock:
            if name not in self._circuits:
                self._circuits[name] = CircuitBreaker(name, config)
            return self._circuits[name]

    def get(self, name: str) -> CircuitBreaker | None:
        """Get a circuit breaker by name."""
        with self._lock:
            return self._circuits.get(name)

    def all_states(self) -> dict[str, dict]:
        """Get state of all circuits."""
        with self._lock:
            return {
                name: {
                    "state": breaker.state.value,
                    "metrics": {
                        "failures": breaker.metrics.failures,
                        "successes": breaker.metrics.successes,
                        "total_calls": breaker.metrics.total_calls,
                        "consecutive_failures": breaker.metrics.consecutive_failures,
                        "last_failure_time": breaker.metrics.last_failure_time,
                    }
                }
                for name, breaker in self._circuits.items()
            }

    def health_check(self) -> dict:
        """Health check all circuits."""
        states = self.all_states()
        all_closed = all(s["state"] == "closed" for s in states.values())

        return {
            "healthy": all_closed,
            "circuits": states,
            "total_circuits": len(states),
        }


# Global circuit manager
circuit_manager = CircuitManager()
