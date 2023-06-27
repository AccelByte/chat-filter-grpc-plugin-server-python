PIP_EXEC_PATH = bin/pip
PROTO_DIR = app/proto
PYTHON_EXEC_PATH = bin/python
SOURCE_DIR = src
TESTS_DIR = tests
VENV_DIR = venv
VENV_DEV_DIR = venv-dev

IMAGE_NAME := $(shell basename "$$(pwd)")-app
BUILDER := grpc-plugin-server-builder

setup:
	rm -rf ${VENV_DEV_DIR}
	python3.9 -m venv ${VENV_DEV_DIR} \
			&& ${VENV_DEV_DIR}/${PIP_EXEC_PATH} install --upgrade pip \
			&& ${VENV_DEV_DIR}/${PIP_EXEC_PATH} install -r requirements-dev.txt \
			&& ${VENV_DEV_DIR}/${PYTHON_EXEC_PATH} -m spacy download en

	rm -rf ${VENV_DIR}
	python3.9 -m venv ${VENV_DEV_DIR} \
			&& ${VENV_DIR}/${PIP_EXEC_PATH} install --upgrade pip \
			&& ${VENV_DIR}/${PIP_EXEC_PATH} install -r requirements.txt \
			&& ${VENV_DIR}/${PYTHON_EXEC_PATH} -m spacy download en

clean:
	rm -f ${SOURCE_DIR}/${PROTO_DIR}/*_grpc.py
	rm -f ${SOURCE_DIR}/${PROTO_DIR}/*_pb2.py
	rm -f ${SOURCE_DIR}/${PROTO_DIR}/*_pb2.pyi
	rm -f ${SOURCE_DIR}/${PROTO_DIR}/*_pb2_grpc.py

proto: clean
	docker run -t --rm -u $$(id -u):$$(id -g) -v $$(pwd):/data/ -w /data/ rvolosatovs/protoc:4.0.0 \
		--proto_path=${PROTO_DIR}=${SOURCE_DIR}/${PROTO_DIR} \
		--python_out=${SOURCE_DIR} \
		--grpc-python_out=${SOURCE_DIR} \
		${SOURCE_DIR}/${PROTO_DIR}/*.proto

build: proto

image:
	docker buildx build -t ${IMAGE_NAME} --load .

imagex:
	docker buildx inspect $(BUILDER) || docker buildx create --name $(BUILDER) --use
	docker buildx build -t ${IMAGE_NAME} --platform linux/arm64/v8,linux/amd64 .
	docker buildx build -t ${IMAGE_NAME} --load .
	docker buildx rm --keep-state $(BUILDER)

imagex_push:
	@test -n "$(IMAGE_TAG)" || (echo "IMAGE_TAG is not set (e.g. 'v0.1.0', 'latest')"; exit 1)
	@test -n "$(REPO_URL)" || (echo "REPO_URL is not set"; exit 1)
	docker buildx inspect $(BUILDER) || docker buildx create --name $(BUILDER) --use
	docker buildx build -t ${REPO_URL}:${IMAGE_TAG} --platform linux/arm64/v8,linux/amd64 --push .
	docker buildx rm --keep-state $(BUILDER)

lint:
	rm -f lint.err
	docker run --rm -t -u $$(id -u):$$(id -g) -v $$(pwd):/data -w /data -e PIP_CACHE_DIR=/data/.cache/pip -e PYLINTHOME=/data/.cache/pylint  --entrypoint /bin/sh python:3.9-slim \
			-c 'PYTHONPATH=${TESTS_DIR}:${SOURCE_DIR}:${PROTO_DIR} ${VENV_DEV_DIR}/${PYTHON_EXEC_PATH} -m pylint -j 0 app || exit $$(( $$? & (1+2+32) ))' \
					|| touch lint.err
	[ ! -f lint.err ]

beautify:
	docker run -t --rm -u $$(id -u):$$(id -g) -v $$(pwd):/data/ -w /data/ cytopia/black:22-py3.9 \
		${SOURCE_DIR} \
		${TESTS_DIR}

test:
	docker run --rm -t -u $$(id -u):$$(id -g) -v $$(pwd):/data -w /data -e PIP_CACHE_DIR=/data/.cache/pip --entrypoint /bin/sh python:3.9-slim \
			-c 'PYTHONPATH=${TESTS_DIR}:${SOURCE_DIR}:${PROTO_DIR} ${VENV_DEV_DIR}/${PYTHON_EXEC_PATH} -m app_tests'

help:
	docker run --rm -t -u $$(id -u):$$(id -g) -v $$(pwd):/data -w /data -e PIP_CACHE_DIR=/data/.cache/pip --entrypoint /bin/sh python:3.9-slim \
			-c 'PYTHONPATH=${SOURCE_DIR}:${PROTO_DIR} ${VENV_DIR}/${PYTHON_EXEC_PATH} -m app --help'

run:
	docker run --rm -t -u $$(id -u):$$(id -g) -v $$(pwd):/data -w /data -e PIP_CACHE_DIR=/data/.cache/pip --entrypoint /bin/sh python:3.9-slim \
			-c 'GRPC_VERBOSITY=debug PYTHONPATH=${SOURCE_DIR}:${PROTO_DIR} ${VENV_DIR}/${PYTHON_EXEC_PATH} -m app'