from src.settings import conf
from datetime import datetime


class DataUpDown:  # Class created to access the database to insert update search from __db
    def __init__(self):
        self.__where = conf.Cred()

    def __find(self, s_data, where_to=None, sor=None, lim=None, count=None, skp=None):
        query = s_data[0]
        data = s_data[1]
        if sor and lim and count is not None:
            return where_to.find(query, data).sort(sor[0], sor[1]).limit(lim).count()
        elif sor and lim is not None:
            return where_to.find(query, data).sort(sor[0], sor[1]).limit(lim)
        elif lim and skp and sor is not None:
            return where_to.find(query, data).limit(lim).skip(skp).sort(sor)
        elif lim and count is not None:
            return where_to.find(query, data).limit(lim).count()
        elif sor and count is not None:
            return where_to.find(query, data).sort(sor).count()
        elif lim is not None:
            return where_to.find(query, data).limit(lim)
        elif sor is not None:
            return where_to.find(query, data).sort(sor)
        elif count is not None:
            return where_to.find(query, data).count()
        else:
            return where_to.find(query, data)

    def __insert(self, insert_data, where_to=None):
        if isinstance(insert_data, dict):
            return where_to.insert_one(insert_data)

        elif isinstance(insert_data, list):
            return where_to.insert_many(insert_data)

        else:
            raise NotADirectoryError

    def __update(self, s_data, update_data, where_to=None):
        if isinstance(s_data, dict) and isinstance(update_data, dict):
            return where_to.update_one(s_data, update_data)

    def manage(self, method, key=None, s_data=dict, input_data=dict, sort=None, limit=None, count=None, skip_val=None):
        where_to = self.__where.sort(key=key)
        if method == "insert":
            self.__insert(insert_data=input_data, where_to=where_to)
        elif method == "update":
            self.__update(s_data, input_data, where_to=where_to)
        elif method in ["search", "find"]:
            # drop_d = []
            drop_down = self.__find(s_data=s_data, where_to=where_to, lim=limit, sor=sort, count=count, skp=skip_val)
            return list(drop_down)
        else:
            print("Enter again")
