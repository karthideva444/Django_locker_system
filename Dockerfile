# Use an official Python runtime as a parent image
FROM python:3.10.12

ENV PYTHONUNBUFFERED=1

# Create container's working directory
RUN mkdir -p /locker

# Set working directory
WORKDIR /locker

COPY pyproject.toml poetry.lock /locker/

RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"


RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --only main

# copy project
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /locker/entrypoint.sh
RUN chmod +x /locker/entrypoint.sh

# Copy all source files to the container's working directory
COPY ./ /locker/

ENTRYPOINT ["/locker/entrypoint.sh"]

EXPOSE 8000

CMD ./manage.py migrate --noinput && ./manage.py collectstatic --noinput && \ 
gunicorn locker.wsgi --bind 0.0.0.0:8000 --workers 2 --worker-class sync --threads 6