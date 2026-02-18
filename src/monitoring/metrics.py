"""Lightweight thread-safe metrics collector."""

import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List, Optional
from functools import wraps


class MetricsCollector:
    def __init__(self):
        self._counters: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = Lock()

    def increment(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        key = self._key(name, labels)
        with self._lock:
            self._counters[key] += value

    def observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        key = self._key(name, labels)
        with self._lock:
            self._histograms[key].append(value)

    def get_all(self) -> dict:
        with self._lock:
            histogram_stats = {}
            for name, values in self._histograms.items():
                if values:
                    histogram_stats[name] = {
                        "count": len(values),
                        "avg": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                    }
            return {
                "counters": dict(self._counters),
                "histograms": histogram_stats,
            }

    @staticmethod
    def _key(name: str, labels: Optional[Dict[str, str]]) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"


metrics_collector = MetricsCollector()


def track_time(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """Decorator to record execution duration."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                metrics_collector.observe(f"{metric_name}_duration_seconds", time.time() - start, labels)
                metrics_collector.increment(f"{metric_name}_total", labels=labels)
        return wrapper
    return decorator
