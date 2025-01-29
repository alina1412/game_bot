import logging
from os import environ

from dotenv import load_dotenv

load_dotenv()

DEBUG = environ.get("DEBUG", None)

db_settings = {
    "db_name": environ.get("DB_NAME"),
    "db_host": environ.get("DB_HOST"),
    "db_user": environ.get("DB_USERNAME"),
    "db_port": environ.get("DB_PORT"),
    "db_password": environ.get("DB_PASSWORD"),
    "db_driver": environ.get("DB_DRIVER"),
}

logging.basicConfig(
    filename=("logs.log" if DEBUG else None),
    level=(logging.INFO if DEBUG else logging.WARNING),
    format=(
        "[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
    ),
    datefmt=("%H:%M:%S" if DEBUG else "%Y-%m-%d %H:%M:%S"),
)
logger = logging.getLogger(__name__)
