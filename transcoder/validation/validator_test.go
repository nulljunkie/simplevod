package validation

import (
	"testing"
	"transcoder/models"

	"github.com/stretchr/testify/assert"
)

func TestMessageValidator_ValidateMessage_ValidMessage(t *testing.T) {
	validator := NewMessageValidator()

	message := &models.Message{
		MessageID:          1,
		VideoURL:           "https://example.com/video.mp4",
		VideoID:            "test-video-123",
		Timestamps:         []float64{0.0, 10.5, 20.0, 30.75},
		TotalVideoDuration: 120.5,
		TotalMessages:      4,
	}

	errors := validator.ValidateMessage(message)

	assert.Empty(t, errors)
	assert.True(t, validator.IsValidMessage(message))
}

func TestMessageValidator_ValidateMessage_EmptyVideoID(t *testing.T) {
	validator := NewMessageValidator()

	message := &models.Message{
		MessageID:          1,
		VideoURL:           "https://example.com/video.mp4",
		VideoID:            "",
		Timestamps:         []float64{0.0, 10.5},
		TotalVideoDuration: 60.0,
		TotalMessages:      2,
	}

	errors := validator.ValidateMessage(message)

	assert.NotEmpty(t, errors)
	assert.False(t, validator.IsValidMessage(message))

	hasVideoIDError := false
	for _, err := range errors {
		if err.Field == "video_id" && err.Message == "video ID cannot be empty" {
			hasVideoIDError = true
			break
		}
	}
	assert.True(t, hasVideoIDError)
}

func TestMessageValidator_ValidateMessage_InvalidTimestamps(t *testing.T) {
	validator := NewMessageValidator()

	message := &models.Message{
		MessageID:          1,
		VideoURL:           "https://example.com/video.mp4",
		VideoID:            "test-video",
		Timestamps:         []float64{10.0, 5.0, 20.0},
		TotalVideoDuration: 60.0,
		TotalMessages:      3,
	}

	errors := validator.ValidateMessage(message)

	assert.NotEmpty(t, errors)

	hasTimestampError := false
	for _, err := range errors {
		if err.Field == "timestamps" && err.Message == "timestamps must be in ascending order at index 1" {
			hasTimestampError = true
			break
		}
	}
	assert.True(t, hasTimestampError)
}

func TestMessageValidator_ValidateVideoID_TooLong(t *testing.T) {
	validator := NewMessageValidator()

	longVideoID := "this-is-a-very-long-video-id-that-exceeds-the-maximum-allowed-length-for-video-identifiers-in-the-system"
	errors := validator.validateVideoID(longVideoID)

	assert.NotEmpty(t, errors)
	assert.Equal(t, "video_id", errors[0].Field)
	assert.Contains(t, errors[0].Message, "exceeds maximum length")
}

func TestMessageValidator_ValidateVideoID_InvalidCharacters(t *testing.T) {
	validator := NewMessageValidator()

	invalidVideoID := "@#$%^&*()"
	errors := validator.validateVideoID(invalidVideoID)

	assert.NotEmpty(t, errors)

	hasInvalidCharsError := false
	for _, err := range errors {
		if err.Field == "video_id" && err.Message == "video ID contains only invalid characters" {
			hasInvalidCharsError = true
			break
		}
	}
	assert.True(t, hasInvalidCharsError)
}

func TestMessageValidator_ValidateVideoURL_InvalidFormat(t *testing.T) {
	validator := NewMessageValidator()

	invalidURL := "not-a-valid-url"
	errors := validator.validateVideoURL(invalidURL)

	assert.NotEmpty(t, errors)
	assert.Equal(t, "video_url", errors[0].Field)
	assert.Contains(t, errors[0].Message, "format is invalid")
}

func TestMessageValidator_ValidateTimestamps_NegativeValues(t *testing.T) {
	validator := NewMessageValidator()

	timestamps := []float64{-5.0, 0.0, 10.0}
	errors := validator.validateTimestamps(timestamps)

	assert.NotEmpty(t, errors)
	assert.Equal(t, "timestamps", errors[0].Field)
	assert.Contains(t, errors[0].Message, "cannot be negative")
}

func TestMessageValidator_ValidateTimestamps_Empty(t *testing.T) {
	validator := NewMessageValidator()

	timestamps := []float64{}
	errors := validator.validateTimestamps(timestamps)

	assert.NotEmpty(t, errors)
	assert.Equal(t, "timestamps", errors[0].Field)
	assert.Equal(t, "timestamps array cannot be empty", errors[0].Message)
}

func TestMessageValidator_ValidateTimestamps_TooMany(t *testing.T) {
	validator := &MessageValidator{maxTimestamps: 2}

	timestamps := []float64{0.0, 10.0, 20.0}
	errors := validator.validateTimestamps(timestamps)

	assert.NotEmpty(t, errors)
	assert.Equal(t, "timestamps", errors[0].Field)
	assert.Contains(t, errors[0].Message, "too many timestamps")
}

