FROM golang:1.21-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./

RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o transcoder main.go

FROM alpine:latest

WORKDIR /app

COPY --from=builder /app/transcoder .

EXPOSE 8080

CMD ["./transcoder"]
