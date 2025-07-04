package redis

import (
	"context"
	"transcoder/config"
)

type RedisClient interface {
	StoreMasterPaylistMetadata(ctx context.Context, videoID string, masterPlaylist config.MasterPlaylistMap) error
	InitializeJobCounters(ctx context.Context, videoID, resolution string, totalJobs int) error
	GetTotalJobsKey(videoID string) string
	GetCompletedJobsKey(videoID string) string
	GetMasterPlaylistKey(videoID string) string
	HealthCheck(ctx context.Context) error
	Close() error
}
