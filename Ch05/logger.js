/**
 * Chapter 5: Winston Logger with Trace Context
 * ==============================================
 * Injects OpenTelemetry trace_id and span_id into every log entry
 * for correlation between logs and traces.
 *
 * Usage: const logger = require('./logger');
 *        logger.info('Processing request', { userId: '123' });
 */

'use strict';

const winston = require('winston');
const { trace, context } = require('@opentelemetry/api');

/**
 * Custom Winston format that injects OTEL trace context into logs.
 */
const traceContextFormat = winston.format((info) => {
  const activeSpan = trace.getSpan(context.active());
  if (activeSpan) {
    const spanContext = activeSpan.spanContext();
    info.trace_id = spanContext.traceId;
    info.span_id = spanContext.spanId;
    info.trace_flags = spanContext.traceFlags;
  }
  return info;
});

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    traceContextFormat(),
    winston.format.timestamp(),
    winston.format.json()
  ),
  defaultMeta: {
    service: process.env.OTEL_SERVICE_NAME || 'demo-app',
    environment: process.env.NODE_ENV || 'development',
  },
  transports: [
    new winston.transports.Console(),
  ],
});

module.exports = logger;

// Example output:
// {"level":"info","message":"Processing request","service":"demo-app",
//  "trace_id":"abc123...","span_id":"def456...","timestamp":"2025-01-20T10:30:00Z"}
