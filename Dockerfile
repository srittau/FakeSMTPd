FROM python:3.14-alpine

# Prepare app dir
RUN mkdir /app
WORKDIR /app
RUN mkdir ./run ./log

# Prepare virtual environment
ENV UV_PROJECT_ENVIRONMENT=/app/virtualenv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock /app/
RUN uv venv ./virtualenv

# Install application
COPY README.md LICENSE pyproject.toml ./
COPY bin/ ./bin
COPY fakesmtpd/ ./fakesmtpd
RUN uv sync --locked --no-dev

# Start eventstreamd
EXPOSE 25
COPY start.sh ./
CMD ["/app/start.sh"]
