import copy
import re
import math
import io
import json
import base64
from flask import Flask, request, jsonify, make_response, abort, Response
from flask_cors import CORS
import src.util.db as db
import pandas as pd
import datetime, calendar
from dateutil.relativedelta import relativedelta
import numpy as np
from collections import Counter
from ordered_set import OrderedSet

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


@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    if request.method == 'OPTIONS':
        # print('options method call')
        return _build_cors_prelight_response()
    if request.method == "POST":
        # get the base64 encoded string from somewhere
        pdf_b64 = request.data.decode('utf-8')

        # decode the base64 string to bytes
        pdf_bytes = base64.b64decode(pdf_b64)

        # create a file-like buffer to receive the decoded bytes
        buffer_data = io.BytesIO(pdf_bytes)

        # send the buffer as a file to the user
        return Response(buffer_data.getvalue(), mimetype='application/pdf', headers={
            'Content-Disposition': 'attachment;filename=sample.pdf'})


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
            if action_items:
                act_item = pd.DataFrame(action_items)
                count = round_off((len(act_item[(act_item['ac_status'] == 'Done') & (act_item['remove'] == False)]) /
                                   len(act_item[act_item['remove'] == False])) * 100)
            else:
                count = 0
            return count

        if payload["method"] == "insert":

            check = db_access.manage(method="find",
                                     key=key,
                                     s_data=[{"project_name": payload["project_name"],
                                              "remove": False
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
                "discussion": payload['discussion'],
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
            if payload["data"].get('project_name',''):
                check = db_access.manage(method="find",
                                         key=key,
                                         s_data=[{"mom_name": payload["mom_name"],
                                                  "remove": False
                                                  # "prepared_by": payload["prepared_by"],
                                                  },
                                                 {"mom_name": 1, "_id": 0}],
                                         sort=("_id", -1), limit=1)
                # check = list(coll.find({"project_name": payload["project_name"]},
                #                        {"mom_name": 1, "_id": 0}).sort(("_id", -1)).limit(1))
                if check:
                    mom_name = check[0]["mom_name"]
                    project_seq_no = str(int(mom_name.split("_")[1]))
                    payload["data"].update(
                        {"mom_name": payload["data"]['project_name'] + '_00' + project_seq_no + '_' + (payload.get('meeting_date') if payload.get('meeting_date','') else payload["data"]['meeting_date'])})
            if payload["data"].get("action_items"):
                action_perc = action_percent(payload["data"].get("action_items"))
                payload["data"].update({"action_percentage": action_perc})


            s_d = {"mom_name": payload["mom_name"]}
            u_d = {"$set": payload["data"]}
            db_access.manage(method=payload["method"], key=key, s_data=s_d, input_data=u_d)
            # coll.update_one(s_d, u_d)

            return _corsify_actual_response(jsonify({"msg": "data updated successfully"}))

        elif payload["method"] == "find":
            if str(payload.get('ac_perc','')).lower() == 'true':
                s_data = ({"action_percentage": {"$eq": 100},'remove': False}, {"_id": 0})
            elif str(payload.get('ac_perc','')).lower() == 'false':
                s_data = ({"action_percentage": {"$ne": 100}, 'remove': False}, {"_id": 0})
            else:
                s_data = ({"mom_name": payload["mom_name"], 'remove': False},{"_id": 0})
            # s_data = ({"action_percentage": payload['ac_perc']}, {"_id": 0})
            mom_data = db_access.manage(method=payload["method"], key=key, s_data=s_data, limit=payload.get('limit',0),
                                        skip_val=payload['sort'], sort=("_id", -1))

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

        team_data = db_access.manage(method="find", key="emp_det",
                                     s_data=({}, {"team": 1, "emp_name": 1, "emp_id": 1, "_id": 0}))
        event_data = db_access.manage(method="find", key="uc", s_data=({}, {"_id": 0}))
        year = db_access.manage(method="find", key="dropdown", s_data=({}, {"_id": 0}))[0]
        month = db_access.manage(method="find", key="dropdown", s_data=({}, {"_id": 0}))[1]
        # team = db_access.manage(method="find", key="dropdown", s_data=({}, {"_id": 0}))[2]
        status = db_access.manage(method="find", key="dropdown", s_data=({}, {"_id": 0}))[3]
        emp_lvl = db_access.manage(method="find", key="dropdown", s_data=({}, {"_id": 0}))[4]
        project_data = db_access.manage(method="find", key="op_data", s_data=({}, {"_id": 0, "Project": 1}))
        project_data = pd.DataFrame(project_data).drop_duplicates()["Project"].to_list()
        data = pd.DataFrame(team_data).groupby("team")['emp_name'].apply(list).to_dict()
        teams_data = list(pd.DataFrame(team_data)['team'].drop_duplicates(inplace=False))
        final_dict = {"teams": teams_data, "event_data": event_data, "year": year["values"], "month": month["values"],
                      "status": status["values"], "projects": project_data, "employee_level": emp_lvl["values"]}
        employee_data = pd.DataFrame(team_data).groupby("emp_id")['emp_name'].apply(list).to_dict()
        emp_data = list()
        for i in employee_data:
            emp_data.append({"emp_id": i, "emp_name": employee_data[i][0]})

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

        data = pd.DataFrame(db_access.manage(method="find", key="op_data", s_data=({}, {"_id": 0})))
        data.rename(columns={'Team': 'team'}, inplace=True)
        status_counts = data.groupby('Project', as_index=False)['Status'].value_counts()
        df_status = status_counts.pivot(index='Project', columns='Status',
                                        values='count').reset_index().fillna(0).to_dict('records')
        return {"report_data": [data.to_dict("records")], "graph": df_status}


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
        query1 = {"$gte": datetime.datetime.strptime(from_date, "%d-%m-%Y").strftime("%Y-%m-%d"),
                  "$lte": datetime.datetime.strptime(to_date, "%d-%m-%Y").strftime("%Y-%m-%d")}
        final_dict = actual_func(query, query1, db_access)

        # previous_time_frame_data
        query = {"$gte": datetime.datetime.strptime(from_date, "%d-%m-%Y") - datetime.timedelta(
            days=time_diff(query['$gte'], query['$lte'])),
                 "$lte": datetime.datetime.strptime(from_date, "%d-%m-%Y")}
        query1 = {"$gte": query['$gte'].strftime("%Y-%m-%d"),
                  "$lte": query['$lte'].strftime("%Y-%m-%d")}
        final_dict_lw = actual_func(query, query1, db_access)
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
        output.update({"hours_graph": final_dict['last_graph']})
        return _corsify_actual_response(jsonify(output))


@app.route("/central_dashboard", methods=["GET", "POST", "OPTIONS"])
def cb_dashboard():
    if request.method == "OPTIONS":
        return _build_cors_prelight_response()
    if request.method in ["GET", "POST"]:
        db_access = db.DataUpDown()
        payload = request.json
        screen = payload["screen"]
        current_year = payload['current_year']
        previous_year = payload['previous_year']
        current_month = payload['current_month']
        previous_month = payload['previous_month']
        if not (current_year and current_month):
            abort(400, "Provide required data")
        current_month, current_year, previous_month, previous_year, days_count = \
            month_convertor(current_month=current_month, current_year=current_year)
        current_month_p, current_year_p, previous_month_p, previous_year_p, days_count_p = \
            month_convertor(previous=True, current_month=current_month, current_year=current_year)

        employee_data_full = pd.DataFrame(db_access.manage(method="find", key="emp_det_new", s_data=({}, {"_id": 0})))
        attendance_data = pd.DataFrame(db_access.manage(method="find", key="attendance", s_data=({}, {"_id": 0})))
        hiring_data = pd.DataFrame(db_access.manage(method="find", key="hiring", s_data=({}, {"_id": 0})))
        financial_data = pd.DataFrame(db_access.manage(method="find", key="fc", s_data=({}, {"_id": 0})))
        financial_field = pd.DataFrame(db_access.manage(method="find", key="ff", s_data=({}, {"_id": 0})))
        financial_kpi = pd.DataFrame(db_access.manage(method="find", key="fk", s_data=({}, {"_id": 0})))
        startup_fld = pd.DataFrame(db_access.manage(method="find", key="sf", s_data=({}, {"_id": 0})))
        # startup_data = pd.DataFrame(db_access.manage(method="find", key="sd", s_data=({}, {"_id": 0})))
        startup_data_new = db_access.manage(method="find", key="sd", s_data=({}, {"_id": 0}))
        marketing_field = pd.DataFrame(db_access.manage(method="find", key="mf", s_data=({}, {"_id": 0})))
        marketing_data = pd.DataFrame(db_access.manage(method="find", key="md", s_data=({}, {"_id": 0})))

        # organization_dashboard
        if screen == "organization_dashboard":
            try:
                final_dict = {}
                current_output_dict = organization_dashboard(employee_data_full=employee_data_full,
                                                             attendance_data=attendance_data, hiring_data=hiring_data,
                                                             current_month=current_month, previous_month=previous_month,
                                                             current_year=current_year, num_days=days_count)
                previous_output_dict = organization_dashboard(employee_data_full=employee_data_full,
                                                              attendance_data=attendance_data, hiring_data=hiring_data,
                                                              current_month=current_month_p,
                                                              previous_month=previous_month_p,
                                                              current_year=current_year_p, num_days=days_count)

                lst = {"headcount_dept": "headcount_growth", "present_attendees": "value", "absent_attendees": "value",
                       "late_attendees": "value", "attrition_rate": ""}
                for i in lst:
                    if isinstance(current_output_dict[i], dict):
                        pct = abs(pct_finder(current_output_dict[i][lst[i]], previous_output_dict[i][lst[i]]))
                        final_dict.update({i + "_pct": pct, i + "_pct_sign": sign(pct)})
                    else:
                        pct = abs(pct_finder(current_output_dict[i], previous_output_dict[i]))
                        final_dict.update({i + "_pct": pct, i + "_pct_sign": sign(pct)})
                current_output_dict.update(final_dict)
                return _corsify_actual_response(jsonify(current_output_dict))
            except:
                return _corsify_actual_response(jsonify({"Msg": "NO DATA FOUND"}))

        # financial_tracker
        if screen == "financial_tracker":
            try:
                current_output_dict = financial_tracker(financial_data=financial_data, financial_field=financial_field,
                                                        current_year=current_year, previous_year=previous_year,
                                                        current_month=current_month, financial_kpi=financial_kpi)
                previous_output_dict = financial_tracker(financial_data=financial_data, financial_field=financial_field,
                                                         current_year=current_year_p, previous_year=previous_year_p,
                                                         current_month=current_month_p, financial_kpi=financial_kpi)
                final_dict = {}
                lst = {'net_cash_flow': "total", 'Revenue_growth_rate': "total", 'current_ratio': "current_ratio"}
                for i in lst:
                    if isinstance(current_output_dict[i], dict):
                        pct = abs(pct_finder(current_output_dict[i][lst[i]], previous_output_dict[i][lst[i]]))
                        final_dict.update({i + "_pct": pct, i + "_pct_sign": sign(pct)})
                    else:
                        pct = abs(pct_finder(current_output_dict[i], previous_output_dict[i]))
                        final_dict.update({i + "_pct": pct, i + "_pct_sign": sign(pct)})
                current_output_dict.update(final_dict)

                return _corsify_actual_response(jsonify(current_output_dict))
            except:
                return _corsify_actual_response(jsonify({"Msg": "NO DATA FOUND"}))

        # startup_Metrics_Screen
        if screen == "startup_metrics_screen":
            try:
                current_output_dict = startup_metrics_screen(startup_fld=startup_fld, financial_data=financial_data,
                                                             startup_data_new=startup_data_new,
                                                             current_year=current_year, previous_year=previous_year,
                                                             current_month=current_month)
                previous_output_dict = startup_metrics_screen(startup_fld=startup_fld, financial_data=financial_data,
                                                              startup_data_new=startup_data_new,
                                                              current_year=current_year_p, previous_year=previous_year_p,
                                                              current_month=current_month_p)

                final_dict = {}
                lst = {'active_customer': "total", 'Annual run rate': "total", 'GBR': "total", 'ARPA': "total",
                       'MRR': "total"}
                for i in lst:
                    if isinstance(current_output_dict[i], dict):
                        pct = abs(pct_finder(current_output_dict[i][lst[i]], previous_output_dict[i][lst[i]]))
                        final_dict.update({i + "_pct": pct, i + "_pct_sign": sign(pct)})
                    else:
                        pct = abs(pct_finder(current_output_dict[i], previous_output_dict[i]))
                        final_dict.update({i + "_pct": pct, i + "_pct_sign": sign(pct)})
                current_output_dict.update(final_dict)

                return _corsify_actual_response(jsonify(current_output_dict))
            except:
                return _corsify_actual_response(jsonify({"Msg": "NO DATA FOUND"}))

        if screen == "marketing_screen":
            try:
                current_output_dict = marketing_screen(marketing_dt=marketing_data, marketing_fld=marketing_field,
                                                       current_year=current_year,
                                                       current_month=current_month, value=0)

                previous_output_dict = marketing_screen(marketing_dt=marketing_data, marketing_fld=marketing_field,
                                                        current_year=current_year_p,
                                                        current_month=current_month_p,
                                                        value=1)
                #
                final_dict = {}
                lst = {'demo_count': "demo_count"}
                for i in lst:
                    if isinstance(current_output_dict[i], dict):
                        pct = abs(pct_finder(current_output_dict[i][lst[i]], previous_output_dict[i][lst[i]]))
                        final_dict.update({i + "_pct": pct, i + "_pct_sign": sign(pct)})
                    else:
                        pct = abs(pct_finder(current_output_dict[i], previous_output_dict[i]))
                        final_dict.update({i + "_pct": pct, i + "_pct_sign": sign(pct)})
                current_output_dict.update(final_dict)

                return _corsify_actual_response(jsonify(current_output_dict))
            except:
                return _corsify_actual_response(jsonify({"Msg": "NO DATA FOUND"}))

        return _corsify_actual_response(jsonify({"Msg": "NO DATA FOUND"}))


@app.route("/milestone", methods=['GET', 'POST', 'OPTIONS'])
def mile_func():
    if request.method == "OPTIONS":
        return _build_cors_prelight_response()
    if request.method in ["GET", "POST"]:
        try:
            db_access = db.DataUpDown()
            payload = request.json
            current_year = payload['current_year']
            current_month = payload['current_month']
            if not (current_year and current_month):
                abort(400, "Provide required data")
            current_month, current_year, previous_month, previous_year, days_count = \
                month_convertor(current_month=current_month, current_year=current_year)
            employee_data_full = pd.DataFrame(db_access.manage(method="find", key="emp_det_new",
                                                               s_data=({}, {"_id": 0,"emp_id":1, "emp_name":1})))
            mile_df = pd.DataFrame(db_access.manage(method="find",
                                                    key="mile", s_data=({"month": current_month,
                                                                         "year": current_year, "remove": False},
                                                                        {"_id": 0})))

            f_df = mile_df.groupby(['name', 'project_assigned'], as_index=False).first()
            f_calc = f_df.groupby('name')['actual_weightage'].sum().reset_index()
            f_calc['new'] = (f_calc[['actual_weightage']] * days_count)/100
            f_calc['new1'] = days_count - f_calc[['new']]

            def floor_or_ceil(x):
                if x < 0:
                    return math.floor(x)
                else:
                    return math.ceil(x)

            f_calc['LOP'] = f_calc['new1'].apply(floor_or_ceil)
            f_calc = f_calc.rename(columns={'name': 'emp_name', 'actual_weightage': 'milestone_completion'})
            merged_df = pd.merge(f_calc, employee_data_full, on='emp_name')
            merged_df = merged_df.rename(columns={'emp_name': 'Employee Name',
                                                  'milestone_completion': 'Milestone completion', "emp_id": 'Employee ID'})
            data_dict = merged_df[['Employee ID', 'Employee Name', 'Milestone completion', 'LOP']].to_dict("records")
            data_str = json.dumps(data_dict, sort_keys=False)
            return _corsify_actual_response(Response(data_str))
        except:
            return _corsify_actual_response(jsonify({"Msg": "NO DATA FOUND"}))


@app.route("/data_entry", methods=["GET", "POST", "OPTIONS"])
def entry_func():
    if request.method == "OPTIONS":
        return _build_cors_prelight_response()
    if request.method in ["GET", "POST"]:
        db_access = db.DataUpDown()
        upload_file = request.files['file']
        # filename = upload_file.filename
        screen, date = request.form.get("screen", ""), request.form.get("date", "")
        if not screen:
            abort(400, "Provide required data")

        if screen == "finance":
            df = pd.read_csv(upload_file).to_dict("records")
            # print(df)
            db_access.manage(method="insert", key="fc", input_data=df)
            return _corsify_actual_response(jsonify({"msg": "FINANCE data inserted successfully"}))

        elif screen == "hr":
            df = pd.read_csv(upload_file)
            df = df.fillna("").to_dict("records")
            # print(df)
            db_access.manage(method="insert", key="attendance", input_data=df)
            return _corsify_actual_response(jsonify({"msg": "HR data inserted successfully"}))

        elif screen == "op":
            df = pd.read_csv(upload_file).to_dict("records")
            # print(df)
            db_access.manage(method="insert", key="op_data", input_data=df)
            return _corsify_actual_response(jsonify({"msg": "OP data inserted successfully"}))

        elif screen == "MARKETING_DATA":
            month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            df = pd.read_csv(upload_file).to_dict("records")
            for i in df:
                if i['month'] in month:
                    data = {"month": i['month'],
                            "year": str(int(i['year'])),
                            "website_traffic": float(i['website_traffic']),
                            "traffic_sources": {
                                "organic": float(i['traffic_sources_organic']),
                                "direct": float(i['traffic_sources_direct']),
                                "referral": float(i['traffic_sources_referral']),
                                "organic_social": float(i['traffic_sources_organic_social']),
                                "organic_video": float(i['traffic_sources_organic_video']),
                                "unassigned": float(i['traffic_sources_unassigned'])
                            },
                            "bounce_rate": str(i['bounce_rate']),
                            # "interactions": str(df[0]['interactions']),
                            "users_per_device": {
                                "mobile": float(i['users_mobile']),
                                "desktop": float(i['users_desktop']),
                                "tablet": float(i['users_tablet'])
                            },
                            "email_successfully_delivered": float(i['email_successfully_delivered']),
                            "email_bounce": float(i['email_bounce']),
                            "open_rate": float(i['open_rate']),
                            "click_rate": float(i['click_rate']),
                            "reply_rate": float(i['reply_rate']),
                            "average_session_duration": i['average_session_duration'],
                            "page_views": float(i['page_views']),
                            "demo_client": str(i['demo_client']),
                            "demo_date": str(i['demo_date']),
                            "demo_product": str(i['demo_product'])}

                    db_access.manage(method="insert", key="mf", input_data=data)
                    return _corsify_actual_response(jsonify({"msg": "MARKETING data inserted successfully"}))
                return _corsify_actual_response(jsonify({"msg": "Wrong Format"}))
        else:
            return _corsify_actual_response(jsonify({"msg": "Wrong Input"}))


@app.route("/workforce", methods=["GET", "OPTIONS"])
def workforce_func():
    if request.method == "OPTIONS":
        return _build_cors_prelight_response()
    else:
        db_access = db.DataUpDown()
        key = ["emp_det", "op_data", "mom", "mile"]
        emp_det = pd.DataFrame(db_access.manage(method="find", key=key[0],
                                                s_data=({}, {"emp_id": 1, "emp_name": 1, "team": 1, "contract_type": 1,
                                                             "_id": 0})))

        

        # Projects assigned, tasks assigned, tasks completed for each employee

        from_date = request.args.get("from_date")
        to_date = request.args.get("to_date")

        # current month
        query = {"$gte": datetime.datetime.strptime(from_date, "%d-%m-%Y"),
                 "$lte": datetime.datetime.strptime(to_date, "%d-%m-%Y")}
        query1 = {"$gte": datetime.datetime.strptime(from_date, "%d-%m-%Y").strftime("%Y-%m-%d"),
                  "$lte": datetime.datetime.strptime(to_date, "%d-%m-%Y").strftime("%Y-%m-%d")}

        final_dict = workforce(query=query, query1=query1, db_access=db_access)

        # prvs_month
        query = {"$gte": datetime.datetime.strptime(from_date, "%d-%m-%Y") - datetime.timedelta(
            days=time_diff(query['$gte'], query['$lte'])),
                 "$lte": datetime.datetime.strptime(from_date, "%d-%m-%Y")}
        query1 = {"$gte": query['$gte'].strftime("%Y-%m-%d"),
                  "$lte": query['$lte'].strftime("%Y-%m-%d")}
        final_dict_lw = workforce(query=query, query1=query1, db_access=db_access)
        final_dict_lw = {key + "_lw": final_dict_lw[key] for key in final_dict_lw}

        # merging current and_old
        final_df = pd.concat([final_dict, pd.DataFrame(final_dict_lw)], axis=1)

        final_df['pct_milestone'] = final_df.apply(
            lambda row: abs(pct_finder(row.milestones_per, row.milestones_per_lw)), axis=1)
        final_df['pct_productivity'] = final_df.apply(
            lambda row: abs(pct_finder(row.overall_productivity, row.overall_productivity_lw)), axis=1)
        final_df['pct_efficiency'] = final_df.apply(
            lambda row: abs(pct_finder(row.overall_efficiency, row.overall_efficiency_lw)), axis=1)
        final_df['pct_action_item'] = final_df.apply(
            lambda row: abs(pct_finder(row.action_item_done, row.action_item_done_lw)), axis=1)

        final_df['pct_milestone_sign'] = final_df.apply(lambda row: sign(row.pct_milestone), axis=1)
        final_df['pct_efficiency_sign'] = final_df.apply(lambda row: sign(row.pct_efficiency), axis=1)
        final_df['pct_productivity_sign'] = final_df.apply(lambda row: sign(row.pct_productivity), axis=1)
        final_df['pct_action_item_sign'] = final_df.apply(lambda row: sign(row.pct_action_item), axis=1)
        print(final_df)

        dataf = pd.DataFrame(db_access.manage(method="find", key=key[1],
                                              s_data=({}, {"_id": 0})))
        dataf['month'] = dataf['Due_date'].dt.strftime('%b')
        final_df_ = copy.deepcopy(emp_det)
        final_df_['graph_data'] = final_df_.apply(lambda x: [], axis=1)
        for i in OrderedSet(list(dataf['month'])):
            data1 = dataf[dataf['month'] == i]

            df_ = workforce(op_data=data1, db_access=db_access)

            df_['month'] = i
            df_['graph_data'] = df_.apply(lambda x: {key: x.get(key) for key in
                                                          ["completed_tasks", "overall_efficiency",
                                                           "overall_productivity", "month"]}, axis=1)
            diction = {x['emp_id']: x['graph_data'] for row, x in df_.iterrows()}
            final_df_.apply(lambda x: x['graph_data'].append(diction.get(x['emp_id'])), axis=1)

        final_df = final_df[
            ['contract_type', 'team', 'emp_name', 'emp_id', 'project_assigned', 'task_assigned', 'completed_tasks',
             'milestones_per', 'action_item_done', 'action_item_total', 'overall_efficiency', 'overall_productivity',
              'pct_action_item_sign', 'pct_productivity_sign', 'pct_efficiency_sign', 'pct_milestone_sign',
             'pct_action_item', 'pct_efficiency', 'pct_milestone', 'pct_productivity']]
        final_df = pd.merge(final_df, final_df_[["emp_id", "graph_data"]], on="emp_id")
        final_df = final_df.to_dict('records')

        return _corsify_actual_response(jsonify(final_df))


def summer(dataf_, key, cols, col_to_sum, flag=False):
    if flag == True:
        total = 0
        features_built = {}
        dataf_[key].replace('', np.nan, inplace=True)
        dataf_[key].dropna()
        df_feature = list(dataf_[key].dropna().unique())
        if not cols:
            cols = df_feature
        for i in df_feature:
            if i and (i in cols):
                data = dataf_[dataf_[key] == i]
                if col_to_sum:
                    data = data[col_to_sum].sum()
                else:
                    data = data.shape[0]
                features_built[i] = data
                total += data
        # features_built.update({i: round((features_built[i] / total) * 100, 2) for i in features_built})
        # features_built['total'] = total
        return features_built
    else:
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
                total += data

        # features_built.update({i + "_per": round_off((features_built[i] / total) * 100) for i in features_built})
        features_built['total'] = int(total)
        return features_built


def workforce(query=None, query1=None, op_data=None, db_access=None):
    key = ["emp_det", "op_data", "mom", "mile"]
    emp_det = pd.DataFrame(db_access.manage(method="find", key=key[0],
                                            s_data=({}, {"emp_id": 1, "emp_name": 1, "team": 1, "contract_type": 1,
                                                         "_id": 0})))

    if query:
        df, df1, df2, df3 = pd.DataFrame(
            db_access.manage(method="find", key=key[1], s_data=({"Assignee": {"$in": list(emp_det["emp_name"])},
                                                                 "Due_date": query
                                                                 }, {"_id": 0}))), pd.DataFrame(
            db_access.manage(method="find", key=key[3], s_data=({"name": {"$in": list(emp_det["emp_name"])},
                                                                 "due_date": query1
                                                                 }, {"_id": 0}))), pd.DataFrame(
            db_access.manage(method="find", key=key[2],
                             s_data=({"action_items.ac_resp": {"$in": list(emp_det['emp_name'])}},
                                     {"_id": 0})
                             )), pd.DataFrame(
            db_access.manage(method="find", key=key[1], s_data=({}, {"_id": 0})))
        # # Projects assigned, tasks assigned, tasks completed for each employee
        op_data = pd.DataFrame(db_access.manage(method="find", key=key[1],
                                                s_data=({"Assignee": {"$in": list(emp_det["emp_name"])}}, {"_id": 0})))

        projects_assigned_per_person = op_data.groupby(by=['Assignee'], as_index=False)['Project'].apply(
            lambda x: len(set(x)))
        projects_assigned_per_person.rename(columns={'Project': 'project_assigned'}, inplace=True)
        final_df = pd.merge(emp_det, projects_assigned_per_person, left_on='emp_name', right_on='Assignee', how='left')
        final_df.drop(['Assignee'], axis=1, inplace=True)
        task_assigned = op_data.groupby(["Assignee", "Feature_type"]).agg(
            {"Subject": pd.Series.nunique}).reset_index().groupby("Assignee").sum().reset_index()
        task_assigned.rename(columns={'Subject': 'task_assigned'}, inplace=True)
        completed_task = op_data.query('Status == "Done"').groupby(["Assignee", "Feature_type"]).agg(
            {"Subject": pd.Series.nunique}).reset_index().groupby("Assignee").sum().reset_index()
        completed_task.rename(columns={'Subject': 'completed_tasks'}, inplace=True)
        final_df = pd.merge(final_df, task_assigned, left_on='emp_name', right_on='Assignee', how='left')
        final_df = pd.merge(final_df, completed_task, left_on='emp_name', right_on='Assignee', how='left')
        final_df['project_assigned'] = final_df['project_assigned'].fillna(0).astype('int')
        final_df['task_assigned'] = final_df['task_assigned'].fillna(0).astype('int')
        final_df['completed_tasks'] = final_df['completed_tasks'].fillna(0).astype('int')

        # action_items_closed
        action_items = df2.explode("action_items")
        action_items = action_items['action_items'].apply(pd.Series)
        action_items1 = copy.deepcopy(action_items)
        action_items = summer(action_items, "ac_resp", [], "", True)
        action_items1['ac_status'] = action_items1.apply(
            lambda x: "Done" if re.search("Done", str(x['ac_status']), flags=re.IGNORECASE) else x['ac_status'], axis=1)

        action_items1 = action_items1[action_items1['ac_status'] == "Done"]
        action_items1 = action_items1.groupby(by=["ac_resp"]).size().reset_index(name='counts')
        # action_items_done = summer(action_items, "ac_status", ["Done"], "", True)

        action_items_done = {row['ac_resp']: row['counts'] for i, row in action_items1.iterrows()}

        final_df['action_item_done'] = final_df['emp_name'].map(action_items_done)
        final_df['action_item_total'] = final_df['emp_name'].map(action_items)
        final_df['action_item_total'] = final_df['action_item_total'].fillna(0).astype('int')
        final_df['action_item_done'] = final_df['action_item_done'].fillna(0).astype('int')

        # milestones_met
        milestones_df = df1.groupby(by=["name"])['actual_weightage'].apply(list).reset_index()
        milestones_df['milestone_percentage'] = milestones_df.apply(
            lambda x: sum(x['actual_weightage']) / len(x['actual_weightage']), axis=1)
        milestones_df = {row['name']: row['milestone_percentage'] for i, row in milestones_df.iterrows()}
        final_df['milestones_per'] = final_df['emp_name'].map(milestones_df)
        final_df['milestones_per'] = final_df['milestones_per'].fillna(0).astype('int')
        # mile = summer(df1, "deliverable_status", [], "", True)

        # mile_project = to_dictionary(
        #     df1.groupby(by=["name"])['deliverable_status'].apply(list).reset_index().to_dict(
        #         "records"), "name", "deliverable_status")
        # mile_project = {
        #     i: {j: mile_project[i].count(j) for j in
        #         mile_project[i]}
        #     for i in mile_project}
        # mile.update(mile_project)
        # final_df['milestone'] = final_df['emp_name'].map(mile)
        # # final_df['milestone'].fillna('{}',inplace=True)
        # final_df['milestone'] = final_df.apply(lambda x: {} if not isinstance(x['milestone'], dict) else x['milestone'],
        #                                        axis=1)

        # overall_efficiency
        ov_eff = df[df['Status'] == "Done"]
        ov_eff['time_taken'] = ov_eff.apply(lambda x: time_diff(x['Start_date'], x['End_date']), axis=1)
        ov_eff['time_to_be_taken'] = ov_eff.apply(lambda x: time_diff(x['Start_date'], x['Due_date']), axis=1)
        ov_effic = effectivity(ov_eff, [""], True)
        ov_effic.update(effectivity(ov_eff, list(ov_eff['Assignee']), True))
        final_df['overall_efficiency'] = final_df['emp_name'].map(ov_effic)
        final_df['overall_efficiency'] = final_df['overall_efficiency'].fillna(0).astype('float')

        oa_pro_project = to_dictionary(
            df[df['Status'] == 'Done'].groupby(by=["Assignee"])['Spent_time'].apply(list).reset_index().to_dict(
                "records"), "Assignee", "Spent_time")
        oa_pro_project = {key: len(oa_pro_project[key]) / sum(oa_pro_project[key]) for key in oa_pro_project}
        final_df['overall_productivity'] = final_df['emp_name'].map(oa_pro_project)
        final_df = final_df.fillna(0)
        return final_df

    else:
        ################################
        completed_task = op_data.query('Status == "Done"').groupby(["Assignee", "Feature_type"]).agg(
            {"Subject": pd.Series.nunique}).reset_index().groupby("Assignee").sum().reset_index()
        completed_task.rename(columns={'Subject': 'completed_tasks'}, inplace=True)
        final_df = pd.merge(emp_det, completed_task, left_on='emp_name', right_on='Assignee', how='left')
        final_df['completed_tasks'] = final_df['completed_tasks'].fillna(0).astype('int')

        ov_eff = op_data[op_data['Status'] == "Done"]
        ov_eff['time_taken'] = ov_eff.apply(lambda x: time_diff(x['Start_date'], x['End_date']), axis=1)
        ov_eff['time_to_be_taken'] = ov_eff.apply(lambda x: time_diff(x['Start_date'], x['Due_date']), axis=1)
        ov_effic = effectivity(ov_eff, [""], True)
        ov_effic.update(effectivity(ov_eff, list(ov_eff['Assignee']), True))
        final_df['overall_efficiency'] = final_df['emp_name'].map(ov_effic)
        final_df['overall_efficiency'] = final_df['overall_efficiency'].fillna(0).astype('float')

        oa_pro_project = to_dictionary(
            op_data[op_data['Status'] == 'Done'].groupby(by=["Assignee"])['Spent_time'].apply(
                list).reset_index().to_dict(
                "records"), "Assignee", "Spent_time")
        oa_pro_project = {key: len(oa_pro_project[key]) / sum(oa_pro_project[key]) for key in oa_pro_project}
        final_df['overall_productivity'] = final_df['emp_name'].map(oa_pro_project)
        final_df = final_df.fillna(0)
        ##################################

        return final_df


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


def effectivity(ov_eff_, projects, flag=False):
    if flag == True:
        return_dict = {}
        for project in projects:
            if project:
                ov_eff = ov_eff_[ov_eff_['Assignee'] == project]

            else:
                project = "overall"
                ov_eff = ov_eff_
            ov_eff_time_taken = ov_eff['time_taken'].sum()
            ov_eff_time_to_be_taken = ov_eff['time_to_be_taken'].sum()

            if ov_eff_time_taken <= ov_eff_time_to_be_taken:
                ov_effi = abs((((ov_eff_time_to_be_taken - ov_eff_time_taken) / ov_eff_time_to_be_taken) * 100) + 100)
            else:
                ov_effi = abs(100 - (((ov_eff_time_taken - ov_eff_time_to_be_taken) / ov_eff_time_taken) * 100))

            return_dict[project] = round(ov_effi, 2)

        return return_dict
    else:
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
            return_dict.update({"spent_time": int(ov_eff_time_taken), "estimated_time": int(ov_eff_time_to_be_taken)})
            return_dict[project.lower().replace(" ", "_")] = round_off(ov_effi)

        return return_dict


def actual_func(query, query1, db_access):
    final_dict = {}
    df, df1, df2 = pd.DataFrame(
        db_access.manage(method="find", key="op_data", s_data=({"Due_date": query}, {"_id": 0}))), \
                   pd.DataFrame(
                       db_access.manage(method="find", key="mile", s_data=({"due_date": query1}, {"_id": 0}))), \
                   pd.DataFrame(
                       db_access.manage(method="find", key="mom", s_data=({"documented_date": query1}, {"_id": 0})))

    # hours_effort
    mon_val, y_val = query['$lte'].month, query['$lte'].year
    num_days = calendar.monthrange(y_val, mon_val)[1]
    df_ef = pd.DataFrame(df[['Spent_time', 'Estimated_time']].sum()).transpose()
    df_ef['max_time'] = len(df['Assignee'].unique()) * 8 * num_days

    df_ef = df_ef.transpose().reset_index().rename(columns={'index':'key',0:'value'}).to_dict("records")
    dict_update_ele("last_graph", df_ef, final_dict)

    # overall_productity
    oa_pro = df[df['Status'] == "Done"].shape[0] / sum(list(df[df['Status'] == "Done"]['Spent_time']))
    oa_pro_project = modularize_df(df[df['Status'] == 'Done'], "Project", "Spent_time")
    oa_pro_project = {key: len(oa_pro_project[key]) / sum(oa_pro_project[key]) for key in oa_pro_project}
    oa_pro_project.update({"value": oa_pro, "task_created": df[df['Status'] == "Done"].shape[0],
                           "spent_time": sum(list(df[df['Status'] == "Done"]['Spent_time']))})
    dict_update_ele("overall_productivity", oa_pro_project, final_dict)

    # avg_spent_timex
    avg_df = df[(df['Status'] == 'Done') & (df['Type'] == "Feature")]
    avg_spent_time = summer(avg_df, "Feature_type", [], "Spent_time")
    # avg_spent_time = {i: avg_spent_time[i + "_per"] for i in avg_spent_time if
    #                   i in list(avg_df['Feature_type'].unique())}
    avg_spent_time['value'] = sum(avg_df['Spent_time']) / avg_df.shape[0]
    avg_spent_time.pop('total')
    dict_update_ele("average_spent_time", avg_spent_time, final_dict)

    # docs_approved
    docs_approved = summer(df[df['Status'] == "Done"], "Subject", ["PDD", "PRD"], "")
    total = docs_approved['total']
    # docs_approved = {i: docs_approved[i + "_per"] for i in docs_approved if
    #                  i in ["PDD", "PRD"]}
    docs_approved['value'] = total
    docs_approved.pop('total')
    dict_update_ele("docs_approved", docs_approved, final_dict)

    # features_built
    features_built = summer(df, "Feature_type", [], "")
    total = features_built['total']
    # features_built = {i: features_built[i + "_per"] for i in features_built if
    #                   i in list(df['Feature_type'].unique())}
    features_built['value'] = total
    features_built.pop('total')
    dict_update_ele("features_built", features_built, final_dict)

    # resource_aloc
    resource_aloc = to_dictionary(df.groupby(by=["Project"], as_index=False)["Assignee"].nunique().to_dict("records"),
                                  "Project", "Assignee")
    dict_update_ele("resource_allocation", resource_aloc, final_dict)

    # action_items_closed
    if 'action_items' in df2.columns:
        action_items = df2.explode("action_items")
        action_items = action_items['action_items'].apply(pd.Series)
        action_items['ac_status'] = action_items.apply(
            lambda x: "Done" if re.search("complete", str(x['ac_status']), flags=re.IGNORECASE) else x['ac_status'], axis=1)
        action_items = summer(action_items, "ac_status", [], "")
        action_items = {"value": action_items['Done']}
    else:
        action_items = {"value": 0}
    dict_update_ele("action_items_closed", action_items, final_dict)

    # milestones_met
    # mile1 = df1[df1['remove'] == False]
    mile1 = df1[(df1['remove'] == False) & (df1["deliverable_status"] == "Done")]
    mile = summer(mile1, "team", [], "")
    value = mile['total']
    # mile = {i.replace("_per", ""): mile[i] for i in mile if "_per" in i}
    mile['value'] = value
    mile.pop('total')
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
    ov_effic.update({"spent_time_": int(ov_effic['spent_time']), "estimated_time_": int(ov_effic['estimated_time'])})
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
    prog_track.pop('total')
    dict_update_ele("progress_tracker", prog_track, final_dict)

    # timeline_Tracker
    time_line = copy.deepcopy(df)
    time_line['time_taken'] = time_line.apply(lambda x: "on_track" if x['End_date'] <= x['Due_date'] else "delayed",
                                              axis=1)
    time_line_dict = {
        "on_track": int(
            round_off((time_line[time_line['time_taken'] == "on_track"].shape[0] / time_line.shape[0]) * 100)),
        "delayed": int(
            round_off((time_line[time_line['time_taken'] == "delayed"].shape[0] / time_line.shape[0]) * 100))}
    # time_line_dict['total'] = time_line_dict['on_track'] + time_line_dict['delayed']
    # time_line_ = modularize_df(time_line, "Project", "time_taken")
    # time_line_dict.update(
    #     {"project": {i.lower().replace(" ", "_"): {j.lower().replace(" ", "_"): time_line_[i].count(j) for j in
    #                                                time_line_[i]} for i in time_line_}})
    dict_update_ele("timeline_tracker", time_line_dict, final_dict)

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


def make_percentage(a, b):
    return ((b - a) / b) * 100


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


def organization_dashboard(employee_data_full=None, attendance_data=None, hiring_data=None, current_month=None,
                           previous_month=None, current_year=None, num_days=None):
    output_dict = {}
    employee_data = employee_data_full[employee_data_full["active"] == True]
    attendance_data = attendance_data[attendance_data['month'] == current_month]
    # employee_data=data_getter(employee_data,duration)
    hg = make_percentage(attendance_data[attendance_data['month'] == current_month].shape[0],
                         attendance_data[attendance_data['month'] == previous_month].shape[0])

    headcount_by_dep = group_and_summer(employee_data, "Department")
    headcount_data = {"headcount_growth": round(hg), "headcount_dept": headcount_by_dep}

    dict_update_ele("headcount_dept", headcount_data, output_dict)

    average_age = int(sum(list(employee_data['Age'])) / employee_data.shape[0])
    # dict_update_ele("average_age", average_age, output_dict)

    gender = group_and_summer(employee_data, "Gender")
    dict_update_ele("gender_demographics", gender, output_dict)

    present_data = present_absent(attendance_data, ["Present", "Late"], employee_data.shape[0], False)
    dict_update_ele("present_attendees", present_data, output_dict)

    absent_data = present_absent(attendance_data, ["Absent"], employee_data.shape[0], True)
    dict_update_ele("absent_attendees", absent_data, output_dict)

    late_data = present_absent(attendance_data, ["Late"], employee_data.shape[0], False)
    dict_update_ele("late_attendees", late_data, output_dict)

    hiring = hiring_data[hiring_data['year'] == current_year]
    h_data = {"months": hiring['month'].tolist(),
              "data": [
                  {"candidates_hired": hiring['Candidates_hired'].tolist(),
                   "Interviews_taken": hiring['Interviews_taken'].tolist(),
                   "applications_received": hiring['applications_received'].tolist()}
              ]}
    dict_update_ele("hiring", h_data, output_dict)

    attrition_rate = employee_data_full[
        (employee_data_full['active'] == False) & (employee_data_full['released_date']).gt(
            datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0)) &
        (employee_data_full['released_date']).lt(
            datetime.datetime.now().replace(day=num_days, hour=0, minute=0, second=0))]
    attrition_rate = round((attrition_rate.shape[0] / employee_data.shape[0] + attrition_rate.shape[0]) * 100, 2)
    dict_update_ele("attrition_rate", attrition_rate, output_dict)

    table = attendance_data[attendance_data['month'] == current_month][
        ['employee_id', 'employee_name', 'attendance', 'reason_of_absence', 'date']].rename(
        columns={'employee_id': 'emp_id', "employee_name": "emp_name"}).fillna("").to_dict("records")
    dict_update_ele("table", table, output_dict)
    return output_dict


def financial_tracker(financial_data=None, financial_field=None, current_year=None, previous_year=None,
                      current_month=None, financial_kpi=None):
    output_dict = {}

    fc_data = sum(
        list(financial_data[(financial_data['transaction_type'] == "Credit") &
                            (financial_data['year'] == current_year)]['amount_transacted'])) - sum(
        list(financial_data[(financial_data['transaction_type'] == "Debit") &
                            (financial_data['year'] == current_year)]['amount_transacted']))
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    fc_df1 = \
        financial_data[(financial_data["year"] == current_year) & (financial_data["transaction_type"] == 'Credit')][
            ["month", "amount_transacted", "transaction_type"]].groupby(["month"]).sum().reset_index()
    fc_df2 = financial_data[(financial_data["year"] == current_year) & (financial_data["transaction_type"] == 'Debit')][
        ["month", "amount_transacted"]].groupby(["month"]).sum().reset_index()
    fc_graph_df = fc_df1.set_index("month").subtract(fc_df2.set_index("month")).fillna(0).reset_index()
    fc_graph_df["month"] = pd.Categorical(fc_graph_df["month"], categories=months, ordered=True)
    fc_graph_df.sort_values(by="month", inplace=True)
    fc_graph = fc_graph_df.set_index("month").cumsum().reset_index().to_dict("records")
    fc_dict = {"total": fc_data, "graph": fc_graph}
    dict_update_ele("net_cash_flow", fc_dict, output_dict)

    rgr_cy = \
        financial_data[(financial_data["year"] == current_year) & (financial_data['transaction_type'] == 'Credit')][
            ['year', 'amount_transacted']].groupby('year').sum()['amount_transacted'][0]
    rgr_py = financial_data[
        (financial_data["year"] == previous_year) & (financial_data['transaction_type'] == 'Credit')][
        ['year', 'amount_transacted']].groupby('year').sum()['amount_transacted'][0]
    rgr = round(((rgr_cy - rgr_py) / rgr_py) * 100, 2)
    rgr_grph = financial_data[(financial_data['transaction_type'] == 'Credit')][
        ['year', 'amount_transacted']].groupby('year', as_index=False).sum().sort_values(['year'],
                                                                                         ascending=True).reset_index(
        drop=True).set_index("year").diff().fillna(0).reset_index().to_dict("records")
    rgr_dict = {"total": rgr, "graph": rgr_grph}
    dict_update_ele("Revenue_growth_rate", rgr_dict, output_dict)

    # gpm = financial_field[(financial_field['year'] == current_year)][
    #     ['year', 'net_income', 'current_assets', 'current_liabilities', 'revenue',
    #      'cost_of_goods_sold']].groupby('year', as_index=False).sum()
    # gpm_calc = round(((gpm['revenue'][0] - gpm['cost_of_goods_sold'][0]) / gpm['revenue'][0]) * 100, 2)
    # gpm_df1 = financial_field[['year', 'net_income', 'current_assets', 'current_liabilities', 'revenue',
    #                            'cost_of_goods_sold']].groupby('year', as_index=False).sum()
    # gpm_df1['data'] = round(((gpm_df1.revenue - gpm_df1.cost_of_goods_sold) / gpm_df1.revenue) * 100, 2)
    gpm = round_off(float(financial_kpi[(financial_kpi["year"] == current_year)]['gross_profit_margin']))
    gpm_value = pd.DataFrame(round(financial_kpi['gross_profit_margin'], 2)).rename(columns={'gross_profit_margin': 'data'})
    gpm_df = pd.concat([financial_kpi[['year']], gpm_value], axis=1).to_dict("records")
    gpm_dict = {"total": gpm, "graph": gpm_df}
    dict_update_ele("gross_profit_margin", gpm_dict, output_dict)

    npm = round_off(float(financial_kpi[(financial_kpi["year"] == current_year)]['net_profit_margin']))
    npm_value = pd.DataFrame(round(financial_kpi['net_profit_margin'], 2)).rename(columns={'net_profit_margin': 'npm_data'})
    npm_df = pd.concat([financial_kpi[['year']], npm_value], axis=1).to_dict("records")
    npm_dict = {"total": npm, "graph": npm_df}
    dict_update_ele("net_profit_margin", npm_dict, output_dict)

    # current_ratio = round((gpm['current_assets'][0] / gpm['current_liabilities'][0]) * 100, 2)
    # cr_gh = pd.DataFrame(round(financial_field['current_assets'] /
    #                            financial_field['current_liabilities'] * 100, 2))
    # grph_new = pd.concat([cr_gh, financial_field[['year']]], axis=1)
    # cr_graph = grph_new.rename(columns={0: 'data', 1: 'year'}).to_dict("records")
    current_ratio = round_off(float(financial_kpi[(financial_kpi["year"] == current_year)]['current_ratio']))
    cr_value = pd.DataFrame(round(financial_kpi['current_ratio'], 2)).rename(columns={'current_ratio': 'data'})
    cr_df = pd.concat([financial_kpi[['year']], cr_value], axis=1).to_dict("records")
    cr_dict = {"current_ratio": current_ratio, "graph": cr_df}
    dict_update_ele("current_ratio", cr_dict, output_dict)

    table_data = financial_data[(financial_data["year"] == current_year) &
                                (financial_data['month'] == current_month)][
        ['transaction', 'transaction_type', 'amount_transacted', 'transaction_date']].to_dict("records")
    # table_data = financial_kpi.to_dict("records")
    dict_update_ele("table", table_data, output_dict)

    return output_dict


def startup_metrics_screen(startup_fld=None, financial_data=None, startup_data_new=None, current_year=None,
                           previous_year=None, current_month=None):
    output_dict = {}

    active_cust = \
        startup_fld[startup_fld["year"] == current_year][['year', 'total_no_of_customer']].groupby("year").sum()[
            "total_no_of_customer"][0]
    active_cust_graph = startup_fld[['year', 'month', 'total_no_of_customer']].groupby('year',
                                                                                       as_index=False).sum().to_dict(
        "records")
    active_custmr = {"total": float(active_cust), "graph": active_cust_graph}
    dict_update_ele("active_customer", active_custmr, output_dict)

    mrr = float(sum(financial_data[
        (financial_data["month"] == current_month) & (financial_data['year'] == current_year) & (
                financial_data['transaction_type'] == 'Credit')]['amount_transacted']))
        # float(active_cust) * startup_fld[startup_fld["year"] == current_year]["annual_revenue_per_customer"].mean()
    mrr_df = startup_fld[startup_fld["year"] == current_year][
        ["month", "total_no_of_customer", "annual_revenue_per_customer"]]

    mrr_revenue = financial_data[(financial_data['transaction_type'] == 'Credit') &
                                      (financial_data["year"] == current_year)].groupby("month", as_index=False).sum()

    mrr_df["total_revenue"] = mrr_df.total_no_of_customer * mrr_revenue.amount_transacted
    mrr_graph = mrr_df[["month", "total_revenue"]].fillna(0).to_dict("records")
    mrr_dict = {"total": mrr, "graph": mrr_graph}
    dict_update_ele("MRR", mrr_dict, output_dict)

    arr = mrr * 12.0
    arr_df1 = financial_data[(financial_data['transaction_type'] ==
                              'Credit')][["year", "amount_transacted"]].groupby("year").mean().reset_index()
    df22 = startup_fld[["year", "total_no_of_customer"]].groupby("year").sum().reset_index()
    arr_df2 = pd.merge(df22, arr_df1)
    arr_df2['arr'] = (arr_df2.total_no_of_customer * arr_df2.amount_transacted * 12).apply(lambda x: round(x, 2))
    arr_graph = arr_df2[["year", "arr"]].fillna(0).to_dict("records")
    arr_dict = {"total": arr, "graph": arr_graph}
    dict_update_ele("Annual recurring revenue", arr_dict, output_dict)

    arpa = arr / active_cust
    arr_df2['arpa'] = arr_df2.arr / arr_df2.total_no_of_customer
    arpa_graph = arr_df2[["year", "arpa"]].fillna(0).to_dict("records")
    arpa_dict = {"total": arpa, "graph": arpa_graph}
    dict_update_ele("ARPA", arpa_dict, output_dict)

    gbr_value = startup_fld[startup_fld["year"] == current_year][
        ['year', "direct_expenses", "revenue"]].groupby("year").sum()
    gbr = (gbr_value.revenue - gbr_value.direct_expenses)[0]
    gbr_df1 = startup_fld[["year", "direct_expenses", "revenue"]].groupby("year").sum().reset_index()
    gbr_df1['data'] = gbr_df1.revenue - gbr_df1.direct_expenses
    gbr_graph = gbr_df1[["year", "data"]].to_dict("records")
    gbr_dict = {"total": float(gbr), "graph": gbr_graph}
    dict_update_ele("GBR", gbr_dict, output_dict)

    anr = startup_fld[startup_fld["year"] == current_year][['year', "revenue"]].groupby("year").sum().reset_index()[
              'revenue'][0] * 12
    gbr_df1['annual_run_rate'] = gbr_df1.revenue * 12
    anr_graph = gbr_df1[["year", "annual_run_rate"]].to_dict("records")
    anr_dict = {"total": float(anr), "graph": anr_graph}
    dict_update_ele("Annual run rate", anr_dict, output_dict)

    ch_rate_cy = int(
        startup_fld[startup_fld["year"] == current_year][['year', "total_no_of_customer"]].groupby("year").sum()[
            'total_no_of_customer'][0])
    ch_rate_py = int(
        startup_fld[startup_fld["year"] == previous_year][['year', "total_no_of_customer"]].groupby("year").sum()[
            'total_no_of_customer'][0])
    churn_rate = round_off(ch_rate_cy / ch_rate_py)
    dict_update_ele("Churn_rate", churn_rate, output_dict)

    cust_cent_risk = financial_data[
        (financial_data["month"] == current_month) & (financial_data['year'] == current_year) & (
                financial_data['transaction_type'] == 'Credit')].sort_values("amount_transacted",
                                                                             ascending=False).head(1)[
        'amount_transacted'].tolist()[0]
    cust_total_rev = int(financial_data[
                             (financial_data["month"] == current_month) & (financial_data['year'] == current_year) & (
                                     financial_data['transaction_type'] == 'Credit')].sort_values(
        "amount_transacted", ascending=False)['amount_transacted'].sum())
    try:
        cust_data = round_off((cust_cent_risk / cust_total_rev) * 100)
    except:
        cust_data = 0
    dict_update_ele("customer_concentration_risk", cust_data, output_dict)

    table_data = [startup_data_new]
    dict_update_ele("Table", table_data, output_dict)

    return output_dict


def marketing_screen(marketing_dt=None, marketing_fld=None, current_year=None, current_month=None,
                     value=None):
    output_dict = {}
    mark_grph = marketing_fld[(marketing_fld["month"] == current_month) &
                              (marketing_fld['year'] == current_year)]
    markting_fld = marketing_fld[(marketing_fld["month"] == current_month) &
                                 (marketing_fld['year'] == current_year)].groupby(by=['month'], as_index=True).last()
    # .groupby('month').sum()).reset_index(), .tail(1)
    wb_visit = int(markting_fld['website_traffic'])
    dict_update_ele("visitors_traffic", wb_visit, output_dict)
    tf_source = markting_fld['traffic_sources'].to_dict()[current_month]
    dict_update_ele("traffic_sources", tf_source, output_dict)
    b_rate = float(markting_fld['bounce_rate'])
    dict_update_ele("bounce_rate", b_rate, output_dict)
    ltb = round_off(len(mark_grph) / (wb_visit+0.001))
    dict_update_ele("look_to_book", ltb, output_dict)
    ubd = markting_fld['users_per_device'].to_dict()[current_month]
    dict_update_ele("users_by_device", ubd, output_dict)
    demo_count = len(mark_grph)
    dict_update_ele("demo_count", demo_count, output_dict)
    e_chart = {"email_bounce": int(markting_fld['email_bounce']),
               "email_success_rate": int(markting_fld['email_successfully_delivered'])}
    dict_update_ele("email_scs_rate", e_chart, output_dict)
    esr = {"open_rate": int(markting_fld['open_rate']),
           "click_rate": int(markting_fld['click_rate']),
           "reply_rate": int(markting_fld['reply_rate'])}
    dict_update_ele("multi_rates", esr, output_dict)

    demo_graph_data = mark_grph[['demo_date', 'demo_client', 'demo_product']].to_dict("records")
    dict_update_ele("demo_graph", demo_graph_data, output_dict)
    # web_traf = {"no_of_users": wb_visit,
    #            "sessions": markting_fld['average_session_duration'][value],
    #            "page_views": int(markting_fld['page_views'][value])}
    website_graph = marketing_fld[['month', 'year', 'website_traffic',
                                   'page_views', 'average_session_duration']].to_dict("records")
    dict_update_ele("website_graph", website_graph, output_dict)

    return output_dict


def month_convertor(previous=None, current_month=None, current_year=None):
    current_date = current_month + current_year

    if previous:
        current_new = (datetime.datetime.strptime(current_date, "%b%Y") - relativedelta(months=1))
        previous_new = (datetime.datetime.strptime(current_date, "%b%Y") - relativedelta(months=2))

        current_month = current_new.strftime("%b")
        previous_month = previous_new.strftime("%b")
        current_year = current_new.strftime("%Y")
        previous_year = (previous_new - relativedelta(years=1)).strftime("%Y")
    else:
        previous_month = (datetime.datetime.strptime(current_date, "%b%Y") - relativedelta(months=1)).strftime("%b")
        previous_year = (datetime.datetime.strptime(current_date, "%b%Y") - relativedelta(years=1)).strftime("%Y")

    month_dt = datetime.datetime.strptime(current_month, '%b')
    month = month_dt.month
    yr_dt = datetime.datetime.strptime(current_year, '%Y')
    year = yr_dt.year
    num_days = calendar.monthrange(year, month)[1]

    return current_month, current_year, previous_month, previous_year, num_days


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004)
