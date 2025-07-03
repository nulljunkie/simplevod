package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"transcoder/config"
	"transcoder/handlers"
	"transcoder/kubernetes"
	"transcoder/minio"
	"transcoder/rabbitmq"
	"transcoder/redis"
)

type TranscoderApp struct {
	configuration    *config.Config
	kubernetesClient *kubernetes.Client
	redisClient      redis.RedisClient
	minioClient      *minio.Client
}

func NewTranscoderApp() (*TranscoderApp, error) {
	cfg, err := loadConfiguration()
	if err != nil {
		return nil, err
	}

	k8sClient, err := createKubernetesClient()
	if err != nil {
		return nil, err
	}

	redisClient, err := createRedisClient(cfg)
	if err != nil {
		return nil, err
	}

	minioClient := createMinioClientSafely(cfg)

	return &TranscoderApp{
		configuration:    cfg,
		kubernetesClient: k8sClient,
		redisClient:      redisClient,
		minioClient:      minioClient,
	}, nil
}

func (app *TranscoderApp) Start() {
	ctx, cancel := createCancellableContext()
	defer cancel()

	shutdownSignals := setupSignalHandler()
	workGroup := &sync.WaitGroup{}

	messageHandler := app.createMessageHandler()
	app.startRabbitMQConsumer(messageHandler, workGroup, ctx)

	app.waitForShutdownSignal(shutdownSignals)
	app.initiateGracefulShutdown(cancel, workGroup)
}

func (app *TranscoderApp) createMessageHandler() *handlers.MessageHandler {
	return handlers.NewMessageHandler(app.configuration, app.kubernetesClient, app.redisClient)
}

func (app *TranscoderApp) startRabbitMQConsumer(handler *handlers.MessageHandler, wg *sync.WaitGroup, ctx context.Context) {
	wg.Add(1)
	go rabbitmq.StartConsumer(&app.configuration.RabbitMQ, handler, wg, ctx)
	log.Println("RabbitMQ consumer started successfully")
}

func (app *TranscoderApp) waitForShutdownSignal(signals chan os.Signal) {
	log.Println("Transcoder service running - waiting for shutdown signal")
	sig := <-signals
	log.Printf("Received shutdown signal: %s", sig)
}

func (app *TranscoderApp) initiateGracefulShutdown(cancel context.CancelFunc, wg *sync.WaitGroup) {
	log.Println("Initiating graceful shutdown")
	cancel()
	log.Println("Waiting for active processes to complete")
	wg.Wait()
	log.Println("Transcoder service shutdown complete")
}

func loadConfiguration() (*config.Config, error) {
	return config.Load()
}

func createKubernetesClient() (*kubernetes.Client, error) {
	return kubernetes.NewClient()
}

func createRedisClient(cfg *config.Config) (redis.RedisClient, error) {
	return redis.NewClient(&cfg.Redis)
}

func createMinioClientSafely(cfg *config.Config) *minio.Client {
	minioClient, err := minio.NewClient(&cfg.Minio)
	if err != nil {
		log.Printf("Warning: MinIO client initialization failed: %v", err)
		return nil
	}
	return minioClient
}

func createCancellableContext() (context.Context, context.CancelFunc) {
	return context.WithCancel(context.Background())
}

func setupSignalHandler() chan os.Signal {
	signals := make(chan os.Signal, 1)
	signal.Notify(signals, syscall.SIGINT, syscall.SIGTERM)
	return signals
}

func main() {
	log.Println("Starting Transcoder service")

	app, err := NewTranscoderApp()
	if err != nil {
		log.Fatalf("Application initialization failed: %v", err)
	}

	app.Start()
}
