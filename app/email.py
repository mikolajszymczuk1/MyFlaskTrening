from flask import Flask, render_template, current_app
from flask_mail import Message
from . import mail
from threading import Thread


def send_async_email(app: Flask, msg: Message) -> None:
    with app.app_context():
        mail.send(msg)


def send_email(to: str, subject: str, template: str, **kwargs) -> Thread:
    """ Function to sending mails """

    app = current_app._get_current_object()  # type: ignore
    msg = Message(app.config['APP_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=app.config['APP_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr
