package rabbitmq

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"
	"transcoder/config"

	amqp "github.com/rabbitmq/amqp091-go"
)

type MessageProcessor interface {
	Process(ctx context.Context, body []byte) error
}

type Consumer struct {
	configuration    *config.RabbitMQConfig
	messageProcessor MessageProcessor
	workGroup        *sync.WaitGroup
	context          context.Context
	connection       *amqp.Connection
	channel          *amqp.Channel
}

func StartConsumer(configuration *config.RabbitMQConfig, processor MessageProcessor, workGroup *sync.WaitGroup, ctx context.Context) {
	defer workGroup.Done()

	consumer := &Consumer{
		configuration:    configuration,
		messageProcessor: processor,
		workGroup:        workGroup,
		context:          ctx,
	}

	consumer.run()
}

func (c *Consumer) run() {
	log.Println("Starting RabbitMQ consumer")

	for {
		if c.shouldShutdown() {
			c.shutdown()
			return
		}

		if err := c.establishConnection(); err != nil {
			c.handleConnectionError(err)
			continue
		}

		if err := c.setupChannel(); err != nil {
			c.handleChannelError(err)
			continue
		}

		if err := c.configureQualityOfService(); err != nil {
			c.handleQoSError(err)
			continue
		}

		messages, err := c.startConsuming()
		if err != nil {
			c.handleConsumerError(err)
			continue
		}

		c.processMessages(messages)
		c.cleanupConnection()
		c.waitBeforeReconnect()
	}
}

func (c *Consumer) shouldShutdown() bool {
	select {
	case <-c.context.Done():
		return true
	default:
		return false
	}
}

func (c *Consumer) shutdown() {
	log.Println("RabbitMQ consumer shutting down")
	c.cleanupConnection()
}

func (c *Consumer) establishConnection() error {
	connectionString := c.buildConnectionString()
	connection, err := amqp.Dial(connectionString)
	if err != nil {
		return fmt.Errorf("RabbitMQ connection failed: %w", err)
	}

	c.connection = connection
	log.Println("RabbitMQ connection established")
	return nil
}

func (c *Consumer) buildConnectionString() string {
	return fmt.Sprintf("amqp://%s:%s@%s:%d/%s",
		c.configuration.User,
		c.configuration.Pass,
		c.configuration.Host,
		c.configuration.Port,
		c.configuration.Vhost)
}

func (c *Consumer) setupChannel() error {
	channel, err := c.connection.Channel()
	if err != nil {
		return fmt.Errorf("channel creation failed: %w", err)
	}

	c.channel = channel
	log.Println("RabbitMQ channel created")
	return nil
}

func (c *Consumer) configureQualityOfService() error {
	if err := c.channel.Qos(c.configuration.Prefetch, 0, false); err != nil {
		return fmt.Errorf("QoS configuration failed: %w", err)
	}

	log.Printf("Channel QoS prefetch set to %d", c.configuration.Prefetch)
	return nil
}

func (c *Consumer) startConsuming() (<-chan amqp.Delivery, error) {
	messages, err := c.channel.Consume(
		c.configuration.ConsumeQueue,
		"",
		false,
		false,
		false,
		false,
		nil,
	)

	if err != nil {
		return nil, fmt.Errorf("consumer registration failed: %w", err)
	}

	log.Printf("Consuming messages from queue: %s", c.configuration.ConsumeQueue)
	return messages, nil
}

func (c *Consumer) processMessages(messages <-chan amqp.Delivery) {
	connectionErrors := make(chan *amqp.Error, 1)
	c.connection.NotifyClose(connectionErrors)

	for {
		select {
		case <-c.context.Done():
			log.Println("Message processing stopped - context cancelled")
			return
		case err := <-connectionErrors:
			log.Printf("Connection lost during message processing: %v", err)
			return
		case delivery, channelOpen := <-messages:
			if !channelOpen {
				log.Println("Message channel closed")
				return
			}
			c.handleMessage(delivery)
		}
	}
}

func (c *Consumer) handleMessage(delivery amqp.Delivery) {
	log.Printf("Processing message with delivery tag: %d", delivery.DeliveryTag)

	c.workGroup.Add(1)
	go func(msg amqp.Delivery) {
		defer c.workGroup.Done()

		if err := c.messageProcessor.Process(c.context, msg.Body); err != nil {
			c.handleProcessingError(msg, err)
		} else {
			c.acknowledgeMessage(msg)
		}
	}(delivery)
}

func (c *Consumer) handleProcessingError(delivery amqp.Delivery, err error) {
	log.Printf("Message processing failed (tag %d): %v - requeuing", delivery.DeliveryTag, err)

	if nackErr := delivery.Nack(false, true); nackErr != nil {
		log.Printf("NACK failed for tag %d: %v", delivery.DeliveryTag, nackErr)
	}
}

func (c *Consumer) acknowledgeMessage(delivery amqp.Delivery) {
	log.Printf("Message processed successfully (tag %d)", delivery.DeliveryTag)

	if ackErr := delivery.Ack(false); ackErr != nil {
		log.Printf("ACK failed for tag %d: %v", delivery.DeliveryTag, ackErr)
	}
}

func (c *Consumer) handleConnectionError(err error) {
	log.Printf("Connection establishment failed: %v - retrying in 10s", err)
	time.Sleep(10 * time.Second)
}

func (c *Consumer) handleChannelError(err error) {
	log.Printf("Channel setup failed: %v - retrying in 10s", err)
	c.closeConnection()
	time.Sleep(10 * time.Second)
}

func (c *Consumer) handleQoSError(err error) {
	log.Printf("QoS configuration failed: %v - retrying in 10s", err)
	c.cleanupConnection()
	time.Sleep(10 * time.Second)
}

func (c *Consumer) handleConsumerError(err error) {
	log.Printf("Consumer setup failed: %v - retrying in 10s", err)
	c.cleanupConnection()
	time.Sleep(10 * time.Second)
}

func (c *Consumer) cleanupConnection() {
	c.closeChannel()
	c.closeConnection()
}

func (c *Consumer) closeChannel() {
	if c.channel != nil && !c.channel.IsClosed() {
		c.channel.Close()
		c.channel = nil
	}
}

func (c *Consumer) closeConnection() {
	if c.connection != nil && !c.connection.IsClosed() {
		c.connection.Close()
		c.connection = nil
	}
}

func (c *Consumer) waitBeforeReconnect() {
	log.Println("Waiting before reconnection attempt")
	time.Sleep(10 * time.Second)
}

