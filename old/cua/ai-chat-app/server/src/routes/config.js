const express = require('express');
const jwt = require('jsonwebtoken');
const db = require('../db');
const router = express.Router();

const authenticate = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token' });
  jwt.verify(token, 'secret', (err, decoded) => {
    if (err) return res.status(401).json({ error: 'Invalid token' });
    req.userId = decoded.userId;
    next();
  });
};

router.get('/', authenticate, (req, res) => {
  db.all('SELECT * FROM configs WHERE userId = ?', [req.userId], (err, configs) => {
    if (err) return res.status(500).json({ error: 'Database error' });
    res.json(configs);
  });
});

router.post('/', authenticate, (req, res) => {
  const { name, baseUrl, apiKey, modelId } = req.body;
  db.run(
    'INSERT INTO configs (userId, name, baseUrl, apiKey, modelId) VALUES (?, ?, ?, ?, ?)',
    [req.userId, name, baseUrl, apiKey, modelId],
    (err) => {
      if (err) return res.status(500).json({ error: 'Database error' });
      res.json({ message: 'Config saved' });
    }
  );
});

module.exports = router;