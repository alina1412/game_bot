## game bot with FastApi and VK api

![bot_vk](https://github.com/user-attachments/assets/d19d9be1-2d9d-45c4-ad60-bef6717ed6a6)


### setup
- check file .python-version
- creating virtual environment or (`pyenv exec python -m venv .venv`), 
- .env
- `poetry install`
- `make up` (for docker)
- `make alembic`
- running using poetry and make: `make run`
- http://localhost:8000/docs/


### notes
enter docker container (why?):
`docker exec -it 47dece677d93  bash`

in host console:
`psql -h 127.0.0.1 -p 5433 -U user postgres -d kts_game`


### alembic:

`alembic init -t async migration`
`alembic revision --autogenerate -m 'initial'`


-edit files configs:

`sqlalchemy.url = postgresql+asyncpg://%(DB_USERNAME)s:%(DB_PASSWORD)s@%(DB_HOST)s:%(DB_PORT)s/%(DB_NAME)s`

--

