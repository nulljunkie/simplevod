package config

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/joho/godotenv"
)

type (
	CRFMapping        map[string]int
	MasterPlaylistMap map[string]int

	Config struct {
		RabbitMQ   RabbitMQConfig
		Redis      RedisConfig
		Kubernetes KubernetesConfig
		Minio      MinioConfig
		Transcode  TranscodeConfig
		App        AppConfig
		Health     HealthConfig
	}

	RabbitMQConfig struct {
		Host         string
		Port         int
		Vhost        string
		User         string
		Pass         string
		ConsumeQueue string
		Prefetch     int
		Exchange     string
		RoutingKey   string
	}

	RedisConfig struct {
		Host     string
		Port     int
		Password string
		DB       int
	}

	KubernetesConfig struct {
		Namespace               string
		MinioSecretName         string
		RabbitMQAdminSecretName string
		MCConfigInitImage       string
		AllowHTTPJobArg         bool
	}

	MinioConfig struct {
		Endpoint     string
		AccessKey    string
		SecretKey    string
		UseSSL       bool
		OutputBucket string
		Alias        string
	}

	TranscodeConfig struct {
		Image          string
		Preset         string
		Resolutions    []string
		CRFMap         CRFMapping
		MasterPlaylist MasterPlaylistMap
	}

	AppConfig struct {
		MaxConcurrentHandlers int
		RetryInterval         time.Duration
	}

	HealthConfig struct {
		Port int
	}
)

func Load() (*Config, error) {
	_ = godotenv.Load()

	transcodeConfig, err := loadTranscodeConfig()
	if err != nil {
		return nil, err
	}

	return &Config{
		RabbitMQ:   loadRabbitMQConfig(),
		Redis:      loadRedisConfig(),
		Kubernetes: loadKubernetesConfig(),
		Minio:      loadMinioConfig(),
		Transcode:  transcodeConfig,
		App:        loadAppConfig(),
		Health:     loadHealthConfig(),
	}, nil
}

func loadRabbitMQConfig() RabbitMQConfig {
	return RabbitMQConfig{
		Host:         getEnv("RABBITMQ_HOST", "localhost"),
		Port:         getEnvAsInt("RABBITMQ_PORT", 5672),
		Vhost:        getEnv("RABBITMQ_VHOST", "/"),
		User:         getEnv("RABBITMQ_USER", "guest"),
		Pass:         getEnv("RABBITMQ_PASSWORD", "guest"),
		ConsumeQueue: getEnv("RABBITMQ_CONSUME_QUEUE", "video_segment_queue"),
		Prefetch:     getEnvAsInt("RABBITMQ_PREFETCH", 5),
		Exchange:     getEnv("DEFAULT_RABBITMQ_EXCHANGE", "video"),
		RoutingKey:   getEnv("DEFAULT_RABBITMQ_ROUTING_KEY", "video.playlist"),
	}
}

func loadRedisConfig() RedisConfig {
	return RedisConfig{
		Host:     getEnv("REDIS_HOST", "localhost"),
		Port:     getEnvAsInt("REDIS_PORT", 6379),
		Password: getEnv("REDIS_PASSWORD", ""),
		DB:       getEnvAsInt("REDIS_DB", 0),
	}
}

func loadKubernetesConfig() KubernetesConfig {
	return KubernetesConfig{
		Namespace:               getEnv("KUBERNETES_NAMESPACE", "default"),
		MinioSecretName:         getEnv("MINIO_SECRET_NAME", "minio-secret"),
		RabbitMQAdminSecretName: getEnv("RABBITMQ_ADMIN_SECRET_NAME", "rabbitmq-admin-secret"),
		MCConfigInitImage:       getEnv("MC_CONFIG_INIT_IMAGE", "alpine:latest"),
		AllowHTTPJobArg:         getEnvAsBool("ALLOW_HTTP_JOB_ARG", true),
	}
}

