package redis

import (
	"context"
	"fmt"
	"log"
	"time"
	"transcoder/config"

	"github.com/redis/go-redis/v9"
)

type client struct {
	rdb *redis.Client
	cfg *config.RedisConfig
}

func NewClient(cfg *config.RedisConfig) (RedisClient, error) {
	rdb := redis.NewClient(&redis.Options{
		Addr:     fmt.Sprintf("%s:%d", cfg.Host, cfg.Port),
		Password: cfg.Password,
		DB:       cfg.DB,
	})

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_, err := rdb.Ping(ctx).Result()
	if err != nil {
		return nil, fmt.Errorf("failed to connect to Redis: %w", err)
	}

	log.Println("Successfully connected to Redis.")
	return &client{rdb: rdb, cfg: cfg}, nil
}

func (c *client) GetTotalJobsKey(videoID string) string {
	return fmt.Sprintf("transcode:jobs:%s:total", videoID)
}

func (c *client) GetCompletedJobsKey(videoID string) string {
	return fmt.Sprintf("transcode:jobs:%s:completed", videoID)
}

func (c *client) GetMasterPlaylistKey(videoID string) string {
	return fmt.Sprintf("transcode:playlists:%s:meta", videoID)
}

func (c *client) InitializeJobCounters(ctx context.Context, videoID, resolution string, totalJobs int) error {
	totalJobsKey := c.GetTotalJobsKey(videoID)
	completedJobsKey := c.GetCompletedJobsKey(videoID)

	pipe := c.rdb.Pipeline()

	pipe.SetNX(ctx, totalJobsKey, totalJobs, 0)
	pipe.HSetNX(ctx, completedJobsKey, resolution, 0)

	cmders, err := pipe.Exec(ctx)
	if err != nil && err != redis.Nil {
		return fmt.Errorf("redis pipeline error initializing counters for %s-%s: %w", videoID, resolution, err)
	}

	totalSetCmd, ok1 := cmders[0].(*redis.BoolCmd)
	completedSetCmd, ok2 := cmders[1].(*redis.BoolCmd)

	if !ok1 || !ok2 {
		return fmt.Errorf("unexpected command result types from redis pipeline for %s-%s", videoID, resolution)
	}

	if totalSetCmd.Err() != nil && totalSetCmd.Err() != redis.Nil {
		return fmt.Errorf("redis error setting total jobs for %s-%s: %w", videoID, resolution, totalSetCmd.Err())
	}
	if completedSetCmd.Err() != nil && completedSetCmd.Err() != redis.Nil {
		return fmt.Errorf("redis error setting completed jobs for %s-%s: %w", videoID, resolution, completedSetCmd.Err())
	}

	if totalSetCmd.Val() {
		log.Printf("Redis: Initialized '%s' to %d", totalJobsKey, totalJobs)
	} else {
		log.Printf("Redis: Key '%s' already exists.", totalJobsKey)
	}

	if completedSetCmd.Val() {
		log.Printf("Redis: Initialized '%s' to 0", completedJobsKey)
	} else {
		log.Printf("Redis: Key '%s' already exists.", completedJobsKey)
	}

	return nil
}

func (c *client) StoreMasterPaylistMetadata(ctx context.Context, videoID string, masterPlaylist config.MasterPlaylistMap) error {
	masterPlaylistKey := c.GetMasterPlaylistKey(videoID)

	for resolution, bitrate := range masterPlaylist {
		result, err := c.rdb.HSetNX(ctx, masterPlaylistKey, resolution, bitrate).Result()
		if err != nil {
			return fmt.Errorf("failed to set field %s in Redis: %v", resolution, err)
		}
		if result {
			log.Printf("Set master playlist field %s:%d in Redis", resolution, bitrate)
		} else {
			log.Printf("Field %s already exists in Redis, skipped", resolution)
		}
	}

	return nil
}

func (c *client) Close() error {
	if c.rdb != nil {
		return c.rdb.Close()
	}
	return nil
}

