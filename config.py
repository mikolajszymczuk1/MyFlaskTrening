import os
from dotenv import load_dotenv


load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))
#MYSQL_URI = 'mysql://root:{}@localhost/Flask'.format(os.getenv('DATABASE_PASSWORD'))
#MYSQL_TEST_URI = 'mysql://root:{}@localhost/testFlask'.format(os.getenv('DATABASE_PASSWORD'))
MYSQL_URI = 'mysql+pymysql://root:{}@dbserver/Flask'.format(os.getenv('DATABASE_PASSWORD'))
MYSQL_TEST_URI = 'mysql+pymysql://root:{}@dbserver/testFlask'.format(os.getenv('DATABASE_PASSWORD'))

SQLITE_URI = 'sqlite:///' + os.path.join(basedir, 'Flask.sqlite')
SQLITE_TEST_URI = 'sqlite:///' + os.path.join(basedir, 'testFlask.sqlite')
DATABASE_URI = MYSQL_URI
DATABASE_TEST_URI = MYSQL_TEST_URI


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
    SQLALCHEMY_RECORD_QUERIES = True
    APP_POSTS_PER_PAGE=10
    APP_FOLLOWERS_PER_PAGE=10
    APP_COMMENTS_PER_PAGE=10
    APP_SLOW_DB_QUERY_TIME = 0.5

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = DATABASE_URI


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = DATABASE_TEST_URI
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = DATABASE_URI

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # email errors to the administrators
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()

        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.APP_MAIL_SENDER,
            toaddrs=[cls.APP_ADMIN],
            subject=cls.APP_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure
        )

        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


class DockerConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}
