import copy
import re
from flask import Flask, request, jsonify, make_response, abort, send_file
from flask_cors import CORS
import src.util.db as db
import pandas as pd
import datetime
import numpy as np
from collections import Counter

UPLOAD_FOLDER = "files1/"

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def _build_cors_prelight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response


def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@app.route("/mom_management", methods=['POST', 'OPTIONS'])
def calc_data():
    if request.method == 'OPTIONS':
        # print('options method call')
        return _build_cors_prelight_response()
    if request.method == "POST":
        db_access = db.DataUpDown()
        payload = request.json
        key = payload["key"]
        payload.pop("key")

        def action_percent(action_items):
            act_item = pd.DataFrame(action_items)
            count = round_off((len(act_item.loc[act_item["remove"] == True]) / len(act_item)) * 100)
            return count

        if payload["method"] == "insert":

            check = db_access.manage(method="find",
                                     key=key,
                                     s_data=[{"project_name": payload["project_name"],
                                              # "prepared_by": payload["prepared_by"],
                                              },
                                             {"mom_name": 1, "_id": 0}],
                                     sort=("_id", -1), limit=1)
            # check = list(coll.find({"project_name": payload["project_name"]},
            #                        {"mom_name": 1, "_id": 0}).sort(("_id", -1)).limit(1))
            if check:
                mom_name = check[0]["mom_name"]
                project_seq_no = str(int(mom_name.split("_")[1]) + 1)
            else:
                project_seq_no = "1"

            action_perc = action_percent(payload['action_items'])
            db_data = {
                "prepared_by": payload['prepared_by'],
                "meeting_date": payload['meeting_date'],
                "project_name": payload['project_name'],
                "mom_name": payload['project_name'] + '_00' + project_seq_no + '_' + payload['meeting_date'],
                "attendees": payload['attendees'],
                "agenda": payload['agenda'],
                "discussion_points": payload['discussion'],
                "action_items": payload['action_items'],
                "action_percentage": round_off(action_perc),
                "remove": False,
                "documented_date": payload["documented_date"],
                "meeting_time": payload["meeting_time"]
            }
            db_access.manage(payload["method"], key=key, input_data=db_data)
            # coll.insert_one(db_data)
            return _corsify_actual_response(jsonify({"msg": "data inserted successfully"}))

        elif payload["method"] == "update":
            if payload["data"].get("action_items"):
                action_perc = action_percent(payload["data"].get("action_items"))
                payload["data"].update({"action_percentage": action_perc})

            s_d = {"mom_name": payload["mom_name"]}
            u_d = {"$set": payload["data"]}
            db_access.manage(method=payload["method"], key=key, s_data=s_d, input_data=u_d)
            # coll.update_one(s_d, u_d)

            return _corsify_actual_response(jsonify({"msg": "data updated successfully"}))

        elif payload["method"] == "find":
            s_data = ({}, {"_id": 0})
            mom_data = db_access.manage(method=payload["method"], key=key, s_data=s_data)
            return _corsify_actual_response(jsonify(mom_data))
        else:
            return _corsify_actual_response(jsonify({"msg": "Enter correct method"}))


@app.route("/dropdown", methods=['OPTIONS', 'GET'])
def dd_api():
    if request.method == 'OPTIONS':
        # print('options method call')
        return _build_cors_prelight_response()
    if request.method == "GET":
        db_access = db.DataUpDown()

        team_data = db_access.manage(method="find", key="emp_det", s_data=({}, {"team": 1, "emp_name": 1,"emp_id":1, "_id": 0}))
        event_data = db_access.manage(method="find", key="uc", s_data=({}, {"_id": 0}))
        year = db_access.manage(method="find", key="dropdown", s_data=({}, {"_id": 0}))[0]
        month = db_access.manage(method="find", key="dropdown", s_data=({}, {"_id": 0}))[1]
        # team = db_access.manage(method="find", key="dropdown", s_data=({}, {"_id": 0}))[2]
        status = db_access.manage(method="find", key="dropdown", s_data=({}, {"_id": 0}))[3]
        project_data = db_access.manage(method="find", key="op_data", s_data=({}, {"_id": 0, "Project": 1}))
        project_data = pd.DataFrame(project_data).drop_duplicates()["Project"].to_list()
        data = pd.DataFrame(team_data).groupby("team")['emp_name'].apply(list).to_dict()
        teams_data = list(pd.DataFrame(team_data)['team'].drop_duplicates(inplace=False))
        final_dict = {"teams": teams_data, "event_data": event_data, "year": year["values"], "month": month["values"],
                      "status": status["values"], "projects": project_data}
        employee_data = pd.DataFrame(team_data).groupby("emp_id")['emp_name'].apply(list).to_dict()
        emp_data = list()
        for i in employee_data:
            emp_data.append({"emp_id":i, "emp_name": employee_data[i][0]})

        final_dict.update(data)
        final_dict.update({"emp_details": emp_data})

        return _corsify_actual_response(jsonify(final_dict))


