# Multi-stage Dockerfile for the platform demo application
# Stage 1: Builder (if needed for future enhancements)
FROM python:3.11-slim as builder

WORKDIR /tmp
RUN pip install --user --no-cache-dir flask

# Stage 2: Runtime
FROM python:3.11-slim

# Set metadata
LABEL maintainer="Platform Engineering Team"
LABEL description="Platform demo application for Chapter 5: Evaluate User Experience"

# Create non-root user for security
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY app.py /app/app.py

# Set environment
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health').read()" || exit 1

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
