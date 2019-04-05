FROM python:3.7-slim AS builder

ENV PIP_DISABLE_VERSION_CHECK=on
RUN pip install poetry==0.12.11

WORKDIR /app
COPY poetry.lock pyproject.toml /app/
RUN poetry config settings.virtualenvs.create false \
    && poetry install --no-dev --no-interaction
COPY ./ /app/
RUN poetry install --develop=. --no-dev --no-interaction

CMD ["aws-codedeploy-watcher"]
