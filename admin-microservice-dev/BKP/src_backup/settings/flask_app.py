import os
import sys
import traceback
import datetime
from time import strftime
from flask_cors import CORS
from flask import Flask, request, abort, g, after_this_request
from src.settings.api_routes import Routes
from src.settings.app import get_mongo_db, Singleton, log
from src.settings.Env_settings import config_env


def before_request():
    if request.method != "OPTIONS":
        if not request.headers.get("Authorization") == lc_travel_app.API_TOKEN_KEY:
            print(request.headers.get("Authorization"))
            #abort(401, "Authorization failed")
    log.info(request)
    try:
        log.info(request.json)
    except:
        pass
    try:
        log.info(request.args)
    except:
        pass
    try:
        log.info(request.form)
    except:
        pass

    @after_this_request
    def generate_session_cookies(response):
        response.headers["name"] = "Ateesh"
        response.set_cookie("access", lc_travel_app.API_TOKEN_KEY, httponly=True)

        return response


def after_request(response):
    ts = strftime("[%Y-%b-%d %H:%M]")
    # logger=logging.getLogger("LC_travel_app")
    # log.info(f"{ts} {request.remote_addr} {request.method} {request.scheme} {request.full_path} {response.status_code}")
    for callback in getattr(g, "after_request_callbacks", ()):
        callback(response)
    return response


class LC_TRAVEL(metaclass=Singleton):
    def __init__(self):
        env_detail = config_env.get(os.getenv("LC_ENV", "default").lower())
        for key in dir(env_detail):
            if key.isupper():
                setattr(self, key, getattr(env_detail, key))
        self.app = self.initialize_lc_app()
        self.api = self.initialize_lc_api()

    def initialize_lc_app(self):
        app = Flask(__name__)
        CORS(app)
        app.config.from_object(config_env[os.getenv("LC_ENV", "default").lower()])
        app.secret_key = os.urandom(20)
        app.before_request(before_request)
        app.after_request(after_request)
        return app

    def initialize_lc_api(self):
        from flask_restful import Api

        return Api(self.app)

    @property
    def LC_db(self):
        return get_mongo_db().db


lc_travel_app = LC_TRAVEL()
api = lc_travel_app.api


@lc_travel_app.app.teardown_request
def internal_server_error(exc):
    if not exc:
        return
    exc_type, exc_value, exc_tb = sys.exc_info()
    tb = traceback.TracebackException(exc_type, exc_value, exc_tb)
    file = str(tb.stack)
    list_of_errors = "".join(tb.format_exception_only())
    print("".join(tb.format_exception_only()))
    try:
        lc_travel_app.LC_db.get_collection("error_logs").insert_one(
            {
                "request": request.json,
                "logger_id": request.args.get("logger_id"),
                "time": datetime.datetime.now(),
                "error": list_of_errors,
                "file": file,
                "endpoint": request.endpoint,
            }
        )
    except Exception as e:
        pass

Routes(api)
