from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_login import LoginManager
import logging
from logging.handlers import SMTPHandler,RotatingFileHandler
import os

app=Flask(__name__)
app.config.from_object(Config)
login=LoginManager(app)
login.login_view='login'
db=SQLAlchemy(app)
migrate =Migrate(app,db)

mail=Mail(app)

border_status_fname='border_statuses.pkl'
vaccine_status_fname='vaccine_statuses.pkl'






from app import routes, models