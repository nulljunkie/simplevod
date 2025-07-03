# Videos Service (Express.js)

This is the backend service responsible for managing video metadata, handling video streaming, and serving video content.

## How it Works

This service is built with Express.js and uses MongoDB (via Mongoose) for data storage. It serves as an API for the frontend application to interact with video data and initiate video streams. It integrates with a storage service (likely MinIO, as inferred from the overall project structure) to retrieve video segments for streaming.

### Core Technologies:
*   **Node.js & Express.js**: For building the RESTful API.
*   **MongoDB & Mongoose**: For database interactions and schema definition.
*   **JSON Web Tokens (JWT)**: For user authentication and protecting certain routes.
*   **HLS (HTTP Live Streaming)**: For adaptive video streaming.

### Request Flow:
1.  **Client Request**: The frontend or another service makes an HTTP request to an API endpoint (e.g., `/api/videos`, `/api/stream`).
2.  **Express.js Routing**: The request is routed to the appropriate controller based on the URL.
3.  **Middleware**: Authentication, validation, and other common tasks are handled by middleware.
4.  **Controller Logic**: The controller interacts with the Mongoose models to fetch or update data in MongoDB, or calls a service to handle streaming logic.
5.  **Service Interaction**: For streaming, the service interacts with the underlying storage to retrieve video manifest files (playlists) and segments.
6.  **Response**: The controller sends a JSON response or streams video content back to the client.

## Key Features & Endpoints

### Video Management (`/api/videos`)
*   `GET /`: List videos with pagination, sorting, and filtering (by visibility, tags, search query, user).
*   `GET /:videoId`: Get detailed information about a specific video.
*   `POST /:videoId/view`: Increment the view count for a video.
*   `POST /:videoId/like` (Protected): Increment the like count for a video.
*   `PUT /:videoId` (Protected): Update video metadata (title, description, tags, visibility) by video owner.
*   `DELETE /:videoId` (Protected): Delete a video by video owner.
*   `GET /:videoId/stream-status`: Get the streaming status of a video.



### Health Check
*   `GET /api/health`: Basic health check endpoint.

## Data Model (`Video`)

The `Video` schema in MongoDB stores comprehensive information about each video, including:
*   `unique_key`: Unique identifier for the video.
*   `title`, `description`, `original_filename`, `size_bytes`, `duration_seconds`.
*   `user_id`, `uploader_username`.
*   `status`: (e.g., `pending_metadata`, `transcoding`, `published`, `failed`).
*   `visibility`: (e.g., `public`, `unlisted`, `private`).
*   `raw_file_info`: Details about the original uploaded file (bucket, key).
*   `streaming_info`: URL for the main HLS stream.
*   `thumbnail_urls`: URLs for small and large thumbnails.
*   `tags`, `views_count`, `likes_count`.
*   `uploaded_at`, `published_at`, `last_modified_at`.

## Identified Issues, Bugs, and Areas for Improvement

1.  **Simplified `likeVideo` Implementation**: The `likeVideo` function in `src/controllers/video.controller.js` only increments a counter. In a production application, a separate mechanism (e.g., a `likes` collection or an array of user IDs on the `Video` model) should be used to track individual user likes, allowing for unliking and preventing multiple likes from the same user.
2.  **Manual Timestamp Management**: The `Video` schema sets `timestamps: false`, meaning `createdAt` and `updatedAt` are not automatically managed by Mongoose. While custom timestamps (`uploaded_at`, `published_at`, `last_modified_at`) are present, developers need to ensure these are consistently and correctly updated manually across all operations.
3.  **Comprehensive Testing**: While some validation is present, a full suite of unit, integration, and end-to-end tests is crucial to ensure the reliability, security, and correctness of all API endpoints and business logic.
4.  **More Specific Error Handling**: While a global error handler is in place, some specific error scenarios (e.g., database connection issues beyond initial startup, external service failures during streaming) could benefit from more granular error messages or retry mechanisms.
4.  **Simplified `likeVideo` Implementation**: The `likeVideo` function in `src/controllers/video.controller.js` only increments a counter. In a production application, a separate mechanism (e.g., a `likes` collection or an array of user IDs on the `Video` model) should be used to track individual user likes, allowing for unliking and preventing multiple likes from the same user.
5.  **Manual Timestamp Management**: The `Video` schema sets `timestamps: false`, meaning `createdAt` and `updatedAt` are not automatically managed by Mongoose. While custom timestamps (`uploaded_at`, `published_at`, `last_modified_at`) are present, developers need to ensure these are consistently and correctly updated manually across all operations.
6.  **Comprehensive Testing**: While some validation is present, a full suite of unit, integration, and end-to-end tests is crucial to ensure the reliability, security, and correctness of all API endpoints and business logic.
7.  **More Specific Error Handling**: While a global error handler is in place, some specific error scenarios (e.g., database connection issues beyond initial startup, external service failures during streaming) could benefit from more granular error messages or retry mechanisms.
