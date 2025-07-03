module.exports = {
  JWT_SECRET: process.env.JWT_SECRET || 'your_jwt_secret',
  JWT_EXPIRE: process.env.JWT_EXPIRE || '30d',
  VIDEO_STATUS: {
    PENDING_METADATA: 'pending_metadata',
    TRANSCODING: 'transcoding',
    PUBLISHED: 'published',
    FAILED: 'failed',
  },
  VIDEO_VISIBILITY: {
    PUBLIC: 'public',
    UNLISTED: 'unlisted',
    PRIVATE: 'private',
  },
  DEFAULT_PAGE_SIZE: 20,
  STREAM_BASE_URL: process.env.STREAM_BASE_URL || 'http://localhost:9000/stream',
  THUMBNAIL_BASE_URL: process.env.THUMBNAIL_BASE_URL || 'http://localhost:9000/thumbnails',
};

