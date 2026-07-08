FROM python:3.13.14-alpine3.24

# Add curl for healthchecks
RUN apk add --update --no-cache curl=8.21.0-r0

WORKDIR /usr/src/app

# Don't write pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Don't buffer stout and stderr
ENV PYTHONUNBUFFERED=1
# No need for virtual environments since container is already isolated
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1
# Set poetry cache dir so we can easily remove it later
ENV POETRY_CACHE_DIR=/tmp/poetry_cache
# Poetry version should match poetry.lock
ARG POETRY_VERSION=2.1

RUN pip install "poetry==${POETRY_VERSION}" --no-cache-dir

# Create non-root user
RUN adduser -D -u 1000 appuser

# Copy pyproject.toml and poetry.lock
COPY --chown=appuser:appuser pyproject.toml poetry.lock README.md ./

# Copy each app
COPY --chown=appuser:appuser accommodation_requests/ /usr/src/app/accommodation_requests/
COPY --chown=appuser:appuser accommodations/ /usr/src/app/accommodations/
COPY --chown=appuser:appuser accounts/ /usr/src/app/accounts/
COPY --chown=appuser:appuser case_management/ /usr/src/app/case_management/
COPY --chown=appuser:appuser deduplication/ /usr/src/app/deduplication/
COPY --chown=appuser:appuser downloads/ /usr/src/app/downloads/
COPY --chown=appuser:appuser guests/ /usr/src/app/guests/
COPY --chown=appuser:appuser hfu_case_management_webapp/ /usr/src/app/hfu_case_management_webapp/
COPY --chown=appuser:appuser hfurb_scripts/ /usr/src/app/hfurb_scripts/
COPY --chown=appuser:appuser ontology/ /usr/src/app/ontology/
COPY --chown=appuser:appuser reassignment_requests/ /usr/src/app/reassignment_requests/
COPY --chown=appuser:appuser safeguarding/ /usr/src/app/safeguarding/
COPY --chown=appuser:appuser sponsors/ /usr/src/app/sponsors/
COPY --chown=appuser:appuser uams/ /usr/src/app/uams/
COPY --chown=appuser:appuser user_management/ /usr/src/app/user_management/
COPY --chown=appuser:appuser visa_applications/ /usr/src/app/visa_applications/
COPY --chown=appuser:appuser unassigned_accommodation_requests/ /usr/src/app/unassigned_accommodation_requests/
COPY --chown=appuser:appuser webapp/ /usr/src/app/webapp/

# Copy the necessary application files
COPY --chown=appuser:appuser static/ /usr/src/app/static/
COPY --chown=appuser:appuser templates/ /usr/src/app/templates/

# Copy manage.py
COPY --chown=appuser:appuser manage.py /usr/src/app/


# Install Dependencies from Codeartifact
RUN --mount=type=secret,id=codeartifact_token \
    --mount=type=secret,id=codeartifact_url \
    /bin/sh -c '\
    set -euo pipefail; \
    TOKEN="$(cat /run/secrets/codeartifact_token)"; \
    CODEARTIFACT_URL="$(cat /run/secrets/codeartifact_url)"; \
    poetry source add --priority=primary codeartifact "$CODEARTIFACT_URL"; \
    poetry config http-basic.codeartifact aws "$TOKEN"; \
    poetry lock; \
    poetry install --no-interaction; \
'

### Remove Poetry and its cache
RUN pip uninstall --yes poetry && rm -rf /tmp/poetry_cache

# Switch to non-root user
USER appuser
