import logging
import json
from service import rule_engine_service
from service import response_util


__logger = logging.getLogger(__name__)


def execute_rule_engine(rule_name, body):
    """

    :param rule_name:
    :param body:
    :return:
    """
    __logger.info("inside execute_rule_engine for " + rule_name)
    __logger.info(json.dumps(body, indent=4, sort_keys=True, default=str))

    try:
        result = rule_engine_service.execute_rule_engine_service(rule_name, body)

        if "code" in result:
            if result["code"] == 0:
                resp = response_util.get_response(200, "Success", result["message"])
            else:
                resp = response_util.get_response(400, "Error", result["message"])
        else:
            resp = response_util.get_response(500, "Error", "Unknown exception")
        return resp

    except:
        import traceback
        __logger.error("Unhandled exception while executing rule engine!!!")
        __logger.error(traceback.format_exc())
        resp = response_util.get_response(500, "Error", traceback.format_exc())
        return resp


def get_rule(rule_name):
    """

    :param rule_name:
    :return:
    """
    data = rule_engine_service.find_rule(rule_name)
    resp = response_util.get_response(200, "Success", data)

    return resp


def get_all_rules():
    """

    :return:
    """
    data = rule_engine_service.find_all_rules()
    resp = response_util.get_response(200, "Success", data)

    return resp
