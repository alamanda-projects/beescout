# ------- STAGE 1: Builder -------
FROM python:3.13-alpine AS builder

# Create virtual environment
RUN python -m venv /opt/venv

# Make sure to use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

# Copy packages
COPY repository/infra/python/packages/ .

# Install standard packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r stdpack.txt

# Install additional packages
RUN pip install --no-cache-dir -r addpack.txt

# ------- STAGE 2: Runtime -------
FROM python:3.13-alpine AS runtime

# Set arguments
ARG BASE_DIR=/work
ARG APP_DIR=app

# Create a non-root user
RUN adduser --system --no-create-home --shell /bin/bash --uid 1000 dgr_user

# Set current directory
WORKDIR ${BASE_DIR}/${APP_DIR}

# Copy the application
COPY repository/app/ .

# Copy the virtualenv from the builder image
COPY --from=builder /opt/venv /opt/venv

# Make sure to use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

# Specify the user to run the application
USER dgr_user

# Set current directory
WORKDIR ${BASE_DIR}

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888"]