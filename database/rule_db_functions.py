import logging
import json
import pymongo
from dateutil.parser import parse
from datetime import datetime
from datetime import timedelta
from database import db_utils
from functions import get_bus_exp_in_months, get_applicant_age, get_growth_qoq, get_growth_mom, get_overdue_status, \
    get_write_off_status, \
    get_qoq_growth_banking, get_mom_growth_banking, get_avg_eod_balance

# db = db_utils.get_db_object('workflow_db')
__logger = logging.getLogger(__name__)


def __is_empty(any_structure):
    if any_structure:
        return False
    else:
        return True


def get_a_rule(rule_name, org_name=None):
    """

    :param org_name:
    :param rule_name:
    :return:
    """
    __db_cas = db_utils.get_db_object('cas_db')
    cas_rules_repo = __db_cas['cas_rules_repository']

    results = None
    if org_name:
        results = cas_rules_repo.find_one(
            {
                "rule_name": rule_name,
                "org_name": org_name
            },
            {
                "_id": 0
            }
        )

    if results:
        return results
    else:
        results = cas_rules_repo.find_one(
            {
                "rule_name": rule_name,
                "org_name": "All"
            },
            {
                "_id": 0
            }
        )
        return results


def get_eligibility_criteria_list(module_name):
    __db_cas = db_utils.get_db_object('cas_db')
    cas_rules_repo = __db_cas['cas_rules_repository']
    eligibility_list = []
    results = cas_rules_repo.find(
        {
            "rule_description": "eligibility_criteria",
            "module_name": module_name
        },
        {"_id": 0}
    )
    eligibility_list = db_utils.get_dict_from_cursor(results)

    return eligibility_list


def get_cibil_score(loan_app_id):
    # DB and collection definitions
    db_cas = db_utils.get_db_object('cas_db')
    cas_loan_app = db_cas["cas_loan_application"]
    cas_cibil_resp = db_cas["cas_bus_partner_cibil_response"]
    cas_business = db_cas["cas_business"]

    # Fetching business details and cibil score
    loan_app = cas_loan_app.find_one({"loan_application_id": loan_app_id}, {"_id": 0})

    if "created_at_pretty" in loan_app:
        loan_application_date = parse(loan_app["created_at_pretty"])
        cibil_max_date = loan_application_date + timedelta(days=30)
    else:
        loan_application_date = datetime.today()
        cibil_max_date = datetime.today()

    consumer_cibil_score = -1
    business_partners = cas_business.find_one({"business_id": loan_app["business_id"]},
                                              {"_id": 0, "business_partners": 1})

    if not __is_empty(business_partners) and "business_partners" in business_partners:
        for partner in business_partners["business_partners"]:
            if partner["main_applicant"] == "Y":
                __logger.info("business id:" + loan_app["business_id"])
                __logger.info("partner pan:" + partner["pan_no"])

                cibil_data = cas_cibil_resp.find(
                    {
                        "business_id": loan_app["business_id"],
                        "business_partner_pan": partner["pan_no"],
                        "cibil_pull_date": {"$lte": str(cibil_max_date)}
                    },
                    {"_id": 0}
                ).sort([("cibil_pull_date", pymongo.DESCENDING)]).limit(1)

                cibil_data = db_utils.get_dict_from_cursor(cibil_data)
                # __logger.info(json.dumps(cibil_data, indent=4, sort_keys=True, default=str))

                if not __is_empty(cibil_data):
                    for record in cibil_data:
                        if "Score" in record:
                            for score in record["Score"]:
                                if "Score" in score:
                                    cibil_score = str(score["Score"])
                                    __logger.info("cibil score:" + cibil_score)
                                    if cibil_score.isdigit():
                                        consumer_cibil_score = int(score["Score"])
                                    else:
                                        consumer_cibil_score = -1
                                    # If a cibil score is obtained, get out of the loop
                                    break

    return consumer_cibil_score


def get_org_name(loan_app_id):
    """
    Fetch organization name for a loan application.
    :param loan_app_id:
    :return:
    """
    org_name = None
    db_cas = db_utils.get_db_object('cas_db')
    cas_loan_app = db_cas["cas_loan_application"]
    loan_app_record = cas_loan_app.find_one({"loan_application_id": loan_app_id}, {"org_name": 1})
    if loan_app_record and "org_name" in loan_app_record:
        org_name = loan_app_record["org_name"]

    return org_name


