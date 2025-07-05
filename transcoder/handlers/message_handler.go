package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"strconv"
	"strings"
	"sync"
	"transcoder/config"
	"transcoder/kubernetes"
	"transcoder/models"
	"transcoder/rabbitmq"
	"transcoder/redis"
	"transcoder/validation"
)

type MessageHandler struct {
	configuration       *config.Config
	jobSubmitter        kubernetes.JobSubmitter
	redisClient         redis.RedisClient
	statusPublisher     *rabbitmq.StatusPublisher
	initializationMutex sync.Mutex
	initializedVideos   map[string]bool
	messageValidator    *validation.MessageValidator
	jobConfigValidator  *validation.JobConfigValidator
}

func NewMessageHandler(cfg *config.Config, jobSubmitter kubernetes.JobSubmitter, redisClient redis.RedisClient) *MessageHandler {
	statusPublisher := rabbitmq.NewStatusPublisher(&cfg.RabbitMQ)
	return &MessageHandler{
		configuration:      cfg,
		jobSubmitter:       jobSubmitter,
		redisClient:        redisClient,
		statusPublisher:    statusPublisher,
		initializedVideos:  make(map[string]bool),
		messageValidator:   validation.NewMessageValidator(),
		jobConfigValidator: validation.NewJobConfigValidator(),
	}
}

func (h *MessageHandler) Process(ctx context.Context, body []byte) error {
	message, err := h.parseMessage(body)
	if err != nil {
		h.logUnmarshalError(err)
		return nil
	}

	if !h.isValidMessage(message) {
		h.logInvalidMessage(message)
		return nil
	}

	h.logProcessingStart(message)

	// Publish "transcoding" status when we first start processing a video
	if h.isFirstMessageForVideo(message) {
		metadata := map[string]interface{}{
			"video_url": message.VideoURL,
			"total_messages": message.TotalMessages,
		}
		if err := h.statusPublisher.PublishStatus(message.VideoID, "transcoding", metadata, nil); err != nil {
			log.Printf("Failed to publish transcoding status for video %s: %v", message.VideoID, err)
			// Continue processing even if status publishing fails
		}
	}

	timestampData := h.formatTimestamps(message.Timestamps)
	if h.hasNoTimestamps(timestampData) {
		h.logNoTimestampsWarning(message)
		return nil
	}

	if err := h.processTranscodeJobs(ctx, message, timestampData); err != nil {
		// Publish "failed" status if job processing fails
		errorMsg := err.Error()
		metadata := map[string]interface{}{
			"video_url": message.VideoURL,
			"message_id": message.MessageID,
		}
		if statusErr := h.statusPublisher.PublishStatus(message.VideoID, "failed", metadata, &errorMsg); statusErr != nil {
			log.Printf("Failed to publish failed status for video %s: %v", message.VideoID, statusErr)
		}
		return err
	}

	h.logProcessingComplete(message)
	return nil
}

func (h *MessageHandler) parseMessage(body []byte) (*models.Message, error) {
	var message models.Message
	if err := json.Unmarshal(body, &message); err != nil {
		return nil, fmt.Errorf("failed to parse message: %w", err)
	}
	return &message, nil
}

func (h *MessageHandler) formatTimestamps(timestamps []float64) string {
	if len(timestamps) == 0 {
		return ""
	}
	return h.buildTimestampString(timestamps)
}

func (h *MessageHandler) processTranscodeJobs(ctx context.Context, message *models.Message, timestampData string) error {
	resolutions := h.configuration.Transcode.Resolutions
	errorChannel := make(chan error, len(resolutions))
	workGroup := &sync.WaitGroup{}

	for _, resolution := range resolutions {
		h.processResolutionAsync(ctx, message, timestampData, resolution, workGroup, errorChannel)
	}

	workGroup.Wait()
	close(errorChannel)

	return h.handleJobErrors(errorChannel)
}

