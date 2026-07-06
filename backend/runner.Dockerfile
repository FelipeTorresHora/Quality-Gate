FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        coreutils \
        git \
        golang-go \
        nodejs \
        npm \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 65532 runner \
    && useradd --uid 65532 --gid 65532 --create-home runner

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt \
    && semgrep --version \
    && bandit --version \
    && detect-secrets --version \
    && pip-audit --version

USER 65532:65532
WORKDIR /workspace

