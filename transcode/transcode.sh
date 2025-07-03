#!/bin/bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

show_help() {
  echo -e "
${BOLD}Usage:${RESET} $0 [OPTIONS]

${BOLD}Required:${RESET}
  ${BOLD}--job-id${RESET}=N          Sequential job number (1, 2, 3...)
  ${BOLD}--video-id${RESET}=ID       Video identifier (alphanumeric)
  ${BOLD}--video-path${RESET}=PATH   Input video file
  ${BOLD}--timestamp-file${RESET}=PATH  File with keyframe timestamps

${BOLD}Optional:${RESET}
  ${BOLD}--crf${RESET}=CRF           Constant Rate Factor (0-51, default: 28)
  ${BOLD}--preset${RESET}=PRESET     x264 preset (default: medium)
  ${BOLD}--resolution${RESET}=HEIGHT Output height in pixels (default: 240)
  ${BOLD}--allow-http${RESET}        Allow HTTP URLs for input video (HTTPS is always allowed)
  ${BOLD}--help${RESET}              Show this message"
  exit 0
}

log_info() {
  echo -e "${CYAN}INFO:${RESET} $1" >&2
}

log_debug() {
  echo -e "${MAGENTA}DEBUG:${RESET} $1" >&2
}

log_error() {
  echo -e "${RED}ERROR:${RESET} $1" >&2
}

error_exit() {
  log_error "$1"
  exit 1
}

########################################################
#        Arguments and variables
########################################################

for arg in "$@"; do
  case "$arg" in
    --job-id=*)         JOB_ID="${arg#*=}" ;;
    --video-id=*)       VIDEO_ID="${arg#*=}" ;;
    --video-path=*)     INPUT_VIDEO="${arg#*=}" ;;
    --timestamp-file=*) TIMESTAMPS_FILE="${arg#*=}" ;;
    --crf=*)            VIDEO_CRF="${arg#*=}" ;;
    --preset=*)         VIDEO_PRESET="${arg#*=}" ;;
    --resolution=*)     VIDEO_HEIGHT="${arg#*=}" ;;
    --help)             show_help ;;
    --allow-http)       ALLOW_HTTP=true ;;
    *)                  error_exit "Unknown option: $arg" ;;
  esac
done

# --- Defaults ---
VIDEO_CRF="${VIDEO_CRF:-28}"
VIDEO_PRESET="${VIDEO_PRESET:-medium}"
VIDEO_HEIGHT="${VIDEO_HEIGHT:-240}"
ALLOW_HTTP="${ALLOW_HTTP:-false}"
OUTPUT_DIR="output"
SEGMENT_PREFIX="segment_"
SEGMENT_EXT="ts"
VIDEO_CODEC="libx264"
AUDIO_CODEC="aac"
AUDIO_BITRATE="64k"

MC_CONFIG_DIR="${MC_CONFIG_DIR:-/mc}"
MINIO_ALIAS="${MINIO_ALIAS:-transcoder}"
BUCKET_NAME="${BUCKET_NAME:-}"  # No default, must be set
MINIO_PATH="$MINIO_ALIAS/$BUCKET_NAME/$VIDEO_ID/$VIDEO_HEIGHT/$JOB_ID/"


REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDISCLI_AUTH="${REDISCLI_AUTH:-}"  # Redis password, used by redis-cli
REDIS_DB="${REDIS_DB:-0}"
REDIS_PLAYLIST_KEY="transcode:playlists:${VIDEO_ID}:data:${VIDEO_HEIGHT}"
REDIS_TOTAL_JOBS_KEY="transcode:jobs:${VIDEO_ID}:total"
REDIS_COMPLETED_JOBS_KEY="transcode:jobs:${VIDEO_ID}:completed"
REDIS_FIELD="${VIDEO_HEIGHT}"

REDIS_CMD="redis-cli -h $REDIS_HOST -p $REDIS_PORT -n $REDIS_DB"

