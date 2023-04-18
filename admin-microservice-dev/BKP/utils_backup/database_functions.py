import gridfs,pymongo
from bson import ObjectId
from datetime import datetime, timedelta
from werkzeug.exceptions import BadRequest
from src.definitions.status_codes import ResponseStatus, RESPONSE_MSG_MAP
from src.definitions.status_codes import key_mapper, default_data


class DbFunctions:
    def __init__(self):
        pass

    @classmethod
    def update_one(cls, database, collection_name, query={}, fields={}, upsert=False,email=""):	
        fields.update({"updated_by":email,"updated_at":datetime.now()})
        database.get_collection(collection_name).update_one(query, {"$set": fields}, upsert=upsert)

    @classmethod
    def update_many(cls, database, collection_name, query={}, fields={}):
        database.get_collection(collection_name).update_many(query, {"$set": fields})

    @classmethod
    def insert_one(cls, database, collection_name, data,email=""):
        data.update({"createdby": email, "created_at": datetime.now()})
        object_id = (
            database.get_collection(collection_name).insert_one(data).inserted_id
        )
        return object_id

    @classmethod
    def insert_many(cls, database, collection_name, data):
        database.get_collection(collection_name).insert_many(data)

    @classmethod
    def delete_one(cls, database, collection_name, data, query={}):
        database.get_collection(collection_name).delete_one(data, query)

    @classmethod
    def find_all(cls, database, collection_name, data, query={}):
        data = {i: 1 for i in data}
        read_data = list(
            database.get_collection(collection_name).find(
                query, data, sort=[("_id", pymongo.DESCENDING)]
            )
        )
        for item in read_data:
            if isinstance(item, dict):
                item["_id"] = str(item["_id"])
        return read_data

    @classmethod
    def find_one(cls, database, collection_name, data, query={}):
        data = {i: 1 for i in data}
        data.update({"_id": 0})
        read_data = database.get_collection(collection_name).find_one(query, data) or {}
        return read_data

    @classmethod
    def update_inc(cls, database, collection_name, query={}, fields={}, upsert=False):
        database.get_collection(collection_name).update_one(
            query, {"$inc": fields}, upsert=upsert
        )

    @classmethod
    def push(cls, database, collection_name, query={}, fields={}, ip="", upsert=False):
        try:
            fields["history"].update({"ip_address": ip})
        except:
            pass
        database.get_collection(collection_name).update_one(
            query, {"$push": fields}, upsert=upsert
        )

    @classmethod
    def aggregate(cls, database, collection_name, pip):
        piplines = ["$match", "$unwind", "$match", "$project"]
        project = pip[3]
        data = {"_id": 0}
        for field in project:
            if "." in field:
                data.update({field.split(".")[-1]: field})
            else:
                data.update({field[1:]: 1})
        pip[3] = data
        pipline = [{val: pip[indx]} for indx, val in enumerate(piplines)]
        return list(database.get_collection(collection_name).aggregate(pipline))

    @classmethod
    def distinct(cls, database, collection_name, fields, query={}):
        return database.get_collection(collection_name).distinct(fields, query)

    @classmethod
    def latest_record(cls, database, collection_name, query={}):
        try:
            data = list(
                database.get_collection(collection_name)
                .find(query)
                .sort("_id", -1)
                .limit(1)
            )[0]
        except IndexError:
            data = {
                "email": query["email"],
                "attempt": 0,
                "valid_upto": datetime(1900, 1, 1),
                "status": False,
                "logged_in_once": False,
            }
            data["_id"] = cls.insert_one(
                database=database, collection_name=collection_name, data=data
            )
        return data

    @staticmethod
    def savefile(database, batch_file, filename):
        gridfs.GridFS(database, collection="CMS_FILE").put(
            batch_file, filename=filename
        )

    @classmethod
    def update_many_(
        cls, database, collection_name, queries=[], fields=[], upsert=False
    ):
        for num, query in enumerate(queries):
            database.get_collection(collection_name).update_one(
                query, {"$set": fields[num]}, upsert=upsert
            )


class RequestResponse:
	__slots__ = ["coll_name", "query", "db_name", "operation", "data", "fields", "pipeline", "response", "email",
	             "password", "res", "token", "logger_id", "ip_address","cifrado"]
	
	def __init__(self, request):
		self.response = ResponseStatus.Sucess
		self.res = default_data.NULL
		self.logger_id, self.email = default_data.STR, ""
		try:
			self.ip_address = request.remote_addr
		except AttributeError:
			pass
		self.attr_setter(request)
		try:
			if not self.email:
				self.email = self.query.get(key_mapper.EMAIL, "")
		except AttributeError:
			pass
		self.email = self.email.lower()
	
	def attr_setter(self, request):
		try:
			for key, val in request.args.items():
				setattr(self, key, val)
		except:
			pass
		try:
			try:
				request_json = request.get_json()
			except:
				request_json = request
			for key, val in request_json.items():
				if key == "query":
					if isinstance(val, list):
						for num, rec in enumerate(val):
							if rec.get("_id") is not None:
								val[num]["_id"] = ObjectId(rec.get("_id"))
					else:
						if val.get("_id") is not None:
							val["_id"] = ObjectId(val.get("_id"))
				setattr(self, key, val)
		except (BadRequest,AttributeError,TypeError):
			pass
	
	def to_dict(self):
		
		return {"msg": RESPONSE_MSG_MAP.get(self.response.name),
		        "res": self.res, "response_code": self.response.value,
		        "logger_id": self.logger_id}


class AttrDict(dict):
	
	def __getattr__(self, attr):
		return self.get(attr, "")
	
	def __setattr__(self, attr, value):
		self[attr] = value


def type_convertor(a):
	return str(a)


def time_convertor(time_obj, weeks=default_data.ZERO, minutes=default_data.ZERO, days=default_data.ZERO,
                   years=default_data.ZERO, hours=default_data.ZERO, months=default_data.ZERO,
                   seconds=default_data.ZERO):
	return time_obj + timedelta(
		minutes=minutes,
		days=days,
		seconds=seconds,
		hours=hours,
		weeks=weeks)



