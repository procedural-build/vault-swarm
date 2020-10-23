# This is a python:3.8.3-alpine image. We are using the hash to be completely consistant on jenkins builds
ARG PYTHON_VERSION=sha256:c5623df482648cacece4f9652a0ae04b51576c93773ccd43ad459e2a195906dd

FROM python@$PYTHON_VERSION as build

# Declare package versions
ENV PIPENV 2020.6.2
ENV BUILD_BASE 0.5-r2

RUN pip install pipenv==$PIPENV

COPY Pipfile* /tmp/
WORKDIR /tmp
RUN pipenv lock --requirements > requirements.txt  && pipenv lock --requirements --dev > requirements_dev.txt

RUN apk update
# Add GCC (required for some python libraries)
RUN apk add build-base=$BUILD_BASE --no-cache

RUN pip wheel --wheel-dir=/root/wheels -r /tmp/requirements.txt
RUN pip wheel --wheel-dir=/root/wheels_dev -r /tmp/requirements_dev.txt

FROM python@$PYTHON_VERSION AS production

COPY --from=build /tmp/requirements* /tmp/
COPY --from=build /root/wheels /root/wheels

RUN mkdir /app
WORKDIR /app

RUN pip install --no-index --find-links=/root/wheels -r /tmp/requirements.txt

COPY src/ /app
COPY VERSION /app

CMD ["python main.py"]

FROM python@$PYTHON_VERSION AS dev
# Dev container with dev dependencies installed
COPY --from=production / /
COPY --from=build /root/wheels_dev /root/wheels_dev

WORKDIR /app

# Install Dev dependencies
RUN pip install --no-index --find-links=/root/wheels_dev -r /tmp/requirements_dev.txt

CMD ["python /app/main.py"]