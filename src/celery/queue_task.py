from celery_config import celery
from src.celery.utils.email_worker import (
    send_verification_email,
    send_forgot_email,
    send_custom_email,
)



@celery.task(name="queue_task.send_verification_email_task", queue="email_queue")
def send_verification_email_task(email: str, verification_link: str):
    send_verification_email(email, verification_link)


@celery.task(name="queue_task.send_forgot_email_task", queue="email_queue")
def send_forgot_email_task(email: str, verification_link: str):
    send_forgot_email(email, verification_link)


@celery.task(name="queue_task.send_custom_email_task", queue="email_queue")
def send_custom_email_task(mail_to: str, mail_subject: str, mail_message: str):
    send_custom_email(mail_to, mail_subject, mail_message)
