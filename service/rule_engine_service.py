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


def __fetch_and_resolve_rule(rule_name):
    """

    :param rule_name:
    :return:
    """
    facts = []
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
                if "rule_rows" in _rule_set:
                    for _rule_row in _rule_set["rule_rows"]:
                        _antecedent = _rule_row["antecedent"]
                        __gather_facts(_antecedent, facts)

    return facts


def __gather_facts(antecedent, facts):
    """

    :param antecedent:
    :return:
    """
    if "@when_all" in antecedent:
        __gather_facts(antecedent["@when_all"], facts)
    elif "@when_any" in antecedent:
        __gather_facts(antecedent["@when_any"], facts)
    else:
        for _token in antecedent:
            if _token["token_category"] in "organic":
                if "@when_all" in antecedent:
                    __gather_facts(antecedent["@when_all"], facts)
                elif "@when_any" in antecedent:
                    __gather_facts(antecedent["@when_any"], facts)
                else:
                    _fact = {}
                    if "token_name" in _token:
                        _fact["token_name"] = _token["token_name"]

                    if "token_type" in _token:
                        _fact["token_type"] = _token["token_type"]
                    facts.append(_fact)
            else:
                _referred_rule_facts = __fetch_and_resolve_rule(_token["child_rule_name"])
                facts.extend(_referred_rule_facts)


def find_rule(rule_name):
    """

    :param rule_name:
    :return:
    """
    facts = __fetch_and_resolve_rule(rule_name)

    return facts


