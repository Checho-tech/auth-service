# syntax=docker/dockerfile:1

# ---- Builder stage: installs dependencies and builds the package ----
FROM python:3.12-slim AS builder

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Pinned, reproducible dependency versions (see docs/00_NOTAS_PERSONALES_INSTALACIONES.txt
# for why bcrypt is pinned <4.1) — installed from the lock file, not resolved fresh here.
COPY requirements-lock.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements-lock.txt

COPY src ./src
# --no-deps: dependencies are already installed above from the lock file;
# this just installs our own package (non-editable) into the venv.
RUN pip install --no-cache-dir --no-deps .


# ---- Runtime stage: slim image, no compilers, no source tree, non-root ----
FROM python:3.12-slim

RUN groupadd --system appuser && useradd --system --gid appuser --create-home appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
# Only Alembic's own files are needed at runtime (for the one-off "migrate"
# service) — the application code itself already lives in /opt/venv as an
# installed package, not as a loose source tree.
COPY alembic ./alembic
COPY alembic.ini ./

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# No curl in the slim image — a one-line urllib request avoids adding a
# package just for the healthcheck.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "auth_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
