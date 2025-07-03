package kubernetes

import (
	"context"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"transcoder/models"
	"transcoder/utils"

	batchv1 "k8s.io/api/batch/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
)

type Client struct {
	kubernetesClientset *kubernetes.Clientset
}

func NewClient() (*Client, error) {
	kubernetesConfig, err := loadKubernetesConfiguration()
	if err != nil {
		return nil, err
	}

	clientset, err := createKubernetesClientset(kubernetesConfig)
	if err != nil {
		return nil, err
	}

	return &Client{kubernetesClientset: clientset}, nil
}

func (c *Client) SubmitJob(ctx context.Context, jobConfig models.JobConfig) error {
	if err := c.ensureConfigMapExists(ctx, jobConfig); err != nil {
		return err
	}

	if err := c.createKubernetesJob(ctx, jobConfig); err != nil {
		return err
	}

	return nil
}

func loadKubernetesConfiguration() (*rest.Config, error) {
	config, err := rest.InClusterConfig()
	if err != nil {
		return loadKubeconfigFromFile()
	}
	log.Println("Using in-cluster Kubernetes configuration")
	return config, nil
}

func loadKubeconfigFromFile() (*rest.Config, error) {
	log.Println("In-cluster config unavailable - attempting kubeconfig file")
	kubeconfigPath := determineKubeconfigPath()

	config, err := clientcmd.BuildConfigFromFlags("", kubeconfigPath)
	if err != nil {
		return nil, fmt.Errorf("kubeconfig loading failed from %s: %w", kubeconfigPath, err)
	}

	log.Printf("Using kubeconfig from: %s", kubeconfigPath)
	return config, nil
}

func determineKubeconfigPath() string {
	kubeconfigPath := os.Getenv("KUBECONFIG")
	if kubeconfigPath != "" {
		return kubeconfigPath
	}

	home, err := os.UserHomeDir()
	if err != nil {
		log.Printf("Unable to determine home directory: %v", err)
		return ""
	}

	return filepath.Join(home, ".kube", "config")
}

func createKubernetesClientset(config *rest.Config) (*kubernetes.Clientset, error) {
	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, fmt.Errorf("Kubernetes clientset creation failed: %w", err)
	}
	return clientset, nil
}

func (c *Client) ensureConfigMapExists(ctx context.Context, jobConfig models.JobConfig) error {
	configMapName := c.generateConfigMapName(jobConfig)
	timestampFileName := "timestamps.txt"

	configMap := c.buildConfigMapSpec(configMapName, jobConfig, timestampFileName)

	if err := c.createOrUpdateConfigMap(ctx, configMap, jobConfig.Namespace); err != nil {
		return fmt.Errorf("ConfigMap management failed: %w", err)
	}

	log.Printf("ConfigMap ready: %s", configMapName)
	return nil
}

func (c *Client) createKubernetesJob(ctx context.Context, jobConfig models.JobConfig) error {
	jobName := c.generateJobName(jobConfig)
	configMapName := c.generateConfigMapName(jobConfig)
	timestampFileName := "timestamps.txt"

	job := c.buildJobSpec(jobName, configMapName, jobConfig, timestampFileName)

	if err := c.submitJobToKubernetes(ctx, job, jobConfig.Namespace); err != nil {
		return fmt.Errorf("Kubernetes job submission failed: %w", err)
	}

	log.Printf("Job submitted successfully: %s", jobName)
	return nil
}

func (c *Client) generateConfigMapName(jobConfig models.JobConfig) string {
	return fmt.Sprintf("ts-%s-%d",
		utils.SanitizeLabel(jobConfig.VideoID),
		jobConfig.SegmentID)
}

func (c *Client) generateJobName(jobConfig models.JobConfig) string {
	sanitizedVideoID := utils.SanitizeLabel(jobConfig.VideoID)
	if len(sanitizedVideoID) > 30 {
		sanitizedVideoID = sanitizedVideoID[:30]
	}
	return fmt.Sprintf("transcode-%s-%d-%s",
		sanitizedVideoID,
		jobConfig.SegmentID,
		jobConfig.Resolution)
}

