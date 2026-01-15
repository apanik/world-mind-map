.PHONY: dev migrate seed test

dev:
	docker-compose up --build

migrate:
	docker-compose run --rm web python manage.py migrate

seed:
	docker-compose run --rm web python manage.py seed_countries

test:
	pytest
