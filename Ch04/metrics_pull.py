"""
Prometheus Pull-Based Metrics Collection
Implements pull-based metrics endpoint for Prometheus scraping.

This module demonstrates how to expose application metrics that Prometheus
periodically scrapes via HTTP. Includes common metric types:
- Counter: monotonically increasing values (e.g., request count)
- Histogram: distribution of values (e.g., request duration)
- Gauge: instantaneous values (e.g., active connections)
"""

from flask import Flask
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
from functools import wraps

app = Flask(__name__)

# Define Prometheus metrics for application monitoring
# Counter: Tracks cumulative HTTP requests by method and endpoint
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Histogram: Measures HTTP request duration distribution in seconds
# Used to detect performance degradation and SLO violations
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

# Gauge: Tracks instantaneous number of active connections
# Useful for detecting connection pool exhaustion or bottlenecks
http_active_connections = Gauge(
    'http_active_connections',
    'Current number of active HTTP connections'
)


def track_metrics(f):
    """
    Decorator to automatically track metrics for Flask endpoints.
    Measures request duration, records counters, and manages gauge updates.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Increment active connections gauge
        http_active_connections.inc()
        
        # Record request start time for duration histogram
        start_time = time.time()
        
        try:
            # Execute the wrapped endpoint handler
            result = f(*args, **kwargs)
            status_code = 200
            return result
        except Exception as e:
            status_code = 500
            raise
        finally:
            # Calculate request duration
            duration = time.time() - start_time
            
            # Record metrics
            endpoint = f.__name__
            http_request_duration_seconds.labels(
                method='GET',
                endpoint=endpoint
            ).observe(duration)
            
            http_requests_total.labels(
                method='GET',
                endpoint=endpoint,
                status=status_code
            ).inc()
            
            # Decrement active connections gauge
            http_active_connections.dec()
    
    return decorated_function


@app.route('/health')
@track_metrics
def health():
    """Health check endpoint."""
    return {'status': 'healthy'}, 200


@app.route('/api/items')
@track_metrics
def get_items():
    """Retrieve list of items from application."""
    # Simulate processing time
    time.sleep(0.01)
    return {'items': []}, 200


@app.route('/metrics')
def metrics():
    """
    Prometheus metrics endpoint.
    Prometheus scrapes this endpoint to collect application metrics.
    Returns metrics in Prometheus text format.
    """
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}


if __name__ == '__main__':
    # Start Flask application on port 5000
    # Prometheus should be configured to scrape http://localhost:5000/metrics
    app.run(host='0.0.0.0', port=5000, debug=False)
