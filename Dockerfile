FROM python:3.10-bullseye AS poetry

RUN pip install -U pip poetry
COPY pyproject.toml ./pyproject.toml
COPY poetry.lock ./poetry.lock
RUN poetry export -o requirements.txt

FROM python:3.10-bullseye

# Prepare app dir
RUN mkdir /app
WORKDIR /app
RUN mkdir ./run ./log

# Prepare virtualenv
RUN python3 -m venv ./virtualenv
RUN ./virtualenv/bin/pip --disable-pip-version-check install --upgrade pip poetry

# Install dependencies
COPY --from=poetry requirements.txt /app/requirements.txt
RUN ./virtualenv/bin/pip --disable-pip-version-check install -r requirements.txt

# Install application
COPY README.md pyproject.toml ./
COPY bin/ ./bin
COPY fakesmtpd/ ./fakesmtpd
RUN ./virtualenv/bin/pip install .

# Start eventstreamd
EXPOSE 25
COPY start.sh ./
CMD ["/app/start.sh"]
