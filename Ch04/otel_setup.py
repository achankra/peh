"""
OpenTelemetry Setup and Configuration
Initializes distributed tracing and metrics collection infrastructure
for comprehensive observability across microservices.

This module configures:
- TracerProvider with OTLP exporter for trace collection
- MeterProvider with OTLP exporter for metrics collection
- Resource attributes for service identification and deployment context
- Semantic conventions for standardized span attributes
"""

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, DEPLOYMENT_ENVIRONMENT, Resource
from opentelemetry.semconv.resource import ResourceAttributes
import os


def setup_tracing(service_name: str, otlp_endpoint: str = "localhost:4317"):
    """
    Configure TracerProvider with OTLP exporter for distributed tracing.
    
    Args:
        service_name: Name of the service for identification in traces
        otlp_endpoint: OTLP collector endpoint (default: localhost:4317)
    
    Returns:
        Configured TracerProvider instance
    
    The tracer exports traces to an OTLP collector for centralized collection,
    storage, and analysis across the entire microservice architecture.
    """
    # Create resource with service identification metadata
    resource = Resource(attributes={
        SERVICE_NAME: service_name,
        SERVICE_VERSION: os.getenv("SERVICE_VERSION", "1.0.0"),
        DEPLOYMENT_ENVIRONMENT: os.getenv("DEPLOYMENT_ENV", "development"),
        # Additional semantic convention attributes
        ResourceAttributes.HOST_NAME: os.getenv("HOSTNAME", "unknown"),
        ResourceAttributes.OS_TYPE: "linux",
    })
    
    # Initialize OTLP span exporter
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    
    # Create TracerProvider with batch processing
    # BatchSpanProcessor improves performance by sending spans in batches
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    return tracer_provider


def setup_metrics(service_name: str, otlp_endpoint: str = "localhost:4317"):
    """
    Configure MeterProvider with OTLP exporter for metrics collection.
    
    Args:
        service_name: Name of the service for identification in metrics
        otlp_endpoint: OTLP collector endpoint (default: localhost:4317)
    
    Returns:
        Configured MeterProvider instance
    
    The meter exports metrics to an OTLP collector for real-time monitoring,
    alerting, and performance analysis of application behavior.
    """
    # Create resource with service identification metadata
    resource = Resource(attributes={
        SERVICE_NAME: service_name,
        SERVICE_VERSION: os.getenv("SERVICE_VERSION", "1.0.0"),
        DEPLOYMENT_ENVIRONMENT: os.getenv("DEPLOYMENT_ENV", "development"),
    })
    
    # Initialize OTLP metric exporter with periodic export
    otlp_metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint)
    
    # PeriodicExportingMetricReader exports metrics every 60 seconds
    metric_reader = PeriodicExportingMetricReader(
        otlp_metric_exporter,
        interval_millis=60000
    )
    
    # Create MeterProvider with metric reader
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    
    return meter_provider


def initialize_observability(service_name: str, otlp_endpoint: str = "localhost:4317"):
    """
    Initialize complete observability stack for a service.
    
    Args:
        service_name: Name of the service
        otlp_endpoint: OTLP collector endpoint
    
    Returns:
        Tuple of (TracerProvider, MeterProvider)
    
    This is the primary initialization function to set up all observability
    instrumentation for a microservice.
    """
    tracer_provider = setup_tracing(service_name, otlp_endpoint)
    meter_provider = setup_metrics(service_name, otlp_endpoint)
    
    return tracer_provider, meter_provider
