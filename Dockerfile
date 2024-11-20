# syntax=docker/dockerfile:1
FROM python:3.11-slim

ARG DJANGO_SETTINGS_MODULE=apps.common.settings.development
ENV DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt update && apt install gcc -y

WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
EXPOSE 80

RUN chmod +x ./docker-entrypoint.sh
ENTRYPOINT [ "bash", "docker-entrypoint.sh" ]
