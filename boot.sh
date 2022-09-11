#!/bin/sh

source env/bin/activate

while true; do
  flask deploy
  if [[ "$?" == "0" ]]; then
    break
  fi
  echo "Deploy command faild !"
  sleep 5
done

exec gunicorn -b :5000 --access-logfile - --error-logfile - main:app