# RABBITMQ_HOST="${RABBITMQ_HOST:-localhost}"
# RABBITMQ_PORT="${RABBITMQ_PORT:-5672}"
# RABBITMQ_USER="${RABBITMQ_USER:-guest}"
# RABBITMQ_PASSWORD="${RABBITMQ_PASSWORD:-guest}"
# RABBITMQ_VHOST="${RABBITMQ_VHOST:-/}"

RABBITMQADMIN_CONFIG="${RABBITMQADMIN_CONFIG:-'/rabbitmqadmin.conf'}"
RABBITMQ_EXCHANGE="${RABBITMQ_EXCHANGE:-''}"
RABBITMQ_ROUTING_KEY="${RABBITMQ_ROUTING_KEY:-''}"


readarray -t TIMESTAMPS < "$TIMESTAMPS_FILE"

TOTAL_DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$INPUT_VIDEO")
FORMATTED_DURATION=$(printf "%02d:%02d:%06.3f" \
                    $(echo "$TOTAL_DURATION" | \
                    awk '{ h=int($1/3600); m=int(($1%3600)/60); s=$1%60; printf "%d %d %f", h, m, s }'))


########################################################
#         Validations
########################################################


validate_number() {
  [[ "$1" =~ ^[0-9]+(\.[0-9]+)?$ ]] || error_exit "Invalid number: '$1'"
}

validate_crf() {
  [[ "$1" =~ ^[0-9]+$ ]] && [ "$1" -le 51 ] || 
    error_exit "CRF must be integer (0-51 for H.264)"
}

validate_preset() {
  local valid_presets=("ultrafast" "superfast" "veryfast" "faster" "fast" 
                      "medium" "slow" "slower" "veryslow")
  [[ " ${valid_presets[*]} " =~ " $1 " ]] || 
    error_exit "Invalid preset '$1'. Use: ${valid_presets[*]}"
}

