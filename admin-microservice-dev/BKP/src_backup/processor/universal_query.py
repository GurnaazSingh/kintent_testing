from src.settings.flask_app import lc_travel_app
from src.definitions.status_codes import ResponseStatus
from utils.database_functions import DbFunctions


class ExecuteUniversal(DbFunctions):
    def __init__(self):
        super().__init__()
        self.res = None
        self.pipeline = None
        self.ip_address = None
        self.fields = None
        self.data = None
        self.query = None
        self.operation = None
        self.response = ResponseStatus.Sucess
        self.coll_name = None

    def operation_executor(self):
        if self.operation == lc_travel_app.CREATE:
            if not self.find_one(
                database=lc_travel_app.LC_db,
                collection_name=self.coll_name,
                data={},
                query=self.query,
            ):
                self.insert_one(
                    database=lc_travel_app.LC_db,
                    collection_name=self.coll_name,
                    data=self.data,
                    email=self.email,
                )
            else:
                self.response = ResponseStatus.Data_Exist
        elif self.operation == lc_travel_app.SEND_EMAIL:
            self.insert_one(
                database=lc_travel_app.LC_db,
                collection_name="EVENTS_MASTER",
                data=self.data,
            )
        elif self.operation == lc_travel_app.UPDATE:
            self.update_one(
                database=lc_travel_app.LC_db,
                collection_name=self.coll_name,
                query=self.query,
                fields=self.data,
                email=self.email,
            )

        elif self.operation == lc_travel_app.DELETE:
            self.update_one(
                database=lc_travel_app.LC_db,
                collection_name=self.coll_name,
                query=self.query,
                fields={"remove": True, "status": False},
            )

        elif self.operation == lc_travel_app.FETCH:
            self.res = self.find_all(
                database=lc_travel_app.LC_db,
                collection_name=self.coll_name,
                data=self.fields,
                query=self.query,
            )

        elif self.operation == lc_travel_app.INC:
            self.update_inc(
                database=lc_travel_app.LC_db,
                collection_name=self.coll_name,
                query=self.query,
                fields=self.fields,
            )

        elif self.operation == lc_travel_app.PUSH:
            self.push(
                database=lc_travel_app.LC_db,
                collection_name=self.coll_name,
                query=self.query,
                fields=self.fields,
                ip=self.ip_address,
            )

        elif self.operation == lc_travel_app.AGGREGATE:
            self.res = self.aggregate(
                database=lc_travel_app.LC_db,
                collection_name=self.coll_name,
                pip=self.pipeline,
            )

        elif self.operation == lc_travel_app.DISTINCT:
            self.res = self.distinct(
                database=lc_travel_app.LC_db,
                collection_name=self.coll_name,
                fields=self.fields,
                query=self.query,
            )

        elif self.operation == lc_travel_app.UPDATE_MANY:
            self.update_many(
                database=lc_travel_app.LC_db,
                collection_name=self.coll_name,
                query=self.query,
                fields=self.data,
            )
        else:
            self.response = ResponseStatus.Operation_not_allowed
