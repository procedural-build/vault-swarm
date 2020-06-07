FROM python:3.8.3-alpine as build

# Declare package versions
ENV PIPENV 2018.11.26
ENV BUILD_BASE 0.5-r1

RUN pip install pipenv==$PIPENV

COPY Pipfile* /tmp/
WORKDIR /tmp
RUN pipenv lock --requirements > requirements.txt  && pipenv lock --requirements --dev > requirements_dev.txt

RUN apk update
# Add GCC (required for some python libraries)
RUN apk add build-base=$BUILD_BASE --no-cache

RUN pip wheel --wheel-dir=/root/wheels -r /tmp/requirements.txt
RUN pip wheel --wheel-dir=/root/wheels_dev -r /tmp/requirements_dev.txt

FROM python:3.8.3-alpine AS production

COPY --from=build /tmp/requirements* /tmp/
COPY --from=build /root/wheels /root/wheels

RUN mkdir /app
WORKDIR /app

RUN pip install --no-index --find-links=/root/wheels -r /tmp/requirements.txt

COPY src/ /app

CMD ["python /app/main.py"]

FROM python:3.8.3-alpine AS dev
# Dev container with dev dependencies installed
COPY --from=production / /
COPY --from=build /root/wheels_dev /root/wheels_dev

WORKDIR /app

# Install Dev dependencies
RUN pip install --no-index --find-links=/root/wheels_dev -r /tmp/requirements_dev.txt

CMD ["python /app/main.py"]