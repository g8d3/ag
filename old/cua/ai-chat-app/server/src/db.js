const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database(':memory:'); // Use file-based DB for persistence

db.serialize(() => {
  db.run(`CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)`);
  db.run(`CREATE TABLE configs (id INTEGER PRIMARY KEY, userId INTEGER, name TEXT, baseUrl TEXT, apiKey TEXT, modelId TEXT)`);
  db.run(`CREATE TABLE chats (id INTEGER PRIMARY KEY, userId INTEGER, parentId INTEGER, message TEXT, response TEXT, timestamp DATETIME)`);
});

module.exports = db;