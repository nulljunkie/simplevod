package redis

import (
	"context"
	"testing"
	"transcoder/config"

	"github.com/stretchr/testify/assert"
)

func TestClient_GetKeys(t *testing.T) {
	cfg := &config.RedisConfig{
		Host:     "localhost",
		Port:     6379,
		Password: "",
		DB:       0,
	}

	client := &client{cfg: cfg}

	videoID := "test-video-123"

	totalKey := client.GetTotalJobsKey(videoID)
	completedKey := client.GetCompletedJobsKey(videoID)
	masterKey := client.GetMasterPlaylistKey(videoID)

	assert.Equal(t, "transcode:jobs:test-video-123:total", totalKey)
	assert.Equal(t, "transcode:jobs:test-video-123:completed", completedKey)
	assert.Equal(t, "transcode:playlists:test-video-123:meta", masterKey)
}

func TestClient_KeyGeneration_WithSpecialCharacters(t *testing.T) {
	cfg := &config.RedisConfig{}
	client := &client{cfg: cfg}

	videoID := "video@with#special$chars"

	totalKey := client.GetTotalJobsKey(videoID)
	completedKey := client.GetCompletedJobsKey(videoID)
	masterKey := client.GetMasterPlaylistKey(videoID)

	assert.Contains(t, totalKey, videoID)
	assert.Contains(t, completedKey, videoID)
	assert.Contains(t, masterKey, videoID)

	assert.Contains(t, totalKey, "transcode:jobs:")
	assert.Contains(t, totalKey, ":total")
	assert.Contains(t, completedKey, ":completed")
	assert.Contains(t, masterKey, "transcode:playlists:")
	assert.Contains(t, masterKey, ":meta")
}

func TestClient_KeyGeneration_EmptyVideoID(t *testing.T) {
	cfg := &config.RedisConfig{}
	client := &client{cfg: cfg}

	videoID := ""

	totalKey := client.GetTotalJobsKey(videoID)
	completedKey := client.GetCompletedJobsKey(videoID)
	masterKey := client.GetMasterPlaylistKey(videoID)

	assert.Equal(t, "transcode:jobs::total", totalKey)
	assert.Equal(t, "transcode:jobs::completed", completedKey)
	assert.Equal(t, "transcode:playlists::meta", masterKey)
}

func TestClient_KeyGeneration_LongVideoID(t *testing.T) {
	cfg := &config.RedisConfig{}
	client := &client{cfg: cfg}

	videoID := "this-is-a-very-long-video-id-that-might-cause-issues-with-key-generation-if-not-handled-properly"

	totalKey := client.GetTotalJobsKey(videoID)
	completedKey := client.GetCompletedJobsKey(videoID)
	masterKey := client.GetMasterPlaylistKey(videoID)

	assert.Contains(t, totalKey, videoID)
	assert.Contains(t, completedKey, videoID)
	assert.Contains(t, masterKey, videoID)
}

func TestStoreMasterPlaylistMetadata_Integration(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	cfg := &config.RedisConfig{
		Host:     "localhost",
		Port:     6379,
		Password: "",
		DB:       15,
	}

	client, err := NewClient(cfg)
	if err != nil {
		t.Skip("Redis not available for integration test")
	}
	defer client.Close()

	videoID := "integration-test-video"
	masterPlaylist := config.MasterPlaylistMap{
		"240":  500000,
		"360":  800000,
		"720":  2000000,
		"1080": 5000000,
	}

	ctx := context.Background()
	err = client.StoreMasterPaylistMetadata(ctx, videoID, masterPlaylist)

	assert.NoError(t, err)
}

func TestInitializeJobCounters_Integration(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	cfg := &config.RedisConfig{
		Host:     "localhost",
		Port:     6379,
		Password: "",
		DB:       15,
	}

	client, err := NewClient(cfg)
	if err != nil {
		t.Skip("Redis not available for integration test")
	}
	defer client.Close()

	videoID := "integration-test-video-counters"
	resolution := "720p"
	totalJobs := 10

	ctx := context.Background()
	err = client.InitializeJobCounters(ctx, videoID, resolution, totalJobs)

	assert.NoError(t, err)
}

