const mongoose = require('mongoose');
const { VIDEO_STATUS, VIDEO_VISIBILITY } = require('../config/constants');

const RawFileInfoSchema = new mongoose.Schema({
  bucket: { type: String, required: true },
  key: { type: String, required: true },
  url: { type: String, default: null },
}, { _id: false });

const StreamingInfoSchema = new mongoose.Schema({
  url: { type: String, required: true },
}, { _id: false });

const ThumbnailUrlsSchema = new mongoose.Schema({
  small: { type: String, default: null },
  large: { type: String, default: null },
}, { _id: false });

const VideoSchema = new mongoose.Schema(
  {
    unique_key: {
      type: String,
      required: [true, 'A unique key is required'],
      unique: true,
      trim: true,
      index: true,
    },
    title: {
      type: String,
      required: [true, 'A title is required'],
      trim: true,
      maxlength: [100, 'Title cannot exceed 100 characters'],
    },
    description: {
      type: String,
      trim: true,
      maxlength: [5000, 'Description cannot exceed 5000 characters'],
      default: null,
    },
    original_filename: {
      type: String,
      required: [true, 'Original filename is required'],
      trim: true,
    },
    original_content_type: {
      type: String,
      required: [true, 'Original content type is required'],
      trim: true,
    },
    size_bytes: {
      type: Number,
      required: [true, 'Size in bytes is required'],
    },
    duration_seconds: {
      type: Number,
      default: null,
    },
    user_id: {
      type: String,
      required: [true, 'User ID is required'],
      trim: true,
      index: true,
    },
    uploader_username: {
      type: String,
      default: null,
    },
    status: {
      type: String,
      enum: Object.values(VIDEO_STATUS),
      default: VIDEO_STATUS.PENDING_METADATA,
    },
    visibility: {
      type: String,
      enum: Object.values(VIDEO_VISIBILITY),
      default: VIDEO_VISIBILITY.PUBLIC,
    },
    raw_file_info: {
      type: RawFileInfoSchema,
      required: true,
    },
    streaming_info: {
      type: StreamingInfoSchema,
      default: null,
    },
    thumbnail_urls: {
      type: ThumbnailUrlsSchema,
      default: () => ({ small: null, large: null }),
    },
    tags: {
      type: [String],
      default: [],
    },
    views_count: {
      type: Number,
      default: 0,
    },
    likes_count: {
      type: Number,
      default: 0,
    },
    uploaded_at: {
      type: Date,
      default: Date.now,
    },
    published_at: {
      type: Date,
      default: null,
    },
    last_modified_at: {
      type: Date,
      default: Date.now,
    },
  },
  {
    timestamps: false, 
  }
);

exports.Video = mongoose.model('Video', VideoSchema, 'videos');