validate_timestamps() {
  [ ${#TIMESTAMPS[@]} -ge 2 ] || error_exit "Need ≥2 timestamps for segmentation"
  for ts in "${TIMESTAMPS[@]}"; do
    validate_number "$ts"
  done
}

for cmd in ffmpeg ffprobe bc mc rabbitmqadmin redis-cli jq; do
  command -v "$cmd" >/dev/null 2>&1 || error_exit "'$cmd' required but not found"
done

[ -z "$JOB_ID" ] && error_exit "--job-id is required"
[ -z "$VIDEO_ID" ] && error_exit "--video-id is required"
[ -z "$INPUT_VIDEO" ] && error_exit "--video-path is required"
[ -z "$TIMESTAMPS_FILE" ] && error_exit "--timestamp-file is required"
[ -z "$BUCKET_NAME" ] && error_exit "Environment variable BUCKET_NAME is required"
[ -z "$REDISCLI_AUTH" ] && error_exit "Environment variable REDISCLI_AUTH is required"

[[ "$JOB_ID" =~ ^[1-9][0-9]*$ ]] || error_exit "Job ID must be a positive integer (1, 2, 3...)"
[[ "$VIDEO_ID" =~ ^[a-zA-Z0-9_-]+$ ]] || error_exit "Video ID must be alphanumeric with underscores or hyphens"
if [[ "$INPUT_VIDEO" =~ ^https:// ]]; then
  log_info "Input video is an HTTPS URL: $INPUT_VIDEO"
elif [[ "$INPUT_VIDEO" =~ ^http:// ]]; then
  if [[ "$ALLOW_HTTP" == "true" ]]; then
    log_info "Input video is an HTTP URL (allowed): $INPUT_VIDEO"
  else
    error_exit "HTTP URLs are not allowed by default. Use --allow-http to enable. Input: '$INPUT_VIDEO'"
  fi
elif [ ! -f "$INPUT_VIDEO" ]; then
  error_exit "Input video not found (and not a valid HTTPS/HTTP URL): '$INPUT_VIDEO'"
fi
[ -f "$TIMESTAMPS_FILE" ] || error_exit "Timestamps file not found: '$TIMESTAMPS_FILE'"
validate_crf "$VIDEO_CRF"
validate_preset "$VIDEO_PRESET"
[[ "$VIDEO_HEIGHT" =~ ^[0-9]+$ ]] || error_exit "Resolution must be a positive integer"
[[ -d "$MC_CONFIG_DIR" && -r "$MC_CONFIG_DIR" ]] || error_exit "MinIO config directory '$MC_CONFIG_DIR' does not exist or is not readable"
[[ -n "$MINIO_ALIAS" ]] || error_exit "MinIO alias cannot be empty"


validate_timestamps

validate_number "$TOTAL_DURATION"


##############################################
#        Processing Segments
##############################################

mkdir -p "$OUTPUT_DIR" || error_exit "Failed to create '$OUTPUT_DIR'"
rm -f "$OUTPUT_DIR"/*."$SEGMENT_EXT" "$OUTPUT_DIR"/playlist.m3u8

echo -e "${GREEN}${BOLD}HLS Transcoding Starting...${RESET}"
echo ""
log_debug "Processing Job ID:       $JOB_ID"
log_debug "Video ID:                $VIDEO_ID"
log_debug "Input Video:             $INPUT_VIDEO"
log_debug "Minio Output Path:       $MINIO_PATH"
log_debug "Minio MC Config Dir:     $MC_CONFIG_DIR"
log_debug "Redis Plyalist Key:      $REDIS_PLAYLIST_KEY"
log_debug "Timestamps:              $TIMESTAMPS_FILE ($(wc -l < "$TIMESTAMPS_FILE") keyframes)"
log_debug "Total Segments:          $((${#TIMESTAMPS[@]} - 1))"
log_debug "Processing:              From ${TIMESTAMPS[0]}s to ${TIMESTAMPS[-1]}s"
log_debug "Total Duration:          $FORMATTED_DURATION (HH:MM:SS.MMM)"
log_debug "Output Folder:           $OUTPUT_DIR"
log_debug "Resolution:              ${VIDEO_HEIGHT}p"
log_debug "Video Codec:             $VIDEO_CODEC"
log_debug "CRF:                     $VIDEO_CRF (Lower = Better Quality)"
log_debug "Preset:                  $VIDEO_PRESET"
log_debug "Audio:                   $AUDIO_CODEC @ $AUDIO_BITRATE"
echo ""
echo -e "${GREEN}${BOLD}Processing...${RESET}"
echo ""


SEGMENT_INFO=()
MAX_DURATION=0

# Total number of iterations
TOTAL=$(( ${#TIMESTAMPS[@]} - 1 ))

# Progress bar width
BAR_WIDTH=50

# Hide cursor for cleaner display
tput civis

for ((i=0; i<TOTAL; i++)); do
  START=${TIMESTAMPS[i]}
  END=${TIMESTAMPS[i+1]}
  validate_number "$START"
  validate_number "$END"

  DURATION=$(bc -l <<< "$END - $START")
  [ $(bc -l <<< "$DURATION <= 0") -eq 1 ] && continue

  SEGMENT_FILE="${SEGMENT_PREFIX}$(printf "%04d" $i).$SEGMENT_EXT"
  SEGMENT_PATH="$OUTPUT_DIR/$SEGMENT_FILE"

  # Calculate progress
  PERCENT=$(( (i * 100) / TOTAL ))
  FILLED=$(( (BAR_WIDTH * i) / TOTAL ))
  EMPTY=$(( BAR_WIDTH - FILLED ))

  # Build progress bar
  BAR=""
  for ((j=0; j<FILLED; j++)); do BAR="${BAR}█"; done
  for ((j=0; j<EMPTY; j++)); do BAR="${BAR} "; done

  # On first iteration, print progress bar and message without moving up
  if [ $i -eq 0 ]; then
    printf "Progress: [${BAR}] %d%%\n" "$PERCENT"
    printf "Processing segment %d: %s - %s (%.2f seconds)" "$i" "$START" "$END" "$DURATION"
  else
    # Move up one line to progress bar, clear, and reprint
    printf "\033[1A\r\033[KProgress: [${BAR}] %d%%\n" "$PERCENT"
    # Clear message line and reprint
    printf "\r\033[KProcessing segment %d: %s - %s (%.2f seconds)" "$i" "$START" "$END" "$DURATION"
  fi

  ffmpeg -hide_banner -loglevel error \
    -fflags +genpts \
    -i "$INPUT_VIDEO" \
    -ss "$START" -t "$DURATION" \
    -reset_timestamps 1 \
    -map 0 \
    -vf "scale=-2:$VIDEO_HEIGHT" \
    -c:v "$VIDEO_CODEC" -preset "$VIDEO_PRESET" -crf "$VIDEO_CRF" \
    -c:a "$AUDIO_CODEC" -b:a "$AUDIO_BITRATE" \
    -f mpegts \
    -mpegts_flags +resend_headers+initial_discontinuity \
    "$SEGMENT_PATH" || continue

  SEGMENT_INFO+=("$DURATION,$SEGMENT_FILE")
  MAX_DURATION=$(bc -l <<< "if ($DURATION > $MAX_DURATION) $DURATION + 1 else $MAX_DURATION")
done

# Update the last iteration to show 100% progress
FILLED=$BAR_WIDTH
BAR=""
for ((j=0; j<FILLED; j++)); do BAR="${BAR}█"; done
# Move up to progress bar, clear, and print final 100% bar
printf "\033[1A\r\033[KProgress: [${BAR}] 100%%\n"
# Clear message line and print "Processing complete!"
printf "\r\033[KProcessing complete!"
# Restore cursor and move to new line
tput cnorm
printf "\n"


echo ""
echo -e "${GREEN}${BOLD}Saving segment to Minio...${RESET}"
echo ""

[[ -d output && "$(ls $OUTPUT_DIR/*.$SEGMENT_EXT 2>/dev/null)" ]] || error_exit "No .ts files found in $OUTPUT_DIR"

mc ls "$MINIO_ALIAS/$BUCKET_NAME" >/dev/null 2>&1 || error_exit "Cannot access MinIO bucket '$BUCKET_NAME' at alias '$MINIO_ALIAS'"

mc cp "$OUTPUT_DIR"/*."$SEGMENT_EXT" "$MINIO_PATH" || error_exit "Failed to upload .ts files to MinIO"


echo ""
echo -e "${GREEN}${BOLD}Saving segments to Redis...${RESET}"
echo ""


# Generate Segments JSON
SEGMENTS_JSON=$(
  {
    printf '{\n  "segments": {\n'
    # Loop through segments and print their JSON representation
    for info in "${SEGMENT_INFO[@]}"; do
      IFS=, read dur file <<< "$info"
      [[ -n "$dur" && "$dur" =~ ^[0-9]+(\.[0-9]+)?$ ]] || error_exit "Invalid duration in SEGMENT_INFO entry: '$info'"
      [[ -n "$file" ]] || error_exit "Invalid file in SEGMENT_INFO entry: '$info'"
      segment_name=$(basename "$file" .ts)
      # *** Construct the path including JOB_ID ***
      segment_path="${JOB_ID}/${file}"
      printf '    "%s": {"path": "%s", "extinf": %.3f},\n' "$segment_name" "$segment_path" "$dur"
    done | sed '$ s/,$//' # Remove trailing comma from the last segment line only

    # Print the closing parts of the JSON
    printf '\n  },\n  "max_duration": %d\n}\n' "$(printf "%.0f" "$MAX_DURATION")"

  } | jq -c . # Pipe the entire collected output of the group to jq
) || error_exit "Failed to generate SEGMENTS_JSON (jq validation failed or generation error)"

# Check if SEGMENTS_JSON was successfully created
if [[ -z "$SEGMENTS_JSON" ]]; then
  error_exit "SEGMENTS_JSON is empty after generation attempt."
fi

log_debug "SEGMENTS_JSON for Job $JOB_ID: $(echo $SEGMENTS_JSON | jq)"

log_info "Pushing segment data for Job $JOB_ID to Redis Hash '$REDIS_PLAYLIST_KEY'"

$REDIS_CMD HSET "$REDIS_PLAYLIST_KEY" "$JOB_ID" "$SEGMENTS_JSON" || error_exit "Failed to push data to Redis (HSET $REDIS_PLAYLIST_KEY $JOB_ID)"

log_info "Successfully pushed data for Job $JOB_ID to Redis."

# log_info "Verifying data in Redis..."
# $REDIS_CMD HGET "$REDIS_PLAYLIST_KEY" "$JOB_ID" >&2

echo ""
echo -e "${GREEN}${BOLD}Updating finished jobs...${RESET}"
echo ""

log_info "Incrementing completed jobs count in Redis..."

current_completed_jobs=$($REDIS_CMD HINCRBY "$REDIS_COMPLETED_JOBS_KEY" "$REDIS_FIELD" 1)
redis_hincrby_status=$?

if [[ $redis_hincrby_status -ne 0 ]]; then
    error_exit "Failed to execute Redis HINCRBY (Exit Code: $redis_hincrby_status)."
fi

if ! [[ "$current_completed_jobs" =~ ^[0-9]+$ ]]; then
    error_exit "Redis HINCRBY did not return a valid number for completed jobs ('$current_completed_jobs'). Key: $REDIS_COMPLETED_JOBS_KEY, Field: $REDIS_FIELD"
fi

log_info "Current completed jobs (after increment): $current_completed_jobs"

log_info "Fetching total jobs count from Redis..."
total_jobs=$($REDIS_CMD GET "$REDIS_TOTAL_JOBS_KEY")
redis_hget_status=$?

if [[ $redis_hget_status -ne 0 ]]; then
    error_exit "Failed to execute Redis GET '$REDIS_TOTAL_JOBS_KEY' (Exit Code: $redis_hget_status)."
fi

if ! [[ "$total_jobs" =~ ^[0-9]+$ ]]; then
    error_exit "Could not retrieve a valid total jobs count from Redis. Key: '$REDIS_TOTAL_JOBS_KEY'. Received: '$total_jobs'."
fi

log_info "Total jobs required: $total_jobs"

if [[ "$current_completed_jobs" -ge "$total_jobs" ]]; then
  log_info "All jobs completed ($current_completed_jobs/$total_jobs). Publishing notification to RabbitMQ."

  # get rabbitmqadmin
  # curl http://localhost:15672/cli/rabbitmqadmin --output rabbimqadmin.py

  rabbitmq_publish_cmd="rabbitmqadmin \
      -c $RABBITMQADMIN_CONFIG -N transcode \
      publish \
      exchange=$RABBITMQ_EXCHANGE \
      routing_key=$RABBITMQ_ROUTING_KEY \
      payload='{\"video_id\": \"$VIDEO_ID\", \"resolution\": \"$VIDEO_HEIGHT\"}'"
      # payload='{\"playlist\": \"$REDIS_PLAYLIST_KEY\"}'"


  log_debug "$rabbitmq_publish_cmd"

  eval $rabbitmq_publish_cmd # Use eval to handle quotes in arguments properly
  rabbitmq_status=$?


  if [[ $rabbitmq_status -eq 0 ]]; then

    log_info "Successfully published message to exchane '$RABBITMQ_EXCHANGE': $(echo "{\"playlist\": \"$REDIS_PLAYLIST_KEY\"}" | jq )"

    # Redis cleanup
    # WARN: delete only the field for the current resolution in completed_jobs key
    # $REDIS_CMD DEL "$REDIS_COMPLETED_JOBS_KEY" "$REDIS_TOTAL_JOBS_KEY" > /dev/null
    # $REDIS_CMD HDEL "$REDIS_COMPLETED_JOBS_KEY" "$VIDEO_HEIGHT" > /dev/null
    # TODO: delete all redis keys transcode* with last service
  else
    log_error "Failed to publish message to RabbitMQ (Exit Code: $rabbitmq_status)"
    error_exit "Failed to notify RabbitMQ about job completion."
  fi

else
  log_info "Not all jobs completed yet ($current_completed_jobs/$total_jobs). No notification sent."
fi

echo ""
echo "Finished!"
exit 0