@app.get("/report")
def report_data():
    if request.method == 'OPTIONS':
        # print('options method call')
        return _build_cors_prelight_response()
    if request.method == "GET":
        db_access = db.DataUpDown()

        data = db_access.manage(method="find", key="op_data", s_data=({}, {"_id": 0}))

        return {"report_data": [data]}


# @app.get("/milestone_admin")
# def milestone_data():
#     db_access = db.DataUpDown()
#     payload = request.json
#     key = payload["key"]
#     method = payload["method"]
#     if payload["method"] == "insert":
#         payload.pop("key")
#         payload.pop("method")
#         db_access.manage(method=method, key=key, input_data=payload)
#
#         return _corsify_actual_response(jsonify({"msg": "Insertion done"}))
#
#     elif payload["method"] == "find":
#         data = db_access.manage(method=method, key=key, s_data=({},{"_id":0}))
#         return data
#     elif payload["method"] == "update":
#         db_access = db.DataUpDown()
#         payload = request.json

def summer(dataf_, key, cols, col_to_sum):
    total = 0
    features_built = {}
    df_feature = list(dataf_[key].unique())
    if not cols:
        cols = df_feature
    for i in df_feature:
        if i and (i in cols):
            data = dataf_[dataf_[key] == i]
            if col_to_sum:
                data = int(data[col_to_sum].sum())
            else:
                data = data.shape[0]
            features_built[i] = data
            # total += data

    # features_built.update({i + "_per": round_off((features_built[i] / total) * 100) for i in features_built})
    # features_built['total'] = int(total)
    return features_built


def to_dictionary(list_, key1, key2):
    return {i[key1]: i[key2] for i in list_}


def round_off(data):
    return round(data, 2)


def dict_update_ele(name, value, final_dict):
    return final_dict.update({name: value})


def time_diff(a, b):
    return (b - a).days


def modularize_df(new_df, value1, value2):
    return to_dictionary(new_df.groupby(by=[value1])[value2].apply(list).reset_index().to_dict("records"),
                         value1, value2)


def effectivity(ov_eff_, projects):
    return_dict = {}
    for project in projects:
        if project:
            ov_eff = ov_eff_[ov_eff_['Project'] == project]
        else:
            project = "value"
            ov_eff = ov_eff_
        ov_eff_time_taken = ov_eff['time_taken'].sum()
        ov_eff_time_to_be_taken = ov_eff['time_to_be_taken'].sum()
        if ov_eff_time_taken <= ov_eff_time_to_be_taken:
            ov_effi = (((ov_eff_time_to_be_taken - ov_eff_time_taken) / ov_eff_time_to_be_taken) * 100) + 100
        else:
            ov_effi = 100 - (((ov_eff_time_taken - ov_eff_time_to_be_taken) / ov_eff_time_taken) * 100)

        return_dict[project.lower().replace(" ", "_")] = round_off(ov_effi)

    return return_dict


