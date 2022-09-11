FROM python:3.9-alpine

RUN apk add gcc musl-dev mariadb-connector-c-dev

ENV FLASK_APP main.py
ENV FLASK_CONFIG docker

RUN adduser -D appAdmin
USER appAdmin

WORKDIR /home/appAdmin

COPY requirements requirements
RUN python -m venv env
RUN env/bin/pip install -r requirements/docker.txt

COPY app app
COPY migrations migrations
COPY main.py config.py boot.sh ./

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
