import os
from dotenv import load_dotenv
load_dotenv()
from alembic import context
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from src.news_assistant.models import Base

config = context.config
fileConfig(config.config_file_name)
config.set_main_option("sqlalchemy.url", os.getenv("DB_URI"))
target_metadata = Base.metadata

from src.news_assistant.models import Base

target_metadata = Base.metadata 