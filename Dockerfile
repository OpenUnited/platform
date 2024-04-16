# syntax=docker/dockerfile:1
FROM python:3.10-alpine as builder
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN set -ex \
    && apk add --no-cache --virtual .build-deps postgresql-dev build-base \
    && python -m venv /app/.venv \
    && /app/.venv/bin/pip install --upgrade pip \
    && /app/.venv/bin/pip install --no-cache-dir -r /app/requirements.txt \
    && runDeps="$(scanelf --needed --nobanner --recursive /app/.venv \
        | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
        | sort -u \
        | xargs -r apk info --installed \
        | sort -u)" \
    && apk add --virtual rundeps $runDeps \
    && apk del .build-deps
COPY . /app
FROM python:3.10-alpine as runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV /app/.venv
ENV PATH /app/.venv/bin:$PATH
EXPOSE 80
COPY --from=builder /app/ /app/
RUN chmod +x ./docker-entrypoint.sh
ENTRYPOINT [ "sh", "docker-entrypoint.sh" ]