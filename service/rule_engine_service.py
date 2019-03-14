from service import rule_parser
from functions import report


def execute_rule_engine_service(rule_name, body):
    """

    :param rule_name:
    :param body:
    :return:
    """

    if not body:
        return report(1, "request is mandatory")

    if "facts" not in body:
        return report(1, "root node facts is mandatory")

    _facts = body["facts"]

    _results = rule_parser.execute_rule(rule_name, _facts)

    return report(0, _results)
