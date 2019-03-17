import logging
import operator

from config.config import get_config
from database import rule_db_functions as rule_dao

__logger = logging.getLogger(__name__)

__recursion_depth = 0

__facts = {}

__operator_mapping = {
    "<=": operator.le,
    "<": operator.lt,
    ">=": operator.ge,
    ">": operator.gt,
    "==": operator.eq,
    "<>": operator.ne,
    "is_none": operator.eq,
    "between": "between"
}

__rule_results = {}


def __is_empty(any_structure):
    if any_structure:
        return False
    else:
        return True


# Error report gen function
def __report(code, message):
    return {"code": code, "message": message}


def __get_func_for_operator(p_operator):
    """

    :param operator:
    :return:
    """
    global __operator_mapping
    if p_operator in __operator_mapping:
        return __operator_mapping[p_operator]
    else:
        return None


def __evaluate_numeric(p_value, p_operator, target_value):
    """

    :param p_value:
    :param p_operator:
    :param target_value:
    :return:
    """
    if p_operator == "is_none":
        return p_value is None
    else:
        try:
            operator_func = __get_func_for_operator(p_operator)
            if operator_func == "between":
                operator_func_gte = __get_func_for_operator(">=")
                operator_func_lte = __get_func_for_operator("<=")

                return (
                        operator_func_gte(p_value, target_value["low"])
                        and
                        operator_func_lte(p_value, target_value["high"])
                )
            else:
                return operator_func(p_value, target_value)
        except:
            import traceback
            __logger.error("Unhandled exception while evaluating numeric!!!")
            __logger.error(traceback.format_exc())
            return False


def __evaluate_string(p_value, p_operator, target_value):
    """

    :param p_value:
    :param p_operator:
    :param target_value:
    :return:
    """
    if p_operator == "in_list":
        if p_value in target_value:
            return True
        else:
            return False

    if p_operator == "contains":
        if target_value in p_value:
            return True
        else:
            return False

    if p_operator == "is_none":
        if target_value == p_value:
            return True
        else:
            return False

    if p_operator == "equals":
        if target_value == p_value:
            return True
        else:
            return False


def __parse_and_execute_token(rule_antecedent, eval_parameter):
    """

    :rtype: object
    :param rule_antecedent:
    :return:
    """
    # __logger.info("token name: " + rule_antecedent["token_name"])
    # __logger.info("token type: " + rule_antecedent["token_type"])
    # __logger.info("token caty: " + rule_antecedent["token_category"])
    # __logger.info("operator: " + rule_antecedent["operator"])

    if rule_antecedent["token_type"] == "numeric":
        if "eval_value" not in rule_antecedent:
            rule_antecedent["eval_value"] = None

        # __logger.info("evaluation vale: " + str(rule_antecedent["eval_value"]))
        return __evaluate_numeric(eval_parameter, rule_antecedent["operator"], rule_antecedent["eval_value"])

    if rule_antecedent["token_type"] == "string":
        if "eval_value" not in rule_antecedent:
            rule_antecedent["eval_value"] = None

        return __evaluate_string(eval_parameter, rule_antecedent["operator"], rule_antecedent["eval_value"])


def __evaluate_token(rule_antecedent):
    """

    :param rule_antecedent:
    :return:
    """

    if "token_category" in rule_antecedent and "token_type" in rule_antecedent:
        if rule_antecedent["token_category"] == "organic":
            global __facts
            if rule_antecedent["token_name"] in __facts:
                # global __facts
                rule_antecedent["token_value"] = __facts[rule_antecedent["token_name"]]
                token_result = __parse_and_execute_token(rule_antecedent, __facts[rule_antecedent["token_name"]])
                rule_antecedent["token_result"] = token_result
                return token_result
            else:
                return False
        if rule_antecedent["token_category"] == 'inorganic':
            child_rule_lexicon = rule_dao.get_a_rule(rule_antecedent["child_rule_name"])
            child_rule_score = __compute_score(child_rule_lexicon)
            token_result = __parse_and_execute_token(rule_antecedent, child_rule_score)
            rule_antecedent["token_result"] = token_result
            return token_result
    else:
        return False


