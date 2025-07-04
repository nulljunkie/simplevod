package health

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

type MockChecker struct {
	mock.Mock
}

func (m *MockChecker) CheckLiveness(ctx context.Context) Response {
	args := m.Called(ctx)
	return args.Get(0).(Response)
}

func (m *MockChecker) CheckReadiness(ctx context.Context) Response {
	args := m.Called(ctx)
	return args.Get(0).(Response)
}

func TestHandler_LivenessHandler_Healthy(t *testing.T) {
	mockChecker := new(MockChecker)
	handler := NewHandler(mockChecker)
	
	expectedResponse := Response{
		Status: StatusHealthy,
		Checks: []Check{{Name: "redis", Status: StatusHealthy}},
	}
	
	mockChecker.On("CheckLiveness", mock.Anything).Return(expectedResponse)
	
	req := httptest.NewRequest(http.MethodGet, "/health/liveness", nil)
	rr := httptest.NewRecorder()
	
	handler.LivenessHandler(rr, req)
	
	assert.Equal(t, http.StatusOK, rr.Code)
	assert.Equal(t, "application/json", rr.Header().Get("Content-Type"))
	
	var response Response
	err := json.Unmarshal(rr.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, expectedResponse, response)
	
	mockChecker.AssertExpectations(t)
}

func TestHandler_LivenessHandler_Unhealthy(t *testing.T) {
	mockChecker := new(MockChecker)
	handler := NewHandler(mockChecker)
	
	expectedResponse := Response{
		Status: StatusUnhealthy,
		Checks: []Check{{Name: "redis", Status: StatusUnhealthy, Error: "connection failed"}},
	}
	
	mockChecker.On("CheckLiveness", mock.Anything).Return(expectedResponse)
	
	req := httptest.NewRequest(http.MethodGet, "/health/liveness", nil)
	rr := httptest.NewRecorder()
	
	handler.LivenessHandler(rr, req)
	
	assert.Equal(t, http.StatusServiceUnavailable, rr.Code)
	assert.Equal(t, "application/json", rr.Header().Get("Content-Type"))
	
	var response Response
	err := json.Unmarshal(rr.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, expectedResponse, response)
	
	mockChecker.AssertExpectations(t)
}

func TestHandler_ReadinessHandler_Healthy(t *testing.T) {
	mockChecker := new(MockChecker)
	handler := NewHandler(mockChecker)
	
	expectedResponse := Response{
		Status: StatusHealthy,
		Checks: []Check{
			{Name: "redis", Status: StatusHealthy},
			{Name: "rabbitmq", Status: StatusHealthy},
		},
	}
	
	mockChecker.On("CheckReadiness", mock.Anything).Return(expectedResponse)
	
	req := httptest.NewRequest(http.MethodGet, "/health/readiness", nil)
	rr := httptest.NewRecorder()
	
	handler.ReadinessHandler(rr, req)
	
	assert.Equal(t, http.StatusOK, rr.Code)
	assert.Equal(t, "application/json", rr.Header().Get("Content-Type"))
	
	var response Response
	err := json.Unmarshal(rr.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, expectedResponse, response)
	
	mockChecker.AssertExpectations(t)
}

func TestHandler_MethodNotAllowed(t *testing.T) {
	mockChecker := new(MockChecker)
	handler := NewHandler(mockChecker)
	
	req := httptest.NewRequest(http.MethodPost, "/health/liveness", nil)
	rr := httptest.NewRecorder()
	
	handler.LivenessHandler(rr, req)
	
	assert.Equal(t, http.StatusMethodNotAllowed, rr.Code)
}