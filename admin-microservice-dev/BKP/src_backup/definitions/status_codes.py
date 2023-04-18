from enum import Enum
from datetime import datetime

RESPONSE_MSG_MAP = {"maximum_attempts": "maximum no of attempts",
                    "User_already_logged_in": "user already logged in",
                    "Incorrect_password": "Incorrect password",
                    "incorrect_Username": "User does not exist",
                    "Invalid_email": "Invalid email",
                    "Old_new_pass": "Old password and new password should be different",
                    "Operation_not_allowed": "Operation Not ALlowed",
                    "password_does_not_match": "password does not match",
                    "Data_Exist": "data already exist!",
                    "Sucess": "success",
                    "Session_Expired": "session expired",
                    "IncorrectKey": "IncorrectKey",
                    "Invalid_link": "invalid_link",
                    "Incorrect_file_format": "Incorrect_file_format",
                    "inactive_user": "Your Account is Blocked.Please Contact Admin"
                    }


class ResponseStatus(Enum):
	default = 190
	Sucess = 200
	Data_Exist = 300
	Incorrect_password = 301
	incorrect_Username = 302
	Invalid_email = 303
	password_does_not_match = 304
	User_already_logged_in = 305
	Old_new_pass = 306
	Operation_not_allowed = 400
	Session_Expired = 401
	maximum_attempts = 402
	Incorrect_file_format = 405
	inactive_user = 408
	IncorrectKey = 409
	Invalid_link = 410


class KEYMAPPER:
	
	def __init__(self):
		self.EMAIL = "email"
		self.PASSWORD = "password"
		self.LOGGER_ID = "logger_id"
		self.ACTIVE = "status"
		self.REMOVE = "remove"
		self._ID = "_id"
		self.VALID_UPTO = "valid_upto"
		self.ATTEMPT = "attempt"
		self.TOKEN = "token"
		self.STATUS = "status"
		self.SUBJECT = "subject"
		self.LOGGED_IN = "logged_in_once"
		self.EXP = "exp"
		self.URL = "url"
		self.RESPONSE_CODE = "response_code"
		self.USED_PASSWORDS = "used_passwords"
		self.TOTAL = "total"
		self.FILENAME = "file_name"
		self.GROUP = "group"
		self.CRITERIA = "criteria"
		self.PROCESSED_DATA = "processed_data"
		self.REJECTION_REASON = "rejection_reason"
		self.REJECTED_DATA = "rejected_data"
		self.REJECTED = "rejected"
		self.PROCESSED = "processed"


class MONGODEFAULT:
	def __init__(self):
		self.EXISTS = "$exists"
		self.GROUP = "$group"
		self.EACH = "$each"
		self.AND = "$and"
		self.OR = "$or"
		self.PROJECT = "$project"
		self.MATCH = "$match"
		self.UNWIND = "$unwind"
		self.LTE = "$lte"
		self.GTE = "$gte"
		self.ADD_TO_SET = "$addToSet"
		self.EQUAL = "$eq"
		self.GT = "$gt"
		self.LT = "$lt"


class DEFAULTDATATYPES:
	
	def __init__(self):
		self.BOOL_FALSE = False
		self.BOOL_TRUE = True
		self.NOW_TIME = datetime.utcnow()
		self.ZERO = 0
		self.NULL = None
		self.STR = ""
		self.LIST = []
		self.DICT = {}


default_data = DEFAULTDATATYPES()
key_mapper = KEYMAPPER()
mongo_default = MONGODEFAULT()
