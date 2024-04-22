FROM python:3.11-buster

WORKDIR /app

# Install deps
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=0 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Manually install devtools to avoid circular dependency
RUN pip install poetry==1.8.2
RUN echo "building the image"

# Install dependencies
COPY ./pyproject.toml ./poetry.lock ./app/main.py ./
RUN poetry install --no-root --only main

CMD exec uvicorn main:app --host 0.0.0.0 --port 8080