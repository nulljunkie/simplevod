package health

import (
	"context"
	"fmt"
	"log"
	"transcoder/kubernetes"
	"transcoder/minio"
	"transcoder/redis"

	amqp "github.com/rabbitmq/amqp091-go"
)

type dependencies struct {
	redisClient      redis.RedisClient
	rabbitMQURL      string
	minioClient      *minio.Client
	kubernetesClient *kubernetes.Client
}

func NewDependencies(redisClient redis.RedisClient, rabbitMQURL string, minioClient *minio.Client, kubernetesClient *kubernetes.Client) DependencyChecker {
	return &dependencies{
		redisClient:      redisClient,
		rabbitMQURL:      rabbitMQURL,
		minioClient:      minioClient,
		kubernetesClient: kubernetesClient,
	}
}

func (d *dependencies) CheckRedis(ctx context.Context) Check {
	if d.redisClient == nil {
		return Check{
			Name:   "redis",
			Status: StatusUnhealthy,
			Error:  "redis client not initialized",
		}
	}

	err := d.redisClient.HealthCheck(ctx)
	if err != nil {
		return Check{
			Name:   "redis",
			Status: StatusUnhealthy,
			Error:  fmt.Sprintf("redis health check failed: %v", err),
		}
	}

	return Check{
		Name:   "redis",
		Status: StatusHealthy,
	}
}

func (d *dependencies) CheckRabbitMQ(ctx context.Context) Check {
	if d.rabbitMQURL == "" {
		return Check{
			Name:   "rabbitmq",
			Status: StatusUnhealthy,
			Error:  "rabbitmq url not configured",
		}
	}

	done := make(chan error, 1)
	go func() {
		conn, err := amqp.Dial(d.rabbitMQURL)
		if err != nil {
			done <- err
			return
		}
		defer func() {
			if closeErr := conn.Close(); closeErr != nil {
				log.Printf("Failed to close RabbitMQ connection: %v", closeErr)
			}
		}()
		done <- nil
	}()

	select {
	case <-ctx.Done():
		return Check{
			Name:   "rabbitmq",
			Status: StatusUnhealthy,
			Error:  "rabbitmq check timeout",
		}
	case err := <-done:
		if err != nil {
			return Check{
				Name:   "rabbitmq",
				Status: StatusUnhealthy,
				Error:  fmt.Sprintf("rabbitmq connection failed: %v", err),
			}
		}
		return Check{
			Name:   "rabbitmq",
			Status: StatusHealthy,
		}
	}
}

func (d *dependencies) CheckMinIO(ctx context.Context) Check {
	if d.minioClient == nil {
		return Check{
			Name:   "minio",
			Status: StatusHealthy,
			Error:  "minio client not configured (optional)",
		}
	}

	if err := d.minioClient.HealthCheck(ctx); err != nil {
		return Check{
			Name:   "minio",
			Status: StatusUnhealthy,
			Error:  fmt.Sprintf("minio health check failed: %v", err),
		}
	}

	return Check{
		Name:   "minio",
		Status: StatusHealthy,
	}
}

func (d *dependencies) CheckKubernetes(ctx context.Context) Check {
	if d.kubernetesClient == nil {
		return Check{
			Name:   "kubernetes",
			Status: StatusUnhealthy,
			Error:  "kubernetes client not initialized",
		}
	}

	if !d.kubernetesClient.IsHealthy(ctx) {
		return Check{
			Name:   "kubernetes",
			Status: StatusUnhealthy,
			Error:  "kubernetes client health check failed",
		}
	}

	return Check{
		Name:   "kubernetes",
		Status: StatusHealthy,
	}
}