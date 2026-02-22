"""
OTLP Push-Based Trace Collection
Demonstrates how to create and export traces to an OTLP collector.

This module shows best practices for distributed tracing:
- Creating spans for business logic operations
- Setting semantic attributes for context
- Building parent-child span relationships
- Recording events and exceptions
- Exporting traces via OTLP protocol
"""

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.semconv.trace import SpanAttributes
import logging

# Configure logging for observability
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_tracer(service_name: str, otlp_endpoint: str = "localhost:4317"):
    """
    Initialize OpenTelemetry TracerProvider with OTLP exporter.
    
    Args:
        service_name: Name of the service for trace attribution
        otlp_endpoint: OTLP collector gRPC endpoint
    
    Returns:
        Configured Tracer instance for creating spans
    """
    # Define resource with service metadata
    resource = Resource(attributes={
        SERVICE_NAME: service_name,
        SERVICE_VERSION: "1.0.0",
    })
    
    # Create OTLP exporter for pushing traces to collector
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    
    # Initialize TracerProvider with batch span processor
    # BatchSpanProcessor improves performance by sending spans in batches
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Set as global tracer provider
    trace.set_tracer_provider(tracer_provider)
    
    return trace.get_tracer(__name__)


def process_user_request(tracer, user_id: str, action: str) -> dict:
    """
    Demonstrate parent span with business logic attributes.
    
    Args:
        tracer: OpenTelemetry Tracer instance
        user_id: User identifier
        action: Action being performed
    
    Returns:
        Result dictionary with processing details
    """
    # Create parent span for entire request processing
    with tracer.start_as_current_span("process_user_request") as parent_span:
        # Set semantic attributes for context and analysis
        parent_span.set_attribute(SpanAttributes.HTTP_METHOD, "POST")
        parent_span.set_attribute(SpanAttributes.HTTP_URL, f"/api/users/{user_id}/action")
        parent_span.set_attribute("user_id", user_id)
        parent_span.set_attribute("action", action)
        
        # Add event to record significant occurrence
        parent_span.add_event("user_request_started", {
            "user_id": user_id,
            "action": action,
            "timestamp": str(__import__('datetime').datetime.utcnow())
        })
        
        try:
            # Simulate validation logic in child span
            validation_result = validate_user_action(tracer, user_id, action)
            
            if not validation_result["valid"]:
                parent_span.set_status(trace.Status(trace.StatusCode.ERROR))
                parent_span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, 400)
                return {"success": False, "error": "Invalid action"}
            
            # Simulate business logic processing in child span
            processing_result = perform_action(tracer, user_id, action)
            
            # Record successful completion
            parent_span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, 200)
            parent_span.add_event("user_request_completed", {
                "result": "success",
                "processing_time": processing_result.get("duration_ms", 0)
            })
            
            return {"success": True, "result": processing_result}
        
        except Exception as e:
            # Record exception in span for error tracking
            parent_span.record_exception(e)
            parent_span.set_status(trace.Status(trace.StatusCode.ERROR))
            parent_span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, 500)
            logger.error(f"Error processing user request: {e}")
            raise


def validate_user_action(tracer, user_id: str, action: str) -> dict:
    """
    Demonstrate child span for validation logic.
    Child spans inherit parent context and appear in trace hierarchy.
    
    Args:
        tracer: OpenTelemetry Tracer instance
        user_id: User identifier
        action: Action to validate
    
    Returns:
        Validation result dictionary
    """
    # Create child span - automatically linked to parent context
    with tracer.start_as_current_span("validate_user_action") as span:
        span.set_attribute("user_id", user_id)
        span.set_attribute("action", action)
        
        # Simulate validation logic
        is_valid = action in ["create", "update", "delete", "read"]
        
        span.set_attribute("valid", is_valid)
        
        return {"valid": is_valid}


def perform_action(tracer, user_id: str, action: str) -> dict:
    """
    Demonstrate child span for business logic processing.
    
    Args:
        tracer: OpenTelemetry Tracer instance
        user_id: User identifier
        action: Action to perform
    
    Returns:
        Processing result dictionary
    """
    # Create child span for action execution
    with tracer.start_as_current_span("perform_action") as span:
        span.set_attribute("user_id", user_id)
        span.set_attribute("action", action)
        
        # Simulate processing with timing
        import time
        start = time.time()
        
        # Simulate action execution (could be database query, API call, etc.)
        time.sleep(0.1)
        
        duration_ms = (time.time() - start) * 1000
        
        # Record processing metrics
        span.set_attribute("duration_ms", duration_ms)
        span.add_event("action_executed", {
            "action": action,
            "duration_ms": duration_ms
        })
        
        return {
            "action": action,
            "status": "completed",
            "duration_ms": duration_ms
        }


if __name__ == "__main__":
    # Initialize tracer
    tracer = initialize_tracer("trace-demo-service")
    
    # Example usage: Process a user request
    try:
        result = process_user_request(tracer, "user123", "update")
        logger.info(f"Request result: {result}")
    except Exception as e:
        logger.error(f"Failed to process request: {e}")
    
    # Ensure all traces are exported before exit
    trace.get_tracer_provider().force_flush()