func (c *Client) createOrUpdateConfigMap(ctx context.Context, configMap *corev1.ConfigMap, namespace string) error {
	_, err := c.kubernetesClientset.CoreV1().ConfigMaps(namespace).Create(ctx, configMap, metav1.CreateOptions{})
	if err != nil {
		if errors.IsAlreadyExists(err) {
			return c.updateExistingConfigMap(ctx, configMap, namespace)
		}
		return fmt.Errorf("ConfigMap creation failed: %w", err)
	}
	return nil
}

func (c *Client) updateExistingConfigMap(ctx context.Context, configMap *corev1.ConfigMap, namespace string) error {
	_, err := c.kubernetesClientset.CoreV1().ConfigMaps(namespace).Update(ctx, configMap, metav1.UpdateOptions{})
	if err != nil {
		return fmt.Errorf("ConfigMap update failed: %w", err)
	}
	return nil
}

func (c *Client) submitJobToKubernetes(ctx context.Context, job *batchv1.Job, namespace string) error {
	_, err := c.kubernetesClientset.BatchV1().Jobs(namespace).Create(ctx, job, metav1.CreateOptions{})
	if err != nil {
		if errors.IsAlreadyExists(err) {
			log.Printf("Job %s already exists - skipping creation", job.Name)
			return nil
		}
		return fmt.Errorf("Job creation failed: %w", err)
	}
	return nil
}

func (c *Client) buildConfigMapSpec(name string, jobConfig models.JobConfig, timestampFileName string) *corev1.ConfigMap {
	return &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: jobConfig.Namespace,
			Labels:    c.createResourceLabels(jobConfig),
		},
		Data: map[string]string{
			timestampFileName: jobConfig.TimestampData,
		},
	}
}

func (c *Client) buildJobSpec(name, configMapName string, jobConfig models.JobConfig, timestampFileName string) *batchv1.Job {
	podSpec := c.createPodSpecification(name, configMapName, jobConfig, timestampFileName)

	return &batchv1.Job{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: jobConfig.Namespace,
			Labels:    c.createResourceLabels(jobConfig),
			Annotations: map[string]string{
				"timestamp-configmap": configMapName,
			},
		},
		Spec: batchv1.JobSpec{
			BackoffLimit: Pointer(int32(2)),
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: c.createResourceLabels(jobConfig),
				},
				Spec: podSpec,
			},
		},
	}
}

func (c *Client) createResourceLabels(jobConfig models.JobConfig) map[string]string {
	return map[string]string{
		"app":        "transcoder",
		"video-id":   utils.SanitizeLabel(jobConfig.VideoID),
		"segment-id": strconv.Itoa(jobConfig.SegmentID),
		"resolution": jobConfig.Resolution,
	}
}

func (c *Client) createPodSpecification(jobName, configMapName string, jobConfig models.JobConfig, timestampFileName string) corev1.PodSpec {
	mountPaths := c.defineMountPaths()
	initContainer := c.createInitContainer(jobConfig, mountPaths)
	transcodeContainer := c.createTranscodeContainer(jobConfig, timestampFileName, mountPaths)
	volumes := c.createVolumes(configMapName, jobConfig)

	return corev1.PodSpec{
		InitContainers: []corev1.Container{initContainer},
		Containers:     []corev1.Container{transcodeContainer},
		Volumes:        volumes,
		RestartPolicy:  corev1.RestartPolicyNever,
	}
}

type mountPaths struct {
	timestamp               string
	minioConfig             string
	rabbitmqAdminConfig     string
	mcConfigSecretForInit   string
	mcConfigEmptyDirForInit string
}

func (c *Client) defineMountPaths() mountPaths {
	return mountPaths{
		timestamp:               "/transcode-data/timestamps",
		minioConfig:             "/mc_config",
		rabbitmqAdminConfig:     "/rabbitmqadmin_config",
		mcConfigSecretForInit:   "/tmp/secret-mc-config",
		mcConfigEmptyDirForInit: "/init-mc-config",
	}
}