def actual_func(query, db_access):
    final_dict = {}
    df, df1, df2 = pd.DataFrame(
        db_access.manage(method="find", key="op_data", s_data=({"Due_date": query}, {"_id": 0}))), \
                   pd.DataFrame(
                       db_access.manage(method="find", key="mile", s_data=({"due_date": query}, {"_id": 0}))), \
                   pd.DataFrame(
                       db_access.manage(method="find", key="mom", s_data=({"documented_date": query}, {"_id": 0})))

    # overall_productity
    # print(df.shape)
    oa_pro = df[df['Status'] == "Done"].shape[0] / sum(list(df[df['Status'] == "Done"]['Spent_time']))
    oa_pro_project = modularize_df(df[df['Status'] == 'Done'], "Project", "Spent_time")
    oa_pro_project = {key: len(oa_pro_project[key]) / sum(oa_pro_project[key]) for key in oa_pro_project}
    oa_pro_project.update({"value": oa_pro})
    dict_update_ele("overall_productivity", oa_pro_project, final_dict)

    # avg_spent_timex
    avg_df = df[(df['Status'] == 'Done') & (df['Type'] == "Feature")]
    avg_spent_time = summer(avg_df, "Feature_type", [], "Spent_time")
    # avg_spent_time = {i: avg_spent_time[i + "_per"] for i in avg_spent_time if
    #                   i in list(avg_df['Feature_type'].unique())}
    avg_spent_time['value'] = sum(avg_df['Spent_time']) / avg_df.shape[0]

    dict_update_ele("average_spent_time", avg_spent_time, final_dict)

    # docs_approved
    docs_approved = summer(df[df['Status'] == "Done"], "Subject", ["PDD", "PRD"], "")
    # total = docs_approved['total']
    # docs_approved = {i: docs_approved[i + "_per"] for i in docs_approved if
    #                  i in ["PDD", "PRD"]}
    # docs_approved['value'] = total
    dict_update_ele("docs_approved", docs_approved, final_dict)

    # features_built
    features_built = summer(df, "Feature_type", [], "")
    # total = features_built['total']
    # features_built = {i: features_built[i + "_per"] for i in features_built if
    #                   i in list(df['Feature_type'].unique())}
    # features_built['value'] = total
    dict_update_ele("features_built", features_built, final_dict)

    # resource_aloc
    resource_aloc = to_dictionary(df.groupby(by=["Project"], as_index=False)["Assignee"].nunique().to_dict("records"),
                                  "Project", "Assignee")
    dict_update_ele("resource_allocation", resource_aloc, final_dict)

    # action_items_closed
    action_items = df2.explode("action_items")
    action_items = action_items['action_items'].apply(pd.Series)
    action_items['ac_status']=action_items.apply(lambda x:"Done" if re.search("complete",str(x['ac_status']),flags=re.IGNORECASE) else x['ac_status'],axis=1)
    action_items = summer(action_items, "ac_status", [], "")
    action_items = {"value": action_items['Done']}
    dict_update_ele("action_items_closed", action_items, final_dict)

    # milestones_met
    mile1 = df1[df1['remove']==False]
    mile = summer(mile1, "team", [], "")
    # value = mile['total']
    mile = {i.replace("_per", ""): mile[i] for i in mile if "_per" in i}
    # mile['value'] = value
    # mile_project = modularize_df(df1, "project_assigned", "deliverable_status")
    # mile_project = {
    #     i.lower().replace(" ", "_"): {j.lower().replace(" ", "_"): mile_project[i].count(j) for j in mile_project[i]}
    #     for i in mile_project}
    # mile.update({"project": mile_project})
    dict_update_ele("milestone_met", mile, final_dict)

    # overall_efficiency
    ov_eff = df[df['Status'] == "Done"]
    ov_eff['time_taken'] = ov_eff.apply(lambda x: time_diff(x['Start_date'], x['End_date']), axis=1)
    ov_eff['time_to_be_taken'] = ov_eff.apply(lambda x: time_diff(x['Start_date'], x['Due_date']), axis=1)
    ov_effic = effectivity(ov_eff, [""])
    ov_effic.update(effectivity(ov_eff, list(ov_eff['Project'].unique())))
    dict_update_ele("overall_efficiency", ov_effic, final_dict)

    # progress_Tracker
    prog_track = summer(df, "Status", [], "")
    # prog_track = {i: prog_track[i + "_per"] for i in prog_track if i in list(df['Status'].unique())}
    # prog_track_project = modularize_df(df, "Project", "Status")
    # prog_track_project = {
    #     i.lower().replace(" ", "_"): {j.lower().replace(" ", "_"): prog_track_project[i].count(j) for j in
    #                                   prog_track_project[i]} for i in prog_track_project}
    # prog_track.update({"project": prog_track_project})
    dict_update_ele("progress_tracker", prog_track, final_dict)

    # timeline_Tracker
    time_line = copy.deepcopy(df)
    time_line['time_taken'] = time_line.apply(lambda x: "on_track" if x['End_date'] <= x['Due_date'] else "delayed",
                                              axis=1)
    time_line_dict = {
        "on_track": int(round_off((time_line[time_line['time_taken'] == "on_track"].shape[0] / time_line.shape[0]) * 100)),
        "delayed": int(round_off((time_line[time_line['time_taken'] == "delayed"].shape[0] / time_line.shape[0]) * 100))}
    # time_line_dict['total'] = time_line_dict['on_track'] + time_line_dict['delayed']
    # time_line_ = modularize_df(time_line, "Project", "time_taken")
    # time_line_dict.update(
    #     {"project": {i.lower().replace(" ", "_"): {j.lower().replace(" ", "_"): time_line_[i].count(j) for j in
    #                                                time_line_[i]} for i in time_line_}})
    dict_update_ele("timeline_tracker", time_line_dict, final_dict)

    # monthly_sprint_burndown_chart

    return final_dict


