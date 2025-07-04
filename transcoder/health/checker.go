package health

import (
	"context"
	"time"
)

type Status string

const (
	StatusHealthy   Status = "healthy"
	StatusUnhealthy Status = "unhealthy"
)

type Check struct {
	Name   string `json:"name"`
	Status Status `json:"status"`
	Error  string `json:"error,omitempty"`
}

type Response struct {
	Status Status  `json:"status"`
	Checks []Check `json:"checks"`
}

type Checker interface {
	CheckReadiness(ctx context.Context) Response
	CheckLiveness(ctx context.Context) Response
}

type DependencyChecker interface {
	CheckRedis(ctx context.Context) Check
	CheckRabbitMQ(ctx context.Context) Check
	CheckMinIO(ctx context.Context) Check
	CheckKubernetes(ctx context.Context) Check
}

type checker struct {
	deps DependencyChecker
}

func NewChecker(deps DependencyChecker) Checker {
	return &checker{deps: deps}
}

func (c *checker) CheckReadiness(ctx context.Context) Response {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	checks := []Check{
		c.deps.CheckRedis(ctx),
		c.deps.CheckRabbitMQ(ctx),
		c.deps.CheckMinIO(ctx),
		c.deps.CheckKubernetes(ctx),
	}

	overallStatus := StatusHealthy
	for _, check := range checks {
		if check.Status == StatusUnhealthy {
			overallStatus = StatusUnhealthy
			break
		}
	}

	return Response{
		Status: overallStatus,
		Checks: checks,
	}
}

func (c *checker) CheckLiveness(ctx context.Context) Response {
	ctx, cancel := context.WithTimeout(ctx, 2*time.Second)
	defer cancel()

	checks := []Check{
		c.deps.CheckRedis(ctx),
		c.deps.CheckRabbitMQ(ctx),
	}

	overallStatus := StatusHealthy
	for _, check := range checks {
		if check.Status == StatusUnhealthy {
			overallStatus = StatusUnhealthy
			break
		}
	}

	return Response{
		Status: overallStatus,
		Checks: checks,
	}
}