# Library API (Django + DRF) image.
#   docker build -t library-api-django .
#   docker compose up --build        (with PostgreSQL, see docker-compose.yml)

# Stage 1: install the pinned packages into a virtual environment.
FROM python:3.13-slim AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /venv
COPY requirements.txt .
RUN /venv/bin/pip install -r requirements.txt

# Stage 2: the runtime image, with the virtual environment and the code only.
FROM python:3.13-slim
ENV PATH=/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    TZ=Europe/London
RUN useradd --create-home --uid 10001 library
WORKDIR /app
COPY --from=build /venv /venv
COPY . .
# The code stays owned by root. The app user may only create files in /app
# (a SQLite database when DATABASE_URL is not set).
RUN chown library /app
USER library
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD python -c "import os, urllib.request as u; u.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT', '8000'), timeout=3)"
# Migrate, load the sample data into an empty database, then serve with Waitress.
CMD ["python", "manage.py", "serve"]
