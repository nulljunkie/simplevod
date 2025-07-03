package models

import (
	"encoding/json"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestMessage_JSONMarshaling(t *testing.T) {
	message := Message{
		MessageID:          123,
		VideoURL:           "https://example.com/video.mp4",
		VideoID:            "test-video-456",
		Timestamps:         []float64{0.0, 10.5, 20.0, 30.75},
		TotalVideoDuration: 120.5,
		TotalMessages:      4,
	}

	jsonData, err := json.Marshal(message)
	require.NoError(t, err)

	var unmarshaledMessage Message
	err = json.Unmarshal(jsonData, &unmarshaledMessage)
	require.NoError(t, err)

	assert.Equal(t, message.MessageID, unmarshaledMessage.MessageID)
	assert.Equal(t, message.VideoURL, unmarshaledMessage.VideoURL)
	assert.Equal(t, message.VideoID, unmarshaledMessage.VideoID)
	assert.Equal(t, message.Timestamps, unmarshaledMessage.Timestamps)
	assert.Equal(t, message.TotalVideoDuration, unmarshaledMessage.TotalVideoDuration)
	assert.Equal(t, message.TotalMessages, unmarshaledMessage.TotalMessages)
}

func TestMessage_JSONUnmarshaling_MissingFields(t *testing.T) {
	jsonData := `{
		"message_id": 1,
		"video_url": "https://example.com/video.mp4"
	}`

	var message Message
	err := json.Unmarshal([]byte(jsonData), &message)
	require.NoError(t, err)

	assert.Equal(t, 1, message.MessageID)
	assert.Equal(t, "https://example.com/video.mp4", message.VideoURL)
	assert.Empty(t, message.VideoID)
	assert.Empty(t, message.Timestamps)
	assert.Equal(t, float64(0), message.TotalVideoDuration)
	assert.Equal(t, 0, message.TotalMessages)
}

func TestMessage_JSONUnmarshaling_EmptyTimestamps(t *testing.T) {
	jsonData := `{
		"message_id": 1,
		"video_url": "https://example.com/video.mp4",
		"video_id": "test-video",
		"timestamps": [],
		"total_video_duration": 60.0,
		"total_messages": 1
	}`

	var message Message
	err := json.Unmarshal([]byte(jsonData), &message)
	require.NoError(t, err)

	assert.Equal(t, 1, message.MessageID)
	assert.Equal(t, "test-video", message.VideoID)
	assert.Empty(t, message.Timestamps)
	assert.Equal(t, 60.0, message.TotalVideoDuration)
}

func TestMessage_JSONUnmarshaling_InvalidJSON(t *testing.T) {
	invalidJSON := `{
		"message_id": "invalid",
		"timestamps": "not_an_array"
	}`

	var message Message
	err := json.Unmarshal([]byte(invalidJSON), &message)

	assert.Error(t, err)
}

func TestJobConfig_AllFieldsPresent(t *testing.T) {
	jobConfig := JobConfig{
		SegmentID:               1,
		Resolution:              "720p",
		VideoID:                 "test-video",
		VideoURL:                "https://example.com/video.mp4",
		TimestampData:           "0.0\n10.5\n20.0",
		CRF:                     28,
		Preset:                  "fast",
		Image:                   "transcode:latest",
		Namespace:               "default",
		OutputBucket:            "output-bucket",
		MinioSecretName:         "minio-secret",
		RabbitMQAdminSecretName: "rabbitmq-secret",
		RedisHost:               "redis-host",
		RedisPort:               6379,
		RedisPassword:           "redis-password",
		RedisDB:                 0,
		TotalJobsKey:            "total-jobs-key",
		CompletedJobsKey:        "completed-jobs-key",
		MasterPlaylistMetaKey:   "playlist-meta-key",
		MCConfigInitImage:       "alpine:latest",
		MinioAlias:              "minio-alias",
		RabbitMQExchange:        "video-exchange",
		RabbitMQRoutingKey:      "video.transcode",
		AllowHTTP:               true,
	}

	assert.Equal(t, 1, jobConfig.SegmentID)
	assert.Equal(t, "720p", jobConfig.Resolution)
	assert.Equal(t, "test-video", jobConfig.VideoID)
	assert.Equal(t, "https://example.com/video.mp4", jobConfig.VideoURL)
	assert.Equal(t, "0.0\n10.5\n20.0", jobConfig.TimestampData)
	assert.Equal(t, 28, jobConfig.CRF)
	assert.Equal(t, "fast", jobConfig.Preset)
	assert.Equal(t, "transcode:latest", jobConfig.Image)
	assert.Equal(t, "default", jobConfig.Namespace)
	assert.Equal(t, "output-bucket", jobConfig.OutputBucket)
	assert.Equal(t, "minio-secret", jobConfig.MinioSecretName)
	assert.Equal(t, "rabbitmq-secret", jobConfig.RabbitMQAdminSecretName)
	assert.Equal(t, "redis-host", jobConfig.RedisHost)
	assert.Equal(t, 6379, jobConfig.RedisPort)
	assert.Equal(t, "redis-password", jobConfig.RedisPassword)
	assert.Equal(t, 0, jobConfig.RedisDB)
	assert.Equal(t, "total-jobs-key", jobConfig.TotalJobsKey)
	assert.Equal(t, "completed-jobs-key", jobConfig.CompletedJobsKey)
	assert.Equal(t, "playlist-meta-key", jobConfig.MasterPlaylistMetaKey)
	assert.Equal(t, "alpine:latest", jobConfig.MCConfigInitImage)
	assert.Equal(t, "minio-alias", jobConfig.MinioAlias)
	assert.Equal(t, "video-exchange", jobConfig.RabbitMQExchange)
	assert.Equal(t, "video.transcode", jobConfig.RabbitMQRoutingKey)
	assert.True(t, jobConfig.AllowHTTP)
}

func TestJobConfig_DefaultValues(t *testing.T) {
	jobConfig := JobConfig{}

	assert.Equal(t, 0, jobConfig.SegmentID)
	assert.Empty(t, jobConfig.Resolution)
	assert.Empty(t, jobConfig.VideoID)
	assert.Empty(t, jobConfig.VideoURL)
	assert.Empty(t, jobConfig.TimestampData)
	assert.Equal(t, 0, jobConfig.CRF)
	assert.Empty(t, jobConfig.Preset)
	assert.Empty(t, jobConfig.Image)
	assert.Empty(t, jobConfig.Namespace)
	assert.Empty(t, jobConfig.OutputBucket)
	assert.False(t, jobConfig.AllowHTTP)
}

func TestMessage_ValidTimestamps(t *testing.T) {
	message := Message{
		MessageID:     1,
		VideoID:       "test-video",
		Timestamps:    []float64{0.0, 5.5, 10.0, 15.75, 20.0},
		TotalMessages: 5,
	}

	assert.Len(t, message.Timestamps, 5)
	assert.Equal(t, 0.0, message.Timestamps[0])
	assert.Equal(t, 5.5, message.Timestamps[1])
	assert.Equal(t, 20.0, message.Timestamps[4])
}

func TestMessage_EdgeCases(t *testing.T) {
	testCases := []struct {
		name    string
		message Message
	}{
		{
			name: "negative_message_id",
			message: Message{
				MessageID: -1,
				VideoID:   "test-video",
			},
		},
		{
			name: "zero_total_messages",
			message: Message{
				MessageID:     1,
				VideoID:       "test-video",
				TotalMessages: 0,
			},
		},
		{
			name: "negative_timestamps",
			message: Message{
				MessageID:  1,
				VideoID:    "test-video",
				Timestamps: []float64{-5.0, 0.0, 5.0},
			},
		},
		{
			name: "very_large_duration",
			message: Message{
				MessageID:          1,
				VideoID:            "test-video",
				TotalVideoDuration: 999999.99,
			},
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			assert.NotNil(t, tc.message)
		})
	}
}

