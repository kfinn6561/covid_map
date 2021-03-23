'''
Created on 30 May 2020

@author: kieran
'''
import os
basedir=os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY=os.environ.get('SECRET_KEY') or '****************'
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL') or 'sqlite:///'+os.path.join(basedir,'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    
    #PREFERRED_URL_SCHEME='https'
    SERVER_NAME = "localhost:5000"
    
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL=False
    MAIL_USERNAME = "kieran.errors@gmail.com"
    MAIL_PASSWORD = "***************"
    ADMINS = ['kieran.finn@hotmail.com']