def pct_finder(a, b):
    try:
        return round(((float(a) - float(b)) / float(b)) * 100, 2)
    except:
        return 0


def differ(a, b):
    try:
        return a - b
    except:
        return "NA"


def sign(pct):
    return "-" if pct < 0 else "+"


def formatter(flag, dict1, key):
    pct = pct_finder(dict1[key].get('value'), dict1[key + "_lw"].get('value'))
    final_dict = {"value": dict1[key].get('value', "NA"), "pct": abs(pct), "sign": sign(pct)}
    list_off_keys = set(dict1[key].keys())
    list_off_keys.update(set(dict1[key + "_lw"].keys()))
    try:
        list_off_keys.remove("value")

    except:
        try:
            list_off_keys.remove("project")
        except:
            pass
    if flag == 1:
        project_wise = {num: [i.lower().replace(" ", "_"), dict1[key].get(i, "NA"), dict1[key + "_lw"].get(i, "NA"),
                              str(differ(dict1[key].get(i, 0), dict1[key + "_lw"].get(i, 0)))] for num, i in
                        enumerate(list(list_off_keys))}
        final_dict.update({"project_wise": project_wise})
    elif flag == 2:
        final_dict.update({"graph": {i.lower().replace(" ", "_"): dict1[key].get(i, "NA") for i in list_off_keys}})
    else:
        project_tw = dict1[key].get("project", {})
        project_lw = dict1[key + "_lw"].get("project", {})
        list_off_keys = set(list(project_tw.keys()) + list(project_lw.keys()))
        final_dict.update({"project_wise": {
            num: [i.lower().replace(" ", "_"), project_tw.get(i, {}), project_lw.get(i, {})] for num, i in
            enumerate(list(list_off_keys))}})

    return final_dict


@app.route("/management_dashboard", methods=["GET", "OPTIONS"])
def surya():
    if request.method == "OPTIONS":
        return _build_cors_prelight_response()
    if request.method == "GET":
        db_access = db.DataUpDown()
        from_date = request.args["from_date"]
        to_date = request.args['to_date']
        if not (from_date and to_date):
            abort(400, "Provide Dates")

        # current_data
        query = {"$gte": datetime.datetime.strptime(from_date, "%d-%m-%Y"),
                 "$lte": datetime.datetime.strptime(to_date, "%d-%m-%Y")}
        final_dict = actual_func(query, db_access)

        # previous_time_frame_data
        query = {"$gte": datetime.datetime.strptime(from_date, "%d-%m-%Y") - datetime.timedelta(
            days=time_diff(query['$gte'], query['$lte'])),
                 "$lt": datetime.datetime.strptime(from_date, "%d-%m-%Y")}

        final_dict_lw = actual_func(query, db_access)
        final_dict_lw = {key + "_lw": final_dict_lw[key] for key in final_dict_lw}

        # merging current and_old
        final_dict.update(final_dict_lw)

        keys = {'progress_tracker': [3, 2], 'action_items_closed': [2], 'average_spent_time': [2], 'docs_approved': [2],
                'features_built': [2], 'milestone_met': [1], 'overall_efficiency': [2], 'overall_productivity': [2],
                'resource_allocation': [1], 'timeline_tracker': [2, 3]}
        output = {}
        for i in keys:
            dict2 = {}
            for j in keys[i]:
                dict2.update(formatter(j, final_dict, i))
            output.update({i: dict2})

        return _corsify_actual_response(jsonify(output))