func (h *MessageHandler) ensureVideoInitialized(ctx context.Context, videoID, resolution string, totalMessages int) error {
	initializationKey := h.createInitializationKey(videoID, resolution)

	if h.isVideoInitialized(initializationKey) {
		return nil
	}

	h.markVideoAsInitialized(initializationKey)

	if err := h.initializeRedisState(ctx, videoID, resolution, totalMessages); err != nil {
		return err
	}

	h.logInitializationComplete(videoID, resolution)
	return nil
}

func (h *MessageHandler) createTranscodeJob(ctx context.Context, message *models.Message, timestampData, resolution string) error {
	crfValue, exists := h.getCRFValue(resolution)
	if !exists {
		return h.createCRFNotFoundError(resolution)
	}

	jobConfig := h.buildJobConfig(message, timestampData, resolution, crfValue)

	if err := h.jobSubmitter.SubmitJob(ctx, jobConfig); err != nil {
		h.logJobCreationError(message, resolution, err)
		return fmt.Errorf("kubernetes job creation failed for resolution %s: %w", resolution, err)
	}

	h.logJobCreationSuccess(message, resolution)
	return nil
}

func (h *MessageHandler) logUnmarshalError(err error) {
	log.Printf("Message parsing failed: %v", err)
}

func (h *MessageHandler) logProcessingStart(message *models.Message) {
	log.Printf("Processing video %s segment %d", message.VideoID, message.MessageID)
}

func (h *MessageHandler) hasNoTimestamps(timestampData string) bool {
	return timestampData == ""
}

func (h *MessageHandler) logNoTimestampsWarning(message *models.Message) {
	log.Printf("No timestamps found for video %s segment %d - skipping", message.VideoID, message.MessageID)
}

func (h *MessageHandler) logProcessingComplete(message *models.Message) {
	log.Printf("Processing complete for video %s segment %d", message.VideoID, message.MessageID)
}

func (h *MessageHandler) buildTimestampString(timestamps []float64) string {
	var builder strings.Builder
	for i, timestamp := range timestamps {
		builder.WriteString(strconv.FormatFloat(timestamp, 'f', 6, 64))
		if i < len(timestamps)-1 {
			builder.WriteString("\n")
		}
	}
	return builder.String()
}

func (h *MessageHandler) processResolutionAsync(ctx context.Context, message *models.Message, timestampData, resolution string, wg *sync.WaitGroup, errorChannel chan error) {
	wg.Add(1)
	go func(res string) {
		defer wg.Done()

		if err := h.ensureVideoInitialized(ctx, message.VideoID, res, message.TotalMessages); err != nil {
			errorChannel <- err
			return
		}

		if err := h.createTranscodeJob(ctx, message, timestampData, res); err != nil {
			errorChannel <- err
		}
	}(resolution)
}

func (h *MessageHandler) handleJobErrors(errorChannel chan error) error {
	var firstError error
	for err := range errorChannel {
		if firstError == nil {
			firstError = err
		}
		log.Printf("Transcode job error: %v", err)
	}

	if firstError != nil {
		return fmt.Errorf("transcode job processing failed: %w", firstError)
	}
	return nil
}

func (h *MessageHandler) createInitializationKey(videoID, resolution string) string {
	return fmt.Sprintf("%s-%s", videoID, resolution)
}

func (h *MessageHandler) isVideoInitialized(key string) bool {
	h.initializationMutex.Lock()
	defer h.initializationMutex.Unlock()
	return h.initializedVideos[key]
}

func (h *MessageHandler) markVideoAsInitialized(key string) {
	h.initializationMutex.Lock()
	defer h.initializationMutex.Unlock()
	h.initializedVideos[key] = true
}

func (h *MessageHandler) initializeRedisState(ctx context.Context, videoID, resolution string, totalMessages int) error {
	if err := h.storeMasterPlaylistMetadata(ctx, videoID); err != nil {
		return err
	}

	if err := h.initializeJobCounters(ctx, videoID, resolution, totalMessages); err != nil {
		return err
	}

	return nil
}

func (h *MessageHandler) storeMasterPlaylistMetadata(ctx context.Context, videoID string) error {
	if err := h.redisClient.StoreMasterPaylistMetadata(ctx, videoID, h.configuration.Transcode.MasterPlaylist); err != nil {
		log.Printf("Redis master playlist creation failed for video %s: %v", videoID, err)
		return fmt.Errorf("master playlist metadata storage failed for video %s: %w", videoID, err)
	}
	return nil
}

