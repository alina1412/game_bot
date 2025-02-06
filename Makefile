run:
	poetry run python -m service
	
alembic_up = make alembic-up

ifdef OS
	docker_up = docker compose up -d
	docker_down = docker compose down --volumes
else
	docker_up = sudo docker-compose up -d
	docker_down = sudo docker-compose down
endif

up:
	$(docker_up) 

alembic:
	$(alembic_up)

down:
	$(docker_down)



renew-sync:
	poetry run alembic -c alembic_s.ini downgrade -1
	poetry run alembic -c alembic_s.ini upgrade head

test-sync:
	make renew-sync
	poetry run pytest -m my --verbosity=2 --showlocals --cov=service --cov-report html

renew-async:
	poetry run alembic -c alembic_as.ini downgrade -1
	poetry run alembic -c alembic_as.ini upgrade head

test-all:
	poetry run pytest -vsx --verbosity=2

alembic-gen:
	poetry run alembic -c alembic.ini revision --autogenerate -m "initial"

alembic-up:
	poetry run alembic -c alembic.ini upgrade head

alembic-down:
	poetry run alembic -c alembic.ini downgrade -1

lint:
	poetry run black service
	poetry run pylint service

isort:
	poetry run isort service tests

req:
	poetry export -f requirements.txt --without-hashes --without dev --output requirements.txt
