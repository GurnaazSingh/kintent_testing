from datetime import datetime
from src.settings.flask_app import lc_travel_app


class ADMIN_BUSINESS_RULES(object):
	def __init__(self):
		self.screen: str = ""
		self.applicable_for: str = ""
		self.type: list = []
		self.status = False
		self.service_type: str = ""
		self.promo_code: str = ""
		self.promo_code_type: str = ""
		self.min_value: float = 0.0
		self.max_value: float = 0.0
		self.percentage: int = 0
		self.fixed_amount: float = 0.0
		self.discount_value: str = ""
		self.customer_group: list = [
		
		]
		self.vendor: list = [
		
		]
		self.payment_mode: str = ""
		self.transaction_type: str = ""
		self.max_discount_limit: float = 0
		self.valid_from: str = ""
		self.valid_upto: str = ""
		self.airline: list = []
		self.flight_class: str = ""
		self.flight_no: str = ""
		self.pax_type: str = ""
		self.city: list = [
		
		]
		self.cab: list = [
		
		]
		self.hotel: list = [
		
		]
		self.room_type: list = [
		
		]
		self.no_of_rooms: list = [
		
		]
		self.description: str = ""
		self.remove = False
		self.last_updated = datetime.now()
		self.destination: list = [
		
		]


class ADMIN_LOGGER:
	def __init__(self):
		self.active:bool=False
		self.logger_id:str=""
		self.email: str = ""
		self.attempt: int = 0
		self.login_time: datetime.now()
		self.valid_upto: datetime.now()
		self.logger_id: str = ""
		self.ip_address: str = ""
		self.history: list = []
		self.status: False


class ADMIN_USER_GROUPS:
	def __init__(self):
		self.group: str = ""
		self.modules: list = []
		self.status: bool = True
		self.no_of_user: int = 0
		self.remove: bool = False


class ADMIN_USERS:
	def __init__(self):
		self.title: str = ""
		self.group: str = ""
		self.first_name: str = ""
		self.last_name: str = ""
		self.password:str=lc_travel_app.DEFAULT_PASSWORD
		self.email: str = ""
		self.status: bool = True
		self.remove: bool = False


class ADMIN_CMS:
	def __init__(self):
		self.group: str = ""
		self.processed: str = ""
		self.processed_data: list = []
		self.rejected: str = ""
		self.rejected_data: list = []
		self.total: str = ""

class ADMIN_SETTINGS:
	def __init__(self):
		self.service_type:str=""
		self.vendor: str=""
		self.type: str=""
		self.payment_method:str= ""
		self.charges: float=0.0
		self.rate_type: str= ""
		self.ctgst:float=0.0
		self.payment_gateway: str= ""
		self.stgst: float=0.0
		self.screen:str= ""
		self.updated_date: datetime.now()
db_struct = {
	"ADMIN_BUSINESS_RULES": ADMIN_BUSINESS_RULES().__dict__,
	"ADMIN_LOGGER": ADMIN_LOGGER().__dict__,
	"ADMIN_USER_GROUPS": ADMIN_USER_GROUPS().__dict__,
	"ADMIN_USERS": ADMIN_USERS().__dict__,
	"ADMIN_CMS": ADMIN_CMS().__dict__,
	"ADMIN_SETTINGS":ADMIN_SETTINGS().__dict__
}

