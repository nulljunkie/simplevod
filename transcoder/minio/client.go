package minio

import (
	"context"
	"fmt"
	"log"
	"transcoder/config"

	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"
)

type Client struct {
	minioClient *minio.Client
}

func NewClient(cfg *config.MinioConfig) (*Client, error) {
	minioClient, err := minio.New(cfg.Endpoint, &minio.Options{
		Creds:  credentials.NewStaticV4(cfg.AccessKey, cfg.SecretKey, ""),
		Secure: cfg.UseSSL,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create Minio client: %w", err)
	}

	log.Printf("Successfully initialized Minio client for endpoint: %s", cfg.Endpoint)
	return &Client{minioClient: minioClient}, nil
}

func (c *Client) EnsureBucketExists(ctx context.Context, bucketName string) error {
	_, err := c.minioClient.BucketExists(ctx, bucketName)
	if err != nil {
		return fmt.Errorf("failed to check if Minio bucket '%s' exists: %w", bucketName, err)
	}
	return nil
}