def __evaluate_rule_antecedent(rule_antecedent, condition):
    """

    :param rule_antecedent:
    :param condition:
    :return:
    """
    global __recursion_depth
    __recursion_depth = __recursion_depth + 1

    _max_recursion_depth = get_config('max_recursion_depth')

    if not __is_empty(_max_recursion_depth):
        _max_recursion_depth = 5

    if __recursion_depth > _max_recursion_depth:
        return False

    truth = True
    # in when_any, any one constituent has to be true
    if condition == "@when_any":
        truth = False

    # in when_all, every constituent has to be true
    if condition == "@when_all":
        truth = True

    rule_antecedents = []
    if type(rule_antecedent).__name__ == 'dict':
        rule_antecedents.append(rule_antecedent)

    if type(rule_antecedent).__name__ == 'list':
        rule_antecedents = rule_antecedent

    for constituent in rule_antecedents:
        if "@when_all" in constituent:
            constituent_result = __evaluate_rule_antecedent(constituent["@when_all"], "@when_all")
        if "@when_any" in constituent:
            constituent_result = __evaluate_rule_antecedent(constituent["@when_any"], "@when_any")
        if "token_name" in constituent:
            # __logger.info("single token case. evaluate token")
            constituent_result = __evaluate_token(constituent)

        if condition == "@when_any":
            truth = truth or constituent_result

        if condition == "@when_all":
            truth = truth and constituent_result

    return truth


def __evaluate_rule_set(rule_name, rule_set, parent):
    """

    :param rule_name:
    :param rule_set:
    :param parent:
    :return:
    """

    rule_set_result = {
        "set_name": rule_set["set_name"],
        "weight": rule_set["weight"],
        "rule_rows": []
    }

    weighted_score = 0
    if "rule_rows" in rule_set:
        unweighted_score = 0
        for rule_row in rule_set["rule_rows"]:
            global __recursion_depth
            __recursion_depth = 0

            rule_row_result = False
            if "antecedent" in rule_row:
                rule_row_result = __evaluate_rule_antecedent(rule_row["antecedent"], "@when_all")

            if rule_row_result:
                unweighted_score = rule_row["consequent"]["score"]
                rule_row["evaluated"] = True
                rule_set_result["rule_rows"].append(rule_row)
                break
            else:
                rule_row["evaluated"] = False
                rule_set_result["rule_rows"].append(rule_row)

        weighted_score = unweighted_score * rule_set["weight"]

        rule_set_result["unweighted_score"] = unweighted_score
        rule_set_result["weighted_score"] = weighted_score

        if parent:
            __assign_rule_set_to_results(rule_set_result)
        else:
            rule_set_result_wrapper = dict(rule_name=rule_name, rule_results=rule_set_result)
            __assign_rule_set_to_results(rule_set_result_wrapper)

    return weighted_score


def __evaluate_rule_decision_set(rule_name, rule_set, parent):
    """

    :param rule_name:
    :param rule_set:
    :param parent:
    :return:
    """

    rule_set_result = {
        "set_name": rule_set["set_name"],
        "rule_rows": []
    }

    decision = 'none'
    if "rule_rows" in rule_set:

        for rule_row in rule_set["rule_rows"]:
            global __recursion_depth
            __recursion_depth = 0

            rule_row_result = False
            if "antecedent" in rule_row:
                rule_row_result = __evaluate_rule_antecedent(rule_row["antecedent"], "@when_all")

            if rule_row_result:
                # __logger.info("This rule row has evaluated as true!!! returning consequent")
                decision = rule_row["consequent"]["decision"]
                rule_row["evaluated"] = True
                rule_set_result["rule_rows"].append(rule_row)
                break
            else:
                # __logger.info("This rule row has evaluated as false :( continue evaluating the next row")
                rule_row["evaluated"] = False
                rule_set_result["rule_rows"].append(rule_row)

        rule_set_result["decision"] = decision

        if parent:
            __assign_rule_set_to_results(rule_set_result)
        else:
            rule_set_result_wrapper = dict(rule_name=rule_name, rule_results=rule_set_result)
            __assign_rule_set_to_results(rule_set_result_wrapper)

    return decision


