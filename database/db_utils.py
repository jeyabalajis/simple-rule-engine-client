import urllib.parse
from config.config import get_config
from pymongo import MongoClient, ReturnDocument
from crypto_util import crypto
import logging
from auth import user
import time
import logging
from database import db_cache

__logger = logging.getLogger(__name__)


def __is_empty(any_structure):
    if any_structure:
        return False
    else:
        return True


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

        db_uri = get_config('db_uri')
        db_username = get_config('db_username')
        db_pwd = get_config('db_password')

        data_decrypt = crypto.decrypt(db_pwd)

        client = MongoClient(db_uri, username=db_username, password=data_decrypt)

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


def enrich_audit_data_before_save(p_dict, p_method):
    """
    This function is to enrich the data to be posted with audit information
    :param p_dict:
    :return:
    """
    __logger.info("inside enrich_audit_data_before_save")
    if not __is_empty(p_dict):
        user_id = user.get_claims('email')
        org_name = user.get_claims('custom:organizationName')
        user_date_time_stamp = time.time()

        __logger.info("Created By: " + user_id)
        __logger.info("Created At: " + str(user_date_time_stamp))

        if "POST" == p_method:
            p_dict['created_by'] = user_id
            p_dict["initiator"] = user_id
            p_dict['created_at'] = user_date_time_stamp
            p_dict['created_at_pretty'] = time.strftime('%c')
            p_dict['org_name'] = org_name

        if "PUT" == p_method:
            p_dict['updated_by'] = user_id
            p_dict['updated_at'] = user_date_time_stamp
            p_dict['updated_at_pretty'] = time.strftime('%c')

    return p_dict
