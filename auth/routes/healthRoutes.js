const express = require('express');
const router = express.Router();

router.get('/health/liveness', (req, res) => {
  res.status(200).send('OK');
});

router.get('/health/readiness', (req, res) => {
  res.status(200).send('Ready');
});

module.exports = router;