func (c *Client) createInitContainer(jobConfig models.JobConfig, paths mountPaths) corev1.Container {
	command := fmt.Sprintf("mkdir -p %s && cp %s/config.json %s/config.json && chmod -R 777 %s",
		paths.mcConfigEmptyDirForInit,
		paths.mcConfigSecretForInit,
		paths.mcConfigEmptyDirForInit,
		paths.mcConfigEmptyDirForInit)

	return corev1.Container{
		Name:            "init-mc-config-copy",
		Image:           jobConfig.MCConfigInitImage,
		ImagePullPolicy: corev1.PullIfNotPresent,
		Command:         []string{"sh", "-c", command},
		VolumeMounts: []corev1.VolumeMount{
			{
				Name:      "minio-config-volume",
				MountPath: paths.mcConfigSecretForInit,
				ReadOnly:  true,
			},
			{
				Name:      "mc-config-writable",
				MountPath: paths.mcConfigEmptyDirForInit,
				ReadOnly:  false,
			},
		},
		Resources: corev1.ResourceRequirements{
			Requests: corev1.ResourceList{
				corev1.ResourceCPU:    resource.MustParse("50m"),
				corev1.ResourceMemory: resource.MustParse("64Mi"),
			},
			Limits: corev1.ResourceList{
				corev1.ResourceCPU:    resource.MustParse("100m"),
				corev1.ResourceMemory: resource.MustParse("128Mi"),
			},
		},
	}
}

func (c *Client) createTranscodeContainer(jobConfig models.JobConfig, timestampFileName string, paths mountPaths) corev1.Container {
	timestampFilePath := filepath.Join(paths.timestamp, timestampFileName)
	args := c.buildTranscodeArgs(jobConfig, timestampFilePath)
	envVars := c.buildEnvironmentVariables(jobConfig, paths)
	volumeMounts := c.buildVolumeMounts(paths)

	return corev1.Container{
		Name:            "transcoder",
		Image:           jobConfig.Image,
		ImagePullPolicy: corev1.PullIfNotPresent,
		Command:         []string{"./transcode.sh"},
		Args:            args,
		Env:             envVars,
		VolumeMounts:    volumeMounts,
		Resources: corev1.ResourceRequirements{
			Requests: corev1.ResourceList{
				corev1.ResourceCPU:    resource.MustParse("500m"),
				corev1.ResourceMemory: resource.MustParse("512Mi"),
			},
			Limits: corev1.ResourceList{
				corev1.ResourceCPU:    resource.MustParse("1"),
				corev1.ResourceMemory: resource.MustParse("1Gi"),
			},
		},
	}
}

func (c *Client) buildTranscodeArgs(jobConfig models.JobConfig, timestampFilePath string) []string {
	args := []string{
		fmt.Sprintf("--job-id=%d", jobConfig.SegmentID),
		fmt.Sprintf("--video-path=%s", jobConfig.VideoURL),
		fmt.Sprintf("--timestamp-file=%s", timestampFilePath),
		fmt.Sprintf("--crf=%d", jobConfig.CRF),
		fmt.Sprintf("--preset=%s", jobConfig.Preset),
		fmt.Sprintf("--resolution=%s", jobConfig.Resolution),
		fmt.Sprintf("--video-id=%s", jobConfig.VideoID),
	}

	if jobConfig.AllowHTTP {
		args = append(args, "--allow-http")
	}

	return args
}

