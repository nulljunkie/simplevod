const { Video } = require('../models/video.model');
const { successResponse, errorResponse } = require('../utils/response');
const { VIDEO_STATUS, VIDEO_VISIBILITY, DEFAULT_PAGE_SIZE } = require('../config/constants');
const { logger } = require('../utils/logger');

exports.listVideos = async (req, res) => {
  try {
    const {
      page = 1,
      limit = DEFAULT_PAGE_SIZE,
      sort = 'published_at',
      order = 'desc',
      visibility = VIDEO_VISIBILITY.PUBLIC,
      tag,
      search,
      user_id,
    } = req.query;

    const query = { status: VIDEO_STATUS.PUBLISHED };

    // Add filters
    if (visibility) query.visibility = visibility;
    if (tag) query.tags = tag;
    if (user_id) query.user_id = user_id;
    if (search) {
      query.$or = [
        { title: { $regex: search, $options: 'i' } },
        { description: { $regex: search, $options: 'i' } },
      ];
    }

    const totalCount = await Video.countDocuments(query);
    const sortObj = { [sort]: order === 'asc' ? 1 : -1 };

    const videos = await Video.find(query)
      .sort(sortObj)
      .skip((page - 1) * limit)
      .limit(Number(limit))
      .select('unique_key title description thumbnail_urls duration_seconds user_id uploader_username views_count likes_count published_at');

    return successResponse(res, {
      videos: videos.map(video => ({
        id: video.unique_key,
        title: video.title,
        description: video.description,
        thumbnail_url: video.thumbnail_urls?.small, // Use 'small' thumbnail
        duration_seconds: video.duration_seconds,
        uploader_id: video.user_id,
        uploader_username: video.uploader_username || video.user_id,
        views_count: video.views_count,
        likes_count: video.likes_count,
        published_at: video.published_at,
      })),
      total_count: totalCount,
      page: Number(page),
      total_pages: Math.ceil(totalCount / limit),
    });
  } catch (error) {
    logger.error('Error listing videos:', error);
    return errorResponse(res, 'Failed to list videos', 500);
  }
};

exports.getVideoDetails = async (req, res) => {
  try {
    const { videoId } = req.params;
    const video = await Video.findOne({ unique_key: videoId });

    if (!video) {
      return errorResponse(res, 'Video not found', 404);
    }

    if (
      video.status !== VIDEO_STATUS.PUBLISHED &&
      (!req.user || req.user.user_id !== video.user_id)
    ) {
      return errorResponse(res, 'Video not available', 403);
    }

    const response = {
      id: video.unique_key,
      title: video.title,
      description: video.description,
      stream_url: video.streaming_info?.url, // Use streaming_info.url
      thumbnail_urls: video.thumbnail_urls, // Returns the { small, large } object
      duration_seconds: video.duration_seconds,
      uploader: {
        id: video.user_id,
        username: video.uploader_username || video.user_id,
      },
      tags: video.tags,
      visibility: video.visibility,
      views_count: video.views_count,
      likes_count: video.likes_count,
      published_at: video.published_at,
    };

    return successResponse(res, response);
  } catch (error) {
    logger.error('Error getting video details:', error);
    return errorResponse(res, 'Failed to get video details', 500);
  }
};

exports.incrementViewCount = async (req, res) => {
  try {
    const { videoId } = req.params;

    const video = await Video.findOneAndUpdate(
      { unique_key: videoId, status: VIDEO_STATUS.PUBLISHED },
      { $inc: { views_count: 1 } },
      { new: true }
    );

    if (!video) {
      return errorResponse(res, 'Video not found', 404);
    }

    return successResponse(res, {
      success: true,
      views_count: video.views_count,
    });
  } catch (error) {
    logger.error('Error incrementing view count:', error);
    return errorResponse(res, 'Failed to increment view count', 500);
  }
};

exports.likeVideo = async (req, res) => {
  try {
    const { videoId } = req.params;
    const userId = req.user.user_id;

    // In a real implementation, you'd have a likes collection
    // For simplicity, we're just incrementing the likes count
    const video = await Video.findOneAndUpdate(
      { unique_key: videoId, status: VIDEO_STATUS.PUBLISHED },
      { $inc: { likes_count: 1 } },
      { new: true }
    );

    if (!video) {
      return errorResponse(res, 'Video not found', 404);
    }

    return successResponse(res, {
      success: true,
      likes_count: video.likes_count,
      liked: true,
    });
  } catch (error) {
    logger.error('Error liking video:', error);
    return errorResponse(res, 'Failed to like video', 500);
  }
};

