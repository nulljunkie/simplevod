package handlers

import (
	"context"
	"encoding/json"
	"errors"
	"testing"
	"transcoder/config"
	"transcoder/models"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// Mocks
type MockJobSubmitter struct {
	mock.Mock
}

func (m *MockJobSubmitter) SubmitJob(ctx context.Context, cfg models.JobConfig) error {
	args := m.Called(ctx, cfg)
	return args.Error(0)
}

type MockRedisClient struct {
	mock.Mock
}

func (m *MockRedisClient) StoreMasterPaylistMetadata(ctx context.Context, videoID string, masterPlaylist config.MasterPlaylistMap) error {
	args := m.Called(ctx, videoID, masterPlaylist)
	return args.Error(0)
}

func (m *MockRedisClient) InitializeJobCounters(ctx context.Context, videoID, resolution string, totalJobs int) error {
	args := m.Called(ctx, videoID, resolution, totalJobs)
	return args.Error(0)
}

func (m *MockRedisClient) GetTotalJobsKey(videoID string) string {
	args := m.Called(videoID)
	return args.String(0)
}

func (m *MockRedisClient) GetCompletedJobsKey(videoID string) string {
	args := m.Called(videoID)
	return args.String(0)
}

func (m *MockRedisClient) GetMasterPlaylistKey(videoID string) string {
	args := m.Called(videoID)
	return args.String(0)
}

func (m *MockRedisClient) Close() error {
	args := m.Called()
	return args.Error(0)
}

func TestMessageHandler_Process_Success(t *testing.T) {
	// Arrange
	mockJobSubmitter := new(MockJobSubmitter)
	mockRedisClient := new(MockRedisClient)

	cfg := &config.Config{
		Transcode: config.TranscodeConfig{
			Resolutions:    []string{"360p"},
			CRFMap:         config.CRFMapping{"360p": 30},
			MasterPlaylist: config.MasterPlaylistMap{"360p": 800000},
		},
	}

	messageHandler := NewMessageHandler(cfg, mockJobSubmitter, mockRedisClient)

	msg := &models.Message{
		VideoID:            "testVideo",
		MessageID:          1,
		VideoURL:           "https://example.com/video.mp4",
		Timestamps:         []float64{0, 1, 2},
		TotalVideoDuration: 60.0,
		TotalMessages:      1,
	}
	body, _ := json.Marshal(msg)

	mockRedisClient.On("StoreMasterPaylistMetadata", mock.Anything, msg.VideoID, cfg.Transcode.MasterPlaylist).Return(nil)
	mockRedisClient.On("InitializeJobCounters", mock.Anything, msg.VideoID, "360p", msg.TotalMessages).Return(nil)
	mockRedisClient.On("GetTotalJobsKey", msg.VideoID).Return("transcode:jobs:testVideo:total")
	mockRedisClient.On("GetCompletedJobsKey", msg.VideoID).Return("transcode:jobs:testVideo:completed")
	mockRedisClient.On("GetMasterPlaylistKey", msg.VideoID).Return("transcode:playlists:testVideo:meta")
	mockJobSubmitter.On("SubmitJob", mock.Anything, mock.AnythingOfType("models.JobConfig")).Return(nil)

	// Act
	err := messageHandler.Process(context.Background(), body)

	// Assert
	assert.NoError(t, err)
	mockJobSubmitter.AssertExpectations(t)
	mockRedisClient.AssertExpectations(t)
}

func TestMessageHandler_Process_UnmarshalError(t *testing.T) {
	// Arrange
	messageHandler := NewMessageHandler(nil, nil, nil)
	body := []byte("invalid json")

	// Act
	err := messageHandler.Process(context.Background(), body)

	// Assert
	assert.Nil(t, err)
}

func TestMessageHandler_Process_SubmitJobError(t *testing.T) {
	// Arrange
	mockJobSubmitter := new(MockJobSubmitter)
	mockRedisClient := new(MockRedisClient)

	cfg := &config.Config{
		Transcode: config.TranscodeConfig{
			Resolutions:    []string{"360p"},
			CRFMap:         config.CRFMapping{"360p": 30},
			MasterPlaylist: config.MasterPlaylistMap{"360p": 800000},
		},
	}

	messageHandler := NewMessageHandler(cfg, mockJobSubmitter, mockRedisClient)

	msg := &models.Message{
		VideoID:            "testVideo",
		MessageID:          1,
		VideoURL:           "https://example.com/video.mp4",
		Timestamps:         []float64{0, 1, 2},
		TotalVideoDuration: 60.0,
		TotalMessages:      1,
	}
	body, _ := json.Marshal(msg)

	submitErr := errors.New("submit job error")
	mockRedisClient.On("StoreMasterPaylistMetadata", mock.Anything, msg.VideoID, cfg.Transcode.MasterPlaylist).Return(nil)
	mockRedisClient.On("InitializeJobCounters", mock.Anything, msg.VideoID, "360p", msg.TotalMessages).Return(nil)
	mockRedisClient.On("GetTotalJobsKey", msg.VideoID).Return("transcode:jobs:testVideo:total")
	mockRedisClient.On("GetCompletedJobsKey", msg.VideoID).Return("transcode:jobs:testVideo:completed")
	mockRedisClient.On("GetMasterPlaylistKey", msg.VideoID).Return("transcode:playlists:testVideo:meta")
	mockJobSubmitter.On("SubmitJob", mock.Anything, mock.AnythingOfType("models.JobConfig")).Return(submitErr)

	// Act
	err := messageHandler.Process(context.Background(), body)

	// Assert
	assert.Error(t, err)
	assert.Contains(t, err.Error(), submitErr.Error())
	mockJobSubmitter.AssertExpectations(t)
	mockRedisClient.AssertExpectations(t)
}
