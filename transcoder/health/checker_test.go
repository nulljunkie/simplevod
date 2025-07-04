package health

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

type MockDependencyChecker struct {
	mock.Mock
}

func (m *MockDependencyChecker) CheckRedis(ctx context.Context) Check {
	args := m.Called(ctx)
	return args.Get(0).(Check)
}

func (m *MockDependencyChecker) CheckRabbitMQ(ctx context.Context) Check {
	args := m.Called(ctx)
	return args.Get(0).(Check)
}

func (m *MockDependencyChecker) CheckMinIO(ctx context.Context) Check {
	args := m.Called(ctx)
	return args.Get(0).(Check)
}

func (m *MockDependencyChecker) CheckKubernetes(ctx context.Context) Check {
	args := m.Called(ctx)
	return args.Get(0).(Check)
}

func TestChecker_CheckLiveness_AllHealthy(t *testing.T) {
	mockDeps := new(MockDependencyChecker)
	
	mockDeps.On("CheckRedis", mock.Anything).Return(Check{Name: "redis", Status: StatusHealthy})
	mockDeps.On("CheckRabbitMQ", mock.Anything).Return(Check{Name: "rabbitmq", Status: StatusHealthy})
	
	checker := NewChecker(mockDeps)
	
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	
	response := checker.CheckLiveness(ctx)
	
	assert.Equal(t, StatusHealthy, response.Status)
	assert.Len(t, response.Checks, 2)
	mockDeps.AssertExpectations(t)
}

func TestChecker_CheckLiveness_OneUnhealthy(t *testing.T) {
	mockDeps := new(MockDependencyChecker)
	
	mockDeps.On("CheckRedis", mock.Anything).Return(Check{Name: "redis", Status: StatusUnhealthy, Error: "connection failed"})
	mockDeps.On("CheckRabbitMQ", mock.Anything).Return(Check{Name: "rabbitmq", Status: StatusHealthy})
	
	checker := NewChecker(mockDeps)
	
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	
	response := checker.CheckLiveness(ctx)
	
	assert.Equal(t, StatusUnhealthy, response.Status)
	assert.Len(t, response.Checks, 2)
	mockDeps.AssertExpectations(t)
}

func TestChecker_CheckReadiness_AllHealthy(t *testing.T) {
	mockDeps := new(MockDependencyChecker)
	
	mockDeps.On("CheckRedis", mock.Anything).Return(Check{Name: "redis", Status: StatusHealthy})
	mockDeps.On("CheckRabbitMQ", mock.Anything).Return(Check{Name: "rabbitmq", Status: StatusHealthy})
	mockDeps.On("CheckMinIO", mock.Anything).Return(Check{Name: "minio", Status: StatusHealthy})
	mockDeps.On("CheckKubernetes", mock.Anything).Return(Check{Name: "kubernetes", Status: StatusHealthy})
	
	checker := NewChecker(mockDeps)
	
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	
	response := checker.CheckReadiness(ctx)
	
	assert.Equal(t, StatusHealthy, response.Status)
	assert.Len(t, response.Checks, 4)
	mockDeps.AssertExpectations(t)
}

func TestChecker_CheckReadiness_OneUnhealthy(t *testing.T) {
	mockDeps := new(MockDependencyChecker)
	
	mockDeps.On("CheckRedis", mock.Anything).Return(Check{Name: "redis", Status: StatusHealthy})
	mockDeps.On("CheckRabbitMQ", mock.Anything).Return(Check{Name: "rabbitmq", Status: StatusHealthy})
	mockDeps.On("CheckMinIO", mock.Anything).Return(Check{Name: "minio", Status: StatusUnhealthy, Error: "not configured"})
	mockDeps.On("CheckKubernetes", mock.Anything).Return(Check{Name: "kubernetes", Status: StatusHealthy})
	
	checker := NewChecker(mockDeps)
	
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	
	response := checker.CheckReadiness(ctx)
	
	assert.Equal(t, StatusUnhealthy, response.Status)
	assert.Len(t, response.Checks, 4)
	mockDeps.AssertExpectations(t)
}