func (h *MessageHandler) initializeJobCounters(ctx context.Context, videoID, resolution string, totalMessages int) error {
	if err := h.redisClient.InitializeJobCounters(ctx, videoID, resolution, totalMessages); err != nil {
		log.Printf("Redis counter initialization failed for video %s resolution %s: %v", videoID, resolution, err)
		return fmt.Errorf("job counter initialization failed for resolution %s: %w", resolution, err)
	}
	return nil
}

func (h *MessageHandler) logInitializationComplete(videoID, resolution string) {
	log.Printf("Redis state initialized for video %s resolution %s", videoID, resolution)
}

func (h *MessageHandler) getCRFValue(resolution string) (int, bool) {
	crfValue, exists := h.configuration.Transcode.CRFMap[resolution]
	return crfValue, exists
}

func (h *MessageHandler) createCRFNotFoundError(resolution string) error {
	log.Printf("CRF value not found for resolution %s - skipping job", resolution)
	return fmt.Errorf("CRF configuration missing for resolution %s", resolution)
}

func (h *MessageHandler) buildJobConfig(message *models.Message, timestampData, resolution string, crfValue int) models.JobConfig {
	return models.JobConfig{
		SegmentID:               message.MessageID,
		Resolution:              resolution,
		VideoID:                 message.VideoID,
		VideoURL:                message.VideoURL,
		TimestampData:           timestampData,
		CRF:                     crfValue,
		Preset:                  h.configuration.Transcode.Preset,
		Image:                   h.configuration.Transcode.Image,
		Namespace:               h.configuration.Kubernetes.Namespace,
		OutputBucket:            h.configuration.Minio.OutputBucket,
		MinioSecretName:         h.configuration.Kubernetes.MinioSecretName,
		RabbitMQAdminSecretName: h.configuration.Kubernetes.RabbitMQAdminSecretName,
		RedisHost:               h.configuration.Redis.Host,
		RedisPort:               h.configuration.Redis.Port,
		RedisPassword:           h.configuration.Redis.Password,
		RedisDB:                 h.configuration.Redis.DB,
		TotalJobsKey:            h.redisClient.GetTotalJobsKey(message.VideoID),
		CompletedJobsKey:        h.redisClient.GetCompletedJobsKey(message.VideoID),
		MasterPlaylistMetaKey:   h.redisClient.GetMasterPlaylistKey(message.VideoID),
		MCConfigInitImage:       h.configuration.Kubernetes.MCConfigInitImage,
		MinioAlias:              h.configuration.Minio.Alias,
		RabbitMQExchange:        h.configuration.RabbitMQ.Exchange,
		RabbitMQRoutingKey:      h.configuration.RabbitMQ.RoutingKey,
		AllowHTTP:               h.configuration.Kubernetes.AllowHTTPJobArg,
	}
}

func (h *MessageHandler) logJobCreationError(message *models.Message, resolution string, err error) {
	log.Printf("Kubernetes job creation failed for video %s segment %d resolution %s: %v",
		message.VideoID, message.MessageID, resolution, err)
}

func (h *MessageHandler) logJobCreationSuccess(message *models.Message, resolution string) {
	log.Printf("Kubernetes job created successfully for video %s segment %d resolution %s",
		message.VideoID, message.MessageID, resolution)
}

func (h *MessageHandler) isValidMessage(message *models.Message) bool {
	return h.messageValidator.IsValidMessage(message)
}

func (h *MessageHandler) isFirstMessageForVideo(message *models.Message) bool {
	return message.MessageID == 1
}

func (h *MessageHandler) logInvalidMessage(message *models.Message) {
	validationErrors := h.messageValidator.ValidateMessage(message)
	log.Printf("Invalid message received for video %s segment %d:", message.VideoID, message.MessageID)
	for _, err := range validationErrors {
		log.Printf("  - %s", err.Error())
	}
}