def get_org_name_scf(invoice_id):
    """
    Fetch organization name for an invoice.
    :param invoice_id:
    :return:
    """
    org_name = None
    db_cas = db_utils.get_db_object('cas_db')
    scf_invoice = db_cas["scf_invoice"]
    invoice_record = scf_invoice.find_one({"invoice_id": invoice_id}, {"org_name": 1})
    if invoice_record and "org_name" in invoice_record:
        org_name = invoice_record["org_name"]

    return org_name


def get_org_preferences(org_name):
    """

    :param org_name:
    :return:
    """
    db_cas = db_utils.get_db_object('cas_db')
    cas_organization = db_cas["cas_organization"]
    org_record = cas_organization.find_one({"org_name": org_name}, {"_id": 0})
    return org_record


def get_element_values(loan_app_id):
    # Definitions
    fact = {}
    partner_data = {}

    db_cas = db_utils.get_db_object('cas_db')
    cas_business = db_cas["cas_business"]
    cas_loan_app = db_cas["cas_loan_application"]
    cas_bus_partner_cibil_analysis = db_cas["cas_bus_partner_cibil_analysis"]
    cas_bank_stmt_txns_tat_analysis = db_cas["cas_business_bank_statement_txns_total_segment_analysis"]
    cas_bank_stmt_6_mo_analysis = db_cas["cas_business_bank_analysis_rules_last_6_month_analysis"]
    cas_bank_stmt_3_mo_analysis = db_cas["cas_business_bank_analysis_rules_last_3_month_analysis"]
    cas_plat_analysis = db_cas["cas_business_platform_analysis"]
    cas_bus_plat = db_cas["cas_business_platform"]
    cas_bank_stmt_txns_bucket_analysis = db_cas["cas_business_bank_statement_txns_bucket_analysis"]
    cas_bank_mon_analysis = db_cas["cas_business_bank_analysis_rules_monthly_analysis"]
    cas_bank_quarterly_analysis = db_cas["cas_business_bank_analysis_rules_quarterly_analysis"]
    cas_bank_stmt_txns_mon_analysis = db_cas["cas_business_bank_statement_txns_monthly_analysis"]

    # Fetching data for fetching rule elements
    loan_application = cas_loan_app.find_one({"loan_application_id": loan_app_id}, {"_id": 0, "business_id": 1, "created_at_pretty": 1})
    business_elements = cas_business.find_one({"business_id": loan_application["business_id"]}, {"_id": 0})

    if "created_at_pretty" in loan_application:
        loan_application_date = parse(loan_application["created_at_pretty"])
        cibil_max_date = loan_application_date + timedelta(days=30)
    else:
        loan_application_date = datetime.today()
        cibil_max_date = datetime.today()

        # __logger.info(json.dumps(business_elements, indent=4, sort_keys=True, default=str))

    cibil_analysis_data = []
    cibil_analysis_record = {}
    if not __is_empty(business_elements) and "business_partners" in business_elements:
        for partner in business_elements["business_partners"]:
            if partner["main_applicant"] == "Y":
                cibil_data = cas_bus_partner_cibil_analysis.find(
                    {
                        "business_id": loan_application["business_id"],
                        "business_partner_pan": partner["pan_no"],
                        "cibil_pull_date": {"$lte": str(cibil_max_date)}
                    },
                    {"_id": 0}
                ).sort([("cibil_pull_date", pymongo.DESCENDING)]).limit(1)

                cibil_analysis_data = db_utils.get_dict_from_cursor(cibil_data)
                break

    if not __is_empty(cibil_analysis_data):
        for cibil_analysis in cibil_analysis_data:
            cibil_analysis_record = cibil_analysis
            break

    # bank_stmt_id = cas_bank_stmt.find_one({"loan_application_id": loan_app_id}, {"_id": 0, "bank_stmt_id": 1})
    anchor_elements = cas_plat_analysis.find_one({"loan_application_id": loan_app_id}, {"_id": 0})
    cheq_bounces_6_mon = cas_bank_stmt_6_mo_analysis.find_one({"loan_application_id": loan_app_id,
                                                               "item_header": "Cheque Bounces – Inward"},
                                                              {"_id": 0, "count": 1})

    # The queries have been changed to pick from monthly analytics collections and pick last n data ignoring the
    # latest month. six_monthly_avg_collection = cas_bank_stmt_6_mo_analysis.find({"loan_application_id":
    # loan_app_id, "item_header": { "$in": ["eCommerce Sales", "POS Sales"]}}, {"_id": 0, "sum": 1})

    result = cas_bank_mon_analysis.aggregate([{"$match": {"loan_application_id": loan_app_id,
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
        result = sorted(result, key=lambda k: parse(k["_id"]).strftime("%Y-%m"))
        result = [x for x in result if parse(x["_id"]) < loan_application_date]
        # On the above ascending ordered set, ignore the last month. Take six months from last but one month onwards.
        monthly_collections_6_mon = result[-7:-1]

    result = cas_bank_mon_analysis.aggregate([{"$match": {"loan_application_id": loan_app_id,
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
        result = sorted(result, key=lambda k: parse(k["_id"]).strftime("%Y-%m"))
        result = [x for x in result if parse(x["_id"]) < loan_application_date]
        # On the above ascending ordered set, ignore the last month. Take six months from last but one month onwards.
        monthly_emi_6_mon = result[-7:-1]

    # monthly_avg_emi_6_mon = cas_bank_stmt_6_mo_analysis.find_one({"loan_application_id": loan_app_id,
    #                                                               "item_header": "Loan Repayments"},
    #                                                              {"_id": 0, "mean": 1})

    # This is handled in monthly_collections_6_mon query.
    # plat_credits = cas_bank_stmt_6_mo_analysis.find({"loan_application_id": loan_app_id,
    #                                                  "item_header": {"$in": ["eCommerce Sales", "POS Sales"]}},
    #                                                 {"_id": 0, "count": 1})
    #
    # plat_credits = db_utils.get_dict_from_cursor(plat_credits)

    cheq_bounces_3_mon = cas_bank_stmt_3_mo_analysis.find_one({"loan_application_id": loan_app_id,
                                                               "item_header": "Cheque Bounces – Inward"},
                                                              {"_id": 0, "count": 1})

    online_platforms = cas_bank_stmt_txns_tat_analysis.find_one(
        {"business_id": loan_application["business_id"], "loan_application_id": loan_app_id,
         "item_header": {"$in": ["eCommerce Sales", "POS Sales"]}}, {"_id": 0, "count": 1})

    platform_elements = cas_bus_plat.find_one({"business_id": loan_application["business_id"]}, {"_id": 0})

    # Query deprecated. Minimum and Maximum collections across 6 months is derived from monthly_collections_6_mon
    # mon_analysis_data = cas_bank_mon_analysis.aggregate([
    #     {"$match": {"loan_application_id": loan_app_id, "item_header": {"$in": ["eCommerce Sales", "POS Sales"]}}},
    #     {"$group": {
    #         "_id": None,
    #         "average_min": {"$avg": "$min"},
    #         "average_max": {"$avg": "$max"}
    #     }
    #     }
    # ])

    online_platforms_bucket_count = cas_bank_stmt_txns_bucket_analysis.find(
        {"loan_application_id": loan_app_id, "item_header": {"$in": ["eCommerce Sales"]}},
        {"_id": 0, "bucket_name": 1}).count()

    # monthly_collections_6_mon is being used to get qoq growth
    # banking_qoq_growth = cas_bank_quarterly_analysis.aggregate([
    #     {"$match": {"loan_application_id": loan_app_id, "item_header": {"$in": ["eCommerce Sales", "POS Sales"]}}},
    #     {"$group": {
    #         "_id": "$value_date",
    #         "total_sum": {"$sum": "$sum"}
    #     }
    #     }
    # ])

    # monthly_collections_6_mon is being used to get mom growth
    # banking_mom_growth = cas_bank_mon_analysis.aggregate([
    #     {"$match": {"loan_application_id": loan_app_id, "item_header": {"$in": ["eCommerce Sales", "POS Sales"]}}},
    #     {"$group": {
    #         "_id": "$value_date",
    #         "total_sum": {"$sum": "$sum"}
    #     }
    #     }
    # ])

    result = cas_bank_stmt_txns_mon_analysis.aggregate([
        {"$match": {"loan_application_id": loan_app_id}},
        {"$group": {
            "_id": "$value_date",
            "total_sum": {"$sum": "$sum"},
            "total_count": {"$sum": "$count"}
        }
        }
    ])
    result = db_utils.get_dict_from_cursor(result)
    monthly_balance_six_months = []
    if len(result) > 0:
        result = sorted(result, key=lambda k: parse(k["_id"]).strftime("%Y-%m"))
        result = [x for x in result if parse(x["_id"]) < loan_application_date]
        # On the above ascending ordered set, ignore the last month. Take six months from last but one month onwards.
        monthly_balance_six_months = result[-7:-1]

    # Manipulate the data fetched from the collections and assign the values to rule elements
    if not __is_empty(business_elements):
        # industry_score
        if "annual_turnover" in business_elements:
            fact["business_size_in_lacs"] = business_elements["annual_turnover"]
        if "business_category_code" in business_elements:
            fact["business_category"] = business_elements["business_category_code"]

        # business_score
        if "operating_type_code" in business_elements:
            fact["constitution"] = business_elements["operating_type_code"]
        if "business_ownership" in business_elements:
            fact["business_premises_ownership"] = business_elements["business_ownership"]
        if "bank_od_cc_limit" in business_elements:
            fact["has_od_cc_limit"] = business_elements["bank_od_cc_limit"]
        if "no_of_employees" in business_elements:
            fact["no_of_employees"] = business_elements["no_of_employees"]
        if "operating_since_year" and "operating_since_month" in business_elements:
            fact["business_exp_in_mnths"] = get_bus_exp_in_months(business_elements["operating_since_year"],
                                                                  business_elements["operating_since_month"])
        # To be re-looked later
        fact["cost_per_employee"] = 10000.0
        fact['total_employee_cost'] = int(fact["no_of_employees"] ) * fact["cost_per_employee"]

    if not __is_empty(platform_elements) and "onBoarded_since" in platform_elements and \
            not __is_empty(platform_elements["onBoarded_since"]):

        onboarded_year = str(platform_elements["onBoarded_since"][:4])
        onboarded_month = str(platform_elements["onBoarded_since"][-2:])

        if onboarded_year.isdigit() and onboarded_month.isdigit():
            fact["no_of_months_on_platform"] = get_bus_exp_in_months(
                platform_elements["onBoarded_since"][:4],
                platform_elements["onBoarded_since"][-2:]
            )

    # management_score
    if "business_partners" in business_elements:
        for partner in business_elements["business_partners"]:
            if partner["main_applicant"] == "Y":
                partner_data = partner
        if "educational_qualification" in partner_data:
            fact["qualification"] = partner_data["educational_qualification"]
        if "marital_status" in partner_data:
            fact["marital_status"] = partner_data["marital_status"]
        if "residence_ownership" in partner_data:
            fact["residence_ownership"] = partner_data["residence_ownership"]
        if "date_of_birth" in partner_data:
            fact["applicant_age"] = get_applicant_age(partner_data["date_of_birth"])

    if not __is_empty(cibil_analysis_record) and "Scoring" in cibil_analysis_record:
        # cb_score/leverage
        if "credit_card_usage_total_limits_ratio" in cibil_analysis_record["Scoring"]:
            fact["ccusage/total_active_cclmts"] = (cibil_analysis_record["Scoring"][
                "credit_card_usage_total_limits_ratio"]) / 100
        if "amt_overdue_total_liabilities_ratio" in cibil_analysis_record["Scoring"]:
            fact["amt_overdue/total_liabilities"] = (cibil_analysis_record["Scoring"][
                "amt_overdue_total_liabilities_ratio"]) / 100
        if "no_acs_overdue_total_accounts_ratio" in cibil_analysis_record["Scoring"]:
            fact["no_accts_overdue/total_active_accts"] = (cibil_analysis_record["Scoring"][
                "no_acs_overdue_total_accounts_ratio"]) / 100
        if "amt_written_off_total_liabilities_ratio" in cibil_analysis_record["Scoring"]:
            fact["amt_w_off_total_liabilities"] = (cibil_analysis_record["Scoring"][
                "amt_written_off_total_liabilities_ratio"]) / 100
        if "no_acs_written_off_total_liabilities_ratio" in cibil_analysis_record["Scoring"]:
            fact["no_of_loans_w_off_total_accts"] = (cibil_analysis_record["Scoring"][
                "no_acs_written_off_total_liabilities_ratio"]) / 100

        # cb_score/loans_volume
        if "no_of_running_bl_pl" in cibil_analysis_record["Scoring"]:
            fact["no_of_running_bl_pl"] = cibil_analysis_record["Scoring"]["no_of_running_bl_pl"]
        if "last_loan_drawn_in_months" in cibil_analysis_record["Scoring"]:
            fact["last_loan_drawn_in_months"] = cibil_analysis_record["Scoring"]["last_loan_drawn_in_months"]
        if "no_of_bl_paid_off" in cibil_analysis_record["Scoring"]:
            fact["no_of_bl_paid_off_successfully"] = cibil_analysis_record["Scoring"]["no_of_bl_paid_off"]
        if "amt_bl_paid_off" in cibil_analysis_record["Scoring"]:
            fact["value_of_bl_paid_successfully"] = cibil_analysis_record["Scoring"]["amt_bl_paid_off"]

    if not __is_empty(cibil_analysis_record) and "Enquiry" in cibil_analysis_record:
        if "no_of_enquiries_last_3_months" in cibil_analysis_record["Enquiry"]:
            fact["bl_loans_last_3months_enqy"] = (cibil_analysis_record["Enquiry"][
                "no_of_enquiries_last_3_months"]) / 100

        if "no_of_enquiries_last_12_months" in cibil_analysis_record["Enquiry"]:
            fact["bl_loans_last_12months_enqy"] = (cibil_analysis_record["Enquiry"][
                "no_of_enquiries_last_12_months"]) / 100

    # emi to total collections ratio
    average_monthly_emi = 0
    count_months = 0
    if not __is_empty(monthly_emi_6_mon):
        total_six_month_emi = 0
        for record in monthly_emi_6_mon:
            if "total_sum" in record and record["total_sum"]:
                total_six_month_emi += record["total_sum"]
                count_months += 1

        if count_months == 0:
            average_monthly_emi = 0
        else:
            average_monthly_emi = total_six_month_emi / count_months
        fact["count_months_emi"] = count_months

    average_monthly_sales = 0
    count_months = 0
    if not __is_empty(monthly_collections_6_mon):
        total_six_month_sales = 0
        for record in monthly_collections_6_mon:
            if "total_sum" in record and record["total_sum"]:
                total_six_month_sales += record["total_sum"]
                count_months += 1

        if count_months == 0:
            average_monthly_sales = 0
        else:
            average_monthly_sales = total_six_month_sales / count_months

    fact["average_monthly_emi"] = average_monthly_emi
    fact["average_monthly_sales"] = average_monthly_sales
    fact["count_months_sales"] = count_months

    if average_monthly_sales == 0:
        fact["emi/total_collections_in_percentage"] = 0
    else:
        fact["emi/total_collections_in_percentage"] = average_monthly_emi / average_monthly_sales

    # Banking_score - inward_cheque_bounces_in_6_months
    if not __is_empty(cheq_bounces_6_mon) and "count" in cheq_bounces_6_mon:
        fact["inward_cheque_bounces_in_6months"] = cheq_bounces_6_mon["count"]
    else:
        fact["inward_cheque_bounces_in_6months"] = 0

    if not __is_empty(cheq_bounces_3_mon) and "count" in cheq_bounces_3_mon:
        fact["inward_cheque_bounces_in_3months"] = cheq_bounces_3_mon["count"]
    else:
        fact["inward_cheque_bounces_in_3months"] = 0

    if not __is_empty(online_platforms) and "no_of_online_platforms" in online_platforms:
        fact["no_of_online_platforms"] = online_platforms["count"]

    # Banking_score - performance_ratios
    __logger.info("Monthly collections for last 6 months")
    __logger.info(json.dumps(monthly_collections_6_mon, indent=4, sort_keys=True, default=str))
    if not __is_empty(monthly_collections_6_mon):
        fact["txn_value_growth_qoq_cq_pq"] = get_qoq_growth_banking(monthly_collections_6_mon)
    if not __is_empty(monthly_collections_6_mon):
        fact["txn_value_growth_mom_cm_pm"] = get_mom_growth_banking(monthly_collections_6_mon)

    # txn_value_variance_momin_momax
    if not __is_empty(monthly_collections_6_mon):
        min_coll_six_months = None
        max_coll_six_months = None
        for item in monthly_collections_6_mon:
            if "total_sum" in item and item["total_sum"]:
                if min_coll_six_months:
                    if item["total_sum"] < min_coll_six_months:
                        min_coll_six_months = item["total_sum"]
                else:
                    min_coll_six_months = item["total_sum"]

                if max_coll_six_months:
                    if item["total_sum"] > max_coll_six_months:
                        max_coll_six_months = item["total_sum"]
                else:
                    max_coll_six_months = item["total_sum"]

            fact["min_coll_six_months"] = min_coll_six_months
            fact["max_coll_six_months"] = max_coll_six_months
            if max_coll_six_months is not None:
                if max_coll_six_months <= 0:
                    fact["txn_value_variance_momin_momax"] = 0
                elif max_coll_six_months > 0:
                    fact["txn_value_variance_momin_momax"] = min_coll_six_months / max_coll_six_months

    fact["annual_transc_value"] = 0
    fact["total_six_month_sales"] = 0
    if not __is_empty(monthly_collections_6_mon):
        total_six_month_sales = 0
        for record in monthly_collections_6_mon:
            if "total_sum" in record and record["total_sum"]:
                total_six_month_sales += record["total_sum"]
        fact["annual_transc_value"] = total_six_month_sales * 2
        fact["total_six_month_sales"] = total_six_month_sales

    fact["no_of_online_platforms"] = online_platforms_bucket_count

    avg_eod_balance = get_avg_eod_balance(monthly_balance_six_months, "total_sum", "total_count")
    fact["avg_eod_bal"] = avg_eod_balance

    fact["avg_eod_bal_or_online_credits"] = 0
    if not __is_empty(average_monthly_sales) and not __is_empty(avg_eod_balance):
        if average_monthly_sales == 0:
            fact["avg_eod_bal_or_online_credits"] = 0
        else:
            fact["avg_eod_bal_or_online_credits"] = avg_eod_balance / average_monthly_sales

    if not __is_empty(monthly_collections_6_mon):
        platform_credits_count = 0
        count_of_months = 0
        for record in monthly_collections_6_mon:
            if "total_count" in record and record["total_count"]:
                platform_credits_count += record["total_count"]
                count_of_months += 1

        if count_of_months == 0:
            fact["no_of_platform_credits_in_months"] = 0
        else:
            fact["no_of_platform_credits_in_months"] = (platform_credits_count / count_of_months)
    else:
        fact["no_of_platform_credits_in_months"] = 0

        # anchor_score
    if not __is_empty(anchor_elements):
        if "growth_quarterly" in anchor_elements:
            fact["txn_value_growth_qoq_cq/pq"] = get_growth_qoq(anchor_elements["growth_quarterly"])
        if "growth_monthly" in anchor_elements:
            fact["txn_value_growth_mom_cq/pq"] = get_growth_mom(anchor_elements["growth_monthly"])
        if "txn_value_variance" in anchor_elements:
            fact["txn_value_variance_monthly_min/monthly_max"] = anchor_elements["txn_value_variance"]
        if "annual_transaction" in anchor_elements:
            fact["annual_transaction"] = anchor_elements["annual_transaction"]

    return fact


def get_criteria_element_values(loan_app_id):
    # DB and collection definitions
    fact = {}
    db_cas = db_utils.get_db_object('cas_db')
    cas_business = db_cas["cas_business"]
    cas_loan_app = db_cas["cas_loan_application"]
    cas_bank_stmt = db_cas["cas_bank_statement"]
    cas_business_platform = db_cas["cas_business_platform"]
    cas_cibil_resp = db_cas["cas_bus_partner_cibil_response"]
    cas_cibil_analysis = db_cas["cas_bus_partner_cibil_analysis"]
    cas_bank_3_mon_analysis = db_cas["cas_business_bank_analysis_rules_last_3_month_analysis"]
    cas_bank_mon_analysis = db_cas["cas_business_bank_analysis_rules_monthly_analysis"]
    cas_bank_eod_bal_analysis = db_cas["cas_business_bank_eod_balance_analysis"]

    # Fetching data
    loan_application = cas_loan_app.find_one({"loan_application_id": loan_app_id}, {"_id": 0, "business_id": 1, "created_at_pretty": 1})
    # bank_stmt_id = cas_bank_stmt.find_one({"loan_application_id": loan_app_id}, {"_id": 0, "bank_stmt_id": 1})

    if "created_at_pretty" in loan_application:
        loan_application_date = parse(loan_application["created_at_pretty"])
        cibil_max_date = loan_application_date + timedelta(days=30)
    else:
        loan_application_date = datetime.today()
        cibil_max_date = datetime.today()

    org_name = cas_loan_app.find_one({"loan_application_id": loan_app_id}, {"_id": 0, "org_name": 1})
    business_vintage = cas_business.find_one({"business_id": loan_application["business_id"]},
                                             {"_id": 0, "operating_since_month": 1, "operating_since_year": 1})
    online_sales_vintage = cas_business_platform.find_one(
        {"business_id": loan_application["business_id"], "org_name": org_name["org_name"]},
        {"_id": 0, "onBoarded_since": 1})
    # Fetching business_ownership - cas_business
    business_ownership = cas_business.find_one({"business_id": loan_application["business_id"]},
                                               {"_id": 0, "business_ownership": 1})

    # Fetching cibil_data - cas_cibil_response

    # Fetching cibil analysis data
    # cibil_analysis_data = cas_cibil_analysis.find({"business_id": bus_id["business_id"]}, {"_id": 0}).sort(
    #     'cibil_pull_date', pymongo.DESCENDING)
    #
    # cibil_analysis_data = db_utils.get_dict_from_cursor(cibil_analysis_data)

    fact["consumer_cibil_criteria"] = -1
    # Fetching residence_ownership and mgmt_min_age from business_partners
    business_partners = cas_business.find_one({"business_id": loan_application["business_id"]},
                                              {"_id": 0, "business_partners": 1})

    cibil_analysis_data = []
    if not __is_empty(business_partners) and "business_partners" in business_partners:
        for partner in business_partners["business_partners"]:
            if partner["main_applicant"] == "Y":
                cibil_data = cas_cibil_analysis.find(
                    {
                        "business_id": loan_application["business_id"],
                        "business_partner_pan": partner["pan_no"],
                        "cibil_pull_date": {"$lte": str(cibil_max_date)}
                    },
                    {"_id": 0}
                ).sort([("cibil_pull_date", pymongo.DESCENDING)]).limit(1)

                cibil_analysis_data = db_utils.get_dict_from_cursor(cibil_data)
                break

    cibil_analysis_record = {}
    if not __is_empty(cibil_analysis_data):
        for cibil_analysis in cibil_analysis_data:
            cibil_analysis_record = cibil_analysis
            break

    if not __is_empty(business_partners) and "business_partners" in business_partners:
        for partner in business_partners["business_partners"]:
            if partner["main_applicant"] == "Y":
                fact["residence_ownership"] = partner["residence_ownership"]
                fact["mgmt_min_age"] = get_applicant_age(partner["date_of_birth"])
                cibil_data = cas_cibil_resp.find(
                    {
                        "business_id": loan_application["business_id"],
                        "business_partner_pan": partner["pan_no"],
                        "cibil_pull_date": {"$lte": str(cibil_max_date)}
                    },
                    {"_id": 0}
                ).sort([("cibil_pull_date", pymongo.DESCENDING)]).limit(1)

                cibil_data = db_utils.get_dict_from_cursor(cibil_data)

                if not __is_empty(cibil_data):
                    for record in cibil_data:
                        if "Score" in record:
                            for score in record["Score"]:
                                if "Score" in score:
                                    cibil_score = str(score["Score"])
                                    if cibil_score.isdigit():
                                        fact["consumer_cibil_criteria"] = int(score["Score"])
                                    else:
                                        fact["consumer_cibil_criteria"] = -1

                                        # Fetching cheque_bounce_in_last_90_days
    cheque_bounce_in_last_90_days = cas_bank_3_mon_analysis.find_one({"loan_application_id": loan_app_id,
                                                                      "item_header": "Cheque Bounces – Inward"},
                                                                     {"_id": 0, "count": 1})
    if not __is_empty(cheque_bounce_in_last_90_days) and "count" in cheque_bounce_in_last_90_days:
        fact["cheque_bounce_in_last_90_days"] = cheque_bounce_in_last_90_days["count"]
    else:
        fact["cheque_bounce_in_last_90_days"] = 0

    # Fetch cheque_bounce_in_last_30_days
    data = cas_bank_mon_analysis.find({"loan_application_id": loan_app_id}, {"_id": 0}).sort('value_date',
                                                                                             pymongo.DESCENDING)
    data = db_utils.get_dict_from_cursor(data)
    if not __is_empty(data):
        for rec in data:
            # print(rec)
            if "item_header" in rec and rec["item_header"] == "Cheque Bounces – Inward" \
                    and "count" in rec and rec["count"]:
                fact["cheque_bounce_in_last_30_days"] = rec["count"]
                break
    else:
        fact["cheque_bounce_in_last_30_days"] = 0

    # Fetch average_bank_balance - cas_business_bank_eod_balance_analysis
    avg_bank_bal = cas_bank_eod_bal_analysis.aggregate([
        {"$match": {"loan_application_id": loan_app_id}},
        {"$group": {
            "_id": None,
            "average": {"$avg": "$balance"}}
        }
    ])

    if not __is_empty(avg_bank_bal):
        for item in avg_bank_bal:
            fact["avg_bank_bal"] = int(item["average"])

    # Mapping values to the keys
    if not __is_empty(
            business_vintage) and "operating_since_year" in business_vintage and "operating_since_month" in business_vintage:
        fact["business_vintage"] = get_bus_exp_in_months(business_vintage["operating_since_year"],
                                                         business_vintage["operating_since_month"])

    if not __is_empty(online_sales_vintage) and "onBoarded_since" in online_sales_vintage and \
            not __is_empty(online_sales_vintage["onBoarded_since"]):

        onboarded_year = str(online_sales_vintage["onBoarded_since"][:4])
        onboarded_month = str(online_sales_vintage["onBoarded_since"][-2:])

        if onboarded_year.isdigit() and onboarded_month.isdigit():
            fact["online_sales_vintage"] = get_bus_exp_in_months(
                online_sales_vintage["onBoarded_since"][:4],
                online_sales_vintage["onBoarded_since"][-2:]
            )

    if not __is_empty(business_ownership) and "business_ownership" in business_ownership:
        fact["office_ownership"] = business_ownership["business_ownership"]

    __logger.info("cibil analysis record")
    __logger.info(json.dumps(cibil_analysis_record, indent=4, sort_keys=True, default=str))
    if not __is_empty(cibil_analysis_record):
        fact["overdues"] = get_overdue_status(cibil_analysis_record)
        fact["write_off"] = get_write_off_status(cibil_analysis_record)

    # Fetching minimum collection of Ecommerce sale in last 3 months

    # min_last_three_mon = cas_bank_3_mon_analysis.find_one(
    #     {"loan_application_id": loan_app_id, "item_header": {"$in": ["eCommerce Sales", "POS Sales"]}},
    #     {"_id": 0, "min": 1})

    result = cas_bank_mon_analysis.aggregate([{"$match": {"loan_application_id": loan_app_id,
                                                          "item_header": {"$in": ["eCommerce Sales", "POS Sales"]}}},
                                              {"$group": {
                                                  "_id": "$value_date",
                                                  "total_sum": {"$sum": "$sum"}
                                              }
                                              }]
                                             )

    result = db_utils.get_dict_from_cursor(result)

    min_last_three_mon = 0
    fact["min_collections_in_last_3months"] = min_last_three_mon

    if len(result) > 0:
        result = sorted(result, key=lambda k: parse(k["_id"]).strftime("%Y-%m"))
        result = [x for x in result if parse(x["_id"]) < loan_application_date]
        # On the above ascending ordered set, ignore the last month. Take three months from last but one month onwards.
        result = sorted(result[-4:-1], key=lambda k: k["total_sum"])
        if result and type(result).__name__ == 'list' and len(result) > 0:
            min_last_three_mon = result[0]["total_sum"]
        else:
            min_last_three_mon = 0

    if not __is_empty(min_last_three_mon):
        fact["min_collections_in_last_3months"] = min_last_three_mon

    # yet to be populated
    fact["info_verification"] = 1
    # fact["leverage"] =

    return fact


def get_criteria_element_values_scf(invoice_id):
    """

    :param invoice_id:
    :return:
    """
    fact = {}

    db_cas = db_utils.get_db_object('cas_db')
    scf_invoice = db_cas["scf_invoice"]

    invoice_record = scf_invoice.find_one({"invoice_id": invoice_id}, {"_id": 0})

    if invoice_record:
        if "customer_status" in invoice_record:
            fact["customer_status"] = invoice_record["customer_status"]

        if "overdrawn_percentage" in invoice_record:
            fact["overdrawn_percentage"] = invoice_record["overdrawn_percentage"]

    return fact


def push_database_function(rule_name, mongo_item, loan_app_id):
    db_cas = db_utils.get_db_object('cas_db')
    cas_rule_engine_score = db_cas["cas_rule_engine_score"]
    mongo_item["loan_application_id"] = loan_app_id
    cas_rule_engine_score.remove({"loan_application_id": loan_app_id, "rule_name": rule_name})
    cas_rule_engine_score.insert_one(mongo_item)

    return "Done inserting into DB"


def push_facts(rule_name, mongo_item, loan_app_id):
    db_cas = db_utils.get_db_object('cas_db')
    cas_rule_engine_facts = db_cas["cas_rule_engine_facts"]
    mongo_item["loan_application_id"] = loan_app_id
    cas_rule_engine_facts.find_one_and_update({"loan_application_id": loan_app_id}, {"$set": {rule_name: mongo_item}},
                                              upsert=True)

    return "Done inserting into DB"