func TestJobConfigValidator_ValidateJobConfig_ValidConfig(t *testing.T) {
	validator := NewJobConfigValidator()

	config := &models.JobConfig{
		SegmentID:     1,
		Resolution:    "720p",
		VideoID:       "test-video",
		VideoURL:      "https://example.com/video.mp4",
		TimestampData: "0.0\n10.5\n20.0",
		CRF:           28,
		Preset:        "fast",
		Image:         "transcode:latest",
		Namespace:     "default",
		OutputBucket:  "output-bucket",
		RedisHost:     "redis-host",
		RedisPort:     6379,
	}

	errors := validator.ValidateJobConfig(config)

	assert.Empty(t, errors)
	assert.True(t, validator.IsValidJobConfig(config))
}

func TestJobConfigValidator_ValidateJobConfig_InvalidCRF(t *testing.T) {
	validator := NewJobConfigValidator()

	config := &models.JobConfig{
		SegmentID:     1,
		Resolution:    "720p",
		VideoID:       "test-video",
		VideoURL:      "https://example.com/video.mp4",
		TimestampData: "0.0\n10.5",
		CRF:           100,
		Preset:        "fast",
		Image:         "transcode:latest",
		Namespace:     "default",
		OutputBucket:  "output-bucket",
		RedisHost:     "redis-host",
		RedisPort:     6379,
	}

	errors := validator.ValidateJobConfig(config)

	assert.NotEmpty(t, errors)

	hasCRFError := false
	for _, err := range errors {
		if err.Field == "crf" && err.Message == "CRF must be between 1 and 51" {
			hasCRFError = true
			break
		}
	}
	assert.True(t, hasCRFError)
}

func TestJobConfigValidator_ValidateJobConfig_InvalidPreset(t *testing.T) {
	validator := NewJobConfigValidator()

	config := &models.JobConfig{
		SegmentID:     1,
		Resolution:    "720p",
		VideoID:       "test-video",
		VideoURL:      "https://example.com/video.mp4",
		TimestampData: "0.0\n10.5",
		CRF:           28,
		Preset:        "invalid-preset",
		Image:         "transcode:latest",
		Namespace:     "default",
		OutputBucket:  "output-bucket",
		RedisHost:     "redis-host",
		RedisPort:     6379,
	}

	errors := validator.ValidateJobConfig(config)

	assert.NotEmpty(t, errors)

	hasPresetError := false
	for _, err := range errors {
		if err.Field == "preset" && err.Message == "preset must be one of: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow" {
			hasPresetError = true
			break
		}
	}
	assert.True(t, hasPresetError)
}

func TestJobConfigValidator_ValidateJobConfig_InvalidRedisPort(t *testing.T) {
	validator := NewJobConfigValidator()

	config := &models.JobConfig{
		SegmentID:     1,
		Resolution:    "720p",
		VideoID:       "test-video",
		VideoURL:      "https://example.com/video.mp4",
		TimestampData: "0.0\n10.5",
		CRF:           28,
		Preset:        "fast",
		Image:         "transcode:latest",
		Namespace:     "default",
		OutputBucket:  "output-bucket",
		RedisHost:     "redis-host",
		RedisPort:     70000,
	}

	errors := validator.ValidateJobConfig(config)

	assert.NotEmpty(t, errors)

	hasPortError := false
	for _, err := range errors {
		if err.Field == "redis_port" && err.Message == "Redis port must be between 1 and 65535" {
			hasPortError = true
			break
		}
	}
	assert.True(t, hasPortError)
}

func TestJobConfigValidator_ValidateJobConfig_EmptyRequiredFields(t *testing.T) {
	validator := NewJobConfigValidator()

	config := &models.JobConfig{}

	errors := validator.ValidateJobConfig(config)

	assert.NotEmpty(t, errors)

	requiredFields := []string{"segment_id", "resolution", "video_id", "video_url", "timestamp_data", "image", "namespace", "output_bucket", "redis_host"}
	foundFields := make(map[string]bool)

	for _, err := range errors {
		for _, field := range requiredFields {
			if err.Field == field {
				foundFields[field] = true
			}
		}
	}

	assert.True(t, len(foundFields) > 0, "Should have validation errors for required fields")
}

func TestValidationError_Error(t *testing.T) {
	err := ValidationError{
		Field:   "test_field",
		Message: "test message",
	}

	expected := "validation failed for test_field: test message"
	assert.Equal(t, expected, err.Error())
}

func TestMessageValidator_IsValidURL(t *testing.T) {
	validator := NewMessageValidator()

	testCases := []struct {
		url      string
		expected bool
	}{
		{"https://example.com/video.mp4", true},
		{"http://example.com/video.mp4", true},
		{"ftp://example.com/video.mp4", true},
		{"invalid-url", false},
		{"", false},
		{"file:///local/video.mp4", false},
	}

	for _, tc := range testCases {
		result := validator.isValidURL(tc.url)
		assert.Equal(t, tc.expected, result, "Failed for URL: %s", tc.url)
	}
}

func TestJobConfigValidator_IsValidPreset(t *testing.T) {
	validator := NewJobConfigValidator()

	validPresets := []string{"ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"}
	invalidPresets := []string{"invalid", "", "FAST", "Ultra-fast"}

	for _, preset := range validPresets {
		assert.True(t, validator.isValidPreset(preset), "Should be valid: %s", preset)
	}

	for _, preset := range invalidPresets {
		assert.False(t, validator.isValidPreset(preset), "Should be invalid: %s", preset)
	}
}

