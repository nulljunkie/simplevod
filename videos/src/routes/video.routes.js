const express = require('express');
const router = express.Router();
const { protect } = require('../middleware/auth.middleware');
const { validateVideoUpdate } = require('../middleware/validation.middleware');
const videoController = require('../controllers/video.controller');

// User-specific routes (must come before parameterized routes)
router.get('/my/videos', protect, videoController.getMyVideos);
router.get('/my/status/poll', protect, videoController.pollVideoStatuses);

// Public routes
router.get('/', videoController.listVideos);
router.get('/:videoId', videoController.getVideoDetails);
router.post('/:videoId/view', videoController.incrementViewCount);

// Protected routes
router.post('/:videoId/like', protect, videoController.likeVideo);
router.put('/:videoId', protect, validateVideoUpdate, videoController.updateVideo);
router.delete('/:videoId', protect, videoController.deleteVideo);
router.get('/:videoId/status', protect, videoController.getVideoStatus);

module.exports = router;
