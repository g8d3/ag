const express = require('express');
const db = require('../db');
const router = express.Router();

router.post('/', (req, res) => {
  const { userId, message, parentId } = req.body;
  // Mock AI response (replace with real API call)
  const response = `AI: Echoing "${message}"`;
  db.run(
    'INSERT INTO chats (userId, parentId, message, response, timestamp) VALUES (?, ?, ?, ?, ?)',
    [userId, parentId || null, message, response, new Date()],
    function (err) {
      if (err) return res.status(500).json({ error: 'Database error' });
      res.json({ id: this.lastID, message, response });
    }
  );
});

router.get('/:userId', (req, res) => {
  db.all('SELECT * FROM chats WHERE userId = ?', [req.params.userId], (err, chats) => {
    if (err) return res.status(500).json({ error: 'Database error' });
    res.json(chats);
  });
});

module.exports = router;