func loadMinioConfig() MinioConfig {
	return MinioConfig{
		Endpoint:     getEnv("MINIO_ENDPOINT", "localhost:9000"),
		AccessKey:    getEnv("MINIO_ACCESS_KEY", ""),
		SecretKey:    getEnv("MINIO_SECRET_KEY", ""),
		UseSSL:       getEnvAsBool("MINIO_USE_SSL", false),
		OutputBucket: getEnv("MINIO_OUTPUT_BUCKET", "transcoded-videos"),
		Alias:        getEnv("DEFAULT_MINIO_ALIAS", "transcoder"),
	}
}

func loadTranscodeConfig() (TranscodeConfig, error) {
	resolutionsStr := getEnv("RESOLUTIONS", "240,360,480,720,1080")
	resolutions := strings.Split(resolutionsStr, ",")

	crfMap, err := parseCRFMap(getEnv("CRF_MAP", "240:36,360:34,480:32,720:30,1080:28"))
	if err != nil {
		return TranscodeConfig{}, fmt.Errorf("failed to parse CRF_MAP: %w", err)
	}

	masterPlaylist, err := parseMasterPlaylistMap(getEnv("MASTER_PLAYLIST", "240:500000,360:800000,480:1200000,720:2000000,1080:5000000"))
	if err != nil {
		return TranscodeConfig{}, fmt.Errorf("failed to parse MASTER_PLAYLIST: %w", err)
	}

	return TranscodeConfig{
		Image:          getEnv("TRANSCODE_IMAGE", "transcode:latest"),
		Preset:         getEnv("TRANSCODE_PRESET", "ultrafast"),
		Resolutions:    resolutions,
		CRFMap:         crfMap,
		MasterPlaylist: masterPlaylist,
	}, nil
}

func loadAppConfig() AppConfig {
	return AppConfig{
		MaxConcurrentHandlers: getEnvAsInt("MAX_CONCURRENT_HANDLERS", 10),
		RetryInterval:         getEnvAsDuration("RETRY_INTERVAL", 10*time.Second),
	}
}

func loadHealthConfig() HealthConfig {
	return HealthConfig{
		Port: getEnvAsInt("HEALTH_PORT", 8080),
	}
}

func getEnv(key, fallback string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return fallback
}

func getEnvAsInt(key string, fallback int) int {
	valueStr := getEnv(key, "")
	if value, err := strconv.Atoi(valueStr); err == nil {
		return value
	}
	return fallback
}

func getEnvAsBool(key string, fallback bool) bool {
	valueStr := getEnv(key, "")
	if value, err := strconv.ParseBool(valueStr); err == nil {
		return value
	}
	return fallback
}

func getEnvAsDuration(key string, fallback time.Duration) time.Duration {
	valueStr := getEnv(key, "")
	if value, err := time.ParseDuration(valueStr); err == nil {
		return value
	}
	return fallback
}

func parseCRFMap(crfStr string) (CRFMapping, error) {
	crfMap := make(CRFMapping)
	pairs := strings.Split(crfStr, ",")
	for _, pair := range pairs {
		parts := strings.Split(strings.TrimSpace(pair), ":")
		if len(parts) != 2 {
			return nil, fmt.Errorf("invalid CRF pair format: '%s'", pair)
		}
		res := strings.TrimSpace(parts[0])
		crfVal, err := strconv.Atoi(strings.TrimSpace(parts[1]))
		if err != nil {
			return nil, fmt.Errorf("invalid CRF value for resolution %s: '%s'", res, parts[1])
		}
		crfMap[res] = crfVal
	}
	return crfMap, nil
}

func parseMasterPlaylistMap(playlistStr string) (MasterPlaylistMap, error) {
	playlistMap := make(MasterPlaylistMap)
	pairs := strings.Split(playlistStr, ",")
	for _, pair := range pairs {
		parts := strings.Split(strings.TrimSpace(pair), ":")
		if len(parts) != 2 {
			return nil, fmt.Errorf("invalid master playlist pair format: '%s'", pair)
		}
		res := strings.TrimSpace(parts[0])
		bitrate, err := strconv.Atoi(strings.TrimSpace(parts[1]))
		if err != nil {
			return nil, fmt.Errorf("invalid bitrate value for resolution %s: '%s'", res, parts[1])
		}
		playlistMap[res] = bitrate
	}
	return playlistMap, nil
}

