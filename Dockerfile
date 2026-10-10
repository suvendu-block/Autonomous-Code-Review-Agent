# syntax=docker/dockerfile:1
# One image, three shapes (DEPLOYMENTS.md, ADR-005).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN useradd --create-home --uid 10001 agent

WORKDIR /app

# Layer order: deps first, code after (DEPLOYMENTS.md — image rules).
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app/ ./app/
COPY index.py ./
COPY fixtures/ ./fixtures/

# The CLI writes review_report.json to the working directory.
RUN chown -R agent:agent /app

# Never COPY .env — config is injected at runtime (SECURITY.md).
USER agent

ENTRYPOINT ["python", "index.py"]
CMD []
