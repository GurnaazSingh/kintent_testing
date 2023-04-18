import pandas as pd
from flask import request, jsonify
from flask_restful import Resource
from src.processor.cms_process import CmsProcess
from src.settings.flask_app import lc_travel_app
from utils.database_functions import DbFunctions
from utils.session import build_cors_preflight_response
from src.definitions.status_codes import ResponseStatus, RESPONSE_MSG_MAP, key_mapper,mongo_default


class CMS(Resource,DbFunctions):


    def __init__(self):
        super().__init__()
        self.db_data = {}
        self.batch_file = request.files["file"]
        self.criteria = request.form[key_mapper.CRITERIA] or ""
        self.coll_name = request.form["coll_name"]
        self.group = request.form[key_mapper.GROUP]
        self.filename = self.batch_file.filename
        
      

    @staticmethod
    def options():
        return build_cors_preflight_response()

    def post(self):
        self.savefile(database=lc_travel_app.LC_db,batch_file=self.batch_file, filename=self.filename)
        df = pd.read_excel(self.batch_file)
        if not CmsProcess.excel_validation_check(self.criteria,df):
            return jsonify(response_code=ResponseStatus.Incorrect_file_format.value,res={},msg=RESPONSE_MSG_MAP.get(ResponseStatus.Incorrect_file_format.name))
        df.columns=[self.criteria]
        self.db_data[key_mapper.TOTAL] = len(df)
        self.db_data[key_mapper.FILENAME]=self.filename
        previous_data=self.find_one(database=lc_travel_app.LC_db,collection_name=self.coll_name,data=[],query={key_mapper.GROUP:self.group,key_mapper.CRITERIA:self.criteria}) or {}
        processed_df=pd.DataFrame(previous_data.get(key_mapper.PROCESSED_DATA,[]))
        self.db_data=CmsProcess.drop_dupli(df=df, processed_df=processed_df, db_data=self.db_data, criteria=self.criteria, group=self.group)
        self.update_one(database=lc_travel_app.LC_db,collection_name=self.coll_name, query={key_mapper.GROUP: self.group,key_mapper.CRITERIA:self.criteria},fields={key_mapper.PROCESSED_DATA:self.db_data[key_mapper.PROCESSED_DATA]}, upsert=True)
        self.push(database=lc_travel_app.LC_db,collection_name=self.coll_name,query={key_mapper.GROUP: self.group,key_mapper.CRITERIA:self.criteria},fields={key_mapper.REJECTED_DATA:{mongo_default.EACH:self.db_data[key_mapper.REJECTED_DATA]},key_mapper.FILENAME:self.filename},upsert=True)
        self.update_inc(database=lc_travel_app.LC_db,collection_name=self.coll_name,query={key_mapper.GROUP: self.group,key_mapper.CRITERIA:self.criteria},fields={key_mapper.PROCESSED:self.db_data[key_mapper.PROCESSED],key_mapper.REJECTED:self.db_data[key_mapper.REJECTED],key_mapper.TOTAL:self.db_data[key_mapper.TOTAL]},upsert=True)
        res={key_mapper.TOTAL:self.db_data[key_mapper.TOTAL],key_mapper.REJECTED:self.db_data[key_mapper.REJECTED],key_mapper.PROCESSED:self.db_data[key_mapper.PROCESSED]}
        return jsonify({"msg": RESPONSE_MSG_MAP.get(ResponseStatus.Sucess.name), "res": res, key_mapper.RESPONSE_CODE: ResponseStatus.Sucess.value})
