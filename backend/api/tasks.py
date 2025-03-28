from celery import Celery
from backend.api.config import REDIS_URL
from backend.services.generate_response import generate_email_response
from backend.models.email_model import save_email



# ✅ Celery Configuration
celery = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

@celery.task
def schedule_email_response(email_text, category, recipient):
    ai_response = generate_email_response(email_text)
    save_email(recipient, f"Re: {category}", ai_response, status="Scheduled")
    return ai_response
