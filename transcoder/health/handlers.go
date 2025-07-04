package health

import (
	"encoding/json"
	"fmt"
	"net/http"
)

type Handler struct {
	checker Checker
}

func NewHandler(checker Checker) *Handler {
	return &Handler{checker: checker}
}

func (h *Handler) LivenessHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	response := h.checker.CheckLiveness(r.Context())
	h.writeResponse(w, response)
}

func (h *Handler) ReadinessHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	response := h.checker.CheckReadiness(r.Context())
	h.writeResponse(w, response)
}

func (h *Handler) writeResponse(w http.ResponseWriter, response Response) {
	w.Header().Set("Content-Type", "application/json")
	
	statusCode := http.StatusOK
	if response.Status == StatusUnhealthy {
		statusCode = http.StatusServiceUnavailable
	}
	w.WriteHeader(statusCode)

	if err := json.NewEncoder(w).Encode(response); err != nil {
		http.Error(w, fmt.Sprintf("JSON encoding error: %v", err), http.StatusInternalServerError)
	}
}