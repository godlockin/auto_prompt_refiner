"""
Prometheus Metrics Exporter.

Features:
- Counter, Gauge, Histogram, Summary metrics
- HTTP endpoint for scraping
- Thread-safe operations
- Built-in collectors
"""
import time
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Dict, Any
from threading import Lock
from random import random

logger = logging.getLogger(__name__)


@dataclass
class MetricSample:
    """A single metric sample."""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class Counter:
    """Counter metric - always increments."""

    def __init__(self, name: str, description: str = "", labels: List[str] = None):
        self.name = name
        self.description = description
        self._labels = labels or []
        self._values: Dict[tuple, float] = {}
        self._lock = Lock()

    def inc(self, value: float = 1.0, labels: Dict[str, str] = None):
        """Increment counter."""
        if value < 0:
            raise ValueError("Counter can only increment")
        key = self._labels_to_key(labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) + value

    def _labels_to_key(self, labels: Dict[str, str] = None) -> tuple:
        """Convert labels dict to hashable key."""
        if not self._labels:
            return ()
        labels = labels or {}
        return tuple(labels.get(l, "") for l in self._labels)

    def collect(self) -> List[MetricSample]:
        """Collect all samples."""
        with self._lock:
            return [
                MetricSample(
                    name=self.name,
                    value=value,
                    labels=dict(zip(self._labels, key))
                )
                for key, value in self._values.items()
            ]


class Gauge:
    """Gauge metric - can go up and down."""

    def __init__(self, name: str, description: str = "", labels: List[str] = None):
        self.name = name
        self.description = description
        self._labels = labels or []
        self._values: Dict[tuple, float] = {}
        self._lock = Lock()

    def inc(self, value: float = 1.0, labels: Dict[str, str] = None):
        """Increment gauge."""
        key = self._labels_to_key(labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) + value

    def dec(self, value: float = 1.0, labels: Dict[str, str] = None):
        """Decrement gauge."""
        key = self._labels_to_key(labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) - value

    def set(self, value: float, labels: Dict[str, str] = None):
        """Set gauge to value."""
        key = self._labels_to_key(labels)
        with self._lock:
            self._values[key] = value

    def _labels_to_key(self, labels: Dict[str, str] = None) -> tuple:
        """Convert labels dict to hashable key."""
        if not self._labels:
            return ()
        labels = labels or {}
        return tuple(labels.get(l, "") for l in self._labels)

    def collect(self) -> List[MetricSample]:
        """Collect all samples."""
        with self._lock:
            return [
                MetricSample(
                    name=self.name,
                    value=value,
                    labels=dict(zip(self._labels, key))
                )
                for key, value in self._values.items()
            ]


class Histogram:
    """Histogram metric - observes values into buckets."""

    def __init__(
        self,
        name: str,
        description: str = "",
        labels: List[str] = None,
        buckets: List[float] = None
    ):
        self.name = name
        self.description = description
        self._labels = labels or []
        self._buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
        self._sum: Dict[tuple, float] = {}
        self._count: Dict[tuple, int] = {}
        self._buckets_data: Dict[tuple, Dict[float, int]] = {}
        self._lock = Lock()

    def observe(self, value: float, labels: Dict[str, str] = None):
        """Observe a value."""
        key = self._labels_to_key(labels)
        with self._lock:
            self._sum[key] = self._sum.get(key, 0.0) + value
            self._count[key] = self._count.get(key, 0) + 1

            if key not in self._buckets_data:
                self._buckets_data[key] = {b: 0 for b in self._buckets}

            for bucket in self._buckets:
                if value <= bucket:
                    self._buckets_data[key][bucket] += 1

    def _labels_to_key(self, labels: Dict[str, str] = None) -> tuple:
        """Convert labels dict to hashable key."""
        if not self._labels:
            return ()
        labels = labels or {}
        return tuple(labels.get(l, "") for l in self._labels)

    def collect(self) -> List[MetricSample]:
        """Collect all samples."""
        samples = []
        with self._lock:
            for key in self._sum.keys():
                labels_dict = dict(zip(self._labels, key))
                count = self._count.get(key, 0)
                sum_val = self._sum.get(key, 0.0)

                # Bucket samples
                cumulative = 0
                for bucket in self._buckets:
                    cumulative += self._buckets_data[key].get(bucket, 0)
                    samples.append(MetricSample(
                        name=f"{self.name}_bucket",
                        value=float(cumulative),
                        labels={**labels_dict, "le": str(bucket)}
                    ))

                # +Inf bucket
                samples.append(MetricSample(
                    name=f"{self.name}_bucket",
                    value=float(count),
                    labels={**labels_dict, "le": "+Inf"}
                ))

                # Count and sum
                samples.append(MetricSample(
                    name=f"{self.name}_count",
                    value=float(count),
                    labels=labels_dict
                ))
                samples.append(MetricSample(
                    name=f"{self.name}_sum",
                    value=sum_val,
                    labels=labels_dict
                ))

        return samples


