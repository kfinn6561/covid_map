'''
Created on 7 Jun 2020

@author: kieran
'''
from flask_mail import Message
from app import app,mail
from threading import Thread


def send_async_email(app,msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email,args=(app,msg)).start()