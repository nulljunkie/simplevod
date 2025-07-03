const express = require('express');
const router = express.Router();

const videoRoutes = require('./video.routes');

router.use('/videos', videoRoutes);

router.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

router.get('/ready', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

module.exports = router;

