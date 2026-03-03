## VK Game Bot 🎮 (with FastApi and VK api)
A game bot for VK chat built with FastAPI and VK API.

This bot integrates with VK chat for gameplay, uses RabbitMQ for message queuing and PostgreSQL for data storage.

It requires token for vk bot in config.yml.

### Stack
- Core: Python, FastAPI, VK API
- Database: PostgreSQL, SQLAlchemy, Alembic
- Infrastructure: Docker, RabbitMQ
- Tools: Poetry, pytest, make

### Quick Start
Prerequisites
- Python 3.10.x (see .python-version)
- Docker
- Poetry (optional)
  
![bot_vk](https://github.com/user-attachments/assets/d19d9be1-2d9d-45c4-ad60-bef6717ed6a6)


### Setup
- check file .python-version
- creating virtual environment or (`pyenv exec python -m venv .venv`), 
- `cp .env.example .env`  # Configure your variables
- `cp config_example.yml config.yml` # Configure your variables
- `poetry install`
- `make up` # Starts PostgreSQL and RabbitMQ in docker
- `make alembic`
- running using poetry and make: `make run`
- Access API docs: http://localhost:8000/docs/


### notes
enter docker container (example):
`docker exec -it 47dece677d93  bash`

in host console:
`psql -h 127.0.0.1 -p 5433 -U user postgres -d db_game`


### alembic:

`alembic init -t async migration`
`alembic revision --autogenerate -m 'initial'`

edit files configs:
`sqlalchemy.url = postgresql+asyncpg://%(DB_USERNAME)s:%(DB_PASSWORD)s@%(DB_HOST)s:%(DB_PORT)s/%(DB_NAME)s`


