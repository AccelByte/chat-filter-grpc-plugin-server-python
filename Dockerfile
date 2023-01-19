# Copyright (c) 2022 AccelByte Inc. All Rights Reserved.
# This is licensed software from AccelByte Inc, for limitations
# and restrictions contact your company contract manager.

FROM --platform=$BUILDPLATFORM rvolosatovs/protoc:3.3.0 as proto

WORKDIR /build

COPY src/app/proto src/app/proto

RUN protoc --proto_path=app/proto=src/app/proto \
        --python_out=src \
        --grpc-python_out=src \
        src/app/proto/*.proto



FROM python:3.9-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

# Install spacy language
# For more info, please refer to https://spacy.io/usage/models#languages
RUN python -m spacy download en

WORKDIR /app
COPY . ./
COPY --from=proto /build/src/app/proto src/app/proto

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Plugin arch gRPC server port
EXPOSE 6565

# Prometheus /metrics web server port
EXPOSE 8080

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
ENTRYPOINT PYTHONPATH=/app/src python -m app -f /app/data/profanities.json
