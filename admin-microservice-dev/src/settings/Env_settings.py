from datetime import datetime, timezone


class BaseConfig(object):
    DEBUG = True
    TESTING = False
    DATABASE_HOST = "15.184.161.217"
    DATABASE_PORT = 27022
    DATABASE = "pet_db"
    DATABASE_USERNAME = "Pet_fn"
    DATABASE_PASSWORD = "Pet@2023"
    DATABASE_AUTH = "admin"
    ENCRYPTED_KEY = "LoyaltyCaravanP1"
    ENCRYPTED_I_VECTOR = "UniversalQueryP1"
    ADMIN_USER = "USERS"
    ADMIN_LOGGER = "ADMIN_LOGGER"
    EVENTS_MASTER = "EVENTS_MASTER"
    CREATE = "create"
    SEND_EMAIL = "send_email"
    UPDATE = "update"
    DELETE = "delete"
    FETCH = "fetch"
    PUSH = "push"
    INC = "inc"
    AGGREGATE = "aggregate"
    UPDATE_MANY = "update_many"
    DISTINCT = "distinct"
    LOGIN_ATTEMPT = 5
    RESTRICT_ATTEMPT = 6
    RESTRICT_TIME = 15
    LOGIN = "login"
    UPDATE_PASSWORD = "update_password"
    JWT_SECRET = "THIS IS SECRET"
    DEFAULT_PASSWORD = "Loyalty@carvan"
    TIME_NOW = datetime.utcnow()
    API_TOKEN_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbiI6ImZseW5hdmFfbGNfdHJhdmVsX2FwcCIsIm9wZXJhdGlvbiI6ImF1dGhlbnRpY2F0aW9uIn0.MoOtq6gTikI63zm_7guiOwzbv2BN8Lv-Vq3qp_JyvqA"


class DevlopConfig(BaseConfig):
    DEBUG = True
    TESTING = False
    DATABASE_HOST = "15.207.8.28"
    DATABASE_PORT = 27017


class TestingConfig(BaseConfig):
    DEBUG = True
    TESTING = True
    DATABASE_HOST = "15.207.8.28"
    DATABASE_PORT = 27017


config_env = dict(development=DevlopConfig, testenv=TestingConfig, default=BaseConfig)
