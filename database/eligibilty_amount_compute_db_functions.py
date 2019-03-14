from database import db_utils
import logging
from pymongo import ReturnDocument
import json
from dateutil.parser import parse
from datetime import datetime
from datetime import timedelta

__logger = logging.getLogger(__name__)


def __is_empty(any_structure):
    if any_structure:
        return False
    else:
        return True


def get_bus_bank_stmt_ids(loan_app_id):
    db = db_utils.get_db_object('cas_db')
    cas_loan_app = db["cas_loan_application"]
    # cas_bank_stmt = db["cas_bank_statement"]

    bus_id = cas_loan_app.find_one({"loan_application_id": loan_app_id}, {"_id": 0, "business_id": 1})
    # bank_stmt_id = cas_bank_stmt.find_one({"loan_application_id": loan_app_id}, {"_id": 0, "bank_stmt_id": 1})

    # return bus_id["business_id"], bank_stmt_id["bank_stmt_id"]
    return bus_id["business_id"]


def get_avg_sales_and_repayments(loan_application_id):
    db = db_utils.get_db_object('cas_db')
    # cas_bank_6_mon_anlysis = db["cas_business_bank_analysis_rules_last_6_month_analysis"]
    # data = cas_bank_6_mon_anlysis.find({"loan_application_id": loan_application_id}, {"_id": 0})
    #
    # # If data not present in the DB, default value gets stored as zero
    # pos_sales = ecom_sales = repayments = 0
    #
    # if not __is_empty(data):
    #     for item in data:
    #         if item["item_header"] == "POS Sales":
    #             pos_sales = item["mean"]
    #         if item["item_header"] == "eCommerce Sales":
    #             ecom_sales = item["mean"]
    #         if item["item_header"] == "Loan Repayments":
    #             repayments = item["mean"]
    #
    #     return (pos_sales + ecom_sales), repayments
    # else:
    #     return "Analysis data does not exists for the given loan application"

    cas_loan_app = db["cas_loan_application"]
    loan_app = cas_loan_app.find_one({"loan_application_id": loan_application_id}, {"_id": 0})

    if "created_at_pretty" in loan_app:
        loan_application_date = parse(loan_app["created_at_pretty"])
    else:
        loan_application_date = datetime.today()

    cas_bank_mon_analysis = db["cas_business_bank_analysis_rules_monthly_analysis"]
    result = cas_bank_mon_analysis.aggregate([{"$match": {"loan_application_id": loan_application_id,
                                                          "item_header": {"$in": ["eCommerce Sales", "POS Sales"]}}},
                                              {"$group": {
                                                  "_id": "$value_date",
                                                  "total_sum": {"$sum": "$sum"},
                                                  "total_count": {"$sum": "$count"}
                                              }
                                              }]
                                             )
    result = db_utils.get_dict_from_cursor(result)
    monthly_collections_6_mon = []
    if len(result) > 0:
        result = [x for x in result if parse(x["_id"]) < loan_application_date]
        result = sorted(result, key=lambda k: parse(k["_id"]).strftime("%Y-%m"))
        # On the above ascending ordered set, ignore the last month. Take six months from last but one month onwards.
        monthly_collections_6_mon = result[-7:-1]

    result = cas_bank_mon_analysis.aggregate([{"$match": {"loan_application_id": loan_application_id,
                                                          "item_header": {"$in": ["Loan Repayments"]}}},
                                              {"$group": {
                                                  "_id": "$value_date",
                                                  "total_sum": {"$sum": "$sum"},
                                                  "total_count": {"$sum": "$count"}
                                              }
                                              }]
                                             )
    result = db_utils.get_dict_from_cursor(result)
    monthly_emi_6_mon = []
    if len(result) > 0:
        result = [x for x in result if parse(x["_id"]) < loan_application_date]
        result = sorted(result, key=lambda k: parse(k["_id"]).strftime("%Y-%m"))
        # On the above ascending ordered set, ignore the last month. Take six months from last but one month onwards.
        monthly_emi_6_mon = result[-7:-1]

    average_monthly_emi = 0
    if not __is_empty(monthly_emi_6_mon):
        total_six_month_emi = 0
        count_months = 0
        for record in monthly_emi_6_mon:
            if "total_sum" in record and record["total_sum"]:
                total_six_month_emi += record["total_sum"]
                count_months += 1

        if count_months == 0:
            average_monthly_emi = 0
        else:
            average_monthly_emi = total_six_month_emi / count_months

    average_monthly_sales = 0
    if not __is_empty(monthly_collections_6_mon):
        total_six_month_sales = 0
        count_months = 0
        for record in monthly_collections_6_mon:
            if "total_sum" in record and record["total_sum"]:
                total_six_month_sales += record["total_sum"]
                count_months += 1

        if count_months == 0:
            average_monthly_sales = 0
        else:
            average_monthly_sales = total_six_month_sales / count_months

    return average_monthly_sales, average_monthly_emi


def get_margin(bus_id):
    db = db_utils.get_db_object('cas_db')
    cas_bus = db["cas_business"]
    cas_bus_cat = db["cas_business_category"]
    bus_cat_code = cas_bus.find_one({"business_id": bus_id}, {"_id": 0, "business_category_code": 1})
    margin = cas_bus_cat.find_one({"business_category_code": bus_cat_code["business_category_code"]},
                                  {"_id": 0, "margin": 1})

    return margin["margin"]


def compute_costs(bus_id):
    db = db_utils.get_db_object('cas_db')
    cas_bus = db["cas_business"]
    bus_details = cas_bus.find_one({"business_id": bus_id}, {"_id": 0})

    # If data not present in the DB, default value gets stored as zero
    emp_cost = 0
    rental_cost = 0
    other_expenses = 0

    if "no_of_employees" and "cost_per_employee" in bus_details:
        emp_cost = (bus_details["no_of_employees"] * bus_details["cost_per_employee"])

    if "no_of_offline_stores" and "rental_cost_per_shop" in bus_details:
        rental_cost = (bus_details["no_of_offline_stores"] * bus_details["rental_cost_per_shop"])

    if "other_expenses" in bus_details:
        other_expenses = bus_details["other_expenses"]

    return emp_cost, rental_cost, other_expenses


def push_eligibilty_details_database(loan_app_id, mongo_item):
    db = db_utils.get_db_object('cas_db')
    cas_bus_elgy_compute = db["cas_business_eligibility_computations"]
    result = cas_bus_elgy_compute.find_one_and_update(
        {"loan_application_id": loan_app_id},
        {"$set": mongo_item},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    __logger.info(json.dumps(result, indent=4, sort_keys=True, default=str))
    if not __is_empty(result):
        return "done"
