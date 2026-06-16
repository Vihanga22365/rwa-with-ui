# syntax=docker/dockerfile:1
# ---- Backend: FastAPI (Python 3.13) served by uvicorn ----
# Uses uv + the committed uv.lock for reproducible, pinned installs.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# 1) Install locked dependencies first (cached layer; only changes when the
#    lockfile changes). --no-install-project: we run from source, not as a pkg.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# 2) Copy application code + data files (graph.py reads the .xlsx via the CWD,
#    so they must live next to the code at /app).
COPY . .

# Put the project virtualenv on PATH so `uvicorn` resolves.
ENV PATH="/app/.venv/bin:$PATH"

# Run as a non-root user (created by the base image is not guaranteed; make one).
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Single worker on purpose: the session store in webapp_api.py is an in-process
# dict, so multiple workers would split sessions. See DEPLOYMENT.md "Scaling".
CMD ["uvicorn", "webapp_api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
