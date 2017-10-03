#encoding:utf-8
from .. import celery, mail, create_app
import os
from flask import current_app
from flask_mail import Message

@celery.task
def send_async_email(to, subject, message, **kwargs):
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    subject = subject
    sender = app.config['FLASKY_MAIL_SENDER']
    recipients=[to]
    html_body = message
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.html = html_body
    app.app_context().push()
    with app.app_context():
        mail.send(msg)