exports.updateVideo = async (req, res) => {
  try {
    const { videoId } = req.params;
    const userId = req.user.user_id;
    const { title, description, tags, visibility } = req.body;

    const video = await Video.findOne({ unique_key: videoId });
    if (!video) {
      return errorResponse(res, 'Video not found', 404);
    }

    // Check if user is the owner
    if (video.user_id !== userId) {
      return errorResponse(res, 'Not authorized to update this video', 403);
    }

    // Update fields
    if (title) video.title = title;
    if (description) video.description = description;
    if (tags) video.tags = tags;
    if (visibility) video.visibility = visibility;
    
    video.last_modified_at = new Date();
    await video.save();

    return successResponse(res, {
      success: true,
      video_id: video.unique_key,
    });
  } catch (error) {
    logger.error('Error updating video:', error);
    return errorResponse(res, 'Failed to update video', 500);
  }
};

exports.deleteVideo = async (req, res) => {
  try {
    const { videoId } = req.params;
    const userId = req.user.user_id;

    const video = await Video.findOne({ unique_key: videoId });
    if (!video) {
      return errorResponse(res, 'Video not found', 404);
    }

    // Check if user is the owner
    if (video.user_id !== userId) {
      return errorResponse(res, 'Not authorized to delete this video', 403);
    }

    // In a real implementation, you'd also delete files from MinIO
    await Video.deleteOne({ _id: video._id });

    return successResponse(res, {
      success: true,
      message: 'Video deleted successfully',
    });
  } catch (error) {
    logger.error('Error deleting video:', error);
    return errorResponse(res, 'Failed to delete video', 500);
  }
};

exports.getMyVideos = async (req, res) => {
  try {
    const userId = req.user.user_id;
    const {
      page = 1,
      limit = DEFAULT_PAGE_SIZE,
      sort = 'uploaded_at',
      order = 'desc',
      status,
    } = req.query;

    logger.info(`Fetching videos for user: ${userId}, query: ${JSON.stringify(req.query)}`);

    const query = { user_id: userId };
    
    if (status) {
      query.status = status;
    }

    logger.info(`Database query: ${JSON.stringify(query)}`);

    const totalCount = await Video.countDocuments(query);
    logger.info(`Total videos found: ${totalCount}`);

    const sortObj = { [sort]: order === 'asc' ? 1 : -1 };

    const videos = await Video.find(query)
      .sort(sortObj)
      .skip((page - 1) * limit)
      .limit(Number(limit))
      .select('unique_key title description thumbnail_urls duration_seconds status visibility views_count likes_count uploaded_at published_at');

    logger.info(`Videos returned: ${videos.length}`);

    return successResponse(res, {
      videos: videos.map(video => ({
        id: video.unique_key,
        title: video.title,
        description: video.description,
        thumbnail_url: video.thumbnail_urls?.small,
        duration_seconds: video.duration_seconds,
        status: video.status,
        visibility: video.visibility,
        views_count: video.views_count,
        likes_count: video.likes_count,
        uploaded_at: video.uploaded_at,
        published_at: video.published_at,
      })),
      total_count: totalCount,
      page: Number(page),
      total_pages: Math.ceil(totalCount / limit),
    });
  } catch (error) {
    logger.error('Error fetching user videos:', error);
    return errorResponse(res, 'Failed to fetch user videos', 500);
  }
};

exports.pollVideoStatuses = async (req, res) => {
  try {
    const userId = req.user.user_id;
    const { video_ids } = req.query;

    if (!video_ids) {
      return errorResponse(res, 'video_ids parameter is required', 400);
    }

    const videoIds = video_ids.split(',').map(id => id.trim());
    
    if (videoIds.length === 0) {
      return errorResponse(res, 'At least one video ID is required', 400);
    }

    const videos = await Video.find({ 
      unique_key: { $in: videoIds }, 
      user_id: userId 
    }).select('unique_key status published_at');

    const statuses = {};
    videos.forEach(video => {
      statuses[video.unique_key] = {
        status: video.status,
        published_at: video.published_at
      };
    });

    return successResponse(res, {
      statuses,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    logger.error('Error polling video statuses:', error);
    return errorResponse(res, 'Failed to poll video statuses', 500);
  }
};

exports.getVideoStatus = async (req, res) => {
  try {
    const { videoId } = req.params;
    const userId = req.user.user_id;

    const video = await Video.findOne({ unique_key: videoId })
      .select('user_id status published_at uploaded_at');

    if (!video) {
      return errorResponse(res, 'Video not found', 404);
    }

    if (video.user_id !== userId) {
      return errorResponse(res, 'Not authorized to view this video status', 403);
    }

    return successResponse(res, {
      id: videoId,
      status: video.status,
      published_at: video.published_at,
      uploaded_at: video.uploaded_at,
    });
  } catch (error) {
    logger.error('Error getting video status:', error);
    return errorResponse(res, 'Failed to get video status', 500);
  }
};
