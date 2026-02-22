/**
 * Chapter 5: OpenTelemetry Instrumentation Setup
 * ================================================
 * Configures the OpenTelemetry SDK for a Node.js application.
 * Must be required BEFORE any other modules.
 *
 * Usage: node --require ./instrumentation.js app.js
 *
 * Prerequisites:
 *   npm install @opentelemetry/sdk-node \
 *     @opentelemetry/auto-instrumentations-node \
 *     @opentelemetry/exporter-trace-otlp-grpc \
 *     @opentelemetry/exporter-metrics-otlp-grpc \
 *     @opentelemetry/resources \
 *     @opentelemetry/semantic-conventions
 */

'use strict';

const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-grpc');
const { OTLPMetricExporter } = require('@opentelemetry/exporter-metrics-otlp-grpc');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');

const serviceName = process.env.OTEL_SERVICE_NAME || 'demo-app';
const otlpEndpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4317';

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
    [SemanticResourceAttributes.SERVICE_VERSION]: process.env.APP_VERSION || '1.0.0',
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: process.env.NODE_ENV || 'development',
  }),
  traceExporter: new OTLPTraceExporter({ url: otlpEndpoint }),
  metricExporter: new OTLPMetricExporter({ url: otlpEndpoint }),
  instrumentations: [
    getNodeAutoInstrumentations({
      '@opentelemetry/instrumentation-http': { enabled: true },
      '@opentelemetry/instrumentation-express': { enabled: true },
      '@opentelemetry/instrumentation-fs': { enabled: false },
    }),
  ],
});

sdk.start();
console.log(`OpenTelemetry initialized for ${serviceName} → ${otlpEndpoint}`);

process.on('SIGTERM', () => {
  sdk.shutdown().then(() => process.exit(0)).catch(() => process.exit(1));
});
