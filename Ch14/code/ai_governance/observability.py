#!/usr/bin/env python3
"""
AI Agent Observability Module

Provides comprehensive monitoring and observability for AI agents including:
- Prometheus metrics collection
- Agent call tracking and latency measurement
- Confidence level monitoring
- Human override rate tracking
- Error rate monitoring
"""

import time
import logging
from typing import Callable, Any, Dict, Optional
from functools import wraps
from datetime import datetime
import json

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AIAgentMetrics:
    """Prometheus metrics for AI agents."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize metrics with optional custom registry."""
        self.registry = registry or CollectorRegistry()

        # Counter: Total AI agent requests
        self.ai_agent_requests_total = Counter(
            'ai_agent_requests_total',
            'Total number of AI agent requests',
            ['agent_type', 'action_type', 'status'],
            registry=self.registry
        )

        # Gauge: Average confidence level of AI agents
        self.ai_agent_confidence = Gauge(
            'ai_agent_confidence',
            'Confidence score of AI agent decisions (0.0-1.0)',
            ['agent_type', 'action_type'],
            registry=self.registry
        )

        # Counter: Human overrides of AI decisions
        self.ai_agent_human_overrides = Counter(
            'ai_agent_human_overrides',
            'Number of times human has overridden AI agent decisions',
            ['agent_type', 'override_reason'],
            registry=self.registry
        )

        # Histogram: AI agent request latency
        self.ai_agent_latency_seconds = Histogram(
            'ai_agent_latency_seconds',
            'Latency of AI agent requests in seconds',
            ['agent_type', 'action_type'],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
            registry=self.registry
        )

        # Counter: AI agent errors
        self.ai_agent_errors = Counter(
            'ai_agent_errors_total',
            'Total number of AI agent errors',
            ['agent_type', 'error_type'],
            registry=self.registry
        )

        # Gauge: AI agent success rate
        self.ai_agent_success_rate = Gauge(
            'ai_agent_success_rate',
            'Success rate of AI agent operations (0.0-1.0)',
            ['agent_type', 'action_type'],
            registry=self.registry
        )

        # Counter: Total decisions made by AI agents
        self.ai_decisions_total = Counter(
            'ai_decisions_total',
            'Total number of decisions made by AI agents',
            ['agent_type', 'decision_type'],
            registry=self.registry
        )

        # Gauge: Current active AI agent operations
        self.ai_agent_active_operations = Gauge(
            'ai_agent_active_operations',
            'Number of active AI agent operations',
            ['agent_type'],
            registry=self.registry
        )

        # Histogram: AI agent response time distribution
        self.ai_agent_response_time = Histogram(
            'ai_agent_response_time_seconds',
            'Response time distribution for AI agent calls',
            ['agent_type', 'endpoint'],
            registry=self.registry
        )

        # Gauge: AI model accuracy/confidence trending
        self.ai_model_accuracy = Gauge(
            'ai_model_accuracy',
            'Measured accuracy of AI model predictions',
            ['agent_type', 'model_version'],
            registry=self.registry
        )