func (c *Client) buildEnvironmentVariables(jobConfig models.JobConfig, paths mountPaths) []corev1.EnvVar {
	rabbitmqAdminConfigFile := "rabbitmqadmin.conf"

	envVars := []corev1.EnvVar{
		{Name: "BUCKET_NAME", Value: jobConfig.OutputBucket},
		{Name: "REDIS_HOST", Value: jobConfig.RedisHost},
		{Name: "REDIS_PORT", Value: strconv.Itoa(jobConfig.RedisPort)},
		{Name: "REDISCLI_AUTH", Value: jobConfig.RedisPassword},
		{Name: "REDIS_DB", Value: strconv.Itoa(jobConfig.RedisDB)},
		{Name: "REDIS_TOTAL_JOBS_KEY", Value: jobConfig.TotalJobsKey},
		{Name: "REDIS_COMPLETED_JOBS_KEY", Value: jobConfig.CompletedJobsKey},
		{Name: "REDIS_MASTER_PLAYLIST_META", Value: jobConfig.MasterPlaylistMetaKey},
		{Name: "MC_CONFIG_DIR", Value: paths.minioConfig},
		{Name: "MINIO_ALIAS", Value: jobConfig.MinioAlias},
		{Name: "RABBITMQ_EXCHANGE", Value: jobConfig.RabbitMQExchange},
		{Name: "RABBITMQ_ROUTING_KEY", Value: jobConfig.RabbitMQRoutingKey},
		{Name: "RABBITMQADMIN_CONFIG", Value: filepath.Join(paths.rabbitmqAdminConfig, rabbitmqAdminConfigFile)},
	}

	return c.filterEmptyRedisPassword(envVars, jobConfig.RedisPassword)
}

func (c *Client) createVolumes(configMapName string, jobConfig models.JobConfig) []corev1.Volume {
	return []corev1.Volume{
		c.createTimestampVolume(configMapName),
		c.createMinioConfigVolume(jobConfig.MinioSecretName),
		c.createRabbitMQAdminVolume(jobConfig.RabbitMQAdminSecretName),
		c.createWritableMinioConfigVolume(),
	}
}

func (c *Client) buildVolumeMounts(paths mountPaths) []corev1.VolumeMount {
	return []corev1.VolumeMount{
		{
			Name:      "timestamp-volume",
			MountPath: paths.timestamp,
			ReadOnly:  true,
		},
		{
			Name:      "mc-config-writable",
			MountPath: paths.minioConfig,
			ReadOnly:  false,
		},
		{
			Name:      "rabbitmq-admin-config-volume",
			MountPath: paths.rabbitmqAdminConfig,
			ReadOnly:  true,
		},
	}
}

func (c *Client) filterEmptyRedisPassword(envVars []corev1.EnvVar, redisPassword string) []corev1.EnvVar {
	if redisPassword == "" {
		for i, env := range envVars {
			if env.Name == "REDIS_PASSWORD" {
				return append(envVars[:i], envVars[i+1:]...)
			}
		}
	}
	return envVars
}

func (c *Client) createTimestampVolume(configMapName string) corev1.Volume {
	return corev1.Volume{
		Name: "timestamp-volume",
		VolumeSource: corev1.VolumeSource{
			ConfigMap: &corev1.ConfigMapVolumeSource{
				LocalObjectReference: corev1.LocalObjectReference{
					Name: configMapName,
				},
			},
		},
	}
}

func (c *Client) createMinioConfigVolume(secretName string) corev1.Volume {
	return corev1.Volume{
		Name: "minio-config-volume",
		VolumeSource: corev1.VolumeSource{
			Secret: &corev1.SecretVolumeSource{
				SecretName: secretName,
				Items: []corev1.KeyToPath{
					{
						Key:  "config.json",
						Path: "config.json",
					},
				},
			},
		},
	}
}

func (c *Client) createRabbitMQAdminVolume(secretName string) corev1.Volume {
	return corev1.Volume{
		Name: "rabbitmq-admin-config-volume",
		VolumeSource: corev1.VolumeSource{
			Secret: &corev1.SecretVolumeSource{
				SecretName: secretName,
				Items: []corev1.KeyToPath{
					{
						Key:  "rabbitmqadmin.conf",
						Path: "rabbitmqadmin.conf",
					},
				},
			},
		},
	}
}

func (c *Client) createWritableMinioConfigVolume() corev1.Volume {
	return corev1.Volume{
		Name: "mc-config-writable",
		VolumeSource: corev1.VolumeSource{
			EmptyDir: &corev1.EmptyDirVolumeSource{},
		},
	}
}

func Pointer[T any](v T) *T {
	return &v
}
