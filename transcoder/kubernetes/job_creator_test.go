package kubernetes

import (
	"testing"
	"transcoder/models"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	corev1 "k8s.io/api/core/v1"
)

func TestClient_GenerateResourceNames(t *testing.T) {
	client := &Client{}

	jobConfig := models.JobConfig{
		VideoID:    "test-video-123",
		SegmentID:  5,
		Resolution: "720p",
	}

	configMapName := client.generateConfigMapName(jobConfig)
	jobName := client.generateJobName(jobConfig)

	assert.Equal(t, "ts-test-video-123-5-720p", configMapName)
	assert.Equal(t, "transcode-test-video-123-5-720p", jobName)
}

func TestClient_GenerateJobName_LongVideoID(t *testing.T) {
	client := &Client{}

	jobConfig := models.JobConfig{
		VideoID:    "this-is-a-very-long-video-id-that-exceeds-thirty-characters",
		SegmentID:  1,
		Resolution: "1080p",
	}

	jobName := client.generateJobName(jobConfig)

	assert.Contains(t, jobName, "transcode-")
	assert.Contains(t, jobName, "-1-1080p")
	assert.LessOrEqual(t, len(jobName), 63)
}

func TestClient_CreateResourceLabels(t *testing.T) {
	client := &Client{}

	jobConfig := models.JobConfig{
		VideoID:    "test-video",
		SegmentID:  3,
		Resolution: "480p",
	}

	labels := client.createResourceLabels(jobConfig)

	assert.Equal(t, "transcoder", labels["app"])
	assert.Equal(t, "test-video", labels["video-id"])
	assert.Equal(t, "3", labels["segment-id"])
	assert.Equal(t, "480p", labels["resolution"])
}

func TestClient_BuildTranscodeArgs(t *testing.T) {
	client := &Client{}

	jobConfig := models.JobConfig{
		SegmentID:  7,
		VideoURL:   "https://example.com/video.mp4",
		CRF:        28,
		Preset:     "fast",
		Resolution: "1080p",
		VideoID:    "test-video",
		AllowHTTP:  true,
	}

	timestampFile := "/data/timestamps.txt"
	args := client.buildTranscodeArgs(jobConfig, timestampFile)

	expectedArgs := []string{
		"--job-id=7",
		"--video-path=https://example.com/video.mp4",
		"--timestamp-file=/data/timestamps.txt",
		"--crf=28",
		"--preset=fast",
		"--resolution=1080p",
		"--video-id=test-video",
		"--allow-http",
	}

	assert.Equal(t, expectedArgs, args)
}

func TestClient_BuildTranscodeArgs_NoHTTP(t *testing.T) {
	client := &Client{}

	jobConfig := models.JobConfig{
		SegmentID:  1,
		VideoURL:   "https://example.com/video.mp4",
		CRF:        32,
		Preset:     "ultrafast",
		Resolution: "240p",
		VideoID:    "test-video",
		AllowHTTP:  false,
	}

	timestampFile := "/data/timestamps.txt"
	args := client.buildTranscodeArgs(jobConfig, timestampFile)

	assert.NotContains(t, args, "--allow-http")
	assert.Len(t, args, 7)
}

func TestClient_FilterEmptyRedisPassword(t *testing.T) {
	client := &Client{}

	envVars := []corev1.EnvVar{
		{Name: "REDIS_HOST", Value: "localhost"},
		{Name: "REDIS_PASSWORD", Value: "secret"},
		{Name: "REDIS_DB", Value: "0"},
	}

	filtered := client.filterEmptyRedisPassword(envVars, "")

	assert.Len(t, filtered, 2)
	assert.Equal(t, "REDIS_HOST", filtered[0].Name)
	assert.Equal(t, "REDIS_DB", filtered[1].Name)
}

func TestClient_FilterEmptyRedisPassword_WithPassword(t *testing.T) {
	client := &Client{}

	envVars := []corev1.EnvVar{
		{Name: "REDIS_HOST", Value: "localhost"},
		{Name: "REDIS_PASSWORD", Value: "secret"},
		{Name: "REDIS_DB", Value: "0"},
	}

	filtered := client.filterEmptyRedisPassword(envVars, "secret")

	assert.Len(t, filtered, 3)
	assert.Equal(t, envVars, filtered)
}

