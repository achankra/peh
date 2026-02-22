#!/usr/bin/env python3
"""
Example Python application instrumented with OpenTelemetry.

Demonstrates:
- Automatic trace instrumentation using decorators
- Custom span attributes and events
- Metrics collection (request latency, error rates)
- Structured logging with context propagation
- Integration with OTEL Collector via gRPC

Usage:
    pip install opentelemetry-api opentelemetry-sdk
    python3 instrument-app.py

The app exposes metrics on http://localhost:8000/metrics
"""

import json
import logging
import sys
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict
from urllib.parse import parse_qs, urlparse

# OpenTelemetry imports (optional - app works without them)
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.instrumentation.wsgi import OpenTelemetryMiddleware
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    print("Warning: OpenTelemetry SDK not installed. Install with:")
    print("  pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp")


# Configure structured logging
class StructuredLogger:
    """Structured logging with context propagation."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
    
    def log(self, level: str, message: str, **context):
        """Log with structured context."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "context": context
        }
        getattr(self.logger, level.lower())(json.dumps(log_entry))


# Global metrics storage (simple in-memory, replace with proper metrics in production)
class MetricsCollector:
    """Simple metrics collector for demonstration."""
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.total_latency = 0.0
        self.latencies = []
    
    def record_request(self, latency: float, status_code: int):
        """Record request metrics."""
        self.request_count += 1
        self.total_latency += latency
        self.latencies.append(latency)
        if status_code >= 500:
            self.error_count += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        if not self.latencies:
            return {}
        
        sorted_latencies = sorted(self.latencies[-100:])  # Keep last 100
        return {
            "http_requests_total": self.request_count,
            "http_errors_total": self.error_count,
            "http_request_duration_avg": self.total_latency / self.request_count,
            "http_request_duration_p50": sorted_latencies[len(sorted_latencies) // 2],
            "http_request_duration_p99": sorted_latencies[int(len(sorted_latencies) * 0.99)],
        }


# Initialize components
logger = StructuredLogger("platform-app")
metrics_collector = MetricsCollector()
tracer = None
meter = None

if OTEL_AVAILABLE:
    # Configure OTEL tracing
    otlp_exporter = OTLPSpanExporter(
        endpoint="localhost:4317",  # OTEL Collector endpoint
        insecure=True
    )
    trace_provider = TracerProvider()
    trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(trace_provider)
    tracer = trace.get_tracer(__name__)
    
    # Configure OTEL metrics
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint="localhost:4317", insecure=True)
    )
    meter_provider = MeterProvider(metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)
    meter = metrics.get_meter(__name__)


