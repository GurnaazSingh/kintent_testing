import jwt
from argon2 import PasswordHasher
from datetime import datetime, timedelta
from src.settings.flask_app import lc_travel_app
from argon2.exceptions import InvalidHash, VerifyMismatchError
from utils.database_functions import DbFunctions, AttrDict, time_convertor, type_convertor
from src.definitions.status_codes import ResponseStatus, default_data, key_mapper, mongo_default


class UserChecks(DbFunctions):
	
	def __init__(self, email, password):
		super().__init__()
		self.passwords_used = None
		self.res = None
		self.passwords = None
		self.login_rec = None
		self.response_code = ResponseStatus.default
		self.password = password
		self.email = email
		self.response = ResponseStatus.default
		self.update_dict = default_data.DICT
		self.logger_id = default_data.STR
		self.reset_flag = default_data.BOOL_FALSE
		# creating the email attribute with the given email
		self.user_rec = self.find_one(database=lc_travel_app.LC_db, collection_name=lc_travel_app.ADMIN_USER,
		                              data=default_data.LIST, query={key_mapper.EMAIL: self.email,key_mapper.REMOVE: default_data.BOOL_FALSE})
	

	
	@property
	def hashpass(self):
		hashedpass = PasswordHasher().hash(self.password)
		return hashedpass
	
	@property
	def encode_token(self):
		email_token = jwt.encode({"email": self.email, "exp": datetime.utcnow() + timedelta(minutes=30)},
		                         lc_travel_app.JWT_SECRET)
		return email_token
	
	@staticmethod
	def decode_token(token):
		return jwt.decode(token, lc_travel_app.JWT_SECRET, algorithms="HS256")
	
	
	def _get_latest_record(self):
		self.login_rec = AttrDict(self.latest_record(database=lc_travel_app.LC_db,
		                                             collection_name=lc_travel_app.ADMIN_LOGGER,
		                                             query={key_mapper.EMAIL: self.email,
		                                                    key_mapper.SUBJECT: {
			                                                    mongo_default.EXISTS: default_data.BOOL_FALSE}}))
	

	
	def _login_checks(self):
		if self.login_rec.attempt == lc_travel_app.LOGIN_ATTEMPT and self.login_rec.valid_upto < datetime.utcnow():
			self.update_one(database=lc_travel_app.LC_db, collection_name=lc_travel_app.ADMIN_LOGGER,
			                query={key_mapper.EMAIL: self.email, key_mapper._ID: self.login_rec._id},
			                fields={key_mapper.VALID_UPTO: time_convertor(datetime.utcnow(),
			                                                              minutes=lc_travel_app.RESTRICT_TIME),
			                        key_mapper.ATTEMPT: lc_travel_app.RESTRICT_ATTEMPT})
			self.response = ResponseStatus.maximum_attempts
		
		elif self.login_rec.valid_upto > datetime.utcnow() and self.login_rec.attempt > lc_travel_app.LOGIN_ATTEMPT:
			self.update_one(database=lc_travel_app.LC_db, collection_name=lc_travel_app.ADMIN_LOGGER,
			                query={key_mapper.EMAIL: self.email, key_mapper._ID: self.login_rec._id})
			self.response = ResponseStatus.maximum_attempts
		
		elif self.login_rec.valid_upto < datetime.utcnow():
			if self.login_rec.attempt > lc_travel_app.LOGIN_ATTEMPT:
				self.update_one(database=lc_travel_app.LC_db, collection_name=lc_travel_app.ADMIN_LOGGER,
				                query={key_mapper.EMAIL: self.email, key_mapper._ID: self.login_rec._id},
				                fields={key_mapper.VALID_UPTO: time_convertor(datetime.utcnow(),
				                                                              minutes=lc_travel_app.RESTRICT_TIME),
				                        key_mapper.ATTEMPT: 0})
			
			if self.user_rec.get(key_mapper.STATUS):
				if self.pass_checker() and self.login_rec.valid_upto < datetime.utcnow():
					self.response = ResponseStatus.Sucess
					self.logger_id = type_convertor(self.login_rec._id)
					self.update_one(database=lc_travel_app.LC_db, collection_name=lc_travel_app.ADMIN_LOGGER,
					                query={key_mapper.EMAIL: self.email, key_mapper._ID: self.login_rec._id},
					                fields={key_mapper.ATTEMPT: 0, key_mapper.LOGGER_ID: self.logger_id,
					                        key_mapper.ACTIVE: default_data.BOOL_TRUE})
					self.res = self.encode_token
				else:
					self.update_inc(database=lc_travel_app.LC_db, collection_name=lc_travel_app.ADMIN_LOGGER,
					                query={key_mapper.EMAIL: self.email, key_mapper._ID: self.login_rec._id},
					                fields={key_mapper.ATTEMPT: 1})
					self.response = ResponseStatus.Incorrect_password
			elif not self.user_rec.get(key_mapper.STATUS):
				self.response = ResponseStatus.inactive_user
			else:
				self.response = ResponseStatus.incorrect_Username

	
	def pass_checker(self):
		# if the operation is not reset then taking only the current password
		if not self.reset_flag:
			self.passwords = [self.user_rec.get(key_mapper.PASSWORD)]
		# if the operation is reset taking all the old password
		if self.reset_flag:
			self.passwords = self.user_rec.get(key_mapper.USED_PASSWORDS,[])
		# checking if any of the password matching with the entered password
		for password in self.passwords:
			try:
				return PasswordHasher().verify(password, self.password)
			except (InvalidHash,VerifyMismatchError) as e:
				raise  	e
				continue
		return False
	
	def old_new_pass_checker(self):
		
		self.reset_flag = True
		flag = self.pass_checker()
		if flag:
			self.response = ResponseStatus.Old_new_pass
			return True
		else:
			return False
		
		
	def execute_login(self):
		self._get_latest_record()
		# if self.login_rec.status:
		# 	self.response = ResponseStatus.User_already_logged_in
		# else:
		self._login_checks()
			
			
		
	
	def password_updater(self):
		# inserting the password entered into the used password list
		self.passwords_used = self.user_rec.get(key_mapper.USED_PASSWORDS, [])
		self.passwords_used.append(self.password)
		self.update_one(database=lc_travel_app.LC_db,collection_name=lc_travel_app.ADMIN_USER,query={key_mapper.EMAIL: self.email},fields={key_mapper.PASSWORD: PasswordHasher().hash(self.password),key_mapper.USED_PASSWORDS: self.passwords_used})
		self.update_one(database=lc_travel_app.LC_db,collection_name=lc_travel_app.EVENTS_MASTER,query={"_id": self.login_rec.get("_id")},fields={"status": False})
		self.response = ResponseStatus.Sucess
