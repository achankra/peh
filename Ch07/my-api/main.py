#!/usr/bin/env python3
"""
my-api - Main application entry point
"""

import os
import logging
from flask import Flask, jsonify

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200


@app.route('/ready', methods=['GET'])
def ready():
    """Readiness check endpoint."""
    return jsonify({'status': 'ready'}), 200


@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint."""
    return 'prometheus_http_requests_total{endpoint="metrics"} 1\n', 200


@app.route('/api/info', methods=['GET'])
def info():
    """Service information endpoint."""
    return jsonify({
        'service': 'my-api',
        'version': '1.0.0',
        'environment': os.getenv('ENVIRONMENT', 'unknown')
    }), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting my-api on port {port}")
    app.run(host='0.0.0.0', port=port, debug=os.getenv('DEBUG', 'False') == 'True')
