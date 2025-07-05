package rabbitmq

import (
	"encoding/json"
	"fmt"
	"log"
	"time"
	"transcoder/config"

	amqp "github.com/rabbitmq/amqp091-go"
)

type StatusEvent struct {
	VideoID   string            `json:"video_id"`
	Status    string            `json:"status"`
	Service   string            `json:"service"`
	Timestamp string            `json:"timestamp"`
	Metadata  map[string]interface{} `json:"metadata"`
	Error     *string           `json:"error,omitempty"`
}

type StatusPublisher struct {
	configuration *config.RabbitMQConfig
	connection    *amqp.Connection
	channel       *amqp.Channel
}

func NewStatusPublisher(cfg *config.RabbitMQConfig) *StatusPublisher {
	return &StatusPublisher{
		configuration: cfg,
	}
}

func (p *StatusPublisher) ensureConnection() error {
	if p.connection != nil && !p.connection.IsClosed() {
		return nil
	}

	connectionString := fmt.Sprintf("amqp://%s:%s@%s:%d/%s",
		p.configuration.User,
		p.configuration.Pass,
		p.configuration.Host,
		p.configuration.Port,
		p.configuration.Vhost)

	connection, err := amqp.Dial(connectionString)
	if err != nil {
		return fmt.Errorf("failed to connect to RabbitMQ: %w", err)
	}

	channel, err := connection.Channel()
	if err != nil {
		connection.Close()
		return fmt.Errorf("failed to open channel: %w", err)
	}

	p.connection = connection
	p.channel = channel
	return nil
}

func (p *StatusPublisher) PublishStatus(videoID, status string, metadata map[string]interface{}, errorMsg *string) error {
	if err := p.ensureConnection(); err != nil {
		return err
	}

	event := StatusEvent{
		VideoID:   videoID,
		Status:    status,
		Service:   "transcoder",
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		Metadata:  metadata,
		Error:     errorMsg,
	}

	body, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("failed to marshal status event: %w", err)
	}

	err = p.channel.Publish(
		"video",       // exchange
		"video.status", // routing key
		false,         // mandatory
		false,         // immediate
		amqp.Publishing{
			ContentType:  "application/json",
			Body:         body,
			DeliveryMode: amqp.Persistent,
		},
	)

	if err != nil {
		return fmt.Errorf("failed to publish status event: %w", err)
	}

	log.Printf("Published status event: video_id=%s, status=%s", videoID, status)
	return nil
}

func (p *StatusPublisher) Close() {
	if p.channel != nil && !p.channel.IsClosed() {
		p.channel.Close()
	}
	if p.connection != nil && !p.connection.IsClosed() {
		p.connection.Close()
	}
}