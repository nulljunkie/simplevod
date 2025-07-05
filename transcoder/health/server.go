package health

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"time"
)

type Server struct {
	server  *http.Server
	handler *Handler
}

// responseWriter wraps http.ResponseWriter to capture status code
type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

func HealthLoggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		debugEnabled := strings.ToLower(os.Getenv("LOG_DEBUG")) == "true"

		if !debugEnabled && strings.HasPrefix(r.URL.Path, "/health") {
			next.ServeHTTP(w, r)
			return
		}

		start := time.Now()

		rw := &responseWriter{ResponseWriter: w, statusCode: 200}
		next.ServeHTTP(rw, r)

		duration := time.Since(start)
		log.Printf("%s %s %d %v", r.Method, r.URL.Path, rw.statusCode, duration)
	})
}

func NewServer(port int, handler *Handler) *Server {
	mux := http.NewServeMux()
	mux.HandleFunc("/health/liveness", handler.LivenessHandler)
	mux.HandleFunc("/health/readiness", handler.ReadinessHandler)

	server := &http.Server{
		Addr:         fmt.Sprintf(":%d", port),
		Handler:      HealthLoggingMiddleware(mux),
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  30 * time.Second,
	}

	return &Server{
		server:  server,
		handler: handler,
	}
}

func (s *Server) Start() error {
	log.Printf("Starting health check server on %s", s.server.Addr)
	if err := s.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		return fmt.Errorf("health server failed to start: %w", err)
	}
	return nil
}

func (s *Server) Stop(ctx context.Context) error {
	log.Println("Stopping health check server")
	return s.server.Shutdown(ctx)
}
