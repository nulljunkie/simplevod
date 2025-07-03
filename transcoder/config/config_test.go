package config

import (
	"os"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestLoadConfiguration_DefaultValues(t *testing.T) {
	config, err := Load()

	require.NoError(t, err)
	assert.NotNil(t, config)

	assert.Equal(t, "localhost", config.RabbitMQ.Host)
	assert.Equal(t, 5672, config.RabbitMQ.Port)
	assert.Equal(t, "localhost", config.Redis.Host)
	assert.Equal(t, 6379, config.Redis.Port)
	assert.Equal(t, "default", config.Kubernetes.Namespace)
}

func TestLoadRabbitMQConfig_WithEnvironmentVariables(t *testing.T) {
	os.Setenv("RABBITMQ_HOST", "test-host")
	os.Setenv("RABBITMQ_PORT", "5673")
	os.Setenv("RABBITMQ_USER", "test-user")
	defer func() {
		os.Unsetenv("RABBITMQ_HOST")
		os.Unsetenv("RABBITMQ_PORT")
		os.Unsetenv("RABBITMQ_USER")
	}()

	config := loadRabbitMQConfig()

	assert.Equal(t, "test-host", config.Host)
	assert.Equal(t, 5673, config.Port)
	assert.Equal(t, "test-user", config.User)
}

func TestLoadRedisConfig_WithEnvironmentVariables(t *testing.T) {
	os.Setenv("REDIS_HOST", "redis-host")
	os.Setenv("REDIS_PORT", "6380")
	os.Setenv("REDIS_PASSWORD", "secret")
	defer func() {
		os.Unsetenv("REDIS_HOST")
		os.Unsetenv("REDIS_PORT")
		os.Unsetenv("REDIS_PASSWORD")
	}()

	config := loadRedisConfig()

	assert.Equal(t, "redis-host", config.Host)
	assert.Equal(t, 6380, config.Port)
	assert.Equal(t, "secret", config.Password)
}

func TestParseCRFMap_ValidInput(t *testing.T) {
	crfMap, err := parseCRFMap("240:36,360:34,480:32")

	require.NoError(t, err)
	assert.Equal(t, 36, crfMap["240"])
	assert.Equal(t, 34, crfMap["360"])
	assert.Equal(t, 32, crfMap["480"])
}

func TestParseCRFMap_InvalidFormat(t *testing.T) {
	_, err := parseCRFMap("240-36,360:34")

	assert.Error(t, err)
	assert.Contains(t, err.Error(), "invalid CRF pair format")
}

func TestParseCRFMap_InvalidCRFValue(t *testing.T) {
	_, err := parseCRFMap("240:invalid,360:34")

	assert.Error(t, err)
	assert.Contains(t, err.Error(), "invalid CRF value")
}

func TestParseMasterPlaylistMap_ValidInput(t *testing.T) {
	playlistMap, err := parseMasterPlaylistMap("240:500000,360:800000")

	require.NoError(t, err)
	assert.Equal(t, 500000, playlistMap["240"])
	assert.Equal(t, 800000, playlistMap["360"])
}

func TestParseMasterPlaylistMap_InvalidFormat(t *testing.T) {
	_, err := parseMasterPlaylistMap("240-500000")

	assert.Error(t, err)
	assert.Contains(t, err.Error(), "invalid master playlist pair format")
}

func TestGetEnvAsInt_ValidValue(t *testing.T) {
	os.Setenv("TEST_INT", "42")
	defer os.Unsetenv("TEST_INT")

	value := getEnvAsInt("TEST_INT", 10)

	assert.Equal(t, 42, value)
}

func TestGetEnvAsInt_InvalidValue(t *testing.T) {
	os.Setenv("TEST_INT", "invalid")
	defer os.Unsetenv("TEST_INT")

	value := getEnvAsInt("TEST_INT", 10)

	assert.Equal(t, 10, value)
}

func TestGetEnvAsBool_ValidValues(t *testing.T) {
	testCases := []struct {
		envValue string
		expected bool
	}{
		{"true", true},
		{"false", false},
		{"1", true},
		{"0", false},
		{"True", true},
		{"False", false},
	}

	for _, tc := range testCases {
		os.Setenv("TEST_BOOL", tc.envValue)
		value := getEnvAsBool("TEST_BOOL", false)
		assert.Equal(t, tc.expected, value, "Failed for input: %s", tc.envValue)
		os.Unsetenv("TEST_BOOL")
	}
}

func TestGetEnvAsDuration_ValidValue(t *testing.T) {
	os.Setenv("TEST_DURATION", "30s")
	defer os.Unsetenv("TEST_DURATION")

	value := getEnvAsDuration("TEST_DURATION", 10*time.Second)

	assert.Equal(t, 30*time.Second, value)
}

func TestGetEnvAsDuration_InvalidValue(t *testing.T) {
	os.Setenv("TEST_DURATION", "invalid")
	defer os.Unsetenv("TEST_DURATION")

	value := getEnvAsDuration("TEST_DURATION", 10*time.Second)

	assert.Equal(t, 10*time.Second, value)
}