def traced(func: Callable) -> Callable:
    """Decorator to automatically trace function calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not tracer:
            return func(*args, **kwargs)
        
        with tracer.start_as_current_span(func.__name__) as span:
            span.set_attribute("function.name", func.__name__)
            span.set_attribute("function.module", func.__module__)
            
            try:
                result = func(*args, **kwargs)
                span.set_attribute("function.status", "success")
                return result
            except Exception as e:
                span.set_attribute("function.status", "error")
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                logger.log("error", f"Error in {func.__name__}", error=str(e))
                raise
    
    return wrapper


class SimpleWSGIApp:
    """Simple WSGI application instrumented with OpenTelemetry."""
    
    def __init__(self):
        """Initialize the application."""
        self.request_count = 0
    
    @traced
    def handle_request(self, path: str, query: Dict[str, Any]) -> tuple:
        """Handle an incoming request and return response."""
        self.request_count += 1
        
        if path == "/":
            return 200, "OK", {"message": "Platform Health API"}
        
        elif path == "/health":
            return self.health_check()
        
        elif path == "/api/data":
            return self.get_data(query)
        
        elif path == "/metrics":
            return self.get_metrics()
        
        elif path == "/error":
            return self.trigger_error()
        
        else:
            return 404, "Not Found", {"error": f"Path {path} not found"}
    
    @traced
    def health_check(self) -> tuple:
        """Health check endpoint."""
        logger.log("info", "Health check requested")
        return 200, "OK", {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "requests": self.request_count
        }
    
    @traced
    def get_data(self, query: Dict[str, Any]) -> tuple:
        """Get sample data with simulated processing."""
        delay = float(query.get("delay", ["0.1"])[0])
        time.sleep(delay)  # Simulate processing
        
        if tracer:
            span = trace.get_current_span()
            span.set_attribute("processing.delay", delay)
        
        logger.log("info", "Data retrieved", delay=delay)
        
        return 200, "OK", {
            "data": {
                "timestamp": datetime.utcnow().isoformat(),
                "values": [1, 2, 3, 4, 5],
                "processing_time": delay
            }
        }
    
    @traced
    def get_metrics(self) -> tuple:
        """Export metrics in Prometheus text format."""
        metrics_data = metrics_collector.get_metrics()
        
        lines = [
            "# HELP http_requests_total Total HTTP requests",
            "# TYPE http_requests_total counter",
            f"http_requests_total {metrics_data.get('http_requests_total', 0)}",
            "",
            "# HELP http_errors_total Total HTTP errors",
            "# TYPE http_errors_total counter",
            f"http_errors_total {metrics_data.get('http_errors_total', 0)}",
            "",
            "# HELP http_request_duration_seconds Request latency in seconds",
            "# TYPE http_request_duration_seconds histogram",
            f"http_request_duration_seconds{{quantile=\"0.5\"}} {metrics_data.get('http_request_duration_p50', 0)}",
            f"http_request_duration_seconds{{quantile=\"0.99\"}} {metrics_data.get('http_request_duration_p99', 0)}",
        ]
        
        body = "\n".join(lines)
        return 200, "OK", body
    
    @traced
    def trigger_error(self) -> tuple:
        """Intentionally trigger an error for testing."""
        logger.log("error", "Error endpoint called")
        
        if tracer:
            span = trace.get_current_span()
            span.set_attribute("error.triggered", True)
        
        return 500, "Internal Server Error", {"error": "Intentional error for testing"}
    
    def __call__(self, environ, start_response):
        """WSGI interface."""
        start_time = time.time()
        
        try:
            # Parse request
            path = environ.get("PATH_INFO", "/")
            query_string = environ.get("QUERY_STRING", "")
            query = parse_qs(query_string)
            
            if tracer:
                span = trace.get_current_span()
                span.set_attribute("http.method", environ.get("REQUEST_METHOD"))
                span.set_attribute("http.url", path)
            
            # Handle request
            status_code, status_text, response = self.handle_request(path, query)
            
            # Record metrics
            latency = (time.time() - start_time) * 1000  # Convert to ms
            metrics_collector.record_request(latency, status_code)
            
            logger.log("info", "Request completed",
                      path=path, status=status_code, latency_ms=latency)
            
            # Prepare response
            if isinstance(response, dict):
                body = json.dumps(response).encode("utf-8")
                content_type = "application/json"
            else:
                body = response.encode("utf-8")
                content_type = "text/plain"
            
            headers = [
                ("Content-Type", content_type),
                ("Content-Length", str(len(body)))
            ]
            
            start_response(f"{status_code} {status_text}", headers)
            return [body]
        
        except Exception as e:
            logger.log("error", "Unhandled exception", error=str(e))
            
            if tracer:
                span = trace.get_current_span()
                span.set_attribute("error.unhandled", True)
            
            error_response = json.dumps({"error": str(e)}).encode("utf-8")
            start_response("500 Internal Server Error", [
                ("Content-Type", "application/json"),
                ("Content-Length", str(len(error_response)))
            ])
            return [error_response]


def run_simple_server(app, host: str = "0.0.0.0", port: int = 8000):
    """Run a simple HTTP server (for testing without WSGI server)."""
    import socket
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    
    logger.log("info", f"Server listening on http://{host}:{port}")
    logger.log("info", "Endpoints: /health, /api/data, /metrics, /error")
    
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            request_data = client_socket.recv(1024).decode("utf-8")
            
            if request_data:
                request_line = request_data.split("\r\n")[0]
                method, path_query, protocol = request_line.split()
                path = path_query.split("?")[0]
                
                # Call WSGI app
                environ = {
                    "REQUEST_METHOD": method,
                    "PATH_INFO": path,
                    "QUERY_STRING": path_query.split("?")[1] if "?" in path_query else "",
                    "SERVER_NAME": host,
                    "SERVER_PORT": str(port),
                    "wsgi.url_scheme": "http",
                }
                
                def start_response(status, headers):
                    response = f"HTTP/1.1 {status}\r\n"
                    for header, value in headers:
                        response += f"{header}: {value}\r\n"
                    response += "\r\n"
                    client_socket.sendall(response.encode("utf-8"))
                
                try:
                    response_body = app(environ, start_response)
                    for chunk in response_body:
                        client_socket.sendall(chunk)
                finally:
                    client_socket.close()
    
    except KeyboardInterrupt:
        logger.log("info", "Server shutting down")
    finally:
        server_socket.close()


if __name__ == "__main__":
    logger.log("info", "Starting instrumented application",
              otel_enabled=OTEL_AVAILABLE)
    
    app = SimpleWSGIApp()
    run_simple_server(app)

