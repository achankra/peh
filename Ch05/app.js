/**
 * Chapter 5: Express App with Custom OpenTelemetry Spans
 * =======================================================
 * Demonstrates manual span creation for business logic tracing.
 *
 * Usage: node --require ./instrumentation.js app.js
 */

'use strict';

const express = require('express');
const { trace, SpanStatusCode } = require('@opentelemetry/api');

const app = express();
const PORT = process.env.PORT || 8080;
const tracer = trace.getTracer('demo-app', '1.0.0');

app.use(express.json());

// Health and readiness endpoints
app.get('/health', (req, res) => res.json({ status: 'healthy' }));
app.get('/ready', (req, res) => res.json({ status: 'ready' }));

// Business logic with custom spans
app.get('/api/items', async (req, res) => {
  const span = tracer.startSpan('fetch-items', {
    attributes: {
      'http.method': 'GET',
      'app.query.limit': req.query.limit || '10',
    },
  });

  try {
    // Simulate database query with child span
    const items = await tracer.startActiveSpan('db-query', async (dbSpan) => {
      dbSpan.setAttribute('db.system', 'postgresql');
      dbSpan.setAttribute('db.statement', 'SELECT * FROM items LIMIT $1');
      dbSpan.addEvent('query-started');

      // Simulated response
      const result = [
        { id: 1, name: 'Platform SDK', version: '2.1.0' },
        { id: 2, name: 'CLI Tool', version: '1.5.3' },
      ];

      dbSpan.addEvent('query-completed', { 'db.rows_returned': result.length });
      dbSpan.end();
      return result;
    });

    span.setAttribute('app.items.count', items.length);
    span.setStatus({ code: SpanStatusCode.OK });
    res.json({ items });
  } catch (error) {
    span.recordException(error);
    span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
    res.status(500).json({ error: 'Internal server error' });
  } finally {
    span.end();
  }
});

app.listen(PORT, () => console.log(`Demo app listening on port ${PORT}`));

module.exports = app;
