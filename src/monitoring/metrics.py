"""Simple metrics collection for production monitoring.

Provides a lightweight metrics collector compatible with Prometheus.
Tracks counters, gauges, and histograms for monitoring application health.
"""

import time
from typing import Dict, List, Optional
from functools import wraps
from collections import defaultdict
from threading import Lock


class MetricsCollector:
    """Thread-safe metrics collector for application monitoring."""

    def __init__(self):
        """Initialize metrics collector."""
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = Lock()

    def increment_counter(
        self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None
    ):
        """Increment a counter metric.

        Args:
            name: Metric name
            value: Amount to increment by
            labels: Optional labels for the metric
        """
        metric_key = self._build_metric_key(name, labels)
        with self._lock:
            self._counters[metric_key] += value

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric to a specific value.

        Args:
            name: Metric name
            value: Value to set
            labels: Optional labels for the metric
        """
        metric_key = self._build_metric_key(name, labels)
        with self._lock:
            self._gauges[metric_key] = value

    def observe_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """Record a value in a histogram.

        Args:
            name: Metric name
            value: Value to record
            labels: Optional labels for the metric
        """
        metric_key = self._build_metric_key(name, labels)
        with self._lock:
            self._histograms[metric_key].append(value)

    def get_metrics(self) -> Dict[str, any]:
        """Get all collected metrics.

        Returns:
            Dictionary containing all metrics
        """
        with self._lock:
            # Calculate histogram stats
            histogram_stats = {}
            for name, values in self._histograms.items():
                if values:
                    histogram_stats[name] = {
                        "count": len(values),
                        "sum": sum(values),
                        "avg": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                    }

            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": histogram_stats,
            }

    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()

    @staticmethod
    def _build_metric_key(name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Build a unique metric key from name and labels.

        Args:
            name: Metric name
            labels: Optional labels

        Returns:
            Metric key string
        """
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"


# Global metrics collector instance
metrics_collector = MetricsCollector()


def track_execution_time(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """Decorator to track function execution time.

    Args:
        metric_name: Name of the metric to record
        labels: Optional labels for the metric

    Example:
        @track_execution_time("agent_execution", labels={"agent": "market"})
        def analyze_market(product_idea):
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metrics_collector.observe_histogram(
                    f"{metric_name}_duration_seconds", duration, labels
                )
                metrics_collector.increment_counter(
                    f"{metric_name}_total", 1.0, labels
                )

        return wrapper

    return decorator


def increment_counter(metric_name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
    """Increment a counter metric.

    Args:
        metric_name: Name of the metric
        value: Amount to increment
        labels: Optional labels
    """
    metrics_collector.increment_counter(metric_name, value, labels)


# Common application metrics
def track_agent_execution(agent_name: str):
    """Track agent execution metrics.

    Args:
        agent_name: Name of the agent
    """
    return track_execution_time("agent_execution", labels={"agent": agent_name})


def track_rag_query():
    """Track RAG query metrics."""
    return track_execution_time("rag_query")


def track_api_request(endpoint: str):
    """Track API request metrics.

    Args:
        endpoint: API endpoint path
    """
    return track_execution_time("api_request", labels={"endpoint": endpoint})
