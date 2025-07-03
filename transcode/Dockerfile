FROM debian:bullseye-slim

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    jq \
    ffmpeg \
    redis-tools \
    bc \
    git \
    bash \
    ca-certificates \
    wget \
    python3 \
    python3-pip \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN curl -sLO https://dl.min.io/client/mc/release/linux-amd64/mc && \
    install mc /usr/local/bin/

WORKDIR /scripts

ENV TERM xterm-256color

COPY transcode.sh .

# WARN: This version is deprecated
COPY rabbitmqadmin.py /usr/local/bin/rabbitmqadmin
RUN chmod +x /usr/local/bin/rabbitmqadmin

ENTRYPOINT ["/bin/bash"]
