import json
import logging

from pymongo import MongoClient

from common.configure import get_config
from common.database import db_cache
from common.secrets_manager import secrets_manager_service

__logger = logging.getLogger(__name__)


def __is_empty(any_structure):
    if any_structure:
        return False
    else:
        return True


def init_rule_db(db):
    """

    :param db:
    :return:
    """
    db_cache.set_db_cache("rule_db", db)


def get_db_object(db_name) -> object:
    """

    :type db_name: object
    :return: pymongo client object
    """

    db_handle = db_cache.get_db_cache(db_name)

    if not __is_empty(db_handle):
        __logger.info("sending db object from cache!")
        return db_handle
    else:
        __logger.info("inside get_db_object with db name as: " + db_name)

        db_credentials_id = get_config("db_credentials_id")
        db_secrets = secrets_manager_service.get_secret(db_credentials_id)
        db_secrets = json.loads(db_secrets)

        db_uri = db_secrets["db_url"]
        db_username = db_secrets["user_name"]
        db_pwd = db_secrets["password"]

        client = MongoClient(db_uri, username=db_username, password=db_pwd)

        __db_name = get_config(db_name)
        db = client[__db_name]

        db_cache.set_db_cache(db_name, db)
        return db


def get_dict_from_cursor(p_cursor):
    """

    :param p_cursor:
    :return:
    """
    r_dict = {}
    if not __is_empty(p_cursor):
        r_dict = [doc for doc in p_cursor]
    return r_dict
