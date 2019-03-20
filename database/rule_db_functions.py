import logging
from datetime import datetime
from datetime import timedelta

import pymongo
from dateutil.parser import parse

from database import db_utils

__logger = logging.getLogger(__name__)


def __is_empty(any_structure):
    if any_structure:
        return False
    else:
        return True


def get_a_rule(rule_name):
    """

    :param rule_name:
    :return:
    """
    __db_rules = db_utils.get_db_object('rule_db')
    rules_repo_db = __db_rules['rules_repository']

    results = rules_repo_db.find_one(
        {
            "rule_name": rule_name,
        },
        {
            "_id": 0
        }
    )

    return results


def get_all_rules():
    """

    :return:
    """
    __db_rules = db_utils.get_db_object('rule_db')
    rules_repo_db = __db_rules['rules_repository']

    results = rules_repo_db.find(
        {
        },
        {
            "_id": 0,
            "rule_name": 1,
            "rule_type": 1,
            "rule_description": 1
        }
    )

    results = db_utils.get_dict_from_cursor(results)
    return results
