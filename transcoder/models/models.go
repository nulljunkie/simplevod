package models

type Message struct {
	MessageID          int       `json:"message_id"`
	VideoURL           string    `json:"video_url"`
	VideoID            string    `json:"video_id"`
	Timestamps         []float64 `json:"timestamps"`
	TotalVideoDuration float64   `json:"total_video_duration"`
	TotalMessages      int       `json:"total_messages"`
}

type JobConfig struct {
	SegmentID               int
	Resolution              string
	VideoID                 string
	VideoURL                string
	TimestampData           string
	CRF                     int
	Preset                  string
	Image                   string
	Namespace               string
	OutputBucket            string
	MinioSecretName         string
	RabbitMQAdminSecretName string
	RedisHost               string
	RedisPort               int
	RedisPassword           string
	RedisDB                 int
	TotalJobsKey            string
	CompletedJobsKey        string
	MasterPlaylistMetaKey   string
	MCConfigInitImage       string
	MinioAlias              string
	RabbitMQExchange        string
	RabbitMQRoutingKey      string
	AllowHTTP               bool
}
