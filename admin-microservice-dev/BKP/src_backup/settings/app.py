import os
import logging
from src.settings.app_log import set_loggers
from src.settings.Env_settings import config_env

set_loggers()
log = logging.getLogger("LC_travel_app")


class Singleton(type):
    _instance = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instance:
            cls._instance[cls] = super().__call__(*args, **kwargs)
        return cls._instance[cls]


class AppMongo(metaclass=Singleton):
    def __init__(self):
        log.info("Database Connection Started")
        env_detail = config_env.get(os.getenv('LC_ENV', 'default').lower())
        host = getattr(env_detail, "DATABASE_HOST")
        port = getattr(env_detail, "DATABASE_PORT")
        db_name = getattr(env_detail, "DATABASE")
        from pymongo import MongoClient
        self.cx =MongoClient(
            "15.207.8.28:27022",
            username='Pet_fn',
            password='Pet@2023',
            authSource='admin',
            authMechanism="SCRAM-SHA-1"
        )
        self.db = self.cx[db_name]


def get_mongo_db():
    return AppMongo()



