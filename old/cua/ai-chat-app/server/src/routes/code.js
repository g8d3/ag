const express = require('express');
const { VM } = require('vm2');
const router = express.Router();

router.post('/run', (req, res) => {
  const { code } = req.body;
  try {
    const vm = new VM({ timeout: 1000, sandbox: {} });
    const output = vm.run(code);
    res.json({ output: String(output) });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

module.exports = router;