def __compute_score(rule_lexicon, parent, depth):
    """

    :param rule_lexicon:
    :return:
    """
    total_score = 0
    if "rule_set" in rule_lexicon:
        for rule_set in rule_lexicon["rule_set"]:
            score = 0
            unweighted_score = 0
            if "rule_set_type" in rule_set:
                if rule_set["rule_set_type"] == 'evaluate':
                    score = __evaluate_rule_set(rule_lexicon["rule_name"], rule_set, parent)

                if rule_set["rule_set_type"] == 'compute':
                    child_rule_lexicon = rule_dao.get_a_rule(rule_set["rule_name"])
                    if __is_empty(child_rule_lexicon):
                        score = 0
                        unweighted_score = 0
                    else:
                        unweighted_score = __compute_score(child_rule_lexicon, False, depth + 1)
                        score = unweighted_score * rule_set["weight"]

                    child_rule_result = dict(rule_name=child_rule_lexicon["rule_name"], weighted_score=score,
                                             unweighted_score=unweighted_score, depth=depth + 1)

                    __assign_child_rule_to_results(child_rule_result)

            total_score = total_score + score
    return total_score


def __get_decision(rule_lexicon, parent):
    """

    :param rule_lexicon:
    :return:
    """
    decision = 'none'
    if "rule_set" in rule_lexicon:
        rule_set = rule_lexicon["rule_set"]
        decision = __evaluate_rule_decision_set(rule_lexicon["rule_name"], rule_set, parent)

    return decision


def __assign_rule_set_to_results(rule_set):
    """

    :param rule_set:
    :return:
    """
    global __rule_results
    __rule_results["result_set"].append(rule_set)


def __assign_child_rule_to_results(child_rule_results):
    """

    :param rule_set:
    :return:
    """
    global __rule_results
    __rule_results["child_rules"].append(child_rule_results)


def __populate_rule_results(tag, value):
    """

    :param tag:
    :param value:
    :return:
    """
    global __rule_results
    __rule_results[tag] = value


def __init_rule_results(rule_lexicon):
    """

    :param rule_lexicon:
    :return:
    """
    global __rule_results
    __rule_results = {
        "rule_name": rule_lexicon["rule_name"],
        "rule_description": rule_lexicon["rule_description"],
        "rule_type": rule_lexicon["rule_type"],
        "result_set": [],
        "child_rules": []
    }


def execute_rule(rule_name, p_facts):
    """

    :param p_facts:
    :param rule_name:
    :return:


    """

    if __is_empty(rule_name):
        __logger.error("rule name is mandatory!")
        return False

    if __is_empty(p_facts):
        __logger.error("facts are mandatory!")
        return False

    global __facts
    __facts = p_facts

    rule_lexicon = rule_dao.get_a_rule(rule_name)

    if __is_empty(rule_lexicon):
        return False

    if "rule_type" in rule_lexicon:

        __init_rule_results(rule_lexicon)

        if rule_lexicon["rule_type"] == "score":
            __logger.info("calling compute score function")
            total_score = __compute_score(rule_lexicon, True, 0)
            __logger.info("$$$$$TOTAL SCORE$$$$$" + str(total_score))
            __populate_rule_results('final_score', total_score)

        if rule_lexicon["rule_type"] == "decision":
            __logger.info("calling get decision function")
            decision = __get_decision(rule_lexicon, True)
            __logger.info("$$$$$FINAL DECISION$$$$$" + str(decision))
            __populate_rule_results('final_decision', decision)

    else:
        __logger.error("Rule type is not set for this rule")
        return False

    return __rule_results
