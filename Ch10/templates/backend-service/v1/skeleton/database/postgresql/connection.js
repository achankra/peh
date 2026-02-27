// Database connection module for PostgreSQL
const { Pool } = require("pg");

const pool = new Pool({
  host: process.env.DB_HOST || "localhost",
  port: parseInt(process.env.DB_PORT || "5432"),
  database: process.env.DB_NAME || "${{ values.serviceName }}",
  user: process.env.DB_USER || "platform",
  password: process.env.DB_PASSWORD || "",
});

async function query(text, params) {
  const result = await pool.query(text, params);
  return result.rows;
}

async function healthCheck() {
  try {
    await pool.query("SELECT 1");
    return { status: "connected", database: "postgresql" };
  } catch (err) {
    return { status: "disconnected", error: err.message };
  }
}

module.exports = { query, healthCheck, pool };