def make_percentage(a, b, c):
    return (b - a / c) * 100


def group_and_summer(data, key):
    return data[key].value_counts().to_dict()


def present_absent(df, key, employees_size, flag):
    analysis = {}
    latest_run = df.iloc[-1]['date']
    df = df[(df['attendance'].isin(key)) & (df['date'] == latest_run)]
    value = round((df.shape[0] /
                   employees_size) * 100, 2)
    if flag:
        analysis = group_and_summer(df, "reason_of_absence")
    return {"value": int(value), "analysis": analysis}


@app.route("/central_dashboard", methods=["GET", "OPTIONS"])
def cb_dashboard():
    if request.method == "OPTIONS":
        return _build_cors_prelight_response()
    if request.method == "GET":
        db_access = db.DataUpDown()
        from_date = request.args["from_date"]
        to_date = request.args['to_date']
        if not (from_date and to_date):
            abort(400, "Provide Dates")
        month = "March"
        year = "2023"
        employee_data_full = pd.DataFrame(db_access.manage(method="find", key="emp_det_new", s_data=({}, {"_id": 0})))
        attendance_data = pd.DataFrame(db_access.manage(method="find", key="attendance", s_data=({}, {"_id": 0})))
        hiring_data = pd.DataFrame(db_access.manage(method="find", key="hiring", s_data=({"month": month, "year": year},
                                                                                         {"_id": 0})))
        financial_data = pd.DataFrame(db_access.manage(method="find", key="fc", s_data=({}, {"_id": 0})))
        employee_data = employee_data_full[employee_data_full["active"] == True]
        # employee_data=data_getter(employee_data,duration)
        output_dict = {}

        # organization_insights

        # headcount_growth:
        # new=.shape[0]
        # old=employee_data[]

        # headcount_by_dep
        headcount_by_dep = group_and_summer(employee_data, "Department")
        dict_update_ele("headcount_dept", headcount_by_dep, output_dict)

        average_age = int(sum(list(employee_data['Age'])) / employee_data.shape[0])
        dict_update_ele("average_age", average_age, output_dict)

        gender = group_and_summer(employee_data, "Gender")
        dict_update_ele("gender_demographics", gender, output_dict)

        present_data = present_absent(attendance_data, ["Present", "Late"], employee_data.shape[0], False)
        dict_update_ele("present_attendees", present_data, output_dict)

        absent_data = present_absent(attendance_data, ["Absent"], employee_data.shape[0], True)
        dict_update_ele("absent_attendees", absent_data, output_dict)

        late_data = present_absent(attendance_data, ["Late"], employee_data.shape[0], False)
        dict_update_ele("late_attendees", late_data, output_dict)

        hiring = round(int(hiring_data.iloc[0]['Candidates_hired']) / int(hiring_data.iloc[0]['applications_received']) * 100, 2)
        dict_update_ele("hiring", hiring, output_dict)

        attrition_rate = employee_data_full[
            (employee_data_full['active'] == False) & (employee_data_full['released_date']).gt(
                datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0)) & (
                employee_data_full['released_date']).lt(
                datetime.datetime.now().replace(day=31, hour=0, minute=0, second=0))]
        attrition_rate = round((attrition_rate.shape[0] / employee_data.shape[0] + attrition_rate.shape[0]) * 100, 2)
        dict_update_ele("attrition_rate", attrition_rate, output_dict)

        # financial_tracker
        # fc_data = sum(list(financial_data[financial_data['transaction_type'] == "Credit"]['amount_transacted'])) - sum(
        #     list(financial_data[financial_data['transaction_type'] == "Debit"]['amount_transacted']))

        # output_dict.update({"financial_tracker": fc_data})

        return _corsify_actual_response(jsonify(output_dict))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
