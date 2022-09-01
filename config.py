import os
from dotenv import load_dotenv

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))
MYSQL_URI = 'mysql://root:{}@localhost/Flask'.format(os.getenv('DATABASE_PASSWORD'))
MYSQL_TEST_URI = 'mysql://root:{}@localhost/testFlask'.format(os.getenv('DATABASE_PASSWORD'))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'some secret key'
    MAIL_SERVER = 'smtp.wp.pl'
    MAIL_PORT = '465'
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    APP_MAIL_SUBJECT_PREFIX = '[App]'
    APP_MAIL_SENDER = 'App Admin <fela55555@wp.pl>'
    APP_ADMIN = os.getenv('APP_ADMIN')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    APP_POSTS_PER_PAGE=10

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = MYSQL_URI

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = MYSQL_TEST_URI

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = MYSQL_URI


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
