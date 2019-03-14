from database import rule_db_functions as rule_dao
import logging
import operator
import json

__logger = logging.getLogger(__name__)

global __recursion_depth
__recursion_depth = 0

global __facts
__facts = {}

global __operator_mapping
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

global __rule_results
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
            # __logger.info("core evaluation for: " + str(p_value) + p_operator + str(target_value))
            # Jeyabalaji@11-Dec-2018 added between operator
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


def __evaluate_token(rule_antecedent, org_name):
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
            child_rule_lexicon = rule_dao.get_a_rule(rule_antecedent["child_rule_name"], org_name)
            child_rule_score = __compute_score(child_rule_lexicon, org_name)
            token_result = __parse_and_execute_token(rule_antecedent, child_rule_score)
            rule_antecedent["token_result"] = token_result
            return token_result
    else:
        return False


def __evaluate_rule_antecedent(rule_antecedent, condition, org_name):
    """

    :param rule_antecedent:
    :param condition:
    :return:
    """
    global __recursion_depth
    __recursion_depth = __recursion_depth + 1
    # __logger.info("recursion depth reached: " + str(__recursion_depth))
    if __recursion_depth > 5:
        # __logger.info("suicide alert!!")
        # __logger.info("attention coder. your code is strangling itself to death. check")
        return False

    truth = True
    # in when_any, any one constituent has to be true
    if condition == "@when_any":
        truth = False

    # in when_all, every constituent has to be true
    if condition == "@when_all":
        truth = True

    # __logger.info("INCOMING ANTECEDENT")
    # __logger.info(json.dumps(rule_antecedent, indent=4, sort_keys=True, default=str))

    rule_antecedents = []
    if type(rule_antecedent).__name__ == 'dict':
        rule_antecedents.append(rule_antecedent)

    if type(rule_antecedent).__name__ == 'list':
        rule_antecedents = rule_antecedent

    for constituent in rule_antecedents:
        if "@when_all" in constituent:
            constituent_result = __evaluate_rule_antecedent(constituent["@when_all"], "@when_all", org_name)
        if "@when_any" in constituent:
            constituent_result = __evaluate_rule_antecedent(constituent["@when_any"], "@when_any", org_name)
        if "token_name" in constituent:
            # __logger.info("single token case. evaluate token")
            constituent_result = __evaluate_token(constituent, org_name)

        if condition == "@when_any":
            truth = truth or constituent_result

        if condition == "@when_all":
            truth = truth and constituent_result

        # # __logger.info("constituent result: " + str(constituent_result))
        # __logger.info("truth===>: " + str(truth))

    # __logger.info("Evaluation results for antecedent: " + str(truth))
    return truth


def __evaluate_rule_set(rule_name, rule_set, parent, org_name):
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
                rule_row_result = __evaluate_rule_antecedent(rule_row["antecedent"], "@when_all", org_name)

            if rule_row_result:
                # __logger.info("This rule row has evaluated as true!!! returning consequent")
                unweighted_score = rule_row["consequent"]["score"]
                rule_row["evaluated"] = True
                rule_set_result["rule_rows"].append(rule_row)
                break
            else:
                # __logger.info("This rule row has evaluated as false :( continue evaluating the next row")
                rule_row["evaluated"] = False
                rule_set_result["rule_rows"].append(rule_row)

        # __logger.info("DONE WITH ALL RULE ROWS for " + rule_set["set_name"])
        # __logger.info("$$$ UNWEIGHTED SCORE@" + rule_set["set_name"] + " = " + str(unweighted_score))

        weighted_score = unweighted_score * rule_set["weight"]
        # __logger.info("$$$   WEIGHTED SCORE@" + rule_set["set_name"] + " = " + str(weighted_score))

        rule_set_result["unweighted_score"] = unweighted_score
        rule_set_result["weighted_score"] = weighted_score

        if parent:
            __assign_rule_set_to_results(rule_set_result)
        else:
            rule_set_result_wrapper = dict(rule_name=rule_name, rule_results=rule_set_result)
            __assign_rule_set_to_results(rule_set_result_wrapper)

    return weighted_score


