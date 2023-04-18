# This file contains all the required __db connections and the collections for the project

from pymongo import MongoClient


class Cred:
    def __init__(self):
        self.__ek_client= MongoClient(
            host='18.179.220.40',
            port=27022,
            username='ViRusFevEr',
            password='coRoNaviRus2020@2021',
            authSource='admin',
            authMechanism="SCRAM-SHA-1"
        )
        self.__fz_client = MongoClient(
            '15.185.110.99:27012',
            username='flynava',
            password='flynava123',
            authSource='admin'
        )
        self.__pet_client = MongoClient(
                "15.184.161.217:27022",
                username='Pet_fn',
                password='Pet@2023',
                authSource='admin',
                authMechanism="SCRAM-SHA-1"
            )
        self.__local_client = MongoClient(
            "localhost:27017"
        )
        # self.__asmi_client = MongoClient(
        #     '65.1.61.233:27022',
        #     username='flynava',
        #     password='flynava123',
        #     authSource='admin'
        # )

        self.__local_db = self.__local_client["PET"]
        self.__pet_db = self.__pet_client["pet_db"]

        self.__op_data_coll = self.__pet_db["OP_DATA"]
        self.__milestone_coll = self.__pet_db["MILESTONE_SCREEN"]
        self.__drop_coll = self.__pet_db["DROPDOWN"]
        self.__mom_coll = self.__pet_db["MOM_SCREEN"]
        self.__workflow = self.__pet_db["WORKFORCE_SCREEN"]
        self.__emp_det_new = self.__pet_db["EMPLOYEE_MASTER_NEW"]
        self.__emp_det = self.__pet_db["EMPLOYEES_MASTER"]
        self.__uc_events = self.__pet_db["CALENDER"]
        self.__manage = self.__pet_db["MGMT_SCREEN"]
        self.__local_workflow = self.__local_db["pet_workflow"]
        self.__local_op_data_coll = self.__local_db["pet_op_data"]
        self.__local_mom_coll = self.__local_db["pet_mom_data"]
        self.__local_milestone_admin_coll = self.__local_db["pet_milestone_admin"]
        self.__local_emp_det_coll = self.__local_db["pet_emp_master"]
        self.__hiring = self.__pet_db['HIRING_DATA']
        self.__attendance = self.__pet_db["ATTENDANCE"]
        self.__fc_data = self.__pet_db["FINANCIAL_DATA"]
        self.__ff_data = self.__pet_db["FINANCIAL_FIELDS"]
        self.__fk_data = self.__pet_db["FINANCIAL_KPI_DATA"]
        self.__sd_data = self.__pet_db["STARTUP_DATA"]
        self.__sf_data = self.__pet_db["STARTUP_FIELDS"]
        self.__md_data = self.__pet_db["MARKETING_DATA"]
        self.__mf_data = self.__pet_db["MARKETING_FIELDS"]

        self.__db_return = {
            "l_mom": self.__local_mom_coll,
            "l_mile": self.__local_milestone_admin_coll,
            "l_emp": self.__local_emp_det_coll,
            "l_workflow": self.__local_workflow,
            "l_op": self.__local_op_data_coll,
            "mom": self.__mom_coll,
            "dropdown": self.__drop_coll,
            "mile": self.__milestone_coll,
            "op_data": self.__op_data_coll,
            "workflow": self.__workflow,
            "emp_det": self.__emp_det,
            "emp_det_new": self.__emp_det_new,
            "uc": self.__uc_events,
            "attendance": self.__attendance,
            "hiring": self.__hiring,
            "fc": self.__fc_data,
            "ff": self.__ff_data,
            "sf": self.__sf_data,
            "sd": self.__sd_data,
            "md": self.__md_data,
            "mf": self.__mf_data,
            "fk": self.__fk_data,
        }

    def sort(self, key=None):
        # if key == "mom":
        #     return self.__mom_coll
        # elif key == "l_mom":
        #     return self.__local_mom_coll
        # elif key == "l_mile":
        #     return self.__local_milestone_admin_coll
        # elif key == "l_drop":
        #     return self.__local_emp_det_coll
        # elif key in ["dd", "drop", "dropdown"]:
        #     return self.__drop_coll
        # elif key in ["mile", "milestone", "milestone_admin", "milestone_administrator", "m_admin"]:
        #     return self.__milestone_coll

        if key in self.__db_return.keys():
            return self.__db_return[key]
        else:
            return False
