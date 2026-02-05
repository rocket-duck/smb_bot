install:
	poetry install

build:
	poetry build

bot-run:
	poetry run bot

lint:
	poetry run ruff check bot tests
	poetry run black --check bot tests

format:
	poetry run ruff check --fix bot tests
	poetry run black bot tests
