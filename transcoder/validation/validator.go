package validation

import (
	"fmt"
	"strings"
	"transcoder/models"
	"transcoder/utils"
)

type ValidationError struct {
	Field   string
	Message string
}

func (e ValidationError) Error() string {
	return fmt.Sprintf("validation failed for %s: %s", e.Field, e.Message)
}

type MessageValidator struct {
	maxVideoIDLength  int
	maxVideoURLLength int
	maxTimestamps     int
}

func NewMessageValidator() *MessageValidator {
	return &MessageValidator{
		maxVideoIDLength:  100,
		maxVideoURLLength: 500,
		maxTimestamps:     1000,
	}
}

func (v *MessageValidator) ValidateMessage(message *models.Message) []ValidationError {
	var errors []ValidationError

	errors = append(errors, v.validateVideoID(message.VideoID)...)
	errors = append(errors, v.validateVideoURL(message.VideoURL)...)
	errors = append(errors, v.validateMessageID(message.MessageID)...)
	errors = append(errors, v.validateTimestamps(message.Timestamps)...)
	errors = append(errors, v.validateTotalMessages(message.TotalMessages)...)
	errors = append(errors, v.validateVideoDuration(message.TotalVideoDuration)...)

	return errors
}

func (v *MessageValidator) IsValidMessage(message *models.Message) bool {
	return len(v.ValidateMessage(message)) == 0
}

func (v *MessageValidator) validateVideoID(videoID string) []ValidationError {
	var errors []ValidationError

	if videoID == "" {
		errors = append(errors, ValidationError{
			Field:   "video_id",
			Message: "video ID cannot be empty",
		})
		return errors
	}

	if len(videoID) > v.maxVideoIDLength {
		errors = append(errors, ValidationError{
			Field:   "video_id",
			Message: fmt.Sprintf("video ID exceeds maximum length of %d characters", v.maxVideoIDLength),
		})
	}

	sanitized := utils.SanitizeLabel(videoID)
	if sanitized == "default-label" {
		errors = append(errors, ValidationError{
			Field:   "video_id",
			Message: "video ID contains only invalid characters",
		})
	}

	if len(sanitized) > 63 {
		errors = append(errors, ValidationError{
			Field:   "video_id",
			Message: "video ID would exceed Kubernetes resource name limit after sanitization",
		})
	}

	return errors
}

func (v *MessageValidator) validateVideoURL(videoURL string) []ValidationError {
	var errors []ValidationError

	if videoURL == "" {
		errors = append(errors, ValidationError{
			Field:   "video_url",
			Message: "video URL cannot be empty",
		})
		return errors
	}

	if len(videoURL) > v.maxVideoURLLength {
		errors = append(errors, ValidationError{
			Field:   "video_url",
			Message: fmt.Sprintf("video URL exceeds maximum length of %d characters", v.maxVideoURLLength),
		})
	}

	if !v.isValidURL(videoURL) {
		errors = append(errors, ValidationError{
			Field:   "video_url",
			Message: "video URL format is invalid",
		})
	}

	return errors
}

func (v *MessageValidator) validateMessageID(messageID int) []ValidationError {
	var errors []ValidationError

	if messageID <= 0 {
		errors = append(errors, ValidationError{
			Field:   "message_id",
			Message: "message ID must be positive",
		})
	}

	return errors
}

func (v *MessageValidator) validateTimestamps(timestamps []float64) []ValidationError {
	var errors []ValidationError

	if len(timestamps) == 0 {
		errors = append(errors, ValidationError{
			Field:   "timestamps",
			Message: "timestamps array cannot be empty",
		})
		return errors
	}

	if len(timestamps) > v.maxTimestamps {
		errors = append(errors, ValidationError{
			Field:   "timestamps",
			Message: fmt.Sprintf("too many timestamps, maximum allowed: %d", v.maxTimestamps),
		})
	}

	for i, timestamp := range timestamps {
		if timestamp < 0 {
			errors = append(errors, ValidationError{
				Field:   "timestamps",
				Message: fmt.Sprintf("timestamp at index %d cannot be negative", i),
			})
		}

		if i > 0 && timestamp <= timestamps[i-1] {
			errors = append(errors, ValidationError{
				Field:   "timestamps",
				Message: fmt.Sprintf("timestamps must be in ascending order at index %d", i),
			})
		}
	}

	return errors
}

func (v *MessageValidator) validateTotalMessages(totalMessages int) []ValidationError {
	var errors []ValidationError

	if totalMessages <= 0 {
		errors = append(errors, ValidationError{
			Field:   "total_messages",
			Message: "total messages must be positive",
		})
	}

	return errors
}

