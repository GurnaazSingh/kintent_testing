from pymongo import MongoClient
from pprint import pprint

client = MongoClient("localhost:27017")
db = client["newpetdb"]

coll1 = db["pet_emp_master"]
coll2 = db["pet_opdata"]
coll3 = db["pet_mom_data"]

emp_det = list(coll1.find({"active": True}, {"_id": 0, "emp_id": 1, "emp_name": 1, "team": 1, "contract_type": 1}))
t_task_per_person = {}
comp_task_per_person = {}
a_item_completed = list(coll3.aggregate([
        {
            "$unwind":"$action_items"
        }
    ]))

for i in emp_det:
    t_task_count = coll2.find({"Assignee": i["emp_name"]}).count()
    c_task_count = coll2.find({"Assignee": i["emp_name"], "Status": "Done"}).count()
    comp_task_per_person.update({i["emp_name"]:c_task_count})
    t_task_per_person.update({i["emp_name"]: t_task_count})

print(t_task_per_person)
print(comp_task_per_person)
print("\n\n")
# pprint(a_item_completed[0])
x