from service import rule_parser
from functions import report
from database import rule_db_functions


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

    return _results


def __fetch_and_resolve_rule(rule_name, facts):
    """

    :param rule_name:
    :return:
    """
    rule_template = rule_db_functions.get_a_rule(rule_name)

    if rule_template:
        if (
                "rule_type" in rule_template
                and rule_template["rule_type"] == "decision"
        ):
            _rule_set = rule_template["rule_set"]

            if "rule_rows" in _rule_set:
                for _rule_row in _rule_set["rule_rows"]:
                    _antecedent = _rule_row["antecedent"]
                    __gather_facts(_antecedent, facts)
        else:
            _rule_sets = rule_template["rule_set"]

            for _rule_set in _rule_sets:
                if _rule_set["rule_set_type"] == "evaluate":
                    if "rule_rows" in _rule_set:
                        for _rule_row in _rule_set["rule_rows"]:
                            _antecedent = _rule_row["antecedent"]
                            __gather_facts(_antecedent, facts)
                elif _rule_set["rule_set_type"] == "compute":
                    print("resolve child rule: " + _rule_set["rule_name"])
                    __fetch_and_resolve_rule(_rule_set["rule_name"], facts)

    return facts


def __gather_facts(antecedent, facts):
    """

    :param antecedent:
    :return:
    """
    rule_antecedents = []
    if type(antecedent).__name__ == 'dict':
        rule_antecedents.append(antecedent)

    if type(antecedent).__name__ == 'list':
        rule_antecedents = antecedent

    for _antecedent in rule_antecedents:
        if "@when_all" in _antecedent:
            __gather_facts(_antecedent["@when_all"], facts)
        elif "@when_any" in _antecedent:
            __gather_facts(_antecedent["@when_any"], facts)
        elif "token_name" in _antecedent:
            if _antecedent["token_category"] in "organic":
                _fact = {"token_name": _antecedent["token_name"]}

                if "token_type" in _antecedent:
                    _fact["token_type"] = _antecedent["token_type"]

                if _fact not in facts:
                    facts.append(_fact)
            else:
                __fetch_and_resolve_rule(_antecedent["child_rule_name"], facts)


def find_rule(rule_name):
    """

    :param rule_name:
    :return:
    """
    facts = []
    __fetch_and_resolve_rule(rule_name, facts)

    return facts


def find_all_rules():
    """

    :return:
    """
    results = rule_db_functions.get_all_rules()

    return results
