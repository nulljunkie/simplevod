#!/bin/bash

BUCKET_NAME=stream
MC_CONFIG_DIR=mc
RABBITMQADMIN_CONFIG=rabbitmqadmin.conf
REDIS_HOST=localhost
REDIS_PORT=6379
REDISCLI_AUTH=password
REDIS_DB=0
VIDEO_PATH=video.mp4
PRESET=ultrafast

RABBITMQ_EXCHANGE=video
RABBITMQ_ROUTING_KEY=video.playlist


VIDEO_ID=wendigo

REDIS_TOTAL_JOBS_KEY="transcode:jobs:${VIDEO_ID}:total"
REDIS_COMPLETED_JOBS_KEY="transcode:jobs:${VIDEO_ID}:completed"
REDIS_MASTER_PLAYLIST_META="transcode:playlists:${VIDEO_ID}:meta"

REDIS_CMD="redis-cli -h $REDIS_HOST -p $REDIS_PORT -n $REDIS_DB -a $REDISCLI_AUTH"

$REDIS_CMD SET $REDIS_TOTAL_JOBS_KEY 3
$REDIS_CMD HSET $REDIS_COMPLETED_JOBS_KEY 240 0 720 0
$REDIS_CMD HSET $REDIS_MASTER_PLAYLIST_META 240 500000 720 2000000


TIMESTAMP_FILES=(timestamps1 timestamps2 timestamps3)
RESOLUTIONS=(240 720)
CRFS=(28 18)

resolutions_length=${#RESOLUTIONS[@]}
total_jobs=${#TIMESTAMP_FILES[@]}

for ((i = 0; i < $total_jobs; i++)); do
    job_id=$(($i + 1))
    timestamps=${TIMESTAMP_FILES[$i]}
    for ((j = 0; j < $resolutions_length; j++)); do
        res=${RESOLUTIONS[$j]}
        crf=${CRFS[$j]}
        echo ""
        echo "#################################################################"
        echo "job_id:$job_id timestamps:$timestamps res:$res crf:$crf"
        echo "#################################################################"
        echo ""

        BUCKET_NAME=${BUCKET_NAME} MC_CONFIG_DIR=${MC_CONFIG_DIR} RABBITMQ_EXCHANGE=${RABBITMQ_EXCHANGE} RABBITMQ_ROUTING_KEY=${RABBITMQ_ROUTING_KEY} RABBITMQADMIN_CONFIG=${RABBITMQADMIN_CONFIG} REDISCLI_AUTH=${REDISCLI_AUTH} ./transcode.sh --job-id=$job_id --video-path=${VIDEO_PATH} --timestamp-file=$timestamps --crf=$crf --preset=${PRESET} --resolution=$res --video-id=${VIDEO_ID}
    done
done