class AgentCallTracker:
    """Tracks individual AI agent calls with detailed metrics."""

    def __init__(self, metrics: AIAgentMetrics):
        """Initialize tracker with metrics."""
        self.metrics = metrics
        self.call_history: list = []

    def track_call(
        self,
        agent_type: str,
        action_type: str,
        duration_seconds: float,
        confidence: float,
        status: str,
        error: Optional[str] = None,
        human_override: bool = False,
        override_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Track a single agent call."""

        # Record metrics
        self.metrics.ai_agent_requests_total.labels(
            agent_type=agent_type,
            action_type=action_type,
            status=status
        ).inc()

        self.metrics.ai_agent_latency_seconds.labels(
            agent_type=agent_type,
            action_type=action_type
        ).observe(duration_seconds)

        self.metrics.ai_agent_confidence.labels(
            agent_type=agent_type,
            action_type=action_type
        ).set(confidence)

        if human_override:
            self.metrics.ai_agent_human_overrides.labels(
                agent_type=agent_type,
                override_reason=override_reason or "unknown"
            ).inc()

        if error:
            self.metrics.ai_agent_errors.labels(
                agent_type=agent_type,
                error_type=type(error).__name__
            ).inc()

        # Create call record
        call_record = {
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "agent_type": agent_type,
            "action_type": action_type,
            "duration_seconds": duration_seconds,
            "confidence": confidence,
            "status": status,
            "error": error,
            "human_override": human_override,
            "override_reason": override_reason
        }

        self.call_history.append(call_record)
        logger.info(f"Agent call tracked: {json.dumps(call_record)}")

        return call_record

    def get_call_history(
        self,
        agent_type: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """Retrieve call history with optional filtering."""
        history = self.call_history

        if agent_type:
            history = [h for h in history if h["agent_type"] == agent_type]

        return history[-limit:]


def track_agent_call(
    metrics: AIAgentMetrics,
    tracker: Optional[AgentCallTracker] = None
) -> Callable:
    """
    Decorator for tracking AI agent calls.

    Automatically measures latency, tracks confidence, and handles errors.

    Usage:
        @track_agent_call(metrics, tracker)
        def my_agent_function(input_data):
            return {"confidence": 0.95, "result": "success"}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            agent_type = kwargs.get('agent_type', 'unknown')
            action_type = kwargs.get('action_type', func.__name__)

            # Increment active operations
            metrics.ai_agent_active_operations.labels(
                agent_type=agent_type
            ).inc()

            start_time = time.time()

            try:
                # Execute the function
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Extract confidence from result
                confidence = result.get('confidence', 0.5) if isinstance(result, dict) else 0.5
                status = "success"
                error = None

                # Track the call
                if tracker:
                    tracker.track_call(
                        agent_type=agent_type,
                        action_type=action_type,
                        duration_seconds=duration,
                        confidence=confidence,
                        status=status,
                        error=error
                    )

                # Record response time
                metrics.ai_agent_response_time.labels(
                    agent_type=agent_type,
                    endpoint=action_type
                ).observe(duration)

                logger.info(
                    f"Agent call successful: {agent_type}/{action_type} "
                    f"(confidence: {confidence:.2f}, duration: {duration:.2f}s)"
                )

                return result

            except Exception as e:
                duration = time.time() - start_time
                status = "error"
                error_msg = str(e)

                # Track the error
                metrics.ai_agent_errors.labels(
                    agent_type=agent_type,
                    error_type=type(e).__name__
                ).inc()

                if tracker:
                    tracker.track_call(
                        agent_type=agent_type,
                        action_type=action_type,
                        duration_seconds=duration,
                        confidence=0.0,
                        status=status,
                        error=error_msg
                    )

                logger.error(
                    f"Agent call failed: {agent_type}/{action_type} "
                    f"(error: {error_msg}, duration: {duration:.2f}s)"
                )

                raise

            finally:
                # Decrement active operations
                metrics.ai_agent_active_operations.labels(
                    agent_type=agent_type
                ).dec()

        return wrapper
    return decorator


class AIObservabilityModule:
    """Main observability module for AI agents."""

    def __init__(self):
        """Initialize the observability module."""
        self.metrics = AIAgentMetrics()
        self.tracker = AgentCallTracker(self.metrics)

    def get_metrics_registry(self) -> CollectorRegistry:
        """Get Prometheus metrics registry."""
        return self.metrics.registry

    def get_metrics(self) -> AIAgentMetrics:
        """Get AI agent metrics."""
        return self.metrics

    def get_tracker(self) -> AgentCallTracker:
        """Get call tracker."""
        return self.tracker

    def record_confidence(self, agent_type: str, action_type: str, confidence: float):
        """Record confidence level for an agent."""
        self.metrics.ai_agent_confidence.labels(
            agent_type=agent_type,
            action_type=action_type
        ).set(confidence)

    def record_override(self, agent_type: str, reason: str):
        """Record human override of agent decision."""
        self.metrics.ai_agent_human_overrides.labels(
            agent_type=agent_type,
            override_reason=reason
        ).inc()
        logger.warning(f"Human override recorded for {agent_type}: {reason}")

    def record_accuracy(self, agent_type: str, model_version: str, accuracy: float):
        """Record model accuracy metric."""
        self.metrics.ai_model_accuracy.labels(
            agent_type=agent_type,
            model_version=model_version
        ).set(accuracy)

    def get_agent_statistics(self, agent_type: str) -> Dict[str, Any]:
        """Get comprehensive statistics for an agent."""
        call_history = self.tracker.get_call_history(agent_type=agent_type)

        if not call_history:
            return {
                "agent_type": agent_type,
                "total_calls": 0,
                "statistics": "No data available"
            }

        # Calculate statistics
        successful_calls = len([c for c in call_history if c['status'] == 'success'])
        failed_calls = len([c for c in call_history if c['status'] == 'error'])
        overridden_calls = len([c for c in call_history if c['human_override']])

        durations = [c['duration_seconds'] for c in call_history]
        confidences = [c['confidence'] for c in call_history if c['confidence'] > 0]

        return {
            "agent_type": agent_type,
            "total_calls": len(call_history),
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "overridden_calls": overridden_calls,
            "success_rate": successful_calls / len(call_history) if call_history else 0,
            "override_rate": overridden_calls / len(call_history) if call_history else 0,
            "average_confidence": sum(confidences) / len(confidences) if confidences else 0,
            "average_duration_seconds": sum(durations) / len(durations) if durations else 0,
            "min_duration_seconds": min(durations) if durations else 0,
            "max_duration_seconds": max(durations) if durations else 0
        }


# Global observability module instance
_observability = None


def get_observability_module() -> AIObservabilityModule:
    """Get or create the global observability module."""
    global _observability
    if _observability is None:
        _observability = AIObservabilityModule()
    return _observability


if __name__ == "__main__":
    # Example usage
    observability = get_observability_module()

    # Create a decorator for tracking
    @track_agent_call(
        observability.get_metrics(),
        observability.get_tracker()
    )
    def example_agent_call(agent_type="example", action_type="test"):
        """Example agent function."""
        time.sleep(0.5)  # Simulate work
        return {
            "confidence": 0.87,
            "result": "Task completed",
            "status": "success"
        }

    # Call the function
    result = example_agent_call()
    print(f"Result: {result}")

    # Get statistics
    stats = observability.get_agent_statistics("example")
    print(f"\nAgent Statistics:\n{json.dumps(stats, indent=2)}")