func TestClient_CreateVolumes(t *testing.T) {
	client := &Client{}

	configMapName := "test-configmap"
	jobConfig := models.JobConfig{
		MinioSecretName:         "minio-secret",
		RabbitMQAdminSecretName: "rabbitmq-secret",
	}

	volumes := client.createVolumes(configMapName, jobConfig)

	require.Len(t, volumes, 4)

	assert.Equal(t, "timestamp-volume", volumes[0].Name)
	assert.Equal(t, "minio-config-volume", volumes[1].Name)
	assert.Equal(t, "rabbitmq-admin-config-volume", volumes[2].Name)
	assert.Equal(t, "mc-config-writable", volumes[3].Name)

	assert.NotNil(t, volumes[0].ConfigMap)
	assert.Equal(t, configMapName, volumes[0].ConfigMap.Name)

	assert.NotNil(t, volumes[1].Secret)
	assert.Equal(t, "minio-secret", volumes[1].Secret.SecretName)

	assert.NotNil(t, volumes[2].Secret)
	assert.Equal(t, "rabbitmq-secret", volumes[2].Secret.SecretName)

	assert.NotNil(t, volumes[3].EmptyDir)
}

func TestClient_BuildVolumeMounts(t *testing.T) {
	client := &Client{}

	paths := mountPaths{
		timestamp:           "/data/timestamps",
		minioConfig:         "/mc-config",
		rabbitmqAdminConfig: "/rabbitmq-config",
	}

	mounts := client.buildVolumeMounts(paths)

	require.Len(t, mounts, 3)

	assert.Equal(t, "timestamp-volume", mounts[0].Name)
	assert.Equal(t, "/data/timestamps", mounts[0].MountPath)
	assert.True(t, mounts[0].ReadOnly)

	assert.Equal(t, "mc-config-writable", mounts[1].Name)
	assert.Equal(t, "/mc-config", mounts[1].MountPath)
	assert.False(t, mounts[1].ReadOnly)

	assert.Equal(t, "rabbitmq-admin-config-volume", mounts[2].Name)
	assert.Equal(t, "/rabbitmq-config", mounts[2].MountPath)
	assert.True(t, mounts[2].ReadOnly)
}

func TestClient_BuildEnvironmentVariables(t *testing.T) {
	client := &Client{}

	jobConfig := models.JobConfig{
		OutputBucket:          "test-bucket",
		RedisHost:             "redis-host",
		RedisPort:             6379,
		RedisPassword:         "redis-secret",
		RedisDB:               1,
		TotalJobsKey:          "total-key",
		CompletedJobsKey:      "completed-key",
		MasterPlaylistMetaKey: "playlist-key",
		MinioAlias:            "minio-alias",
		RabbitMQExchange:      "video-exchange",
		RabbitMQRoutingKey:    "video.transcode",
	}

	paths := mountPaths{
		minioConfig:         "/mc-config",
		rabbitmqAdminConfig: "/rabbitmq-config",
	}

	envVars := client.buildEnvironmentVariables(jobConfig, paths)

	expectedVars := map[string]string{
		"BUCKET_NAME":                "test-bucket",
		"REDIS_HOST":                 "redis-host",
		"REDIS_PORT":                 "6379",
		"REDISCLI_AUTH":              "redis-secret",
		"REDIS_DB":                   "1",
		"REDIS_TOTAL_JOBS_KEY":       "total-key",
		"REDIS_COMPLETED_JOBS_KEY":   "completed-key",
		"REDIS_MASTER_PLAYLIST_META": "playlist-key",
		"MC_CONFIG_DIR":              "/mc-config",
		"MINIO_ALIAS":                "minio-alias",
		"RABBITMQ_EXCHANGE":          "video-exchange",
		"RABBITMQ_ROUTING_KEY":       "video.transcode",
		"RABBITMQADMIN_CONFIG":       "/rabbitmq-config/rabbitmqadmin.conf",
	}

	assert.Len(t, envVars, len(expectedVars))

	for _, envVar := range envVars {
		expectedValue, exists := expectedVars[envVar.Name]
		assert.True(t, exists, "Unexpected environment variable: %s", envVar.Name)
		assert.Equal(t, expectedValue, envVar.Value, "Wrong value for %s", envVar.Name)
	}
}

func TestDetermineKubeconfigPath_WithEnvVar(t *testing.T) {
	t.Setenv("KUBECONFIG", "/custom/kubeconfig")

	path := determineKubeconfigPath()

	assert.Equal(t, "/custom/kubeconfig", path)
}

func TestPointer(t *testing.T) {
	value := int32(5)
	ptr := Pointer(value)

	assert.NotNil(t, ptr)
	assert.Equal(t, value, *ptr)

	stringValue := "test"
	stringPtr := Pointer(stringValue)

	assert.NotNil(t, stringPtr)
	assert.Equal(t, stringValue, *stringPtr)
}

func TestClient_SubmitJob_InvalidJobConfig(t *testing.T) {
	// This test requires a valid Kubernetes client which is not available in unit tests
	t.Skip("Skipping test that requires Kubernetes client")
}

