"""
Monitoring and Health Check Module.

Provides comprehensive health checks, metrics collection, and monitoring endpoints.
"""
import os
import sys
import time
import logging
import threading
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


@dataclass
class MetricsSnapshot:
    """A snapshot of system metrics at a point in time."""
    timestamp: datetime
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    active_requests: int = 0
    errors_by_type: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        if self.errors_by_type is None:
            self.errors_by_type = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "total_latency_ms": self.total_latency_ms,
            "avg_latency_ms": self.avg_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "p99_latency_ms": self.p99_latency_ms,
            "active_requests": self.active_requests,
            "errors_by_type": self.errors_by_type,
            "success_rate": (
                self.successful_requests / self.total_requests * 100
                if self.total_requests > 0 else 0
            )
        }


class MetricsCollector:
    """Thread-safe metrics collector for monitoring system performance."""

    def __init__(self, window_seconds: int = 300):
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._request_times: List[float] = []
        self._request_count = 0
        self._success_count = 0
        self._failure_count = 0
        self._total_latency = 0.0
        self._active_requests = 0
        self._errors: Dict[str, int] = defaultdict(int)
        self._latency_history: List[float] = []

    def record_latency(self, latency_ms: float, success: bool = True):
        """Record a latency measurement."""
        with self._lock:
            self._latency_history.append(latency_ms)
            self._total_latency += latency_ms
            if success:
                self._success_count += 1
            else:
                self._failure_count += 1
            self._cleanup_old_data()

    def _cleanup_old_data(self):
        """Remove old latency data beyond the window."""
        cutoff_time = time.time() - self.window_seconds
        self._latency_history = [t for t in self._latency_history if t > cutoff_time]

    def get_snapshot(self) -> MetricsSnapshot:
        """Get a snapshot of current metrics."""
        with self._lock:
            latencies = list(self._latency_history)

            snapshot = MetricsSnapshot(
                timestamp=datetime.now(timezone.utc),
                total_requests=self._request_count,
                successful_requests=self._success_count,
                failed_requests=self._failure_count,
                total_latency_ms=self._total_latency,
                avg_latency_ms=(
                    self._total_latency / self._request_count
                    if self._request_count > 0 else 0
                ),
                active_requests=self._active_requests,
                errors_by_type=dict(self._errors)
            )

            if latencies:
                sorted_latencies = sorted(latencies)
                n = len(sorted_latencies)
                snapshot.p95_latency_ms = sorted_latencies[int(n * 0.95)]
                snapshot.p99_latency_ms = sorted_latencies[int(n * 0.99)]

            return snapshot


class HealthChecker:
    """Comprehensive health checker for the Synthesis Prime system."""

    def __init__(self):
        self.metrics = MetricsCollector()
        self._start_time = time.time()

    def check_all(self) -> Dict[str, Any]:
        """Perform comprehensive health checks."""
        checks = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": self.get_uptime(),
            "components": {}
        }

        checks["components"]["config"] = self._check_config()
        checks["components"]["llm_client"] = self._check_llm_client()
        checks["components"]["storage"] = self._check_storage()

        overall_status = "healthy"
        for component_status in checks["components"].values():
            if component_status["status"] == "unhealthy":
                overall_status = "unhealthy"
            elif component_status["status"] == "degraded" and overall_status == "healthy":
                overall_status = "degraded"

        checks["status"] = overall_status

        if overall_status == "unhealthy":
            checks["summary"] = "One or more components are unhealthy"
        elif overall_status == "degraded":
            checks["summary"] = "System is running with degraded performance"
        else:
            checks["summary"] = "All components are healthy"

        return checks

    def _check_config(self) -> Dict[str, Any]:
        """Check configuration health."""
        try:
            from src.config import Config
            missing = Config.validate()

            return {
                "status": "healthy" if len(missing) == 0 else "unhealthy",
                "missing_env_vars": missing,
                "config_valid": Config.is_valid()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def _check_llm_client(self) -> Dict[str, Any]:
        """Check LLM client health."""
        try:
            from src.llm_client import LLMClient
            client = LLMClient()
            health = client.health_check()

            primary_available = health.get("primary", {}).get("available", False)
            fallback_available = health.get("fallback", {}).get("available", False)

            status = "healthy" if (primary_available or fallback_available) else "unhealthy"

            return {
                "status": status,
                "primary": health.get("primary", {}),
                "fallback": health.get("fallback", {})
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def _check_storage(self) -> Dict[str, Any]:
        """Check storage health."""
        try:
            from src.storage import TaskBox
            storage = TaskBox()
            tasks_dir_exists = os.path.exists(storage.tasks_dir)

            return {
                "status": "healthy" if tasks_dir_exists else "degraded",
                "tasks_directory": storage.tasks_dir,
                "tasks_directory_exists": tasks_dir_exists
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        snapshot = self.metrics.get_snapshot()
        return snapshot.to_dict()

    def get_uptime(self) -> float:
        """Get system uptime in seconds."""
        return time.time() - self._start_time


# Global instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker
