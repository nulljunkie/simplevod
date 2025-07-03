package kubernetes

import (
	"context"
	"transcoder/models"
)

type JobSubmitter interface {
	SubmitJob(ctx context.Context, cfg models.JobConfig) error
}