class Summary:
    """Summary metric - calculates quantiles."""

    def __init__(
        self,
        name: str,
        description: str = "",
        labels: List[str] = None,
        quantiles: List[float] = None
    ):
        self.name = name
        self.description = description
        self._labels = labels or []
        self._quantiles = quantiles or [0.5, 0.9, 0.95, 0.99]
        self._values: Dict[tuple, List[float]] = {}
        self._sum: Dict[tuple, float] = {}
        self._lock = Lock()

    def observe(self, value: float, labels: Dict[str, str] = None):
        """Observe a value."""
        key = self._labels_to_key(labels)
        with self._lock:
            if key not in self._values:
                self._values[key] = []
                self._sum[key] = 0.0
            self._values[key].append(value)
            self._sum[key] += value

    def _labels_to_key(self, labels: Dict[str, str] = None) -> tuple:
        """Convert labels dict to hashable key."""
        if not self._labels:
            return ()
        labels = labels or {}
        return tuple(labels.get(l, "") for l in self._labels)

    def collect(self) -> List[MetricSample]:
        """Collect all samples."""
        samples = []
        with self._lock:
            for key, values in self._values.items():
                labels_dict = dict(zip(self._labels, key))

                # Quantile samples (using interpolation)
                sorted_vals = sorted(values)
                n = len(sorted_vals)

                for q in self._quantiles:
                    idx = int(q * (n - 1))
                    val = sorted_vals[idx]
                    samples.append(MetricSample(
                        name=f"{self.name}_quantile",
                        value=val,
                        labels={**labels_dict, "quantile": str(q)}
                    ))

                # Count and sum
                samples.append(MetricSample(
                    name=f"{self.name}_count",
                    value=float(n),
                    labels=labels_dict
                ))
                samples.append(MetricSample(
                    name=f"{self.name}_sum",
                    value=self._sum[key],
                    labels=labels_dict
                ))

        return samples


class MetricsRegistry:
    """
    Prometheus metrics registry.

    Features:
    - Register and collect metrics
    - HTTP endpoint for scraping
    - Thread-safe operations
    """

    def __init__(self):
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._summaries: Dict[str, Summary] = {}
        self._lock = Lock()

    def counter(
        self,
        name: str,
        description: str = "",
        labels: List[str] = None
    ) -> Counter:
        """Get or create a counter."""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name, description, labels)
            return self._counters[name]

    def gauge(
        self,
        name: str,
        description: str = "",
        labels: List[str] = None
    ) -> Gauge:
        """Get or create a gauge."""
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name, description, labels)
            return self._gauges[name]

    def histogram(
        self,
        name: str,
        description: str = "",
        labels: List[str] = None,
        buckets: List[float] = None
    ) -> Histogram:
        """Get or create a histogram."""
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name, description, labels, buckets)
            return self._histograms[name]

    def summary(
        self,
        name: str,
        description: str = "",
        labels: List[str] = None,
        quantiles: List[float] = None
    ) -> Summary:
        """Get or create a summary."""
        with self._lock:
            if name not in self._summaries:
                self._summaries[name] = Summary(name, description, labels, quantiles)
            return self._summaries[name]

    def collect(self) -> str:
        """Collect all metrics in Prometheus format."""
        lines = []

        with self._lock:
            for metric in self._counters.values():
                for sample in metric.collect():
                    lines.append(self._format_sample(sample, "# TYPE {} counter".format(metric.name)))

            for metric in self._gauges.values():
                for sample in metric.collect():
                    lines.append(self._format_sample(sample, "# TYPE {} gauge".format(metric.name)))

            for metric in self._histograms.values():
                for sample in metric.collect():
                    lines.append(self._format_sample(sample, "# TYPE {} histogram".format(metric.name)))

            for metric in self._summaries.values():
                for sample in metric.collect():
                    lines.append(self._format_sample(sample, "# TYPE {} summary".format(metric.name)))

        return "\n".join(lines)

    def _format_sample(self, sample: MetricSample, type_line: str) -> str:
        """Format a sample for Prometheus output."""
        labels_str = ",".join(
            f'{k}="{v}"' for k, v in sample.labels.items()
        ) if sample.labels else ""

        lines = [type_line]

        if labels_str:
            lines.append(f'{sample.name}{{{labels_str}}} {sample.value}')
        else:
            lines.append(f'{sample.name} {sample.value}')

        return "\n".join(lines)


# Global registry
registry = MetricsRegistry()

# Pre-defined metrics
REFINEMENT_REQUESTS = registry.counter(
    "refinement_requests_total",
    "Total number of refinement requests",
    ["task_type"]
)

REFINEMENT_DURATION = registry.histogram(
    "refinement_duration_seconds",
    "Duration of refinement operations",
    ["task_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

CACHE_HITS = registry.counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_name"]
)

CACHE_MISSES = registry.counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_name"]
)

LLM_REQUESTS = registry.counter(
    "llm_requests_total",
    "Total LLM API requests",
    ["model", "status"]
)

LLM_DURATION = registry.histogram(
    "llm_request_duration_seconds",
    "Duration of LLM API requests",
    ["model"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0]
)

AGENT_EXECUTIONS = registry.counter(
    "agent_executions_total",
    "Total agent executions",
    ["agent_name", "status"]
)

CIRCUIT_STATE = registry.gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=half-open, 2=open)",
    ["circuit_name"]
)

TASK_CLASSIFICATION = registry.counter(
    "task_classifications_total",
    "Task classifications by type",
    ["task_type"]
)
