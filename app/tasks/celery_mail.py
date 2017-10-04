#encoding:utf-8
from .. import celery, mail, create_app
from ..models import User, Post, Webpush
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

@celery.task
def send_async_webpush(username, postid):
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        print('user:',user)
        post = Post.query.get_or_404(postid)
        followers = user.followers
        print('followers:', user.followers)
        for follower in followers:
            print('follower:',follower)
            if follower.follower != user:
                print('follower.follower:', follower.follower)
                webpush = Webpush(sendto=follower.follower, author=user, post_id=post.id)
