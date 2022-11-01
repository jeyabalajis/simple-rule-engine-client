from simpleruleengine.conditional.conditional import Conditional
from simpleruleengine.expression.expression import Expression
from simpleruleengine.operator.between import Between
from simpleruleengine.operator.string_in import In
from simpleruleengine.operator.equal import Eq
from simpleruleengine.operator.greater_than import Gt
from simpleruleengine.operator.greater_than_equal import Gte
from simpleruleengine.operator.less_than import Lt
from simpleruleengine.operator.less_than_equal import Lte
from simpleruleengine.operator.boolean_operator import BooleanOperator
from lark import Tree, Token


def expression_pretty(expression: Expression):
    expression_string = ""
    expression_string += expression.token.name + " "
    expression_string += type(expression.operator).__name__ + " "
    if type(expression.operator).__name__ == "Between":
        expression_string += str(expression.operator.floor) + ", " + str(expression.operator.ceiling)
    else:
        expression_string += str(expression.operator.base_value)

    return expression_string


def conditional_pretty(conditional: Conditional, depth=0):
    conditional_string = type(conditional).__name__ + "("

    for child in conditional.expressions:
        if type(child).__name__ in ("WhenAll", "WhenAny"):
            conditional_string += "(" + conditional_pretty(child, depth + 1) + "), "

        if type(child).__name__ in "Expression":
            conditional_string += "{" + expression_pretty(child) + "}, "

    conditional_string += ")"

    return conditional_string


def get_between(*base_value: Tree):
    return Between(
        floor=float(base_value[0].children[0].value),
        ceiling=float(base_value[1].children[0].value)
    )


def get_list_in(base_value):
    str_in_list: List[str] = []
    for item in base_value:
        for child in item.children:
            str_in_list.append(child.value)
    return In(*tuple(str_in_list))


def get_operator_value(base_value):
    operator_value = None
    for item in base_value:
        for child in item.children:
            operator_value = float(child.value)
    return operator_value


def get_greater_than_equal(base_value):
    operator_value = get_operator_value(base_value)
    assert operator_value is not None
    return Gte(operator_value)


def get_greater_than(base_value):
    operator_value = get_operator_value(base_value)
    assert operator_value is not None
    return Gt(operator_value)


def get_less_than(base_value):
    operator_value = get_operator_value(base_value)
    assert operator_value is not None
    return Lt(operator_value)


def get_less_than_equal(base_value):
    operator_value = get_operator_value(base_value)
    assert operator_value is not None
    return Lte(operator_value)


def get_equal(base_value, rule_engine_token_type):
    for item in base_value:
        for child in item.children:
            if rule_engine_token_type == "NumericToken":
                operator_value = float(child.value)
                return Eq(operator_value)

            if rule_engine_token_type == "StringToken":
                operator_value = str(child.value)
                return In(*tuple([operator_value]))

            if rule_engine_token_type == "BooleanToken":
                operator_value = str(child.value)
                if operator_value == "true":
                    return BooleanOperator(True)
                if operator_value == "false":
                    return BooleanOperator(False)


def get_boolean(boolean_token: Token):
    if boolean_token.value == "true":
        return True
    else:
        return False


def get_number(numeric_token: Token):
    return float(numeric_token.value)


def get_token_value(token: Tree):
    if token.data == "boolean":
        return get_boolean(token.children[0])

    if token.data == "number":
        return get_number(token.children[0])


def get_consequent(consequent: Tree):
    return get_token_value(consequent.children[0])