func (v *MessageValidator) validateVideoDuration(duration float64) []ValidationError {
	var errors []ValidationError

	if duration <= 0 {
		errors = append(errors, ValidationError{
			Field:   "total_video_duration",
			Message: "video duration must be positive",
		})
	}

	if duration > 86400 {
		errors = append(errors, ValidationError{
			Field:   "total_video_duration",
			Message: "video duration exceeds maximum allowed (24 hours)",
		})
	}

	return errors
}

func (v *MessageValidator) isValidURL(url string) bool {
	return strings.HasPrefix(url, "http://") || strings.HasPrefix(url, "https://") || strings.HasPrefix(url, "ftp://")
}

type JobConfigValidator struct {
	maxNamespaceLength int
	supportedPresets   []string
}

func NewJobConfigValidator() *JobConfigValidator {
	return &JobConfigValidator{
		maxNamespaceLength: 63,
		supportedPresets:   []string{"ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"},
	}
}

func (v *JobConfigValidator) ValidateJobConfig(config *models.JobConfig) []ValidationError {
	var errors []ValidationError

	errors = append(errors, v.validateBasicFields(config)...)
	errors = append(errors, v.validateVideoFields(config)...)
	errors = append(errors, v.validateEncodingFields(config)...)
	errors = append(errors, v.validateInfrastructureFields(config)...)

	return errors
}

func (v *JobConfigValidator) IsValidJobConfig(config *models.JobConfig) bool {
	return len(v.ValidateJobConfig(config)) == 0
}

func (v *JobConfigValidator) validateBasicFields(config *models.JobConfig) []ValidationError {
	var errors []ValidationError

	if config.SegmentID <= 0 {
		errors = append(errors, ValidationError{
			Field:   "segment_id",
			Message: "segment ID must be positive",
		})
	}

	if config.Resolution == "" {
		errors = append(errors, ValidationError{
			Field:   "resolution",
			Message: "resolution cannot be empty",
		})
	}

	if config.VideoID == "" {
		errors = append(errors, ValidationError{
			Field:   "video_id",
			Message: "video ID cannot be empty",
		})
	}

	return errors
}

func (v *JobConfigValidator) validateVideoFields(config *models.JobConfig) []ValidationError {
	var errors []ValidationError

	if config.VideoURL == "" {
		errors = append(errors, ValidationError{
			Field:   "video_url",
			Message: "video URL cannot be empty",
		})
	}

	if config.TimestampData == "" {
		errors = append(errors, ValidationError{
			Field:   "timestamp_data",
			Message: "timestamp data cannot be empty",
		})
	}

	return errors
}

func (v *JobConfigValidator) validateEncodingFields(config *models.JobConfig) []ValidationError {
	var errors []ValidationError

	if config.CRF <= 0 || config.CRF > 51 {
		errors = append(errors, ValidationError{
			Field:   "crf",
			Message: "CRF must be between 1 and 51",
		})
	}

	if !v.isValidPreset(config.Preset) {
		errors = append(errors, ValidationError{
			Field:   "preset",
			Message: fmt.Sprintf("preset must be one of: %s", strings.Join(v.supportedPresets, ", ")),
		})
	}

	if config.Image == "" {
		errors = append(errors, ValidationError{
			Field:   "image",
			Message: "container image cannot be empty",
		})
	}

	return errors
}

func (v *JobConfigValidator) validateInfrastructureFields(config *models.JobConfig) []ValidationError {
	var errors []ValidationError

	if config.Namespace == "" {
		errors = append(errors, ValidationError{
			Field:   "namespace",
			Message: "Kubernetes namespace cannot be empty",
		})
	}

	if len(config.Namespace) > v.maxNamespaceLength {
		errors = append(errors, ValidationError{
			Field:   "namespace",
			Message: fmt.Sprintf("namespace exceeds maximum length of %d", v.maxNamespaceLength),
		})
	}

	if config.OutputBucket == "" {
		errors = append(errors, ValidationError{
			Field:   "output_bucket",
			Message: "output bucket cannot be empty",
		})
	}

	if config.RedisHost == "" {
		errors = append(errors, ValidationError{
			Field:   "redis_host",
			Message: "Redis host cannot be empty",
		})
	}

	if config.RedisPort <= 0 || config.RedisPort > 65535 {
		errors = append(errors, ValidationError{
			Field:   "redis_port",
			Message: "Redis port must be between 1 and 65535",
		})
	}

	return errors
}

func (v *JobConfigValidator) isValidPreset(preset string) bool {
	for _, supportedPreset := range v.supportedPresets {
		if preset == supportedPreset {
			return true
		}
	}
	return false
}

