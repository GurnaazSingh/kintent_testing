from flask import request
#from jwt import InvalidTokenError
from flask_restful import Resource
from src.settings.flask_app import lc_travel_app
from src.processor.authentication import UserChecks
from src.definitions.status_codes import ResponseStatus
from utils.session import build_cors_preflight_response
from utils.database_functions import DbFunctions, AttrDict, RequestResponse


class Login(Resource, RequestResponse):

    def __init__(self):
        super().__init__(request=request)
        self.update_link_rec = None

    @staticmethod
    def options():
        return build_cors_preflight_response()

    def get(self):
        self.attr_setter(UserChecks.decode_token(self.token))
        user_obj = UserChecks(email=self.email, password=self.password)
        if self.operation == lc_travel_app.LOGIN:
            user_obj.execute_login()
        elif self.operation == lc_travel_app.UPDATE_PASSWORD:
            try:
                self.update_link_rec = AttrDict(
                    DbFunctions.latest_record(database=lc_travel_app.LC_db, collection_name=lc_travel_app.EVENTS_MASTER,
                                              query={"url": self.token}))
                if not user_obj.old_new_pass_checker():
                    user_obj.password_updater()
            except Exception as e:
                self.response = ResponseStatus.Invalid_link
        self.logger_id, self.res, self.response = user_obj.logger_id, user_obj.res, user_obj.response
        # for i in range(100):
            # print(self.logger_id, self.res, self.response)

        DbFunctions.insert_one(database=lc_travel_app.LC_db, collection_name=lc_travel_app.EVENTS_MASTER,
                                  data=self.to_dict())
        
        print("hi")
        return self.to_dict()