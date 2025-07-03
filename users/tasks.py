from email.mime.text import MIMEText
from celery import Celery
import smtplib
from decouple import config
import logging
from tenacity import retry, stop_after_attempt, wait_fixed
from probe_server import ProbeState, start_probe_server
from celery.signals import worker_ready, worker_shutdown

CELERY_BROKER = config('CELERY_BROKER_URL')
CELERY_BACKEND = config('CELERY_BACKEND_URL')
EMAIL_ADDRESS = config('EMAIL_ADDRESS')
EMAIL_SERVER_NAME = config('EMAIL_SERVER_NAME')
EMAIL_SERVER_PORT = config('EMAIL_SERVER_PORT', cast=int)
EMAIL_PASSWORD = config("EMAIL_PASSWORD")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
def make_celery_app():
    logger.info('Attempting to connect to Celery broker/backend...')
    app = Celery(
        "tasks",
        broker=CELERY_BROKER,
        backend=CELERY_BACKEND
    )
    # Test connection by pinging broker
    try:
        app.control.ping(timeout=2)
    except Exception as e:
        logger.error(f'Celery broker/backend connection failed: {e}')
        raise
    logger.info('Celery broker/backend connection established.')
    return app

app = make_celery_app()
start_probe_server(port=8084)

app.conf.update(
    task_routes={
        "send_email_task": {"queue": "email"},
    },
    worker_log_format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    worker_redirect_stdouts_level='INFO',
    broker_connection_retry_on_startup=True,
)

@app.task(name="send_email_task")
def send_email_task(recipient, token_url):
    subject = "Activate Your Account Right NOW"
    body = f"Click the link to activate your account: {token_url}"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = recipient

    try:
        with smtplib.SMTP_SSL(EMAIL_SERVER_NAME, EMAIL_SERVER_PORT) as smtp_server:
            smtp_server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp_server.sendmail(EMAIL_ADDRESS, recipient, msg.as_string())
        return f"Email sent to {recipient}"
    except Exception as e:
        return f"Failed to send email: {str(e)}"

@worker_ready.connect
def on_worker_ready(**kwargs):
    ProbeState.readiness = True

@worker_shutdown.connect
def on_worker_shutdown(**kwargs):
    ProbeState.liveness = False
    ProbeState.readiness = False

