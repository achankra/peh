import express from "express";
import pino from "pino";
import pinoHttp from "pino-http";

const logger = pino({ level: process.env.LOG_LEVEL || "info" });
const app = express();
const port = parseInt(process.env.PORT || "${{ values.port }}", 10);

app.use(pinoHttp({ logger }));
app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({ status: "ok", service: "${{ values.serviceName }}" });
});

app.get("/", (_req, res) => {
  res.json({
    service: "${{ values.serviceName }}",
    version: "0.1.0",
    team: "${{ values.team }}",
  });
});

app.listen(port, () => {
  logger.info(`${{ values.serviceName }} listening on port ${port}`);
});

export default app;