def __evaluate_rule_decision_set(rule_name, rule_set, parent, org_name):
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
                rule_row_result = __evaluate_rule_antecedent(rule_row["antecedent"], "@when_all", org_name)

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

        # __logger.info("DONE WITH ALL RULE ROWS for " + rule_set["set_name"])
        # __logger.info("$$$ DECISION@" + rule_set["set_name"] + " = " + str(decision))

        rule_set_result["decision"] = decision

        if parent:
            __assign_rule_set_to_results(rule_set_result)
        else:
            rule_set_result_wrapper = dict(rule_name=rule_name, rule_results=rule_set_result)
            __assign_rule_set_to_results(rule_set_result_wrapper)

    return decision


def __compute_score(rule_lexicon, parent, depth, org_name):
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
                    # __logger.info("evaluating rule set: " + rule_set["set_name"])

                    score = __evaluate_rule_set(rule_lexicon["rule_name"], rule_set, parent, org_name)
                    # __logger.info("rule set score for#" + rule_lexicon["rule_name"]
                    #               + "#============>" + str(score))

                if rule_set["rule_set_type"] == 'compute':
                    # __logger.info("computing child rule: " + rule_set["rule_name"])
                    child_rule_lexicon = rule_dao.get_a_rule(rule_set["rule_name"], org_name)
                    if __is_empty(child_rule_lexicon):
                        # __logger.info("rule lexicon not found!")
                        score = 0
                        unweighted_score = 0
                    else:
                        unweighted_score = __compute_score(child_rule_lexicon, False, depth+1, org_name)
                        score = unweighted_score * rule_set["weight"]

                    child_rule_result = dict(rule_name=child_rule_lexicon["rule_name"], weighted_score=score,
                                             unweighted_score=unweighted_score, depth=depth+1)

                    __assign_child_rule_to_results(child_rule_result)

                    # __logger.info("rule set score for#" + child_rule_lexicon["rule_name"]
                    #               + "#============>" + str(score))
            total_score = total_score + score
            # __logger.info("total score now ============>" + str(total_score))
    return total_score


def __get_decision(rule_lexicon, parent, org_name):
    """

    :param rule_lexicon:
    :return:
    """
    decision = 'none'
    if "rule_set" in rule_lexicon:
        rule_set = rule_lexicon["rule_set"]
        # __logger.info("evaluating rule set: " + rule_set["set_name"])
        decision = __evaluate_rule_decision_set(rule_lexicon["rule_name"], rule_set, parent, org_name)

        # __logger.info("final decision now ============>" + str(decision))

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
    # __logger.info(json.dumps(__rule_results, indent=4, sort_keys=True, default=str))


def __init_rule_results(rule_lexicon):
    """

    :param rule_lexicon:
    :return:
    """
    global __rule_results
    __rule_results = {"rule_name": rule_lexicon["rule_name"], "rule_description": rule_lexicon["rule_description"],
                      "rule_type": rule_lexicon["rule_type"], "result_set": [], "child_rules": []}


def execute_rule(rule_name, p_facts, org_name=None):
    """

    :param org_name:
    :param p_facts:
    :param rule_name:
    :return:


    """

    if __is_empty(rule_name):
        return False
        # __logger.info("rule name is mandatory!")

    if __is_empty(p_facts):
        return False
        # __logger.info("facts are mandatory!")

    global __facts
    __facts = p_facts

    # __logger.info("rule name: " + rule_name)
    # __logger.info(json.dumps(p_facts, indent=4, sort_keys=True, default=str))

    rule_lexicon = rule_dao.get_a_rule(rule_name, org_name)

    if __is_empty(rule_lexicon):
        return False
        # __logger.info("rule lexicon not found!")

    if "rule_type" in rule_lexicon:

        __init_rule_results(rule_lexicon)

        if rule_lexicon["rule_type"] == "score":
            # __logger.info("calling compute score function")
            total_score = __compute_score(rule_lexicon, True, 0, org_name)
            # __logger.info("$$$$$TOTAL SCORE$$$$$" + str(total_score))
            __populate_rule_results('final_score', total_score)

        if rule_lexicon["rule_type"] == "decision":
            decision = __get_decision(rule_lexicon, True, org_name)
            # __logger.info("$$$$$FINAL DECISION$$$$$" + str(decision))
            __populate_rule_results('final_decision', decision)

    else:
        return False
        # __logger.info("Rule type is not set for this rule")

    return __rule_results
