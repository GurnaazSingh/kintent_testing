from flask import request
from flask_restful import Resource
from src.settings.flask_app import lc_travel_app
from src.processor.authentication import UserChecks
from src.definitions.status_codes import ResponseStatus
from src.processor.universal_query import ExecuteUniversal
from utils.session import build_cors_preflight_response
from utils.database_functions import RequestResponse
from utils.api_encryption import ApiEncryption


class ApiQuery(Resource, RequestResponse, ExecuteUniversal):
    def __init__(self):
        super().__init__(request=request)
        self.user_record = None
        self.logger_id = None
        self.decrypt_request = ApiEncryption(
            i_vector=lc_travel_app.ENCRYPTED_I_VECTOR,
            enc_key=lc_travel_app.ENCRYPTED_KEY,
        )

    @staticmethod
    def options():
        return build_cors_preflight_response()

    def post(self):
        # self.attr_setter(
        #     self.decrypt_request.get_decrypt(encrypted_request=self.cifrado)
        # )
        #self.user_record = UserChecks(email=self.email, password="")
        #if not self.user_record.user_rec:
        #    self.response = ResponseStatus.Session_Expired
        #else:
        self.operation_executor()
        return self.to_dict()
