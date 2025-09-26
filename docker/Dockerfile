ARG PYTHON_VERSION=3.12
ARG POETRY_VERSION=2.1

FROM harbor.cloud.infn.it/datacloud-middleware/poetry:${POETRY_VERSION}-python${PYTHON_VERSION} AS base

WORKDIR /app

COPY ./pyproject.toml ./poetry.lock ./README.md /app/
COPY ./orchestrator /app/orchestrator

RUN poetry install --without dev --with rest-api,mysql

USER ${USERNAME}

CMD ["fastapi", "run", "/app/orchestrator/main.py", "--port", "80"]
