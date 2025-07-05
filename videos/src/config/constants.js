module.exports = {
  JWT_SECRET: process.env.JWT_SECRET || 'your_jwt_secret',
  VIDEO_STATUS: {
    UPLOADED: 'uploaded',
    PENDING_METADATA: 'pending_metadata',
    PROCESSING: 'processing',
    TRANSCODING: 'transcoding',
    PUBLISHED: 'published',
    FAILED: 'failed',
  },
  VIDEO_VISIBILITY: {
    PUBLIC: 'public',
    PRIVATE: 'private',
  },
  DEFAULT_PAGE_SIZE: 20,
  STREAM_BASE_URL: process.env.STREAM_BASE_URL || 'http://localhost:9000/stream',
  THUMBNAIL_BASE_URL: process.env.THUMBNAIL_BASE_URL || 'http://localhost:9000/thumbnails',
};

