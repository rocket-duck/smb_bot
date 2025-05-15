install:
	poetry install

build:
	poetry build

bot-run:
	poetry run bot

lint:
	poetry run flake8 bot
