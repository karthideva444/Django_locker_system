PYTHON = python3.10.12

.PHONY = create setup lock install run-server migrate migrations superuser

create:
	virtualenv -p ${PYTHON} venv

setup:
	pip3 install poetry==1.1.7
	sudo apt-get install libpq-dev python3.8-dev


lock:
	poetry lock

install:
	poetry install --no-root

run-server:
	poetry run python3 manage.py runserver 0.0.0.0:8001

migrate:
	poetry run python3 manage.py migrate

migrations:
	poetry run python3 manage.py makemigrations

superuser:
	poetry run python3 manage.py createsuperuser