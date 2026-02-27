// Database connection module for MongoDB
const { MongoClient } = require("mongodb");

const MONGODB_URI =
  process.env.MONGODB_URI || "mongodb://localhost:27017/${{ values.serviceName }}";

let client;

async function connect() {
  if (!client) {
    client = new MongoClient(MONGODB_URI);
    await client.connect();
    console.log("Connected to MongoDB");
  }
  return client.db();
}

async function disconnect() {
  if (client) {
    await client.close();
    client = null;
  }
}

module.exports = { connect, disconnect };
